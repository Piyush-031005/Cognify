# Performance Baselines (Regression Audit)
Recorded on: 2026-06-29T12:18:18.433794

## Engine Run Latency
* **APD Run Latency**: 7.97ms
* **Misconception Run Latency**: 4.0ms
* **Context Recommendation Latency**: 1.0ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 3.67ms
* **SQLite Write Speed (1000 Rows)**: 2.03ms
* **SQLite Read Speed (1000 Rows)**: 2.97ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 4145.64ms
* **tests/test_apd_step2.py**: 3974.48ms
* **tests/test_apd_v2.py**: 4034.62ms
* **tests/test_context_engine.py**: 129.18ms
* **tests/test_md_integration.py**: 4095.38ms
* **tests/test_memory_integration.py**: 127.15ms
* **tests/test_misconception_v2.py**: 4775.48ms
* **tests/test_orchestrator.py**: 106.27ms
* **tests/test_pilot_analytics.py**: 105.11ms
* **tests/test_pilot_analytics_v2.py**: 105.0ms
* **tests/test_qqi_calibration.py**: 184.44ms
* **tests/test_teacher_twin.py**: 273.17ms
* **tests/test_e2e_integration.py**: 4028.19ms
* **tests/test_qqi_feedback_loop.py**: 209.06ms
* **tests/test_nbirt.py**: 169.57ms
* **tests/test_cognitive_load.py**: 293.78ms
* **tests/test_cdo.py**: 219.76ms
* **tests/test_cte.py**: 200.51ms
* **tests/test_attention.py**: 195.4ms
* **tests/test_question_lifecycle.py**: 203.0ms
* **tests/test_event_bus.py**: 202.03ms
