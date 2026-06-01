"""Socket and image serialization helpers."""

from __future__ import annotations

import base64
import json
import socket
from typing import Any, Iterator

import cv2
import numpy as np


def encode_frame_to_base64(frame: np.ndarray, quality: int = 80) -> str:
    """Encode an OpenCV frame to a JPEG base64 string."""
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise ValueError("Cannot encode frame to JPEG")
    return base64.b64encode(buffer).decode("utf-8")


def decode_base64_to_frame(base64_str: str) -> np.ndarray:
    """Decode a JPEG base64 string back to an OpenCV frame."""
    raw = base64.b64decode(base64_str.encode("utf-8"))
    array = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Cannot decode base64 image")
    return frame


def send_json_line(sock: socket.socket, payload: dict[str, Any]) -> None:
    """Send one newline-delimited JSON message."""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\n"
    sock.sendall(data)


def iter_json_lines(conn: socket.socket) -> Iterator[dict[str, Any]]:
    """Yield JSON messages from a socket until the connection closes."""
    buffer = b""
    while True:
        chunk = conn.recv(65536)
        if not chunk:
            break
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            if line.strip():
                yield json.loads(line.decode("utf-8"))


def connect_with_retry(host: str, port: int, retries: int = 30) -> socket.socket:
    """Connect to a TCP server with a small retry loop."""
    import time

    last_error: OSError | None = None
    for _ in range(retries):
        try:
            return socket.create_connection((host, port), timeout=5)
        except OSError as exc:
            last_error = exc
            time.sleep(1)
    raise ConnectionError(f"Cannot connect to {host}:{port}") from last_error
