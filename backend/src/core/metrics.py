"""Prometheus metrics for request count, latency, and error rate (APM)."""
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# HTTP request total by method and path (without variable segments)
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path_template", "status_class"],
)

# Request duration in seconds (response time tracking)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path_template"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# HTTP errors (4xx, 5xx) for error rate monitoring
HTTP_ERRORS_TOTAL = Counter(
    "http_errors_total",
    "Total HTTP error responses (4xx, 5xx)",
    ["method", "path_template", "status_class"],
)


def get_status_class(status_code: int) -> str:
    """Return Prometheus-friendly status class: 2xx, 3xx, 4xx, 5xx."""
    if status_code < 300:
        return "2xx"
    if status_code < 400:
        return "3xx"
    if status_code < 500:
        return "4xx"
    return "5xx"


# Path segments that are literal (not IDs/symbols) for metrics grouping
_PATH_LITERALS = frozenset({
    "v1", "markets", "history", "analytics", "strategy", "results", "ingest", "run",
    "health", "auth", "register", "login", "verify-email", "request-password-reset", "reset-password",
    "me", "logout", "2fa", "enable", "verify", "disable",
})


def path_to_template(path: str) -> str:
    """Normalize path to a template for metrics (e.g. /v1/markets/BTC -> /v1/markets/{param})."""
    if not path.startswith("/"):
        return path
    parts = [p for p in path.split("/") if p]
    out = []
    for p in parts:
        if p in _PATH_LITERALS:
            out.append(p)
        elif p.isdigit():
            out.append("{id}")
        else:
            out.append("{param}")
    return "/" + "/".join(out) if out else "/"


def get_metrics_bytes() -> bytes:
    """Return Prometheus exposition format."""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Return content type for metrics response."""
    return CONTENT_TYPE_LATEST
