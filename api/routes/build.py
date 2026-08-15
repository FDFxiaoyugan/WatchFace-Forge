"""构建路由 — CDM → WFF XML → APK"""
import sys
import uuid
import tempfile
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.models import BuildRequest, BuildResponse

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "wff-builder"))

from compiler.wff.compiler import WFFCompiler
from wff_builder import WFFBuilder, validate_watchface_xml

router = APIRouter()

# APK 输出目录
APK_OUTPUT_DIR = Path(tempfile.gettempdir()) / "watchface-forge-apks"
APK_OUTPUT_DIR.mkdir(exist_ok=True)


@router.post("/build", response_model=BuildResponse)
async def build_apk(req: BuildRequest):
    """CDM → WFF XML → APK 全流程构建"""
    task_id = str(uuid.uuid4())[:8]

    try:
        # 1. 编译 CDM → WFF XML
        compiler = WFFCompiler()
        wff_xml = compiler.compile(req.cdm)

        # 2. 校验
        failures = validate_watchface_xml(wff_xml)
        errors = [f for f in failures if f["severity"] == "error"]
        if errors:
            return BuildResponse(
                task_id=task_id,
                status="failed",
                error=f"Validation failed: {errors[0]['detail']}",
            )

        # 3. 创建临时项目目录
        project_dir = APK_OUTPUT_DIR / task_id
        project_dir.mkdir(exist_ok=True)

        # 4. 写入项目文件
        (project_dir / "watchface.xml").write_text(wff_xml, encoding="utf-8")

        # 5. 生成预览图 (临时占位)
        _generate_preview(project_dir / "preview.png", req.cdm)

        # 6. 写入 project.yaml
        import yaml
        config = {
            "package_name": req.cdm.metadata.package_name,
            "version_code": req.cdm.metadata.version_code,
            "version_name": req.cdm.metadata.version_name,
            "watch_face_name": req.cdm.metadata.name,
            "wff_version": 1,
        }
        (project_dir / "project.yaml").write_text(
            yaml.dump(config, default_flow_style=False)
        )

        # 7. 调用 wff-builder 构建
        builder = WFFBuilder(str(project_dir), verbose=False)
        apk_path = builder.build()

        # 8. 复制到输出目录
        final_apk = APK_OUTPUT_DIR / f"{req.cdm.metadata.package_name}-{task_id}.apk"
        shutil.copy2(apk_path, final_apk)

        # 9. 清理临时目录
        shutil.rmtree(project_dir, ignore_errors=True)

        return BuildResponse(
            task_id=task_id,
            status="success",
            apk_filename=final_apk.name,
            apk_size=final_apk.stat().st_size,
            download_url=f"/api/download/{final_apk.name}",
        )

    except Exception as e:
        return BuildResponse(
            task_id=task_id,
            status="failed",
            error=str(e),
        )


@router.get("/download/{filename}")
async def download_apk(filename: str):
    """下载 APK 文件"""
    apk_path = APK_OUTPUT_DIR / filename
    if not apk_path.exists():
        raise HTTPException(status_code=404, detail="APK not found")

    return FileResponse(
        path=str(apk_path),
        media_type="application/vnd.android.package-archive",
        filename=filename,
    )


def _generate_preview(path: Path, cdm):
    """生成预览图 (简单纯色圆形)"""
    from PIL import Image, ImageDraw

    size = 384
    img = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # 背景色
    bg_color = cdm.background.color if cdm.background.type != "image" else "#ff000000"
    # 解析 #ffRRGGBB
    bg_r = int(bg_color[2:4], 16)
    bg_g = int(bg_color[4:6], 16)
    bg_b = int(bg_color[6:8], 16)

    # 径向渐变
    cx, cy = size // 2, size // 2
    for r in range(size // 2, 0, -1):
        t = r / (size // 2)
        cr = int(bg_r * (1 - t) + 0 * t)
        cg = int(bg_g * (1 - t) + 0 * t)
        cb = int(bg_b * (1 - t) + 0 * t)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(cr, cg, cb, 255))

    # 时间颜色文字
    time_color = cdm.digital_time.font.color if cdm.digital_time.enabled else "#ffffffff"
    tr = int(time_color[2:4], 16)
    tg = int(time_color[4:6], 16)
    tb = int(time_color[6:8], 16)

    try:
        from PIL import ImageFont
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/chinese/NotoSansSC-Bold.otf", 60
        )
    except Exception:
        font = ImageFont.load_default()

    draw.text((size // 2 - 60, size // 2 - 30), "10:08",
              fill=(tr, tg, tb, 255), font=font)

    img.save(path, "PNG", optimize=True)
