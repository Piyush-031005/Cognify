# Performance Baselines (Regression Audit)
Recorded on: 2026-06-28T12:02:55.862990

## Engine Run Latency
* **APD Run Latency**: 7.35ms
* **Misconception Run Latency**: 3.0ms
* **Context Recommendation Latency**: 4.13ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.57ms
* **SQLite Write Speed (1000 Rows)**: 1.0ms
* **SQLite Read Speed (1000 Rows)**: 1.0ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 4757.14ms
* **tests/test_apd_step2.py**: 4129.06ms
* **tests/test_apd_v2.py**: 3964.56ms
* **tests/test_context_engine.py**: 94.97ms
* **tests/test_md_integration.py**: 3695.09ms
* **tests/test_memory_integration.py**: 96.64ms
* **tests/test_misconception_v2.py**: 3975.68ms
* **tests/test_orchestrator.py**: 95.66ms
* **tests/test_pilot_analytics.py**: 101.46ms
* **tests/test_pilot_analytics_v2.py**: 109.0ms
* **tests/test_qqi_calibration.py**: 114.89ms
* **tests/test_teacher_twin.py**: 116.82ms
* **tests/test_e2e_integration.py**: 3995.04ms
