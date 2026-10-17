import json
from loguru import logger

from adapters.base import PlatformAdapter, LoginResult, PublishResult, JobStatus, ErrorCode
from adapters.cli.base_cli import cli_executor
from core.models.account import Account
from core.models.job import PublishJob

class BaijiahaoCLIAdapter:
    """百家号发布适配器 (通过 MatrixMedia CLI 命令行子进程调用)"""

    platform = "baijiahao"
    backend = "cli"
    capabilities = {"article", "video", "image_text"}

    async def check_login(self, account: Account) -> bool:
        if not cli_executor.is_available():
            return account.is_logged_in

        exit_code, data, _ = await cli_executor.execute_command([
            "account", "check",
            "--platform", "baijiahao",
            "--profile", account.profile_dir
        ])
        return exit_code == 0 and bool(data and data.get("logged_in"))

    async def login(self, account: Account) -> LoginResult:
        if not cli_executor.is_available():
            return LoginResult(
                success=False,
                account_id=account.id,
                error_code=ErrorCode.UNSUPPORTED,
                error_msg="系统未检测到 MatrixMedia CLI 可执行文件"
            )

        exit_code, data, raw_out = await cli_executor.execute_command([
            "account", "login",
            "--platform", "baijiahao",
            "--profile", account.profile_dir
        ], timeout=180.0)

        if exit_code == 0:
            nickname = data.get("nickname") if data else account.nickname
            return LoginResult(success=True, account_id=account.id, nickname=nickname)
        return LoginResult(
            success=False,
            account_id=account.id,
            error_code=ErrorCode.LOGIN_EXPIRED,
            error_msg=f"百家号 CLI 登录失败: {raw_out}"
        )

    async def publish(self, job: PublishJob, account: Account) -> PublishResult:
        if not cli_executor.is_available():
            return PublishResult(
                success=False,
                job_id=job.id,
                error_code=ErrorCode.UNKNOWN_RESULT,
                error_msg="MatrixMedia CLI 工具未就绪，请在终端执行 'matrix-media' 或安装相关组件",
                require_human_confirm=True
            )

        rendered = job.rendered
        title = rendered.get("title", "")
        body = rendered.get("body", "")
        tags = ",".join(rendered.get("tags", []))
        media_paths = ",".join(rendered.get("media_paths", []))

        args = [
            "publish",
            "--platform", "baijiahao",
            "--profile", account.profile_dir,
            "--title", title,
            "--content", body,
            "--tags", tags,
            "--media", media_paths
        ]

        logger.info(f"正在调用 MatrixMedia 发布百家号文章/图文: {job.id}")
        exit_code, result_data, raw_out = await cli_executor.execute_command(args, timeout=600.0)

        if exit_code == 0:
            post_url = result_data.get("url") if result_data else None
            return PublishResult(success=True, job_id=job.id, result_url=post_url)
        else:
            return PublishResult(
                success=False,
                job_id=job.id,
                error_code=ErrorCode.UNKNOWN_RESULT,
                error_msg=f"百家号 CLI 发布失败(退出码 {exit_code}): {raw_out[:300]}",
                require_human_confirm=True
            )

    async def fetch_status(self, job: PublishJob, account: Account) -> JobStatus:
        return job.status

baijiahao_adapter = BaijiahaoCLIAdapter()
