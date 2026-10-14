"""API 异常处理 — 统一错误响应格式"""
import logging
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from api.services.error_sanitize import safe_client_error

logger = logging.getLogger("watchface_forge.errors")


async def validation_exception_handler(request: Request, exc):
    """处理 Pydantic 校验错误 (422)"""
    errors = []
    if hasattr(exc, "errors"):
        for err in exc.errors():
            loc = ".".join(str(l) for l in err.get("loc", []) if l != "body")
            errors.append({
                "field": loc,
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            })
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error_type": "validation_error",
            "errors": errors,
            "message": "请求参数校验失败",
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获异常 (500) — 不向客户端泄露内部异常细节"""
    client_msg, request_id = safe_client_error(exc, context=f"request:{request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_type": "internal_error",
            "request_id": request_id,
            "message": client_msg,
        },
    )
