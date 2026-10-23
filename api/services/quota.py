"""服务端 AI 配额（审计 S4 修复）— Redis 原子固定窗口，多 worker 共享。

- 键: ``wff:quota:{operation}:{identity}``，窗口 1 小时（首次 INCR 设 TTL）
- INCR + EXPIRE 两条命令原子性说明: 首次 INCR 返回 1 后设置 TTL；进程在
  INCR 与 EXPIRE 间崩溃的窗口只影响 TTL 缺失（key 永不过期）→ 用
  pipeline 内执行, 且 GETEX/TTL 兜底刷新（见 _consume_redis）。
- production: Redis 不可用 → 429/503 拒绝（fail-closed，不消耗服务端额度）
- development: Redis 不可用 → 降级 wff_access 进程内令牌桶（单进程语义）
- 身份 = API key（可信）；development 未配置 key 体系时用固定开发身份。

配额默认值（可用环境变量覆盖）:
- generate: WF_QUOTA_GENERATE_PER_HOUR = 10
- ai/test:  WF_QUOTA_AI_TEST_PER_HOUR = 20
"""

import os
import time
from typing import Optional

from api.services.wff_access import WFFAPIError, configured_api_keys, limiter

_redis_client = None
_redis_checked = False


def _is_production() -> bool:
    return os.environ.get("WF_ENV", "development").strip().lower() == "production"


def _get_redis():
    """懒加载 Redis 客户端；不可用返回 None（每次调用重试连接）。"""
    global _redis_client, _redis_checked
    if _redis_client is not None:
        return _redis_client
    try:
        import redis  # noqa
        from api.tasks.celery_app import REDIS_URL
        client = redis.Redis.from_url(REDIS_URL, socket_timeout=2.0, socket_connect_timeout=2.0)
        client.ping()
        _redis_client = client
    except Exception:
        _redis_client = None
        _redis_checked = True
    return _redis_client


def reset_for_tests() -> None:
    global _redis_client, _redis_checked
    _redis_client = None
    _redis_checked = False
    limiter.reset()


# 公共别名：cdm_store 等服务复用同一 Redis 客户端（不可用时返回 None）
get_redis = _get_redis


def _consume_redis(key: str, limit: int) -> Optional[int]:
    """原子扣减一次配额；返回剩余次数；Redis 不可用返回 None。"""
    client = _get_redis()
    if client is None:
        return None
    try:
        pipe = client.pipeline(transaction=True)
        pipe.incr(key)
        pipe.ttl(key)
        results = pipe.execute()
        count = int(results[0])
        ttl = int(results[1])
        if ttl < 0:
            # 无 TTL（历史残留/竞态窗口）→ 修复为 1 小时
            client.expire(key, 3600)
        if count > limit:
            remaining_window = client.ttl(key)
            raise WFFAPIError(
                429, "RATE_LIMITED",
                f"配额已用尽（每 {3600 // 60} 分钟 {limit} 次），"
                f"{max(remaining_window, 1)} 秒后重试",
            )
        return limit - count
    except WFFAPIError:
        raise
    except Exception:
        # 连接中途失败 → 视为不可用
        global _redis_client
        _redis_client = None
        return None


def consume_ai_quota(identity: str, operation: str) -> None:
    """消耗一次配额；超限抛 WFFAPIError(429)。

    operation 决定默认配额与环境变量名:
    - "generate" | "ai_test": AI 消耗端点
    - "build_legacy" | "cdm_read" | "image": 复查 G1/G2/G3 入口统一
      （旧 CDM 构建/CDM 取回/图片处理, 2026-10-23）
    """
    defaults = {
        "generate": 10, "ai_test": 20,
        "build_legacy": 10, "cdm_read": 60, "image": 30,
    }
    env_names = {
        "generate": "WF_QUOTA_GENERATE_PER_HOUR",
        "ai_test": "WF_QUOTA_AI_TEST_PER_HOUR",
        "build_legacy": "WF_QUOTA_BUILD_LEGACY_PER_HOUR",
        "cdm_read": "WF_QUOTA_CDM_READ_PER_HOUR",
        "image": "WF_QUOTA_IMAGE_PER_HOUR",
    }
    limit = int(os.environ.get(env_names[operation], defaults[operation]))
    key = f"wff:quota:{operation}:{identity}"
    remaining = _consume_redis(key, limit)
    if remaining is not None:
        return
    # Redis 不可用
    if _is_production():
        raise WFFAPIError(
            503, "QUOTA_BACKEND_UNAVAILABLE",
            "配额后端（Redis）不可用：生产模式拒绝消耗服务端 AI 额度",
        )
    # development 降级：进程内令牌桶（容量=每小时配额, 补充速率=limit/3600）
    limiter.consume(identity, operation, limit)


def authorize_ai_endpoint(api_key: Optional[str], operation: str) -> str:
    """AI 消耗端点（/api/generate、/api/ai/test）鉴权。

    - 配置了 WFF_API_KEYS → 必须提供有效 key（401 无效/缺失）
    - production 且未配置 keys → 503（fail-closed：不允许匿名消耗服务端额度）
    - development 且未配置 keys → 固定开发身份放行（配额仍按该身份计）
    返回配额计费身份（= API key 或 "dev-anonymous"）。
    """
    keys = configured_api_keys()
    if not keys:
        if _is_production():
            raise WFFAPIError(
                503, "API_KEYS_NOT_CONFIGURED",
                "服务端尚未配置 WFF_API_KEYS（生产模式必须配置）",
            )
        return "dev-anonymous"
    if not api_key or api_key not in keys:
        raise WFFAPIError(401, "INVALID_API_KEY", "X-API-Key 无效或缺失")
    return api_key


def owner_digest(identity: str) -> str:
    """身份 → 稳定摘要（CDM 所有权绑定用, 不落存 key 原文）。

    identity = authorize_ai_endpoint 返回值（API key 原文或 "dev-anonymous"）。
    """
    import hashlib
    return "sha256:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]


def authorize_and_consume(api_key: Optional[str], operation: str) -> str:
    """鉴权 + 扣配额一步到位（复查 G1/G2/G3 入口统一用）。

    authorize_ai_endpoint 只鉴权不扣额（generate/ai_test 历史调用方自行
    两步组合）；新入口统一走本函数, 避免漏扣导致限流失效。
    """
    identity = authorize_ai_endpoint(api_key, operation)
    consume_ai_quota(identity, operation)
    return identity
