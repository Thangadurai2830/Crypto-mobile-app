"""Structured logging with JSON format (structlog) or stdlib fallback."""
import logging
import sys
from typing import Any

try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False

from src.core.config import get_settings

settings = get_settings()


def configure_logging() -> None:
    """Configure structlog for JSON structured logging, or stdlib fallback."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
        level=level,
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    if not HAS_STRUCTLOG:
        return
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.format_exc_info,
    ]
    if settings.log_json:
        processors = shared_processors + [structlog.processors.JSONRenderer()]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):  # structlog.stdlib.BoundLogger when structlog present
    """Return a bound logger for the given name (structlog or stdlib adapter)."""
    if HAS_STRUCTLOG:
        return structlog.get_logger(name)
    return _StdlibLoggerAdapter(logging.getLogger(name))


class _StdlibLoggerAdapter:
    """Thin adapter so callers can use .info(msg, key=val) or .info(msg, *args)."""

    def __init__(self, log: logging.Logger) -> None:
        self._log = log

    def _msg(self, msg: str, *args: Any, **kwargs: Any) -> str:
        if args:
            return msg % args if "%" in msg else msg + " " + " ".join(str(a) for a in args)
        if kwargs:
            extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{msg} {extra}" if msg else extra
        return msg

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.debug(self._msg(msg, *args, **kwargs))

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.info(self._msg(msg, *args, **kwargs))

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.warning(self._msg(msg, *args, **kwargs))

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.error(self._msg(msg, *args, **kwargs))

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.exception(self._msg(msg, *args, **kwargs))
