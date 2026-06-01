"""Frame annotation helpers."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np


def draw_detections(frame: np.ndarray, detections: list[dict[str, Any]]) -> np.ndarray:
    """Draw bounding boxes and track IDs on a copy of the frame."""
    annotated = frame.copy()
    for detection in detections:
        x1 = int(detection["x1"])
        y1 = int(detection["y1"])
        x2 = int(detection["x2"])
        y2 = int(detection["y2"])
        source = detection.get("source", "global")
        color = (0, 180, 0) if source == "global" else (0, 180, 255)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label = f"ID {detection.get('track_id', '-')}: {detection['confidence']:.2f}"
        cv2.putText(
            annotated,
            label,
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )
    return annotated
