<h1 align="center"><b>DS200.Q21.1 - Lab 05 Output Summary</b></h1>

<p align="center">
  <img src="https://img.shields.io/badge/Videos-3-3776AB?style=for-the-badge" alt="Videos" />
  <img src="https://img.shields.io/badge/Frames-3084-E25A1C?style=for-the-badge" alt="Frames" />
  <img src="https://img.shields.io/badge/YOLO-Detection-00FFFF?style=for-the-badge" alt="YOLO Detection" />
  <img src="https://img.shields.io/badge/Tracking-Enabled-181717?style=for-the-badge" alt="Tracking Enabled" />
</p>

**Output folder:** `output/`

---

## Table of Contents

1. [Objective](#objective)
2. [Result Overview](#result-overview)
3. [Output Layout](#output-layout)
4. [Per-Video Results](#per-video-results)
5. [Overall Summary](#overall-summary)
6. [Result Files](#result-files)
7. [Screenshots](#screenshots)

---

## Objective

This folder stores the returned results of the distributed person counting
system. Each processed video has its own result directory containing frame-level
bounding boxes, a summary file, and a short report. The folder also contains an
overall summary table for quick review.

---

## Result Overview

| Video | Frames | Avg persons/frame | Max persons/frame | Unique persons | Time (s) | Processing FPS |
|-------|-------:|------------------:|------------------:|---------------:|---------:|---------------:|
| `data/data1.mp4` | 1038 | 3.85 | 8 | 47 | 109.66 | 9.47 |
| `data/data2.mp4` | 1008 | 5.73 | 11 | 70 | 179.84 | 5.60 |
| `data/data3.mp4` | 1038 | 3.85 | 8 | 47 | 156.81 | 6.62 |

---

## Output Layout

```text
output/
├── README.md
├── results/
│   ├── overall_summary.json
│   ├── data1/
│   │   ├── camera_01_log.jsonl
│   │   ├── summary.json
│   │   └── report.txt
│   ├── data2/
│   │   ├── camera_01_log.jsonl
│   │   ├── summary.json
│   │   └── report.txt
│   └── data3/
│       ├── camera_01_log.jsonl
│       ├── summary.json
│       └── report.txt
└── screenshots/
    ├── data1/
    ├── data2/
    └── data3/
```

---

## Per-Video Results

### data1.mp4

| Metric | Value |
|--------|------:|
| Frames processed | 1038 |
| Average persons per frame | 3.85 |
| Maximum persons in one frame | 8 |
| Total unique persons counted | 47 |
| Processing time | 109.66 seconds |
| Processing FPS | 9.47 |

### data2.mp4

| Metric | Value |
|--------|------:|
| Frames processed | 1008 |
| Average persons per frame | 5.73 |
| Maximum persons in one frame | 11 |
| Total unique persons counted | 70 |
| Processing time | 179.84 seconds |
| Processing FPS | 5.60 |

### data3.mp4

| Metric | Value |
|--------|------:|
| Frames processed | 1038 |
| Average persons per frame | 3.85 |
| Maximum persons in one frame | 8 |
| Total unique persons counted | 47 |
| Processing time | 156.81 seconds |
| Processing FPS | 6.62 |

---

## Overall Summary

| Metric | Value |
|--------|------:|
| Total videos | 3 |
| Total frames processed | 3084 |
| Total processing time | 446.31 seconds |
| Overall processing FPS | 6.91 |

The result shows that the system can process thousands of video frames while
preserving frame-level bounding boxes and per-video summaries for submission.

---

## Result Files

| File | Description |
|------|-------------|
| `results/overall_summary.json` | Combined summary of all processed videos |
| `results/<video>/camera_01_log.jsonl` | Frame-level JSONL detection log |
| `results/<video>/summary.json` | Per-video processing summary |
| `results/<video>/report.txt` | Human-readable per-video report |

Example frame-level record:

```json
{
  "frame_number": 1,
  "person_count": 4,
  "total_unique_persons_counted": 4,
  "bounding_boxes": [
    {
      "x1": 120.5,
      "y1": 80.0,
      "x2": 190.5,
      "y2": 260.0,
      "confidence": 0.91,
      "track_id": 1
    }
  ]
}
```

---

## Screenshots

Annotated screenshots are stored under:

```text
output/screenshots/
├── data1/
├── data2/
└── data3/
```

The screenshots provide visual evidence of the detected person bounding boxes
and tracking IDs produced by the processing server.
