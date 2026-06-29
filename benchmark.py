"""
benchmark.py
Week 24 — Automated Performance Validation & Benchmarking.
Measures Event Replay throughput, API latency, and db foot print size.
Saves results to docs/BENCHMARK_RESULTS.md.
"""

import os
import sys
import time
import json
import sqlite3
import datetime
import psutil
import config

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import app
import event_replay

def run_benchmarks():
    print("[BENCHMARK] Starting automated performance validation...")
    results = {}

    # 1. Database Size
    db_size = 0
    if os.path.exists(config.DATABASE_URL):
        db_size = os.path.getsize(config.DATABASE_URL)
    results["database_size_bytes"] = db_size
    results["database_size_mb"] = round(db_size / (1024 * 1024), 2)
    print(f"[BENCHMARK] Database Size: {results['database_size_mb']} MB")

    # 2. Memory Consumption
    process = psutil.Process(os.getpid())
    mem_bytes = process.memory_info().rss
    results["memory_rss_bytes"] = mem_bytes
    results["memory_rss_mb"] = round(mem_bytes / (1024 * 1024), 2)
    print(f"[BENCHMARK] Memory Footprint: {results['memory_rss_mb']} MB")

    # 3. API Latency Benchmarks
    client = app.test_client()
    endpoints = ["/health", "/metrics"]
    results["api_latencies"] = {}
    
    for ep in endpoints:
        latencies = []
        for _ in range(50):
            t_start = time.time()
            resp = client.get(ep)
            elapsed = (time.time() - t_start) * 1000.0  # ms
            if resp.status_code == 200:
                latencies.append(elapsed)
        avg_lat = round(sum(latencies) / len(latencies), 3) if latencies else 0.0
        results["api_latencies"][ep] = {
            "avg_ms": avg_lat,
            "min_ms": round(min(latencies), 3) if latencies else 0.0,
            "max_ms": round(max(latencies), 3) if latencies else 0.0
        }
        print(f"[BENCHMARK] API {ep} Latency: {avg_lat} ms")

    # 4. Replay Throughput Benchmark
    # We count events present in event_store
    conn = sqlite3.connect(config.DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM event_store")
    event_count = cur.fetchone()[0] or 0
    conn.close()

    results["event_count"] = event_count
    
    # Measure replay
    t_start = time.time()
    replay_res = event_replay.replay_all_events("research_analytics_twin", mode="SAFE")
    elapsed_replay = time.time() - t_start
    
    results["replay_duration_seconds"] = round(elapsed_replay, 3)
    results["replay_throughput_eps"] = round(event_count / elapsed_replay, 2) if elapsed_replay > 0 else 0.0
    print(f"[BENCHMARK] Replay Throughput: {results['replay_throughput_eps']} events/sec")

    # 5. Save results to docs/BENCHMARK_RESULTS.md
    docs_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "docs")
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    md_content = f"""# Cognify v3.0 Performance Benchmark Results

Generated on: {datetime.datetime.now().isoformat()}
Git Commit: {config.GIT_COMMIT}
Release Tag: {config.RELEASE_TAG}

---

## 1. System Footprint
- **Database File Size**: {results['database_size_mb']} MB ({results['database_size_bytes']} bytes)
- **Active Process Memory (RSS)**: {results['memory_rss_mb']} MB ({results['memory_rss_bytes']} bytes)

## 2. Event Processing Throughput
- **Total Events in Append-Only Ledger**: {results['event_count']}
- **Chronological Replay Duration (SAFE Mode)**: {results['replay_duration_seconds']} seconds
- **Replay Throughput**: {results['replay_throughput_eps']} events/second

## 3. REST API Query Latency (Measured over 50 requests)
| Endpoint | Average Latency (ms) | Min Latency (ms) | Max Latency (ms) |
|---|---|---|---|
"""
    for ep, lat in results["api_latencies"].items():
        md_content += f"| `{ep}` | {lat['avg_ms']} ms | {lat['min_ms']} ms | {lat['max_ms']} ms |\n"

    md_path = os.path.join(docs_dir, "BENCHMARK_RESULTS.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"[BENCHMARK] Benchmark validation completed successfully. Saved to docs/BENCHMARK_RESULTS.md")

if __name__ == "__main__":
    run_benchmarks()
