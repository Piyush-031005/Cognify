# Changelog

All notable changes to the Cognify platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

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
