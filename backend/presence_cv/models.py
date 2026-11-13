import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from .config import BACKEND_ROOT
from .types import BaselineError


def model_manifest():
    return json.loads((BACKEND_ROOT / "models" / "manifest.json").read_text(encoding="utf-8"))


def file_sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_models(directory: Path):
    found = {}
    for model in model_manifest()["models"]:
        path = directory / model["filename"]
        if not path.is_file() or path.stat().st_size != model["size"]:
            raise BaselineError(
                "MODEL_UNAVAILABLE", f"Missing or incomplete {path.name}. Run setup-models."
            )
        if file_sha256(path) != model["sha256"]:
            raise BaselineError(
                "MODEL_CHECKSUM", f"Checksum mismatch for {path.name}. Run setup-models."
            )
        found[model["name"]] = path
    return found


def download_models(directory: Path):
    manifest = model_manifest()
    directory.mkdir(parents=True, exist_ok=True)
    for model in manifest["models"]:
        target = directory / model["filename"]
        if (
            target.exists()
            and target.stat().st_size == model["size"]
            and file_sha256(target) == model["sha256"]
        ):
            continue
        url = (
            f"https://media.githubusercontent.com/media/opencv/opencv_zoo/"
            f"{manifest['revision']}/models/{model['directory']}/{model['filename']}"
        )
        temporary = target.with_suffix(".download")
        try:
            request = Request(url, headers={"User-Agent": "Presence-CV/0.1"})
            with urlopen(request, timeout=60) as response, temporary.open("wb") as destination:
                while chunk := response.read(1024 * 1024):
                    destination.write(chunk)
            if (
                temporary.stat().st_size != model["size"]
                or file_sha256(temporary) != model["sha256"]
            ):
                raise BaselineError(
                    "MODEL_CHECKSUM", f"Downloaded model failed verification: {target.name}"
                )
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return verify_models(directory)
