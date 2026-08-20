"""
Celery 应用配置 — 异步任务队列

队列设计:
  image  — 图像处理任务 (轻量, 高并发)
  build  — APK 构建任务 (重量, 低并发)
  dead_letter — 死信队列 (重试耗尽的任务)

可靠性:
  - 任务确认: task_acks_late (执行成功才 ack, 防止 worker 崩溃丢任务)
  - 预取: prefetch=1 (build 队列), 公平分发
  - 重试: 指数退避, 最多 3 次
  - 死信: 重试耗尽 → dead_letter 队列 + 状态标记
"""

from __future__ import annotations

import os

from celery import Celery

REDIS_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)

celery_app = Celery(
    "watchface_forge",
    broker=REDIS_URL,
    backend=RESULT_BACKEND,
)

celery_app.conf.update(
    # 序列化
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # 时区
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 可靠性: 执行成功才 ack
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # 队列路由
    task_routes={
        "api.tasks.tasks.process_image_task": {"queue": "image"},
        "api.tasks.tasks.build_apk_task": {"queue": "build"},
    },

    # 默认队列
    task_default_queue="default",

    # 重试策略 (broker 连接)
    broker_connection_retry_on_startup=True,

    # 结果过期 (24h)
    result_expires=86400,

    # 任务执行超时
    task_time_limit=300,          # 硬超时 5min
    task_soft_time_limit=240,     # 软超时 4min
)


def get_queue_info() -> dict:
    """返回队列拓扑信息 (供健康检查/文档)"""
    return {
        "queues": ["image", "build", "dead_letter", "default"],
        "routes": {
            "process_image_task": "image",
            "build_apk_task": "build",
        },
        "retry": {"max_retries": 3, "backoff": "exponential"},
        "dead_letter": "重试耗尽的任务进入 dead_letter 队列",
    }
