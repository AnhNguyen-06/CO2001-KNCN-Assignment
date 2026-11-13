from copy import deepcopy
from datetime import timedelta

import numpy as np
import pytest

from presence_cv.config import Paths
from presence_cv.session import BaselineSession
from presence_cv.types import AttendanceResult, BaselineError, FramePacket
from test_matching_tracking import face


class FakeClock:
    def __init__(self, now):
        self.current = now
        self.elapsed = 0.0

    def now(self):
        return self.current

    def monotonic(self):
        return self.elapsed


class FakeVision:
    model_id = "model"
    preprocessing_version = "pipeline"

    def __init__(self, *_):
        self.faces = [face("0012345")]
        self.calls = 0

    def analyze(self, *_):
        self.calls += 1
        return deepcopy(self.faces)


@pytest.fixture
def session(tmp_path, config, now, samples, monkeypatch):
    monkeypatch.setattr("presence_cv.session.VisionEngine", FakeVision)
    value = BaselineSession(config, Paths(data_dir=tmp_path), FakeClock(now))
    value.repository.register("0012345", "Triệu Thiên Ân", samples, now)
    value.reload_gallery()
    yield value
    value.close()


def frame(session, index, elapsed, generation=1):
    session.clock.elapsed = elapsed
    return session.process(
        FramePacket(generation, index, elapsed, np.zeros((10, 10, 3), dtype=np.uint8))
    )


def test_confirm_then_save_once_and_notify_after_commit(session):
    first = frame(session, 1, 0)
    assert first.faces[0].state == "confirming" and session.repository.records() == []
    frame(session, 2, 0.2)
    third = frame(session, 3, 0.4)
    assert third.faces[0].state == "created"
    assert sum(event.kind == "attendance_created" for event in third.events) == 1
    assert len(session.repository.records()) == 1
    for index in range(4, 40):
        result = frame(session, index, index * 0.2)
        assert not any(event.kind == "attendance_created" for event in result.events)
    assert len(session.repository.records()) == 1
    assert session.exports.flush()
    assert session.exporter.pending_dates() == []


def test_new_day_records_again_even_with_same_continuous_track(session):
    for index in range(3):
        frame(session, index, index * 0.2)
    session.clock.current += timedelta(days=1)
    result = frame(session, 3, 0.6)
    assert result.faces[0].state == "created"
    assert len(session.repository.records()) == 2


def test_stale_future_and_duplicate_frame_ids_do_not_record(session):
    frame(session, 1, 0)
    frame(session, 2, 0.2)
    session.clock.elapsed = 3
    result = session.process(FramePacket(1, 3, 0.4, np.zeros((10, 10, 3), dtype=np.uint8)))
    assert result.stale
    assert session.vision.calls == 2
    assert session.repository.records() == []
    future = session.process(FramePacket(1, 4, 10, np.zeros((10, 10, 3), dtype=np.uint8)))
    assert future.stale
    assert frame(session, 2, 3).stale


def test_old_generation_and_inference_that_finishes_too_late_are_discarded(session, monkeypatch):
    frame(session, 1, 0, generation=2)
    assert frame(session, 2, 0.2, generation=1).stale

    def slow_analyze(*_):
        session.clock.elapsed += 2
        return [face("0012345")]

    monkeypatch.setattr(session.vision, "analyze", slow_analyze)
    assert frame(session, 3, 0.4, generation=2).stale
    assert session.repository.records() == []


def test_storage_error_retries_and_never_emits_false_success(session, monkeypatch):
    real_record = session.repository.record
    monkeypatch.setattr(
        session.repository,
        "record",
        lambda *_: AttendanceResult("failed", error="Disk unavailable"),
    )
    frame(session, 1, 0)
    frame(session, 2, 0.2)
    failed = frame(session, 3, 0.4)
    assert [event.kind for event in failed.events if event.kind.startswith("attendance_")] == [
        "attendance_failed"
    ]
    assert session.repository.records() == []
    monkeypatch.setattr(session.repository, "record", real_record)
    frame(session, 4, 0.7)
    frame(session, 5, 1.0)
    frame(session, 6, 1.3)
    succeeded = frame(session, 7, 1.6)
    assert any(event.kind == "attendance_created" for event in succeeded.events)
    assert len(session.repository.records()) == 1


def test_unknown_and_gallery_reload_reset_evidence(session):
    frame(session, 1, 0)
    frame(session, 2, 0.2)
    session.reload_gallery()
    assert frame(session, 3, 0.4).faces[0].state == "confirming"
    session.vision.faces = [face(None, decision="unknown")]
    assert frame(session, 4, 0.6).faces[0].state == "unknown"
    assert session.repository.records() == []


def test_gallery_reload_failure_blocks_recognition_until_recovered(session, monkeypatch):
    real_gallery = session.repository.gallery

    def unavailable(*_):
        raise BaselineError("GALLERY_RELOAD_FAILED", "Gallery temporarily unavailable")

    monkeypatch.setattr(session.repository, "gallery", unavailable)
    with pytest.raises(BaselineError):
        session.reload_gallery()
    with pytest.raises(BaselineError, match="Reload the gallery"):
        frame(session, 1, 0)
    monkeypatch.setattr(session.repository, "gallery", real_gallery)
    session.reload_gallery()
    assert frame(session, 1, 0).faces[0].state == "confirming"


def test_nonfinite_timestamp_is_rejected(session):
    with pytest.raises(BaselineError, match="timestamp"):
        session.process(FramePacket(1, 1, float("nan"), np.zeros((10, 10, 3), dtype=np.uint8)))
