"""api.tasks — Celery 异步任务包

导入本包即初始化配置好的 celery app (redis broker),
保证 shared_task 正确绑定, 不会落到默认 amqp:// app。
"""

from api.tasks.celery_app import celery_app

__all__ = ["celery_app"]
