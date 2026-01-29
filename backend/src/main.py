"""FastAPI application entry point."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response as StarletteResponse

from src.api.v1 import api_router
from src.api.v1.middleware import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
)
from src.core.config import get_settings
from src.core.database import AsyncSessionLocal, engine, init_db
from src.core.health import check_database, check_redis
from src.core.logging_config import configure_logging, get_logger
from src.core.metrics import get_metrics_bytes, get_metrics_content_type
from src.core.security import validate_symbol
from src.models.market import MarketData
from src.services.data_ingestion import ingest_latest_prices
from src.tasks.scheduler import start_scheduler, stop_scheduler

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


def init_sentry() -> None:
    """Initialize Sentry if DSN is set."""
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.asyncio import AsyncioIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.sentry_environment or None,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            integrations=[FastApiIntegration(), AsyncioIntegration()],
            send_default_pii=False,
        )
        logger.info("sentry_initialized", dsn_configured=True)
    except Exception as e:
        logger.warning("sentry_init_failed", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init logging, Sentry, DB, initial ingest, scheduler. Shutdown: stop scheduler, dispose DB pool."""
    init_sentry()
    await init_db()
    try:
        async with AsyncSessionLocal() as session:
            await ingest_latest_prices(session)
            await session.commit()
    except Exception as e:
        logger.warning("initial_ingest_failed", error=str(e))
    start_scheduler(app)
    yield
    stop_scheduler()
    await engine.dispose()
    logger.info("graceful_shutdown", message="Scheduler stopped, DB pool disposed")


OPENAPI_TAGS = [
    {"name": "markets", "description": "Market data: list assets, get by symbol, trigger ingestion."},
    {"name": "prices", "description": "Current price for a symbol."},
    {"name": "history", "description": "Historical price/volume for a symbol."},
    {"name": "analytics", "description": "Computed analytics: change %, SMA/EMA, RSI, MACD, ranking."},
    {"name": "strategy", "description": "Run strategies and fetch results (signals)."},
]

app = FastAPI(
    title=settings.app_name,
    description="""
Crypto Market Data & Analytics API.

- **Markets:** List assets with latest price/volume; get by symbol; trigger ingestion.
- **Analytics:** Price/volume change %, moving averages, RSI, MACD, performance ranking.
- **Strategy:** Run backtests (MA crossover, momentum, momentum RSI); persist runs and signals.

**Authentication:** When `API_KEY_ENABLED=true`, send header `X-API-Key` on all `/v1` requests. Supports key rotation (current or previous key).
    """.strip(),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS: allow any localhost origin (Flutter web uses random port e.g. 60996) when enabled
def _is_localhost_origin(origin: str | None) -> bool:
    if not origin:
        return False
    return origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1")


class LocalhostCORSMiddleware(BaseHTTPMiddleware):
    """Allow any http://localhost:* or http://127.0.0.1:* origin for Flutter web dev."""

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        if not settings.cors_allow_localhost_any_port or not _is_localhost_origin(origin):
            return await call_next(request)
        if request.method == "OPTIONS":
            return StarletteResponse(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": str(settings.cors_max_age),
                },
            )
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        if settings.cors_expose_headers:
            response.headers["Access-Control-Expose-Headers"] = ", ".join(settings.cors_expose_headers)
        return response


# CORS: LocalhostCORSMiddleware first (outermost) so OPTIONS from any localhost port gets 200 + CORS before router
if settings.cors_allow_localhost_any_port:
    app.add_middleware(LocalhostCORSMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_localhost_regex if settings.cors_allow_localhost_any_port else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=settings.cors_expose_headers,
    max_age=settings.cors_max_age,
)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# API v1 under /v1 and /api/v1
app.include_router(api_router, prefix="/v1")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict:
    """Root: when frontend isn't running, this tells users how to start the app."""
    return {
        "message": "Crypto Market API is running.",
        "docs": "/docs",
        "health": "/health",
        "frontend": "To use the app, run the frontend in another terminal: cd frontend && npm run dev, then open http://localhost:3000 (see CONNECTING.md).",
    }


@app.get("/health")
async def health() -> dict:
    """Simple health: returns 200 with status ok."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/health/detailed")
async def health_detailed() -> dict:
    """Detailed health: DB and Redis checks. Returns 503 if database is down."""
    db_check = await check_database()
    redis_check = await check_redis()

    checks = {"database": db_check, "redis": redis_check}
    db_ok = db_check["status"] == "ok"
    redis_ok = redis_check["status"] in ("ok", "skipped")
    body = {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "version": "1.0.0",
        "checks": checks,
    }
    if not db_ok:
        return JSONResponse(content=body, status_code=503)
    return body


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics (request count, latency)."""
    return Response(
        content=get_metrics_bytes(),
        media_type=get_metrics_content_type(),
    )


# WebSocket for real-time price updates (e.g. chart live data)
WS_PUSH_INTERVAL_SEC = 10


async def _websocket_prices_handler(websocket: WebSocket) -> None:
    """Shared handler: real-time price stream. Query param: symbol (e.g. ?symbol=BTC)."""
    await websocket.accept()
    raw = websocket.query_params.get("symbol") or ""
    if not raw:
        await websocket.send_json({"error": "Missing query param: symbol"})
        await websocket.close()
        return
    try:
        symbol = validate_symbol(raw)
    except ValueError:
        await websocket.send_json({"error": "Invalid symbol format"})
        await websocket.close()
        return
    try:
        while True:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(MarketData)
                    .where(MarketData.symbol == symbol)
                    .order_by(MarketData.timestamp.desc())
                    .limit(1)
                )
                row = result.scalar_one_or_none()
                if row:
                    await websocket.send_json({
                        "symbol": row.symbol,
                        "price": str(row.price),
                        "volume": str(row.volume) if row.volume is not None else None,
                        "timestamp": row.timestamp.isoformat() if hasattr(row.timestamp, "isoformat") else str(row.timestamp),
                    })
            await asyncio.sleep(WS_PUSH_INTERVAL_SEC)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass


@app.websocket("/ws")
async def websocket_prices(websocket: WebSocket):
    """Real-time price stream at /ws (root). Query param: symbol."""
    await _websocket_prices_handler(websocket)


@app.websocket("/api/ws")
async def websocket_prices_api(websocket: WebSocket):
    """Real-time price stream at /api/ws (for frontend proxy). Query param: symbol."""
    await _websocket_prices_handler(websocket)
