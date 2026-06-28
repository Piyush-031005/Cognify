# Changelog

All notable changes to the Cognify platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

## [1.8.0] - 2026-06-28

### Added (Week 9 — Context Engine v2.0)
- **Stateless Recommendation Engine** (`context_engine.py`): Generates personalized concept recommendations per student with deterministic, reproducible scoring.
- **Eligibility / Conflict Resolution Gate**: Hard blocking rules applied before scoring — unmet prerequisites (Forgotten/At Risk state), teacher-blocked concepts, recently-completed concepts, and concepts already at Mastered state are excluded.
- **Multi-Signal Scoring Formula**: Each concept's score is computed from six weighted components — Educational Memory (retention × mastery), APD prerequisite readiness, Misconception penalty, QQI calibration alignment, Teacher Priority override, and Curriculum/Exam weight.
- **Context Multipliers**: `session_start_hour`, `device_type`, `network_quality` telemetry signals applied as multiplicative context multipliers with graceful fallback (`context_quality` field: FULL/PARTIAL/FALLBACK).
- **Explainability Trace**: Every recommendation includes `score_breakdown`, `context_quality`, `missing_signals`, `confidence`, and `confidence_reason` fields for full teacher auditability.
- **Configuration-Driven Weights**: All scoring weights and multipliers live in `context_recommendations_config` table; no hard-coded values in engine logic.
- **New API Endpoints**:
  - `POST /memory/recommendations` — Generate ranked recommendations for a student
  - `GET /memory/recommendations/config` — View all active scoring configuration
  - `POST /memory/recommendations/config` — Update scoring configuration at runtime
- **DB Migrations**: `recommendations_log` enriched with 9 metadata columns; `context_recommendations_config` table created and seeded with defaults.
- **Integration Tests**: 12 tests in `tests/test_context_engine_v2.py` covering scoring, eligibility gating, determinism, context fallback, and API endpoints.

## [1.7.0] - 2026-06-28

### Added (Week 8 — Educational Memory v2.0)
- **Event Sourcing Architecture**: `memory_events` is now the append-only, immutable source of truth. Every interaction appends an immutable event with full provenance metadata (`event_version`, `source_module`, `algorithm_version`, `qqi_version`, `twin_version`, `config_version`).
- **Deterministic Projector**: `project_concept_memory()` replays all events for a `(student, concept)` pair deterministically to rebuild `concept_memory`. Rule 11 guaranteed: identical events + identical config → identical final state.
- **Memory State Machine**: Six-state machine (`Unknown → Learning → Stable → At Risk → Forgotten → Recovered`) driven strictly by evidence. No direct jumps. All transitions logged in `memory_state_transitions`.
- **Ebbinghaus Decay Engine**: Retrieval strength `R(t) = e^(−t·f/S)`, next review scheduling via `t = S·ln(1/R_threshold)/f`, and 7/14/30-day decay predictions with uncertainty estimates.
- **Explainability**: `concept_memory.memory_explanation` stores human-readable JSON rationale (positives, negatives, decay_days, decay_retrieval_strength).
- **Provenance Tracking**: Every projection records `derived_from` (list of contributing source modules) and `trigger_event_id`.
- **Alert Generation**: `memory_alerts` table auto-populated when concept enters `At Risk` or `Forgotten` state; `prerequisite_failure` alert raised when a prerequisite concept is forgotten.
- **Dynamic Review Scheduling**: `review_schedule` updated on every projection with configurable priority formula: `priority = memory_risk + misconception_severity + prerequisite_importance + teacher_priority + exam_weight`.
- **Configuration Versioning**: All thresholds and weights stored in `memory_config` with `config_version`. No hardcoded weights anywhere.
- **REST API Suite** (`/memory/...`):
  - `GET /memory/student/<student>` — full longitudinal profile (mastered/at_risk/forgetting/misconceptions)
  - `GET /memory/concept/<student>/<concept>` — projection detail with explainability
  - `GET /memory/review_queue/<student>` — priority-sorted review queue
  - `GET /memory/statistics` — platform-wide aggregated statistics
  - `GET /memory/health` — engine health and config snapshot (computation-only, no business logic)
  - `GET /memory/replay/<student>/<concept>` — full chronological event log + state transition audit (Rule 11 support)
  - `POST /memory/update` — record new memory event and trigger projection
  - `POST /memory/review_complete` — mark scheduled review complete and record outcome
- **Integration Tests**: `tests/test_memory_v2.py` — 35 tests covering DB migration idempotency, event sourcing, state machine, Ebbinghaus decay, deterministic replay, review scheduling, alerts, config isolation, full student profile, and all 8 REST APIs.
- **ADR-011**: Documents Event Sourcing decision for Educational Memory.
- **ADR-012**: Documents `concept_memory` as a derived projection, not source of truth.

### Changed
- `api_student_memory` route (`GET /memory/student/<email>`) upgraded to return standardized `{"status": "success", "data": {...}}` response envelope (backward-compatible).
- `tests/test_memory_integration.py` and `tests/test_qqi_calibration.py` updated to seed v2.0 memory tables (`memory_config`, `memory_events`, `concept_memory`, `memory_state_transitions`, `review_schedule`, `memory_alerts`) in their in-memory mock DBs for regression compatibility.

## [1.6.0] - 2026-06-28

### Added
- Created central test runner `run_regression.py` validating schema migration idempotency, executing all 13 tests sequentially, compiling performance benchmarks, and outputting structured execution reports.
- Created `tests/test_e2e_integration.py` to programmatically verify the end-to-end learning lifecycle (Student Telemetry Ingestion ➔ QQI calculations ➔ Student Mastery Updates ➔ APD Candidate Generation & Approvals ➔ Misconception Discovery & Confirmations ➔ Digital Twin profiles ➔ Recommendations ➔ Recommendation execution logs ➔ Pilot Analytics outcomes evaluation).
- Created `docs/PERFORMANCE_BASELINE.md` establishing runtime baselines for engines, database read/writes, schema migrations, and test suites.
- Created `regression_report.md` artifact representing the detailed cross-module validation and regression status summary.

## [1.5.0] - 2026-06-28

### Added
- Implemented Misconception Discovery v2.0 (Research Grade) with stable misconception cluster identifiers (`mcp_000001` format) and append-only evidence tracking.
- Added multi-dimensional normalized behavioral consistency aggregation (combining hesitation, response time, hovers, and backspaces).
- Implemented four-component explainable confidence engine (Cluster Size, Behavioral Consistency, Mastery Consistency, and Teacher Agreement) dynamically weighted via `misconception_config`.
- Implemented cohort-isolated misconception discovery and cohort severity rating (Low, Medium, High, Critical).
- Added canonical cluster linking, recommended interventions library hooks, and version replication attributes.
- Implemented complete REST API suite under `/misconceptions/...` including statistics, configuration, run, confirmation, rejection, and chronological replay log histories.
- Created ADR-010 detailing the architectural decision of mapping misconceptions to concepts instead of individual questions (Rule #9).
- Created a comprehensive integration test suite `tests/test_misconception_v2.py` with 12 distinct test cases.

### Changed
- Refactored `md_engine.py` to support v2.0 explainable clustering, backward-compatible default fallback options, and automated promotions to Knowledge Graph tables on teacher confirmation.

## [1.4.0] - 2026-06-28

### Added
- Implemented APD v2.0 (Research Grade) with stable edge identifiers (`apd_000001` format) and append-only evidence logging.
- Added four-component confidence aggregation engine (Statistical Evidence, Teacher Validation, Historical Stability, Sample Reliability) dynamically weighted via `apd_config`.
- Implemented exponential temporal confidence decay: $C_{new} = C_{prev} \times e^{-\lambda \times days}$.
- Added cohort-isolated prerequisite discovery and sample-size weighted cohort aggregation.
- Implemented a complete REST API suite for APD under `/apd/...` to fetch configuration, candidates, detailed evidence, confidence replay histories, statistics, and validate actions.
- Performed DB schema migration on `responses` table to add `selected_option` and `correct_option` columns supporting misconception discovery.
- Added comprehensive integration test suite `tests/test_apd_v2.py` verifying all APD v2.0 specifications.

### Changed
- Refactored `apd_engine.py` to support append-only updates and dynamic database-backed configurations.
- Exposed a backward-compatible `config` dict wrapper in `apd_engine.py` to prevent regression on existing tests.
- Updated `tests/test_apd_integration.py` and `tests/test_apd_step2.py` to align with the new exponential decay and overall confidence aggregation.

## [1.3.1] - 2026-06-28

### Added
- Added `PROJECT STATUS` section to `docs/PROJECT_CONTEXT.md` to establish rules and active constraints for future sprint phases.
- Added `confidence_delta` column to `kg_evolution_log` table in `database.py`.

### Fixed
- Fixed closed-database connection issues in `tests/test_apd_integration.py`, `tests/test_apd_step2.py`, and `tests/test_md_integration.py` by wrapping in-memory connections in custom wrappers that ignore `.close()` calls during module imports.
- Fixed test suite state pollution in `test_apd_integration.py` by clearing candidate tables before starting the duplicate edge test case.
- Fixed query assertions in `test_md_integration.py` to target newly discovered `'candidate'` misconceptions instead of pre-seeded production misconception nodes.
