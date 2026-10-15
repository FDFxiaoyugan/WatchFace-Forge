"""安全回归测试（2026-10 审计修复的守护性测试）。

覆盖:
- S5 输出路径逃逸（artifact_paths 单元 + build/generate 端到端 + download/qrcode 读路径）
- S1 生产签名模式（fail-closed + 开发证书指纹拒绝）
- S3 BYOK SSRF（私网/回环/保留段/白名单）
- S4 鉴权与配额（401/503/内存降级）
- 错误脱敏（内部异常不外泄）
- S6 dockerignore 哨兵检查（无 Docker 环境的规则模拟降级验证）
"""

import ipaddress
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "wff-builder"))

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.services.artifact_paths import (
    APK_OUTPUT_DIR, final_apk_path, resolve_download_filename, task_id_dir,
)

client = TestClient(app)


# ─── S5: 路径安全单元 ────────────────────────────────────

class TestArtifactPaths:
    @pytest.mark.parametrize("task_id", [
        "ab12cd34", "0123456789abcdefabcdefabcdef", "f" * 32,
    ])
    def test_final_apk_path_accepts_server_ids(self, task_id):
        path = final_apk_path(task_id)
        assert path.parent == APK_OUTPUT_DIR
        assert path.name == f"{task_id}.apk"

    @pytest.mark.parametrize("task_id", [
        "../escape", "..", "/abs", "C:\\evil", "../../etc/passwd",
        "abc", "AB12CD34", "逃逸",
    ])
    def test_final_apk_path_rejects_non_hex_ids(self, task_id):
        with pytest.raises(ValueError):
            final_apk_path(task_id)

    def test_task_id_dir_rejects_traversal(self):
        with pytest.raises(ValueError):
            task_id_dir("../etc")
        with pytest.raises(ValueError):
            task_id_dir("ab12cd34/..")

    @pytest.mark.parametrize("filename", [
        "../../etc/passwd", "..%2Fetc%2Fpasswd", "/etc/passwd",
        "C:\\Windows\\evil.apk", "..\\evil.apk", "evil.apk/../../x.apk",
        "中文.apk", ".hidden.apk", "..apk", "x:y.apk", "a/b.apk",
    ])
    def test_download_filename_whitelist(self, filename):
        with pytest.raises(ValueError):
            resolve_download_filename(filename)

    def test_download_filename_accepts_hex_apk(self):
        path = resolve_download_filename("ab12cd34.apk")
        assert path.parent == APK_OUTPUT_DIR

    def test_display_name_never_enters_path(self):
        # 显示名含穿越序列时产物路径不受影响（仅来自服务端 task_id）
        from api.services.artifact_paths import new_task_id
        task_id = new_task_id(8)
        path = final_apk_path(task_id)
        assert ".." not in str(path)


# ─── S5: API 层读路径 ─────────────────────────────────────

class TestDownloadEndpoints:
    def test_download_traversal_returns_404(self):
        for payload in ["..%2F..%2Fetc%2Fpasswd", "%2e%2e%2fconfig.py", "x..apk"]:
            r = client.get(f"/api/download/{payload}")
            assert r.status_code == 404, payload

    def test_qrcode_traversal_returns_404(self):
        r = client.get("/api/qrcode/..%2F..%2Fetc%2Fpasswd")
        assert r.status_code == 404

    def test_wff_builds_traversal_returns_404(self):
        r = client.get("/api/v1/wff/builds/..%2F..%2Fetc%2Fpasswd.apk")
        assert r.status_code == 404


# ─── S5: 构建入口端到端（显示名逃逸防护）──────────────────

def _minimal_cdm(name="../escape"):
    return {
        "metadata": {"name": name, "package_name": "com.watchfaceforge.t",
                     "version_code": 1, "version_name": "1.0"},
        "clock_type": "DIGITAL",
        "digital_time": {
            "time_format": "24h",
            "font": {"family": "SYNC_TO_DEVICE", "size": 72, "weight": "BOLD",
                     "color": "#FFFFFFFF"},
        },
    }


class TestBuildEscaping:
    def test_generate_with_traversal_name_keeps_safe_filename(self, monkeypatch):
        """generate 全链路（mock AI 与 builder）中显示名不得进入产物路径。"""
        from api.routes import generate as gen_route
        from api.services.artifact_paths import APK_OUTPUT_DIR

        fake_cdm = _minimal_cdm(name="../escape attack")
        monkeypatch.setattr(
            gen_route.CDMGenerator, "generate",
            lambda self, prompt, user_id="d": {
                "success": True, "cdm": fake_cdm, "fixes": [], "backend": "mock",
                "attempts": 1,
            },
        )
        monkeypatch.setattr(
            gen_route, "WFFBuilder",
            lambda project_dir, verbose=False: type("B", (), {"build": lambda s: str(APK_OUTPUT_DIR / "x.apk")})(),
        )
        (APK_OUTPUT_DIR / "x.apk").write_bytes(b"PK-fake")

        r = client.post("/api/generate", json={"prompt": "test"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        apk_name = data["apk_filename"]
        # 文件名 = 纯服务端 hex id
        assert apk_name.endswith(".apk")
        stem = apk_name[:-4]
        assert stem.isalnum() and stem.islower()
        assert ".." not in apk_name and "/" not in apk_name and "escape" not in apk_name
        # 产物落在输出根内
        resolved = (APK_OUTPUT_DIR / apk_name).resolve()
        assert APK_OUTPUT_DIR.resolve() in resolved.parents


# ─── S1: 签名模式 ─────────────────────────────────────────

class TestSigningMode:
    def test_dev_default_uses_public_keystore(self, monkeypatch):
        import wff_builder
        for var in ("WFF_KEYSTORE", "WFF_KEYSTORE_ALIAS", "WFF_KEYSTORE_PASSWORD"):
            monkeypatch.delenv(var, raising=False)
        cfg = wff_builder.resolve_signing_config()
        assert cfg.alias == "wfftest"
        assert cfg.ks_pass_ref == "pass:wfftest123"

    def test_production_requires_keystore_env(self, monkeypatch):
        import wff_builder
        monkeypatch.setenv("WF_ENV", "production")
        monkeypatch.delenv("WFF_KEYSTORE", raising=False)
        monkeypatch.delenv("WFF_KEYSTORE_ALIAS", raising=False)
        monkeypatch.delenv("WFF_KEYSTORE_PASSWORD", raising=False)
        with pytest.raises(RuntimeError, match="WFF_KEYSTORE"):
            wff_builder.resolve_signing_config()

    def test_production_rejects_dev_certificate_fingerprint(self, monkeypatch):
        """三件套齐但 keystore=公开开发证书 → 指纹比对拒绝（换文件名无效）。"""
        import wff_builder
        dev_copy = APK_OUTPUT_DIR / "renamed-prod.keystore"
        dev_copy.write_bytes((PROJECT_ROOT / "wff-builder" / "keystore" / "test.keystore").read_bytes())
        monkeypatch.setenv("WF_ENV", "production")
        monkeypatch.setenv("WFF_KEYSTORE", str(dev_copy))
        monkeypatch.setenv("WFF_KEYSTORE_ALIAS", "wfftest")
        monkeypatch.setenv("WFF_KEYSTORE_PASSWORD", "wfftest123")
        with pytest.raises(RuntimeError, match="PUBLIC dev"):
            wff_builder.resolve_signing_config()

    def test_dev_custom_keystore_requires_full_config(self, monkeypatch):
        import wff_builder
        monkeypatch.delenv("WF_ENV", raising=False)
        monkeypatch.setenv("WFF_KEYSTORE", str(APK_OUTPUT_DIR / "custom.keystore"))
        monkeypatch.delenv("WFF_KEYSTORE_ALIAS", raising=False)
        monkeypatch.delenv("WFF_KEYSTORE_PASSWORD", raising=False)
        with pytest.raises(RuntimeError, match="WFF_KEYSTORE_ALIAS"):
            wff_builder.resolve_signing_config()


# ─── S3: BYOK SSRF ───────────────────────────────────────

class TestSSRF:
    def _normalize(self, base_url, monkeypatch, resolved_ip="93.184.216.34"):
        from services.ai_gateway import ssrf_guard
        monkeypatch.setattr(
            ssrf_guard, "_resolve_all_ips",
            lambda host: [ipaddress.ip_address(resolved_ip)],
        )
        from services.ai_gateway import normalize_user_ai_config
        return normalize_user_ai_config({"api_key": "sk-x", "base_url": base_url, "model": "m"})

    @pytest.mark.parametrize("base_url", [
        "https://10.1.2.3/v1", "https://172.20.0.1/v1", "https://192.168.0.9/v1",
        "https://127.0.0.1/v1", "https://169.254.169.254/v1", "https://100.64.0.1/v1",
        "https://[::1]/v1", "https://[fe80::1]/v1", "https://[fc00::1]/v1",
    ])
    def test_private_ranges_rejected(self, base_url, monkeypatch):
        from services.ai_gateway import AIConfigError
        literal_ip = base_url.split("/")[2].strip("[]")
        with pytest.raises(AIConfigError):
            self._normalize(base_url, monkeypatch, resolved_ip=literal_ip)

    def test_private_resolution_rejected_for_domain(self, monkeypatch):
        from services.ai_gateway import AIConfigError
        with pytest.raises(AIConfigError):
            self._normalize("https://internal.corp/v1", monkeypatch, resolved_ip="10.0.0.5")

    def test_public_domain_allowed(self, monkeypatch):
        cfg = self._normalize("https://api.example.com/v1", monkeypatch)
        assert cfg["base_url"] == "https://api.example.com/v1"

    def test_whitelist_blocks_unlisted_host(self, monkeypatch):
        from services.ai_gateway import AIConfigError
        monkeypatch.setenv("WF_AI_ALLOWED_HOSTS", "api.openai.com")
        with pytest.raises(AIConfigError, match="允许列表"):
            self._normalize("https://api.deepseek.com/v1", monkeypatch)
        monkeypatch.delenv("WF_AI_ALLOWED_HOSTS", raising=False)

    def test_whitelist_suffix_wildcard(self, monkeypatch):
        monkeypatch.setenv("WF_AI_ALLOWED_HOSTS", "api.openai.com,*.deepseek.com")
        cfg = self._normalize("https://api.deepseek.com/v1", monkeypatch)
        assert cfg is not None
        monkeypatch.delenv("WF_AI_ALLOWED_HOSTS", raising=False)

    def test_openai_client_pins_no_redirects(self):
        """SDK 默认 follow_redirects=True（实测）; gateway 必须显式关闭。"""
        from services.ai_gateway import AIGateway
        gw = AIGateway(backend="openai", api_key="sk-x")
        # 触发 client 构建
        try:
            gw._call_openai("s", "u")
        except Exception:
            pass  # 请求会失败（无真实网络目标），只验证 client 配置
        if gw._openai_client is not None:
            # OpenAI SDK 的 httpx client 挂在 _client
            assert gw._openai_client._client.follow_redirects is False


# ─── S4: 鉴权与配额 ──────────────────────────────────────

class TestAuthAndQuota:
    def test_generate_rejects_invalid_key_when_configured(self, monkeypatch):
        monkeypatch.setenv("WFF_API_KEYS", "valid-key-123")
        r = client.post("/api/generate", json={"prompt": "x"})
        assert r.status_code == 401
        body = r.json()
        assert body["error"]["code"] == "INVALID_API_KEY"
        monkeypatch.delenv("WFF_API_KEYS", raising=False)

    def test_generate_503_in_production_without_keys(self, monkeypatch):
        monkeypatch.setenv("WF_ENV", "production")
        monkeypatch.delenv("WFF_API_KEYS", raising=False)
        r = client.post("/api/generate", json={"prompt": "x"})
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "API_KEYS_NOT_CONFIGURED"
        monkeypatch.delenv("WF_ENV", raising=False)

    def test_ai_test_401_with_bad_key(self, monkeypatch):
        monkeypatch.setenv("WFF_API_KEYS", "valid-key-123")
        r = client.post("/api/ai/test", json={"ai_config": {"api_key": "sk-x"}},
                        headers={"X-API-Key": "wrong"})
        assert r.status_code == 401
        monkeypatch.delenv("WFF_API_KEYS", raising=False)

    def test_quota_memory_fallback_in_dev(self, monkeypatch):
        """development + Redis 不可用 → 进程内降级（不抛 503）。"""
        from api.services import quota
        quota.reset_for_tests()
        monkeypatch.setattr(quota, "_get_redis", lambda: None)
        monkeypatch.delenv("WF_ENV", raising=False)
        quota.consume_ai_quota("test-identity", "generate")  # 不应抛
        quota.reset_for_tests()

    def test_quota_enforced_in_memory_fallback(self, monkeypatch):
        from api.services import quota
        from api.services.wff_access import WFFAPIError
        quota.reset_for_tests()
        monkeypatch.setattr(quota, "_get_redis", lambda: None)
        monkeypatch.setenv("WF_QUOTA_GENERATE_PER_HOUR", "2")
        try:
            quota.consume_ai_quota("q-identity", "generate")
            quota.consume_ai_quota("q-identity", "generate")
            with pytest.raises(WFFAPIError) as exc_info:
                quota.consume_ai_quota("q-identity", "generate")
            assert exc_info.value.status_code == 429
        finally:
            monkeypatch.delenv("WF_QUOTA_GENERATE_PER_HOUR", raising=False)
            quota.reset_for_tests()


# ─── 错误脱敏 ────────────────────────────────────────────

class TestErrorSanitize:
    def test_unknown_exception_not_leaked(self):
        from api.services.error_sanitize import safe_client_error
        secret = "/home/ops/credentials/token.txt"
        msg, request_id = safe_client_error(
            RuntimeError(f"failed opening {secret}"), context="unit")
        assert secret not in msg
        assert request_id
        assert "内部错误" in msg or "BUILD_FAILED" in msg

    def test_known_tool_error_mapped(self):
        from api.services.error_sanitize import safe_client_error
        msg, _ = safe_client_error(
            RuntimeError("apksigner not found at /opt/android-sdk/..."), context="unit")
        assert "签名工具不可用" in msg
        assert "/opt/android-sdk" not in msg

    def test_password_scrubbed_from_apksigner_stderr(self):
        import wff_builder
        cleaned = wff_builder._scrub_apksigner_error(
            "Keystore was tampered with, or password was wrong (pass:SuperSecret1)")
        assert "SuperSecret1" not in cleaned


# ─── S6: dockerignore 哨兵（无 Docker 的降级验证）────────

class TestDockerignore:
    """模拟 .dockerignore 匹配语义（fnmatch + 目录排除 + 否定规则）。"""

    @staticmethod
    def _is_excluded(rel_path: str, ignore_file: Path) -> bool:
        lines = [l.strip() for l in ignore_file.read_text(encoding="utf-8").splitlines()
                 if l.strip() and not l.startswith("#")]
        patterns, negations = [], []
        for line in lines:
            (negations if line.startswith("!") else patterns).append(
                line.lstrip("!"))
        import fnmatch

        def match(pattern: str, path: str) -> bool:
            if pattern.endswith("/"):
                pattern = pattern.rstrip("/")
                return path == pattern or path.startswith(pattern + "/")
            if fnmatch.fnmatch(path, pattern):
                return True
            # 目录规则作用于其下所有文件
            return fnmatch.fnmatch(path, pattern + "/*")

        excluded = any(match(p, rel_path) for p in patterns)
        if excluded:
            for n in negations:
                if match(n, rel_path):
                    return False
        return excluded

    def test_root_env_files_excluded(self):
        root = PROJECT_ROOT / ".dockerignore"
        assert self._is_excluded(".env", root)
        assert self._is_excluded(".env.production", root)
        assert not self._is_excluded(".env.example", root)  # 例外规则

    def test_root_ops_secrets_excluded(self):
        root = PROJECT_ROOT / ".dockerignore"
        assert self._is_excluded(".tools-backup-20260821", root)
        assert self._is_excluded("credentials/devspace.key", root)

    def test_git_and_dev_payloads_excluded(self):
        root = PROJECT_ROOT / ".dockerignore"
        assert self._is_excluded(".git/config", root)
        assert self._is_excluded("web/src/app/page.tsx", root)
        assert self._is_excluded("skills/wff-watchface-dev/SKILL.md", root)
        assert self._is_excluded("tests/test_api.py", root)

    def test_dev_keystore_explicitly_kept(self):
        root = PROJECT_ROOT / ".dockerignore"
        assert not self._is_excluded("wff-builder/keystore/test.keystore", root)
        # 其他私有 keystore 仍被排除
        assert self._is_excluded("ops/private.keystore", root)

    def test_web_dockerignore_excludes_env_and_modules(self):
        web = PROJECT_ROOT / "web" / ".dockerignore"
        assert self._is_excluded(".env.local", web)
        assert self._is_excluded("node_modules/next/index.js", web)
        assert self._is_excluded(".next/BUILD_ID", web)
        # 构建必需文件保留
        assert not self._is_excluded("package.json", web)
        assert not self._is_excluded("src/app/page.tsx", web)


# ─── 校验层状态（批 3-11 守护）────────────────────────────

class TestValidationLayers:
    def test_layers_field_present(self):
        from api.services.wff_validation import validate_wff
        xml = b"""<?xml version="1.0"?>
<WatchFace platform="WATCH" width="450" height="450">
  <Metadata key="CLOCK_TYPE"><String value="DIGITAL"/></Metadata>
</WatchFace>"""
        result = validate_wff(xml, [])
        assert "layers" in result and "degraded" in result
        assert result["layers"]["syntax"] in ("passed", "failed")
        # 本机无 Java 时 official 层应显式 unavailable 而非静默 passed
        if result["degraded"]:
            assert "official_validator" in result["layers"]
            assert result["layers"]["official_validator"] == "unavailable"

    def test_syntax_failure_marks_remaining_layers_not_run(self):
        """复查 R5: XML 语法失败提前返回 → 未执行的层标 not_run 而非 passed。"""
        from api.services.wff_validation import validate_wff
        bad = b"<?xml version='1.0'?><WatchFace><Unclosed"
        result = validate_wff(bad, [])
        assert result["valid"] is False
        assert result["layers"]["syntax"] == "failed"
        for layer in ("xsd", "official_validator", "lint"):
            assert result["layers"][layer] == "not_run", layer
        # 未执行层同样计入 degraded（结论不完整）
        assert result["degraded"] is True

    def test_valid_xml_runs_all_layers(self):
        from api.services.wff_validation import validate_wff
        xml = b"""<?xml version="1.0"?>
<WatchFace platform="WATCH" width="450" height="450">
  <Metadata key="CLOCK_TYPE"><String value="DIGITAL"/></Metadata>
</WatchFace>"""
        result = validate_wff(xml, [])
        for layer in ("syntax", "xsd", "official_validator", "lint"):
            status = result["layers"][layer]
            assert status in ("passed", "unavailable", "failed"), (layer, status)


# ─── 复查 R1: key 密码继承不落明文 ────────────────────────

class TestKeyPassInheritance:
    _PROD = {"WF_ENV": "production", "WFF_KEYSTORE": "/tmp/audit-fake.ks",
             "WFF_KEYSTORE_ALIAS": "release", "WFF_KEYSTORE_PASSWORD": "store-secret"}

    @staticmethod
    def _resolve(monkeypatch, cfg):
        import wff_builder as wb
        for k, v in cfg.items():
            monkeypatch.setenv(k, v)
        # 指纹检查绕开（本测试只验密码引用形式; 指纹绑定由 R2 测试覆盖）
        monkeypatch.setattr(wb, "_keystore_sha256", lambda *a, **k: "AA:BB:CC")
        return wb.resolve_signing_config()

    def test_key_pass_inherits_store_env_ref(self, monkeypatch):
        """key 密码省略 → 复用 store 的 env: 引用（非 pass: 明文）。"""
        cfg = dict(self._PROD)
        monkeypatch.delenv("WFF_KEY_KEY_PASSWORD", raising=False)
        monkeypatch.delenv("WFF_KEY_KEY_PASSWORD_FILE", raising=False)
        sc = self._resolve(monkeypatch, cfg)
        assert sc.ks_pass_ref == "env:WFF_KEYSTORE_PASSWORD"
        assert sc.key_pass_ref == "env:WFF_KEYSTORE_PASSWORD"
        assert not sc.key_pass_ref.startswith("pass:")

    def test_key_pass_inherits_store_file_ref(self, monkeypatch, tmp_path):
        cfg = dict(self._PROD)
        del cfg["WFF_KEYSTORE_PASSWORD"]
        secret = tmp_path / "ks-pass"
        secret.write_text("store-secret", encoding="utf-8")
        monkeypatch.setenv("WFF_KEYSTORE_PASSWORD_FILE", str(secret))
        monkeypatch.delenv("WFF_KEY_KEY_PASSWORD", raising=False)
        monkeypatch.delenv("WFF_KEY_KEY_PASSWORD_FILE", raising=False)
        sc = self._resolve(monkeypatch, cfg)
        assert sc.ks_pass_ref == f"file:{secret}"
        assert sc.key_pass_ref == f"file:{secret}"

    def test_key_pass_explicit_env_wins(self, monkeypatch):
        monkeypatch.setenv("WFF_KEY_KEY_PASSWORD", "key-secret")
        monkeypatch.delenv("WFF_KEY_KEY_PASSWORD_FILE", raising=False)
        sc = self._resolve(monkeypatch, dict(self._PROD))
        assert sc.ks_pass_ref == "env:WFF_KEYSTORE_PASSWORD"
        assert sc.key_pass_ref == "env:WFF_KEY_KEY_PASSWORD"

    def test_key_pass_explicit_file_wins(self, monkeypatch, tmp_path):
        monkeypatch.delenv("WFF_KEY_KEY_PASSWORD", raising=False)
        key_secret = tmp_path / "key-pass"
        key_secret.write_text("key-secret", encoding="utf-8")
        monkeypatch.setenv("WFF_KEY_KEY_PASSWORD_FILE", str(key_secret))
        sc = self._resolve(monkeypatch, dict(self._PROD))
        assert sc.key_pass_ref == f"file:{key_secret}"


# ─── 复查 R2: 指纹绑定 alias（需 keytool, 无则 skip）──────

class TestFingerprintAliasBinding:
    def _make_keystore(self, tmp_path):
        """两个 alias: fresh(新密钥对) + devcert(导入公开开发证书, 无私钥)。"""
        import subprocess as sp
        keytool = sp.run(["which", "keytool"], capture_output=True, text=True).stdout.strip()
        if not keytool:
            pytest.skip("keytool not available (JDK required)")
        ks = tmp_path / "multi.ks"
        sp.run([keytool, "-genkeypair", "-alias", "fresh", "-keyalg", "RSA",
                "-keysize", "2048", "-validity", "1", "-storepass", "tmpstore",
                "-keypass", "tmpstore", "-dname", "CN=fresh", "-keystore", str(ks)],
               capture_output=True, check=True)
        # 导入公开开发证书（导出到临时 PEM 再 import）
        dev_ks = PROJECT_ROOT / "wff-builder" / "keystore" / "test.keystore"
        pem = tmp_path / "dev.pem"
        sp.run([keytool, "-exportcert", "-rfc", "-alias", "wfftest",
                "-storepass", "wfftest123", "-keystore", str(dev_ks),
                "-file", str(pem)], capture_output=True, check=True)
        sp.run([keytool, "-importcert", "-alias", "devcert", "-noprompt",
                "-storepass", "tmpstore", "-keystore", str(ks), "-file", str(pem)],
               capture_output=True, check=True)
        return ks

    def test_fingerprint_follows_alias_not_first_entry(self, tmp_path):
        """多证书库: fresh alias 指纹 ≠ dev 指纹, devcert alias 指纹 == dev 指纹。"""
        import wff_builder as wb
        ks = self._make_keystore(tmp_path)
        import os
        old = (os.environ.get("WFF_KEYSTORE_PASSWORD"),)
        os.environ["WFF_KEYSTORE_PASSWORD"] = "tmpstore"
        try:
            fresh_fp = wb._keystore_sha256(ks, "fresh",
                                           "WFF_KEYSTORE_PASSWORD", "WFF_KEYSTORE_PASSWORD_FILE")
            dev_fp = wb._keystore_sha256(ks, "devcert",
                                         "WFF_KEYSTORE_PASSWORD", "WFF_KEYSTORE_PASSWORD_FILE")
        finally:
            os.environ["WFF_KEYSTORE_PASSWORD"] = old[0] or ""
        assert fresh_fp != wb.DEV_CERT_SHA256_COLONS
        assert dev_fp == wb.DEV_CERT_SHA256_COLONS  # 绑定 alias: devcert 就是 dev 证书

    def test_unknown_alias_rejected(self, tmp_path):
        import wff_builder as wb
        ks = self._make_keystore(tmp_path)
        import os
        os.environ["WFF_KEYSTORE_PASSWORD"] = "tmpstore"
        with pytest.raises(RuntimeError):
            wb._keystore_sha256(ks, "nonexistent",
                                "WFF_KEYSTORE_PASSWORD", "WFF_KEYSTORE_PASSWORD_FILE")

    def test_verify_signed_fingerprint_mismatch_raises(self, monkeypatch, tmp_path):
        """签名后复核: 指纹不匹配必须拒绝（mock apksigner 输出）。"""
        import wff_builder as wb
        import subprocess as sp
        outputs = {
            ("print-certs",): sp.CompletedProcess([], 0,
                stdout="Signer #1 certificate SHA-256 digest: deadbeef", stderr=""),
        }
        def fake_run(cmd, **kw):
            key = tuple(a for a in cmd if a in ("print-certs",))
            return outputs.get(key, sp.CompletedProcess([], 0, stdout="", stderr=""))
        monkeypatch.setattr(wb.subprocess, "run", fake_run)
        builder = wb.WFFBuilder.__new__(wb.WFFBuilder)  # 只用方法, 不跑 __init__
        builder.log = lambda *a, **k: None
        with pytest.raises(RuntimeError):
            builder._verify_signed_fingerprint(Path("/tmp/fake.apk"), "AA:BB:CC")


# ─── 复查 R3: SSRF 生产强制白名单 ─────────────────────────

class TestSSRFProductionWhitelist:
    def test_production_without_whitelist_rejects_byok(self, monkeypatch):
        from services.ai_gateway import AIConfigError
        from services.ai_gateway.ssrf_guard import assert_safe_base_url
        monkeypatch.setenv("WF_ENV", "production")
        monkeypatch.delenv("WF_AI_ALLOWED_HOSTS", raising=False)
        with pytest.raises(AIConfigError):
            assert_safe_base_url("https://api.openai.com/v1")

    def test_production_with_whitelist_proceeds_to_dns_check(self, monkeypatch):
        from services.ai_gateway import AIConfigError
        from services.ai_gateway import ssrf_guard
        monkeypatch.setenv("WF_ENV", "production")
        monkeypatch.setenv("WF_AI_ALLOWED_HOSTS", "api.openai.com")
        # mock DNS: 返回公网 IP, 避免真实网络依赖
        import ipaddress as _ipa
        monkeypatch.setattr(ssrf_guard, "_resolve_all_ips",
                            lambda h: [_ipa.ip_address("93.184.216.34")])
        ssrf_guard.assert_safe_base_url("https://api.openai.com/v1")  # 不抛

    def test_development_without_whitelist_still_hard_checks(self, monkeypatch):
        from services.ai_gateway import AIConfigError
        from services.ai_gateway import ssrf_guard
        import ipaddress as _ipa
        monkeypatch.setenv("WF_ENV", "development")
        monkeypatch.delenv("WF_AI_ALLOWED_HOSTS", raising=False)
        monkeypatch.setattr(ssrf_guard, "_resolve_all_ips",
                            lambda h: [_ipa.ip_address("10.0.0.5")])
        with pytest.raises(AIConfigError):
            ssrf_guard.assert_safe_base_url("https://evil.example.com/v1")


# ─── 复查 R6: CDM 存储降级语义 ────────────────────────────

class TestCDMStoreDegradation:
    def test_memory_fallback_has_ttl(self, monkeypatch):
        from api.services import cdm_store
        monkeypatch.setattr(cdm_store, "_get_redis", lambda: None)
        cdm_store._memory_store.clear()
        cdm_store.store_cdm("11223344", {"a": 1}, ttl=60)
        assert cdm_store.load_cdm("11223344") == {"a": 1}
        # 模拟过期
        payload, exp = cdm_store._memory_store["11223344"]
        cdm_store._memory_store["11223344"] = (payload, exp - 61)
        assert cdm_store.load_cdm("11223344") is None
        assert "11223344" not in cdm_store._memory_store  # 懒清理

    def test_production_store_failure_fails_closed(self, monkeypatch):
        from api.services import cdm_store
        monkeypatch.setattr(cdm_store, "_get_redis", lambda: None)
        monkeypatch.setenv("WF_ENV", "production")
        with pytest.raises(RuntimeError):
            cdm_store.store_cdm("11223344", {"a": 1})

    def test_redis_failure_falls_back_to_memory(self, monkeypatch):
        from api.services import cdm_store

        class BrokenRedis:
            def set(self, *a, **k):
                raise ConnectionError("redis down")
            def get(self, *a, **k):
                raise ConnectionError("redis down")

        monkeypatch.setattr(cdm_store, "_get_redis", lambda: BrokenRedis())
        cdm_store._memory_store.clear()
        monkeypatch.delenv("WF_ENV", raising=False)
        cdm_store.store_cdm("11223344", {"b": 2})  # 断连 → 降级内存, 不抛
        # load 同样断连 → 内存取回
        assert cdm_store.load_cdm("11223344") == {"b": 2}
