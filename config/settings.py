import os
from pathlib import Path
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "OmniPost - 全平台内容分发系统"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 路径配置
    BASE_DIR: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    PROFILES_DIR: Path = PROJECT_ROOT / "data" / "profiles"
    LOGS_DIR: Path = PROJECT_ROOT / "data" / "logs"
    RULES_FILE: Path = PROJECT_ROOT / "config" / "platform_rules.yaml"

    # 数据库配置 (优先 PostgreSQL，支持连接检测与灵活配置)
    DATABASE_URL: str = "postgresql+asyncpg://omnipost:omnipost_password@localhost:5432/omnipost_db"
    SQLITE_FALLBACK_URL: str = f"sqlite+aiosqlite:///{PROJECT_ROOT}/data/omnipost.db"

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery 配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # MatrixMedia CLI 路径 (子进程解耦调用)
    MATRIX_MEDIA_CLI_PATH: str = "matrix-media"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# 确保核心物理目录存在
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.PROFILES_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
