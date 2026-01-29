"""Database transaction tests: rollback on error, isolation."""
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.models.market import CryptoAsset, MarketData
from decimal import Decimal
from datetime import datetime, timezone


@pytest_asyncio.fixture
async def session():
    """Yield a session; tests should not rely on commit (conftest cleans)."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest.mark.asyncio
async def test_rollback_on_error(session: AsyncSession):
    """Rollback reverts uncommitted changes."""
    asset = CryptoAsset(symbol="ROLLBACK_TEST", name="Rollback Test", coingecko_id="rollback")
    session.add(asset)
    await session.flush()
    asset_id = asset.id
    await session.rollback()
    # New session to check DB state
    async with AsyncSessionLocal() as s2:
        r = await s2.execute(select(CryptoAsset).where(CryptoAsset.symbol == "ROLLBACK_TEST"))
        assert r.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_commit_persists(session: AsyncSession):
    """Commit makes data visible to other sessions."""
    asset = CryptoAsset(symbol="COMMIT_TEST", name="Commit Test", coingecko_id="commit")
    session.add(asset)
    await session.commit()
    async with AsyncSessionLocal() as s2:
        r = await s2.execute(select(CryptoAsset).where(CryptoAsset.symbol == "COMMIT_TEST"))
        found = r.scalar_one_or_none()
        assert found is not None
        assert found.symbol == "COMMIT_TEST"
    # conftest clean_db_after_test will delete it


@pytest.mark.asyncio
async def test_isolation_two_sessions():
    """Two sessions see each other's commits after commit."""
    async with AsyncSessionLocal() as s1:
        asset = CryptoAsset(symbol="ISO_TEST", name="Isolation Test", coingecko_id="iso")
        s1.add(asset)
        await s1.commit()
    async with AsyncSessionLocal() as s2:
        r = await s2.execute(select(CryptoAsset).where(CryptoAsset.symbol == "ISO_TEST"))
        assert r.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_unique_constraint_violation(session: AsyncSession):
    """Duplicate symbol raises integrity error (unique constraint)."""
    session.add(CryptoAsset(symbol="DUP", name="Dup", coingecko_id="dup1"))
    await session.commit()
    async with AsyncSessionLocal() as s2:
        s2.add(CryptoAsset(symbol="DUP", name="Dup2", coingecko_id="dup2"))
        with pytest.raises(Exception):  # IntegrityError
            await s2.commit()
        await s2.rollback()
