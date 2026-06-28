# Performance Baselines (Regression Audit)
Recorded on: 2026-06-28T13:57:12.578444

## Engine Run Latency
* **APD Run Latency**: 7.14ms
* **Misconception Run Latency**: 2.0ms
* **Context Recommendation Latency**: 3.02ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.66ms
* **SQLite Write Speed (1000 Rows)**: 1.0ms
* **SQLite Read Speed (1000 Rows)**: 1.0ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 3308.16ms
* **tests/test_apd_step2.py**: 3481.81ms
* **tests/test_apd_v2.py**: 3290.62ms
* **tests/test_context_engine.py**: 104.31ms
* **tests/test_md_integration.py**: 3203.56ms
* **tests/test_memory_integration.py**: 86.54ms
* **tests/test_misconception_v2.py**: 3063.99ms
* **tests/test_orchestrator.py**: 87.38ms
* **tests/test_pilot_analytics.py**: 83.68ms
* **tests/test_pilot_analytics_v2.py**: 84.58ms
* **tests/test_qqi_calibration.py**: 95.8ms
* **tests/test_teacher_twin.py**: 88.38ms
* **tests/test_e2e_integration.py**: 3405.63ms
