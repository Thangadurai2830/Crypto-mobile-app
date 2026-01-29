"""Integration tests for API endpoints: health, markets, analytics, strategy."""
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_health(client):
    """GET /health returns 200 and status ok."""
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_health_detailed(client):
    """GET /health/detailed returns database and redis checks."""
    r = await client.get("/health/detailed")
    assert r.status_code in (200, 503)
    data = r.json()
    assert "checks" in data
    assert "database" in data["checks"]


@pytest.mark.asyncio
async def test_v1_health(client):
    """GET /v1/health returns 200."""
    r = await client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_markets_list_empty(client):
    """GET /v1/markets returns empty list when no data."""
    r = await client.get("/v1/markets")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_markets_list_with_data(client, seeded_market):
    """GET /v1/markets returns assets when seeded."""
    r = await client.get("/v1/markets")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    btc = next((x for x in data if x["symbol"] == "BTC"), None)
    assert btc is not None
    assert "latest_price" in btc


@pytest.mark.asyncio
async def test_markets_get_by_symbol(client, seeded_market):
    """GET /v1/markets/{symbol} returns asset."""
    r = await client.get("/v1/markets/BTC")
    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "BTC"
    assert data["latest_price"] is not None


@pytest.mark.asyncio
async def test_markets_get_invalid_symbol(client):
    """GET /v1/markets/{symbol} with invalid symbol returns 422."""
    r = await client.get("/v1/markets/INVALID!!")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_markets_get_404(client):
    """GET /v1/markets/UNKNOWN returns 404 when asset not found."""
    r = await client.get("/v1/markets/UNKNOWN")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_analytics(client):
    """GET /v1/analytics returns 200 and window_hours, assets."""
    r = await client.get("/v1/analytics", params={"window_hours": 24})
    assert r.status_code == 200
    data = r.json()
    assert "window_hours" in data
    assert "assets" in data
    assert data["window_hours"] == 24


@pytest.mark.asyncio
async def test_analytics_validation(client):
    """GET /v1/analytics with invalid window_hours returns 422."""
    r = await client.get("/v1/analytics", params={"window_hours": 9999})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_strategy_results(client):
    """GET /v1/strategy/results returns list."""
    r = await client.get("/v1/strategy/results", params={"limit": 5})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_strategy_run(client, seeded_market):
    """POST /v1/strategy/run returns run with signals or empty."""
    r = await client.post(
        "/v1/strategy/run",
        json={"strategy_name": "ma_crossover", "limit_per_symbol": 50},
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "strategy_name" in data
    assert "signals" in data


@pytest.mark.asyncio
async def test_strategy_run_invalid_name(client):
    """POST /v1/strategy/run with invalid strategy_name returns 422."""
    r = await client.post("/v1/strategy/run", json={"strategy_name": "invalid_strategy"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    """GET /metrics returns Prometheus text."""
    r = await client.get("/metrics")
    assert r.status_code == 200
    assert "request_count" in r.text or "http_requests" in r.text or "# HELP" in r.text
