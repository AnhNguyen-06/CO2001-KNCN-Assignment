from dataclasses import asdict, dataclass, fields
import json
from pathlib import Path
from zoneinfo import ZoneInfo

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Config:
    detector_max_size: int = 640
    detector_threshold: float = 0.9
    match_threshold: float = 0.45
    match_margin: float = 0.08
    min_face_size: int = 80
    min_eye_distance: float = 24
    min_brightness: float = 40
    max_brightness: float = 220
    min_sharpness: float = 50
    max_roll_degrees: float = 25
    max_nose_offset: float = 0.65
    min_visible_fraction: float = 0.95
    confirmation_frames: int = 3
    confirmation_seconds: float = 0.35
    confirmation_window: float = 1.5
    max_observation_gap: float = 0.6
    max_frame_age: float = 1.0
    track_iou_threshold: float = 0.25
    overlap_reset_threshold: float = 0.2
    write_retry_seconds: float = 1.0
    opencv_threads: int = 4
    timezone: str = "Asia/Ho_Chi_Minh"

    def __post_init__(self):
        import math

        for key, value in asdict(self).items():
            if key == "timezone":
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{key} must be a number")
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{key} must be finite and nonnegative")
        for key in ("detector_max_size", "min_face_size", "confirmation_frames", "opencv_threads"):
            if not isinstance(getattr(self, key), int) or getattr(self, key) < 1:
                raise ValueError(f"{key} must be a positive integer")
        for key in (
            "detector_threshold",
            "min_visible_fraction",
            "track_iou_threshold",
            "overlap_reset_threshold",
        ):
            if not 0 < getattr(self, key) <= 1:
                raise ValueError(f"{key} must be in (0, 1]")
        if not 0 < self.match_threshold <= 1 or not 0 <= self.match_margin < 2:
            raise ValueError("Invalid matching threshold or margin")
        if not self.min_brightness < self.max_brightness <= 255:
            raise ValueError("Brightness bounds must be ordered within [0, 255]")
        if self.confirmation_window < self.confirmation_seconds:
            raise ValueError("Confirmation window must cover the required duration")
        if min(self.max_frame_age, self.max_observation_gap, self.write_retry_seconds) <= 0:
            raise ValueError("Timing limits must be positive")
        if not isinstance(self.timezone, str):
            raise ValueError("timezone must be an IANA timezone name")
        ZoneInfo(self.timezone)

    @classmethod
    def load(cls, path: Path | None = None):
        if path is None:
            path = BACKEND_ROOT / "config" / "default.json"
        values = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(values, dict):
            raise ValueError("Configuration must be a JSON object")
        unknown = set(values) - {field.name for field in fields(cls)}
        if unknown:
            raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")
        return cls(**values)


@dataclass(frozen=True)
class Paths:
    model_dir: Path = BACKEND_ROOT / "models"
    data_dir: Path = BACKEND_ROOT / "var"

    @property
    def database(self):
        return self.data_dir / "attendance.sqlite3"

    @property
    def exports(self):
        return self.data_dir / "exports"
