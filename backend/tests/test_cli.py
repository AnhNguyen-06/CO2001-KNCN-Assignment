import json
import subprocess
import sys

import cv2

from presence_cv.config import BACKEND_ROOT
from presence_cv.display import window_open


def test_cli_reports_unreadable_database_as_structured_error(tmp_path):
    (tmp_path / "attendance.sqlite3").write_bytes(b"This is not a SQLite database")
    result = subprocess.run(
        [sys.executable, str(BACKEND_ROOT / "main.py"), "--data-dir", str(tmp_path), "records"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["error"] == "DatabaseError"
    assert "database" in payload["message"]
    assert "Traceback" not in result.stderr


def test_closed_native_window_is_a_normal_stop(monkeypatch):
    def closed(*_):
        raise cv2.error("Window has already been destroyed")

    monkeypatch.setattr(cv2, "getWindowProperty", closed)
    assert not window_open("Presence CV baseline")
