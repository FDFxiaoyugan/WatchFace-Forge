"""api.tasks — Celery 异步任务包

导入本包即完成:
  1. 初始化配置好的 celery app (redis broker) + set_default
  2. 注册所有任务 (process_image_task / build_apk_task)

Worker 启动: celery -A api.tasks worker -Q image,default
(不能用 -A api.tasks.celery_app — 那样不会导入任务定义模块)
"""

from api.tasks.celery_app import celery_app
from api.tasks.tasks import process_image_task, build_apk_task  # noqa: F401

__all__ = ["celery_app", "process_image_task", "build_apk_task"]
