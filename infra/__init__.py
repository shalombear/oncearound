# infra/__init__.py
"""
Infrastructure layer public interface.
Exposes logging and other infra services for application-wide use.
"""

from .logger import get_logger, init_logging

__all__ = ["get_logger", "init_logging"]
