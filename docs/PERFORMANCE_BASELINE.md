# Performance Baselines (Regression Audit)
Recorded on: 2026-06-28T16:36:28.309009

## Engine Run Latency
* **APD Run Latency**: 7.98ms
* **Misconception Run Latency**: 3.52ms
* **Context Recommendation Latency**: 0.99ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.33ms
* **SQLite Write Speed (1000 Rows)**: 2.67ms
* **SQLite Read Speed (1000 Rows)**: 1.0ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 5455.49ms
* **tests/test_apd_step2.py**: 4359.59ms
* **tests/test_apd_v2.py**: 4070.46ms
* **tests/test_context_engine.py**: 125.91ms
* **tests/test_md_integration.py**: 3932.59ms
* **tests/test_memory_integration.py**: 114.93ms
* **tests/test_misconception_v2.py**: 3964.2ms
* **tests/test_orchestrator.py**: 135.25ms
* **tests/test_pilot_analytics.py**: 108.34ms
* **tests/test_pilot_analytics_v2.py**: 103.32ms
* **tests/test_qqi_calibration.py**: 122.53ms
* **tests/test_teacher_twin.py**: 119.4ms
* **tests/test_e2e_integration.py**: 3944.23ms
