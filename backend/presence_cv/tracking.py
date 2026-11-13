from collections import deque
from dataclasses import dataclass, field

from .config import Config
from .types import Face


def iou(first, second):
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    intersection = max(0, min(ax + aw, bx + bw) - max(ax, bx)) * max(
        0, min(ay + ah, by + bh) - max(ay, by)
    )
    union = aw * ah + bw * bh - intersection
    return intersection / union if union > 0 else 0.0


@dataclass
class Track:
    track_id: int
    bbox: tuple[float, float, float, float]
    person_id: str | None = None
    observations: deque[float] = field(default_factory=deque)
    last_seen: float = 0
    confirmed: bool = False

    def reset_identity(self):
        self.person_id = None
        self.observations.clear()
        self.confirmed = False


class TemporalTracker:
    def __init__(self, config: Config):
        self.config = config
        self.tracks: dict[int, Track] = {}
        self.next_id = 1
        self.last_timestamp: float | None = None

    def reset(self):
        self.tracks.clear()
        self.last_timestamp = None

    def update(self, faces: list[Face], timestamp: float):
        if self.last_timestamp is not None and timestamp <= self.last_timestamp:
            self.reset()
        self.last_timestamp = timestamp
        config = self.config
        # Losing a face in even one processed frame resets confirmation evidence.
        old = {
            key: track
            for key, track in self.tracks.items()
            if 0 < timestamp - track.last_seen <= config.max_observation_gap
        }
        candidates = {
            index: [
                key
                for key, track in old.items()
                if iou(face.bbox, track.bbox) >= config.track_iou_threshold
            ]
            for index, face in enumerate(faces)
        }
        ambiguous = {index for index, choices in candidates.items() if len(choices) > 1}
        for key in old:
            linked = [index for index, choices in candidates.items() if key in choices]
            if len(linked) > 1:
                ambiguous.update(linked)
        for first, face in enumerate(faces):
            for second in range(first + 1, len(faces)):
                if iou(face.bbox, faces[second].bbox) >= config.overlap_reset_threshold:
                    ambiguous.update((first, second))

        updated = {}
        for index, face in enumerate(faces):
            choices = candidates[index]
            if len(choices) == 1 and index not in ambiguous:
                track = old[choices[0]]
            else:
                track = Track(self.next_id, face.bbox)
                self.next_id += 1
            track.bbox = face.bbox
            track.last_seen = timestamp
            face.track_id = track.track_id
            updated[track.track_id] = track
            if index in ambiguous:
                track.reset_identity()
                face.state = "tracking_ambiguous"
                continue
            if face.match.decision != "candidate":
                track.reset_identity()
                face.state = face.match.decision
                continue
            if track.person_id != face.match.person_id:
                track.reset_identity()
                track.person_id = face.match.person_id
            track.observations.append(timestamp)
            while (
                track.observations
                and timestamp - track.observations[0] > config.confirmation_window
            ):
                track.observations.popleft()
            if (
                len(track.observations) >= config.confirmation_frames
                and timestamp - track.observations[0] >= config.confirmation_seconds
            ):
                track.confirmed = True
            face.state = "confirmed" if track.confirmed else "confirming"
        self.tracks = updated
        return faces
