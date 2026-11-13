# Presence backend — FastAPI + CV

Python backend with FastAPI, YuNet detection, quality checks, SFace embeddings, per-browser temporal confirmation, persistent SQLite/PostgreSQL attendance and automatic Excel export. The standalone CLI remains available for diagnostics.

## Environment

Validated on Windows with Python 3.13.5, OpenCV 4.14.0, NumPy 2.5.4 and openpyxl 3.1.5. The project-local environment is `backend/.venv`. Use Python 3.13 to reproduce the supplied lockfile.

From the repository root, run these commands for a fresh installation.

```powershell
py -3.13 -m venv backend/.venv
cd backend
.venv/Scripts/python.exe -m pip install -r requirements.lock.txt
.venv/Scripts/python.exe -m pip install -e . --no-deps
.venv/Scripts/python.exe main.py setup-models
.venv/Scripts/python.exe main.py doctor
```

All remaining commands in this document run from `backend/`. For a different compatible Python environment, `python -m pip install -e ".[desktop,dev]"` resolves dependencies according to pyproject.toml. The locked environment above is the one used for the reported checks.

## Models

`models/manifest.json` pins the OpenCV Zoo revision, filenames, sizes and SHA-256 hashes. Setup downloads the two ONNX files and checks them before replacing local copies. Runtime verifies both hashes before loading the models once on CPU.

| Model | Role | Size | License |
| --- | --- | --- | --- |
| face_detection_yunet_2023mar.onnx | Detection and five landmarks | 232,589 bytes | MIT |
| face_recognition_sface_2021dec.onnx | Aligned face → 128-dimensional embedding | 38,696,353 bytes | Apache 2.0 |

Model license files are included in `models/`. Model weights are downloaded locally and excluded from Git. Model identity and alignment pipeline metadata travel with each stored embedding.

## Run the web API

From backend/, after setup:

```powershell
.venv/Scripts/python.exe -m uvicorn presence_cv.api:app --host 127.0.0.1 --port 8000
```

Start Next.js separately and open its workspace. The browser owns the webcam; close standalone camera previews before using it. Register real profiles directly through the web. See [WEB_DEMO](../docs/WEB_DEMO.md) and the [HTTP contract](../docs/INTERFACES.md).

PRESENCE_DATA_DIR overrides the local scratch directory. DATABASE_URL selects PostgreSQL instead of the default SQLite. The web API defaults to download-only Excel when a database URL is supplied. PRESENCE_EXPORT_MODE can explicitly select daily or download. PRESENCE_BACKEND_KEY optionally requires X-Presence-Key from the Next.js server. Use one Uvicorn worker. The API loads the models once, serializes inference, and shares the exporter/database while retaining independent per-browser tracking.

For local connections, both API and CLI read .env and .env.local from the repository root and backend directory. Backend files override root files, .env.local overrides .env, and process environment variables have highest priority. Neon init can write DATABASE_URL and DATABASE_URL_UNPOOLED into the root .env.local; the app uses the pooled DATABASE_URL. Keep these files outside Git. Hosting services use their environment settings. Restart the backend after editing env files. To explicitly use SQLite in a test subprocess on Windows, provide a whitespace DATABASE_URL, which is trimmed to an empty value.

Web registration validates exactly three distinct, quality-approved photos of one consistent identity. It stores name, string ID and embeddings atomically. Original web photos are not saved. Duplicate/similar identities are rejected; exact retry of a committed registration is idempotent. Live recognition is the only web route that creates attendance.

The web adapter uses a 2.5s maximum observation gap, 6s confirmation window and 3s maximum frame age to accommodate low-CPU hosting and request timing. PRESENCE_CV_THREADS controls inference threads; the cloud image uses 1. Other thresholds remain the defaults below. Per-frame age is measured on the backend clock.

## Register a member with the CLI

Collect three different, consented photographs of the same person. Aim for a clear frontal image and two small changes in head direction. Store private inputs under the ignored `var/` directory.

```powershell
.venv/Scripts/python.exe main.py register --id "0012345" --name "Triệu Thiên Ân" --images "var/enrollment/an/front.jpg" "var/enrollment/an/left.jpg" "var/enrollment/an/right.jpg"
```

Or use the standalone webcam enrollment preview.

```powershell
.venv/Scripts/python.exe main.py register --id "0012345" --name "Triệu Thiên Ân" --camera 0
```

Press Space to collect each sample, wait for the next angle, and press Q or Escape to cancel. Each sample must contain exactly one quality-approved face. Three distinct frame digests are required. Exact repeated images are rejected. The operator follows the angle prompts. Automated checks enforce exposure, sharpness, visibility and landmark geometry.

Registration stores the identity and three normalized float32 embeddings atomically in SQLite. Original photos stay in memory during webcam enrollment. The profile becomes available after gallery reload. ID comparison is case-sensitive after trimming. Leading zeros and Unicode names are preserved.

If a face is very similar to an existing identity, registration reports `POSSIBLE_DUPLICATE_FACE`. Review the ID before using `--allow-similar` for an intentional exception. That warning uses an initial cosine threshold of 0.65. The threshold needs validation on group data.

## Run attendance

```powershell
.venv/Scripts/python.exe main.py run --source 0
```

The preview shows face boxes, landmarks, names, confirmation states and the latest attendance notification. Q/Escape closes the session, R retries pending Excel exports, and G reloads identities registered by another process. The capture worker owns and releases the webcam and keeps only the latest frame. Windows tries DirectShow then Media Foundation.

For a bounded camera check or prerecorded video, use headless mode.

```powershell
.venv/Scripts/python.exe main.py doctor --camera
.venv/Scripts/python.exe main.py run --source 0 --headless --max-frames 20
.venv/Scripts/python.exe main.py run --source "var/verification/held_out_arrival.avi" --headless
```

Notifications are newline-delimited JSON on stdout. Successful attendance is emitted only after SQLite commits. Typical event kinds are `registration_created`, `attendance_created`, `attendance_already_exists`, `attendance_failed`, `excel_synced`, `excel_pending` and `excel_failed`.

An empty gallery can still be used to verify camera capture and inference. Register people before expecting named attendance. Profiles registered while a session is running can be loaded with G. The web adapter reloads the gallery after registration and updates browser sessions at the next frame.

## Inspect one image

```powershell
.venv/Scripts/python.exe main.py inspect --image "var/probe.jpg"
.venv/Scripts/python.exe main.py inspect --image "var/probe.jpg" --output "var/annotated.jpg"
```

Inspect reports detections, quality metrics and matching candidates. Temporal confirmation and attendance creation run through the streaming session.

## Read and export attendance

```powershell
.venv/Scripts/python.exe main.py members
.venv/Scripts/python.exe main.py records
.venv/Scripts/python.exe main.py records --date 2026-11-13
.venv/Scripts/python.exe main.py export
.venv/Scripts/python.exe main.py export --date 2026-11-13
```

`export` retries days with pending revisions, errors or missing files. `export --date` explicitly rebuilds a day, including a workbook that was edited or damaged externally. These data commands work without loading model weights.

Default outputs are `var/attendance.sqlite3` and `var/exports/attendance_YYYY_MM_DD.xlsx`. Columns are No., ID, Full Name, Date, Time and Status. ID and name cells are explicitly text, including values beginning with `=`. Names are snapshots from the original check-in.

SQLite enforces one ID per local date in `Asia/Ho_Chi_Minh`, including after process restart and concurrent requests. The attendance transaction also increments the day's export revision. Excel runs on a separate worker. It writes a temporary workbook, atomically replaces the destination and then records the exported revision. File locks leave attendance saved and export pending. Startup recovers pending work, and explicit retry is available through R or the export command. Per-day file locks coordinate simultaneous exporters across processes.

Use a separate data directory for experiments. Global arguments precede the subcommand.

```powershell
.venv/Scripts/python.exe main.py --data-dir "var/my-demo" run --source 0
.venv/Scripts/python.exe main.py --config "config/default.json" --data-dir "var/my-demo" records
```

## Recognition settings

`config/default.json` contains starting values, with validation in `presence_cv/config.py`.

| Setting | Initial value | Meaning |
| --- | --- | --- |
| detector_max_size | 640 | Maximum detector image side, preserving aspect ratio |
| detector_threshold | 0.9 | YuNet detection cutoff |
| min_face_size | 80 pixels | Smallest original-frame box side |
| min_eye_distance | 24 pixels | Required landmark separation |
| min/max_brightness | 40 / 220 | Mean luminance in aligned 112×112 crop |
| min_sharpness | 50 | Laplacian variance in aligned crop |
| max_roll_degrees | 25 | Landmark eye-line tilt |
| max_nose_offset | 0.65 | Nose horizontal offset / inter-eye distance |
| match_threshold | 0.45 | Best ID must exceed this cosine similarity |
| match_margin | 0.08 | Required gap between best and second-best IDs |
| confirmation_frames | 3 | Minimum consistent observations of the same tracked face |
| confirmation_seconds | 0.35 | Minimum evidence duration |
| confirmation_window | 1.5 seconds | Rolling evidence window |
| max_observation_gap | 0.6 seconds | Reset after an observation gap |
| max_frame_age | 1.0 second | Reject stale frames before and after inference |

The nose-offset check is a geometric heuristic. It provides a conservative pose gate. SFace uses its native BGR alignment path followed by L2-normalized embeddings. The best score is the maximum across a person's three samples. The runner-up is a different ID. Similarity is reported as a cosine score.

Evidence is reset when the face disappears, becomes low quality, changes candidate identity, has ambiguous spatial association, or belongs to an old generation. Overlapping/crossing faces are conservatively deferred. Database failures allow a delayed retry. Gallery reload resets confirmation. An unsuccessful reload pauses recognition until recovery.

## Verify the baseline

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check presence_cv tools tests
.venv/Scripts/python.exe -m pip check
```

Core tests use deterministic embeddings and clocks for concurrency, midnight rollover, transactions, retries, Excel text safety, file locks, tracking and stale results. Model tests use actual ONNX inference when the verification fixtures are available. Test scratch data lives under the reserved `var/pytest` directory, which pytest recreates on each run.

To prepare public smoke-test fixtures and run actual models through the full workflow, use these commands.

```powershell
.venv/Scripts/python.exe -m tools.verification_data
.venv/Scripts/python.exe -m tools.verify_baseline
.venv/Scripts/python.exe -m pytest -q -m models
```

Fixtures are downloaded from a pinned revision of the face_recognition examples repository. Their source URLs and hashes are recorded in `var/verification/sources.json`. They remain in the ignored local directory. Enrollment variants share one source photo, and the known probe is a different photograph. A separate identity tests unknown rejection. This is a functional smoke test. Field recognition rates require independent student trials.

The smoke report is `var/verification/report.json`. It includes config, timings, decisions, notifications, SQLite/workbook locations and a generated video fixture. A tracked summary is in [CV_BASELINE.md](../docs/CV_BASELINE.md).

## Integration boundary

`BaselineSession.register()` accepts identity data and three BGR images. `BaselineSession.process()` accepts a `FramePacket` and returns a serializable `FrameResult` with faces, quality, scores, confirmation states and committed attendance events. Background Excel events are drained through the same result or `session.exports.drain_events()`.

One inference worker owns the shared VisionEngine. Each browser session has its own tracker/generation and shares the repository and exporter. The implemented FastAPI adapter feeds browser frames into this boundary and supplies monotonic timestamps from the backend clock domain. See [ARCHITECTURE](../docs/ARCHITECTURE.md).

Original-frame box and landmark coordinates are returned after detector resizing is undone. Match metadata includes the gallery version. Stop/restart camera generation and sequence IDs belong to the controller. Call `close()` to release the exporter, and close `LatestFrames` to release the camera. `flush()` waits for queued attempts to finish. Inspect pending dates/events to determine whether all workbooks synchronized.

## Remaining validation

The initial thresholds need calibration using the four members and independent people outside the gallery, across the planned lighting/pose/glasses tests. The RGB identity pipeline also needs its planned phone-photo spoofing test. Liveness is a separate future capability. Browser integration is implemented and tested with actual models and an isolated database. Field measurements with the group remain to be collected after their web enrollment.

## Free cloud deployment

See [Render/Neon walkthrough](../docs/DEPLOYMENT.md). Docker builds from backend/, installs requirements-cloud.lock.txt with opencv-python-headless, downloads pinned ONNX files and runs as a non-root user. The runtime command binds 0.0.0.0 and reads PORT.

DATABASE_URL is a PostgreSQL URI from Neon's Connect dialog, including TLS parameters. The repository uses psycopg binary, parameterized SQL, atomic enrollment and UNIQUE(person_id, attendance_date). Read snapshots use repeatable-read transactions. Schema initialization is serialized with a transaction-scoped advisory lock. Connections are closed after each operation, with prepared statements disabled for transaction pool compatibility.

Download mode stores attendance in the database and builds Excel in memory per download/filter. It starts no background Excel worker and requires no persistent filesystem. Local daily mode retains automatic files, revisions and retry behavior. SQLite and existing local data stay usable when DATABASE_URL is unset.

To run PostgreSQL integration checks, set PRESENCE_TEST_DATABASE_URL to a dedicated test server and run pytest. Each test creates and removes a unique schema there. To test the container locally, build from the repository root:

```powershell
docker build -t presence-api ./backend
```

Run it with DATABASE_URL and PRESENCE_BACKEND_KEY supplied through your local environment or an ignored env file. Keep the database URL out of shell history when using real credentials. The cloud runtime has no GUI preview; physical webcam capture remains in the browser.
