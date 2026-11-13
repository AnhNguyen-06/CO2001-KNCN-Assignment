"""Local/persistent-host web adapter. The browser owns the camera."""

import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, replace
from datetime import date as Date
from functools import partial
import hashlib
from io import BytesIO
import os
from pathlib import Path
import secrets
from threading import RLock
import time

import cv2
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
import numpy as np
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field, ValidationError

from .config import Config, Paths
from .export import attendance_workbook
from .session import BaselineSession
from .types import BaselineError, FramePacket

MAX_BODY = 4 * 1024 * 1024
MAX_IMAGE = 1024 * 1024
LEASE_SECONDS = 15


class SampleInput(BaseModel):
    image: str = Field(max_length=1500000)


class RegistrationInput(BaseModel):
    person_id: str = Field(min_length=1, max_length=64)
    full_name: str = Field(min_length=1, max_length=120)
    images: list[str] = Field(min_length=3, max_length=3)


async def bounded_body(request: Request, limit=MAX_BODY):
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > limit:
            raise HTTPException(
                413,
                detail={"code": "IMAGE_TOO_LARGE", "message": "The image payload is too large."},
            )
    return bytes(data)


async def json_input(request: Request, model):
    try:
        return model.model_validate_json(await bounded_body(request))
    except ValidationError as error:
        raise HTTPException(
            422,
            detail={
                "code": "INVALID_INPUT",
                "message": "Check the required fields and image count.",
            },
        ) from error


def decode_image(data: bytes):
    if not data or len(data) > MAX_IMAGE:
        raise BaselineError("INVALID_IMAGE", "Supply a JPEG or PNG image smaller than 1 MB.")
    try:
        with Image.open(BytesIO(data)) as header:
            width, height = header.size
            if (
                header.format not in ("JPEG", "PNG")
                or max(width, height) > 2400
                or width * height > 4000000
            ):
                raise BaselineError(
                    "INVALID_IMAGE", "Use a JPEG/PNG camera image up to 2400 pixels per side."
                )
        image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    except (UnidentifiedImageError, OSError, ValueError, cv2.error) as error:
        raise BaselineError("INVALID_IMAGE", "The image could not be decoded.") from error
    if image is None:
        raise BaselineError("INVALID_IMAGE", "The image could not be decoded.")
    return image


def decode_data_url(value: str):
    if not value.startswith(("data:image/jpeg;base64,", "data:image/png;base64,")):
        raise BaselineError("INVALID_IMAGE", "Capture a JPEG or PNG photo from your camera.")
    try:
        return decode_image(base64.b64decode(value.split(",", 1)[1], validate=True))
    except (ValueError, TypeError) as error:
        raise BaselineError("INVALID_IMAGE", "Invalid image encoding.") from error


@dataclass
class Lease:
    token: str
    generation: int
    last_seen: float
    stream: BaselineSession


class WebRuntime:
    def __init__(self, config: Config, paths: Paths):
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="presence-inference")
        self.config, self.paths = config, paths
        self.session = None
        self.leases: dict[str, Lease] = {}
        self.generation = 0
        self.lock = RLock()

    async def call(self, function, *args):
        return await asyncio.get_running_loop().run_in_executor(
            self.executor, partial(function, *args)
        )

    async def start(self):
        self.session = await self.call(BaselineSession, self.config, self.paths)

    async def close(self):
        for token in list(self.leases):
            stream = self.end(token)
            if stream:
                await self.call(stream.close)
        if self.session:
            await self.call(self.session.close)
        self.executor.shutdown(wait=True, cancel_futures=True)

    def lease_current(self, token: str):
        with self.lock:
            lease = self.leases.get(token)
            return lease is not None and time.monotonic() - lease.last_seen < LEASE_SECONDS

    def begin(self):
        with self.lock:
            for token, lease in list(self.leases.items()):
                if time.monotonic() - lease.last_seen >= LEASE_SECONDS:
                    lease.stream.close()
                    del self.leases[token]
            if len(self.leases) >= 64:
                raise BaselineError(
                    "CAMERA_BUSY", "The recognition service is busy. Retry shortly."
                )
            self.generation += 1
            stream = BaselineSession(
                self.config,
                self.paths,
                vision=self.session.vision,
                repository=self.session.repository,
                exports=self.session.exports,
            )
            lease = Lease(secrets.token_urlsafe(32), self.generation, time.monotonic(), stream)
            self.leases[lease.token] = lease
            return {"token": lease.token, "generation": lease.generation}

    def end(self, token: str):
        with self.lock:
            lease = self.leases.pop(token, None)
            return lease.stream if lease else None

    def process(self, token: str, frame_id: int, received_at: float, data: bytes):
        with self.lock:
            if not self.lease_current(token):
                raise BaselineError(
                    "SESSION_EXPIRED", "The camera session ended. Turn the camera on again."
                )
            lease = self.leases[token]
            generation = lease.generation
            lease.last_seen = time.monotonic()
        if lease.stream.gallery.version != self.session.gallery.version:
            lease.stream.reload_gallery()
        image = decode_image(data)
        result = lease.stream.process(
            FramePacket(generation, frame_id, received_at, image),
            is_current=lambda: self.lease_current(token),
        )
        payload = asdict(result)
        payload.update({"image_width": image.shape[1], "image_height": image.shape[0]})
        for face in payload["faces"]:
            face["name"] = self.session.gallery.names.get(face["match"]["person_id"])
        return payload

    def validate_sample(self, data_url: str):
        sample = self.session.vision.make_sample(decode_data_url(data_url))
        return {"accepted": True, "quality": asdict(sample.quality)}

    def register(self, payload: RegistrationInput):
        images = [decode_data_url(value) for value in payload.images]
        person_id, name = payload.person_id.strip(), payload.full_name.strip()
        repository = self.session.repository
        # A lost HTTP response can be retried with the same three photos safely.
        existing = next(
            (row for row in repository.members() if row["person_id"] == person_id), None
        )
        if existing:
            digests = {hashlib.sha256(image.tobytes()).hexdigest() for image in images}
            with repository.connection() as connection:
                stored = {
                    row["image_digest"]
                    for row in connection.execute(
                        "SELECT image_digest FROM face_samples WHERE person_id=?", (person_id,)
                    )
                }
            if existing["full_name"] == name and len(digests) == 3 and digests == stored:
                self.session.reload_gallery()
                return {"outcome": "already_registered", "person_id": person_id}
            raise BaselineError(
                "DUPLICATE_ID", "This ID is already registered. Use a different ID."
            )
        event = self.session.register(person_id, name, images)
        return {"outcome": "created", **asdict(event)}


def create_app(config: Config | None = None, paths: Paths | None = None):
    config = config or replace(
        Config.load(),
        max_observation_gap=2.5,
        confirmation_window=6.0,
        max_frame_age=3.0,
        opencv_threads=int(os.environ.get("PRESENCE_CV_THREADS", "4")),
    )
    database_url = os.environ.get("DATABASE_URL", "").strip() or None
    paths = paths or Paths(
        data_dir=Path(os.environ.get("PRESENCE_DATA_DIR", str(Paths().data_dir))).resolve(),
        database_url=database_url,
        export_mode=os.environ.get("PRESENCE_EXPORT_MODE", "download" if database_url else "daily"),
    )

    @asynccontextmanager
    async def lifespan(app):
        runtime = WebRuntime(config, paths)
        await runtime.start()
        app.state.runtime = runtime
        try:
            yield
        finally:
            await runtime.close()

    app = FastAPI(title="Presence API", version="1.0.0", lifespan=lifespan)

    @app.middleware("http")
    async def private_backend(request: Request, call_next):
        key = os.environ.get("PRESENCE_BACKEND_KEY", "")
        if (
            key
            and request.url.path != "/api/health"
            and not secrets.compare_digest(request.headers.get("x-presence-key", ""), key)
        ):
            return JSONResponse(
                {
                    "code": "UNAUTHORIZED",
                    "message": "This endpoint is available through the web application.",
                },
                status_code=401,
            )
        return await call_next(request)

    @app.exception_handler(BaselineError)
    async def baseline_error(_request, error):
        status = (
            409
            if error.code
            in ("DUPLICATE_ID", "POSSIBLE_DUPLICATE_FACE", "CAMERA_BUSY", "SESSION_EXPIRED")
            else 422
        )
        return JSONResponse({"code": error.code, "message": str(error)}, status_code=status)

    @app.exception_handler(Exception)
    async def unexpected_error(_request, _error):
        return JSONResponse(
            {
                "code": "BACKEND_ERROR",
                "message": "The backend could not complete this request. Please retry.",
            },
            status_code=500,
        )

    @app.get("/api/health")
    async def health():
        return {
            "status": "ready",
            "storage": app.state.runtime.session.repository.storage,
            "export_mode": paths.export_mode,
            "timezone": config.timezone,
            "recognition": "YuNet + SFace",
        }

    @app.get("/api/workspace")
    async def workspace():
        return await asyncio.to_thread(workspace_snapshot)

    def workspace_snapshot():
        runtime = app.state.runtime
        repository = runtime.session.repository
        members = []
        for index, row in enumerate(repository.members()):
            if not row["active"]:
                continue
            members.append(
                {
                    "id": row["person_id"],
                    "name": row["full_name"],
                    "role": "Registered member",
                    "color": ["blue", "lavender", "teal", "silver"][index % 4],
                    "joinedAt": row["created_at"][:10],
                    "samples": 3,
                }
            )
        records = [
            {
                "id": str(row.attendance_id),
                "memberId": row.person_id,
                "name": row.full_name_snapshot,
                "recordedAt": row.recorded_at,
                "date": row.attendance_date,
                "source": "camera",
            }
            for row in reversed(repository.records())
        ]
        states = []
        for state in repository.export_states():
            state["status"] = (
                "available"
                if paths.export_mode == "download"
                else (
                    "error"
                    if state["last_error"]
                    else "synced"
                    if state["exported_revision"] == state["data_revision"]
                    and runtime.session.exporter.destination(state["attendance_date"]).exists()
                    else "pending"
                )
            )
            states.append(state)
        return {"members": members, "records": records, "exports": states}

    @app.post("/api/registration/sample")
    async def validate_sample(request: Request):
        payload = await json_input(request, SampleInput)
        return await app.state.runtime.call(app.state.runtime.validate_sample, payload.image)

    @app.post("/api/members", status_code=201)
    async def register(request: Request):
        payload = await json_input(request, RegistrationInput)
        return await app.state.runtime.call(app.state.runtime.register, payload)

    @app.post("/api/recognition/sessions")
    async def begin_session():
        return await app.state.runtime.call(app.state.runtime.begin)

    @app.delete("/api/recognition/sessions/{token}")
    async def end_session(token: str):
        stream = app.state.runtime.end(token)
        if stream:
            await app.state.runtime.call(stream.close)
        return {"stopped": True}

    @app.post("/api/recognition/sessions/{token}/frames")
    async def frame(token: str, request: Request, frame_id: int):
        if frame_id < 0:
            raise HTTPException(422, "frame_id must be nonnegative")
        received_at = time.monotonic()
        data = await bounded_body(request, MAX_IMAGE)
        return await app.state.runtime.call(
            app.state.runtime.process, token, frame_id, received_at, data
        )

    @app.post("/api/exports/retry")
    async def retry_exports():
        await asyncio.to_thread(app.state.runtime.session.exports.retry_pending)
        return {"scheduled": True}

    @app.get("/api/exports/download")
    async def download(date: Date | None = None, member_id: str = "", q: str = ""):
        return await asyncio.to_thread(download_workbook, date, member_id, q)

    def download_workbook(date, member_id, q):
        repository = app.state.runtime.session.repository
        records = [
            row
            for row in repository.records(date.isoformat() if date else None)
            if (not member_id or row.person_id == member_id)
            and (not q or q.casefold() in f"{row.full_name_snapshot} {row.person_id}".casefold())
        ]
        workbook = attendance_workbook(records, repository.timezone)
        stream = BytesIO()
        try:
            workbook.save(stream)
        finally:
            workbook.close()
        label = str(date).replace("-", "_") if date else "records"
        return Response(
            stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="attendance_{label}.xlsx"',
                "Cache-Control": "no-store",
            },
        )

    return app


app = create_app()
