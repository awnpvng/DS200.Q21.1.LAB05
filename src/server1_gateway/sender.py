"""Server 1: read camera/video frames and stream them to Server 2."""

from __future__ import annotations

import argparse
import logging
import socket
import time
import uuid
from datetime import datetime, timezone

import cv2
import numpy as np

from src.utils.config import load_config, resolve_path, setup_logging
from src.utils.networking import encode_frame_to_base64, send_json_line

LOGGER = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=None, help="Video path or webcam index")
    parser.add_argument("--frames", type=int, default=None)
    parser.add_argument("--fps", type=float, default=None)
    parser.add_argument(
        "--serve-source",
        action="store_true",
        help="Listen on server1_gateway port for Spark socket source",
    )
    args = parser.parse_args()

    config = load_config()
    setup_logging(config["system"]["log_level"])
    host = config["system"]["host"]
    port = int(config["network_ports"]["server1_gateway"])
    processing_port = int(config["network_ports"]["server2_processing"])
    fps = args.fps or float(config["streaming"]["fps"])
    max_frames = args.frames or int(config["streaming"]["max_frames"])
    source = args.source or config["streaming"]["source"]

    if args.serve_source:
        LOGGER.info("Serving frame source for Spark at %s:%s", host, port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((host, port))
            server.listen(1)
            sock, _ = server.accept()
            with sock:
                _send_frames(sock, source, max_frames, fps, config)
        return

    LOGGER.info("Connecting to processing server at %s:%s", host, processing_port)
    with socket.create_connection((host, processing_port), timeout=10) as sock:
        _send_frames(sock, source, max_frames, fps, config)


def _send_frames(
    sock: socket.socket,
    source: str,
    max_frames: int,
    fps: float,
    config: dict,
) -> None:
        for frame_number, frame in enumerate(_frame_stream(source, max_frames), start=1):
            payload = {
                "type": "frame",
                "frame_id": str(uuid.uuid4()),
                "camera_id": config["system"]["camera_id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "frame_number": frame_number,
                "data": encode_frame_to_base64(frame),
            }
            send_json_line(sock, payload)
            LOGGER.info("Sent frame %s", frame_number)
            time.sleep(1 / fps)


def _frame_stream(source: str, max_frames: int):
    capture = None
    if str(source).isdigit():
        capture = cv2.VideoCapture(int(source))
    else:
        path = resolve_path(source)
        if path.exists():
            capture = cv2.VideoCapture(str(path))

    if capture and capture.isOpened():
        count = 0
        while count < max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            count += 1
            yield frame
        capture.release()
        return

    LOGGER.warning("Video/camera unavailable; generating synthetic frames")
    for index in range(max_frames):
        yield _synthetic_frame(index)


def _synthetic_frame(index: int) -> np.ndarray:
    frame = np.zeros((480, 720, 3), dtype=np.uint8)
    frame[:] = (28, 32, 38)
    for person in range(4):
        x = 80 + person * 145 + (index * (person + 1) * 3) % 60
        y = 160 + (person % 2) * 40
        cv2.circle(frame, (x + 25, y - 35), 22, (210, 210, 210), -1)
        cv2.rectangle(frame, (x, y), (x + 50, y + 150), (80, 180, 230), -1)
    return frame


if __name__ == "__main__":
    main()
