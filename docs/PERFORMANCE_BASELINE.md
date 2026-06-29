# Performance Baselines (Regression Audit)
Recorded on: 2026-06-30T00:50:06.371683

## Engine Run Latency
* **APD Run Latency**: 8.0ms
* **Misconception Run Latency**: 1.31ms
* **Context Recommendation Latency**: 1.01ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.0ms
* **SQLite Write Speed (1000 Rows)**: 1.0ms
* **SQLite Read Speed (1000 Rows)**: 1.0ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 3368.33ms
* **tests/test_apd_step2.py**: 3259.23ms
* **tests/test_apd_v2.py**: 3315.65ms
* **tests/test_context_engine.py**: 116.88ms
* **tests/test_md_integration.py**: 3405.73ms
* **tests/test_memory_integration.py**: 106.25ms
* **tests/test_misconception_v2.py**: 3270.81ms
* **tests/test_orchestrator.py**: 97.81ms
* **tests/test_pilot_analytics.py**: 87.8ms
* **tests/test_pilot_analytics_v2.py**: 99.28ms
* **tests/test_qqi_calibration.py**: 97.02ms
* **tests/test_teacher_twin.py**: 163.94ms
* **tests/test_e2e_integration.py**: 3142.63ms
* **tests/test_qqi_feedback_loop.py**: 107.98ms
* **tests/test_nbirt.py**: 100.85ms
* **tests/test_cognitive_load.py**: 156.73ms
* **tests/test_cdo.py**: 151.14ms
* **tests/test_cte.py**: 165.0ms
* **tests/test_attention.py**: 148.21ms
* **tests/test_question_lifecycle.py**: 160.53ms
* **tests/test_event_bus.py**: 162.14ms
* **tests/test_student_twin.py**: 188.33ms
* **tests/test_parent_twin.py**: 168.7ms
* **tests/test_school_admin_twin.py**: 175.39ms
* **tests/test_research_analytics_twin.py**: 181.75ms
* **tests/test_production_hardening.py**: 3515.54ms
* **tests/test_pilot_dataset.py**: 965.49ms
* **tests/test_dataset_validation.py**: 6596.34ms
