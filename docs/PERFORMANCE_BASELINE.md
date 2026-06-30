# Performance Baselines (Regression Audit)
Recorded on: 2026-06-30T23:06:05.228983

## Engine Run Latency
* **APD Run Latency**: 8.51ms
* **Misconception Run Latency**: 3.09ms
* **Context Recommendation Latency**: 2.02ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 3.68ms
* **SQLite Write Speed (1000 Rows)**: 1.7ms
* **SQLite Read Speed (1000 Rows)**: 1.64ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 4119.91ms
* **tests/test_apd_step2.py**: 4052.47ms
* **tests/test_apd_v2.py**: 4010.75ms
* **tests/test_context_engine.py**: 157.08ms
* **tests/test_md_integration.py**: 4275.47ms
* **tests/test_memory_integration.py**: 112.91ms
* **tests/test_misconception_v2.py**: 4054.65ms
* **tests/test_orchestrator.py**: 103.37ms
* **tests/test_pilot_analytics.py**: 102.67ms
* **tests/test_pilot_analytics_v2.py**: 102.22ms
* **tests/test_qqi_calibration.py**: 116.25ms
* **tests/test_teacher_twin.py**: 204.17ms
* **tests/test_e2e_integration.py**: 4103.34ms
* **tests/test_qqi_feedback_loop.py**: 132.3ms
* **tests/test_nbirt.py**: 114.24ms
* **tests/test_cognitive_load.py**: 193.82ms
* **tests/test_cdo.py**: 197.26ms
* **tests/test_cte.py**: 173.49ms
* **tests/test_attention.py**: 166.96ms
* **tests/test_question_lifecycle.py**: 173.99ms
* **tests/test_event_bus.py**: 172.81ms
* **tests/test_student_twin.py**: 195.39ms
* **tests/test_parent_twin.py**: 194.56ms
* **tests/test_school_admin_twin.py**: 202.41ms
* **tests/test_research_analytics_twin.py**: 192.99ms
* **tests/test_production_hardening.py**: 4253.62ms
* **tests/test_pilot_dataset.py**: 1284.57ms
* **tests/test_dataset_validation.py**: 7841.08ms
