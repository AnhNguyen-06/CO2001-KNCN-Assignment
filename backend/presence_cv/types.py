from dataclasses import dataclass, field
from typing import Any

import numpy as np


class BaselineError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FramePacket:
    generation: int
    frame_id: int
    captured_at: float
    image_bgr: np.ndarray = field(repr=False, compare=False)


@dataclass(frozen=True)
class Quality:
    accepted: bool
    reasons: tuple[str, ...]
    metrics: dict[str, float]


@dataclass(frozen=True)
class Sample:
    embedding: np.ndarray = field(repr=False, compare=False)
    model_id: str
    preprocessing_version: str
    image_digest: str
    quality: Quality


@dataclass(frozen=True)
class Gallery:
    version: int
    samples: dict[str, np.ndarray] = field(repr=False, compare=False)
    names: dict[str, str]


@dataclass(frozen=True)
class Match:
    decision: str
    person_id: str | None = None
    score: float | None = None
    runner_up_score: float | None = None


@dataclass
class Face:
    bbox: tuple[float, float, float, float]
    landmarks: list[list[float]]
    quality: Quality
    match: Match
    track_id: int | None = None
    state: str = "unknown"


@dataclass(frozen=True)
class AttendanceRecord:
    attendance_id: int
    person_id: str
    full_name_snapshot: str
    attendance_date: str
    recorded_at: str
    status: str = "Present"


@dataclass(frozen=True)
class AttendanceResult:
    outcome: str
    record: AttendanceRecord | None = None
    error: str | None = None


@dataclass(frozen=True)
class ExportResult:
    date: str
    outcome: str
    revision: int
    destination: str
    error: str | None = None


@dataclass(frozen=True)
class Event:
    kind: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class FrameResult:
    generation: int
    frame_id: int
    gallery_version: int
    faces: list[Face]
    events: list[Event]
    processing_ms: float
    stale: bool = False
