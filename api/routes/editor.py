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

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "wff-builder"))

router = APIRouter()

# 导入生成路由的存储, 复用 CDM 查询
from api.routes.generate import _progress_store


# ─── 请求/响应模型 ────────────────────────────────────

class ImageProcessRequest(BaseModel):
    image_b64: str
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
async def process_image(req: ImageProcessRequest):
    """提交图片处理任务到 Celery image 队列"""
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
    except ImportError:
        # celery/redis 不可用时降级为同步处理
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
            result = process_image(raw, opts)
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
    except Exception as e:
        raise HTTPException(500, f"submit failed: {e}")


@router.post("/image/upload")
async def upload_image(
    file: UploadFile = File(...),
    remove_bg: bool = Form(True),
    auto_crop: bool = Form(True),
    max_size: int = Form(1024),
):
    """multipart 文件上传 → 处理 (同步, 用于小图快速路径)"""
    from api.services.image.processor import ProcessOptions, process_image

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(400, f"not an image: {file.content_type}")

    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(400, "image too large (max 10MB)")

    opts = ProcessOptions(remove_bg=remove_bg, auto_crop=auto_crop, max_size=max_size)
    result = process_image(raw, opts)
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
            response["error"] = str(result.result)[:500]
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
async def get_cdm(task_id: str):
    """获取生成任务的 CDM (编辑器导入用)"""
    events = _progress_store.get(task_id, [])
    for event in reversed(events):
        cdm = event.get("data", {}).get("cdm") if isinstance(event.get("data"), dict) else None
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
    if cdm.clock_type == ClockType.ANALOG and not cdm.analog_time.hands:
        warnings.append("ANALOG 表盘未配置表针")
    if cdm.clock_type == ClockType.DIGITAL and cdm.digital_time.enabled:
        if cdm.digital_time.font.size > 120:
            warnings.append("数字时间字号超过 120, 可能超出画布")
    if len(cdm.complications) > 4:
        warnings.append("complications 超过 4 个, WFF 最多支持 4 个")

    return CDMValidateResponse(valid=len(errors) == 0, errors=errors, warnings=warnings)
