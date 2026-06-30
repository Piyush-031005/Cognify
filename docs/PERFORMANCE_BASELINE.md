# Performance Baselines (Regression Audit)
Recorded on: 2026-06-30T15:55:09.619758

## Engine Run Latency
* **APD Run Latency**: 6.56ms
* **Misconception Run Latency**: 3.0ms
* **Context Recommendation Latency**: 1.01ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.11ms
* **SQLite Write Speed (1000 Rows)**: 1.0ms
* **SQLite Read Speed (1000 Rows)**: 2.0ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 4779.49ms
* **tests/test_apd_step2.py**: 3136.18ms
* **tests/test_apd_v2.py**: 3101.18ms
* **tests/test_context_engine.py**: 178.67ms
* **tests/test_md_integration.py**: 3229.53ms
* **tests/test_memory_integration.py**: 93.77ms
* **tests/test_misconception_v2.py**: 3094.26ms
* **tests/test_orchestrator.py**: 93.68ms
* **tests/test_pilot_analytics.py**: 82.67ms
* **tests/test_pilot_analytics_v2.py**: 80.67ms
* **tests/test_qqi_calibration.py**: 98.27ms
* **tests/test_teacher_twin.py**: 194.01ms
* **tests/test_e2e_integration.py**: 3154.34ms
* **tests/test_qqi_feedback_loop.py**: 108.23ms
* **tests/test_nbirt.py**: 87.44ms
* **tests/test_cognitive_load.py**: 139.57ms
* **tests/test_cdo.py**: 139.57ms
* **tests/test_cte.py**: 136.21ms
* **tests/test_attention.py**: 138.15ms
* **tests/test_question_lifecycle.py**: 139.69ms
* **tests/test_event_bus.py**: 139.75ms
* **tests/test_student_twin.py**: 167.65ms
* **tests/test_parent_twin.py**: 227.91ms
* **tests/test_school_admin_twin.py**: 188.83ms
* **tests/test_research_analytics_twin.py**: 161.65ms
* **tests/test_production_hardening.py**: 3514.45ms
* **tests/test_pilot_dataset.py**: 975.25ms
* **tests/test_dataset_validation.py**: 6197.82ms
