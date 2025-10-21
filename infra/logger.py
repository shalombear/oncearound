"""Structured JSON logger for consistent, machine-readable application logging."""

import sys
import os

import logging
import json
import atexit
import contextvars

from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path

from pythonjsonlogger import jsonlogger

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_PATH = "./logs/app.log"
DEFAULT_ROTATE_SIZE = 100 * 1024 * 1024  # 100 MB
DEFAULT_RETENTION_COUNT = 10
DEFAULT_ENCODING = "utf-8"

_context = contextvars.ContextVar("log_context", default={})

def _load_config(*, overrides: dict | None = None) -> dict:
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

    return cfg

