import pytest
from infra import init_logging, get_logger
from pathlib import Path

@pytest.fixture
def test_logger(tmp_path):
    log_file = tmp_path / "test.log"
    init_logging(overrides={
        "log_path": str(log_file),
        "level": "DEBUG",
        "rotate_size": 1024,         # tiny for rotation tests if needed
        "retention_count": 2,
    })
    return get_logger("tests")