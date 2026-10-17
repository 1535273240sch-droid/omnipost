import webbrowser
import json
from pathlib import Path
from loguru import logger

from adapters.base import PlatformAdapter, LoginResult, PublishResult, JobStatus, ErrorCode
from config.settings import settings
from core.models.account import Account
from core.models.job import PublishJob

class ManualFallbackAdapter:
    """兜底的手动发布包适配器 (生成预填内容并打开发布页，由人点击最后一步)"""

    backend = "manual"
    capabilities = {"video", "image_text", "article"}

    def __init__(self, platform: str, publish_url: str):
        self.platform = platform
        self.publish_url = publish_url

    async def check_login(self, account: Account) -> bool:
        return True

    async def login(self, account: Account) -> LoginResult:
        webbrowser.open(self.publish_url)
        return LoginResult(success=True, account_id=account.id, nickname=account.nickname)

    async def publish(self, job: PublishJob, account: Account) -> PublishResult:
        """生成一键剪贴板/预填包，并拉起浏览器让用户人工最后核对并点击"""
        rendered = job.rendered
        pkg_dir = settings.DATA_DIR / "manual_packages" / job.id
        pkg_dir.mkdir(parents=True, exist_ok=True)

        package_manifest = pkg_dir / "package.json"
        with open(package_manifest, "w", encoding="utf-8") as f:
            json.dump(rendered, f, ensure_ascii=False, indent=2)

        readme_file = pkg_dir / "发布说明.txt"
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(f"【平台】: {self.platform}\n")
            f.write(f"【标题】: {rendered.get('title', '')}\n\n")
            f.write(f"【正文】:\n{rendered.get('body', '')}\n\n")
            f.write(f"【标签】: {', '.join(rendered.get('tags', []))}\n")
            f.write(f"【素材路径】: {', '.join(rendered.get('media_paths', []))}\n")

        logger.info(f"已为平台 {self.platform} 生成手动发布包: {pkg_dir}")
        webbrowser.open(self.publish_url)

        return PublishResult(
            success=False,
            job_id=job.id,
            error_code=ErrorCode.UNKNOWN_RESULT,
            error_msg="已生成手动发布包并打开发布页，待人工确认点击",
            require_human_confirm=True
        )

    async def fetch_status(self, job: PublishJob, account: Account) -> JobStatus:
        return job.status
