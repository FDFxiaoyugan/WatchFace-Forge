"""
Generate 路由 — 自然语言 → CDM → APK

POST /api/generate
  body: {prompt: "霓虹蓝赛博朋克数字表盘", user_id?: "default", ai_config?: {...}}
  → 异步: LLM 生成 CDM → 自动修复 → 编译 WFF → 构建 APK
  → 同步返回: CDM + 下载 URL

WebSocket /api/ws/{task_id}
  → 实时推送生成进度
"""

import sys
import json
import asyncio
from pathlib import Path
from fastapi import APIRouter, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from api.models import BuildResponse
from api.services.artifact_paths import final_apk_path, new_task_id, task_id_dir
from api.services.error_sanitize import safe_client_error
from api.services.quota import authorize_ai_endpoint, consume_ai_quota
from api.services.wff_access import WFFAPIError

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "wff-builder"))

from services.cdm_generator import CDMGenerator
from services.ai_gateway import AIGateway, AIConfigError, normalize_user_ai_config
from compiler.wff.compiler import WFFCompiler
from wff_builder import WFFBuilder, validate_watchface_xml

router = APIRouter()

# 进度存储 (task_id → progress list)
_progress_store: dict[str, list[dict]] = {}


class ProgressTracker:
    """WebSocket 进度推送"""
    def __init__(self, task_id: str):
        self.task_id = task_id
        _progress_store[task_id] = []

    def emit(self, stage: str, progress: int, message: str = ""):
        event = {"task_id": self.task_id, "stage": stage, "progress": progress, "message": message}
        _progress_store[self.task_id].append(event)

    def get_history(self) -> list[dict]:
        return _progress_store.get(self.task_id, [])


import tempfile
import shutil


@router.post("/ai/test")
async def test_ai_connection(req: dict, x_api_key: str = Header(default=None, alias="X-API-Key")):
    """验证用户临时 OpenAI 兼容配置；不保存或回显密钥。

    审计 S4: 需通过 API key 鉴权并计入配额（客户端 user_id 不再是配额身份）。
    """
    identity = authorize_ai_endpoint(x_api_key, "ai_test")
    consume_ai_quota(identity, "ai_test")
    try:
        ai_config = normalize_user_ai_config(req.get("ai_config"))
    except AIConfigError as exc:
        return JSONResponse(status_code=400, content={
            "status": "error",
            "error_type": "invalid_ai_config",
            "message": str(exc),
        })

    if not ai_config:
        return JSONResponse(status_code=400, content={
            "status": "error",
            "error_type": "missing_api_key",
            "message": "请先填写自定义 AI API Key",
        })

    gateway = AIGateway(
        backend="openai",
        api_key=ai_config["api_key"],
        base_url=ai_config["base_url"] or None,
        model=ai_config["model"],
    )
    result = gateway.test_connection()
    if not result["success"]:
        return JSONResponse(status_code=502, content={
            "status": "error",
            "error_type": "ai_connection_failed",
            "message": result.get("error", "AI 服务连接失败"),
            "model": result["model"],
            "latency_ms": result["latency_ms"],
        })
    return {"status": "success", **result}


@router.post("/generate")
async def generate_watchface(req: dict, x_api_key: str = Header(default=None, alias="X-API-Key")):
    """自然语言 → CDM → APK 全流程"""
    # 审计 S4: AI 消耗端点鉴权 + 服务端配额（调用前原子扣减）
    identity = authorize_ai_endpoint(x_api_key, "generate")
    consume_ai_quota(identity, "generate")
    prompt = req.get("prompt", "").strip()

    if not prompt:
        return JSONResponse(status_code=400, content={
            "status": "error",
            "error_type": "invalid_input",
            "message": "prompt is required",
        })

    try:
        ai_config = normalize_user_ai_config(req.get("ai_config"))
    except AIConfigError as exc:
        return JSONResponse(status_code=400, content={
            "status": "error",
            "error_type": "invalid_ai_config",
            "message": str(exc),
        })

    task_id = new_task_id(8)
    tracker = ProgressTracker(task_id)

    # 1. LLM 生成 CDM
    tracker.emit("llm_generating", 20, "正在调用 AI 生成表盘设计...")

    gateway = AIGateway(
        backend="openai",
        api_key=ai_config["api_key"],
        base_url=ai_config["base_url"] or None,
        model=ai_config["model"],
    ) if ai_config else AIGateway()
    generator = CDMGenerator(gateway)
    gen_result = generator.generate(prompt)

    if not gen_result["success"]:
        tracker.emit("failed", 100, f"生成失败: {gen_result.get('error', '')[:100]}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": gen_result.get("error", "Unknown error"),
            "stage": "llm_generating",
        }

    cdm_dict = gen_result["cdm"]
    tracker.emit("cdm_generated", 50, f"CDM 生成完成 (backend: {gen_result['backend']}, {gen_result['attempts']} 次尝试)")

    # CDM 校验通过即持久化（Redis TTL 1h）：APK 构建失败也可进编辑器调整
    from api.services.cdm_store import store_cdm
    try:
        store_cdm(task_id, cdm_dict)
    except ValueError:
        pass  # task_id 由服务端生成, 此分支仅为防御
    except RuntimeError as exc:
        # 复查 R6: 生产模式存档失败 → 整体失败响应（拒绝"已存档"但取不回）
        tracker.emit("failed", 100, str(exc)[:120])
        return {
            "task_id": task_id,
            "status": "failed",
            "error_type": "cdm_store_unavailable",
            "message": str(exc)[:300],
        }
    tracker.emit("cdm_stored", 55, "CDM 已存档, 可随时带入编辑器")

    if gen_result["fixes"]:
        tracker.emit("auto_fixed", 60, f"自动修复 {len(gen_result['fixes'])} 处问题")

    # 2. 编译 CDM → WFF XML
    tracker.emit("compiling", 70, "正在编译 WFF XML...")
    from schema.cdm.models import WatchFaceCDM
    cdm = WatchFaceCDM(**cdm_dict)
    compiler = WFFCompiler()
    wff_xml = compiler.compile(cdm)

    failures = validate_watchface_xml(wff_xml)
    errors = [f for f in failures if f["severity"] == "error"]
    if errors:
        tracker.emit("failed", 100, f"WFF 校验失败: {len(errors)} 个错误")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": f"WFF validation failed: {errors[0]['detail']}",
            "cdm": cdm_dict,
        }

    tracker.emit("compiled", 80, "WFF XML 校验通过")

    # 3. 构建 APK
    tracker.emit("building_apk", 85, "正在构建 APK...")

    try:
        from api.services.preview_renderer import render_preview

        # S5: project dir 只由服务端 task_id 决定
        project_dir = task_id_dir(task_id)
        project_dir.mkdir(exist_ok=True)

        (project_dir / "watchface.xml").write_text(wff_xml, encoding="utf-8")
        render_preview(project_dir / "preview.png", cdm)

        import yaml
        config = {
            "package_name": cdm.metadata.package_name,
            "version_code": cdm.metadata.version_code,
            "version_name": cdm.metadata.version_name,
            "watch_face_name": cdm.metadata.name,
            "wff_version": 1,
        }
        with open(project_dir / "project.yaml", "w") as f:
            yaml.dump(config, f)

        builder = WFFBuilder(str(project_dir), verbose=False)
        apk_path = builder.build()

        # S5: 文件名仅来自服务端 task_id; 表盘名仅作展示字段
        final_apk = final_apk_path(task_id)
        shutil.copy2(apk_path, final_apk)
        shutil.rmtree(project_dir, ignore_errors=True)

        tracker.emit("done", 100, f"构建完成! APK {final_apk.stat().st_size:,} bytes")

        return {
            "task_id": task_id,
            "status": "success",
            "cdm": cdm_dict,
            "fixes": gen_result["fixes"],
            "backend": gen_result["backend"],
            "attempts": gen_result["attempts"],
            "apk_filename": final_apk.name,
            "apk_size": final_apk.stat().st_size,
            "download_url": f"/api/download/{final_apk.name}",
        }

    except ValueError as e:
        tracker.emit("failed", 100, f"构建失败: 无效输入 {str(e)[:80]}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": f"Invalid input: {e}",
            "cdm": cdm_dict,
        }
    except Exception as e:
        # 脱敏: 客户端只收稳定文案 + request_id, 堆栈进服务端日志
        client_msg, request_id = safe_client_error(e, context=f"generate:{task_id}")
        tracker.emit("failed", 100, "构建失败(内部错误), 详见响应")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": client_msg,
            "cdm": cdm_dict,
        }


@router.websocket("/ws/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """WebSocket 实时推送生成进度"""
    await websocket.accept()

    # 发送已有历史
    history = _progress_store.get(task_id, [])
    for event in history:
        await websocket.send_json(event)

    # 如果已完成, 关闭连接
    if history and history[-1]["stage"] in ("done", "failed"):
        await websocket.close()
        return

    # 轮询新事件
    last_index = len(history)
    try:
        while True:
            await asyncio.sleep(0.5)
            events = _progress_store.get(task_id, [])
            while last_index < len(events):
                await websocket.send_json(events[last_index])
                last_index += 1

            if events and events[-1]["stage"] in ("done", "failed"):
                break
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
