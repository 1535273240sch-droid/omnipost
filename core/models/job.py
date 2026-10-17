from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    NEED_CONFIRM = "need_confirm"

class PublishJob(BaseModel):
    id: str
    content_id: str
    platform: str                 # 如 douyin, xiaohongshu, bilibili, baijiahao
    account_id: str
    rendered: dict = Field(default_factory=dict) # 按平台规则改写后的内容
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    result_url: str | None = None
    error_code: str | None = None
    error_msg: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None
