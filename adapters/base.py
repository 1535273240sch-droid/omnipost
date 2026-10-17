from enum import Enum
from typing import Protocol, runtime_checkable
from pydantic import BaseModel, Field

from core.models.account import Account
from core.models.job import PublishJob, JobStatus

class ErrorCode(str, Enum):
    LOGIN_EXPIRED = "LOGIN_EXPIRED"       # 登录态失效，需重新扫码/登录
    NEED_VERIFY = "NEED_VERIFY"           # 触发验证码或滑动验证，需人工介入
    RATE_LIMITED = "RATE_LIMITED"         # 触发频率限制，进入冷却
    RULE_VIOLATION = "RULE_VIOLATION"     # 违反平台内容规范，不自动重试
    SELECTOR_CHANGED = "SELECTOR_CHANGED" # 页面改版选择器失效，发出告警
    UNSUPPORTED = "UNSUPPORTED"           # 平台不支持当前内容类型
    UNKNOWN_RESULT = "UNKNOWN_RESULT"     # 点击发布后无法确认状态，人工核对防重发

class LoginResult(BaseModel):
    success: bool
    account_id: str
    nickname: str | None = None
    avatar_url: str | None = None
    error_code: ErrorCode | None = None
    error_msg: str | None = None

class PublishResult(BaseModel):
    success: bool
    job_id: str
    result_url: str | None = None
    error_code: ErrorCode | None = None
    error_msg: str | None = None
    require_human_confirm: bool = False

@runtime_checkable
class PlatformAdapter(Protocol):
    """平台适配器通用标准接口规范"""
    platform: str                  # 如 douyin, xiaohongshu, bilibili, baijiahao
    backend: str                   # browser / cli / api / manual
    capabilities: set[str]         # video, image_text, article, schedule

    async def login(self, account: Account) -> LoginResult:
        """拉起环境引导登录 (首次由用户扫码，随后持久化 Profile)"""
        ...

    async def check_login(self, account: Account) -> bool:
        """检查账号的持久化 Profile 登录态是否仍然有效"""
        ...

    async def publish(self, job: PublishJob, account: Account) -> PublishResult:
        """
        执行发布任务。
        硬性约定：
        1. 发布按钮只点击一次；
        2. 无法确认结果标记 UNKNOWN_RESULT，绝不随意二次点击；
        3. 内部不保存明文密码，仅依赖隔离 Profile。
        """
        ...

    async def fetch_status(self, job: PublishJob, account: Account) -> JobStatus:
        """查询任务最新状态"""
        ...
