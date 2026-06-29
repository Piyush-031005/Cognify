# Performance Baselines (Regression Audit)
Recorded on: 2026-06-29T11:37:48.962143

## Engine Run Latency
* **APD Run Latency**: 10.0ms
* **Misconception Run Latency**: 2.02ms
* **Context Recommendation Latency**: 1.98ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 4.0ms
* **SQLite Write Speed (1000 Rows)**: 5.03ms
* **SQLite Read Speed (1000 Rows)**: 1.98ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 4218.81ms
* **tests/test_apd_step2.py**: 4193.03ms
* **tests/test_apd_v2.py**: 4465.07ms
* **tests/test_context_engine.py**: 125.06ms
* **tests/test_md_integration.py**: 4204.17ms
* **tests/test_memory_integration.py**: 113.9ms
* **tests/test_misconception_v2.py**: 3903.23ms
* **tests/test_orchestrator.py**: 115.94ms
* **tests/test_pilot_analytics.py**: 103.99ms
* **tests/test_pilot_analytics_v2.py**: 97.49ms
* **tests/test_qqi_calibration.py**: 136.81ms
* **tests/test_teacher_twin.py**: 128.0ms
* **tests/test_e2e_integration.py**: 3878.35ms
* **tests/test_qqi_feedback_loop.py**: 128.99ms
* **tests/test_nbirt.py**: 120.0ms
* **tests/test_cognitive_load.py**: 219.15ms
* **tests/test_cdo.py**: 174.6ms
* **tests/test_cte.py**: 171.02ms
* **tests/test_attention.py**: 197.43ms
* **tests/test_question_lifecycle.py**: 183.99ms
