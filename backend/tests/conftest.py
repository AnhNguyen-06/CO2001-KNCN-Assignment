from datetime import datetime, timezone

import numpy as np
import pytest

from presence_cv.config import Config
from presence_cv.storage import Repository
from presence_cv.types import Quality, Sample


@pytest.fixture(autouse=True)
def isolate_application_database(monkeypatch):
    # CLI subprocesses must not use a developer's .env database during tests.
    # Windows can omit empty environment variables in child processes.
    monkeypatch.setenv("DATABASE_URL", " ")


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def now():
    return datetime(2026, 11, 13, 3, 15, 30, tzinfo=timezone.utc)


@pytest.fixture
def samples():
    vector = np.zeros(128, dtype=np.float32)
    vector[0] = 1
    return [
        Sample(vector.copy(), "model", "pipeline", f"image-{index}", Quality(True, (), {}))
        for index in range(3)
    ]


@pytest.fixture
def repository(tmp_path, samples, now):
    repository = Repository(tmp_path / "attendance.sqlite3")
    repository.register("0012345", "Triệu Thiên Ân", samples, now)
    return repository
