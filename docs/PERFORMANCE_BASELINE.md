# Performance Baselines (Regression Audit)
Recorded on: 2026-06-29T23:41:05.995835

## Engine Run Latency
* **APD Run Latency**: 8.0ms
* **Misconception Run Latency**: 3.0ms
* **Context Recommendation Latency**: 1.0ms

## Database Benchmarks
* **Idempotent Schema Migration Latency (Avg)**: 3.0ms
* **SQLite Write Speed (1000 Rows)**: 1.0ms
* **SQLite Read Speed (1000 Rows)**: 2.0ms

## Test Suite Execution Durations
* **tests/test_apd_integration.py**: 4288.31ms
* **tests/test_apd_step2.py**: 4597.08ms
* **tests/test_apd_v2.py**: 3897.99ms
* **tests/test_context_engine.py**: 124.92ms
* **tests/test_md_integration.py**: 4080.99ms
* **tests/test_memory_integration.py**: 101.0ms
* **tests/test_misconception_v2.py**: 3475.98ms
* **tests/test_orchestrator.py**: 95.87ms
* **tests/test_pilot_analytics.py**: 92.05ms
* **tests/test_pilot_analytics_v2.py**: 87.2ms
* **tests/test_qqi_calibration.py**: 104.35ms
* **tests/test_teacher_twin.py**: 166.28ms
* **tests/test_e2e_integration.py**: 3679.78ms
* **tests/test_qqi_feedback_loop.py**: 122.35ms
* **tests/test_nbirt.py**: 107.45ms
* **tests/test_cognitive_load.py**: 208.32ms
* **tests/test_cdo.py**: 179.16ms
* **tests/test_cte.py**: 178.39ms
* **tests/test_attention.py**: 201.65ms
* **tests/test_question_lifecycle.py**: 183.4ms
* **tests/test_event_bus.py**: 171.31ms
* **tests/test_student_twin.py**: 227.64ms
* **tests/test_parent_twin.py**: 204.41ms
* **tests/test_school_admin_twin.py**: 213.83ms
* **tests/test_research_analytics_twin.py**: 220.78ms
* **tests/test_production_hardening.py**: 4161.93ms
* **tests/test_pilot_dataset.py**: 1370.63ms
