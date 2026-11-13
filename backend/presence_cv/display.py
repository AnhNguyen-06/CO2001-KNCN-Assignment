from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .types import FrameResult


def window_open(title: str):
    try:
        return cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) >= 1
    except cv2.error:
        return False


def display_font(size: int):
    candidates = [
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def annotate(image: np.ndarray, result: FrameResult, names: dict[str, str], notification: str = ""):
    output = image.copy()
    labels = []
    for face in result.faces:
        x, y, width, height = map(round, face.bbox)
        color = (
            (178, 207, 160)
            if face.state in ("created", "already_exists", "confirmed")
            else (230, 190, 150)
        )
        cv2.rectangle(output, (x, y), (x + width, y + height), color, 2)
        for point in face.landmarks:
            cv2.circle(output, tuple(map(round, point)), 2, color, -1)
        name = names.get(face.match.person_id, "Unknown")
        if not face.quality.accepted:
            name = ", ".join(face.quality.reasons)
        labels.append(((max(0, x), max(5, y - 30)), f"{name} · {face.state}"))
    rgb = Image.fromarray(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(rgb)
    font = display_font(19)
    for position, label in labels:
        bounds = draw.textbbox(position, label, font=font)
        draw.rectangle(
            (bounds[0] - 3, bounds[1] - 2, bounds[2] + 5, bounds[3] + 3), fill=(9, 14, 25)
        )
        draw.text(position, label, font=font, fill=(209, 228, 250))
    status = (
        notification or f"{result.processing_ms:.0f} ms · Q quit · R retry Excel · G reload gallery"
    )
    if result.stale:
        status = "Frame skipped because its result was stale."
    draw.rectangle(
        (0, max(0, image.shape[0] - 39), image.shape[1], image.shape[0]), fill=(5, 6, 15)
    )
    draw.text(
        (12, max(0, image.shape[0] - 32)), status, font=display_font(17), fill=(209, 228, 250)
    )
    return cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)
