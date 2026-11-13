from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo

import numpy as np

from .types import AttendanceRecord, AttendanceResult, BaselineError, Gallery, Sample

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value INTEGER NOT NULL
);
INSERT OR IGNORE INTO meta VALUES ('gallery_revision', 0);
CREATE TABLE IF NOT EXISTS persons (
    person_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1))
);
CREATE TABLE IF NOT EXISTS face_samples (
    sample_id INTEGER PRIMARY KEY,
    person_id TEXT NOT NULL REFERENCES persons(person_id),
    sample_index INTEGER NOT NULL CHECK(sample_index BETWEEN 0 AND 2),
    embedding BLOB NOT NULL,
    embedding_dim INTEGER NOT NULL CHECK(embedding_dim = 128),
    dtype TEXT NOT NULL CHECK(dtype = 'float32-le'),
    model_id TEXT NOT NULL,
    preprocessing_version TEXT NOT NULL,
    image_digest TEXT NOT NULL,
    UNIQUE(person_id, sample_index)
);
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY,
    person_id TEXT NOT NULL REFERENCES persons(person_id),
    full_name_snapshot TEXT NOT NULL,
    attendance_date TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Present' CHECK(status = 'Present'),
    UNIQUE(person_id, attendance_date)
);
CREATE INDEX IF NOT EXISTS attendance_by_date ON attendance(attendance_date, recorded_at);
CREATE TABLE IF NOT EXISTS export_state (
    attendance_date TEXT PRIMARY KEY,
    data_revision INTEGER NOT NULL,
    exported_revision INTEGER NOT NULL DEFAULT 0,
    last_export_at TEXT,
    last_error TEXT
);
PRAGMA user_version = 1;
"""


def unit_vector(value: np.ndarray) -> np.ndarray:
    vector = np.asarray(value, dtype=np.float32).reshape(-1)
    if vector.shape != (128,) or not np.isfinite(vector).all():
        raise BaselineError(
            "INVALID_EMBEDDING", "Expected a finite 128-dimensional SFace embedding."
        )
    magnitude = float(np.linalg.norm(vector.astype(np.float64)))
    if magnitude < 1e-8:
        raise BaselineError("INVALID_EMBEDDING", "Embedding has zero magnitude.")
    return np.ascontiguousarray(vector.astype(np.float64) / magnitude, dtype=np.float32)


def identity(raw_id: str, raw_name: str):
    person_id, name = raw_id.strip(), raw_name.strip()
    if not person_id or not name or len(person_id) > 64 or len(name) > 120:
        raise BaselineError("INVALID_IDENTITY", "Provide an ID (1–64 characters) and name (1–120).")
    if any(ord(char) < 32 for char in person_id + name):
        raise BaselineError("INVALID_IDENTITY", "ID and name cannot contain control characters.")
    return person_id, name


def record_from_row(row):
    return AttendanceRecord(**dict(row))


class Repository:
    """Each operation owns its connection, including operations on export workers."""

    def __init__(self, path: Path, timezone: str = "Asia/Ho_Chi_Minh"):
        self.path = Path(path)
        self.timezone = ZoneInfo(timezone)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise BaselineError(
                    "SCHEMA_VERSION", f"Unsupported database schema version {version}."
                )
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(SCHEMA)

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self):
        with self.connection() as connection:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                yield connection

    def register(self, raw_id: str, raw_name: str, samples: list[Sample], now: datetime):
        person_id, name = identity(raw_id, raw_name)
        if now.utcoffset() is None:
            raise ValueError("Registration timestamp must include a timezone")
        if len(samples) != 3 or len({sample.image_digest for sample in samples}) != 3:
            raise BaselineError(
                "SAMPLE_COUNT", "Supply three distinct, quality-approved face samples."
            )
        if not all(sample.quality.accepted for sample in samples):
            raise BaselineError(
                "SAMPLE_LOW_QUALITY", "A registration sample failed its quality checks."
            )
        contracts = {(sample.model_id, sample.preprocessing_version) for sample in samples}
        if len(contracts) != 1:
            raise BaselineError(
                "MODEL_MISMATCH", "All samples must use the same model and preprocessing."
            )
        vectors = [unit_vector(sample.embedding).astype("<f4").tobytes() for sample in samples]
        try:
            with self.transaction() as connection:
                connection.execute(
                    "INSERT INTO persons(person_id, full_name, created_at) VALUES (?, ?, ?)",
                    (person_id, name, now.isoformat()),
                )
                connection.executemany(
                    """INSERT INTO face_samples(person_id, sample_index, embedding,
                       embedding_dim, dtype, model_id, preprocessing_version, image_digest)
                       VALUES (?, ?, ?, 128, 'float32-le', ?, ?, ?)""",
                    [
                        (
                            person_id,
                            index,
                            vector,
                            sample.model_id,
                            sample.preprocessing_version,
                            sample.image_digest,
                        )
                        for index, (sample, vector) in enumerate(zip(samples, vectors, strict=True))
                    ],
                )
                connection.execute("UPDATE meta SET value=value+1 WHERE key='gallery_revision'")
        except sqlite3.IntegrityError as error:
            if any(member["person_id"] == person_id for member in self.members()):
                raise BaselineError(
                    "DUPLICATE_ID", "This member ID is already registered."
                ) from error
            raise BaselineError(
                "REGISTRATION_FAILED", "Registration could not be saved."
            ) from error

    def members(self):
        with self.connection() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT person_id, full_name, created_at, active FROM persons ORDER BY created_at, person_id"
                )
            ]

    def gallery(self, model_id: str, preprocessing_version: str):
        samples, names = {}, {}
        with self.connection() as connection:
            connection.execute("BEGIN")
            revision = connection.execute(
                "SELECT value FROM meta WHERE key='gallery_revision'"
            ).fetchone()[0]
            rows = connection.execute(
                """SELECT f.*, p.full_name FROM face_samples f
                   JOIN persons p ON p.person_id=f.person_id WHERE p.active=1
                   ORDER BY f.person_id, f.sample_index"""
            ).fetchall()
        for row in rows:
            if row["model_id"] != model_id or row["preprocessing_version"] != preprocessing_version:
                raise BaselineError(
                    "MODEL_MISMATCH",
                    "Registered samples use another model. Re-enroll in a separate data directory.",
                )
            vector = np.frombuffer(row["embedding"], dtype="<f4").copy()
            vector = unit_vector(vector)
            samples.setdefault(row["person_id"], []).append(vector)
            names[row["person_id"]] = row["full_name"]
        if any(len(vectors) != 3 for vectors in samples.values()):
            raise BaselineError("INCOMPLETE_GALLERY", "An active profile has incomplete samples.")
        return Gallery(revision, {key: np.stack(value) for key, value in samples.items()}, names)

    def record(self, person_id: str, now: datetime):
        if now.utcoffset() is None:
            raise ValueError("Attendance timestamp must include a timezone")
        local_now = now.astimezone(self.timezone)
        date = local_now.date().isoformat()
        try:
            with self.transaction() as connection:
                person = connection.execute(
                    "SELECT full_name FROM persons WHERE person_id=? AND active=1", (person_id,)
                ).fetchone()
                if person is None:
                    return AttendanceResult("failed", error="Member is missing or inactive.")
                cursor = connection.execute(
                    """INSERT INTO attendance(person_id, full_name_snapshot, attendance_date, recorded_at)
                       VALUES (?, ?, ?, ?) ON CONFLICT(person_id, attendance_date) DO NOTHING""",
                    (person_id, person["full_name"], date, local_now.isoformat()),
                )
                created = cursor.rowcount == 1
                if created:
                    connection.execute(
                        """INSERT INTO export_state(attendance_date, data_revision) VALUES (?, 1)
                           ON CONFLICT(attendance_date) DO UPDATE SET
                           data_revision=data_revision+1, last_error=NULL""",
                        (date,),
                    )
                row = connection.execute(
                    "SELECT * FROM attendance WHERE person_id=? AND attendance_date=?",
                    (person_id, date),
                ).fetchone()
            return AttendanceResult(
                "created" if created else "already_exists", record_from_row(row)
            )
        except sqlite3.Error as error:
            return AttendanceResult("failed", error=str(error))

    def records(self, date: str | None = None):
        with self.connection() as connection:
            if date is None:
                rows = connection.execute(
                    "SELECT * FROM attendance ORDER BY recorded_at, attendance_id"
                )
            else:
                rows = connection.execute(
                    "SELECT * FROM attendance WHERE attendance_date=? ORDER BY recorded_at, attendance_id",
                    (date,),
                )
            return [record_from_row(row) for row in rows]

    def export_snapshot(self, date: str):
        with self.connection() as connection:
            connection.execute("BEGIN")
            state = connection.execute(
                "SELECT data_revision FROM export_state WHERE attendance_date=?", (date,)
            ).fetchone()
            rows = connection.execute(
                "SELECT * FROM attendance WHERE attendance_date=? ORDER BY recorded_at, attendance_id",
                (date,),
            ).fetchall()
        return [record_from_row(row) for row in rows], state[0] if state else 0

    def export_states(self):
        with self.connection() as connection:
            return [
                dict(row)
                for row in connection.execute("SELECT * FROM export_state ORDER BY attendance_date")
            ]

    def mark_exported(self, date: str, revision: int, now: datetime):
        with self.transaction() as connection:
            connection.execute(
                """UPDATE export_state SET exported_revision=?, last_export_at=?, last_error=NULL
                   WHERE attendance_date=?""",
                (revision, now.isoformat(), date),
            )

    def mark_export_error(self, date: str, message: str):
        with self.transaction() as connection:
            connection.execute(
                "UPDATE export_state SET last_error=? WHERE attendance_date=?", (message, date)
            )
