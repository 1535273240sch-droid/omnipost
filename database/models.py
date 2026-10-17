from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AccountModel(Base):
    __tablename__ = "accounts"

    id = Column(String(64), primary_key=True)
    platform = Column(String(32), nullable=False, index=True)
    nickname = Column(String(128), nullable=False)
    avatar_url = Column(String(512), nullable=True)
    profile_dir = Column(String(512), nullable=False)
    proxy_url = Column(String(256), nullable=True)
    is_active = Column(Boolean, default=True)
    is_logged_in = Column(Boolean, default=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ContentModel(Base):
    __tablename__ = "contents"

    id = Column(String(64), primary_key=True)
    type = Column(String(32), nullable=False)
    title = Column(String(256), nullable=False)
    body = Column(Text, nullable=False)
    tags_json = Column(Text, default="[]")
    media_json = Column(Text, default="[]")
    cover_path = Column(String(512), nullable=True)
    schedule_at = Column(DateTime, nullable=True)
    ai_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PublishJobModel(Base):
    __tablename__ = "publish_jobs"

    id = Column(String(64), primary_key=True)
    content_id = Column(String(64), nullable=False, index=True)
    platform = Column(String(32), nullable=False, index=True)
    account_id = Column(String(64), nullable=False, index=True)
    rendered_json = Column(Text, default="{}")
    status = Column(String(32), default="pending", index=True)
    attempts = Column(Integer, default=0)
    result_url = Column(String(512), nullable=True)
    error_code = Column(String(64), nullable=True)
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
