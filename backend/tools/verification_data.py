import hashlib
import json
from urllib.request import Request, urlopen

import cv2

from presence_cv.config import BACKEND_ROOT
from presence_cv.vision import read_image

REVISION = "9f3061aaeed9a8756d2c970f5dfe066617a8281d"
FILES = ("obama.jpg", "obama2.jpg", "biden.jpg", "lin-manuel-miranda.png", "two_people.jpg")
FIXTURES = BACKEND_ROOT / "var" / "verification" / "fixtures"


def fetch():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    sources = []
    for filename in FILES:
        destination = FIXTURES / filename
        url = f"https://raw.githubusercontent.com/ageitgey/face_recognition/{REVISION}/examples/{filename}"
        if not destination.exists():
            request = Request(url, headers={"User-Agent": "Presence-CV/0.1"})
            with urlopen(request, timeout=30) as response:
                content = response.read()
            temporary = destination.with_suffix(destination.suffix + ".download")
            temporary.write_bytes(content)
            temporary.replace(destination)
        sources.append(
            {
                "file": filename,
                "url": url,
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            }
        )
    (FIXTURES.parent / "sources.json").write_text(json.dumps(sources, indent=2), encoding="utf-8")
    return sources


def enrollment_images(filename: str):
    image = read_image(FIXTURES / filename)
    height, width = image.shape[:2]
    variants = [image]
    for angle in (-4, 4):
        matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
        variants.append(
            cv2.warpAffine(image, matrix, (width, height), borderMode=cv2.BORDER_REFLECT)
        )
    return variants


if __name__ == "__main__":
    print(json.dumps(fetch(), indent=2))
