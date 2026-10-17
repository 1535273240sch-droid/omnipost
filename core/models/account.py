from datetime import datetime
from pydantic import BaseModel, Field

class Account(BaseModel):
    id: str                                  # 唯一账号标识，例如 acc_douyin_01
    platform: str                            # douyin / xiaohongshu / bilibili / baijiahao
    nickname: str
    avatar_url: str | None = None
    profile_dir: str                         # 物理独立隔离目录绝对路径
    proxy_url: str | None = None             # 专属绑定代理 (http://user:pass@host:port)
    is_active: bool = True
    is_logged_in: bool = False
    last_login_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
