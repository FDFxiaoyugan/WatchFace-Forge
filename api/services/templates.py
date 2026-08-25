"""
固定模板定义 — Phase 1 提供 3 个预设表盘模板

模板作为 CDM 实例存储，用户可基于模板自定义颜色/字体等参数。
"""

from schema.cdm.models import (
    WatchFaceCDM, WatchFaceMetadata, ClockType,
    DigitalTime, AnalogTime, DateDisplay, InfoLine,
    Background, FontStyle, FontWeight, Position,
    DataSource,
)


def _digital_blue() -> WatchFaceCDM:
    """模板 1: Neon Tide — 冷色渐变与克制的霓虹层级。"""
    return WatchFaceCDM(
        metadata=WatchFaceMetadata(
            name="Neon Tide",
            package_name="com.watchfaceforge.cyberblue",
            version_code=1,
            version_name="1.0",
            author="WatchFace Forge",
            description="霓虹蓝数字表盘",
        ),
        clock_type=ClockType.DIGITAL,
        background=Background(
            type="gradient", color="#ff071426",
            gradient_start="#ff071426", gradient_end="#ff160b33",
        ),
        digital_time=DigitalTime(
            format="HH:mm",
            position=Position(x=35, y=132, width=380, height=112),
            font=FontStyle(size=88, weight=FontWeight.BOLD, color="#ff67E8F9"),
            ambient_color="#ff34515f",
        ),
        date_display=DateDisplay(
            format="%s月%s日",
            params=[DataSource.MONTH, DataSource.DAY],
            position=Position(x=75, y=252, width=300, height=42),
            font=FontStyle(size=24, color="#ffA5B4FC"),
        ),
        info_line=InfoLine(
            label="🔋",
            data_source=DataSource.BATTERY_PERCENT,
            position=Position(x=125, y=305, width=200, height=34),
            font=FontStyle(size=18, color="#ff64748B"),
        ),
    )


def _minimal_white() -> WatchFaceCDM:
    """模板 2: 极简白 — 大字号细体，纯净背景"""
    return WatchFaceCDM(
        metadata=WatchFaceMetadata(
            name="Quiet Mono",
            package_name="com.watchfaceforge.minimalwhite",
            version_code=1,
            version_name="1.0",
            author="WatchFace Forge",
            description="极简白色表盘",
        ),
        clock_type=ClockType.DIGITAL,
        background=Background(type="solid", color="#ff050505"),
        digital_time=DigitalTime(
            format="HH:mm",
            position=Position(x=40, y=138, width=370, height=112),
            font=FontStyle(size=92, weight=FontWeight.NORMAL, color="#ffF4F4F5"),
            ambient_color="#ff52525B",
        ),
        date_display=DateDisplay(
            format="%s月%s日",
            params=[DataSource.MONTH, DataSource.DAY],
            position=Position(x=100, y=264, width=250, height=38),
            font=FontStyle(size=22, weight=FontWeight.NORMAL, color="#ffA1A1AA"),
        ),
        info_line=InfoLine(
            label="🔋",
            data_source=DataSource.BATTERY_PERCENT,
            position=Position(x=155, y=316, width=140, height=30),
            font=FontStyle(size=16, weight=FontWeight.NORMAL, color="#ff52525B"),
        ),
    )


def _amber_glow() -> WatchFaceCDM:
    """模板 3: Solar Dusk — 日落色渐变与暖色强调。"""
    return WatchFaceCDM(
        metadata=WatchFaceMetadata(
            name="Solar Dusk",
            package_name="com.watchfaceforge.amberglow",
            version_code=1,
            version_name="1.0",
            author="WatchFace Forge",
            description="琥珀橙暖色表盘",
        ),
        clock_type=ClockType.DIGITAL,
        background=Background(
            type="gradient", color="#ff1B0B16",
            gradient_start="#ff2A0F1F", gradient_end="#ff09090B",
        ),
        digital_time=DigitalTime(
            format="HH:mm",
            position=Position(x=35, y=130, width=380, height=112),
            font=FontStyle(size=90, weight=FontWeight.BOLD, color="#ffFDBA74"),
            ambient_color="#ff6B4B35",
        ),
        date_display=DateDisplay(
            format="%s月%s日",
            params=[DataSource.MONTH, DataSource.DAY],
            position=Position(x=100, y=252, width=250, height=42),
            font=FontStyle(size=23, color="#ffFED7AA"),
        ),
        info_line=InfoLine(
            label="🔋",
            data_source=DataSource.BATTERY_PERCENT,
            position=Position(x=125, y=306, width=200, height=34),
            font=FontStyle(size=18, color="#ffFB7185"),
        ),
    )


# 模板注册表
TEMPLATES = {
    "cyber-blue": {
        "id": "cyber-blue",
        "name": "Neon Tide",
        "description": "深海冷色渐变，清晰而克制",
        "preview_color": "#67E8F9",
        "cdm": _digital_blue,
    },
    "minimal-white": {
        "id": "minimal-white",
        "name": "Quiet Mono",
        "description": "OLED 黑底，中性灰阶与充足留白",
        "preview_color": "#F4F4F5",
        "cdm": _minimal_white,
    },
    "amber-glow": {
        "id": "amber-glow",
        "name": "Solar Dusk",
        "description": "暖橙与玫红点缀的日落渐变",
        "preview_color": "#FDBA74",
        "cdm": _amber_glow,
    },
}
