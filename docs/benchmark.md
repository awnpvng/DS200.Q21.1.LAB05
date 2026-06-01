# Benchmark Rationale

The benchmark project uses SAHI to improve detection of small persons by slicing
each frame into overlapping tiles. This project intentionally avoids SAHI and
uses a different design:

| Aspect | Benchmark SAHI Design | This Project |
|---|---|---|
| Small-object strategy | Fixed-grid slicing | Adaptive crop refinement |
| Extra inference cost | Many tiles per frame | Only suspicious regions |
| Tracking | Not included | Centroid tracking |
| Output | Per-frame count | Per-frame count and total unique persons |
| Big Data layer | PySpark included | Spark Structured Streaming pipeline |

The main claim is not that Dynamic Cascade is always more accurate than SAHI.
The claim is that it is a reasonable architecture for real-time streams because
it spends extra inference only where the global detector is uncertain.
