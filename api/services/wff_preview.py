"""Small deterministic WFF XML renderer for API previews (not a device emulator)."""

import base64
import io
import re
from datetime import datetime
from pathlib import Path
from typing import Dict
from xml.etree import ElementTree as ET

from PIL import Image, ImageColor, ImageDraw, ImageFont


def _color(value: str, fallback: str = "#000000") -> tuple:
    value = value or fallback
    if re.fullmatch(r"#[0-9a-fA-F]{8}", value):
        aa, rr, gg, bb = value[1:3], value[3:5], value[5:7], value[7:9]
        return int(rr, 16), int(gg, 16), int(bb, 16), int(aa, 16)
    try:
        return ImageColor.getcolor(value, "RGBA")
    except ValueError:
        return ImageColor.getcolor(fallback, "RGBA")


def _number(node: ET.Element, name: str, default: float) -> float:
    try:
        return float(node.get(name, default))
    except (TypeError, ValueError):
        return default


def _font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, max(8, size))
    return ImageFont.load_default()


def _format_time(pattern: str, moment: datetime) -> str:
    result = pattern or "HH:mm"
    for token, value in (
        ("HH", f"{moment.hour:02d}"), ("hh", f"{(moment.hour - 1) % 12 + 1:02d}"),
        ("mm", f"{moment.minute:02d}"), ("ss", f"{moment.second:02d}"),
    ):
        result = result.replace(token, value)
    return result


def _template_text(template: ET.Element, moment: datetime) -> str:
    values = {
        "MONTH": str(moment.month), "DAY": str(moment.day), "DAY_Z": f"{moment.day:02d}",
        "YEAR": str(moment.year), "BATTERY_PERCENT": "85", "HEART_RATE": "72",
    }
    text = (template.text or "").strip()
    for parameter in template.findall(".//Parameter"):
        expression = (parameter.get("expression") or "").strip("[]")
        text = text.replace("%s", values.get(expression, "--"), 1)
    return text


def render_wff_frame(xml_text: str, assets: Dict[str, bytes], moment: datetime, mode: str, shape: str, size: int) -> bytes:
    root = ET.fromstring(xml_text)
    design_w = max(1.0, _number(root, "width", 450))
    design_h = max(1.0, _number(root, "height", 450))
    scene = root.find("Scene")
    background = _color(scene.get("backgroundColor") if scene is not None else "#ff000000")
    image = Image.new("RGBA", (size, size), background)
    draw = ImageDraw.Draw(image)
    sx, sy = size / design_w, size / design_h

    if scene is not None:
        for node in scene.iter():
            if node.tag in {"PartImage", "Image"}:
                resource = (node.get("resource") or node.get("source") or "").split("/")[-1]
                raw = assets.get(resource) or assets.get(resource + ".png") or assets.get(resource + ".jpg")
                if raw:
                    try:
                        layer = Image.open(io.BytesIO(raw)).convert("RGBA")
                        box = (int(_number(node, "x", 0) * sx), int(_number(node, "y", 0) * sy),
                               max(1, int(_number(node, "width", design_w) * sx)), max(1, int(_number(node, "height", design_h) * sy)))
                        image.alpha_composite(layer.resize((box[2], box[3])), (box[0], box[1]))
                    except Exception:
                        pass
            elif node.tag == "DrawOval":
                x, y = _number(node, "x", 0) * sx, _number(node, "y", 0) * sy
                w, h = _number(node, "width", design_w) * sx, _number(node, "height", design_h) * sy
                draw.ellipse((x, y, x + w, y + h), fill=_color(node.get("color", "#ffffffff")))
            elif node.tag == "TimeText":
                _draw_text(draw, node, _format_time(node.get("format", "HH:mm"), moment), sx, sy, mode)
            elif node.tag == "Text":
                template = node.find(".//Template")
                if template is not None:
                    parent = node
                    _draw_text(draw, parent, _template_text(template, moment), sx, sy, mode)

    if shape == "round":
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
        image.putalpha(Image.composite(image.getchannel("A"), mask, mask))
    output = io.BytesIO()
    image.save(output, "PNG", optimize=True)
    return output.getvalue()


def _draw_text(draw: ImageDraw.ImageDraw, node: ET.Element, text: str, sx: float, sy: float, mode: str) -> None:
    if mode == "ambient" and any(v.get("mode") == "AMBIENT" and v.get("target") == "alpha" and v.get("value") == "0" for v in node.findall(".//Variant")):
        return
    font_node = node.find(".//Font")
    if font_node is None:
        return
    x, y = _number(node, "x", 0) * sx, _number(node, "y", 0) * sy
    width = _number(node, "width", 450) * sx
    font = _font(int(_number(font_node, "size", 40) * min(sx, sy)))
    fill = _color(font_node.get("color", "#ffffffff"))
    bbox = draw.textbbox((0, 0), text, font=font)
    align = node.get("align", "CENTER").upper()
    tx = x + (width - (bbox[2] - bbox[0])) / 2 if align == "CENTER" else x
    if align == "RIGHT":
        tx = x + width - (bbox[2] - bbox[0])
    draw.text((tx, y), text, font=font, fill=fill)


def frame_data_url(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")
