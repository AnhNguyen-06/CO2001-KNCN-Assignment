import json
import subprocess
import sys

import cv2
import numpy as np
from openpyxl import load_workbook
import pytest

from presence_cv.config import BACKEND_ROOT, Config, Paths
from presence_cv.session import BaselineSession
from presence_cv.types import BaselineError, FramePacket, Gallery
from presence_cv.vision import VisionEngine, match_embedding, read_image
from tools.verification_data import FIXTURES, enrollment_images
from test_session import FakeClock

pytestmark = pytest.mark.models


@pytest.fixture(scope="module")
def engine():
    if (
        not (Paths().model_dir / "face_recognition_sface_2021dec.onnx").exists()
        or not (FIXTURES / "obama2.jpg").exists()
    ):
        pytest.skip("Run setup-models and python -m tools.verification_data first")
    return VisionEngine(Config.load(), Paths().model_dir)


def test_actual_sface_distinguishes_held_out_identity_and_unknown(engine):
    first = [engine.make_sample(image).embedding for image in enrollment_images("obama.jpg")]
    second = [engine.make_sample(image).embedding for image in enrollment_images("biden.jpg")]
    gallery = Gallery(
        1, {"A": np.stack(first), "B": np.stack(second)}, {"A": "Person A", "B": "Person B"}
    )
    probe = engine.make_sample(read_image(FIXTURES / "obama2.jpg"))
    assert probe.embedding.shape == (128,)
    assert np.linalg.norm(probe.embedding) == pytest.approx(1.0, abs=1e-5)
    assert match_embedding(probe.embedding, gallery, engine.config).person_id == "A"
    unknown = engine.make_sample(read_image(FIXTURES / "lin-manuel-miranda.png"))
    assert match_embedding(unknown.embedding, gallery, engine.config).person_id is None


def test_quality_reasons_and_registration_face_count(engine):
    image = read_image(FIXTURES / "obama2.jpg")
    row = engine._detect(image)[0]
    dark = (image * 0.05).astype(np.uint8)
    quality, _ = engine._quality_and_align(dark, row)
    assert not quality.accepted and "too_dark" in quality.reasons
    blurred = cv2.GaussianBlur(image, (81, 81), 30)
    quality, _ = engine._quality_and_align(blurred, row)
    assert not quality.accepted and "too_blurry" in quality.reasons
    small = row.copy()
    small[2:4] = 20
    assert "face_too_small" in engine._quality_and_align(image, small)[0].reasons
    tilted = row.copy()
    tilted[7] = tilted[5] + abs(tilted[6] - tilted[4])
    assert "face_tilted" in engine._quality_and_align(image, tilted)[0].reasons
    with pytest.raises(BaselineError) as error:
        engine.make_sample(read_image(FIXTURES / "two_people.jpg"))
    assert error.value.code == "SAMPLE_MULTIPLE_FACES"
    with pytest.raises(BaselineError) as error:
        engine.make_sample(np.zeros((480, 640, 3), dtype=np.uint8))
    assert error.value.code == "SAMPLE_NO_FACE"


def test_detector_coordinates_return_to_original_resolution(engine):
    image = read_image(FIXTURES / "obama2.jpg")
    rows = engine._detect(image)
    enlarged = cv2.resize(image, None, fx=2, fy=2)
    bigger = engine._detect(enlarged)
    assert len(rows) == len(bigger) == 1
    np.testing.assert_allclose(rows[0, :14] * 2, bigger[0, :14], atol=4)


def test_real_pipeline_notifies_saves_exports_and_survives_restart(engine, tmp_path, now):
    paths = Paths(data_dir=tmp_path)
    probe = read_image(FIXTURES / "obama2.jpg")
    clock = FakeClock(now)
    events = []
    with BaselineSession(engine.config, paths, clock) as session:
        session.register("000001", "Verification person A", enrollment_images("obama.jpg"))
        for index in range(5):
            clock.elapsed = index * 0.2
            result = session.process(FramePacket(1, index, clock.elapsed, probe))
            events.extend(result.events)
        assert sum(event.kind == "attendance_created" for event in events) == 1
        assert session.exports.flush()
        records = session.repository.records()
        assert len(records) == 1
        workbook = load_workbook(session.exporter.destination(records[0].attendance_date))
        try:
            assert workbook["Attendance"]["B2"].value == "000001"
        finally:
            workbook.close()
    with BaselineSession(engine.config, paths, clock) as session:
        events = []
        for index in range(5):
            clock.elapsed += 0.2
            events.extend(session.process(FramePacket(2, index, clock.elapsed, probe)).events)
        assert any(event.kind == "attendance_already_exists" for event in events)
        assert len(session.repository.records()) == 1


def test_video_cli_runs_actual_models_and_prints_notifications(engine, tmp_path, now):
    paths = Paths(data_dir=tmp_path)
    with BaselineSession(engine.config, paths) as session:
        session.register("CLI-001", "Video verification", enrollment_images("obama.jpg"))
    image = read_image(FIXTURES / "obama2.jpg")
    image = cv2.resize(image, (400, 640))
    video = tmp_path / "arrival.avi"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 10, (400, 640))
    assert writer.isOpened()
    try:
        for _ in range(25):
            writer.write(image)
    finally:
        writer.release()
    result = subprocess.run(
        [
            sys.executable,
            str(BACKEND_ROOT / "main.py"),
            "--data-dir",
            str(tmp_path),
            "run",
            "--source",
            str(video),
            "--headless",
            "--max-frames",
            "25",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert sum(event.get("kind") == "attendance_created" for event in events) == 1, events
    assert any(event.get("kind") == "excel_synced" for event in events)
    assert events[-1]["kind"] == "session_stopped"


def test_real_two_face_scene_confirms_each_identity_separately(engine, tmp_path, now):
    clock = FakeClock(now)
    with BaselineSession(engine.config, Paths(data_dir=tmp_path), clock) as session:
        session.register("A", "Person A", enrollment_images("obama.jpg"))
        session.register("B", "Person B", enrollment_images("biden.jpg"))
        image = read_image(FIXTURES / "two_people.jpg")
        events = []
        for index in range(4):
            clock.elapsed = index * 0.2
            result = session.process(FramePacket(1, index, clock.elapsed, image))
            events.extend(result.events)
        assert {face.match.person_id for face in result.faces} == {"A", "B"}
        assert sum(event.kind == "attendance_created" for event in events) == 2
        assert {record.person_id for record in session.repository.records()} == {"A", "B"}
