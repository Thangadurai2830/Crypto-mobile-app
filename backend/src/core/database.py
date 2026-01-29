"""Database session and engine configuration."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import get_settings

settings = get_settings()

# Connection pooling: pool_size and max_overflow only for PostgreSQL (SQLite/StaticPool rejects them).
_engine_kw: dict = {
    "echo": settings.debug,
    "future": True,
}
if "sqlite" not in settings.database_url:
    _engine_kw["pool_size"] = settings.db_pool_size
    _engine_kw["max_overflow"] = settings.db_max_overflow
    _engine_kw["pool_pre_ping"] = True

engine = create_async_engine(settings.database_url, **_engine_kw)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables. Call on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
