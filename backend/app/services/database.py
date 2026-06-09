import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

_engine = None
_session_factory: Optional[async_sessionmaker] = None


def _async_url(url: str) -> str:
    """Ensure the URL uses an async driver scheme."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _init_engine() -> None:
    global _engine, _session_factory
    if _engine is not None or not settings.database_url:
        return
    _engine = create_async_engine(
        _async_url(settings.database_url),
        pool_pre_ping=True,
        echo=settings.debug,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    logger.info("Database engine initialised")


async def init_db() -> None:
    _init_engine()
    if _engine is None:
        logger.info("DATABASE_URL not set — skipping table creation")
        return
    from app.models.portfolio import Base
    try:
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    except Exception as exc:
        logger.warning("Database unavailable at startup (%s) — continuing without it", exc)


async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    if _session_factory is None:
        _init_engine()
    if _session_factory is None:
        yield None
        return
    async with _session_factory() as session:
        yield session
