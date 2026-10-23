"""生成任务 CDM 存取（审计：/api/editor/cdm/{task_id} 永远 404 的缺陷修复）。

- 生成链路在 CDM 校验通过后立即 store_cdm()（APK 构建失败也不丢 CDM，
  仍可进编辑器继续调整）
- 存储优先 Redis（key: wff:cdm:{task_id}，TTL 默认 1 小时，多 worker 共享、
  重启不丢）；Redis 不可用/中途断连退化为进程内 dict（复查 R6：带 TTL
  懒过期；断连时清共享客户端缓存并降级，恢复后自动切回）
- **WF_ENV=production 存档失败直接抛错**（fail-closed）：生产模式拒绝
  "声称已存档但实际取不回"的成功响应
- task_id 走 artifact_paths 同款白名单校验（防注入式键名）
"""

import json
import re
import time
from typing import Optional, Tuple

from api.services.quota import get_redis as _get_redis

_TASK_ID_RE = re.compile(r"^[a-f0-9]{8,32}$")
_CDM_TTL_SECONDS = 3600

# 复查 R6: 内存回退 (payload, expires_at)，读侧懒过期——不再永久驻留
_memory_store: dict[str, Tuple[str, float]] = {}


def _is_production() -> bool:
    return str(__import__("os").environ.get("WF_ENV", "development")).strip().lower() == "production"


def _reset_shared_client() -> None:
    """清 quota 模块缓存的 Redis 客户端（断连后坏客户端不留缓存）。"""
    try:
        from api.services import quota as _q
        global_client_clear = getattr(_q, "_reset_client_only", None)
        if callable(global_client_clear):
            global_client_clear()
        else:
            _q._redis_client = None  # noqa: SLF001（降级路径内部协同）
    except Exception:
        pass


def _store_in_memory(task_id: str, payload: str, ttl: int) -> None:
    _memory_store[task_id] = (payload, time.time() + ttl)


def _load_from_memory(task_id: str) -> Optional[str]:
    entry = _memory_store.get(task_id)
    if entry is None:
        return None
    payload, expires_at = entry
    if time.time() >= expires_at:  # 懒过期
        del _memory_store[task_id]
        return None
    return payload


def store_cdm(task_id: str, cdm: dict, ttl: int = _CDM_TTL_SECONDS,
              owner: Optional[str] = None) -> None:
    """存档 CDM。

    development: Redis 可用写 Redis；不可用/断连降级进程内存。
    production: Redis 不可用或写入失败 → RuntimeError（调用方应失败该次
    生成，不得返回"已存档"的成功响应）。
    owner: 复查 G2 所有权摘要（quota.owner_digest(identity)），存为
    payload 顶层 ``_owner`` 字段；取回时由路由层校验（key 不匹配 → 404）。
    存 None 则不绑定（历史记录/匿名）。
    """
    task_id = str(task_id)
    if not _TASK_ID_RE.fullmatch(task_id):
        raise ValueError("invalid task id")
    if owner is not None:
        cdm = {**cdm, "_owner": owner}
    payload = json.dumps(cdm, ensure_ascii=False)
    redis = _get_redis()
    if redis is not None:
        try:
            redis.set(f"wff:cdm:{task_id}", payload, ex=ttl)
            return
        except Exception:
            # 中途断连：清坏客户端缓存，走降级路径
            _reset_shared_client()
    if _is_production():
        raise RuntimeError(
            "CDM 存档失败（Redis 不可用）；生产模式拒绝返回不可取回的结果"
        )
    _store_in_memory(task_id, payload, ttl)


def load_cdm(task_id: str) -> Optional[dict]:
    """取回 CDM；Redis 与内存均无记录或已过期 → None。

    复查 R6: Redis 断连时自动降级读内存（此前直接 500/404）。
    """
    task_id = str(task_id)
    if not _TASK_ID_RE.fullmatch(task_id):
        return None
    redis = _get_redis()
    raw = None
    if redis is not None:
        try:
            raw = redis.get(f"wff:cdm:{task_id}")
        except Exception:
            _reset_shared_client()
            raw = None
    if raw is None:
        raw = _load_from_memory(task_id)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def reset_for_tests() -> None:
    """测试隔离：清内存存储与 Redis 客户端缓存。"""
    global _memory_store
    _memory_store = {}
    from api.services import quota as _q
    _q.reset_for_tests()
