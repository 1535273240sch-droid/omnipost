import json
import random
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from filelock import FileLock, Timeout
from loguru import logger

from config.settings import settings
from core.profiles.models import AccountFingerprint, AccountEnvironment

# 常见的高权重真实 Windows Chrome User-Agent 种子库
REAL_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

VIEWPORT_PRESETS = [
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1600, "height": 900},
]

class ProfileManager:
    """账号物理隔离沙盒与硬件指纹管理中心"""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or settings.PROFILES_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_account_dir(self, account_id: str) -> Path:
        """获取并确保账号唯一的物理沙盒目录"""
        account_dir = self.base_dir / account_id
        account_dir.mkdir(parents=True, exist_ok=True)
        return account_dir

    def get_or_create_fingerprint(self, account_id: str) -> AccountFingerprint:
        """
        获取账号终身绑定的静态指纹。
        【核心防风控原则】：若已存在指纹文件，直接读取；绝不每次随机变动硬件指纹。
        """
        account_dir = self.get_account_dir(account_id)
        fp_path = account_dir / "fingerprint.json"

        if fp_path.is_file():
            try:
                with open(fp_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return AccountFingerprint(**data)
            except Exception as e:
                logger.warning(f"读取账号 {account_id} 指纹文件失败，将重新生成: {e}")

        # 首次创建：稳定生成并永久保存
        chosen_viewport = random.choice(VIEWPORT_PRESETS)
        chosen_ua = random.choice(REAL_USER_AGENTS)
        fingerprint = AccountFingerprint(
            user_agent=chosen_ua,
            viewport=chosen_viewport,
            device_scale_factor=1.0 if chosen_viewport["width"] >= 1920 else 1.25,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            canvas_noise_salt=uuid.uuid4().hex[:12]
        )

        with open(fp_path, "w", encoding="utf-8") as f:
            json.dump(fingerprint.model_dump(), f, ensure_ascii=False, indent=2)

        logger.info(f"账号 {account_id} 已成功生成并锚定专属硬件指纹: UA={chosen_ua[:35]}..., Viewport={chosen_viewport}")
        return fingerprint

    def get_environment(self, account_id: str, platform: str, proxy_url: str | None = None) -> AccountEnvironment:
        """获取账号完整的运行时隔离环境元数据"""
        account_dir = self.get_account_dir(account_id)
        fingerprint = self.get_or_create_fingerprint(account_id)
        return AccountEnvironment(
            account_id=account_id,
            platform=platform,
            profile_dir=str(account_dir.resolve()),
            proxy_url=proxy_url,
            fingerprint=fingerprint
        )

    @asynccontextmanager
    async def lock_account(self, account_id: str, timeout: float = 30.0) -> AsyncGenerator[bool, None]:
        """
        排他式独占锁：确保同一时刻、同一账号只能被单个进程/Worker启动和操作。
        采用双层防御：本地文件独占锁 (FileLock) + 预留 Redis 分布式锁。
        """
        account_dir = self.get_account_dir(account_id)
        lock_file = account_dir / ".profile.lock"
        file_lock = FileLock(str(lock_file), timeout=timeout)

        logger.debug(f"正在申请账号 {account_id} 运行时排他锁...")
        try:
            file_lock.acquire(timeout=timeout)
            logger.info(f"账号 {account_id} 已成功获取运行独占锁，环境完全物理隔离")
            yield True
        except Timeout:
            logger.error(f"账号 {account_id} 正在被其他发布任务或浏览器实例占用，申请超时！")
            raise RuntimeError(f"Account {account_id} is currently locked by another process.")
        finally:
            if file_lock.is_locked:
                file_lock.release()
                logger.debug(f"账号 {account_id} 已释放独占锁")

profile_manager = ProfileManager()
