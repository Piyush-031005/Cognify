# Performance Baselines (Regression Audit)
Recorded on: 2026-06-30T14:03:07.818430

## Engine Run Latency
* **APD Run Latency**: 7.0ms
* **Misconception Run Latency**: 2.01ms
* **Context Recommendation Latency**: 1.97ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 3.01ms
* **SQLite Write Speed (1000 Rows)**: 2.01ms
* **SQLite Read Speed (1000 Rows)**: 1.99ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 18231.42ms
* **tests/test_apd_step2.py**: 4049.87ms
* **tests/test_apd_v2.py**: 4074.13ms
* **tests/test_context_engine.py**: 198.62ms
* **tests/test_md_integration.py**: 4028.71ms
* **tests/test_memory_integration.py**: 140.83ms
* **tests/test_misconception_v2.py**: 4242.02ms
* **tests/test_orchestrator.py**: 135.64ms
* **tests/test_pilot_analytics.py**: 123.37ms
* **tests/test_pilot_analytics_v2.py**: 118.28ms
* **tests/test_qqi_calibration.py**: 142.13ms
* **tests/test_teacher_twin.py**: 220.6ms
* **tests/test_e2e_integration.py**: 4007.63ms
* **tests/test_qqi_feedback_loop.py**: 164.87ms
* **tests/test_nbirt.py**: 137.91ms
* **tests/test_cognitive_load.py**: 213.61ms
* **tests/test_cdo.py**: 236.49ms
* **tests/test_cte.py**: 254.49ms
* **tests/test_attention.py**: 210.47ms
* **tests/test_question_lifecycle.py**: 216.63ms
* **tests/test_event_bus.py**: 200.47ms
* **tests/test_student_twin.py**: 239.81ms
* **tests/test_parent_twin.py**: 232.43ms
* **tests/test_school_admin_twin.py**: 238.29ms
* **tests/test_research_analytics_twin.py**: 231.64ms
* **tests/test_production_hardening.py**: 4811.18ms
* **tests/test_pilot_dataset.py**: 1452.01ms
* **tests/test_dataset_validation.py**: 7889.82ms
