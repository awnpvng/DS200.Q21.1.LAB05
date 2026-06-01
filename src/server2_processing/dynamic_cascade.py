"""Dynamic Cascade inference without SAHI fixed-grid slicing."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

import cv2
import numpy as np

from src.server2_processing.detector import Detection, PersonDetector


def run_cascade_pipeline(
    frame: np.ndarray,
    detector: PersonDetector,
    params: dict[str, Any],
) -> list[Detection]:
    """Run global detection, refine suspicious regions, and merge boxes."""
    global_boxes = detector.predict(
        frame,
        conf=float(params["global_conf_threshold"]),
        source="global",
    )
    regions = _build_refinement_regions(frame, global_boxes, params)
    refined_boxes: list[Detection] = []

    for region in regions:
        x1, y1, x2, y2 = region
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        scale = float(params.get("local_upscale_factor", 1.5))
        enlarged = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        local_boxes = detector.predict(
            enlarged,
            conf=float(params["local_conf_threshold"]),
            source="cascade",
        )
        for box in local_boxes:
            # The local detector sees the upscaled crop. Divide by the scale and
            # add crop origin to map the coordinates back to the original frame.
            refined_boxes.append(
                Detection(
                    x1=x1 + box.x1 / scale,
                    y1=y1 + box.y1 / scale,
                    x2=x1 + box.x2 / scale,
                    y2=y1 + box.y2 / scale,
                    confidence=box.confidence,
                    class_id=box.class_id,
                    source="cascade",
                )
            )

    merged = _merge_by_center_distance(
        global_boxes + refined_boxes,
        float(params["duplicate_center_distance"]),
    )
    return sorted(merged, key=lambda item: item.confidence, reverse=True)


def _build_refinement_regions(
    frame: np.ndarray,
    boxes: list[Detection],
    params: dict[str, Any],
) -> list[tuple[int, int, int, int]]:
    height, width = frame.shape[:2]
    suspicious = [
        box
        for box in boxes
        if box.confidence < float(params["cascade_trigger_threshold"])
    ]
    suspicious.extend(_dense_cluster_boxes(boxes, params))
    return _boxes_to_regions(suspicious, width, height, int(params["padding_pixels"]))


def _dense_cluster_boxes(
    boxes: list[Detection],
    params: dict[str, Any],
) -> list[Detection]:
    limit = int(params["density_trigger_limit"])
    if len(boxes) <= limit:
        return []
    distance_limit = float(params["min_cluster_center_distance"])
    dense: list[Detection] = []
    for box in boxes:
        close_count = 0
        for other in boxes:
            if _center_distance(box, other) <= distance_limit:
                close_count += 1
        if close_count > limit:
            dense.append(box)
    return dense


def _boxes_to_regions(
    boxes: list[Detection],
    width: int,
    height: int,
    padding: int,
) -> list[tuple[int, int, int, int]]:
    regions: list[tuple[int, int, int, int]] = []
    for box in boxes:
        regions.append(
            (
                max(0, int(box.x1) - padding),
                max(0, int(box.y1) - padding),
                min(width, int(box.x2) + padding),
                min(height, int(box.y2) + padding),
            )
        )
    return _merge_regions(regions)


def _merge_regions(regions: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    merged: list[tuple[int, int, int, int]] = []
    for region in regions:
        current = region
        changed = True
        while changed:
            changed = False
            remaining: list[tuple[int, int, int, int]] = []
            for other in merged:
                if _intersects(current, other):
                    current = (
                        min(current[0], other[0]),
                        min(current[1], other[1]),
                        max(current[2], other[2]),
                        max(current[3], other[3]),
                    )
                    changed = True
                else:
                    remaining.append(other)
            merged = remaining
        merged.append(current)
    return merged


def _merge_by_center_distance(
    boxes: list[Detection],
    distance_threshold: float,
) -> list[Detection]:
    kept: list[Detection] = []
    for box in sorted(boxes, key=lambda item: item.confidence, reverse=True):
        duplicate_index = None
        for index, other in enumerate(kept):
            if _center_distance(box, other) <= distance_threshold:
                duplicate_index = index
                break
        if duplicate_index is None:
            kept.append(box)
        elif box.source == "cascade" and box.confidence >= kept[duplicate_index].confidence:
            kept[duplicate_index] = replace(box)
    return kept


def _center_distance(left: Detection, right: Detection) -> float:
    lx, ly = left.center
    rx, ry = right.center
    return math.hypot(lx - rx, ly - ry)


def _intersects(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
) -> bool:
    return not (
        left[2] < right[0]
        or right[2] < left[0]
        or left[3] < right[1]
        or right[3] < left[1]
    )
