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
    """模板 1: 赛博蓝 — 数字表盘，霓虹蓝主色"""
    return WatchFaceCDM(
        metadata=WatchFaceMetadata(
            name="Cyber Blue",
            package_name="com.watchfaceforge.cyberblue",
            version_code=1,
            version_name="1.0",
            author="WatchFace Forge",
            description="霓虹蓝数字表盘",
        ),
        clock_type=ClockType.DIGITAL,
        background=Background(type="solid", color="#ff0a0e1a"),
        digital_time=DigitalTime(
            format="HH:mm",
            position=Position(x=0, y=120, width=450, height=120),
            font=FontStyle(size=100, weight=FontWeight.BOLD, color="#ff00F5FF"),
            ambient_color="#ff888888",
        ),
        date_display=DateDisplay(
            format="%s/%s",
            params=[DataSource.MONTH, DataSource.DAY],
            position=Position(x=0, y=260, width=450, height=50),
            font=FontStyle(size=32, color="#ffAAAAAA"),
        ),
        info_line=InfoLine(
            label="BAT",
            data_source=DataSource.BATTERY_PERCENT,
            position=Position(x=0, y=320, width=450, height=50),
            font=FontStyle(size=28, color="#ffFF6B6B"),
        ),
    )


def _minimal_white() -> WatchFaceCDM:
    """模板 2: 极简白 — 大字号细体，纯净背景"""
    return WatchFaceCDM(
        metadata=WatchFaceMetadata(
            name="Minimal White",
            package_name="com.watchfaceforge.minimalwhite",
            version_code=1,
            version_name="1.0",
            author="WatchFace Forge",
            description="极简白色表盘",
        ),
        clock_type=ClockType.DIGITAL,
        background=Background(type="solid", color="#ff1a1a1a"),
        digital_time=DigitalTime(
            format="HH:mm",
            position=Position(x=0, y=140, width=450, height=120),
            font=FontStyle(size=110, weight=FontWeight.THIN, color="#ffffffff"),
            ambient_color="#ff666666",
        ),
        date_display=DateDisplay(
            format="%s %s",
            params=[DataSource.DAY_OF_WEEK_S, DataSource.DAY],
            position=Position(x=0, y=270, width=450, height=50),
            font=FontStyle(size=28, weight=FontWeight.NORMAL, color="#ffcccccc"),
        ),
        info_line=InfoLine(
            label="",
            data_source=DataSource.BATTERY_PERCENT,
            position=Position(x=0, y=330, width=450, height=40),
            font=FontStyle(size=22, weight=FontWeight.NORMAL, color="#ff888888"),
        ),
    )


def _amber_glow() -> WatchFaceCDM:
    """模板 3: 琥珀光 — 暖橙色调数字表盘"""
    return WatchFaceCDM(
        metadata=WatchFaceMetadata(
            name="Amber Glow",
            package_name="com.watchfaceforge.amberglow",
            version_code=1,
            version_name="1.0",
            author="WatchFace Forge",
            description="琥珀橙暖色表盘",
        ),
        clock_type=ClockType.DIGITAL,
        background=Background(type="solid", color="#ff1a1000"),
        digital_time=DigitalTime(
            format="HH:mm",
            position=Position(x=0, y=120, width=450, height=120),
            font=FontStyle(size=100, weight=FontWeight.BOLD, color="#ffFFB300"),
            ambient_color="#ff8a6d00",
        ),
        date_display=DateDisplay(
            format="%s/%s",
            params=[DataSource.MONTH, DataSource.DAY],
            position=Position(x=0, y=260, width=450, height=50),
            font=FontStyle(size=30, color="#ffFFCC80"),
        ),
        info_line=InfoLine(
            label="PWR",
            data_source=DataSource.BATTERY_PERCENT,
            position=Position(x=0, y=310, width=450, height=50),
            font=FontStyle(size=26, color="#ffFF8A65"),
        ),
    )


# 模板注册表
TEMPLATES = {
    "cyber-blue": {
        "id": "cyber-blue",
        "name": "Cyber Blue",
        "description": "霓虹蓝数字表盘，赛博朋克风格",
        "preview_color": "#00F5FF",
        "cdm": _digital_blue,
    },
    "minimal-white": {
        "id": "minimal-white",
        "name": "Minimal White",
        "description": "极简白色表盘，大字号细体",
        "preview_color": "#FFFFFF",
        "cdm": _minimal_white,
    },
    "amber-glow": {
        "id": "amber-glow",
        "name": "Amber Glow",
        "description": "琥珀橙暖色表盘",
        "preview_color": "#FFB300",
        "cdm": _amber_glow,
    },
}
