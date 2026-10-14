"""
异步任务定义 — Celery tasks

任务:
  process_image_task — 图像后处理 (抠图/裁剪/压缩)
  build_apk_task     — CDM → WFF → APK 构建

失败处理:
  - 指数退避重试 (3 次): delay = 2^retry * 10s
  - 重试耗尽 → 写入 dead_letter (Redis hash: dead:{task_id})
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Optional

from celery import shared_task, Task

logger = logging.getLogger(__name__)

# Redis 客户端 (延迟导入, 无 redis 时任务降级为同步执行)
_redis = None

def _get_redis():
    global _redis
    if _redis is None:
        import redis
        _redis = redis.from_url(
            __import__("api.tasks.celery_app", fromlist=["REDIS_URL"]).REDIS_URL,
            decode_responses=True,
        )
    return _redis


# ─── 死信工具 ─────────────────────────────────────────

def _send_to_dead_letter(task: Task, exc: Exception, payload: dict):
    """重试耗尽后, 记录到死信存储"""
    try:
        r = _get_redis()
        r.hset(f"dead:{task.request.id}", mapping={
            "task": task.name,
            "error": str(exc)[:500],
            "payload": json.dumps(payload, ensure_ascii=False)[:2000],
            "failed_at": time.time(),
        })
        r.expire(f"dead:{task.request.id}", 7 * 86400)  # 保留 7 天
        logger.error("task %s moved to dead letter: %s", task.request.id, exc)
    except Exception as e:
        # 死信写入失败不能阻塞任务结束
        logger.critical("dead letter write failed: %s", e)


# ─── 图像处理任务 ─────────────────────────────────────

@shared_task(
    bind=True,
    name="api.tasks.tasks.process_image_task",
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    retry_backoff=10,      # delay = 10 * 2^retry 秒
    retry_backoff_max=300,
    retry_jitter=True,
)
def process_image_task(self, image_b64: str, options: Optional[dict] = None) -> dict:
    """
    图像后处理异步任务

    args:
      image_b64 — base64 编码的图片
      options   — ProcessOptions 的 dict 形式

    returns:
      {success, image_b64?, format, width, height, sizes, bg_removed, ...}
    """
    import base64

    from api.services.image.processor import ProcessOptions, process_image

    payload = {"options": options or {}, "size": len(image_b64)}
    try:
        raw = base64.b64decode(image_b64)
        opts = ProcessOptions(**(options or {}))
        result = process_image(raw, opts)

        if not result.success:
            raise RuntimeError(result.error or "process failed")

        return {
            "success": True,
            "task_id": self.request.id,
            "image_b64": base64.b64encode(result.data).decode(),
            "format": result.format,
            "width": result.width,
            "height": result.height,
            "original_size": result.original_size,
            "processed_size": result.processed_size,
            "bg_removed": result.bg_removed,
            "cropped": result.cropped,
        }

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _send_to_dead_letter(self, exc, payload)
            return {"success": False, "error": str(exc), "dead_letter": True}
        raise self.retry(exc=exc)


# ─── APK 构建任务 ─────────────────────────────────────

@shared_task(
    bind=True,
    name="api.tasks.tasks.build_apk_task",
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=30,
    retry_backoff_max=600,
    retry_jitter=True,
)
def build_apk_task(self, cdm_dict: dict, task_id: Optional[str] = None) -> dict:
    """
    CDM → WFF XML → APK 构建任务

    args:
      cdm_dict — WatchFaceCDM 的 dict 形式
      task_id  — 业务任务 ID (用于产物命名)
    """
    import sys
    import shutil

    payload = {"cdm_name": cdm_dict.get("metadata", {}).get("name", "?")}
    try:
        task_id = task_id or str(uuid.uuid4())[:8]

        PROJECT_ROOT = Path(__file__).parent.parent.parent
        for p in (str(PROJECT_ROOT), str(PROJECT_ROOT / "wff-builder")):
            if p not in sys.path:
                sys.path.insert(0, p)

        from schema.cdm.models import WatchFaceCDM
        from compiler.wff.compiler import WFFCompiler
        from wff_builder import WFFBuilder, validate_watchface_xml

        cdm = WatchFaceCDM(**cdm_dict)
        compiler = WFFCompiler()
        wff_xml = compiler.compile(cdm)

        failures = validate_watchface_xml(wff_xml)
        errors = [f for f in failures if f["severity"] == "error"]
        if errors:
            # 校验错误是确定性错误, 不重试
            return {
                "success": False,
                "error": f"WFF validation failed: {errors[0]['detail']}",
                "no_retry": True,
            }

        import yaml

        from api.services.artifact_paths import final_apk_path, task_id_dir

        # S5: project dir / 产物文件名均只由服务端 task_id 决定
        project_dir = task_id_dir(task_id)
        project_dir.mkdir(exist_ok=True)
        (project_dir / "watchface.xml").write_text(wff_xml, encoding="utf-8")

        config = {
            "package_name": cdm.metadata.package_name,
            "version_code": cdm.metadata.version_code,
            "version_name": cdm.metadata.version_name,
            "watch_face_name": cdm.metadata.name,
            "wff_version": 1,
        }
        with open(project_dir / "project.yaml", "w") as f:
            yaml.dump(config, f)

        builder = WFFBuilder(str(project_dir), verbose=False)
        apk_path = builder.build()

        # S5: 文件名仅来自服务端 task_id; 表盘名仅作展示字段
        final_apk = final_apk_path(task_id)
        shutil.copy2(apk_path, final_apk)
        shutil.rmtree(project_dir, ignore_errors=True)

        return {
            "success": True,
            "task_id": task_id,
            "celery_id": self.request.id,
            "apk_filename": final_apk.name,
            "apk_size": final_apk.stat().st_size,
            "download_url": f"/api/download/{final_apk.name}",
        }

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _send_to_dead_letter(self, exc, payload)
            return {"success": False, "error": str(exc), "dead_letter": True}
        raise self.retry(exc=exc)
