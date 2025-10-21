from pathlib import Path
from logging import Logger

import pytest
import pytest_asyncio

from httpx import AsyncClient
from fastapi import FastAPI

from infra import init_logging, get_logger
from main import app

@pytest.fixture
def test_logger(tmp_path: Path) -> Logger:
    """Return a configured logger writing to a temporary file."""
    log_file = tmp_path / "test.log"
    init_logging(overrides={
        "log_path": str(log_file),
        "level": "DEBUG",
        "rotate_size": 1024,
        "retention_count": 2,
    })
    return get_logger("tests")


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Reusable asynchronous HTTP client bound to the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac