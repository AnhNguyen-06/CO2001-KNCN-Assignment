from dataclasses import asdict
from datetime import datetime, timezone
import math
import time

import numpy as np

from .config import Config, Paths
from .export import DownloadExports, ExcelExporter, ExportWorker
from .storage import Repository, identity
from .tracking import TemporalTracker
from .types import BaselineError, Event, FramePacket, FrameResult
from .vision import VisionEngine, match_embedding


class Clock:
    def now(self):
        return datetime.now(timezone.utc)

    def monotonic(self):
        return time.monotonic()


class BaselineSession:
    """CV session with independent tracking and a shareable asynchronous exporter."""

    def __init__(
        self,
        config: Config,
        paths: Paths,
        clock: Clock | None = None,
        *,
        vision=None,
        repository=None,
        exports=None,
    ):
        self.config = config
        self.paths = paths
        self.clock = clock or Clock()
        self.vision = vision if vision is not None else VisionEngine(config, paths.model_dir)
        self.repository = (
            repository
            if repository is not None
            else Repository(paths.database, config.timezone, database_url=paths.database_url)
        )
        self.gallery = self.repository.gallery(
            self.vision.model_id, self.vision.preprocessing_version
        )
        self.gallery_ready = True
        self.tracker = TemporalTracker(config)
        self.owns_exports = exports is None
        if exports is not None:
            self.exporter = getattr(exports, "exporter", None)
            self.exports = exports
        elif paths.export_mode == "download":
            self.exporter = None
            self.exports = DownloadExports()
        else:
            self.exporter = ExcelExporter(self.repository, paths.exports)
            self.exports = ExportWorker(self.exporter)
        self.generation: int | None = None
        self.last_frame_id = -1
        self.saved: dict[tuple[int, str, str], str] = {}
        self.retry_after: dict[tuple[int, str, str], float] = {}
        self.closed = False

    def reload_gallery(self):
        self.gallery_ready = False
        self.gallery = self.repository.gallery(
            self.vision.model_id, self.vision.preprocessing_version
        )
        self.gallery_ready = True
        self.tracker.reset()
        self.saved.clear()
        self.retry_after.clear()
        return self.gallery

    def register(
        self, person_id: str, name: str, images: list[np.ndarray], allow_similar: bool = False
    ):
        person_id, name = identity(person_id, name)
        if len(images) != 3:
            raise BaselineError("SAMPLE_COUNT", "Registration requires three distinct images.")
        if any(member["person_id"] == person_id for member in self.repository.members()):
            raise BaselineError("DUPLICATE_ID", "This member ID is already registered.")
        samples = [self.vision.make_sample(image) for image in images]
        for first in range(len(samples)):
            for second in range(first + 1, len(samples)):
                if (
                    float(samples[first].embedding @ samples[second].embedding)
                    < self.config.match_threshold
                ):
                    raise BaselineError(
                        "SAMPLE_IDENTITY_MISMATCH",
                        "The three photos must show the same person. Please retake the samples.",
                    )
        self.reload_gallery()
        warnings = []
        for sample in samples:
            match = match_embedding(sample.embedding, self.gallery, self.config)
            if match.person_id and match.score is not None and match.score >= 0.65:
                warnings.append(f"A similar face is already registered as {match.person_id}.")
        if warnings and not allow_similar:
            raise BaselineError(
                "POSSIBLE_DUPLICATE_FACE",
                warnings[0] + " Review the ID before registering another profile.",
            )
        self.repository.register(person_id, name, samples, self.clock.now())
        self.reload_gallery()
        return Event(
            "registration_created",
            f"Registered {name} with three face samples.",
            {"person_id": person_id, "gallery_version": self.gallery.version, "warnings": warnings},
        )

    def process(self, packet: FramePacket, is_current=None):
        started = time.perf_counter()
        if self.closed:
            raise BaselineError("SESSION_CLOSED", "This recognition session is closed.")
        if not self.gallery_ready:
            raise BaselineError(
                "GALLERY_RELOAD_FAILED", "Reload the gallery before resuming recognition."
            )
        if (
            not isinstance(packet.generation, int)
            or packet.generation < 0
            or not isinstance(packet.frame_id, int)
            or packet.frame_id < 0
            or not math.isfinite(packet.captured_at)
        ):
            raise BaselineError("INVALID_FRAME", "Frame identifiers and timestamp are invalid.")
        events = self.exports.drain_events()
        if self.generation is None or packet.generation > self.generation:
            self.generation = packet.generation
            self.last_frame_id = -1
            self.tracker.reset()
            self.saved.clear()
            self.retry_after.clear()
        age = self.clock.monotonic() - packet.captured_at
        if (
            packet.generation != self.generation
            or packet.frame_id <= self.last_frame_id
            or age < 0
            or age > self.config.max_frame_age
            or (is_current is not None and not is_current())
        ):
            self.tracker.reset()
            return FrameResult(
                packet.generation, packet.frame_id, self.gallery.version, [], events, 0, True
            )
        self.last_frame_id = packet.frame_id
        faces = self.vision.analyze(packet.image_bgr, self.gallery)
        # Recheck age after inference so a delayed result cannot create attendance.
        if self.clock.monotonic() - packet.captured_at > self.config.max_frame_age or (
            is_current is not None and not is_current()
        ):
            self.tracker.reset()
            return FrameResult(
                packet.generation,
                packet.frame_id,
                self.gallery.version,
                faces,
                events,
                (time.perf_counter() - started) * 1000,
                True,
            )
        self.tracker.update(faces, packet.captured_at)
        now = self.clock.now()
        date = now.astimezone(self.repository.timezone).date().isoformat()
        current_tracks = set(self.tracker.tracks)
        self.saved = {
            key: value
            for key, value in self.saved.items()
            if key[0] in current_tracks and key[2] == date
        }
        self.retry_after = {
            key: value
            for key, value in self.retry_after.items()
            if key[0] in current_tracks and key[2] == date
        }
        for face in faces:
            if is_current is not None and not is_current():
                self.tracker.reset()
                return FrameResult(
                    packet.generation,
                    packet.frame_id,
                    self.gallery.version,
                    faces,
                    events,
                    (time.perf_counter() - started) * 1000,
                    True,
                )
            if face.state != "confirmed" or face.match.person_id is None:
                continue
            key = (face.track_id, face.match.person_id, date)
            if key in self.saved:
                face.state = self.saved[key]
                continue
            if self.clock.monotonic() < self.retry_after.get(key, 0):
                face.state = "save_pending"
                continue
            result = self.repository.record(face.match.person_id, now)
            if result.outcome == "failed":
                self.retry_after[key] = self.clock.monotonic() + self.config.write_retry_seconds
                face.state = "save_failed"
                events.append(
                    Event(
                        "attendance_failed",
                        "Attendance could not be saved. Retrying shortly.",
                        {"person_id": face.match.person_id, "error": result.error},
                    )
                )
                continue
            face.state = result.outcome
            self.saved[key] = result.outcome
            record = result.record
            message = (
                f"Attendance successful — {record.full_name_snapshot}."
                if result.outcome == "created"
                else f"{record.full_name_snapshot} already checked in today."
            )
            events.append(Event(f"attendance_{result.outcome}", message, asdict(record)))
            self.exports.schedule(record.attendance_date)
        return FrameResult(
            packet.generation,
            packet.frame_id,
            self.gallery.version,
            faces,
            events,
            (time.perf_counter() - started) * 1000,
        )

    def close(self):
        if not self.closed:
            self.closed = True
            if self.owns_exports and not self.exports.close():
                raise BaselineError(
                    "EXPORT_TIMEOUT",
                    "Excel worker is still finishing. Pending data remains in SQLite.",
                )
        return self.exports.drain_events() if self.owns_exports else []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
