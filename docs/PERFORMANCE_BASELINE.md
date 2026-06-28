# Performance Baselines (Regression Audit)
Recorded on: 2026-06-28T23:14:10.569864

## Engine Run Latency
* **APD Run Latency**: 6.87ms
* **Misconception Run Latency**: 3.31ms
* **Context Recommendation Latency**: 1.0ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.8ms
* **SQLite Write Speed (1000 Rows)**: 1.46ms
* **SQLite Read Speed (1000 Rows)**: 1.01ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 15975.97ms
* **tests/test_apd_step2.py**: 3046.49ms
* **tests/test_apd_v2.py**: 3022.48ms
* **tests/test_context_engine.py**: 106.71ms
* **tests/test_md_integration.py**: 3062.42ms
* **tests/test_memory_integration.py**: 93.62ms
* **tests/test_misconception_v2.py**: 3096.24ms
* **tests/test_orchestrator.py**: 98.55ms
* **tests/test_pilot_analytics.py**: 96.69ms
* **tests/test_pilot_analytics_v2.py**: 91.31ms
* **tests/test_qqi_calibration.py**: 99.62ms
* **tests/test_teacher_twin.py**: 96.74ms
* **tests/test_e2e_integration.py**: 3072.57ms
* **tests/test_qqi_feedback_loop.py**: 102.89ms
* **tests/test_nbirt.py**: 87.16ms
