"""Integration checks against a real, explicitly configured test PostgreSQL server."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import BytesIO
import os
from uuid import uuid4
from urllib.parse import quote, urlencode

from fastapi.testclient import TestClient
import numpy as np
from openpyxl import load_workbook
import psycopg
from psycopg import sql
import pytest

from presence_cv.api import create_app
from presence_cv.config import Config, Paths
from presence_cv.session import BaselineSession
from presence_cv.storage import Repository
from presence_cv.types import BaselineError
from presence_cv.vision import read_image
from tools.verification_data import FIXTURES
from test_api import registration, recognize

pytestmark = pytest.mark.postgres


@pytest.fixture
def database_url():
    url = os.environ.get("PRESENCE_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set PRESENCE_TEST_DATABASE_URL to a dedicated PostgreSQL test database")
    schema = "presence_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        separator = "&" if "?" in url else "?"
        yield url + separator + urlencode({"options": f"-c search_path={schema}"}, quote_via=quote)
    finally:
        with psycopg.connect(url, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def pg_repository(database_url, tmp_path):
    return Repository(tmp_path / "unused.sqlite3", database_url=database_url)


def test_postgres_registration_roundtrip_and_restart(pg_repository, database_url, samples, now):
    repo = pg_repository
    repo.register("0000456", "Nguyễn Văn Kiểm Thử", samples, now)
    restarted = Repository(repo.path, database_url=database_url)
    gallery = restarted.gallery("model", "pipeline")
    assert gallery.version == 1
    assert gallery.names["0000456"] == "Nguyễn Văn Kiểm Thử"
    np.testing.assert_array_equal(gallery.samples["0000456"][0], samples[0].embedding)
    with pytest.raises(BaselineError, match="already registered"):
        restarted.register("0000456", "Conflict", samples, now)
    assert not repo.path.exists()


def test_postgres_concurrent_check_in_and_midnight(pg_repository, samples, now):
    repo = pg_repository
    repo.register("A", "Person A", samples, now)
    repo.register("B", "Person B", samples, now)
    with ThreadPoolExecutor(max_workers=8) as workers:
        results = list(workers.map(lambda _: repo.record("A", now), range(16)))
    assert sum(result.outcome == "created" for result in results) == 1
    assert sum(result.outcome == "already_exists" for result in results) == 15
    assert repo.record("B", now).outcome == "created"
    assert repo.export_states()[0]["data_revision"] == 2
    assert repo.record("A", now + timedelta(days=1)).outcome == "created"
    assert len(repo.records()) == 3
    assert repo.record("missing", now).outcome == "failed"


def test_postgres_registration_rolls_back_samples_and_revision(pg_repository, samples, now):
    with pg_repository.connection() as connection:
        connection.execute(
            "ALTER TABLE face_samples ADD CONSTRAINT reject_sample CHECK(sample_index<>1)"
        )
    with pytest.raises(BaselineError):
        pg_repository.register("ROLLBACK", "Rejected", samples, now)
    assert pg_repository.members() == []
    assert pg_repository.gallery("model", "pipeline").version == 0


def test_postgres_snapshot_and_export_revisions(pg_repository, samples, now):
    pg_repository.register("0001", "=SUM(1,2)", samples, now)
    pg_repository.record("0001", now)
    records, revision = pg_repository.export_snapshot("2026-11-13")
    assert revision == 1 and records[0].person_id == "0001"
    pg_repository.mark_export_error("2026-11-13", "Test failure")
    assert pg_repository.export_states()[0]["last_error"] == "Test failure"
    pg_repository.mark_exported("2026-11-13", revision, now)
    assert pg_repository.export_states()[0]["exported_revision"] == revision


def test_postgres_web_cv_download_and_restart(database_url, tmp_path):
    if not (FIXTURES / "obama2.jpg").exists():
        pytest.skip("Prepare model fixtures first")
    paths = Paths(data_dir=tmp_path, database_url=database_url, export_mode="download")
    app = create_app(Config.load(), paths)
    with TestClient(app) as client:
        assert client.get("/api/health").json()["storage"] == "postgresql"
        assert client.post("/api/members", json=registration(name="=SUM(1,2)")).status_code == 201
        token = client.post("/api/recognition/sessions").json()["token"]
        frames = recognize(client, token, read_image(FIXTURES / "obama2.jpg"))
        assert any(
            event["kind"] == "attendance_created" for frame in frames for event in frame["events"]
        )
        assert client.get("/api/workspace").json()["exports"][0]["status"] == "available"
        assert not paths.exports.exists()
        assert client.post("/api/exports/retry").status_code == 200
    with TestClient(create_app(Config.load(), paths)) as restarted:
        snapshot = restarted.get("/api/workspace").json()
        assert len(snapshot["members"]) == len(snapshot["records"]) == 1
        response = restarted.get("/api/exports/download", params={"member_id": "0000123"})
        with BytesIO(response.content) as stream:
            workbook = load_workbook(stream)
            try:
                assert workbook["Attendance"]["B2"].value == "0000123"
                assert workbook["Attendance"]["C2"].data_type == "s"
            finally:
                workbook.close()


def test_download_mode_keeps_local_baseline_available(tmp_path):
    paths = Paths(data_dir=tmp_path, export_mode="download")
    with BaselineSession(Config.load(), paths) as session:
        assert session.exports.flush()
        assert session.exports.drain_events() == []
        assert session.exporter is None
    assert not paths.exports.exists()
