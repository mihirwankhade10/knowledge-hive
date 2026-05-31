"""
KnowledgeHive - Centralized Logging Configuration

Provides structured JSON logging for production and human-readable
colored output for development. All log messages automatically include
the current request_id when available.
"""

import logging
import sys
from contextvars import ContextVar

from pythonjsonlogger import json as json_log

# Context variable for request ID correlation
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Inject the current request_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get("-")  # type: ignore[attr-defined]
        return True


class _DevFormatter(logging.Formatter):
    """Human-readable formatter with level-based coloring for development."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        rid = getattr(record, "request_id", "-")
        prefix = f"{color}{record.levelname:7s}{self.RESET}"
        timestamp = self.formatTime(record, self.datefmt)
        msg = record.getMessage()
        base = f"{timestamp} | {prefix} | {record.name:30s} | rid={rid} | {msg}"
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            base += f"\n{record.exc_text}"
        return base


def setup_logging(debug: bool = False) -> None:
    """
    Configure application-wide logging.

    Args:
        debug: If True, use human-readable dev format.
               If False, use structured JSON format for production.
    """
    root = logging.getLogger()

    # Clear existing handlers to avoid duplicates on reload
    root.handlers.clear()

    root.setLevel(logging.DEBUG if debug else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    if debug:
        formatter = _DevFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    else:
        formatter = json_log.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
        )

    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Quiet noisy third-party loggers
    for noisy in ("httpx", "httpcore", "urllib3", "neo4j", "qdrant_client", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
