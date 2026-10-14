"""构建路由 — CDM → WFF XML → APK"""
import sys
import shutil
import base64
import io
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.models import BuildRequest, BuildResponse
from api.services.artifact_paths import (
    APK_OUTPUT_DIR,  # noqa: F401 — kept for historical imports in this repo
    final_apk_path,
    new_task_id,
    resolve_download_filename,
    task_id_dir,
)
from api.services.error_sanitize import safe_client_error

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "wff-builder"))

from compiler.wff.compiler import WFFCompiler
from wff_builder import WFFBuilder, validate_watchface_xml

router = APIRouter()


def _write_background_asset(project_dir: Path, background) -> None:
    """验证并将 CDM 图片背景转为 450x450 PNG APK 资源。"""
    if background.type != "image" or not background.image_data:
        return
    payload = background.image_data
    if "," in payload:
        header, payload = payload.split(",", 1)
        if not header.startswith("data:image/") or ";base64" not in header:
            raise ValueError("invalid background image data URL")
    try:
        raw = base64.b64decode(payload, validate=True)
    except Exception as exc:
        raise ValueError("invalid background image base64") from exc
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("background image too large (max 10MB)")

    from PIL import Image, ImageOps
    try:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGBA")
        image.load()
    except Exception as exc:
        raise ValueError(f"invalid background image: {exc}") from exc

    target = 450
    fit = background.image_fit
    if fit == "stretch":
        result = image.resize((target, target), Image.Resampling.LANCZOS)
    else:
        ratio = min(target / image.width, target / image.height) if fit == "contain" else max(target / image.width, target / image.height)
        resized = image.resize((max(1, round(image.width * ratio)), max(1, round(image.height * ratio))), Image.Resampling.LANCZOS)
        result = Image.new("RGBA", (target, target), (0, 0, 0, 0))
        result.alpha_composite(resized, ((target - resized.width) // 2, (target - resized.height) // 2))
    result.save(project_dir / "background.png", "PNG", optimize=True)
    background.image_resource = "background"


@router.post("/build", response_model=BuildResponse)
async def build_apk(req: BuildRequest):
    """CDM → WFF XML → APK 全流程构建"""
    # S5: server-generated id only; never derived from user input.
    task_id = new_task_id(8)

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

        # 3. 创建临时项目目录 (task_id 白名单校验, S5)
        project_dir = task_id_dir(task_id)
        project_dir.mkdir(exist_ok=True)

        # 4. 写入项目文件
        (project_dir / "watchface.xml").write_text(wff_xml, encoding="utf-8")

        # 5. 生成预览图
        _write_background_asset(project_dir, req.cdm.background)
        from api.services.preview_renderer import render_preview
        render_preview(project_dir / "preview.png", req.cdm)

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

        # 8. 复制到输出目录 (S5: 文件名仅来自服务端 task_id; 表盘名仅作展示字段)
        final_apk = final_apk_path(task_id)
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

    except ValueError as e:
        # 用户输入域错误 (图片解码/尺寸等), 消息来自受控校验代码, 无服务器细节
        return BuildResponse(
            task_id=task_id,
            status="failed",
            error=f"Invalid input: {e}",
        )
    except Exception as e:
        # 未分类异常: 客户端只收稳定错误码 + request_id, 完整堆栈进服务端日志
        client_msg, request_id = safe_client_error(e, context=f"build:{task_id}")
        return BuildResponse(
            task_id=task_id,
            status="failed",
            error=client_msg,
        )


@router.get("/download/{filename}")
async def download_apk(filename: str):
    """下载 APK 文件"""
    # S5: 白名单校验 + resolve 兜底, 拒绝 ../、绝对路径、盘符、URL 编码变体
    try:
        apk_path = resolve_download_filename(filename)
    except ValueError:
        raise HTTPException(status_code=404, detail="APK not found")
    if not apk_path.exists():
        raise HTTPException(status_code=404, detail="APK not found")

    return FileResponse(
        path=str(apk_path),
        media_type="application/vnd.android.package-archive",
        filename=filename,
    )
