"""健康检查路由"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "watchface-forge-api",
        "phase": 1,
    }
