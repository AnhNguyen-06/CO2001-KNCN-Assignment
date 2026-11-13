"""Exercise actual models and durable attendance using public, held-out examples."""

from dataclasses import asdict
import json
from pathlib import Path
import platform
import tempfile
import time

import cv2
import numpy as np
from openpyxl import load_workbook

from presence_cv.config import BACKEND_ROOT, Config, Paths
from presence_cv.session import BaselineSession
from presence_cv.types import BaselineError, FramePacket
from presence_cv.vision import read_image
from tools.verification_data import FIXTURES, enrollment_images


def arrivals(session, image, duration=1.4):
    events, states = [], []
    started = time.monotonic()
    index = 0
    while time.monotonic() - started < duration:
        index += 1
        result = session.process(FramePacket(1, index, time.monotonic(), image))
        observed_after_ms = (time.monotonic() - started) * 1000
        events.extend(
            {**asdict(event), "observed_after_ms": observed_after_ms} for event in result.events
        )
        states.extend(face.state for face in result.faces)
        time.sleep(0.10)
    assert session.exports.flush(), "Excel worker did not finish"
    events.extend(asdict(event) for event in session.exports.drain_events())
    return events, states


def main():
    config = Config.load()
    output = BACKEND_ROOT / "var" / "verification"
    output.mkdir(parents=True, exist_ok=True)
    data = Path(tempfile.mkdtemp(prefix="baseline_", dir=output))
    paths = Paths(data_dir=data)
    probe = read_image(FIXTURES / "obama2.jpg")
    unknown = read_image(FIXTURES / "lin-manuel-miranda.png")
    report = {
        "environment": {
            "python": platform.python_version(),
            "opencv": cv2.__version__,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
        "config": asdict(config),
        "data_dir": str(data),
        "scope": "Public example smoke test. Enrollment variants share a source image; group field accuracy remains unmeasured.",
    }
    with BaselineSession(config, paths) as session:
        session.register("FIXTURE-A", "Verification person A", enrollment_images("obama.jpg"))
        session.register("FIXTURE-B", "Verification person B", enrollment_images("biden.jpg"))
        known_faces = session.vision.analyze(probe, session.gallery)
        unknown_faces = session.vision.analyze(unknown, session.gallery)
        assert len(known_faces) == 1 and known_faces[0].match.person_id == "FIXTURE-A", (
            asdict(known_faces[0]) if known_faces else "No held-out face"
        )
        assert unknown_faces and all(face.match.person_id is None for face in unknown_faces)
        report["held_out_known"] = [asdict(face) for face in known_faces]
        report["unknown_person"] = [asdict(face) for face in unknown_faces]
        timings = []
        for _ in range(15):
            started = time.perf_counter()
            session.vision.analyze(probe, session.gallery)
            timings.append((time.perf_counter() - started) * 1000)
        report["inference_ms"] = {
            "mean": float(np.mean(timings)),
            "p95": float(np.percentile(timings, 95)),
            "runs": len(timings),
        }
        events, states = arrivals(session, probe)
        assert sum(event["kind"] == "attendance_created" for event in events) == 1, events
        assert "confirming" in states and "created" in states
        assert len(session.repository.records()) == 1
        report["first_arrival_events"] = events
        report["first_frame_to_attendance_ms"] = next(
            event["observed_after_ms"] for event in events if event["kind"] == "attendance_created"
        )
        date = session.repository.records()[0].attendance_date
        workbook_path = session.exporter.destination(date)
        workbook = load_workbook(workbook_path)
        try:
            sheet = workbook["Attendance"]
            assert sheet.max_row == 2 and sheet["B2"].value == "FIXTURE-A"
        finally:
            workbook.close()
        report["workbook"] = str(workbook_path)
        for label, image in (
            ("dark", (probe * 0.07).astype(np.uint8)),
            ("blurred", cv2.GaussianBlur(probe, (81, 81), 30)),
        ):
            try:
                session.vision.make_sample(image)
            except BaselineError as error:
                report[f"{label}_rejection"] = {"code": error.code, "message": str(error)}
            else:
                raise AssertionError(f"{label} image unexpectedly accepted")
        try:
            session.vision.make_sample(read_image(FIXTURES / "two_people.jpg"))
        except BaselineError as error:
            assert error.code == "SAMPLE_MULTIPLE_FACES", str(error)
            report["multiple_face_registration"] = error.code
        else:
            raise AssertionError("Multiple-face registration unexpectedly accepted")
    with BaselineSession(config, paths) as restarted:
        events, _ = arrivals(restarted, probe)
        assert sum(event["kind"] == "attendance_already_exists" for event in events) == 1
        assert len(restarted.repository.records()) == 1
        report["restart_duplicate_events"] = events
    # A short video drives the same CLI source path used by the standalone webcam runner.
    video_path = output / "held_out_arrival.avi"
    h, w = probe.shape[:2]
    scale = min(1, 640 / max(h, w))
    size = (round(w * scale) // 2 * 2, round(h * scale) // 2 * 2)
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"MJPG"), 10, size)
    assert writer.isOpened()
    try:
        frame = cv2.resize(probe, size)
        for _ in range(35):
            writer.write(frame)
    finally:
        writer.release()
    report["video_fixture"] = str(video_path)
    report["passed"] = True
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": True,
                "report": str(report_path),
                "data_dir": str(data),
                "inference_ms": report["inference_ms"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
