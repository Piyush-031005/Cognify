# Performance Baselines (Regression Audit)
Recorded on: 2026-06-30T01:25:55.457287

## Engine Run Latency
* **APD Run Latency**: 10.0ms
* **Misconception Run Latency**: 3.03ms
* **Context Recommendation Latency**: 1.0ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.67ms
* **SQLite Write Speed (1000 Rows)**: 0.97ms
* **SQLite Read Speed (1000 Rows)**: 2.01ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 4349.78ms
* **tests/test_apd_step2.py**: 4543.04ms
* **tests/test_apd_v2.py**: 4180.88ms
* **tests/test_context_engine.py**: 142.3ms
* **tests/test_md_integration.py**: 4089.3ms
* **tests/test_memory_integration.py**: 110.44ms
* **tests/test_misconception_v2.py**: 3616.61ms
* **tests/test_orchestrator.py**: 102.24ms
* **tests/test_pilot_analytics.py**: 95.51ms
* **tests/test_pilot_analytics_v2.py**: 101.51ms
* **tests/test_qqi_calibration.py**: 116.01ms
* **tests/test_teacher_twin.py**: 190.02ms
* **tests/test_e2e_integration.py**: 3633.13ms
* **tests/test_qqi_feedback_loop.py**: 135.86ms
* **tests/test_nbirt.py**: 118.2ms
* **tests/test_cognitive_load.py**: 176.26ms
* **tests/test_cdo.py**: 170.27ms
* **tests/test_cte.py**: 178.25ms
* **tests/test_attention.py**: 173.49ms
* **tests/test_question_lifecycle.py**: 186.48ms
* **tests/test_event_bus.py**: 190.01ms
* **tests/test_student_twin.py**: 223.29ms
* **tests/test_parent_twin.py**: 196.63ms
* **tests/test_school_admin_twin.py**: 222.59ms
* **tests/test_research_analytics_twin.py**: 217.31ms
* **tests/test_production_hardening.py**: 4077.58ms
* **tests/test_pilot_dataset.py**: 1261.72ms
* **tests/test_dataset_validation.py**: 7446.03ms
