from datetime import datetime
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field

class ContentType(str, Enum):
    TEXT = "text"
    IMAGE_TEXT = "image_text"
    VIDEO = "video"
    ARTICLE = "article"

class MediaAsset(BaseModel):
    id: str
    path: str                     # 本地绝对路径
    type: str                     # "image" | "video"
    mime_type: str | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None

    def exists(self) -> bool:
        return Path(self.path).is_file()

class Content(BaseModel):
    id: str
    type: ContentType
    title: str = Field(..., max_length=200)
    body: str                     # 正文内容 (Markdown 格式)
    tags: list[str] = Field(default_factory=list)
    media: list[MediaAsset] = Field(default_factory=list)
    cover: MediaAsset | None = None
    schedule_at: datetime | None = None
    ai_generated: bool = False    # 用于合规标识 (部分平台要求勾选 AI 标识)
    created_at: datetime = Field(default_factory=datetime.utcnow)
