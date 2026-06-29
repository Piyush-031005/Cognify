# Changelog

All notable changes to the Cognify platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

## [2.7.0] - 2026-06-29

### Added (Week 18 — Teacher Twin)
- **Modular Policy Engine Structure**: Structurally segregated the engine into four submodules: `aggregator.py`, `intervention.py`, `overrides.py`, and `reports.py` under the `teacher_twin/` subfolder package.
- **CQRS Projection Queries**: Confined normal dashboard/API requests strictly to local projection tables (`teacher_classroom_retention`, `teacher_intervention_queue`, `teacher_engagement_summary`, `teacher_override_history`, `teacher_recommendation_history`), bypassing raw cognitive tables.
- **Recommendation Status Lifecycle**: Implemented status lifecycle transitions (`PENDING`, `VIEWED`, `ACCEPTED`, `REJECTED`, `EXPIRED`) instead of binary accepted/ignored columns.
- **Explainability Evidence Snapshot**: Added `evidence_snapshot_json` capturing immutable cognitive parameters at recommendation generation.
- **Safe Replay Rebuilds**: Programmed `rebuild_projections()` which truncates projection records and safely replays historical events sequentially.
- **Urgency Priority Score**: Decoupled `priority_score` (urgency/impact) from `confidence` (predictive certainty).
- **New REST API Endpoints**: Bound `/teacher/override`, `/teacher/rebuild`, and `/rooms/<room_id>/report` routes.

## [2.6.0] - 2026-06-29

### Added (Week 17 — Cognitive Event Bus)
- **Cognitive Event Bus (CEB)**: Established an event-driven pub/sub communication backbone (`event_bus.py`, `event_dispatcher.py`, `event_registry.py`) decoupling cognitive engines.
- **At-Least-Once Delivery & Idempotency**: Implemented `processed_events` idempotency ledger preventing duplicate event executions.
- **Entity Sequence Numbering**: Incremented `entity_sequence` monotonically per entity inside `event_store` to guarantee chronological replaying.
- **Metadata Separation**: Split `metadata_json` (correlation/causation/trace ids) from `payload_json` (raw domain parameters).
- **Dead Letter Queue (DLQ)**: Routed failed handler events to `dead_letter_events` after exactly 3 execution retries.
- **Versioned Subscriptions**: Keyed subscriptions using `schema_version` to support clean downstream evolutionary versions.
- **Chronological Replay (SAFE & LIVE modes)**: Added `event_replay.py` querying historical event sequences. `SAFE` mode isolates side effects and blocks downstream cascading publishes.
- **New REST API Endpoints**: Bound `/events/publish`, `/events/replay`, `/events`, `/events/history`, and `/events/subscriptions` endpoints in Flask.

## [2.5.0] - 2026-06-29

### Added (Week 16 — Question Blueprint & Lifecycle Engine)
- **Question Blueprint & Lifecycle Engine (QBL)**: Built a complete question genome module (`question_lifecycle_engine.py`) supporting templates/blueprints, families, lineages, and parent-version psychometric prior inheritance.
- **Blueprint Versioning**: Added `blueprint_version` tracking parameter inside the blueprint templates.
- **Drift Calculations & Authoritative Source**: Computes psychometric drifts (time and difficulty differences) and maintains QQI/NBIRT as the single source of truth.
- **Retirement Evidence Ledger**: Logged retirement metrics dynamically (`retirement_metrics_json`) on question version retirement.
- **Lineage Ancestor Caching**: Cached ancestor path string (`ancestor_path`) in versions to support $O(1)$ lineages.
- **Lifecycle Status Filtration**: Updated context recommendation loaders to only fetch `'Active'` or `'Calibration'` questions.
- **New REST API Endpoints**: Exposed routes for version creation, promotes, retirements, lineage hierarchies, and family details.

## [2.4.0] - 2026-06-29

### Added (Week 15 — Attention & Circadian Intelligence)
- **Attention & Circadian Intelligence (ACI)**: Formulated an inference module (`attention_engine.py`) calculating instantaneous focus scores, session fatigue, dynamic circadian factors, and EWMA attention decay.
- **Config-Driven Circadian Intervals**: Supported start/end hour boundaries in `attention_config` to customize circadian multipliers.
- **Attention Confidence Scoring**: Added telemetry completeness metric mapping populated features to confidence ($0.0 - 1.0$).
- **Soft Score Modulation**: Modulated Context Engine recommendations softly: $S_{\text{final}} = S_{\text{base}} \cdot (1 - \lambda) + S_{\text{base}} \cdot (CF \cdot AD) \cdot \lambda$.
- **Continuous Session Streak Tracking**: Parsed raw events to sum continuous study minutes, resetting if breaks are $> 10$ minutes.
- **New REST APIs**: Added endpoints for computation, configuration overrides, and transition logs.

## [2.3.0] - 2026-06-29

### Added (Week 14 — Cross-Platform Cognitive Telemetry Engine)
- **Cross-Platform Cognitive Telemetry Engine (CTE)**: Integrates desktop/Android telemetry normalizing adapters, standardizing mouse movement coordinates, velocity, click coordinates, scrolling velocity, orientation, and focus lost/gained events.
- **Derived Behavior Feature Extractor** (`feature_extractor.py`): Performs processing on raw telemetry to derive high-level interaction entropy, hesitation index, scroll entropy, typing cadence, and focus lost events.
- **Derived Features Cache**: Caches student behavior features in `derived_behavior_features`.
- **CDO Stability & Confidence Calibration**: Upgraded `decision_engine.py` to calculate stability score indicator based on alternative candidate conflict differentials.
- **REST Sync Endpoint**: `POST /telemetry/sync` handles batch upload from offline mobile storage, performing idempotent UUID-checked event insertion.

## [2.2.0] - 2026-06-29

### Added (Week 13 — Cognitive Decision Orchestrator)
- **Cognitive Decision Orchestrator Engine** (`decision_engine.py`): Centralizes and resolves learning recommendation conflicts via a decoupled rule object pipeline (`TeacherRule`, `LoadRule`, `MisconceptionRule`, `APDRule`, `MemoryRule`, `NBIRTRule`).
- **Config-driven Priorities**: Dynamically fetches and resolves rule priorities via the database (`decision_config` table) rather than hardcoding priority sequences.
- **Traceable Explainability & Conflict Logging**: Logs evaluated rule options (`candidates_json`) and discarded candidates (`conflicts_json`) directly into the `decision_explanations` table for auditable compliance.
- **Context Engine Gating**: Filters recommendation candidates against the CDO's final winning action.
- **Policy Versioning**: Stores policy versioning information (`decision_policy_version`) on every run.
- **New API Endpoints**:
  - `POST /decision/run` — trigger the decision pipeline pass manually.
  - `GET /decision/student/<email>` — retrieve a student's active CDO recommendations and audit logs.
  - `GET /decision/history` — fetch recent runs log ledger.
  - `GET/POST /decision/config` — manage rule priorities parameters dynamically.

## [2.1.0] - 2026-06-28

### Added (Week 12 — Cognitive Load Intelligence Engine)
- **Cognitive Load Intelligence Engine** (`cognitive_load_engine.py`): Implements deterministic estimation of Intrinsic Load (IL), Extraneous Load (EL), and Germane Load (GL) post-response.
- **EWMA-Based Rolling State**: Tracks student fatigue status via Exponentially Weighted Moving Average (EWMA) with configurable `ewma_alpha` (default 0.25).
- **Cognitive Recovery Mode**: Context Engine (`context_engine.py`) upgraded with recovery mode blocks (blocking new concept recommendations, prioritizing prerequisite reinforcement, memory review, and lower-difficulty questions $b \le \theta - 0.5$ when student is overloaded).
- **Explainability Payload**: Appends an explainability JSON block containing sub-component score details to every computed cognitive load event.
- **History & Alerts Ledgers**:
  - `cognitive_load_events` — record of raw IL, EL, GL, and CCLI values.
  - `student_cognitive_load_state` — active rolling metrics state per student.
  - `cognitive_load_alerts` — active/resolved fatigue alerts.
  - `cognitive_load_history` — append-only state transition audit ledger.
- **New API Endpoints**:
  - `POST /cognitive-load/compute` — manually trigger load estimation for a response.
  - `GET /cognitive-load/student/<email>/state` — fetch student state, alerts, and history.
  - `GET/POST /cognitive-load/config` — view and manage load config weights and alphas.
- **Safe DB Migrations**: Idempotently creates config, event, state, alert, and history tables and seeds defaults.
- **Integration Tests**: 4 test cases in `tests/test_cognitive_load.py` validating Sweller load calculations, EWMA alerts, and Context Engine gating.

## [2.0.0] - 2026-06-28

### Added (Week 11 — NBIRT: Neural Bayesian Item Response Theory)
- **Neural Bayesian Item Response Theory Engine** (`nbirt_engine.py`): Implements 2-Parameter Logistic (2PL) psychometric item response model (estimating latent difficulty $b$ and discrimination $a$, keeping guessing parameter $c$ fixed to 0.0) via on-demand Expectation-Maximization (EM) loop.
- **Personalized Bayesian Ability Priors**: Fuses student's Educational Memory storage strength and confirmed active misconception count to compute dynamic priors for latent ability $\theta$ estimation.
- **Ability Confidence & Percentile Estimations**: Calculates standard error (SE), reliability/confidence index, and normal CDF ability percentile for each student.
- **Cold Start Protection Gate**: Enforces minimum response threshold per student (`min_items_per_student`) before ability estimation; falls back safely to QQI heuristics when evidence is insufficient.
- **Additive Context Signal**: Context Engine (`context_engine.py`) upgraded with IRT alignment term ($S_{\text{base}} = \dots + w_{\text{irt}} \cdot \text{sigmoid}(-|\theta - b|)$) as a 7th additive recommendation signal, with graceful backward-compatible fallback when student/item IRT statistics are NULL.
- **History ledgers**:
  - `nbirt_runs` — audit log for each EM execution run.
  - `nbirt_item_history` — append-only tracking of difficulty and discrimination parameters.
  - `nbirt_ability_history` — append-only tracking of student abilities, error boundaries, percentiles, and prior parameters used.
- **New API Endpoints**:
  - `POST /nbirt/run` — trigger on-demand batch 2PL EM optimization run.
  - `GET /nbirt/student/<email>/ability` — returns student theta logit, standard error, percentile, confidence, and items used.
  - `GET /nbirt/question/<id>/parameters` — returns question difficulty b, discrimination a, and guessing c.
  - `GET /nbirt/runs` — fetch EM runs ledger logs.
  - `GET/POST /nbirt/config` — view and edit NBIRT parameters.
- **Safe DB Migrations**: Idempotent alterations adding IRT parameters to `question_bank` and `student_cognitive_profiles`, and creating the config, runs, and history ledger tables.
- **Integration Tests**: 9 test suites in `tests/test_nbirt.py` validating 2PL math, EM convergence, prior shifting, misconception penalties, cold starts, and context engine integration.

## [1.9.0] - 2026-06-28

### Added (Week 10 — QQI Calibration Feedback Loop)
- **Closed-Loop QQI Calibration Engine** (`qqi_engine.py`): Dynamically evaluates student question response correctness against active cognitive digital twin storage strength and confidence profiles to calibrate item difficulty and quality metrics.
- **Asynchronous Replay Job Queue** (`replay_jobs`): Prevents SQLite database write locks during bulk student memory updates by enqueuing, staging, and executing projection replays asynchronously. Supported by a state machine (`pending` -> `running` -> `completed` / `failed` -> `retrying`).
- **Calibration Run Ledger** (`calibration_runs`): Establishes a reproducible audit ledger tracking every execution run, configuration parameters, timing metrics, and counts of processed questions, alerts created/resolved, and replay jobs.
- **Calibration Version History** (`qqi_calibration_history`): Append-only database table tracking old/new QQI scores, old/new difficulty levels, and reasoning text for every calibration shift.
- **Automated QQI Alerts** (`qqi_alerts`): Triggers teacher-actionable alerts for questions exhibiting severe calibration drift or falling below configured quarantine thresholds.
- **Closed-Loop Resolution Pipeline**: Resolving alerts (e.g., 'quarantine') updates question status, marks all past student responses to the question as invalidated (appending `response_invalidated` to `memory_events`), and enqueues replay jobs to reconstruct affected student profiles.
- **New API Endpoints**:
  - `POST /qqi/calibrate` — Run full system calibration pass
  - `GET /qqi/alerts` — Fetch active/resolved calibration alerts
  - `POST /qqi/alerts/<id>/resolve` — Resolve a calibration alert
  - `POST /qqi/jobs/process` — Process a batch of pending replay jobs
  - `GET/POST /qqi/config` — View and edit calibration parameters
  - `GET /qqi/runs` — Fetch calibration run history
- **DB Migrations**: Safe, idempotent migrations adding tables for configurations, runs, history, alerts, and replay queue jobs.
- **Integration Tests**: 12 test cases in `tests/test_qqi_feedback_loop.py` validating all states of the calibration engine, replay worker, version history, ledger, and state machine.

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
