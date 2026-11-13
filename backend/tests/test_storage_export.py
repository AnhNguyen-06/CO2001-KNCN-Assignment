from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import os
import sqlite3

import numpy as np
from openpyxl import load_workbook
import pytest

from presence_cv.export import ExcelExporter, ExportWorker, export_lock
from presence_cv.storage import Repository, unit_vector
from presence_cv.types import BaselineError


def test_embedding_roundtrip_and_duplicate_id(repository, samples, now):
    gallery = repository.gallery("model", "pipeline")
    np.testing.assert_array_equal(gallery.samples["0012345"][0], samples[0].embedding)
    assert gallery.names["0012345"] == "Triệu Thiên Ân"
    with pytest.raises(BaselineError, match="already registered"):
        repository.register("0012345", "Another name", samples, now)
    assert len(repository.members()) == 1


def test_embedding_normalization_handles_large_finite_values():
    result = unit_vector(np.full(128, 1e38, dtype=np.float32))
    assert result.dtype == np.float32
    assert np.linalg.norm(result) == pytest.approx(1, abs=1e-6)


def test_registration_rolls_back_all_rows(tmp_path, samples, now):
    repository = Repository(tmp_path / "rollback.sqlite3")
    with repository.connection() as connection:
        connection.execute("""CREATE TRIGGER fail_second_sample BEFORE INSERT ON face_samples
                              WHEN NEW.sample_index=1 BEGIN SELECT RAISE(ABORT, 'test failure'); END""")
    with pytest.raises(BaselineError):
        repository.register("NEW", "New person", samples, now)
    assert repository.members() == []
    assert repository.gallery("model", "pipeline").version == 0


def test_daily_unique_constraint_survives_concurrency_and_restart(repository, now):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: repository.record("0012345", now), range(16)))
    assert sum(result.outcome == "created" for result in results) == 1
    assert sum(result.outcome == "already_exists" for result in results) == 15
    restarted = Repository(repository.path)
    result = restarted.record("0012345", now + timedelta(hours=1))
    assert result.outcome == "already_exists"
    assert result.record.recorded_at == now.astimezone(restarted.timezone).isoformat()
    assert len(restarted.records()) == 1
    assert restarted.export_states()[0]["data_revision"] == 1


def test_timezone_rollover_and_first_time_are_correct(repository):
    before = datetime(2026, 11, 13, 16, 59, 59, tzinfo=timezone.utc)
    after = before + timedelta(seconds=1)
    assert repository.record("0012345", before).record.attendance_date == "2026-11-13"
    assert repository.record("0012345", after).record.attendance_date == "2026-11-14"
    assert len(repository.records()) == 2


def test_invalid_registration_and_model_contract_are_rejected(repository, samples, now):
    with pytest.raises(BaselineError):
        repository.register("", "Name", samples, now)
    with pytest.raises(BaselineError):
        repository.register("BAD", "Name", [samples[0]] * 3, now)
    with pytest.raises(BaselineError):
        repository.register(
            "BAD", "Name", [replace(sample, embedding=np.zeros(128)) for sample in samples], now
        )
    with pytest.raises(BaselineError, match="another model"):
        repository.gallery("other-model", "pipeline")
    assert len(repository.members()) == 1


def test_naive_time_and_unknown_member_cannot_record(repository, now):
    with pytest.raises(ValueError):
        repository.record("0012345", now.replace(tzinfo=None))
    assert repository.record("missing", now).outcome == "failed"
    assert repository.records() == []


def test_excel_contents_are_text_safe_and_idempotent(repository, samples, now, tmp_path):
    repository.register("00002", "=SUM(1,2)", samples, now)
    repository.record("0012345", now)
    repository.record("00002", now)
    exporter = ExcelExporter(repository, tmp_path / "exports")
    result = exporter.export_day("2026-11-13")
    assert result.outcome == "synced"
    assert exporter.export_day("2026-11-13").outcome == "synced"
    workbook = load_workbook(result.destination, data_only=False)
    try:
        sheet = workbook["Attendance"]
        assert sheet.max_row == 3
        assert [cell.value for cell in sheet[1]] == [
            "No.",
            "ID",
            "Full Name",
            "Date",
            "Time",
            "Status",
        ]
        assert sheet["B2"].value == "0012345" and sheet["B2"].data_type == "s"
        assert sheet["C2"].value == "Triệu Thiên Ân"
        assert sheet["E2"].value == "10:15:30"
        assert sheet["C3"].value == "=SUM(1,2)" and sheet["C3"].data_type == "s"
    finally:
        workbook.close()
    assert exporter.pending_dates() == []


def test_excel_failure_preserves_existing_workbook_and_retries(
    repository, now, tmp_path, monkeypatch
):
    repository.record("0012345", now)
    exporter = ExcelExporter(repository, tmp_path / "exports")
    path = exporter.destination("2026-11-13")
    exporter.export_day("2026-11-13")
    original_bytes = path.read_bytes()
    real_replace = os.replace

    def locked(*_):
        raise PermissionError("Workbook is open in Excel")

    monkeypatch.setattr("presence_cv.export.os.replace", locked)
    assert exporter.export_day("2026-11-13").outcome == "failed"
    assert path.read_bytes() == original_bytes
    assert len(repository.records()) == 1
    assert exporter.pending_dates() == ["2026-11-13"]
    monkeypatch.setattr("presence_cv.export.os.replace", real_replace)
    assert exporter.export_day("2026-11-13").outcome == "synced"
    assert exporter.pending_dates() == []


@pytest.mark.skipif(os.name != "nt", reason="Checks Windows file-sharing semantics")
def test_real_windows_file_lock_is_recoverable(repository, now, tmp_path):
    repository.record("0012345", now)
    exporter = ExcelExporter(repository, tmp_path / "exports")
    exporter.export_day("2026-11-13")
    with exporter.destination("2026-11-13").open("rb"):
        assert exporter.export_day("2026-11-13").outcome == "failed"
    assert exporter.export_day("2026-11-13").outcome == "synced"


def test_export_revision_covers_concurrent_new_attendance(
    repository, samples, now, tmp_path, monkeypatch
):
    from openpyxl import Workbook

    repository.register("SECOND", "Second person", samples, now)
    repository.record("0012345", now)
    exporter = ExcelExporter(repository, tmp_path / "exports")
    real_save = Workbook.save

    def save_with_arrival(workbook, path):
        repository.record("SECOND", now)
        real_save(workbook, path)

    monkeypatch.setattr(Workbook, "save", save_with_arrival)
    assert exporter.export_day("2026-11-13").outcome == "pending"
    assert exporter.pending_dates() == ["2026-11-13"]
    assert exporter.export_day("2026-11-13").outcome == "synced"
    state = repository.export_states()[0]
    assert state["data_revision"] == state["exported_revision"] == 2


def test_export_lock_prevents_overlapping_writers(repository, now, tmp_path):
    repository.record("0012345", now)
    exporter = ExcelExporter(repository, tmp_path / "exports")
    with export_lock(exporter.destination("2026-11-13").with_suffix(".xlsx.lock")):
        assert exporter.export_day("2026-11-13").outcome == "failed"
    assert exporter.export_day("2026-11-13").outcome == "synced"


def test_worker_recovers_pending_and_missing_file_on_restart(repository, now, tmp_path):
    repository.record("0012345", now)
    exporter = ExcelExporter(repository, tmp_path / "exports")
    worker = ExportWorker(exporter)
    try:
        assert worker.flush()
        assert any(event.kind == "excel_synced" for event in worker.drain_events())
    finally:
        assert worker.close()
    exporter.destination("2026-11-13").unlink()
    second_worker = ExportWorker(exporter)
    try:
        assert second_worker.flush()
        assert exporter.destination("2026-11-13").is_file()
    finally:
        assert second_worker.close()


def test_storage_failure_is_not_reported_as_success(repository, now):
    with repository.connection() as connection:
        connection.execute("""CREATE TRIGGER fail_write BEFORE INSERT ON attendance
                              BEGIN SELECT RAISE(ABORT, 'simulated disk failure'); END""")
    result = repository.record("0012345", now)
    assert result.outcome == "failed" and result.record is None
    assert repository.records() == []
    assert repository.export_states() == []


def test_future_schema_is_rejected(tmp_path):
    path = tmp_path / "future.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version=999")
    with pytest.raises(BaselineError, match="schema version"):
        Repository(path)
