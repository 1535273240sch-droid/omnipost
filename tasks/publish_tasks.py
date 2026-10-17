import asyncio
from loguru import logger
from tasks.celery_app import celery_app
from core.models.job import PublishJob
from core.models.account import Account
from tasks.dispatcher import task_dispatcher

@celery_app.task(bind=True, max_retries=3)
def async_publish_task(self, job_dict: dict, account_dict: dict):
    """Celery 异步发布任务入口"""
    job = PublishJob(**job_dict)
    account = Account(**account_dict)
    job.attempts = self.request.retries + 1

    logger.info(f"[Celery Worker] 正在执行任务 {job.id} (第 {job.attempts} 次尝试)")

    # 运行异步执行器
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(task_dispatcher.execute_job_now(job, account))

    if not result.success:
        if result.error_code == "RATE_LIMITED" and self.request.retries < self.max_retries:
            logger.warning(f"任务 {job.id} 触发频率限制，120秒后自动重试...")
            raise self.retry(countdown=120)

    return result.model_dump()
