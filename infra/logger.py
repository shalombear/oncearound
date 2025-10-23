"""Structured JSON logger for consistent, machine-readable application logging."""

import sys
import os

import logging
import atexit
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Final, Literal, Mapping, Optional, TypedDict
from contextlib import suppress
from pythonjsonlogger import jsonlogger

Level = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class LoggerConfig(TypedDict):
    level: Level
    log_path: str
    rotate_size: int
    retention_count: int
    encoding: str

DEFAULT_LOG_LEVEL: Final[Level] = "INFO"
DEFAULT_LOG_PATH: Final[str] = "./logs/app.log"
DEFAULT_ROTATE_SIZE: Final[int] = 100 * 1024 * 1024
DEFAULT_RETENTION_COUNT: Final[int] = 10
DEFAULT_ENCODING: Final[str] = "utf-8"

_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})

def _shutdown_handlers() -> None:
    root = logging.getLogger()
    for h in root.handlers[:]:
        with suppress(Exception):
            h.flush()
            h.close()
        root.removeHandler(h)

def _load_config(*, overrides: Optional[Mapping[str, Any]] = None) -> LoggerConfig:
    """Return merged logger configuration from defaults, env, and overrides."""
    cfg = {
        "level": DEFAULT_LOG_LEVEL,
        "log_path": DEFAULT_LOG_PATH,
        "rotate_size": DEFAULT_ROTATE_SIZE,
        "retention_count": DEFAULT_RETENTION_COUNT,
        "encoding": DEFAULT_ENCODING,
    }

    # deriving env-based keys, e.g. LOG_LEVEL -> level
    env_cfg = {key[4:].lower(): val for key, val in os.environ.items() if key.startswith("LOG_")}
    cfg.update(env_cfg)

    if overrides:
        cfg.update({k: v for k, v in overrides.items() if v is not None})

    # validation and normalization
    level_name = str(cfg["level"]).upper()
    cfg["level"] = level_name if level_name in logging._nameToLevel else DEFAULT_LOG_LEVEL

    cfg["log_path"] = str(Path(cfg["log_path"]).expanduser())

    try:
        cfg["rotate_size"] = max(1, int(cfg["rotate_size"]))
    except (TypeError, ValueError):
        cfg["rotate_size"] = DEFAULT_ROTATE_SIZE

    try:
        cfg["retention_count"] = max(1, int(cfg["retention_count"]))
    except (TypeError, ValueError):
        cfg["retention_count"] = DEFAULT_RETENTION_COUNT

    cfg["encoding"] = cfg.get("encoding") or DEFAULT_ENCODING

    return cfg

def init_logging(*, overrides: Optional[Mapping[str, Any]] = None) -> None:
    """Initialize root logging with JSON formatter and rotating file; idempotent."""
    cfg = _load_config(overrides=overrides)

    _shutdown_handlers()

    # ensure log directory exists
    log_path = Path(cfg["log_path"])
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # configure handlers
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=cfg["rotate_size"],
        backupCount=cfg["retention_count"],
        encoding=cfg["encoding"],
    )
    stream_handler = logging.StreamHandler(sys.stdout)

    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    root.setLevel(cfg["level"])
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    # flush and close handlers on exit
    atexit.register(_shutdown_handlers)

    return

def get_logger(name: str) -> logging.Logger:
    """Return a logger with contextual enrichment."""
    logger = logging.getLogger(name)

    class ContextFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            ctx = _context.get()
            for key, val in ctx.items():
                setattr(record, key, val)
            return True

    # Attach filter once
    if not any(isinstance(f, ContextFilter) for f in logger.filters):
        logger.addFilter(ContextFilter())

    return logger

def bind_context(**fields: Any) -> None:
    ctx = dict(_context.get())
    ctx.update({k: v for k, v in fields.items() if v is not None})
    _context.set(ctx)

def clear_context() -> None:
    _context.set({})

