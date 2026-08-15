"""
AI Gateway — 统一封装 LLM 调用

支持两种后端:
  1. z-ai SDK (默认, 无需 API key)
  2. OpenAI API (可选, 需 OPENAI_API_KEY)

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
from typing import Optional

# ─── 限流 ──────────────────────────────────────────────

_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 3600  # 1 hour
RATE_LIMIT_MAX = 10       # 10 requests per hour per user


def check_rate_limit(user_id: str = "default") -> bool:
    """检查用户是否超过限流"""
    now = time.time()
    history = _rate_limit_store.get(user_id, [])
    # 清理过期记录
    history = [t for t in history if now - t < RATE_LIMIT_WINDOW]
    _rate_limit_store[user_id] = history
    return len(history) < RATE_LIMIT_MAX


def record_request(user_id: str = "default"):
    """记录一次请求"""
    if user_id not in _rate_limit_store:
        _rate_limit_store[user_id] = []
    _rate_limit_store[user_id].append(time.time())


# ─── LLM 调用 ──────────────────────────────────────────

class AIGateway:
    """统一 AI 网关"""

    def __init__(self, backend: str = "auto"):
        """
        backend: "z-ai" | "openai" | "auto"
        auto = 优先 z-ai, 不可用则 openai
        """
        self.backend = backend
        self._openai_client = None

    def _get_backend(self) -> str:
        if self.backend != "auto":
            return self.backend
        # z-ai CLI 可用?
        try:
            r = subprocess.run(["z-ai", "--help"], capture_output=True, timeout=5)
            if r.returncode == 0:
                return "z-ai"
        except Exception:
            pass
        # OpenAI key 可用?
        if os.environ.get("OPENAI_API_KEY"):
            return "openai"
        raise RuntimeError("No AI backend available (z-ai CLI not found, no OPENAI_API_KEY)")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ) -> dict:
        """调用 LLM 生成文本, 返回 {success, content, backend, attempts}"""
        backend = self._get_backend()
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
                last_error = str(e)
                if attempt < max_retries:
                    time.sleep(2 * attempt)  # 指数退避

        return {
            "success": False,
            "content": None,
            "backend": backend,
            "attempts": max_retries,
            "error": last_error,
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

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """通过 OpenAI SDK 调用"""
        if self._openai_client is None:
            from openai import OpenAI
            self._openai_client = OpenAI()

        r = self._openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        return r.choices[0].message.content or ""
