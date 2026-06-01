"""YOLO detector wrapper with a deterministic fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

LOGGER = logging.getLogger(__name__)


@dataclass
class Detection:
    """Single person detection in xyxy format."""

    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int = 0
    source: str = "global"

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "x1": round(self.x1, 2),
            "y1": round(self.y1, 2),
            "x2": round(self.x2, 2),
            "y2": round(self.y2, 2),
            "width": round(self.x2 - self.x1, 2),
            "height": round(self.y2 - self.y1, 2),
            "confidence": round(self.confidence, 4),
            "class_id": self.class_id,
            "source": self.source,
        }


class PersonDetector:
    """Person detector using Ultralytics YOLO when available."""

    def __init__(self, model_path: str | Path, person_class_id: int = 0) -> None:
        self.model_path = Path(model_path)
        self.person_class_id = person_class_id
        self.model = None
        try:
            from ultralytics import YOLO

            if self.model_path.exists():
                self.model = YOLO(str(self.model_path))
                LOGGER.info("Loaded YOLO model from %s", self.model_path)
            else:
                LOGGER.warning("Model not found at %s; using fallback", self.model_path)
        except Exception as exc:  # pragma: no cover - depends on optional package
            LOGGER.warning("Ultralytics unavailable; using fallback detector: %s", exc)

    def predict(self, frame: np.ndarray, conf: float, source: str) -> list[Detection]:
        """Run detector and return person boxes."""
        if self.model is None:
            return self._fallback_predict(frame, source)

        result = self.model.predict(frame, conf=conf, verbose=False)[0]
        detections: list[Detection] = []
        for box in result.boxes:
            class_id = int(box.cls[0])
            if class_id != self.person_class_id:
                continue
            x1, y1, x2, y2 = [float(value) for value in box.xyxy[0]]
            detections.append(
                Detection(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    confidence=float(box.conf[0]),
                    class_id=class_id,
                    source=source,
                )
            )
        return detections

    def _fallback_predict(self, frame: np.ndarray, source: str) -> list[Detection]:
        """Simple contour-based fallback for demos without YOLO installed."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 35, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections: list[Detection] = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h < 60 or w < 20:
                continue
            detections.append(
                Detection(x, y, x + w, y + h, 0.50, self.person_class_id, source)
            )
        return detections[:12]
