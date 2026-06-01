"""Lightweight centroid tracker for unique person counting."""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.server2_processing.detector import Detection


@dataclass
class Track:
    track_id: int
    center: tuple[float, float]
    missed_frames: int = 0


class CentroidTracker:
    """Assign stable IDs to detections using nearest-centroid matching."""

    def __init__(self, max_missed: int = 30, match_distance: float = 80) -> None:
        self.max_missed = max_missed
        self.match_distance = match_distance
        self.next_track_id = 1
        self.tracks: dict[int, Track] = {}
        self.seen_ids: set[int] = set()

    def update(self, detections: list[Detection]) -> list[dict[str, object]]:
        assigned_tracks: set[int] = set()
        assigned_detections: set[int] = set()
        outputs: list[dict[str, object]] = []

        for det_index, detection in enumerate(detections):
            best_id = None
            best_distance = self.match_distance
            for track_id, track in self.tracks.items():
                if track_id in assigned_tracks:
                    continue
                distance = _distance(track.center, detection.center)
                if distance < best_distance:
                    best_distance = distance
                    best_id = track_id
            if best_id is None:
                best_id = self._create_track(detection.center)
            else:
                self.tracks[best_id].center = detection.center
                self.tracks[best_id].missed_frames = 0
            assigned_tracks.add(best_id)
            assigned_detections.add(det_index)
            item = detection.to_dict()
            item["track_id"] = best_id
            outputs.append(item)

        for track_id, track in list(self.tracks.items()):
            if track_id not in assigned_tracks:
                track.missed_frames += 1
                if track.missed_frames > self.max_missed:
                    del self.tracks[track_id]

        return outputs

    @property
    def total_unique(self) -> int:
        return len(self.seen_ids)

    def _create_track(self, center: tuple[float, float]) -> int:
        track_id = self.next_track_id
        self.next_track_id += 1
        self.tracks[track_id] = Track(track_id=track_id, center=center)
        self.seen_ids.add(track_id)
        return track_id


def _distance(left: tuple[float, float], right: tuple[float, float]) -> float:
    return math.hypot(left[0] - right[0], left[1] - right[1])
