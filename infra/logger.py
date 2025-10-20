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

