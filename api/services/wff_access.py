"""API key authentication and in-process token-bucket quotas for WFF v1 APIs."""

import os
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Set, Tuple


class WFFAPIError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass
class _Bucket:
    tokens: float
    updated_at: float


class TokenBucketLimiter:
    """Thread-safe fixed-capacity token bucket keyed by API key and operation."""

    def __init__(self):
        self._buckets: Dict[Tuple[str, str], _Bucket] = {}
        self._lock = threading.Lock()

    def consume(self, api_key: str, operation: str, capacity: int) -> None:
        now = time.monotonic()
        refill_per_second = capacity / 3600.0
        key = (api_key, operation)
        with self._lock:
            bucket = self._buckets.get(key, _Bucket(float(capacity), now))
            elapsed = max(0.0, now - bucket.updated_at)
            bucket.tokens = min(float(capacity), bucket.tokens + elapsed * refill_per_second)
            bucket.updated_at = now
            if bucket.tokens < 1.0:
                retry_after = max(1, int((1.0 - bucket.tokens) / refill_per_second))
                self._buckets[key] = bucket
                raise WFFAPIError(429, "RATE_LIMITED", f"请求过于频繁，请在 {retry_after} 秒后重试")
            bucket.tokens -= 1.0
            self._buckets[key] = bucket

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


limiter = TokenBucketLimiter()


def configured_api_keys() -> Set[str]:
    """Read comma-separated API keys on every request so rotations need no restart."""
    return {item.strip() for item in os.getenv("WFF_API_KEYS", "").split(",") if item.strip()}


def authorize(api_key: Optional[str], operation: str, capacity: int) -> str:
    keys = configured_api_keys()
    if not keys:
        raise WFFAPIError(503, "API_KEYS_NOT_CONFIGURED", "服务端尚未配置 WFF_API_KEYS")
    if not api_key or api_key not in keys:
        raise WFFAPIError(401, "INVALID_API_KEY", "X-API-Key 无效或缺失")
    limiter.consume(api_key, operation, capacity)
    return api_key
