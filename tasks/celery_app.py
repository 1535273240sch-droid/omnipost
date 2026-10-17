from celery import Celery
from config.settings import settings

celery_app = Celery(
    "omnipost",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["tasks.publish_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=900,         # 单个任务硬超时 15 分钟
    task_soft_time_limit=840,    # 软超时 14 分钟
    worker_concurrency=4,        # 并发 Worker 数量
    worker_prefetch_multiplier=1 # 每次预取一个任务，保证并发锁公平
)
