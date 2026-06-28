# Performance Baselines (Regression Audit)
Recorded on: 2026-06-29T00:31:50.774503

## Engine Run Latency
* **APD Run Latency**: 7.99ms
* **Misconception Run Latency**: 2.02ms
* **Context Recommendation Latency**: 1.99ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.66ms
* **SQLite Write Speed (1000 Rows)**: 1.01ms
* **SQLite Read Speed (1000 Rows)**: 2.0ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 4095.94ms
* **tests/test_apd_step2.py**: 3904.91ms
* **tests/test_apd_v2.py**: 4188.48ms
* **tests/test_context_engine.py**: 146.92ms
* **tests/test_md_integration.py**: 3918.36ms
* **tests/test_memory_integration.py**: 108.51ms
* **tests/test_misconception_v2.py**: 3939.83ms
* **tests/test_orchestrator.py**: 117.02ms
* **tests/test_pilot_analytics.py**: 116.4ms
* **tests/test_pilot_analytics_v2.py**: 133.91ms
* **tests/test_qqi_calibration.py**: 131.0ms
* **tests/test_teacher_twin.py**: 131.22ms
* **tests/test_e2e_integration.py**: 4347.77ms
* **tests/test_qqi_feedback_loop.py**: 135.67ms
* **tests/test_nbirt.py**: 115.25ms
* **tests/test_cognitive_load.py**: 185.49ms
* **tests/test_cdo.py**: 183.42ms
