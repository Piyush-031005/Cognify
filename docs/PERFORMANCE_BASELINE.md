# Performance Baselines (Regression Audit)
Recorded on: 2026-06-29T11:55:56.542369

## Engine Run Latency
* **APD Run Latency**: 8.99ms
* **Misconception Run Latency**: 4.0ms
* **Context Recommendation Latency**: 1.0ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 3.67ms
* **SQLite Write Speed (1000 Rows)**: 1.98ms
* **SQLite Read Speed (1000 Rows)**: 3.0ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 5392.41ms
* **tests/test_apd_step2.py**: 4658.3ms
* **tests/test_apd_v2.py**: 4944.35ms
* **tests/test_context_engine.py**: 135.01ms
* **tests/test_md_integration.py**: 5749.39ms
* **tests/test_memory_integration.py**: 149.0ms
* **tests/test_misconception_v2.py**: 5717.12ms
* **tests/test_orchestrator.py**: 165.17ms
* **tests/test_pilot_analytics.py**: 144.09ms
* **tests/test_pilot_analytics_v2.py**: 148.4ms
* **tests/test_qqi_calibration.py**: 184.38ms
* **tests/test_teacher_twin.py**: 157.0ms
* **tests/test_e2e_integration.py**: 5893.22ms
* **tests/test_qqi_feedback_loop.py**: 207.98ms
* **tests/test_nbirt.py**: 138.27ms
* **tests/test_cognitive_load.py**: 258.41ms
* **tests/test_cdo.py**: 212.74ms
* **tests/test_cte.py**: 209.98ms
* **tests/test_attention.py**: 221.54ms
* **tests/test_question_lifecycle.py**: 222.09ms
* **tests/test_event_bus.py**: 219.39ms
