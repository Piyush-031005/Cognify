# Performance Baselines (Regression Audit)
Recorded on: 2026-06-30T14:30:09.472721

## Engine Run Latency
* **APD Run Latency**: 8.34ms
* **Misconception Run Latency**: 3.0ms
* **Context Recommendation Latency**: 1.0ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.69ms
* **SQLite Write Speed (1000 Rows)**: 1.0ms
* **SQLite Read Speed (1000 Rows)**: 2.52ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 4076.91ms
* **tests/test_apd_step2.py**: 4040.17ms
* **tests/test_apd_v2.py**: 3957.54ms
* **tests/test_context_engine.py**: 154.44ms
* **tests/test_md_integration.py**: 4020.42ms
* **tests/test_memory_integration.py**: 156.66ms
* **tests/test_misconception_v2.py**: 3850.63ms
* **tests/test_orchestrator.py**: 103.14ms
* **tests/test_pilot_analytics.py**: 101.68ms
* **tests/test_pilot_analytics_v2.py**: 102.59ms
* **tests/test_qqi_calibration.py**: 116.48ms
* **tests/test_teacher_twin.py**: 205.18ms
* **tests/test_e2e_integration.py**: 3957.5ms
* **tests/test_qqi_feedback_loop.py**: 134.27ms
* **tests/test_nbirt.py**: 115.28ms
* **tests/test_cognitive_load.py**: 176.84ms
* **tests/test_cdo.py**: 179.99ms
* **tests/test_cte.py**: 172.96ms
* **tests/test_attention.py**: 173.65ms
* **tests/test_question_lifecycle.py**: 174.51ms
* **tests/test_event_bus.py**: 178.69ms
* **tests/test_student_twin.py**: 209.57ms
* **tests/test_parent_twin.py**: 187.06ms
* **tests/test_school_admin_twin.py**: 192.62ms
* **tests/test_research_analytics_twin.py**: 197.16ms
* **tests/test_production_hardening.py**: 4015.65ms
* **tests/test_pilot_dataset.py**: 1241.68ms
* **tests/test_dataset_validation.py**: 7446.25ms
