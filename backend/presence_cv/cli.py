import argparse
from dataclasses import asdict
from datetime import date as Date
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

import cv2
import numpy as np
import psycopg

from .camera import LatestFrames
from .config import Config, Paths
from .display import annotate, window_open
from .export import ExcelExporter
from .models import download_models, verify_models
from .session import BaselineSession
from .storage import Repository
from .types import BaselineError, Event
from .vision import read_image


def emit(value):
    print(
        json.dumps(
            asdict(value) if hasattr(value, "__dataclass_fields__") else value,
            ensure_ascii=False,
            allow_nan=False,
        ),
        flush=True,
    )


def parse_date(value):
    try:
        return Date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise argparse.ArgumentTypeError("Use a date such as 2026-11-13") from error


def parser():
    root = argparse.ArgumentParser(
        description="Presence standalone YuNet/SFace attendance baseline"
    )
    root.add_argument("--config", type=Path, help="Configuration JSON path")
    root.add_argument(
        "--data-dir", type=Path, default=Path(os.environ.get("PRESENCE_DATA_DIR", Paths().data_dir))
    )
    root.add_argument("--model-dir", type=Path, default=Paths().model_dir)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("setup-models", help="Download and verify pinned ONNX model files")
    doctor = commands.add_parser(
        "doctor", help="Verify models, runtime, database and optional camera"
    )
    doctor.add_argument(
        "--camera", action="store_true", help="Briefly open camera 0 and report frame dimensions"
    )
    register = commands.add_parser(
        "register", help="Enroll a local identity with three quality-approved samples"
    )
    register.add_argument("--id", required=True)
    register.add_argument("--name", required=True)
    source = register.add_mutually_exclusive_group(required=True)
    source.add_argument("--images", type=Path, nargs=3, metavar=("FRONT", "LEFT", "RIGHT"))
    source.add_argument(
        "--camera", type=int, help="Camera index. Space captures a sample, Q cancels."
    )
    register.add_argument(
        "--allow-similar",
        action="store_true",
        help="Proceed after reviewing a possible duplicate face",
    )
    inspect = commands.add_parser(
        "inspect", help="Analyze one image without creating an attendance record"
    )
    inspect.add_argument("--image", type=Path, required=True)
    inspect.add_argument("--output", type=Path, help="Optional annotated image destination")
    run = commands.add_parser(
        "run", help="Run recognition, attendance notifications and automatic daily Excel export"
    )
    run.add_argument("--source", default="0", help="Camera index or video file")
    run.add_argument(
        "--headless", action="store_true", help="Emit JSON notifications without a preview window"
    )
    run.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="Stop after this many processed frames, 0 runs until stopped",
    )
    records = commands.add_parser("records", help="Read saved attendance as JSON")
    records.add_argument("--date", type=parse_date)
    commands.add_parser("members", help="List registered identities")
    export = commands.add_parser("export", help="Export a day or retry all pending daily workbooks")
    export.add_argument("--date", type=parse_date)
    return root


def capture_enrollment(session: BaselineSession, index: int):
    images = []
    last = -1
    last_capture = -float("inf")
    try:
        with LatestFrames(str(index)) as camera:
            while len(images) < 3:
                packet = camera.read(last)
                if packet is None:
                    raise BaselineError(
                        "CAMERA_UNAVAILABLE", "Camera ended before three samples were collected."
                    )
                last = packet.frame_id
                faces = [detection.face for detection in session.vision.extract(packet.image_bgr)]
                from .types import FrameResult

                result = FrameResult(1, packet.frame_id, session.gallery.version, faces, [], 0)
                prompt = f"Sample {len(images) + 1}/3: {['face front', 'turn slightly left', 'turn slightly right'][len(images)]}. Space capture; Q cancel."
                cv2.imshow("Presence registration", annotate(packet.image_bgr, result, {}, prompt))
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27) or not window_open("Presence registration"):
                    raise BaselineError(
                        "REGISTRATION_CANCELLED",
                        "Registration cancelled. Temporary photos discarded.",
                    )
                if key == ord(" ") and time.monotonic() - last_capture >= 0.75:
                    try:
                        session.vision.make_sample(packet.image_bgr)
                        images.append(packet.image_bgr.copy())
                        last_capture = time.monotonic()
                        emit(Event("sample_captured", f"Captured sample {len(images)}/3."))
                    except BaselineError as error:
                        emit(Event("sample_rejected", str(error), {"code": error.code}))
    finally:
        cv2.destroyAllWindows()
    return images


def run_attendance(session: BaselineSession, arguments):
    if arguments.max_frames < 0:
        raise BaselineError("INVALID_ARGUMENT", "--max-frames must be nonnegative.")
    frame_id, processed = -1, 0
    notification, notification_until = "", 0.0
    emit(
        Event(
            "session_started",
            "Recognition session ready.",
            {
                "registered_members": len(session.gallery.names),
                "gallery_version": session.gallery.version,
                "match_threshold": session.config.match_threshold,
                "data_dir": str(session.paths.data_dir),
            },
        )
    )
    try:
        with LatestFrames(arguments.source) as camera:
            while not arguments.max_frames or processed < arguments.max_frames:
                packet = camera.read(frame_id)
                if packet is None:
                    break
                frame_id = packet.frame_id
                result = session.process(packet)
                processed += 1
                for event in result.events:
                    emit(event)
                    if event.kind.startswith("attendance_"):
                        notification, notification_until = event.message, time.monotonic() + 3
                if arguments.headless:
                    continue
                current = notification if time.monotonic() < notification_until else ""
                cv2.imshow(
                    "Presence CV baseline",
                    annotate(packet.image_bgr, result, session.gallery.names, current),
                )
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27) or not window_open("Presence CV baseline"):
                    break
                if key == ord("r"):
                    session.exports.retry_pending()
                if key == ord("g"):
                    session.reload_gallery()
                    emit(Event("gallery_reloaded", "Registered identities reloaded."))
    finally:
        cv2.destroyAllWindows()
    session.exports.flush()
    for event in session.exports.drain_events():
        emit(event)
    emit(Event("session_stopped", f"Processed {processed} frames."))


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    arguments = parser().parse_args(argv)
    try:
        config = Config.load(arguments.config)
        paths = Paths(
            arguments.model_dir.resolve(),
            arguments.data_dir.resolve(),
            database_url=os.environ.get("DATABASE_URL", "").strip() or None,
        )
        if arguments.command == "setup-models":
            emit(
                {
                    "models": {
                        key: str(path) for key, path in download_models(paths.model_dir).items()
                    }
                }
            )
            return 0
        if arguments.command in ("records", "members", "export"):
            repository = Repository(
                paths.database, config.timezone, database_url=paths.database_url
            )
            if arguments.command == "members":
                emit(repository.members())
            elif arguments.command == "records":
                emit([asdict(record) for record in repository.records(arguments.date)])
            else:
                exporter = ExcelExporter(repository, paths.exports)
                dates = [arguments.date] if arguments.date else exporter.pending_dates()
                results = [exporter.export_day(date) for date in dates]
                emit([asdict(result) for result in results])
                return int(any(result.outcome == "failed" for result in results))
            return 0
        with BaselineSession(config, paths) as session:
            if arguments.command == "doctor":
                emit(
                    {
                        "python": sys.version.split()[0],
                        "opencv": cv2.__version__,
                        "numpy": np.__version__,
                        "models_verified": list(verify_models(paths.model_dir)),
                        "embedding_dimension": 128,
                        "registered_members": len(session.gallery.names),
                        "config": asdict(config),
                        "database": session.repository.storage,
                        "exports": str(paths.exports),
                    }
                )
                if arguments.camera:
                    with LatestFrames() as camera:
                        packet = camera.read()
                        emit({"camera_frame_shape": list(packet.image_bgr.shape)})
            elif arguments.command == "register":
                images = (
                    [read_image(path) for path in arguments.images]
                    if arguments.images
                    else capture_enrollment(session, arguments.camera)
                )
                emit(
                    session.register(arguments.id, arguments.name, images, arguments.allow_similar)
                )
            elif arguments.command == "inspect":
                image = read_image(arguments.image)
                faces = session.vision.analyze(image, session.gallery)
                emit(
                    {
                        "faces": [asdict(face) for face in faces],
                        "gallery_version": session.gallery.version,
                    }
                )
                if arguments.output:
                    from .types import FrameResult

                    result = FrameResult(1, 1, session.gallery.version, faces, [], 0)
                    output = annotate(image, result, session.gallery.names)
                    arguments.output.parent.mkdir(parents=True, exist_ok=True)
                    ok, encoded = cv2.imencode(arguments.output.suffix or ".jpg", output)
                    if not ok:
                        raise BaselineError(
                            "IMAGE_WRITE_FAILED", "Could not encode annotated image."
                        )
                    encoded.tofile(arguments.output)
            elif arguments.command == "run":
                run_attendance(session, arguments)
        return 0
    except KeyboardInterrupt:
        emit(Event("session_stopped", "Stopped by user."))
        return 130
    except (BaselineError, OSError, ValueError, sqlite3.Error, psycopg.Error, cv2.error) as error:
        emit({"error": getattr(error, "code", type(error).__name__), "message": str(error)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
