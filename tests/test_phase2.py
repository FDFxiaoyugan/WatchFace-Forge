"""
Phase 2 测试 — AI 生成 + CDM 自动修复

运行: python -m pytest tests/test_phase2.py -v
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "wff-builder"))

import pytest
from services.cdm_generator import CDMGenerator, fix_cdm
from services.ai_gateway import (
    AIGateway,
    AIConfigError,
    normalize_user_ai_config,
)


class TestLegacyRateLimitRemoved:
    """复查 R4: 旧内存限流已删除, 唯一限流入口为路由层 Redis 配额"""

    def test_cdm_generator_no_longer_limits(self, monkeypatch):
        import services.ai_gateway as gwmod
        assert not hasattr(gwmod, "check_rate_limit")
        assert not hasattr(gwmod, "record_request")

    def test_generate_signature_has_no_user_id(self):
        import inspect
        params = inspect.signature(CDMGenerator.generate).parameters
        assert "user_id" not in params


class TestCDMAutoFixer:
    """CDM 自动修复层测试"""

    def test_fix_missing_alpha_channel(self):
        """6 位颜色应该被修复为 8 位"""
        cdm = {
            "metadata": {"name": "T", "package_name": "com.t", "version_code": 1, "version_name": "1.0"},
            "clock_type": "DIGITAL",
            "digital_time": {
                "enabled": True,
                "format": "HH:mm",
                "font": {"size": 100, "weight": "BOLD", "color": "#00F5FF"},
            },
        }
        fixed, fixes = fix_cdm(cdm)
        assert len(fixes) > 0
        assert fixed["digital_time"]["font"]["color"] == "#ff00F5FF"

    def test_fix_placeholder_name(self):
        """空名称应该被替换为默认值"""
        cdm = {
            "metadata": {"name": "", "package_name": "", "version_code": 0, "version_name": ""},
            "clock_type": "DIGITAL",
        }
        fixed, fixes = fix_cdm(cdm)
        assert fixed["metadata"]["name"] == "AI Generated"
        assert fixed["metadata"]["package_name"].startswith("com.watchfaceforge.")
        assert "watch" in fixed["metadata"]["package_name"]

    def test_fix_data_source_brackets(self):
        """数据源缺少方括号应该被修复"""
        cdm = {
            "metadata": {"name": "T", "package_name": "com.t", "version_code": 1, "version_name": "1.0"},
            "clock_type": "DIGITAL",
            "date_display": {
                "format": "%s/%s",
                "params": ["MONTH", "DAY"],
            },
            "info_line": {
                "label": "BAT",
                "data_source": "BATTERY_PERCENT",
            },
        }
        fixed, fixes = fix_cdm(cdm)
        # CDM 中 MONTH 应该被识别为 DataSource 枚举
        from schema.cdm.models import DataSource
        assert DataSource(fixed["date_display"]["params"][0]) == DataSource.MONTH

    def test_fix_weight_case(self):
        """weight 大小写应该被标准化"""
        cdm = {
            "metadata": {"name": "T", "package_name": "com.t", "version_code": 1, "version_name": "1.0"},
            "clock_type": "DIGITAL",
            "digital_time": {
                "enabled": True,
                "format": "HH:mm",
                "font": {"size": 100, "weight": "bold", "color": "#ff00F5FF"},
            },
        }
        fixed, fixes = fix_cdm(cdm)
        assert fixed["digital_time"]["font"]["weight"] == "BOLD"


class TestAIGateway:
    """AI Gateway 测试 (不实际调用 LLM)"""

    def test_gateway_init(self):
        """Gateway 应该可以初始化"""
        gw = AIGateway()
        assert gw is not None

    def test_user_key_selects_openai_and_keeps_custom_endpoint(self, monkeypatch):
        # S3: normalize 现在做 SSRF 出站校验, 假域名须 mock 为公网地址解析
        import ipaddress
        from services.ai_gateway import ssrf_guard
        monkeypatch.setattr(
            ssrf_guard, "_resolve_all_ips",
            lambda host: [ipaddress.ip_address("93.184.216.34")],
        )
        config = normalize_user_ai_config({
            "api_key": "sk-user-secret",
            "base_url": "https://ai.example.com/v1",
            "model": "custom-model",
        })
        assert config is not None
        gw = AIGateway(backend="auto", **config)
        assert gw._get_backend() == "openai"
        assert gw.base_url == "https://ai.example.com/v1"
        assert gw.model == "custom-model"

    def test_empty_user_key_uses_server_default(self):
        assert normalize_user_ai_config({"api_key": "", "base_url": "", "model": ""}) is None

    def test_gateway_redacts_user_key_from_errors(self):
        gw = AIGateway(backend="openai", api_key="sk-never-echo-this")
        error = gw._safe_error(RuntimeError("request failed for sk-never-echo-this"))
        assert "sk-never-echo-this" not in error
        assert "[REDACTED]" in error

    def test_connection_does_not_return_content_or_key(self, monkeypatch):
        gw = AIGateway(backend="openai", api_key="sk-test-secret", model="test-model")
        monkeypatch.setattr(gw, "_call_openai", lambda *args, **kwargs: '{"ok":true}')
        result = gw.test_connection()
        assert result["success"] is True
        assert result["model"] == "test-model"
        assert "content" not in result
        assert "sk-test-secret" not in str(result)

    @pytest.mark.parametrize("url", ["http://ai.example.com/v1", "https://user:pass@ai.example.com/v1", "https://ai.example.com/v1?key=secret"])
    def test_rejects_unsafe_custom_base_url(self, url):
        with pytest.raises(AIConfigError):
            normalize_user_ai_config({"api_key": "sk-test", "base_url": url, "model": "gpt-4o"})

    def test_parse_json_from_code_block(self):
        """应该能从 markdown 代码块中提取 JSON"""
        gw = AIGateway()
        content = '```json\n{"name": "test"}\n```'
        result = gw._extract_json(content)
        assert result == {"name": "test"}

    def test_parse_raw_json(self):
        """应该能解析原始 JSON"""
        gw = AIGateway()
        content = '{"name": "test", "value": 123}'
        result = gw._extract_json(content)
        assert result["name"] == "test"
        assert result["value"] == 123


class TestCDMGenerator:
    """CDM 生成器测试 (不实际调用 LLM)"""

    def test_generator_init(self):
        """生成器应该可以初始化"""
        gen = CDMGenerator()
        assert gen is not None
