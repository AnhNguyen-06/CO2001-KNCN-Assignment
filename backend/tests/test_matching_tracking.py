from dataclasses import replace

import numpy as np
import pytest

from presence_cv.config import Config
from presence_cv.tracking import TemporalTracker
from presence_cv.types import Face, Gallery, Match, Quality
from presence_cv.vision import match_embedding


def face(person_id="A", bbox=(20, 20, 100, 100), decision="candidate"):
    return Face(bbox, [], Quality(True, (), {}), Match(decision, person_id, 0.8, 0.1))


def test_match_uses_distinct_id_runner_up(config):
    probe = np.zeros(128, dtype=np.float32)
    probe[0] = 1
    a = np.stack([probe] * 3)
    b = np.roll(a, 1, axis=1)
    gallery = Gallery(1, {"A": a, "B": b}, {"A": "Alpha", "B": "Beta"})
    result = match_embedding(probe, gallery, config)
    assert result.person_id == "A" and result.runner_up_score == 0
    assert match_embedding(np.roll(probe, 2), gallery, config).decision == "unknown"


def test_ambiguous_and_empty_gallery_are_rejected(config):
    probe = np.ones(128, dtype=np.float32) / np.sqrt(128)
    gallery = Gallery(1, {"A": np.stack([probe] * 3), "B": np.stack([probe] * 3)}, {})
    assert match_embedding(probe, gallery, config).decision == "ambiguous"
    assert match_embedding(probe, Gallery(0, {}, {}), config).decision == "no_gallery"
    assert (
        match_embedding(probe, Gallery(1, {"A": np.stack([probe] * 3)}, {}), config).person_id
        == "A"
    )


def test_confirmation_requires_count_and_duration(config):
    tracker = TemporalTracker(config)
    for timestamp in (0, 0.01, 0.02):
        result = tracker.update([face()], timestamp)
        assert result[0].state == "confirming"
    assert tracker.update([face()], 0.4)[0].state == "confirmed"


@pytest.mark.parametrize("interrupt", ["missing", "unknown", "identity_changed", "time_gap"])
def test_interruptions_reset_confirmation(config, interrupt):
    tracker = TemporalTracker(config)
    tracker.update([face()], 0)
    tracker.update([face()], 0.2)
    if interrupt == "missing":
        tracker.update([], 0.3)
    elif interrupt == "unknown":
        tracker.update([face(None, decision="unknown")], 0.3)
    elif interrupt == "identity_changed":
        tracker.update([face("B")], 0.3)
    timestamp = 1.0 if interrupt == "time_gap" else 0.4
    assert tracker.update([face()], timestamp)[0].state == "confirming"


def test_two_separate_faces_confirm_independently(config):
    tracker = TemporalTracker(config)
    for timestamp in (0, 0.2, 0.4):
        result = tracker.update(
            [face("A", (0, 0, 100, 100)), face("B", (250, 0, 100, 100))], timestamp
        )
    assert [item.state for item in result] == ["confirmed", "confirmed"]
    assert len({item.track_id for item in result}) == 2


def test_crossing_or_ambiguous_association_cannot_confirm(config):
    tracker = TemporalTracker(config)
    for timestamp in (0, 0.2, 0.4, 0.6):
        result = tracker.update(
            [face("A", (0, 0, 100, 100)), face("B", (20, 0, 100, 100))], timestamp
        )
        assert all(item.state == "tracking_ambiguous" for item in result)


@pytest.mark.parametrize(
    "changes",
    [
        {"match_threshold": float("nan")},
        {"confirmation_frames": 0},
        {"detector_threshold": 2},
        {"min_brightness": 220, "max_brightness": 40},
        {"confirmation_seconds": 3},
        {"max_frame_age": 0},
        {"opencv_threads": True},
    ],
)
def test_invalid_config_fails_early(config, changes):
    with pytest.raises(ValueError):
        replace(config, **changes)


def test_config_file_is_checked(tmp_path):
    file = tmp_path / "config.json"
    file.write_text('{"typo_threshold": 1}')
    with pytest.raises(ValueError, match="Unknown"):
        Config.load(file)
