import asyncio
from datetime import datetime
from loguru import logger

from core.models.job import PublishJob, JobStatus
from core.models.account import Account
from adapters.registry import adapter_registry
from adapters.base import PublishResult, ErrorCode
from database.session import async_session_factory
from database.models import PublishJobModel

class TaskDispatcher:
    """任务调度与执行中枢 (支持异步直调与 Celery 分布式投递)"""

    @classmethod
    async def execute_job_now(cls, job: PublishJob, account: Account) -> PublishResult:
        """
        在当前进程以安全异步方式直调执行（适合桌面端直接触发与冒烟测试）
        严格遵循：五维账号隔离、并发排他锁、只点一次发布按钮
        """
        adapter = adapter_registry.get(job.platform)
        logger.info(f"开始调度任务 {job.id} -> 目标平台 [{job.platform}], 账号 [{account.id}]")

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        await cls._update_job_record(job)

        try:
            # 委托适配器执行（适配器内部自动加持 Profile 独占锁与环境指纹）
            result: PublishResult = await adapter.publish(job, account)

            if result.success:
                job.status = JobStatus.SUCCESS
                job.result_url = result.result_url
                logger.info(f"任务 {job.id} 执行成功，链接: {result.result_url}")
            elif result.require_human_confirm or result.error_code == ErrorCode.UNKNOWN_RESULT:
                job.status = JobStatus.NEED_CONFIRM
                job.error_code = result.error_code.value if result.error_code else None
                job.error_msg = result.error_msg
                logger.warning(f"任务 {job.id} 需人工确认: {result.error_msg}")
            else:
                job.status = JobStatus.FAILED
                job.error_code = result.error_code.value if result.error_code else None
                job.error_msg = result.error_msg
                logger.error(f"任务 {job.id} 执行失败: {result.error_msg}")

            job.finished_at = datetime.utcnow()
            await cls._update_job_record(job)
            return result

        except Exception as e:
            logger.exception(f"任务 {job.id} 调度遭遇非预期异常: {e}")
            job.status = JobStatus.FAILED
            job.error_code = "EXCEPTION"
            job.error_msg = str(e)
            job.finished_at = datetime.utcnow()
            await cls._update_job_record(job)
            return PublishResult(success=False, job_id=job.id, error_msg=str(e))

    @classmethod
    async def _update_job_record(cls, job: PublishJob):
        """同步持久化任务状态到数据库"""
        try:
            async with async_session_factory() as session:
                record = await session.get(PublishJobModel, job.id)
                if not record:
                    record = PublishJobModel(
                        id=job.id,
                        content_id=job.content_id,
                        platform=job.platform,
                        account_id=job.account_id,
                        rendered_json=str(job.rendered),
                        status=job.status.value,
                        attempts=job.attempts,
                        result_url=job.result_url,
                        error_code=job.error_code,
                        error_msg=job.error_msg,
                        created_at=job.created_at,
                        started_at=job.started_at,
                        finished_at=job.finished_at,
                    )
                    session.add(record)
                else:
                    record.status = job.status.value
                    record.attempts = job.attempts
                    record.result_url = job.result_url
                    record.error_code = job.error_code
                    record.error_msg = job.error_msg
                    record.started_at = job.started_at
                    record.finished_at = job.finished_at
                await session.commit()
        except Exception as e:
            logger.warning(f"更新任务记录失败 (已忽略，不影响发布): {e}")

task_dispatcher = TaskDispatcher()
