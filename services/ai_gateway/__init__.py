"""
AI Gateway — 统一封装 LLM 调用

支持两种后端:
  1. z-ai CLI (服务端默认)
  2. OpenAI 兼容 API（服务端环境变量或用户临时 BYOK）

功能:
  - 调用 LLM 生成文本 (system + user prompt)
  - 自动重试 (最多 3 次)
  - JSON 输出解析
  - 限流 (单用户 10 次/小时)
"""

import json
import time
import subprocess
import os
from time import perf_counter
from typing import Optional
from urllib.parse import urlparse

DEFAULT_OPENAI_MODEL = "gpt-4o"
MAX_API_KEY_LENGTH = 512
MAX_BASE_URL_LENGTH = 512
MAX_MODEL_LENGTH = 128


class AIConfigError(ValueError):
    """用户 AI 配置无效；错误消息不得包含密钥内容。"""


def normalize_user_ai_config(value: object) -> Optional[dict[str, str]]:
    """校验浏览器提交的临时 OpenAI 兼容配置，不持久化任何字段。"""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise AIConfigError("ai_config 必须是对象")

    api_key = str(value.get("api_key", "")).strip()
    base_url = str(value.get("base_url", "")).strip()
    model = str(value.get("model", "")).strip() or DEFAULT_OPENAI_MODEL
    if not api_key:
        return None
    if len(api_key) > MAX_API_KEY_LENGTH:
        raise AIConfigError("AI API Key 长度超出限制")
    if len(base_url) > MAX_BASE_URL_LENGTH or len(model) > MAX_MODEL_LENGTH:
        raise AIConfigError("AI 服务地址或模型名称长度超出限制")
    if any(ord(char) < 32 for char in api_key + base_url + model):
        raise AIConfigError("AI 配置包含非法控制字符")
    if base_url:
        parsed = urlparse(base_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise AIConfigError("自定义 Base URL 必须是无内嵌凭据的 HTTPS 地址")
        if parsed.query or parsed.fragment:
            raise AIConfigError("自定义 Base URL 不能包含查询参数或片段")
        # 审计 S3: SSRF 硬检查（私网/回环/保留段 + 全量 A/AAAA 解析 +
        # 可选 WF_AI_ALLOWED_HOSTS 白名单）
        from .ssrf_guard import assert_safe_base_url
        assert_safe_base_url(base_url)

    return {"api_key": api_key, "base_url": base_url, "model": model}

# ─── 限流（复查 R4: 已移除）────────────────────────────
# 旧内存令牌桶（check_rate_limit/record_request, user_id 维度 10/h）与
# 路由层 Redis 配额（api/services/quota.py: X-API-Key 维度、429/503 语义、
# 生产 fail-closed）冲突且语义弱，已整体删除。HTTP 链路限流唯一入口
# = api/routes/generate.py 的 authorize_ai_endpoint()。

# ─── LLM 调用 ──────────────────────────────────────────

class AIGateway:
    """统一 AI 网关"""

    def __init__(
        self,
        backend: str = "auto",
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        backend: "z-ai" | "openai" | "auto"
        auto = 优先 z-ai, 不可用则 openai
        """
        self.backend = backend
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL")
        self.model = model or os.environ.get("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL
        self._openai_client = None

    def _get_backend(self) -> str:
        if self.backend != "auto":
            return self.backend
        # 用户显式提供的 OpenAI 兼容密钥优先于服务端 z-ai。
        if self.api_key:
            return "openai"
        # z-ai CLI 可用?
        try:
            r = subprocess.run(["z-ai", "--help"], capture_output=True, timeout=5)
            if r.returncode == 0:
                return "z-ai"
        except Exception:
            pass
        # OpenAI key 可用?
        raise RuntimeError("No AI backend available (z-ai CLI not found, no OPENAI_API_KEY)")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ) -> dict:
        """调用 LLM 生成文本, 返回 {success, content, backend, attempts}"""
        try:
            backend = self._get_backend()
        except Exception as exc:
            return {
                "success": False,
                "content": None,
                "backend": self.backend,
                "attempts": 0,
                "error": self._safe_error(exc),
            }
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                if backend == "z-ai":
                    content = self._call_zai(system_prompt, user_prompt)
                else:
                    content = self._call_openai(system_prompt, user_prompt)

                if content and content.strip():
                    return {
                        "success": True,
                        "content": content,
                        "backend": backend,
                        "attempts": attempt,
                    }
            except Exception as e:
                last_error = self._safe_error(e)
                if attempt < max_retries:
                    time.sleep(2 * attempt)  # 指数退避

        return {
            "success": False,
            "content": None,
            "backend": backend,
            "attempts": max_retries,
            "error": last_error,
        }

    def _safe_error(self, error: Exception) -> str:
        """返回适合客户端展示的错误，避免上游异常意外回显密钥。"""
        message = str(error)
        if self.api_key:
            message = message.replace(self.api_key, "[REDACTED]")
        return message[:500]

    def test_connection(self) -> dict:
        """用一次最小 completion 验证密钥、端点和所选模型是否都可用。"""
        started = perf_counter()
        try:
            content = self._call_openai(
                "You are an API connection test. Return JSON only.",
                'Return exactly {"ok":true}.',
                max_tokens=16,
                timeout_seconds=15.0,
            )
            if not content.strip():
                raise RuntimeError("AI 服务返回了空响应")
            return {
                "success": True,
                "model": self.model,
                "latency_ms": round((perf_counter() - started) * 1000),
            }
        except Exception as exc:
            return {
                "success": False,
                "model": self.model,
                "latency_ms": round((perf_counter() - started) * 1000),
                "error": self._safe_error(exc),
            }

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ) -> dict:
        """调用 LLM 生成 JSON, 自动解析"""
        result = self.generate(system_prompt, user_prompt, max_retries)
        if not result["success"]:
            return result

        content = result["content"]
        parsed = self._extract_json(content)
        if parsed is not None:
            result["json"] = parsed
            result["json_parsed"] = True
        else:
            result["json"] = None
            result["json_parsed"] = False
            result["json_error"] = "Failed to parse JSON from content"

        return result

    @staticmethod
    def _extract_json(content: str) -> Optional[dict]:
        """从 LLM 输出中提取 JSON (支持 markdown 代码块)"""
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            return None

    def _call_zai(self, system_prompt: str, user_prompt: str) -> str:
        """通过 z-ai CLI 调用"""
        cmd = [
            "z-ai", "chat",
            "-s", system_prompt,
            "-p", user_prompt,
            "-o", "/tmp/zai-output.json",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError(f"z-ai CLI failed: {r.stderr[:200]}")

        with open("/tmp/zai-output.json") as f:
            data = json.load(f)
        # z-ai 返回格式: {choices: [{message: {content: "..."}}]}
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
    ) -> str:
        """通过 OpenAI SDK 调用"""
        if self._openai_client is None:
            import httpx
            from openai import OpenAI
            if not self.api_key:
                raise RuntimeError("OpenAI backend requires an API key")
            client_options = {"api_key": self.api_key}
            if self.base_url:
                client_options["base_url"] = self.base_url
            # 审计 S3: openai SDK 默认跟随重定向（实测 follow_redirects=True），
            # 校验后的目标可经 3xx 跳到内部地址。显式关闭重定向跟随。
            client_options["http_client"] = httpx.Client(
                follow_redirects=False, timeout=30.0,
            )
            self._openai_client = OpenAI(**client_options, timeout=30.0, max_retries=0)

        request_options = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        if max_tokens is not None:
            request_options["max_tokens"] = max_tokens
        if timeout_seconds is not None:
            request_options["timeout"] = timeout_seconds
        r = self._openai_client.chat.completions.create(**request_options)
        return r.choices[0].message.content or ""
