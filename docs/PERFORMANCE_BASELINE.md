# Performance Baselines (Regression Audit)
Recorded on: 2026-06-30T15:33:47.853864

## Engine Run Latency
* **APD Run Latency**: 8.0ms
* **Misconception Run Latency**: 1.0ms
* **Context Recommendation Latency**: 2.0ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.33ms
* **SQLite Write Speed (1000 Rows)**: 1.0ms
* **SQLite Read Speed (1000 Rows)**: 2.0ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 3881.02ms
* **tests/test_apd_step2.py**: 3305.03ms
* **tests/test_apd_v2.py**: 3012.3ms
* **tests/test_context_engine.py**: 113.63ms
* **tests/test_md_integration.py**: 3160.91ms
* **tests/test_memory_integration.py**: 96.38ms
* **tests/test_misconception_v2.py**: 3236.1ms
* **tests/test_orchestrator.py**: 105.69ms
* **tests/test_pilot_analytics.py**: 80.96ms
* **tests/test_pilot_analytics_v2.py**: 84.85ms
* **tests/test_qqi_calibration.py**: 96.45ms
* **tests/test_teacher_twin.py**: 158.59ms
* **tests/test_e2e_integration.py**: 3225.94ms
* **tests/test_qqi_feedback_loop.py**: 111.68ms
* **tests/test_nbirt.py**: 96.58ms
* **tests/test_cognitive_load.py**: 151.65ms
* **tests/test_cdo.py**: 152.53ms
* **tests/test_cte.py**: 144.17ms
* **tests/test_attention.py**: 142.96ms
* **tests/test_question_lifecycle.py**: 144.97ms
* **tests/test_event_bus.py**: 157.73ms
* **tests/test_student_twin.py**: 173.77ms
* **tests/test_parent_twin.py**: 170.07ms
* **tests/test_school_admin_twin.py**: 173.14ms
* **tests/test_research_analytics_twin.py**: 165.36ms
* **tests/test_production_hardening.py**: 3861.26ms
* **tests/test_pilot_dataset.py**: 1551.58ms
* **tests/test_dataset_validation.py**: 7059.66ms
