# DS200.Q21.1 Lab 05 - Distributed Person Counting

This repository builds a three-server person counting system for camera/video
streams in a Big Data context.

## Highlights

- Three independent services: gateway, processing, storage.
- TCP JSONL frame streaming with base64 JPEG payloads.
- Spark Structured Streaming micro-batch processing.
- YOLO detector using `models/yolo26n.pt`.
- Dynamic Cascade inference instead of SAHI fixed-grid slicing.
- Lightweight tracking to estimate total unique persons over time.
- Submission outputs: JSONL log, summary JSON, report text, annotated frames.

## Repository Layout

```text
DS200.Q21.1_lab5/
├── config/settings.yaml
├── data/
├── docs/
│   ├── architecture.md
│   └── benchmark.md
├── models/yolo26n.pt
├── output/
│   ├── results/
│   └── screenshots/
├── scripts/
├── src/
│   ├── server1_gateway/
│   ├── server2_processing/
│   ├── server3_storage/
│   └── utils/
├── requirements.txt
└── README.md
```

## Install

```bash
pip install -r requirements.txt
```

PySpark requires Java. If Java/Spark is not available, use the plain socket
processing mode for the live demo.

## Quick Batch Demo

This generates output files and annotated screenshots without starting three
terminals.

```bash
python -m src.server2_processing.batch_evaluator --video data/data1.mp4 --frames 60
```

Outputs:

```text
output/results/camera_01_log.jsonl
output/results/summary.json
output/results/report.txt
output/screenshots/annotated/
output/screenshots/raw/
```

## Run Three Servers

Open three terminals.

Terminal 1:

```bash
python -m src.server3_storage.receiver_store
```

Terminal 2, Spark mode:

```bash
python -m src.server2_processing.spark_streaming
```

Terminal 2, fallback plain socket mode:

```bash
python -m src.server2_processing.spark_streaming --plain-socket
```

Terminal 3:

```bash
python -m src.server1_gateway.sender --source data/data1.mp4 --frames 120 --fps 5
```

For Spark mode, Server 1 must expose the socket source on port 6100:

```bash
python -m src.server1_gateway.sender --serve-source --source data/data1.mp4 --frames 120 --fps 5
```

## Output Format

Each line in `output/results/camera_01_log.jsonl` is one processed frame:

```json
{
  "type": "detection_result",
  "camera_id": "camera_01",
  "frame_number": 1,
  "person_count": 3,
  "total_unique_persons_counted": 3,
  "bounding_boxes": [
    {
      "x1": 100,
      "y1": 60,
      "x2": 150,
      "y2": 210,
      "confidence": 0.91,
      "track_id": 1,
      "source": "global"
    }
  ]
}
```

See [docs/architecture.md](docs/architecture.md) and
[docs/benchmark.md](docs/benchmark.md).

