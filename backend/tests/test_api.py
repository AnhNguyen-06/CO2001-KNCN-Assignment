import base64
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from threading import Event
import time

import cv2
from fastapi.testclient import TestClient
import numpy as np
from openpyxl import load_workbook
import pytest

from presence_cv.api import create_app
from presence_cv.config import Config, Paths
from tools.verification_data import FIXTURES, enrollment_images
from presence_cv.vision import read_image

pytestmark = pytest.mark.models


def jpeg(image):
    ok, data = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    assert ok
    return data.tobytes()


def data_url(image):
    return "data:image/jpeg;base64," + base64.b64encode(jpeg(image)).decode()


def registration(person_id="0000123", name="Verification user", source="obama.jpg"):
    return {
        "person_id": person_id,
        "full_name": name,
        "images": [data_url(image) for image in enrollment_images(source)],
    }


@pytest.fixture
def app(tmp_path):
    if (
        not (Paths().model_dir / "face_recognition_sface_2021dec.onnx").exists()
        or not (FIXTURES / "obama2.jpg").exists()
    ):
        pytest.skip("Run setup-models and python -m tools.verification_data first")
    return create_app(Config.load(), Paths(data_dir=tmp_path))


@pytest.fixture
def client(app):
    with TestClient(app) as value:
        yield value


def recognize(client, token, image, start=1, count=4):
    responses = []
    for index in range(start, start + count):
        response = client.post(
            f"/api/recognition/sessions/{token}/frames?frame_id={index}",
            content=jpeg(image),
            headers={"content-type": "image/jpeg"},
        )
        assert response.status_code == 200, response.text
        responses.append(response.json())
        time.sleep(0.18)
    return responses


def test_api_starts_empty_and_registers_real_profile_atomically(client):
    assert client.get("/api/workspace").json() == {"members": [], "records": [], "exports": []}
    payload = registration(name="Nguyễn Văn Kiểm Thử")
    assert client.post("/api/registration/sample", json={"image": payload["images"][0]}).json()[
        "accepted"
    ]
    response = client.post("/api/members", json=payload)
    assert response.status_code == 201, response.text
    snapshot = client.get("/api/workspace").json()
    assert snapshot["members"][0]["id"] == "0000123"
    assert snapshot["members"][0]["name"] == "Nguyễn Văn Kiểm Thử"
    assert "embedding" not in snapshot["members"][0]
    assert client.post("/api/members", json=payload).json()["outcome"] == "already_registered"
    payload["full_name"] = "Conflicting identity"
    assert client.post("/api/members", json=payload).status_code == 409
    assert len(client.get("/api/workspace").json()["members"]) == 1


def test_invalid_samples_do_not_create_accounts(client):
    blank = data_url(np.zeros((480, 640, 3), dtype=np.uint8))
    assert (
        client.post("/api/registration/sample", json={"image": blank}).json()["code"]
        == "SAMPLE_NO_FACE"
    )
    payload = registration()
    payload["images"][1] = data_url(enrollment_images("biden.jpg")[0])
    response = client.post("/api/members", json=payload)
    assert response.status_code == 422
    assert response.json()["code"] == "SAMPLE_IDENTITY_MISMATCH"
    assert client.get("/api/workspace").json()["members"] == []


def test_web_recognition_saves_sqlite_exports_and_survives_restart(client, app):
    assert client.post("/api/members", json=registration()).status_code == 201
    token = client.post("/api/recognition/sessions").json()["token"]
    probe = read_image(FIXTURES / "obama2.jpg")
    frames = recognize(client, token, probe)
    assert (
        sum(event["kind"] == "attendance_created" for frame in frames for event in frame["events"])
        == 1
    )
    client.delete(f"/api/recognition/sessions/{token}")
    assert app.state.runtime.session.exports.flush()
    snapshot = client.get("/api/workspace").json()
    assert len(snapshot["records"]) == 1 and snapshot["records"][0]["memberId"] == "0000123"
    assert snapshot["exports"][0]["status"] == "synced"
    response = client.get(
        "/api/exports/download", params={"member_id": "0000123", "q": "Verification"}
    )
    assert response.status_code == 200
    workbook = load_workbook(BytesIO(response.content))
    try:
        assert workbook["Attendance"]["B2"].value == "0000123"
        assert workbook["Attendance"]["B2"].data_type == "s"
    finally:
        workbook.close()
    restarted_app = create_app(Config.load(), app.state.runtime.paths)
    with TestClient(restarted_app) as restarted:
        assert len(restarted.get("/api/workspace").json()["members"]) == 1
        token = restarted.post("/api/recognition/sessions").json()["token"]
        frames = recognize(restarted, token, probe)
        assert any(
            event["kind"] == "attendance_already_exists"
            for frame in frames
            for event in frame["events"]
        )
        assert len(restarted.get("/api/workspace").json()["records"]) == 1


def test_unknown_and_stopped_session_cannot_check_in(client):
    client.post("/api/members", json=registration())
    token = client.post("/api/recognition/sessions").json()["token"]
    frames = recognize(client, token, read_image(FIXTURES / "lin-manuel-miranda.png"))
    assert all(
        not frame["events"]
        or all(not event["kind"].startswith("attendance_") for event in frame["events"])
        for frame in frames
    )
    assert client.get("/api/workspace").json()["records"] == []
    assert client.delete(f"/api/recognition/sessions/{token}").status_code == 200
    assert (
        client.post(
            f"/api/recognition/sessions/{token}/frames?frame_id=5",
            content=jpeg(read_image(FIXTURES / "obama2.jpg")),
        ).status_code
        == 409
    )


def test_browser_sessions_keep_confirmation_separate(client):
    client.post("/api/members", json=registration("A"))
    client.post("/api/members", json=registration("B", source="biden.jpg"))
    first = client.post("/api/recognition/sessions").json()["token"]
    second = client.post("/api/recognition/sessions").json()["token"]
    a, b = read_image(FIXTURES / "obama2.jpg"), read_image(FIXTURES / "biden.jpg")
    for index in range(1, 5):
        for token, image, expected in [(first, a, "A"), (second, b, "B")]:
            response = client.post(
                f"/api/recognition/sessions/{token}/frames?frame_id={index}", content=jpeg(image)
            )
            assert response.status_code == 200
            assert response.json()["faces"][0]["match"]["person_id"] == expected
        time.sleep(0.15)
    assert {row["memberId"] for row in client.get("/api/workspace").json()["records"]} == {"A", "B"}
    client.delete(f"/api/recognition/sessions/{first}")
    assert (
        client.post(
            f"/api/recognition/sessions/{second}/frames?frame_id=6", content=jpeg(b)
        ).status_code
        == 200
    )


def test_payload_limits_and_expired_session(client, app):
    assert client.post("/api/registration/sample", json={"image": "not-a-photo"}).status_code == 422
    token = client.post("/api/recognition/sessions").json()["token"]
    assert (
        client.post(
            f"/api/recognition/sessions/{token}/frames?frame_id=1", content=b"0" * (1024 * 1024 + 1)
        ).status_code
        == 413
    )
    app.state.runtime.leases[token].last_seen -= 100
    assert (
        client.post(
            f"/api/recognition/sessions/{token}/frames?frame_id=2", content=b"bad"
        ).status_code
        == 409
    )


def test_hosted_backend_key_stays_server_side(client, monkeypatch):
    monkeypatch.setenv("PRESENCE_BACKEND_KEY", "test-server-secret")
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/workspace").status_code == 401
    assert (
        client.get("/api/workspace", headers={"X-Presence-Key": "test-server-secret"}).status_code
        == 200
    )


def test_stopping_camera_during_inference_cancels_pending_check_in(client, app, monkeypatch):
    client.post("/api/members", json=registration())
    token = client.post("/api/recognition/sessions").json()["token"]
    probe = read_image(FIXTURES / "obama2.jpg")
    recognize(client, token, probe, count=2)
    runtime = app.state.runtime
    original = runtime.session.vision.analyze
    entered, release = Event(), Event()

    def delayed(*args):
        faces = original(*args)
        entered.set()
        assert release.wait(5)
        return faces

    monkeypatch.setattr(runtime.session.vision, "analyze", delayed)
    with ThreadPoolExecutor(max_workers=2) as requests:
        frame = requests.submit(
            client.post,
            f"/api/recognition/sessions/{token}/frames?frame_id=3",
            content=jpeg(probe),
        )
        try:
            assert entered.wait(5)
            stop = requests.submit(client.delete, f"/api/recognition/sessions/{token}")
            deadline = time.monotonic() + 3
            while runtime.lease_current(token) and time.monotonic() < deadline:
                time.sleep(0.01)
            assert not runtime.lease_current(token)
        finally:
            release.set()
        assert frame.result(timeout=5).json()["stale"]
        assert stop.result(timeout=5).status_code == 200
    assert client.get("/api/workspace").json()["records"] == []
