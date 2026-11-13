from dataclasses import dataclass
import hashlib
import math
from pathlib import Path

import cv2
import numpy as np

from .config import Config
from .models import model_manifest, verify_models
from .storage import unit_vector
from .types import BaselineError, Face, Gallery, Match, Quality, Sample


def read_image(path: Path):
    try:
        image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    except (OSError, cv2.error) as error:
        raise BaselineError("IMAGE_UNAVAILABLE", f"Cannot read image: {path}") from error
    if image is None:
        raise BaselineError("IMAGE_UNAVAILABLE", f"Unsupported or invalid image: {path}")
    return image


def match_embedding(embedding: np.ndarray, gallery: Gallery, config: Config):
    if not gallery.samples:
        return Match("no_gallery")
    vector = unit_vector(embedding)
    scores = sorted(
        (
            (person_id, float(np.max(samples @ vector)))
            for person_id, samples in gallery.samples.items()
        ),
        key=lambda item: (-item[1], item[0]),
    )
    person_id, score = scores[0]
    runner_up = scores[1][1] if len(scores) > 1 else None
    if score < config.match_threshold:
        return Match("unknown", score=score, runner_up_score=runner_up)
    if runner_up is not None and score - runner_up < config.match_margin:
        return Match("ambiguous", score=score, runner_up_score=runner_up)
    return Match("candidate", person_id, score, runner_up)


@dataclass
class Detection:
    face: Face
    sample: Sample | None


class VisionEngine:
    """Own one instance per inference worker. OpenCV model objects are not shared."""

    def __init__(self, config: Config, model_dir: Path):
        self.config = config
        models = verify_models(model_dir)
        manifest = {item["name"]: item for item in model_manifest()["models"]}
        self.model_id = f"sface-2021dec:{manifest['sface']['sha256']}"
        self.preprocessing_version = (
            f"yunet-2023mar:{manifest['yunet']['sha256']}:alignCrop-bgr-l2-v1"
        )
        cv2.setNumThreads(config.opencv_threads)
        self.detector = cv2.FaceDetectorYN.create(
            str(models["yunet"]),
            "",
            (320, 320),
            config.detector_threshold,
            0.3,
            5000,
            cv2.dnn.DNN_BACKEND_OPENCV,
            cv2.dnn.DNN_TARGET_CPU,
        )
        self.recognizer = cv2.FaceRecognizerSF.create(
            str(models["sface"]),
            "",
            cv2.dnn.DNN_BACKEND_OPENCV,
            cv2.dnn.DNN_TARGET_CPU,
        )

    def _detect(self, image: np.ndarray):
        if (
            not isinstance(image, np.ndarray)
            or image.dtype != np.uint8
            or image.ndim != 3
            or image.shape[2] != 3
        ):
            raise BaselineError("INVALID_FRAME", "Expected a nonempty uint8 BGR image.")
        height, width = image.shape[:2]
        if min(height, width) < 2:
            raise BaselineError("INVALID_FRAME", "Frame is empty or too small.")
        scale = min(1.0, self.config.detector_max_size / max(height, width))
        resized_width, resized_height = max(2, round(width * scale)), max(2, round(height * scale))
        resized = (
            cv2.resize(image, (resized_width, resized_height), interpolation=cv2.INTER_AREA)
            if scale < 1
            else image
        )
        self.detector.setInputSize((resized_width, resized_height))
        _, faces = self.detector.detect(np.ascontiguousarray(resized))
        if faces is None:
            return np.empty((0, 15), dtype=np.float32)
        faces = faces.copy()
        sx, sy = resized_width / width, resized_height / height
        faces[:, [0, 2]] /= sx
        faces[:, [1, 3]] /= sy
        faces[:, 4:14:2] /= sx
        faces[:, 5:14:2] /= sy
        return faces

    def _quality_and_align(self, image: np.ndarray, row: np.ndarray):
        config = self.config
        metrics = {"detection_score": float(row[14])}
        reasons = []
        if not np.isfinite(row).all():
            return Quality(False, ("invalid_landmarks",), {}), None
        x, y, width, height = map(float, row[:4])
        metrics["face_size"] = min(width, height)
        if min(width, height) < config.min_face_size:
            reasons.append("face_too_small")
        area = max(width * height, 1)
        visible_width = max(0, min(image.shape[1], x + width) - max(0, x))
        visible_height = max(0, min(image.shape[0], y + height) - max(0, y))
        metrics["visible_fraction"] = visible_width * visible_height / area
        if metrics["visible_fraction"] < config.min_visible_fraction:
            reasons.append("face_clipped")
        landmarks = row[4:14].reshape(5, 2)
        eye_delta = landmarks[1] - landmarks[0]
        eye_distance = float(np.linalg.norm(eye_delta))
        metrics["eye_distance"] = eye_distance
        if eye_distance < config.min_eye_distance:
            reasons.append("eyes_too_close")
        metrics["roll_degrees"] = math.degrees(
            math.atan2(abs(float(eye_delta[1])), abs(float(eye_delta[0])))
        )
        if metrics["roll_degrees"] > config.max_roll_degrees:
            reasons.append("face_tilted")
        metrics["nose_offset_ratio"] = abs(float(landmarks[2, 0] - landmarks[:2, 0].mean())) / max(
            eye_distance, 1
        )
        if metrics["nose_offset_ratio"] > config.max_nose_offset:
            reasons.append("face_turned_too_far")
        if reasons:
            return Quality(False, tuple(reasons), metrics), None
        aligned = self.recognizer.alignCrop(image, row)
        gray = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
        metrics["brightness"] = float(gray.mean())
        metrics["sharpness"] = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if metrics["brightness"] < config.min_brightness:
            reasons.append("too_dark")
        if metrics["brightness"] > config.max_brightness:
            reasons.append("too_bright")
        if metrics["sharpness"] < config.min_sharpness:
            reasons.append("too_blurry")
        return Quality(not reasons, tuple(reasons), metrics), aligned

    def extract(self, image: np.ndarray):
        detections = []
        for row in self._detect(image):
            quality, aligned = self._quality_and_align(image, row)
            sample = None
            if quality.accepted:
                embedding = unit_vector(self.recognizer.feature(aligned).copy())
                sample = Sample(
                    embedding,
                    self.model_id,
                    self.preprocessing_version,
                    hashlib.sha256(image.tobytes()).hexdigest(),
                    quality,
                )
            face = Face(
                tuple(map(float, row[:4])),
                row[4:14].reshape(5, 2).tolist(),
                quality,
                Match("unmatched" if sample else "low_quality"),
                state="unmatched" if sample else "low_quality",
            )
            detections.append(Detection(face, sample))
        return detections

    def make_sample(self, image: np.ndarray):
        detections = self.extract(image)
        if not detections:
            raise BaselineError("SAMPLE_NO_FACE", "No face detected. Look toward the camera.")
        if len(detections) != 1:
            raise BaselineError(
                "SAMPLE_MULTIPLE_FACES", "Keep exactly one person in frame for registration."
            )
        detection = detections[0]
        if detection.sample is None:
            raise BaselineError("SAMPLE_LOW_QUALITY", ", ".join(detection.face.quality.reasons))
        return detection.sample

    def analyze(self, image: np.ndarray, gallery: Gallery):
        detections = self.extract(image)
        for detection in detections:
            if detection.sample:
                detection.face.match = match_embedding(
                    detection.sample.embedding, gallery, self.config
                )
                detection.face.state = detection.face.match.decision
        return [detection.face for detection in detections]
