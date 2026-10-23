"""
Editor 路由 — Phase 3 可视化编辑器后端

POST /api/editor/image/process   — 上传图片并异步处理 (返回 celery task_id)
GET  /api/editor/task/{id}       — 查询异步任务结果
GET  /api/editor/cdm/{task_id}   — 获取生成任务的 CDM (导入编辑器)
POST /api/editor/cdm/validate    — 校验 CDM 合法性
GET  /api/editor/queue/info      — 队列拓扑信息
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "wff-builder"))

router = APIRouter()

# 导入生成路由的存储, 复用 CDM 查询
from api.routes.generate import _progress_store


# ─── 请求/响应模型 ────────────────────────────────────

class ImageProcessRequest(BaseModel):
    # 复查 G3: b64 限长 ~14M 字符（≈10.5MB 原始字节），防超大 JSON 内存放大
    image_b64: str = Field(min_length=8, max_length=14_000_000)
    remove_bg: bool = True
    bg_tolerance: int = 32
    feather_radius: int = 2
    auto_crop: bool = True
    max_size: int = 1024
    output_format: str = "png"


class CDMValidateRequest(BaseModel):
    cdm: dict


class CDMValidateResponse(BaseModel):
    valid: bool
    errors: list = []
    warnings: list = []


# ─── 图片处理 (异步) ──────────────────────────────────

@router.post("/image/process")
async def process_image(req: ImageProcessRequest,
                        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    """提交图片处理任务到 Celery image 队列"""
    # 复查 G3: 匿名滥用防线——production fail-closed / dev 匿名走开发身份+配额
    from api.services.quota import authorize_and_consume
    authorize_and_consume(x_api_key, "image")
    try:
        from api.tasks.tasks import process_image_task
        options = {
            "remove_bg": req.remove_bg,
            "bg_tolerance": req.bg_tolerance,
            "feather_radius": req.feather_radius,
            "auto_crop": req.auto_crop,
            "max_size": req.max_size,
            "output_format": req.output_format,
        }
        async_result = process_image_task.delay(req.image_b64, options)
        return {"success": True, "task_id": async_result.id, "queue": "image"}
    except Exception:
        # celery 不可用/broker 掉线/导入失败 → 降级为同步处理
        # (kombu OperationalError / ConnectionRefusedError / ImportError 统一走此路径)
        from starlette.concurrency import run_in_threadpool
        from api.services.image.processor import ProcessOptions, process_image
        try:
            raw = base64.b64decode(req.image_b64)
            opts = ProcessOptions(
                remove_bg=req.remove_bg,
                bg_tolerance=req.bg_tolerance,
                feather_radius=req.feather_radius,
                auto_crop=req.auto_crop,
                max_size=req.max_size,
                output_format=req.output_format,
            )
            # 复查 G1b: 同步重活不占事件循环
            result = await run_in_threadpool(process_image, raw, opts)
            if not result.success:
                raise HTTPException(400, result.error)
            return {
                "success": True,
                "task_id": None,
                "sync": True,
                "image_b64": base64.b64encode(result.data).decode(),
                "format": result.format,
                "width": result.width,
                "height": result.height,
                "original_size": result.original_size,
                "processed_size": result.processed_size,
                "bg_removed": result.bg_removed,
                "cropped": result.cropped,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"image process failed: {e}")


@router.post("/image/upload")
async def upload_image(
    file: UploadFile = File(...),
    remove_bg: bool = Form(True),
    auto_crop: bool = Form(True),
    max_size: int = Form(1024),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    """multipart 文件上传 → 处理 (同步, 用于小图快速路径)"""
    # 复查 G3: 匿名滥用防线（同 image/process）
    from api.services.quota import authorize_and_consume
    from starlette.concurrency import run_in_threadpool
    from api.services.image.processor import ProcessOptions, process_image
    authorize_and_consume(x_api_key, "image")

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(400, f"not an image: {file.content_type}")

    # 复查 G3: 分块读 + 累计上限——不再 await file.read() 一次性拉全量 body
    # (原实现先完整读入内存再查 10MB, 内存峰值=完整文件)
    limit = 10 * 1024 * 1024
    chunks, total = [], 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise HTTPException(400, "image too large (max 10MB)")
        chunks.append(chunk)
    raw = b"".join(chunks)

    opts = ProcessOptions(remove_bg=remove_bg, auto_crop=auto_crop, max_size=max_size)
    result = await run_in_threadpool(process_image, raw, opts)
    if not result.success:
        raise HTTPException(400, result.error)

    return {
        "success": True,
        "image_b64": base64.b64encode(result.data).decode(),
        "format": result.format,
        "width": result.width,
        "height": result.height,
        "original_size": result.original_size,
        "processed_size": result.processed_size,
        "bg_removed": result.bg_removed,
        "cropped": result.cropped,
    }


# ─── 异步任务状态 ─────────────────────────────────────

@router.get("/task/{task_id}")
async def get_task_result(task_id: str):
    """查询 Celery 任务结果"""
    try:
        from api.tasks.tasks import process_image_task, build_apk_task
    except ImportError:
        raise HTTPException(503, "celery not available")

    # 依次尝试两种任务
    for task_fn in (process_image_task, build_apk_task):
        result = task_fn.AsyncResult(task_id)
        if result is None:
            continue
        state = result.state
        response = {"task_id": task_id, "state": state}
        if state == "SUCCESS":
            response["result"] = result.result
        elif state == "FAILURE":
            # 脱敏: 异常细节只进日志, 客户端收稳定文案 + request_id
            from api.services.error_sanitize import safe_client_error
            client_msg, request_id = safe_client_error(result.result, context=f"editor-task:{task_id}")
            response["error"] = client_msg
            response["request_id"] = request_id
        return response

    raise HTTPException(404, "task not found")


@router.get("/queue/info")
async def queue_info():
    """队列拓扑信息"""
    try:
        from api.tasks.celery_app import get_queue_info
        return {"success": True, **get_queue_info()}
    except ImportError:
        return {"success": False, "celery_available": False}


# ─── CDM 读取/校验 ────────────────────────────────────

@router.get("/cdm/{task_id}")
async def get_cdm(task_id: str,
                  x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    """获取生成任务的 CDM (编辑器导入用)

    优先从 cdm_store（Redis TTL 1h, 生成即存）读取；退化为内存进度事件。

    复查 G2 (2026-10-23): 读取端纳入鉴权/配额（cdm_read 60/h；
    production fail-closed、dev 匿名走固定开发身份）；存档带 ``_owner``
    时校验所有权——key 不匹配 → 404（不泄漏存在性），响应剥离内部字段。
    """
    from api.services.quota import authorize_and_consume, owner_digest
    from api.services.cdm_store import load_cdm

    identity = authorize_and_consume(x_api_key, "cdm_read")
    digest = owner_digest(identity)

    def _owned(cdm: Optional[dict]) -> Optional[dict]:
        if cdm is None:
            return None
        owner = cdm.pop("_owner", None)
        if owner is not None and owner != digest:
            # 所有权不匹配 → 与不存在同语义, 不泄漏该 task_id 归属
            return None
        return cdm

    cdm = _owned(load_cdm(task_id))
    if cdm:
        return {"success": True, "task_id": task_id, "cdm": cdm}
    events = _progress_store.get(task_id, [])
    for event in reversed(events):
        cdm = event.get("data", {}).get("cdm") if isinstance(event.get("data"), dict) else None
        cdm = _owned(cdm)
        if cdm:
            return {"success": True, "task_id": task_id, "cdm": cdm}
    raise HTTPException(404, f"CDM not found for task {task_id}")


@router.post("/cdm/validate", response_model=CDMValidateResponse)
async def validate_cdm(req: CDMValidateRequest):
    """校验 CDM (编辑器实时校验 + 导出前校验)"""
    from schema.cdm.models import WatchFaceCDM, ClockType
    from pydantic import ValidationError

    errors, warnings = [], []
    try:
        cdm = WatchFaceCDM(**req.cdm)
    except ValidationError as e:
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            errors.append(f"{loc}: {err['msg']}")
        return CDMValidateResponse(valid=False, errors=errors, warnings=warnings)

    # 语义级 warning
    if cdm.clock_type == ClockType.ANALOG and cdm.analog_time.enabled:
        if cdm.analog_time.hour_hand_length > cdm.analog_time.minute_hand_length:
            warnings.append("时针长度大于分针, 视觉上可能违和")
    if cdm.clock_type == ClockType.DIGITAL and cdm.digital_time.enabled:
        if cdm.digital_time.font.size > 120:
            warnings.append("数字时间字号超过 120, 可能超出画布")
    if len(cdm.complications) > 4:
        warnings.append("complications 超过 4 个, WFF 最多支持 4 个")

    return CDMValidateResponse(valid=len(errors) == 0, errors=errors, warnings=warnings)
