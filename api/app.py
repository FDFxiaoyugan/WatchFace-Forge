"""
WatchFace Forge — FastAPI 应用入口

Phase 1 端点:
  GET  /api/templates           — 列出 3 个固定模板
  GET  /api/templates/{id}      — 获取模板详情
  POST /api/compile             — CDM → WFF XML
  POST /api/build               — CDM → WFF XML → APK
  GET  /api/download/{task_id}  — 下载 APK
  GET  /api/health              — 健康检查
Phase 3 新增端点:
  POST /api/editor/image/process — 图片异步处理 (抠图/裁剪/压缩)
  POST /api/editor/image/upload  — 图片同步快速处理
  GET  /api/editor/task/{id}     — 异步任务状态查询
  GET  /api/editor/cdm/{task_id} — 获取生成任务 CDM (编辑器导入)
  POST /api/editor/cdm/validate  — CDM 实时校验
  GET  /api/editor/queue/info    — Celery 队列拓扑
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from api.routes import templates, compile as compile_route, build, health, qrcode, generate, editor, wff
from api.routes.error_handlers import validation_exception_handler, general_exception_handler
from api.services.wff_access import WFFAPIError

app = FastAPI(
    title="WatchFace Forge API",
    description="AI 驱动的 Wear OS 表盘生成平台",
    version="0.1.0",
)

# CORS — 审计补充修复: "*" + credentials 组合会回显任意 Origin, 放大凭据泄露面。
# 规则: WF_CORS_ORIGINS 配置具体来源列表时启用 credentials; 否则 "*" 但禁用 credentials。
import os as _os

_cors_env = _os.getenv("WF_CORS_ORIGINS", "").strip()
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()] if _cors_env else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=bool(_cors_env),  # 仅显式配置来源列表时启用; "*" 模式必须为 False
    allow_methods=["*"],
    allow_headers=["*"],
)

# 错误处理
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.exception_handler(WFFAPIError)
async def wff_api_exception_handler(request: Request, exc: WFFAPIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )

# 路由
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(templates.router, prefix="/api", tags=["templates"])
app.include_router(compile_route.router, prefix="/api", tags=["compile"])
app.include_router(build.router, prefix="/api", tags=["build"])
app.include_router(qrcode.router, prefix="/api", tags=["qrcode"])
app.include_router(generate.router, prefix="/api", tags=["generate"])
app.include_router(editor.router, prefix="/api/editor", tags=["editor"])
app.include_router(wff.router, prefix="/api/v1/wff", tags=["wff-v1"])


@app.get("/")
async def root():
    return {
        "name": "WatchFace Forge API",
        "version": "0.1.0",
        "phase": 1,
        "docs": "/docs",
    }
