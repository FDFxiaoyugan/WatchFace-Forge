"""
API 端点测试

运行: cd watchface-forge && python -m pytest tests/test_api.py -v
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"


class TestTemplatesEndpoint:
    def test_list_templates(self):
        r = client.get("/api/templates")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3

    def test_get_template_detail(self):
        r = client.get("/api/templates/cyber-blue")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "cyber-blue"
        assert "cdm" in data

    def test_template_not_found(self):
        r = client.get("/api/templates/nonexistent")
        assert r.status_code == 404

    def test_all_templates_have_cdm(self):
        """所有模板都应该能返回完整 CDM"""
        for tmpl_id in ["cyber-blue", "minimal-white", "amber-glow"]:
            r = client.get(f"/api/templates/{tmpl_id}")
            assert r.status_code == 200
            data = r.json()
            assert data["cdm"] is not None
            assert "clock_type" in data["cdm"]


class TestCompileEndpoint:
    def test_compile_valid_cdm(self):
        cdm = {
            "metadata": {"name": "T", "package_name": "com.t", "version_code": 1, "version_name": "1.0"},
            "clock_type": "DIGITAL",
            "digital_time": {"enabled": True, "format": "HH:mm", "font": {"size": 100, "weight": "BOLD", "color": "#ff00F5FF"}},
            "date_display": {"format": "%s/%s", "params": ["MONTH", "DAY"]},
            "info_line": {"label": "BAT", "data_source": "BATTERY_PERCENT"},
        }
        r = client.post("/api/compile", json={"cdm": cdm})
        assert r.status_code == 200
        data = r.json()
        assert data["validation_passed"] is True
        assert len(data["wff_xml"]) > 0

    def test_compile_analog(self):
        cdm = {
            "metadata": {"name": "A", "package_name": "com.a", "version_code": 1, "version_name": "1.0"},
            "clock_type": "ANALOG",
            "analog_time": {"enabled": True},
        }
        r = client.post("/api/compile", json={"cdm": cdm})
        assert r.status_code == 200
        data = r.json()
        assert data["validation_passed"] is True

    def test_compile_bad_color_returns_422(self):
        """6 位颜色应该返回 422 (而不是崩溃)"""
        cdm = {
            "metadata": {"name": "B", "package_name": "com.b", "version_code": 1, "version_name": "1.0"},
            "clock_type": "DIGITAL",
            "digital_time": {"enabled": True, "format": "HH:mm", "font": {"size": 100, "weight": "BOLD", "color": "#00F5FF"}},
            "date_display": {"format": "%s/%s", "params": ["MONTH", "DAY"]},
            "info_line": {"label": "BAT", "data_source": "BATTERY_PERCENT"},
        }
        r = client.post("/api/compile", json={"cdm": cdm})
        assert r.status_code == 422
        data = r.json()
        assert data["status"] == "error"


class TestBuildEndpoint:
    def test_build_digital(self):
        """构建数字表盘 APK"""
        cdm = {
            "metadata": {"name": "TestBuild", "package_name": "com.testbuild", "version_code": 1, "version_name": "1.0"},
            "clock_type": "DIGITAL",
            "digital_time": {"enabled": True, "format": "HH:mm", "font": {"size": 100, "weight": "BOLD", "color": "#ff00F5FF"}},
            "date_display": {"format": "%s/%s", "params": ["MONTH", "DAY"]},
            "info_line": {"label": "BAT", "data_source": "BATTERY_PERCENT"},
        }
        r = client.post("/api/build", json={"cdm": cdm})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["apk_size"] > 0
        assert data["download_url"] is not None
