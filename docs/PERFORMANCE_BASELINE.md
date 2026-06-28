# Performance Baselines (Regression Audit)
Recorded on: 2026-06-29T00:16:09.617428

## Engine Run Latency
* **APD Run Latency**: 6.99ms
* **Misconception Run Latency**: 2.99ms
* **Context Recommendation Latency**: 1.03ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.66ms
* **SQLite Write Speed (1000 Rows)**: 2.0ms
* **SQLite Read Speed (1000 Rows)**: 1.02ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 4371.21ms
* **tests/test_apd_step2.py**: 4043.87ms
* **tests/test_apd_v2.py**: 3922.23ms
* **tests/test_context_engine.py**: 146.43ms
* **tests/test_md_integration.py**: 4255.29ms
* **tests/test_memory_integration.py**: 118.72ms
* **tests/test_misconception_v2.py**: 3889.2ms
* **tests/test_orchestrator.py**: 103.24ms
* **tests/test_pilot_analytics.py**: 97.22ms
* **tests/test_pilot_analytics_v2.py**: 105.62ms
* **tests/test_qqi_calibration.py**: 122.36ms
* **tests/test_teacher_twin.py**: 112.05ms
* **tests/test_e2e_integration.py**: 4299.75ms
* **tests/test_qqi_feedback_loop.py**: 131.22ms
* **tests/test_nbirt.py**: 111.98ms
* **tests/test_cognitive_load.py**: 180.68ms
