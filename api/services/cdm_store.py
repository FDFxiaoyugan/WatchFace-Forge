"""生成任务 CDM 存取（审计：/api/editor/cdm/{task_id} 永远 404 的缺陷修复）。

- 生成链路在 CDM 校验通过后立即 store_cdm()（APK 构建失败也不丢 CDM，
  仍可进编辑器继续调整）
- 存储优先 Redis（key: wff:cdm:{task_id}，TTL 默认 1 小时，多 worker 共享、
  重启不丢）；Redis 不可用退化为进程内 dict（单进程语义）
- task_id 走 artifact_paths 同款白名单校验（防注入式键名）
"""

import json
import re
from typing import Optional

from api.services.quota import get_redis as _get_redis

_TASK_ID_RE = re.compile(r"^[a-f0-9]{8,32}$")
_CDM_TTL_SECONDS = 3600
_memory_store: dict[str, str] = {}


def store_cdm(task_id: str, cdm: dict, ttl: int = _CDM_TTL_SECONDS) -> None:
    task_id = str(task_id)
    if not _TASK_ID_RE.fullmatch(task_id):
        raise ValueError("invalid task id")
    payload = json.dumps(cdm, ensure_ascii=False)
    redis = _get_redis()
    if redis is not None:
        redis.set(f"wff:cdm:{task_id}", payload, ex=ttl)
    else:
        _memory_store[task_id] = payload


def load_cdm(task_id: str) -> Optional[dict]:
    task_id = str(task_id)
    if not _TASK_ID_RE.fullmatch(task_id):
        return None
    redis = _get_redis()
    if redis is not None:
        raw = redis.get(f"wff:cdm:{task_id}")
    else:
        raw = _memory_store.get(task_id)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None
