"""Deterministic camera videos for browser tests using real CV inference."""

import math

import cv2
import numpy as np

from .verification_data import FIXTURES
from presence_cv.vision import read_image


def create_video(source, destination):
    image = read_image(FIXTURES / source) if source else np.full((480, 640, 3), 90, dtype=np.uint8)
    height, width = image.shape[:2]
    scale = min(640 / width, 480 / height)
    resized = cv2.resize(image, (round(width * scale), round(height * scale)))
    canvas = np.zeros((480, 640, 3), dtype=np.uint8)
    x, y = (640 - resized.shape[1]) // 2, (480 - resized.shape[0]) // 2
    canvas[y : y + resized.shape[0], x : x + resized.shape[1]] = resized
    with destination.open("wb") as output:
        output.write(b"YUV4MPEG2 W640 H480 F5:1 Ip A1:1 C420jpeg\n")
        for index in range(60):
            angle = math.sin(index / 4) * 3
            matrix = cv2.getRotationMatrix2D((320, 240), angle, 1)
            frame = cv2.warpAffine(canvas, matrix, (640, 480))
            cv2.putText(frame, str(index), (8, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (90, 90, 90), 1)
            output.write(b"FRAME\n")
            output.write(cv2.cvtColor(frame, cv2.COLOR_BGR2YUV_I420).tobytes())


def main():
    directory = FIXTURES.parent
    for source, filename in [
        ("obama.jpg", "web-camera-known.y4m"),
        ("lin-manuel-miranda.png", "web-camera-unknown.y4m"),
        (None, "web-camera-empty.y4m"),
    ]:
        create_video(source, directory / filename)
        print(directory / filename)


if __name__ == "__main__":
    main()
