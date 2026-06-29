# Performance Baselines (Regression Audit)
Recorded on: 2026-06-29T11:12:58.811394

## Engine Run Latency
* **APD Run Latency**: 7.0ms
* **Misconception Run Latency**: 3.06ms
* **Context Recommendation Latency**: 2.0ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.34ms
* **SQLite Write Speed (1000 Rows)**: 2.1ms
* **SQLite Read Speed (1000 Rows)**: 1.88ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 3916.0ms
* **tests/test_apd_step2.py**: 3964.84ms
* **tests/test_apd_v2.py**: 3828.43ms
* **tests/test_context_engine.py**: 120.34ms
* **tests/test_md_integration.py**: 4067.31ms
* **tests/test_memory_integration.py**: 106.11ms
* **tests/test_misconception_v2.py**: 3705.95ms
* **tests/test_orchestrator.py**: 100.63ms
* **tests/test_pilot_analytics.py**: 96.17ms
* **tests/test_pilot_analytics_v2.py**: 95.85ms
* **tests/test_qqi_calibration.py**: 106.4ms
* **tests/test_teacher_twin.py**: 108.21ms
* **tests/test_e2e_integration.py**: 3737.62ms
* **tests/test_qqi_feedback_loop.py**: 129.65ms
* **tests/test_nbirt.py**: 135.95ms
* **tests/test_cognitive_load.py**: 221.66ms
* **tests/test_cdo.py**: 187.08ms
* **tests/test_cte.py**: 210.2ms
* **tests/test_attention.py**: 234.15ms
