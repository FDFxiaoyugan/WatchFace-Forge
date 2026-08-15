"""二维码路由 — 扫码安装 APK"""
import io
import base64
import qrcode
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path

from api.routes.build import APK_OUTPUT_DIR

router = APIRouter()


@router.get("/qrcode/{filename}")
async def get_qrcode(filename: str, base_url: str = "http://localhost:8000"):
    """生成 APK 下载二维码

    用法: GET /api/qrcode/xxx.apk?base_url=http://192.168.1.100:8000
    扫码后浏览器直接下载 APK
    """
    apk_path = APK_OUTPUT_DIR / filename
    if not apk_path.exists():
        raise HTTPException(status_code=404, detail="APK not found")

    download_url = f"{base_url}/api/download/{filename}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(download_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")
