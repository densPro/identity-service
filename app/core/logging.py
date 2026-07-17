"""Centralized logging configuration for the Identity Service.

Usage
-----
Import the pre-configured root logger or get a child logger for any module:

    from app.core.logging import get_logger
    logger = get_logger(__name__)

    logger.info("User registered", extra={"user_id": str(user.id)})
    logger.error("Unexpected error", exc_info=True)

Format
------
* **Development** (LOG_FORMAT=text):  human-readable, colorized output.
* **Production** (LOG_FORMAT=json):   one JSON object per line — suitable for
  log aggregators (Datadog, CloudWatch, Loki, etc.).

Environment variables
---------------------
LOG_LEVEL   - Python log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
              Defaults to INFO.
LOG_FORMAT  - "json" or "text".  Defaults to "text".
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any


# ---------------------------------------------------------------------------
# ANSI color helpers (text formatter only)
# ---------------------------------------------------------------------------

_LEVEL_COLORS: dict[str, str] = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
}
_RESET = "\033[0m"
_BOLD  = "\033[1m"
_DIM   = "\033[2m"


class _ColoredFormatter(logging.Formatter):
    """Human-readable, colorized log lines for development consoles."""

    _FMT = (
        "{dim}{asctime}{reset} "
        "{color}{bold}{levelname:<8}{reset} "
        "{dim}[{name}]{reset} "
        "{message}"
    )

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        color = _LEVEL_COLORS.get(record.levelname, "")
        record.asctime = self.formatTime(record, self.datefmt)
        line = self._FMT.format(
            dim=_DIM,
            reset=_RESET,
            color=color,
            bold=_BOLD,
            asctime=record.asctime,
            levelname=record.levelname,
            name=record.name,
            message=record.getMessage(),
        )
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord.__dict__ and not k.startswith("_")
            and k not in (
                "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno",
                "funcName", "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "name", "asctime",
                "message",
            )
        }
        if extras:
            kv = "  ".join(f"{_DIM}{k}={_RESET}{v}" for k, v in extras.items())
            line = f"{line}  {kv}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


class _JsonFormatter(logging.Formatter):
    """Structured JSON log lines — one object per line."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
            "module":    record.module,
            "function":  record.funcName,
            "line":      record.lineno,
        }
        skip = {
            "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno",
            "funcName", "created", "msecs", "relativeCreated", "thread",
            "threadName", "processName", "process", "name", "asctime",
            "message", "taskName",
        }
        for k, v in record.__dict__.items():
            if k not in skip and not k.startswith("_"):
                payload[k] = v

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def setup_logging(level: str = "INFO", fmt: str = "text") -> None:
    """Configure the root logger.  Call once at application startup."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    if fmt.lower() == "json":
        formatter: logging.Formatter = _JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
    else:
        formatter = _ColoredFormatter(datefmt="%Y-%m-%d %H:%M:%S")

    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(numeric_level)
    root.handlers.clear()
    root.addHandler(handler)

    if numeric_level > logging.DEBUG:
        for noisy in ("sqlalchemy.engine", "sqlalchemy.pool", "asyncio", "uvicorn.access"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).debug(
        "Logging initialized", extra={"level": level, "format": fmt}
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger namespaced to *name* (typically ``__name__``)."""
    return logging.getLogger(name)
