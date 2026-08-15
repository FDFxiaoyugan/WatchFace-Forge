"""
WatchFace Forge — FastAPI 应用入口

Phase 1 端点:
  GET  /api/templates           — 列出 3 个固定模板
  GET  /api/templates/{id}      — 获取模板详情
  POST /api/compile             — CDM → WFF XML
  POST /api/build               — CDM → WFF XML → APK
  GET  /api/download/{task_id}  — 下载 APK
  GET  /api/health              — 健康检查
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from api.routes import templates, compile as compile_route, build, health, qrcode
from api.routes.error_handlers import validation_exception_handler, general_exception_handler

app = FastAPI(
    title="WatchFace Forge API",
    description="AI 驱动的 Wear OS 表盘生成平台",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 错误处理
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 路由
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(templates.router, prefix="/api", tags=["templates"])
app.include_router(compile_route.router, prefix="/api", tags=["compile"])
app.include_router(build.router, prefix="/api", tags=["build"])
app.include_router(qrcode.router, prefix="/api", tags=["qrcode"])


@app.get("/")
async def root():
    return {
        "name": "WatchFace Forge API",
        "version": "0.1.0",
        "phase": 1,
        "docs": "/docs",
    }
