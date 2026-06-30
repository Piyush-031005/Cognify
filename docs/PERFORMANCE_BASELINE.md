# Performance Baselines (Regression Audit)
Recorded on: 2026-06-30T14:59:16.154205

## Engine Run Latency
* **APD Run Latency**: 6.05ms
* **Misconception Run Latency**: 2.46ms
* **Context Recommendation Latency**: 2.62ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 2.4ms
* **SQLite Write Speed (1000 Rows)**: 0.85ms
* **SQLite Read Speed (1000 Rows)**: 1.46ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 3741.18ms
* **tests/test_apd_step2.py**: 3259.64ms
* **tests/test_apd_v2.py**: 3384.37ms
* **tests/test_context_engine.py**: 125.15ms
* **tests/test_md_integration.py**: 3418.01ms
* **tests/test_memory_integration.py**: 88.21ms
* **tests/test_misconception_v2.py**: 3427.05ms
* **tests/test_orchestrator.py**: 82.5ms
* **tests/test_pilot_analytics.py**: 79.59ms
* **tests/test_pilot_analytics_v2.py**: 79.99ms
* **tests/test_qqi_calibration.py**: 87.02ms
* **tests/test_teacher_twin.py**: 151.64ms
* **tests/test_e2e_integration.py**: 2975.4ms
* **tests/test_qqi_feedback_loop.py**: 97.25ms
* **tests/test_nbirt.py**: 89.6ms
* **tests/test_cognitive_load.py**: 145.47ms
* **tests/test_cdo.py**: 136.7ms
* **tests/test_cte.py**: 140.28ms
* **tests/test_attention.py**: 142.89ms
* **tests/test_question_lifecycle.py**: 142.69ms
* **tests/test_event_bus.py**: 139.05ms
* **tests/test_student_twin.py**: 164.66ms
* **tests/test_parent_twin.py**: 167.67ms
* **tests/test_school_admin_twin.py**: 164.64ms
* **tests/test_research_analytics_twin.py**: 165.82ms
* **tests/test_production_hardening.py**: 3566.51ms
* **tests/test_pilot_dataset.py**: 959.97ms
* **tests/test_dataset_validation.py**: 6376.05ms
