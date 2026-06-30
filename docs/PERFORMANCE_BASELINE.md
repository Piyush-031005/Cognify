# Performance Baselines (Regression Audit)
Recorded on: 2026-06-30T22:56:20.361522

## Engine Run Latency
* **APD Run Latency**: 7.96ms
* **Misconception Run Latency**: 2.84ms
* **Context Recommendation Latency**: 1.23ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.41ms
* **SQLite Write Speed (1000 Rows)**: 1.72ms
* **SQLite Read Speed (1000 Rows)**: 1.71ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 18238.47ms
* **tests/test_apd_step2.py**: 3981.44ms
* **tests/test_apd_v2.py**: 3905.86ms
* **tests/test_context_engine.py**: 280.29ms
* **tests/test_md_integration.py**: 3679.6ms
* **tests/test_memory_integration.py**: 117.03ms
* **tests/test_misconception_v2.py**: 3850.02ms
* **tests/test_orchestrator.py**: 112.18ms
* **tests/test_pilot_analytics.py**: 108.35ms
* **tests/test_pilot_analytics_v2.py**: 106.84ms
* **tests/test_qqi_calibration.py**: 122.96ms
* **tests/test_teacher_twin.py**: 194.58ms
* **tests/test_e2e_integration.py**: 3997.96ms
* **tests/test_qqi_feedback_loop.py**: 145.74ms
* **tests/test_nbirt.py**: 133.0ms
* **tests/test_cognitive_load.py**: 213.74ms
* **tests/test_cdo.py**: 194.53ms
* **tests/test_cte.py**: 199.89ms
* **tests/test_attention.py**: 206.04ms
* **tests/test_question_lifecycle.py**: 211.43ms
* **tests/test_event_bus.py**: 203.57ms
* **tests/test_student_twin.py**: 235.05ms
* **tests/test_parent_twin.py**: 220.34ms
* **tests/test_school_admin_twin.py**: 228.19ms
* **tests/test_research_analytics_twin.py**: 225.9ms
* **tests/test_production_hardening.py**: 4653.28ms
* **tests/test_pilot_dataset.py**: 1313.89ms
* **tests/test_dataset_validation.py**: 7854.6ms
