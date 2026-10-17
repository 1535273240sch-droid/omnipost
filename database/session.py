import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from loguru import logger

from config.settings import settings
from database.models import Base

# 优先尝试 PostgreSQL，失败则平滑降级至本地轻量 SQLite 保证系统即刻可用
try:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
except Exception:
    logger.warning("PostgreSQL 引擎配置初始化失败，降级为 SQLite")
    engine = create_async_engine(settings.SQLITE_FALLBACK_URL, echo=False)

async_session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """初始化数据库表结构 (自动建表)"""
    global engine, async_session_factory
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表结构校验与初始化成功")
    except Exception as e:
        logger.warning(f"连接目标数据库异常 ({e})，正在自动无缝降级为本地 SQLite 数据库...")
        engine = create_async_engine(settings.SQLITE_FALLBACK_URL, echo=False)
        async_session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"本地 SQLite 数据库初始化成功: {settings.SQLITE_FALLBACK_URL}")

async def get_session() -> AsyncSession:
    """获取异步数据库会话上下文"""
    async with async_session_factory() as session:
        yield session
