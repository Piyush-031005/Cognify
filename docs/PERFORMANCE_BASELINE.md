# Performance Baselines (Regression Audit)
Recorded on: 2026-06-29T22:01:35.068357

## Engine Run Latency
* **APD Run Latency**: 7.0ms
* **Misconception Run Latency**: 3.05ms
* **Context Recommendation Latency**: 2.0ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.67ms
* **SQLite Write Speed (1000 Rows)**: 1.0ms
* **SQLite Read Speed (1000 Rows)**: 1.99ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 4133.88ms
* **tests/test_apd_step2.py**: 4185.06ms
* **tests/test_apd_v2.py**: 4133.26ms
* **tests/test_context_engine.py**: 142.9ms
* **tests/test_md_integration.py**: 3612.65ms
* **tests/test_memory_integration.py**: 105.03ms
* **tests/test_misconception_v2.py**: 3731.37ms
* **tests/test_orchestrator.py**: 99.73ms
* **tests/test_pilot_analytics.py**: 94.21ms
* **tests/test_pilot_analytics_v2.py**: 100.08ms
* **tests/test_qqi_calibration.py**: 109.91ms
* **tests/test_teacher_twin.py**: 181.41ms
* **tests/test_e2e_integration.py**: 3712.76ms
* **tests/test_qqi_feedback_loop.py**: 124.08ms
* **tests/test_nbirt.py**: 110.0ms
* **tests/test_cognitive_load.py**: 172.18ms
* **tests/test_cdo.py**: 176.34ms
* **tests/test_cte.py**: 170.82ms
* **tests/test_attention.py**: 167.73ms
* **tests/test_question_lifecycle.py**: 179.28ms
* **tests/test_event_bus.py**: 186.17ms
* **tests/test_student_twin.py**: 219.01ms
* **tests/test_parent_twin.py**: 226.37ms
* **tests/test_school_admin_twin.py**: 210.48ms
* **tests/test_research_analytics_twin.py**: 212.81ms
* **tests/test_production_hardening.py**: 3931.87ms
* **tests/test_pilot_dataset.py**: 240.4ms
