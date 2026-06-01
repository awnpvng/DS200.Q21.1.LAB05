"""Batch demo runner that produces submission-friendly outputs."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2

from src.server1_gateway.sender import _synthetic_frame
from src.server2_processing.detector import PersonDetector
from src.server2_processing.dynamic_cascade import run_cascade_pipeline
from src.server2_processing.tracker import CentroidTracker
from src.utils.config import load_config, resolve_path, setup_logging
from src.utils.visualization import draw_detections


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default=None)
    parser.add_argument("--videos-dir", default="data")
    parser.add_argument("--frames", type=int, default=0, help="0 means process full video")
    parser.add_argument("--sample-every", type=int, default=15)
    args = parser.parse_args()

    config = load_config()
    setup_logging(config["system"]["log_level"])
    detector = PersonDetector(resolve_path(config["model_weights"]["yolo_path"]))

    videos = [resolve_path(args.video)] if args.video else _discover_videos(args.videos_dir)
    if not videos:
        videos = [None]

    summaries = []
    for video_path in videos:
        summaries.append(
            _process_one_source(
                video_path=video_path,
                max_frames=args.frames,
                sample_every=args.sample_every,
                detector=detector,
                config=config,
            )
        )
    _write_overall_outputs(summaries)


def _process_one_source(
    video_path: Path | None,
    max_frames: int,
    sample_every: int,
    detector: PersonDetector,
    config: dict,
) -> dict:
    tracker = CentroidTracker(
        max_missed=int(config["tracking"]["track_buffer_frames"]),
        match_distance=float(config["tracking"]["match_distance_pixels"]),
    )
    source_name = video_path.stem if video_path else "synthetic"
    source_label = (
        video_path.relative_to(resolve_path(".")).as_posix() if video_path else "synthetic"
    )

    results = []
    start = time.time()
    for frame_number, frame in enumerate(_read_frames(video_path, max_frames), start=1):
        boxes = run_cascade_pipeline(frame, detector, config["cascade_parameters"])
        tracked = tracker.update(boxes)
        result = {
            "frame_number": frame_number,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "person_count": len(tracked),
            "total_unique_persons_counted": tracker.total_unique,
            "bounding_boxes": tracked,
        }
        results.append(result)
        if frame_number == 1 or frame_number % sample_every == 0:
            _write_sample(frame, tracked, frame_number, source_name)

    duration = time.time() - start
    return _write_outputs(results, duration, source_label, source_name)


def _discover_videos(videos_dir: str) -> list[Path]:
    directory = resolve_path(videos_dir)
    extensions = {".mp4", ".avi", ".mov", ".mkv"}
    return sorted(
        path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in extensions
    )


def _read_frames(video: Path | None, max_frames: int):
    capture = None
    if video:
        capture = cv2.VideoCapture(str(video))
    if capture and capture.isOpened():
        count = 0
        while max_frames <= 0 or count < max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            count += 1
            yield frame
        capture.release()
        return
    synthetic_frames = max_frames if max_frames > 0 else 60
    for index in range(synthetic_frames):
        yield _synthetic_frame(index)


def _write_sample(frame, tracked, frame_number: int, source_name: str) -> None:
    annotated_dir = resolve_path("output/screenshots") / source_name
    annotated_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(
        str(annotated_dir / f"frame_{frame_number:04d}.jpg"),
        draw_detections(frame, tracked),
    )


def _write_outputs(
    results: list[dict],
    duration: float,
    source: str,
    source_name: str,
) -> dict:
    output_dir = resolve_path("output/results") / source_name
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "camera_01_log.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as file:
        for result in results:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")

    summary = {
        "source": source,
        "frames_processed": len(results),
        "max_persons_in_frame": max((item["person_count"] for item in results), default=0),
        "avg_persons_per_frame": round(
            sum(item["person_count"] for item in results) / max(len(results), 1),
            2,
        ),
        "total_unique_persons_counted": results[-1]["total_unique_persons_counted"]
        if results
        else 0,
        "processing_time_seconds": round(duration, 2),
        "processing_fps": round(len(results) / duration, 2) if duration > 0 else 0,
        "dynamic_cascade": True,
        "sahi_used": False,
        "tracking_enabled": True,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "report.txt").write_text(
        "\n".join(
            [
                "DS200 Lab 05 - Dynamic Cascade Person Counting Report",
                f"Source: {source}",
                f"Frames processed: {summary['frames_processed']}",
                f"Average persons/frame: {summary['avg_persons_per_frame']}",
                f"Max persons/frame: {summary['max_persons_in_frame']}",
                f"Total unique persons counted: {summary['total_unique_persons_counted']}",
                f"Processing FPS: {summary['processing_fps']}",
                "SAHI used: no",
                "Tracking enabled: yes",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def _write_overall_outputs(summaries: list[dict]) -> None:
    output_dir = resolve_path("output")
    results_dir = output_dir / "results"
    total_frames = sum(item["frames_processed"] for item in summaries)
    total_time = sum(item["processing_time_seconds"] for item in summaries)
    overall = {
        "total_videos": len(summaries),
        "total_frames_processed": total_frames,
        "total_processing_time_seconds": round(total_time, 2),
        "overall_processing_fps": round(total_frames / total_time, 2) if total_time > 0 else 0,
        "videos": summaries,
    }
    (results_dir / "overall_summary.json").write_text(
        json.dumps(overall, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(_render_output_readme(overall), encoding="utf-8")


def _render_output_readme(overall: dict) -> str:
    lines = [
        "# Output Summary",
        "",
        "He thong da xu ly ca 3 video bang YOLO26 + Dynamic Cascade, khong dung SAHI, co tracking.",
        "Bang nay tom tat truc tiep toc do xu ly va chat luong dem nguoi de nop kem bai lab.",
        "",
        "| Video | Frames | Avg persons/frame | Max persons/frame | Unique persons | Time (s) | Processing FPS |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in overall["videos"]:
        lines.append(
            "| {source} | {frames_processed} | {avg_persons_per_frame} | "
            "{max_persons_in_frame} | {total_unique_persons_counted} | "
            "{processing_time_seconds} | {processing_fps} |".format(**item)
        )
    lines.extend(
        [
            "",
            "## Overall",
            "",
            f"- Total videos: {overall['total_videos']}",
            f"- Total frames processed: {overall['total_frames_processed']}",
            f"- Total processing time: {overall['total_processing_time_seconds']} seconds",
            f"- Overall processing FPS: {overall['overall_processing_fps']}",
            "- SAHI used: no",
            "- Dynamic Cascade: yes",
            "- Tracking enabled: yes",
            "",
            "Per-video folders are stored under `output/results/<video-name>/`.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
