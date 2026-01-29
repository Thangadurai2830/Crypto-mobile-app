"""
Custom middleware for API v1.

- Request ID: add X-Request-ID to state and response header
- Rate limiting: per-IP (or X-Forwarded-For), configurable; exempts /health, /metrics
- Timing + structured request/response logging (JSON)
- Prometheus metrics (request count, latency)
- Sentry request_id tag when Sentry is enabled
"""
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.core.config import get_settings
from src.core.logging_config import get_logger
from src.core.metrics import (
    HTTP_ERRORS_TOTAL,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    get_status_class,
    path_to_template,
)
from src.core.rate_limit import check_rate_limit

logger = get_logger(__name__)
settings = get_settings()

# Paths that skip rate limiting
RATE_LIMIT_EXEMPT_PATHS = {"/health", "/health/detailed", "/metrics", "/ws", "/api/ws"}


def _is_websocket_upgrade(request: Request) -> bool:
    """True if this is a WebSocket upgrade request. BaseHTTPMiddleware must not modify WS responses."""
    return request.headers.get("upgrade", "").strip().lower() == "websocket"


def _client_identifier(request: Request) -> str:
    """Client identifier for rate limiting: X-Forwarded-For (first hop) or client host."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-client rate limiting. Adds X-RateLimit-Limit and X-RateLimit-Remaining to responses."""

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if _is_websocket_upgrade(request):
            return await call_next(request)
        path = request.url.path
        if path in RATE_LIMIT_EXEMPT_PATHS:
            return await call_next(request)

        identifier = _client_identifier(request)
        allowed, limit, remaining = await check_rate_limit(identifier)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Try again later.",
                    "retry_after_seconds": settings.rate_limit_window_seconds,
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(settings.rate_limit_window_seconds),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


def _set_sentry_request_id(request_id: str | None) -> None:
    """Set request_id as Sentry tag for error correlation."""
    if not request_id:
        return
    try:
        import sentry_sdk
        sentry_sdk.set_tag("request_id", request_id)
    except Exception:
        pass


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add a unique request ID to each request (state + response header)."""

    async def dispatch(self, request: Request, call_next: object) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        if _is_websocket_upgrade(request):
            return response
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Structured request/response logging and Prometheus metrics."""

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if _is_websocket_upgrade(request):
            return await call_next(request)
        start = time.perf_counter()
        request_id = getattr(request.state, "request_id", None)
        _set_sentry_request_id(request_id)
        path_template = path_to_template(request.url.path)

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            path_template=path_template,
            request_id=request_id,
        )

        response = await call_next(request)
        duration = time.perf_counter() - start
        status_class = get_status_class(response.status_code)

        # Prometheus
        REQUEST_COUNT.labels(
            method=request.method,
            path_template=path_template,
            status_class=status_class,
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            path_template=path_template,
        ).observe(duration)
        if status_class in ("4xx", "5xx"):
            HTTP_ERRORS_TOTAL.labels(
                method=request.method,
                path_template=path_template,
                status_class=status_class,
            ).inc()

        response.headers["X-Response-Time-Ms"] = f"{duration * 1000:.0f}"

        logger.info(
            "request_finished",
            method=request.method,
            path=request.url.path,
            path_template=path_template,
            status_code=response.status_code,
            duration_sec=round(duration, 4),
            request_id=request_id,
        )
        return response
