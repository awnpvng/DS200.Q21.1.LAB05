"""Server 3: receive detection results, append JSONL, and print dashboard."""

from __future__ import annotations

import argparse
import json
import logging
import socket
from pathlib import Path

from src.utils.config import load_config, resolve_path, setup_logging
from src.utils.networking import iter_json_lines

LOGGER = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()

    config = load_config()
    setup_logging(config["system"]["log_level"])
    host = config["system"]["host"]
    port = int(config["network_ports"]["server3_storage"])
    output_path = resolve_path(config["storage"]["result_jsonl"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Storage server listening on %s:%s", host, port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(5)
        while True:
            conn, _ = server.accept()
            with conn:
                for payload in iter_json_lines(conn):
                    append_result(output_path, payload)
                    print_dashboard(payload)


def append_result(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def print_dashboard(payload: dict) -> None:
    print(
        "[{time}] Frame {frame} | Hien tai: {current} | Tong unique: {total}".format(
            time=payload.get("processed_timestamp", "-"),
            frame=payload.get("frame_number", "-"),
            current=payload.get("person_count", 0),
            total=payload.get("total_unique_persons_counted", 0),
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
