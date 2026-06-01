# Architecture

This project implements the DS200 Lab 05 person counting system as three
independent services.

```text
Camera/Video
    |
    | JSONL over TCP, base64 JPEG frames
    v
Server 1 - Gateway
    |
    v
Server 2 - Processing
    | Spark Structured Streaming micro-batches
    | YOLO26 detector
    | Dynamic Cascade adaptive crop refinement
    | Lightweight centroid tracking
    v
Server 3 - Storage
    |
    v
output/results/*.jsonl, summary.json, report.txt
```

The Big Data context is represented by Spark Structured Streaming. In Spark
mode, Server 1 exposes a TCP frame source on port 6100 and Spark consumes it as
micro-batches. In plain demo mode, Server 1 connects directly to Server 2 on
port 6200 so the same code can run on machines without Java/Spark.

Unlike SAHI, Dynamic Cascade does not slice every frame into a fixed grid. It
first runs a global pass, then selectively crops regions with low confidence or
dense local clusters. Those crops are upscaled, processed again, and mapped back
to the original coordinate system.
