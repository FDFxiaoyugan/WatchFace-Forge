"""Layered validation and resource statistics for uploaded WFF XML."""

import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
from xml.etree import ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "wff-builder"))

from wff_builder import validate_watchface_xml  # noqa: E402
from api.services.wff_official import validate_with_official_tool

MAX_XML_BYTES = 2 * 1024 * 1024
MAX_ASSET_BYTES = 10 * 1024 * 1024
OFFICIAL_XSD = PROJECT_ROOT / "vendor" / "google-watchface" / "specification" / "1" / "watchface.xsd"


def _issue(source: str, rule: str, severity: str, message: str, hint: str = "", element: Optional[str] = None, line: Optional[int] = None) -> dict:
    return {
        "source": source,
        "rule": rule,
        "severity": severity,
        "element": element,
        "line": line,
        "message": message,
        "hint": hint,
    }


def validate_wff(xml_bytes: bytes, assets: Iterable[Tuple[str, bytes]]) -> dict:
    if len(xml_bytes) > MAX_XML_BYTES:
        return _result([_issue("xsd", "XML_SIZE", "error", "XML 超过 2MB 限制", "精简 XML 后重试")], None, assets)
    try:
        xml_text = xml_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return _result([_issue("xsd", "XML_ENCODING", "error", "XML 必须使用 UTF-8 编码")], None, assets)

    issues: List[dict] = []
    root = None
    try:
        root = ET.fromstring(xml_text)
        if root.tag != "WatchFace":
            issues.append(_issue("xsd", "ROOT_ELEMENT", "error", "根元素必须是 WatchFace", "将根元素改为 <WatchFace>", root.tag))
    except ET.ParseError as exc:
        line = exc.position[0] if getattr(exc, "position", None) else None
        issues.append(_issue("xsd", "XML_WELL_FORMED", "error", f"XML 语法错误：{exc}", "修正标签闭合或属性格式", line=line))
        return _result(issues, None, assets)

    issues.extend(_validate_official_xsd(xml_bytes))
    issues.extend(validate_with_official_tool(xml_bytes, version=1))

    for failure in validate_watchface_xml(xml_text):
        issues.append(_issue(
            "lint",
            failure["rule_id"],
            "warning" if failure["severity"] == "warn" else "error",
            failure["detail"],
            failure["fix"],
        ))

    referenced = set(re.findall(r'(?:resource|source)="(?:drawable|font)/([^"/]+)"', xml_text))
    asset_list = list(assets)
    available = {Path(name).stem for name, _ in asset_list}
    for missing in sorted(referenced - available):
        issues.append(_issue("lint", "ASSET_MISSING", "error", f"缺少资源：{missing}", "在 assets[] 中上传同名图片或字体"))
    for name, data in asset_list:
        if len(data) > MAX_ASSET_BYTES:
            issues.append(_issue("lint", "ASSET_SIZE", "error", f"资源 {name} 超过 10MB", "压缩资源后重试"))

    return _result(issues, root, asset_list)


def _validate_official_xsd(xml_bytes: bytes) -> List[dict]:
    """Validate against Google's vendored XSD 1.1 tree without network access."""
    if not OFFICIAL_XSD.is_file():
        return [_issue(
            "xsd", "XSD_UNAVAILABLE", "warning",
            "Google 官方 WFF XSD 校验器当前不可用",
            "确认 vendor/google-watchface/specification/1 已部署",
        )]
    try:
        schema = _official_schema()
    except ImportError:
        return [_issue("xsd", "XSD_UNAVAILABLE", "warning", "缺少 XSD 1.1 运行库 xmlschema", "安装 requirements.txt")]
    except Exception as exc:
        return [_issue("xsd", "XSD_UNAVAILABLE", "warning", f"Google WFF schema 初始化失败：{exc}")]

    result = []
    for error in schema.iter_errors(xml_bytes):
        line = getattr(getattr(error, "elem", None), "sourceline", None)
        result.append(_issue(
            "xsd", "OFFICIAL_XSD", "error", str(error.reason or error),
            "按 Google WFF v1 schema 修正元素、属性或顺序",
            element=getattr(error, "path", None), line=line,
        ))
    return result


@lru_cache(maxsize=1)
def _official_schema():
    import xmlschema
    return xmlschema.XMLSchema11(str(OFFICIAL_XSD), allow="local")


def _result(issues: List[dict], root: Optional[ET.Element], assets: Iterable[Tuple[str, bytes]]) -> dict:
    asset_list = list(assets)
    elements = list(root.iter()) if root is not None else []
    image_count = sum(1 for node in elements if node.tag in {"PartImage", "Image"})
    font_count = sum(1 for node in elements if node.tag == "Font")
    asset_bytes = sum(len(data) for _, data in asset_list)
    # Conservative platform estimate until the official evaluator is vendored.
    estimated_memory = asset_bytes + image_count * 64 * 1024 + font_count * 16 * 1024
    return {
        "valid": not any(item["severity"] == "error" for item in issues),
        "errors": issues,
        "stats": {
            "element_count": len(elements),
            "image_count": image_count,
            "font_count": font_count,
            "asset_kb": round(asset_bytes / 1024, 2),
            "estimated_memory_kb": round(estimated_memory / 1024, 2),
            "memory_source": "estimate",
        },
    }
