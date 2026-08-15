"""
CDM Generator — 自然语言 → CDM JSON

使用 LLM (z-ai / GPT-4o) 解析用户提示词, 生成合法 CDM JSON。
包含自动修复层: 如果 LLM 输出不符合 CDM Schema, 尝试修复。
"""

import json
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from schema.cdm.models import WatchFaceCDM, ClockType, FontWeight, DataSource
from services.ai_gateway import AIGateway, check_rate_limit, record_request

# ─── 提示词工程 ────────────────────────────────────────

SYSTEM_PROMPT = """You are a watch face design assistant. You convert natural language descriptions into CDM (Canonical Data Model) JSON for Wear OS watch faces.

Output ONLY valid JSON, no markdown, no explanation.

CDM Schema rules:
- All colors MUST be 8-digit ARGB hex: #ffRRGGBB (e.g. #ff00F5FF for cyan)
- clock_type: "DIGITAL" or "ANALOG"
- Font weight: "THIN", "NORMAL", or "BOLD"
- Data sources: "HOUR_0_23", "HOUR_1_12", "MINUTE_Z", "SECOND_Z", "DAY", "DAY_Z", "DAY_OF_WEEK_S", "MONTH", "MONTH_S", "YEAR", "BATTERY_PERCENT", "HEART_RATE"
- Canvas is 450x450 pixels
- Background color format: #ffRRGGBB

Example output:
{
  "metadata": {
    "name": "My Watch Face",
    "package_name": "com.user.mywatch",
    "version_code": 1,
    "version_name": "1.0"
  },
  "clock_type": "DIGITAL",
  "background": {
    "type": "solid",
    "color": "#ff0a0e1a"
  },
  "digital_time": {
    "enabled": true,
    "format": "HH:mm",
    "position": {"x": 0, "y": 120, "width": 450, "height": 120},
    "font": {"family": "SYNC_TO_DEVICE", "size": 100, "weight": "BOLD", "color": "#ff00F5FF"},
    "ambient_color": "#ff888888"
  },
  "date_display": {
    "enabled": true,
    "format": "%s/%s",
    "params": ["MONTH", "DAY"],
    "position": {"x": 0, "y": 260, "width": 450, "height": 50},
    "font": {"family": "SYNC_TO_DEVICE", "size": 30, "color": "#ffAAAAAA"}
  },
  "info_line": {
    "enabled": true,
    "label": "BAT",
    "data_source": "BATTERY_PERCENT",
    "suffix": "%%",
    "position": {"x": 0, "y": 320, "width": 450, "height": 50},
    "font": {"family": "SYNC_TO_DEVICE", "size": 26, "color": "#ffFF6B6B"}
  }
}"""

USER_PROMPT_TEMPLATE = """Create a watch face design for: "{prompt}"

Requirements:
- Generate a creative name and package_name (com.watchfaceforge.xxx)
- Choose appropriate colors that match the description
- Set suitable font sizes for a 450x450 circular display
- Include date and battery info
- Use SYNC_TO_DEVICE font family
- All colors must be 8-digit ARGB (#ffRRGGBB)"""


# ─── 自动修复 ──────────────────────────────────────────

def fix_cdm(cdm_dict: dict) -> tuple[dict, list[str]]:
    """尝试修复 CDM JSON 中的常见问题, 返回 (修复后的 CDM, 修复列表)"""
    fixes = []

    # 1. 修复 6 位颜色 → 8 位 ARGB
    def fix_color(obj, key):
        val = obj.get(key, "")
        if isinstance(val, str) and val.startswith("#") and len(val) == 7:
            obj[key] = "#ff" + val[1:]
            fixes.append(f"Fixed {key}: {val} → {obj[key]}")

    fix_color(cdm_dict.get("background", {}), "color")

    digital = cdm_dict.get("digital_time", {})
    if digital.get("font"):
        fix_color(digital["font"], "color")
    fix_color(digital, "ambient_color")

    date = cdm_dict.get("date_display", {})
    if date.get("font"):
        fix_color(date["font"], "color")

    info = cdm_dict.get("info_line", {})
    if info.get("font"):
        fix_color(info["font"], "color")

    analog = cdm_dict.get("analog_time", {})
    for k in ["hour_hand_color", "minute_hand_color", "second_hand_color"]:
        fix_color(analog, k)

    # 2. 确保必要字段存在
    if "metadata" not in cdm_dict:
        cdm_dict["metadata"] = {}
        fixes.append("Added missing metadata")

    meta = cdm_dict["metadata"]
    if not meta.get("name") or meta["name"] == "":
        meta["name"] = "AI Generated"
        fixes.append("Added default name")
    if not meta.get("package_name"):
        pkg = "com.watchfaceforge." + meta.get("name", "generated").lower().replace(" ", "")
        meta["package_name"] = pkg
        fixes.append(f"Added default package_name: {pkg}")
    if not meta.get("version_code"):
        meta["version_code"] = 1
    if not meta.get("version_name"):
        meta["version_name"] = "1.0"

    # 3. 确保 clock_type 合法
    if cdm_dict.get("clock_type") not in ["DIGITAL", "ANALOG"]:
        cdm_dict["clock_type"] = "DIGITAL"
        fixes.append("Set default clock_type to DIGITAL")

    # 3.5 修复 weight 大小写
    valid_weights = {"THIN", "NORMAL", "BOLD"}
    for section in ["digital_time", "date_display", "info_line"]:
        sec = cdm_dict.get(section, {})
        font = sec.get("font", {})
        w = font.get("weight", "")
        if w and w not in valid_weights:
            upper = w.upper()
            if upper in valid_weights:
                font["weight"] = upper
                fixes.append(f"Fixed {section} weight: {w} → {upper}")
            else:
                font["weight"] = "NORMAL"
                fixes.append(f"Fixed {section} weight: {w} → NORMAL")

    # 4. 确保 font family 是 SYNC_TO_DEVICE
    for section in ["digital_time", "date_display", "info_line"]:
        sec = cdm_dict.get(section, {})
        font = sec.get("font", {})
        if font.get("family") and font["family"] != "SYNC_TO_DEVICE":
            font["family"] = "SYNC_TO_DEVICE"
            fixes.append(f"Fixed {section} font family to SYNC_TO_DEVICE")

    # 5. 修复数据源名称 (加方括号的去掉)
    def fix_datasource(obj, key):
        val = obj.get(key, "")
        if isinstance(val, str) and val.startswith("[") and val.endswith("]"):
            obj[key] = val[1:-1]
            fixes.append(f"Fixed {key}: removed brackets → {obj[key]}")

    fix_datasource(cdm_dict.get("info_line", {}), "data_source")

    date = cdm_dict.get("date_display", {})
    if "params" in date:
        new_params = []
        for p in date["params"]:
            if isinstance(p, str) and p.startswith("[") and p.endswith("]"):
                new_params.append(p[1:-1])
                fixes.append(f"Fixed date param: {p} → {p[1:-1]}")
            else:
                new_params.append(p)
        date["params"] = new_params

    return cdm_dict, fixes


# ─── CDM 生成器 ────────────────────────────────────────

class CDMGenerator:
    """自然语言 → CDM JSON"""

    def __init__(self):
        self.ai = AIGateway()

    def generate(
        self,
        prompt: str,
        user_id: str = "default",
        max_retries: int = 3,
    ) -> dict:
        """生成 CDM JSON

        返回:
        {
            "success": bool,
            "cdm": dict | None,
            "fixes": list[str],
            "attempts": int,
            "error": str | None,
            "backend": str,
        }
        """
        # 1. 限流检查
        if not check_rate_limit(user_id):
            return {
                "success": False,
                "cdm": None,
                "fixes": [],
                "attempts": 0,
                "error": "Rate limit exceeded (10 requests/hour)",
                "backend": "none",
            }

        # 2. 调用 LLM
        user_prompt = USER_PROMPT_TEMPLATE.format(prompt=prompt)
        result = self.ai.generate_json(SYSTEM_PROMPT, user_prompt, max_retries)

        if not result["success"]:
            return {
                "success": False,
                "cdm": None,
                "fixes": [],
                "attempts": result["attempts"],
                "error": result.get("error", "LLM generation failed"),
                "backend": result.get("backend", "unknown"),
            }

        if not result.get("json_parsed") or not result.get("json"):
            return {
                "success": False,
                "cdm": None,
                "fixes": [],
                "attempts": result["attempts"],
                "error": f"JSON parse failed: {result.get('json_error', 'unknown')}",
                "backend": result.get("backend", "unknown"),
                "raw_content": result.get("content", "")[:500],
            }

        # 3. 自动修复
        cdm_dict, fixes = fix_cdm(result["json"])

        # 4. Pydantic 校验
        try:
            cdm = WatchFaceCDM(**cdm_dict)
        except Exception as e:
            # 最后一次尝试失败, 返回错误
            return {
                "success": False,
                "cdm": None,
                "fixes": fixes,
                "attempts": result["attempts"],
                "error": f"CDM validation failed: {str(e)[:300]}",
                "backend": result.get("backend", "unknown"),
            }

        # 5. 记录请求
        record_request(user_id)

        return {
            "success": True,
            "cdm": cdm.model_dump(),
            "fixes": fixes,
            "attempts": result["attempts"],
            "error": None,
            "backend": result.get("backend", "unknown"),
        }
