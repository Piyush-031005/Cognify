# Changelog

All notable changes to the Cognify platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

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
