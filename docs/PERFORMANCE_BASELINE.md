# Performance Baselines (Regression Audit)
Recorded on: 2026-06-29T10:58:24.838495

## Engine Run Latency
* **APD Run Latency**: 7.98ms
* **Misconception Run Latency**: 3.0ms
* **Context Recommendation Latency**: 1.03ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.33ms
* **SQLite Write Speed (1000 Rows)**: 1.0ms
* **SQLite Read Speed (1000 Rows)**: 1.99ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 18994.11ms
* **tests/test_apd_step2.py**: 4020.19ms
* **tests/test_apd_v2.py**: 4040.46ms
* **tests/test_context_engine.py**: 156.36ms
* **tests/test_md_integration.py**: 3945.75ms
* **tests/test_memory_integration.py**: 133.43ms
* **tests/test_misconception_v2.py**: 3825.28ms
* **tests/test_orchestrator.py**: 117.89ms
* **tests/test_pilot_analytics.py**: 113.49ms
* **tests/test_pilot_analytics_v2.py**: 121.0ms
* **tests/test_qqi_calibration.py**: 139.0ms
* **tests/test_teacher_twin.py**: 131.92ms
* **tests/test_e2e_integration.py**: 3871.21ms
* **tests/test_qqi_feedback_loop.py**: 149.07ms
* **tests/test_nbirt.py**: 144.38ms
* **tests/test_cognitive_load.py**: 208.65ms
* **tests/test_cdo.py**: 189.04ms
* **tests/test_cte.py**: 190.0ms
