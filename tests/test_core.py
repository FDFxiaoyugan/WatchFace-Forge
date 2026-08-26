"""
Phase 1 核心测试 — CDM 模型 + WFF 编译器

运行: cd watchface-forge && python -m pytest tests/ -v
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "wff-builder"))

import pytest
from schema.cdm.models import (
    WatchFaceCDM, WatchFaceMetadata, ClockType,
    DigitalTime, AnalogTime, DateDisplay, InfoLine,
    Background, FontStyle, FontWeight, Position,
    DataSource,
)
from compiler.wff.compiler import WFFCompiler
from wff_builder import validate_watchface_xml


# ─── 测试数据 ──────────────────────────────────────────

def _make_digital_cdm() -> WatchFaceCDM:
    """创建标准数字表盘 CDM"""
    return WatchFaceCDM(
        metadata=WatchFaceMetadata(
            name="Test Digital",
            package_name="com.test.digital",
            version_code=1,
            version_name="1.0",
        ),
        clock_type=ClockType.DIGITAL,
        digital_time=DigitalTime(
            format="HH:mm",
            font=FontStyle(size=100, weight=FontWeight.BOLD, color="#ff00F5FF"),
        ),
        date_display=DateDisplay(
            format="%s/%s",
            params=[DataSource.MONTH, DataSource.DAY],
        ),
        info_line=InfoLine(
            label="BAT",
            data_source=DataSource.BATTERY_PERCENT,
        ),
    )


def _make_analog_cdm() -> WatchFaceCDM:
    """创建标准模拟表盘 CDM"""
    return WatchFaceCDM(
        metadata=WatchFaceMetadata(
            name="Test Analog",
            package_name="com.test.analog",
            version_code=1,
            version_name="1.0",
        ),
        clock_type=ClockType.ANALOG,
        analog_time=AnalogTime(enabled=True),
    )


# ─── CDM 模型测试 ──────────────────────────────────────

class TestCDMModel:
    """CDM 数据模型测试"""

    def test_digital_cdm_creation(self):
        cdm = _make_digital_cdm()
        assert cdm.clock_type == ClockType.DIGITAL
        assert cdm.digital_time.enabled is True
        assert cdm.metadata.name == "Test Digital"

    def test_analog_cdm_creation(self):
        cdm = _make_analog_cdm()
        assert cdm.clock_type == ClockType.ANALOG
        assert cdm.analog_time.enabled is True

    def test_color_validation_good(self):
        """8 位 ARGB 颜色应该通过校验"""
        cdm = _make_digital_cdm()
        cdm.digital_time.font.color = "#ff00F5FF"
        assert cdm.digital_time.font.color == "#ff00F5FF"

    def test_color_validation_bad_6digit(self):
        """6 位颜色应该被拒绝"""
        with pytest.raises(Exception):
            FontStyle(color="#00F5FF")

    def test_position_bounds(self):
        """坐标超出范围应该报错"""
        with pytest.raises(Exception):
            Position(x=500)

    def test_data_source_wff_expression(self):
        """DataSource.wff_expression 应该带方括号"""
        assert DataSource.MONTH.wff_expression == "[MONTH]"
        assert DataSource.BATTERY_PERCENT.wff_expression == "[BATTERY_PERCENT]"
        assert DataSource.HOUR_0_23.wff_expression == "[HOUR_0_23]"

    def test_json_schema_export(self):
        """JSON Schema 应该可以导出"""
        schema = WatchFaceCDM.model_json_schema()
        assert "properties" in schema
        assert "clock_type" in schema["properties"]


# ─── WFF 编译器测试 ────────────────────────────────────

class TestWFFCompiler:
    """WFF 编译器测试"""

    def test_compile_digital(self):
        """数字表盘编译应该通过所有校验规则"""
        cdm = _make_digital_cdm()
        compiler = WFFCompiler()
        xml = compiler.compile(cdm)

        failures = validate_watchface_xml(xml)
        errors = [f for f in failures if f["severity"] == "error"]
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_compile_analog(self):
        """模拟表盘编译应该通过所有校验规则"""
        cdm = _make_analog_cdm()
        compiler = WFFCompiler()
        xml = compiler.compile(cdm)

        failures = validate_watchface_xml(xml)
        errors = [f for f in failures if f["severity"] == "error"]
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_xml_has_metadata(self):
        """WFF XML 必须有 CLOCK_TYPE 和 PREVIEW_TIME"""
        cdm = _make_digital_cdm()
        compiler = WFFCompiler()
        xml = compiler.compile(cdm)

        assert 'key="CLOCK_TYPE"' in xml
        assert 'key="PREVIEW_TIME"' in xml

    def test_xml_has_digital_clock(self):
        """数字表盘必须有 DigitalClock 和 TimeText"""
        cdm = _make_digital_cdm()
        compiler = WFFCompiler()
        xml = compiler.compile(cdm)

        assert "<DigitalClock" in xml
        assert "<TimeText" in xml

    def test_xml_has_ambient_variant(self):
        """必须有 ambient 模式 Variant"""
        cdm = _make_digital_cdm()
        compiler = WFFCompiler()
        xml = compiler.compile(cdm)

        assert "<Variant" in xml
        assert 'mode="AMBIENT"' in xml

    def test_xml_has_bracket_expressions(self):
        """表达式必须有方括号"""
        cdm = _make_digital_cdm()
        compiler = WFFCompiler()
        xml = compiler.compile(cdm)

        assert "[MONTH]" in xml
        assert "[DAY]" in xml
        assert "[BATTERY_PERCENT]" in xml

    def test_xml_has_sync_to_device_font(self):
        """字体必须是 SYNC_TO_DEVICE"""
        cdm = _make_digital_cdm()
        compiler = WFFCompiler()
        xml = compiler.compile(cdm)

        assert 'family="SYNC_TO_DEVICE"' in xml

    def test_xml_has_argb_colors(self):
        """颜色必须是 8 位 ARGB"""
        cdm = _make_digital_cdm()
        compiler = WFFCompiler()
        xml = compiler.compile(cdm)

        # 不应该有 6 位颜色 (#RRGGBB without alpha)
        import re
        bad_colors = re.findall(r'color="#([0-9a-fA-F]{6})"', xml)
        assert len(bad_colors) == 0, f"Found 6-digit colors: {bad_colors}"

    def test_analog_has_transform(self):
        """模拟表盘必须有 Transform 旋转表达式"""
        cdm = _make_analog_cdm()
        compiler = WFFCompiler()
        xml = compiler.compile(cdm)

        assert "<Transform" in xml
        assert "[HOUR_1_12]" in xml
        assert "[MINUTE_Z]" in xml

    def test_gradient_background(self):
        """渐变背景应该生成官方 WFF v1 原生径向渐变"""
        cdm = _make_digital_cdm()
        cdm.background = Background(
            type="gradient",
            color="#ff000000",
            gradient_start="#ff0a0e1a",
            gradient_end="#ff000000",
        )
        compiler = WFFCompiler()
        xml = compiler.compile(cdm)

        assert "<Ellipse" in xml
        assert "<RadialGradient" in xml
        assert 'colors="#ff0a0e1a #ff000000"' in xml
