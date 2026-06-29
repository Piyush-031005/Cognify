# Cognify v3.0 Performance Benchmark Results

Generated on: 2026-06-29T17:28:34.366564
Git Commit: 844d6e3
Release Tag: v3.0.0-rc1

---

## 1. System Footprint
- **Database File Size**: 2.99 MB (3133440 bytes)
- **Active Process Memory (RSS)**: 174.88 MB (183373824 bytes)

## 2. Event Processing Throughput
- **Total Events in Append-Only Ledger**: 0
- **Chronological Replay Duration (SAFE Mode)**: 0.01 seconds
- **Replay Throughput**: 0.0 events/second

## 3. REST API Query Latency (Measured over 50 requests)
| Endpoint | Average Latency (ms) | Min Latency (ms) | Max Latency (ms) |
|---|---|---|---|
| `/health` | 3.239 ms | 1.996 ms | 8.31 ms |
| `/metrics` | 3.577 ms | 1.999 ms | 5.455 ms |
