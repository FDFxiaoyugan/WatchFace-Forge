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
        digital_time=DigitalTime(
            format="HH:mm",
            position=Position(x=0, y=120, width=450, height=120),
            font=FontStyle(size=100, weight=FontWeight.BOLD, color="#ff00F5FF"),
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


def _digital_minimal() -> WatchFaceCDM:
    """模板 2: 极简白 — 纯白数字，无信息行"""
    return WatchFaceCDM(
        metadata=WatchFaceMetadata(
            name="Minimal White",
            package_name="com.watchfaceforge.minimalwhite",
            version_code=1,
            version_name="1.0",
            author="WatchFace Forge",
            description="极简白色数字表盘",
        ),
        clock_type=ClockType.DIGITAL,
        digital_time=DigitalTime(
            format="HH:mm",
            position=Position(x=0, y=160, width=450, height=140),
            font=FontStyle(size=120, weight=FontWeight.THIN, color="#ffffffff"),
        ),
        date_display=DateDisplay(
            format="%s %s",
            params=[DataSource.MONTH_S, DataSource.DAY],
            position=Position(x=0, y=310, width=450, height=50),
            font=FontStyle(size=28, weight=FontWeight.NORMAL, color="#ff999999"),
        ),
        info_line=InfoLine(enabled=False),
    )


def _digital_amber() -> WatchFaceCDM:
    """模板 3: 琥珀橙 — 暖色调数字表盘"""
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
        digital_time=DigitalTime(
            format="HH:mm",
            position=Position(x=0, y=100, width=450, height=120),
            font=FontStyle(size=96, weight=FontWeight.BOLD, color="#ffFFB300"),
        ),
        date_display=DateDisplay(
            format="%s-%s",
            params=[DataSource.MONTH, DataSource.DAY],
            position=Position(x=0, y=240, width=450, height=50),
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
        "cdm": _digital_minimal,
    },
    "amber-glow": {
        "id": "amber-glow",
        "name": "Amber Glow",
        "description": "琥珀橙暖色表盘",
        "preview_color": "#FFB300",
        "cdm": _digital_amber,
    },
}
