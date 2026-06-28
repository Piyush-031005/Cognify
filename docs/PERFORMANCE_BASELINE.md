# Performance Baselines (Regression Audit)
Recorded on: 2026-06-28T13:04:44.447038

## Engine Run Latency
* **APD Run Latency**: 8.0ms
* **Misconception Run Latency**: 4.0ms
* **Context Recommendation Latency**: 8.0ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.33ms
* **SQLite Write Speed (1000 Rows)**: 3.01ms
* **SQLite Read Speed (1000 Rows)**: 0.99ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 3992.4ms
* **tests/test_apd_step2.py**: 4194.86ms
* **tests/test_apd_v2.py**: 4145.84ms
* **tests/test_context_engine.py**: 116.09ms
* **tests/test_md_integration.py**: 4252.93ms
* **tests/test_memory_integration.py**: 114.38ms
* **tests/test_misconception_v2.py**: 4121.7ms
* **tests/test_orchestrator.py**: 110.54ms
* **tests/test_pilot_analytics.py**: 101.01ms
* **tests/test_pilot_analytics_v2.py**: 107.89ms
* **tests/test_qqi_calibration.py**: 119.51ms
* **tests/test_teacher_twin.py**: 111.66ms
* **tests/test_e2e_integration.py**: 4156.81ms
