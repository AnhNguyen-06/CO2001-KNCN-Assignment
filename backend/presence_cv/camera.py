import os
from threading import Condition, Thread
import time

import cv2

from .types import BaselineError, FramePacket


class LatestFrames:
    """Single owner and one-slot buffer. A slow consumer never queues old frames."""

    def __init__(self, source: str = "0", generation: int = 1):
        self.source = source
        self.generation = generation
        self.condition = Condition()
        self.latest: FramePacket | None = None
        self.stopping = False
        self.ended = False
        self.error: str | None = None
        self.thread = Thread(target=self._capture, name="presence-camera", daemon=True)

    def start(self):
        self.thread.start()
        return self

    def _capture(self):
        camera = None
        try:
            device = int(self.source) if self.source.isdecimal() else self.source
            api = cv2.CAP_DSHOW if isinstance(device, int) and os.name == "nt" else cv2.CAP_ANY
            camera = cv2.VideoCapture(device, api)
            if not camera.isOpened() and isinstance(device, int) and os.name == "nt":
                camera.release()
                camera = cv2.VideoCapture(device, cv2.CAP_MSMF)
            if not camera.isOpened():
                raise BaselineError(
                    "CAMERA_UNAVAILABLE", "Could not open the camera or video source."
                )
            if isinstance(device, int):
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            fps = camera.get(cv2.CAP_PROP_FPS)
            file_interval = 1 / fps if not isinstance(device, int) and 0 < fps <= 240 else 0
            next_frame = time.monotonic()
            index = 0
            while not self.stopping:
                if file_interval:
                    time.sleep(max(0, next_frame - time.monotonic()))
                    next_frame += file_interval
                ok, image = camera.read()
                if not ok:
                    if isinstance(device, int):
                        self.error = "The camera stopped delivering frames. Reconnect it and retry."
                    break
                index += 1
                packet = FramePacket(self.generation, index, time.monotonic(), image)
                with self.condition:
                    self.latest = packet
                    self.condition.notify_all()
        except Exception as error:
            self.error = str(error)
        finally:
            if camera is not None:
                camera.release()
            with self.condition:
                self.ended = True
                self.condition.notify_all()

    def read(self, after_frame_id: int = -1, timeout: float = 5):
        with self.condition:
            available = self.condition.wait_for(
                lambda: (
                    (self.latest is not None and self.latest.frame_id > after_frame_id)
                    or self.ended
                ),
                timeout=timeout,
            )
            if not available:
                raise BaselineError("CAMERA_TIMEOUT", "Timed out waiting for a camera frame.")
            if self.latest is not None and self.latest.frame_id > after_frame_id:
                return self.latest
            if self.error:
                raise BaselineError("CAMERA_UNAVAILABLE", self.error)
            return None

    def close(self):
        self.stopping = True
        if self.thread.is_alive():
            self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise BaselineError("CAMERA_TIMEOUT", "Camera driver has not released the device yet.")

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
