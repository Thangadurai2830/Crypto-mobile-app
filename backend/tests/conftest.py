"""
Pytest fixtures for backend tests.

- Override settings: in-memory SQLite, rate limit/API key disabled.
- Session-scoped lifespan so tables exist; optional table cleanup between tests.
- Async client and DB session fixtures.
"""
import os
from collections.abc import AsyncGenerator
from typing import AsyncGenerator as TypedAsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.models.analytics import AnalyticsResult
from src.models.market import CryptoAsset, MarketData
from src.models.strategy import StrategyRun, StrategySignal

# Use in-memory SQLite and disable rate limit/API key for tests
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("API_KEY_ENABLED", "false")
get_settings.cache_clear()

from src.main import app  # noqa: E402


TEST_DATABASE_URL = os.environ["DATABASE_URL"]


@pytest_asyncio.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def _lifespan():
    """Run app lifespan once per session so DB tables exist."""
    async with app.router.lifespan_context(app):
        yield


@pytest_asyncio.fixture(scope="session")
def engine():
    """Return the global engine (in-memory SQLite when env is set)."""
    from src.core.database import engine as _engine
    return _engine


@pytest_asyncio.fixture
async def db_session(engine) -> TypedAsyncGenerator[AsyncSession, None]:
    """Yield an async DB session; rollback after test."""
    from src.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(_lifespan):
    """Async HTTP client for API tests. Depends on lifespan so tables exist."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def seeded_market(client):
    """Insert one asset and one price record for API tests that need data."""
    from datetime import datetime, timezone
    from decimal import Decimal
    from src.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        asset = CryptoAsset(
            symbol="BTC",
            name="Bitcoin",
            coingecko_id="bitcoin",
        )
        session.add(asset)
        await session.flush()
        session.add(MarketData(
            asset_id=asset.id,
            symbol="BTC",
            price=Decimal("50000.00"),
            volume=Decimal("1000"),
            timestamp=datetime.now(timezone.utc),
        ))
        await session.commit()
    yield
    # cleanup in clean_db_after_test


@pytest_asyncio.fixture(autouse=True)
async def clean_db_after_test(engine):
    """Clean market tables after each test for isolation. No-op if tables don't exist (e.g. unit-only run)."""
    yield
    from sqlalchemy.exc import OperationalError
    from src.core.database import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(delete(StrategySignal))
            await session.execute(delete(StrategyRun))
            await session.execute(delete(AnalyticsResult))
            await session.execute(delete(MarketData))
            await session.execute(delete(CryptoAsset))
            await session.commit()
    except OperationalError:
        pass
