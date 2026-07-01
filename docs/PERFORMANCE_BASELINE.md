# Performance Baselines (Regression Audit)
Recorded on: 2026-07-01T08:24:09.002478

## Engine Run Latency
* **APD Run Latency**: 7.96ms
* **Misconception Run Latency**: 2.63ms
* **Context Recommendation Latency**: 1.03ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 3.0ms
* **SQLite Write Speed (1000 Rows)**: 1.0ms
* **SQLite Read Speed (1000 Rows)**: 2.03ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 5634.89ms
* **tests/test_apd_step2.py**: 5262.4ms
* **tests/test_apd_v2.py**: 5295.52ms
* **tests/test_context_engine.py**: 305.38ms
* **tests/test_md_integration.py**: 4093.6ms
* **tests/test_memory_integration.py**: 118.02ms
* **tests/test_misconception_v2.py**: 4211.84ms
* **tests/test_orchestrator.py**: 141.4ms
* **tests/test_pilot_analytics.py**: 107.84ms
* **tests/test_pilot_analytics_v2.py**: 104.36ms
* **tests/test_qqi_calibration.py**: 122.04ms
* **tests/test_teacher_twin.py**: 221.34ms
* **tests/test_e2e_integration.py**: 3737.82ms
* **tests/test_qqi_feedback_loop.py**: 126.3ms
* **tests/test_nbirt.py**: 109.53ms
* **tests/test_cognitive_load.py**: 179.15ms
* **tests/test_cdo.py**: 176.43ms
* **tests/test_cte.py**: 178.78ms
* **tests/test_attention.py**: 192.05ms
* **tests/test_question_lifecycle.py**: 190.97ms
* **tests/test_event_bus.py**: 286.86ms
* **tests/test_student_twin.py**: 242.03ms
* **tests/test_parent_twin.py**: 225.15ms
* **tests/test_school_admin_twin.py**: 253.33ms
* **tests/test_research_analytics_twin.py**: 232.37ms
* **tests/test_production_hardening.py**: 4448.25ms
* **tests/test_pilot_dataset.py**: 1207.49ms
* **tests/test_dataset_validation.py**: 8693.84ms
