# Performance Baselines (Regression Audit)
Recorded on: 2026-06-30T23:17:52.460007

## Engine Run Latency
* **APD Run Latency**: 7.75ms
* **Misconception Run Latency**: 2.97ms
* **Context Recommendation Latency**: 2.01ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.66ms
* **SQLite Write Speed (1000 Rows)**: 1.0ms
* **SQLite Read Speed (1000 Rows)**: 2.0ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 4807.71ms
* **tests/test_apd_step2.py**: 4944.07ms
* **tests/test_apd_v2.py**: 4519.22ms
* **tests/test_context_engine.py**: 198.09ms
* **tests/test_md_integration.py**: 4275.41ms
* **tests/test_memory_integration.py**: 165.67ms
* **tests/test_misconception_v2.py**: 4238.94ms
* **tests/test_orchestrator.py**: 120.25ms
* **tests/test_pilot_analytics.py**: 104.89ms
* **tests/test_pilot_analytics_v2.py**: 108.68ms
* **tests/test_qqi_calibration.py**: 133.88ms
* **tests/test_teacher_twin.py**: 223.26ms
* **tests/test_e2e_integration.py**: 3847.72ms
* **tests/test_qqi_feedback_loop.py**: 132.32ms
* **tests/test_nbirt.py**: 109.37ms
* **tests/test_cognitive_load.py**: 186.5ms
* **tests/test_cdo.py**: 178.31ms
* **tests/test_cte.py**: 175.17ms
* **tests/test_attention.py**: 166.63ms
* **tests/test_question_lifecycle.py**: 211.67ms
* **tests/test_event_bus.py**: 187.56ms
* **tests/test_student_twin.py**: 198.38ms
* **tests/test_parent_twin.py**: 192.77ms
* **tests/test_school_admin_twin.py**: 199.75ms
* **tests/test_research_analytics_twin.py**: 204.68ms
* **tests/test_production_hardening.py**: 5029.44ms
* **tests/test_pilot_dataset.py**: 1480.57ms
* **tests/test_dataset_validation.py**: 8543.8ms
