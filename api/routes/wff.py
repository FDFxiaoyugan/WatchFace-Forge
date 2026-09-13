"""Versioned direct WFF APIs used by agents and external CI clients."""

import hashlib
import json
import re
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import APIRouter, File, Form, Header, UploadFile
from fastapi.responses import FileResponse

from api.services.wff_access import WFFAPIError, authorize
from api.services.wff_preview import frame_data_url, render_wff_frame
from api.services.wff_official import evaluate_memory
from api.services.wff_validation import MAX_ASSET_BYTES, MAX_XML_BYTES, validate_wff

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "wff-builder"))
from wff_builder import WFFBuilder  # noqa: E402

router = APIRouter()
OUTPUT_DIR = Path("/tmp/watchface-forge-apks")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def _read_assets(assets: List[UploadFile]) -> List[Tuple[str, bytes]]:
    result = []
    for asset in assets:
        name = asset.filename or "asset"
        result.append((name, await _read_upload_limited(asset, MAX_ASSET_BYTES, f"资源 {name}")))
    return result


async def _read_upload_limited(upload: UploadFile, limit: int, label: str) -> bytes:
    """Read a spooled upload incrementally and stop as soon as its limit is exceeded."""
    chunks = []
    total = 0
    while True:
        chunk = await upload.read(min(1024 * 1024, limit - total + 1))
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise WFFAPIError(422, "VALIDATION_FAILED", f"{label}超过 {limit // (1024 * 1024)}MB 限制")
        chunks.append(chunk)
    return b"".join(chunks)


async def _read_request_files(
    xml: Optional[UploadFile],
    assets: List[UploadFile],
    bracket_assets: List[UploadFile],
) -> Tuple[bytes, List[Tuple[str, bytes]]]:
    """Read multipart files and enforce request-level contract limits."""
    if xml is None:
        raise WFFAPIError(422, "VALIDATION_FAILED", "缺少必填的 xml 文件")
    xml_bytes = await _read_upload_limited(xml, MAX_XML_BYTES, "xml 文件")
    asset_list = await _read_assets([*assets, *bracket_assets])
    return xml_bytes, asset_list


def _parse_list(value: str, field: str, limit: int) -> list:
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        raise WFFAPIError(422, "INVALID_PREVIEW_OPTIONS", f"{field} 必须是 JSON 数组字符串")
    if not isinstance(parsed, list) or not parsed:
        raise WFFAPIError(422, "INVALID_PREVIEW_OPTIONS", f"{field} 必须是非空 JSON 数组")
    if len(parsed) > limit:
        raise WFFAPIError(422, "INVALID_PREVIEW_OPTIONS", f"{field} 最多允许 {limit} 项")
    return parsed


@router.post("/validate")
async def validate_endpoint(
    xml: Optional[UploadFile] = File(default=None),
    assets: List[UploadFile] = File(default=[]),
    bracket_assets: List[UploadFile] = File(default=[], alias="assets[]"),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    authorize(x_api_key, "validate", 60)
    xml_bytes, asset_list = await _read_request_files(xml, assets, bracket_assets)
    return validate_wff(xml_bytes, asset_list)


@router.post("/preview")
async def preview_endpoint(
    xml: Optional[UploadFile] = File(default=None),
    assets: List[UploadFile] = File(default=[]),
    bracket_assets: List[UploadFile] = File(default=[], alias="assets[]"),
    times: str = Form(default='["10:08:32"]'),
    modes: str = Form(default='["active"]'),
    shape: str = Form(default="round"),
    size: int = Form(default=384),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    authorize(x_api_key, "preview", 20)
    if shape not in {"round", "square"} or size < 128 or size > 1024:
        raise WFFAPIError(422, "INVALID_PREVIEW_OPTIONS", "shape 仅支持 round/square，size 范围为 128-1024")
    xml_bytes, asset_list = await _read_request_files(xml, assets, bracket_assets)
    validation = validate_wff(xml_bytes, asset_list)
    if not validation["valid"]:
        raise WFFAPIError(422, "VALIDATION_FAILED", "WFF XML 未通过校验，无法生成预览")
    xml_text = xml_bytes.decode("utf-8")
    assets_by_name = {name: data for name, data in asset_list}
    time_values = _parse_list(times, "times", 6)
    mode_values = _parse_list(modes, "modes", 2)
    moments = []
    for time_value in time_values:
        try:
            moment = datetime.strptime(str(time_value), "%H:%M:%S").replace(year=2026, month=8, day=24)
        except ValueError:
            raise WFFAPIError(422, "INVALID_TIME", f"无效预览时间：{time_value}")
        moments.append((time_value, moment))
    for mode in mode_values:
        if mode not in {"active", "ambient"}:
            raise WFFAPIError(422, "INVALID_MODE", f"无效模式：{mode}")

    frames = []
    for time_value, moment in moments:
        for mode in mode_values:
            png = render_wff_frame(xml_text, assets_by_name, moment, mode, shape, size)
            frames.append({"time": time_value, "mode": mode, "image": frame_data_url(png)})
    return {"frames": frames, "warnings": ["预览为近似渲染，不代表 Wear OS 设备最终效果"]}


@router.post("/build")
async def build_endpoint(
    xml: Optional[UploadFile] = File(default=None),
    assets: List[UploadFile] = File(default=[]),
    bracket_assets: List[UploadFile] = File(default=[], alias="assets[]"),
    name: str = Form(default="WFF Watch Face"),
    package: str = Form(default="com.watchfaceforge.generated"),
    version: int = Form(default=1),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    authorize(x_api_key, "build", 10)
    if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", package):
        raise WFFAPIError(422, "INVALID_PACKAGE", "package 必须是合法的小写 Android 包名")
    if version < 1:
        raise WFFAPIError(422, "INVALID_VERSION", "version 必须大于 0")
    xml_bytes, asset_list = await _read_request_files(xml, assets, bracket_assets)
    validation = validate_wff(xml_bytes, asset_list)
    if not validation["valid"]:
        raise WFFAPIError(422, "VALIDATION_FAILED", "WFF XML 未通过校验，构建已拒绝")

    build_id = uuid.uuid4().hex[:12]
    project_dir = OUTPUT_DIR / ("wff-" + build_id)
    project_dir.mkdir(parents=True)
    warnings = []
    try:
        xml_text = xml_bytes.decode("utf-8")
        asset_map = {filename: data for filename, data in asset_list}
        preview = render_wff_frame(xml_text, asset_map, datetime(2026, 8, 24, 10, 8, 32), "active", "round", 384)
        (project_dir / "preview.png").write_bytes(preview)
        # 2026-09-13: qemu-user + aapt2 + JDK17 全工具链就绪, 切换多资源标准打包
        # (替代旧 "ARM 预编译模板" 仅打包首个图片当 background 的降级实现)。
        drawable_dir = project_dir / "res" / "drawable"
        for filename, data in asset_list:
            if Path(filename).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            if len(data) > MAX_ASSET_BYTES:
                raise WFFAPIError(422, "ASSET_TOO_LARGE", f"资源 {filename} 超过 10MB")
            if Path(filename).stem == "preview":
                continue  # preview 由上方单独渲染, 不进 APK
            drawable_dir.mkdir(parents=True, exist_ok=True)
            (drawable_dir / Path(filename).name).write_bytes(data)
        (project_dir / "watchface.xml").write_text(xml_text, encoding="utf-8")
        safe_name = name.replace("\n", " ").replace("\r", " ")[:80]
        (project_dir / "project.yaml").write_text(
            f'package_name: {package}\nversion_code: {version}\nversion_name: "{version}.0"\nwatch_face_name: "{safe_name}"\nwff_version: 1\n',
            encoding="utf-8",
        )
        apk_path = WFFBuilder(str(project_dir), verbose=False).build()
        filename = f"{package.rsplit('.', 1)[-1]}-{build_id}.apk"
        final_path = OUTPUT_DIR / filename
        shutil.copy2(apk_path, final_path)
    except WFFAPIError:
        raise
    except Exception as exc:
        raise WFFAPIError(500, "BUILD_FAILED", str(exc))
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)

    sha256 = hashlib.sha256(final_path.read_bytes()).hexdigest()
    memory = evaluate_memory(final_path, version=1)
    if memory.get("warning"):
        warnings.append(memory["warning"])
    return {
        "build_id": build_id,
        "apk": {"url": f"/api/v1/wff/builds/{filename}", "size": final_path.stat().st_size, "sha256": sha256},
        "qr_url": f"/api/qrcode/{filename}",
        "memory": memory,
        "warnings": warnings,
    }


@router.get("/builds/{filename}")
async def download_build(filename: str):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.apk", filename):
        raise WFFAPIError(404, "BUILD_NOT_FOUND", "构建产物不存在")
    path = OUTPUT_DIR / filename
    if not path.is_file():
        raise WFFAPIError(404, "BUILD_NOT_FOUND", "构建产物不存在")
    return FileResponse(str(path), media_type="application/vnd.android.package-archive", filename=filename)
