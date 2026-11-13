from contextlib import contextmanager
from datetime import date as Date, datetime, timezone
import os
from pathlib import Path
from queue import Empty, Queue
import tempfile
from threading import Condition, Thread
import time

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from .storage import Repository
from .types import Event, ExportResult


@contextmanager
def export_lock(path: Path):
    """Coordinate exporters across processes without holding a SQLite write lock."""
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def attendance_workbook(records, local_timezone):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Attendance"
    sheet.append(["No.", "ID", "Full Name", "Date", "Time", "Status"])
    for index, record in enumerate(records, 1):
        local = datetime.fromisoformat(record.recorded_at).astimezone(local_timezone)
        sheet.append(
            [
                index,
                record.person_id,
                record.full_name_snapshot,
                record.attendance_date,
                local.strftime("%H:%M:%S"),
                record.status,
            ]
        )
        for column in (2, 3, 4, 5, 6):
            sheet.cell(index + 1, column).data_type = "s"
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="D8ECF8")
        cell.fill = PatternFill("solid", fgColor="10121D")
    for column, width in zip("ABCDEF", (8, 23, 34, 16, 15, 14), strict=True):
        sheet.column_dimensions[column].width = width
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    return workbook


class ExcelExporter:
    def __init__(self, repository: Repository, directory: Path):
        self.repository = repository
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def destination(self, date: str):
        Date.fromisoformat(date)
        return self.directory / f"attendance_{date.replace('-', '_')}.xlsx"

    def pending_dates(self):
        return [
            state["attendance_date"]
            for state in self.repository.export_states()
            if state["data_revision"] != state["exported_revision"]
            or state["last_error"]
            or not self.destination(state["attendance_date"]).is_file()
        ]

    def export_day(self, date: str):
        destination = self.destination(date)
        revision = 0
        temporary = None
        try:
            with export_lock(destination.with_suffix(".xlsx.lock")):
                records, revision = self.repository.export_snapshot(date)
                workbook = attendance_workbook(records, self.repository.timezone)
                try:
                    descriptor, filename = tempfile.mkstemp(
                        prefix=".attendance_", suffix=".xlsx", dir=self.directory
                    )
                    os.close(descriptor)
                    temporary = Path(filename)
                    workbook.save(temporary)
                finally:
                    workbook.close()
                os.replace(temporary, destination)
                self.repository.mark_exported(date, revision, datetime.now(timezone.utc))
                current = next(
                    (
                        state
                        for state in self.repository.export_states()
                        if state["attendance_date"] == date
                    ),
                    None,
                )
                outcome = "pending" if current and current["data_revision"] > revision else "synced"
                return ExportResult(date, outcome, revision, str(destination))
        except Exception as error:
            # The error is surfaced separately from an already committed attendance record.
            try:
                self.repository.mark_export_error(date, str(error))
            except Exception:
                pass
            return ExportResult(date, "failed", revision, str(destination), str(error))
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass


class ExportWorker:
    def __init__(self, exporter: ExcelExporter):
        self.exporter = exporter
        self.events: Queue[Event] = Queue()
        self.condition = Condition()
        self.pending: set[str] = set()
        self.active = False
        self.stopping = False
        self.thread = Thread(target=self._run, name="presence-excel", daemon=True)
        self.thread.start()
        self.retry_pending()

    def schedule(self, date: str):
        with self.condition:
            if self.stopping:
                return
            self.pending.add(date)
            self.condition.notify_all()

    def retry_pending(self):
        for date in self.exporter.pending_dates():
            self.schedule(date)

    def _run(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda: self.pending or self.stopping)
                if not self.pending and self.stopping:
                    return
                date = min(self.pending)
                self.pending.remove(date)
                self.active = True
            result = self.exporter.export_day(date)
            self.events.put(
                Event(
                    f"excel_{result.outcome}",
                    "Excel updated."
                    if result.outcome == "synced"
                    else "Attendance is saved. Excel update is pending."
                    if result.outcome == "pending"
                    else "Attendance is saved. Close the Excel file or check the export folder, then retry.",
                    {
                        "date": date,
                        "revision": result.revision,
                        "path": result.destination,
                        "error": result.error,
                    },
                )
            )
            with self.condition:
                if result.outcome == "pending":
                    self.pending.add(date)
                self.active = False
                self.condition.notify_all()

    def drain_events(self):
        events = []
        while True:
            try:
                events.append(self.events.get_nowait())
            except Empty:
                return events

    def flush(self, timeout: float = 10):
        deadline = time.monotonic() + timeout
        with self.condition:
            while self.pending or self.active:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self.condition.wait(remaining)
        return True

    def close(self):
        with self.condition:
            self.stopping = True
            self.condition.notify_all()
        self.thread.join(timeout=10)
        return not self.thread.is_alive()


class DownloadExports:
    """Cloud mode builds workbooks from durable database records on download."""

    def schedule(self, date: str):
        pass

    def retry_pending(self):
        pass

    def drain_events(self):
        return []

    def flush(self, timeout: float = 10):
        return True

    def close(self):
        return True
