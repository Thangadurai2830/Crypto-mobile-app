"""Load tests for data ingestion and list APIs: concurrent requests."""
import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.main import app

# Number of concurrent requests and iterations for load test
CONCURRENT_REQUESTS = 20
REQUESTS_PER_CLIENT = 5


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as ac:
        yield ac


@pytest.mark.asyncio
@pytest.mark.slow
async def test_list_markets_concurrent(client):
    """Many concurrent GET /v1/markets requests complete without errors."""
    async def one_request():
        r = await client.get("/v1/markets")
        assert r.status_code == 200
        return r

    tasks = [one_request() for _ in range(CONCURRENT_REQUESTS)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    errors = [r for r in results if isinstance(r, Exception)]
    assert len(errors) == 0, f"Concurrent requests failed: {errors}"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_analytics_concurrent(client):
    """Many concurrent GET /v1/analytics requests complete without errors."""
    async def one_request():
        r = await client.get("/v1/analytics", params={"window_hours": 24})
        assert r.status_code == 200
        return r

    tasks = [one_request() for _ in range(CONCURRENT_REQUESTS)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    errors = [r for r in results if isinstance(r, Exception)]
    assert len(errors) == 0, f"Concurrent requests failed: {errors}"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_health_sustained(client):
    """Sustained health checks complete successfully."""
    async def one_request():
        return await client.get("/health")

    tasks = [one_request() for _ in range(REQUESTS_PER_CLIENT * CONCURRENT_REQUESTS)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            raise r
        assert r.status_code == 200
