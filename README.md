<h1 align="center"><b>DS200.Q21.1 - Big Data Analysis (Lab 05)</b></h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.8+" />
  <img src="https://img.shields.io/badge/Spark%20Streaming-3.x-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white" alt="Spark Streaming" />
  <img src="https://img.shields.io/badge/YOLO-Object%20Detection-00FFFF?style=for-the-badge" alt="YOLO" />
  <img src="https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV" />
  <img src="https://img.shields.io/badge/TCP-Socket-181717?style=for-the-badge" alt="TCP Socket" />
</p>

<p align="center">
  <a href="https://github.com/awnpvng/DS200.Q21.1.LAB05"><img src="https://img.shields.io/badge/GitHub-DS200.Q21.1.LAB05-181717?style=flat-square&logo=github" alt="GitHub Repository" /></a>
</p>

**Lab folder:** `DS200.Q21.1_lab5/`

---

## Student Information

| Student ID | Full Name | GitHub |
|:----------:|-----------|--------|
| Update in submission | Update in submission | [awnpvng](https://github.com/awnpvng) |

---

## Table of Contents

1. [Objective](#objective)
2. [System Architecture](#system-architecture)
3. [Technologies](#technologies)
4. [Repository Layout](#repository-layout)
5. [Prerequisites](#prerequisites)
6. [Quick Start](#quick-start)
7. [Batch Video Processing](#batch-video-processing)
8. [Running Individual Components](#running-individual-components)
9. [Utility Scripts](#utility-scripts)
10. [Output Format](#output-format)
11. [Configuration](#configuration)
12. [Screenshots](#screenshots)
13. [Submission Checklist](#submission-checklist)

---

## Objective

Build a **distributed person counting system** that receives camera frames,
detects people in each frame, returns bounding boxes, and stores the processing
results. The system is organized into three independent servers and uses a Big
Data streaming context through **PySpark Structured Streaming**.

### Features

- **Server 1 - Gateway:** reads frames from video/camera and sends them through TCP.
- **Server 2 - Processing:** receives frames, detects people, assigns tracking IDs, and sends results to storage.
- **Server 3 - Storage:** receives detection results and stores JSONL logs, summaries, reports, and screenshots.
- **Big Data Streaming:** supports Spark Structured Streaming micro-batches.
- **YOLO Detection:** uses `models/yolo26n.pt` for person detection.
- **Result Management:** stores outputs by video for easy submission review.

---

## System Architecture

```text
Camera / Video
      |
      | frames
      v
+---------------------+        TCP JSONL        +-------------------------+
| Server 1: Gateway   | ----------------------> | Server 2: Processing    |
| Read frames         |                         | Spark + YOLO + Tracker  |
+---------------------+                         +-------------------------+
                                                        |
                                                        | detection results
                                                        v
                                                +-------------------------+
                                                | Server 3: Storage       |
                                                | JSONL / summary / report|
                                                +-------------------------+
                                                        |
                                                        v
                                                output/results/
```

In Spark mode, Server 1 exposes a TCP source on port `6100` and Spark consumes
the stream as micro-batches. A plain socket mode is also provided for machines
without a Java/Spark runtime.

---

## Technologies

| Technology | Purpose |
|------------|---------|
| **Python 3.8+** | Primary programming language |
| **PySpark Structured Streaming** | Big Data stream processing |
| **Ultralytics YOLO** | Person detection model |
| **OpenCV** | Image/video reading, encoding, and visualization |
| **TCP Sockets** | Inter-server communication |
| **JSONL** | Stream-friendly result storage |
| **YAML** | Centralized configuration |

---

## Repository Layout

```text
DS200.Q21.1_lab5/
├── README.md
├── requirements.txt
├── prompt.md
├── config/
│   └── settings.yaml
├── data/
│   ├── data1.mp4
│   ├── data2.mp4
│   └── data3.mp4
├── docs/
│   └── architecture.md
├── models/
│   └── yolo26n.pt
├── scripts/
│   ├── run_demo.ps1
│   ├── run_processing_plain.ps1
│   ├── run_processing_spark.ps1
│   ├── run_sender.ps1
│   └── run_storage.ps1
├── src/
│   ├── server1_gateway/
│   │   └── sender.py
│   ├── server2_processing/
│   │   ├── batch_evaluator.py
│   │   ├── detector.py
│   │   ├── dynamic_cascade.py
│   │   ├── spark_streaming.py
│   │   └── tracker.py
│   ├── server3_storage/
│   │   └── receiver_store.py
│   └── utils/
│       ├── config.py
│       ├── networking.py
│       └── visualization.py
└── output/
    ├── README.md
    ├── results/
    │   ├── overall_summary.json
    │   ├── data1/
    │   ├── data2/
    │   └── data3/
    └── screenshots/
        ├── data1/
        ├── data2/
        └── data3/
```

---

## Prerequisites

### Python Environment

```bash
python --version
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Git Bash / Linux / macOS:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Java Runtime

Spark mode requires Java. If Java is not available, use the plain socket mode or
the batch evaluator.

---

## Quick Start

### 1. Run Batch Evaluation

This command processes all videos under `data/` and writes submission-friendly
outputs.

```bash
python -m src.server2_processing.batch_evaluator --videos-dir data --frames 0 --sample-every 100
```

### 2. View Results

```bash
cat output/results/overall_summary.json
cat output/README.md
```

On Windows PowerShell:

```powershell
Get-Content output\results\overall_summary.json
Get-Content output\README.md
```

---

## Batch Video Processing

The batch evaluator is included to produce repeatable result files for GitHub
submission.

```bash
python -m src.server2_processing.batch_evaluator --videos-dir data --frames 0 --sample-every 100
```

Parameters:

| Argument | Description |
|----------|-------------|
| `--videos-dir data` | Directory containing input videos |
| `--frames 0` | Process the full video; use a positive number to limit frames |
| `--sample-every 100` | Save one annotated screenshot every 100 frames |

Output structure:

```text
output/results/
├── overall_summary.json
├── data1/
│   ├── camera_01_log.jsonl
│   ├── summary.json
│   └── report.txt
├── data2/
│   ├── camera_01_log.jsonl
│   ├── summary.json
│   └── report.txt
└── data3/
    ├── camera_01_log.jsonl
    ├── summary.json
    └── report.txt
```

---

## Running Individual Components

### Plain Socket Mode

Open three terminals.

Terminal 1:

```bash
python -m src.server3_storage.receiver_store
```

Terminal 2:

```bash
python -m src.server2_processing.spark_streaming --plain-socket
```

Terminal 3:

```bash
python -m src.server1_gateway.sender --source data/data1.mp4 --frames 120 --fps 5
```

### Spark Streaming Mode

Terminal 1:

```bash
python -m src.server3_storage.receiver_store
```

Terminal 2:

```bash
python -m src.server2_processing.spark_streaming
```

Terminal 3:

```bash
python -m src.server1_gateway.sender --serve-source --source data/data1.mp4 --frames 120 --fps 5
```

---

## Utility Scripts

PowerShell:

```powershell
.\scripts\run_demo.ps1
.\scripts\run_storage.ps1
.\scripts\run_processing_plain.ps1
.\scripts\run_processing_spark.ps1
.\scripts\run_sender.ps1
```

Git Bash / Linux / macOS:

```bash
bash scripts/run_demo.sh
bash scripts/run_storage.sh
bash scripts/run_processing_plain.sh
bash scripts/run_processing_spark.sh
bash scripts/run_sender.sh
```

---

## Output Format

### Frame Result

Each line in `camera_01_log.jsonl` represents one processed frame.

```json
{
  "frame_number": 1,
  "timestamp": "2026-06-01T09:12:13.000000+00:00",
  "person_count": 4,
  "total_unique_persons_counted": 4,
  "bounding_boxes": [
    {
      "x1": 120.5,
      "y1": 80.0,
      "x2": 190.5,
      "y2": 260.0,
      "width": 70.0,
      "height": 180.0,
      "confidence": 0.91,
      "class_id": 0,
      "source": "global",
      "track_id": 1
    }
  ]
}
```

### Per-Video Summary

```json
{
  "source": "data/data1.mp4",
  "frames_processed": 1038,
  "max_persons_in_frame": 8,
  "avg_persons_per_frame": 3.85,
  "total_unique_persons_counted": 47,
  "processing_time_seconds": 109.66,
  "processing_fps": 9.47,
  "dynamic_cascade": true,
  "tracking_enabled": true
}
```

### Overall Summary

```json
{
  "total_videos": 3,
  "total_frames_processed": 3084,
  "total_processing_time_seconds": 446.31,
  "overall_processing_fps": 6.91
}
```

---

## Configuration

Main configuration file:

```text
config/settings.yaml
```

Important settings:

| Field | Description |
|-------|-------------|
| `network_ports.server1_gateway` | Frame source port |
| `network_ports.server2_processing` | Processing server port |
| `network_ports.server3_storage` | Storage server port |
| `streaming.fps` | Sender frame rate |
| `model_weights.yolo_path` | YOLO model path |
| `cascade_parameters.*` | Detection refinement parameters |
| `tracking.*` | Tracking parameters |

---

## Screenshots

Annotated frames are stored per video:

```text
output/screenshots/
├── data1/
├── data2/
└── data3/
```

Each screenshot contains detected person bounding boxes, confidence values, and
tracking IDs.

---

## Submission Checklist

- [x] Source code committed under `src/`
- [x] Three-server architecture implemented
- [x] Big Data streaming context included through PySpark
- [x] Person detection model configured
- [x] Bounding boxes returned for detected persons
- [x] Result storage implemented
- [x] Output files generated under `output/`
- [x] GitHub repository prepared for submission

---

## License

This project is developed for educational purposes as part of DS200.Q21.1 Big
Data Analysis Lab 05.
