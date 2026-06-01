"""Server 2: Spark Streaming processing server."""

from __future__ import annotations

import argparse
import json
import logging
import socket
from datetime import datetime, timezone
from typing import Any

from src.server2_processing.detector import PersonDetector
from src.server2_processing.dynamic_cascade import run_cascade_pipeline
from src.server2_processing.tracker import CentroidTracker
from src.utils.config import load_config, resolve_path, setup_logging
from src.utils.networking import decode_base64_to_frame, iter_json_lines, send_json_line

LOGGER = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plain-socket", action="store_true", help="Run without Spark")
    args = parser.parse_args()
    if args.plain_socket:
        run_plain_socket_server()
    else:
        run_spark_streaming()


def run_plain_socket_server() -> None:
    """Run a lightweight socket server useful on machines without Java/Spark."""
    config = load_config()
    setup_logging(config["system"]["log_level"])
    host = config["system"]["host"]
    source_port = int(config["network_ports"]["server1_gateway"])
    storage_port = int(config["network_ports"]["server3_storage"])
    detector = PersonDetector(resolve_path(config["model_weights"]["yolo_path"]))
    tracker = CentroidTracker(
        max_missed=int(config["tracking"]["track_buffer_frames"]),
        match_distance=float(config["tracking"]["match_distance_pixels"]),
    )

    LOGGER.info("Processing server listening on %s:%s", host, listen_port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, listen_port))
        server.listen(1)
        conn, _ = server.accept()
        with conn, socket.create_connection((host, storage_port), timeout=10) as storage:
            for payload in iter_json_lines(conn):
                result = process_frame_payload(payload, detector, tracker, config)
                send_json_line(storage, result)
                LOGGER.info("Processed frame %s", result["frame_number"])


def run_spark_streaming() -> None:
    """Run Spark Structured Streaming over newline-delimited TCP frames."""
    from pyspark.sql import SparkSession

    config = load_config()
    setup_logging(config["system"]["log_level"])
    host = config["system"]["host"]
    listen_port = int(config["network_ports"]["server2_processing"])
    storage_port = int(config["network_ports"]["server3_storage"])

    spark = (
        SparkSession.builder.appName(config["spark"]["app_name"])
        .master(config["spark"]["master"])
        .getOrCreate()
    )
    stream = (
        spark.readStream.format("socket")
        .option("host", host)
        .option("port", source_port)
        .load()
    )

    detector = PersonDetector(resolve_path(config["model_weights"]["yolo_path"]))
    tracker = CentroidTracker(
        max_missed=int(config["tracking"]["track_buffer_frames"]),
        match_distance=float(config["tracking"]["match_distance_pixels"]),
    )

    def foreach_batch(batch_df, batch_id: int) -> None:
        rows = batch_df.collect()
        if not rows:
            return
        with socket.create_connection((host, storage_port), timeout=10) as storage:
            for row in rows:
                payload = json.loads(row["value"])
                result = process_frame_payload(payload, detector, tracker, config)
                result["spark_batch_id"] = batch_id
                send_json_line(storage, result)

    query = (
        stream.writeStream.foreachBatch(foreach_batch)
        .option("checkpointLocation", str(resolve_path(config["spark"]["checkpoint_dir"])))
        .start()
    )
    query.awaitTermination()


def process_frame_payload(
    payload: dict[str, Any],
    detector: PersonDetector,
    tracker: CentroidTracker,
    config: dict[str, Any],
) -> dict[str, Any]:
    frame = decode_base64_to_frame(payload["data"])
    boxes = run_cascade_pipeline(frame, detector, config["cascade_parameters"])
    tracked = tracker.update(boxes)
    return {
        "type": "detection_result",
        "camera_id": payload.get("camera_id", config["system"]["camera_id"]),
        "frame_id": payload["frame_id"],
        "frame_number": payload["frame_number"],
        "source_timestamp": payload["timestamp"],
        "processed_timestamp": datetime.now(timezone.utc).isoformat(),
        "person_count": len(tracked),
        "total_unique_persons_counted": tracker.total_unique,
        "bounding_boxes": tracked,
    }


if __name__ == "__main__":
    main()
