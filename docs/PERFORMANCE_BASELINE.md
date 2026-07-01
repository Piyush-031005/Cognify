# Performance Baselines (Regression Audit)
Recorded on: 2026-07-01T07:59:12.788053

## Engine Run Latency
* **APD Run Latency**: 7.0ms
* **Misconception Run Latency**: 2.96ms
* **Context Recommendation Latency**: 1.02ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.75ms
* **SQLite Write Speed (1000 Rows)**: 1.02ms
* **SQLite Read Speed (1000 Rows)**: 1.98ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 7520.38ms
* **tests/test_apd_step2.py**: 4732.7ms
* **tests/test_apd_v2.py**: 4816.52ms
* **tests/test_context_engine.py**: 322.35ms
* **tests/test_md_integration.py**: 4449.9ms
* **tests/test_memory_integration.py**: 128.01ms
* **tests/test_misconception_v2.py**: 4629.62ms
* **tests/test_orchestrator.py**: 107.25ms
* **tests/test_pilot_analytics.py**: 91.0ms
* **tests/test_pilot_analytics_v2.py**: 111.18ms
* **tests/test_qqi_calibration.py**: 129.46ms
* **tests/test_teacher_twin.py**: 331.2ms
* **tests/test_e2e_integration.py**: 4244.38ms
* **tests/test_qqi_feedback_loop.py**: 134.42ms
* **tests/test_nbirt.py**: 124.9ms
* **tests/test_cognitive_load.py**: 206.43ms
* **tests/test_cdo.py**: 178.1ms
* **tests/test_cte.py**: 184.93ms
* **tests/test_attention.py**: 176.44ms
* **tests/test_question_lifecycle.py**: 207.89ms
* **tests/test_event_bus.py**: 186.56ms
* **tests/test_student_twin.py**: 218.78ms
* **tests/test_parent_twin.py**: 213.28ms
* **tests/test_school_admin_twin.py**: 305.59ms
* **tests/test_research_analytics_twin.py**: 284.9ms
* **tests/test_production_hardening.py**: 5972.21ms
* **tests/test_pilot_dataset.py**: 1603.49ms
* **tests/test_dataset_validation.py**: 9726.41ms
