# Performance Baselines (Regression Audit)
Recorded on: 2026-06-30T23:11:58.416797

## Engine Run Latency
* **APD Run Latency**: 8.63ms
* **Misconception Run Latency**: 4.66ms
* **Context Recommendation Latency**: 1.68ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 4.14ms
* **SQLite Write Speed (1000 Rows)**: 2.38ms
* **SQLite Read Speed (1000 Rows)**: 3.53ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 5375.87ms
* **tests/test_apd_step2.py**: 5182.65ms
* **tests/test_apd_v2.py**: 5343.09ms
* **tests/test_context_engine.py**: 190.01ms
* **tests/test_md_integration.py**: 4972.92ms
* **tests/test_memory_integration.py**: 135.8ms
* **tests/test_misconception_v2.py**: 5043.06ms
* **tests/test_orchestrator.py**: 122.1ms
* **tests/test_pilot_analytics.py**: 106.86ms
* **tests/test_pilot_analytics_v2.py**: 109.5ms
* **tests/test_qqi_calibration.py**: 123.84ms
* **tests/test_teacher_twin.py**: 217.3ms
* **tests/test_e2e_integration.py**: 4708.52ms
* **tests/test_qqi_feedback_loop.py**: 223.31ms
* **tests/test_nbirt.py**: 145.73ms
* **tests/test_cognitive_load.py**: 249.71ms
* **tests/test_cdo.py**: 226.28ms
* **tests/test_cte.py**: 240.99ms
* **tests/test_attention.py**: 246.46ms
* **tests/test_question_lifecycle.py**: 241.45ms
* **tests/test_event_bus.py**: 244.2ms
* **tests/test_student_twin.py**: 266.78ms
* **tests/test_parent_twin.py**: 282.46ms
* **tests/test_school_admin_twin.py**: 335.22ms
* **tests/test_research_analytics_twin.py**: 314.22ms
* **tests/test_production_hardening.py**: 6184.28ms
* **tests/test_pilot_dataset.py**: 2004.38ms
* **tests/test_dataset_validation.py**: 9607.78ms
