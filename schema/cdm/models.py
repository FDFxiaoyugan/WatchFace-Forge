"""
CDM (Canonical Data Model) — 表盘设计的中立数据模型

设计原则:
1. 简单 — AI 可直接生成 JSON
2. 中立 — 不绑定 WFF/Apple Watch 具体格式
3. 可编译 — 能转换为 WFF XML 或其他目标格式
4. 可校验 — Pydantic 模型自动生成 JSON Schema

CDM 结构:
  WatchFace
  ├── metadata         # 表盘元信息
  ├── background       # 背景层
  ├── time             # 时间显示
  ├── date             # 日期显示
  ├── info             # 信息层 (电量/心率等)
  ├── complications    # 并发复杂功能
  └── styles           # 颜色/字体配置
"""

from __future__ import annotations

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


# ─── 枚举 ─────────────────────────────────────────────

class ClockType(str, Enum):
    DIGITAL = "DIGITAL"
    ANALOG = "ANALOG"


class FontWeight(str, Enum):
    THIN = "THIN"
    NORMAL = "NORMAL"
    BOLD = "BOLD"


class HorizontalAlign(str, Enum):
    LEFT = "LEFT"
    CENTER = "CENTER"
    RIGHT = "RIGHT"


class VerticalAlign(str, Enum):
    TOP = "TOP"
    MIDDLE = "MIDDLE"
    BOTTOM = "BOTTOM"


class ColorScheme(str, Enum):
    LIGHT_ON_DARK = "LIGHT_ON_DARK"
    DARK_ON_LIGHT = "DARK_ON_LIGHT"


class BatteryDisplayMode(str, Enum):
    PERCENT = "PERCENT"           # BAT 85%
    ICON = "ICON"                 # 电池图标
    PERCENT_WITH_ICON = "PERCENT_WITH_ICON"


class DataSource(str, Enum):
    """已验证的 WFF 数据源表达式

    CDM 中用简写名 (如 MONTH), 编译器自动加方括号变为 [MONTH]。
    """
    HOUR_0_23 = "HOUR_0_23"
    HOUR_1_12 = "HOUR_1_12"
    MINUTE_Z = "MINUTE_Z"
    SECOND_Z = "SECOND_Z"
    AMPM_STRING = "AMPM_STRING"
    DAY = "DAY"
    DAY_Z = "DAY_Z"
    DAY_OF_WEEK_S = "DAY_OF_WEEK_S"
    MONTH = "MONTH"
    MONTH_S = "MONTH_S"
    YEAR = "YEAR"
    BATTERY_PERCENT = "BATTERY_PERCENT"
    HEART_RATE = "HEART_RATE"

    @property
    def wff_expression(self) -> str:
        """转换为 WFF 表达式 (带方括号)"""
        return f"[{self.value}]"


# ─── 子模型 ────────────────────────────────────────────

class Position(BaseModel):
    """元素位置和尺寸 (WFF 画布 450x450)"""
    x: int = Field(0, ge=0, le=450, description="X 坐标")
    y: int = Field(0, ge=0, le=450, description="Y 坐标")
    width: int = Field(450, ge=1, le=450, description="宽度")
    height: int = Field(50, ge=1, le=450, description="高度")


class FontStyle(BaseModel):
    """字体配置"""
    family: str = Field("SYNC_TO_DEVICE", description="字体族, 默认同步设备")
    size: int = Field(48, ge=8, le=200, description="字号")
    weight: FontWeight = FontWeight.NORMAL
    color: str = Field("#ffffffff", pattern=r"^#[0-9a-fA-F]{8}$",
                        description="8位 ARGB 颜色, 如 #ff00F5FF")


class Background(BaseModel):
    """背景层"""
    type: str = Field("solid", description="背景类型: solid | gradient | image")
    color: str = Field("#ff000000", pattern=r"^#[0-9a-fA-F]{8}$",
                        description="纯色背景颜色")
    gradient_start: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{8}$",
                                          description="渐变起始色")
    gradient_end: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{8}$",
                                        description="渐变结束色")
    image_resource: Optional[str] = Field(None, description="背景图片资源名")


class DigitalTime(BaseModel):
    """数字时间显示"""
    enabled: bool = True
    format: str = Field("HH:mm", description="时间格式: HH:mm / hh:mm / HH:mm:ss")
    position: Position = Field(default_factory=lambda: Position(x=0, y=120, width=450, height=120))
    font: FontStyle = Field(default_factory=lambda: FontStyle(
        size=100, weight=FontWeight.BOLD, color="#ff00F5FF"
    ))
    align: HorizontalAlign = HorizontalAlign.CENTER
    ambient_color: str = Field("#ff888888", pattern=r"^#[0-9a-fA-F]{8}$",
                                description="暗屏颜色")


class AnalogTime(BaseModel):
    """模拟时间显示 (指针表盘)"""
    enabled: bool = False
    center_x: int = Field(225, ge=0, le=450)
    center_y: int = Field(225, ge=0, le=450)
    hour_hand_color: str = Field("#ffffffff", pattern=r"^#[0-9a-fA-F]{8}$")
    minute_hand_color: str = Field("#ff00F5FF", pattern=r"^#[0-9a-fA-F]{8}$")
    second_hand_color: str = Field("#ffFF6B6B", pattern=r"^#[0-9a-fA-F]{8}$")
    hour_hand_length: int = Field(120, ge=10, le=200)
    minute_hand_length: int = Field(160, ge=10, le=200)
    second_hand_length: int = Field(180, ge=10, le=200)


class DateDisplay(BaseModel):
    """日期显示"""
    enabled: bool = True
    format: str = Field("%s/%s", description="日期格式模板, 使用 %s 占位")
    position: Position = Field(default_factory=lambda: Position(x=0, y=260, width=450, height=50))
    font: FontStyle = Field(default_factory=lambda: FontStyle(
        size=32, weight=FontWeight.NORMAL, color="#ffAAAAAA"
    ))
    align: HorizontalAlign = HorizontalAlign.CENTER
    params: List[DataSource] = Field(
        default_factory=lambda: [DataSource.MONTH, DataSource.DAY],
        description="日期参数数据源"
    )


class InfoLine(BaseModel):
    """信息行 (电量/心率等)"""
    enabled: bool = True
    label: str = Field("BAT", description="前缀标签, 如 BAT/HR")
    data_source: DataSource = DataSource.BATTERY_PERCENT
    suffix: str = Field("%%", description="后缀, %% 表示百分号")
    position: Position = Field(default_factory=lambda: Position(x=0, y=320, width=450, height=50))
    font: FontStyle = Field(default_factory=lambda: FontStyle(
        size=28, weight=FontWeight.NORMAL, color="#ffFF6B6B"
    ))
    align: HorizontalAlign = HorizontalAlign.CENTER


class ComplicationSlot(BaseModel):
    """并发复杂功能槽位"""
    enabled: bool = False
    slot_type: str = Field("SHORT_TEXT", description="SHORT_TEXT | LONG_TEXT | RANGED_VALUE | ICON")
    position: Position = Field(default_factory=lambda: Position(x=160, y=160, width=130, height=130))
    tint_color: str = Field("#ffffffff", pattern=r"^#[0-9a-fA-F]{8}$")


class WatchFaceMetadata(BaseModel):
    """表盘元信息"""
    name: str = Field(..., min_length=1, max_length=50, description="表盘名称")
    package_name: str = Field(..., pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$",
                               description="Android 包名, 如 com.example.mywatch")
    version_code: int = Field(1, ge=1)
    version_name: str = Field("1.0.0")
    author: str = Field("WatchFace Forge", description="作者/生成来源")
    preview_time: str = Field("10:08:32", description="预览图显示时间")


# ─── 顶层模型 ──────────────────────────────────────────

class WatchFaceCDM(BaseModel):
    """表盘设计 CDM 模型 — AI 生成的目标格式"""

    schema_version: str = Field("1.0", description="CDM 版本号")
    metadata: WatchFaceMetadata
    clock_type: ClockType = ClockType.DIGITAL
    background: Background = Field(default_factory=Background)
    digital_time: DigitalTime = Field(default_factory=DigitalTime)
    analog_time: AnalogTime = Field(default_factory=AnalogTime)
    date_display: DateDisplay = Field(default_factory=DateDisplay)
    info_line: InfoLine = Field(default_factory=InfoLine)
    complications: List[ComplicationSlot] = Field(default_factory=list, max_length=4)
    ambient_dim_mode: bool = Field(True, description="暗屏是否降低亮度")


# ─── 工具函数 ──────────────────────────────────────────

def generate_json_schema() -> dict:
    """导出 CDM JSON Schema, 供 AI 生成时参考"""
    return WatchFaceCDM.model_json_schema()


def save_schema(path: str):
    """保存 JSON Schema 到文件"""
    import json
    schema = generate_json_schema()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    save_schema("schema/cdm/v1.0.json")
    print("CDM JSON Schema saved to schema/cdm/v1.0.json")
