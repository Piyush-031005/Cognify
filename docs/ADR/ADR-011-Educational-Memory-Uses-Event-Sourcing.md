# ADR-011: Educational Memory Uses Event Sourcing

**Status:** Accepted  
**Date:** 2026-06-28  
**Sprint:** Week 8 – Educational Memory v2.0  
**Author:** Cognify CTO Review

---

## Context

Cognify needed a longitudinal cognitive tracking layer that could:

1. Track how individual students' knowledge of a concept evolves over weeks and months.
2. Allow complete audit of every state change that has ever affected a student's memory profile.
3. Support deterministic replay of any student's memory history (Rule 11).
4. Remain backward-compatible with the platform's existing QQI, Misconception Discovery, and APD modules.

The naive approach would be a mutable `concept_memory` row that is updated in place whenever a student interacts with a concept. This would:

- Make audit trails impossible.
- Break determinism — the current state would depend on the update order.
- Prevent replay of historical states.
- Violate Cognify's architectural principle: **Raw telemetry is immutable**.

---

## Decision

**Educational Memory will use Event Sourcing as its core architectural pattern.**

Specifically:

- **`memory_events`** is the **append-only, immutable source of truth**. Every interaction (correct answers, wrong answers, misconception events, review completions) is recorded as an event with full provenance metadata.
- **`concept_memory`** is a **derived projection** — a materialized read-cache rebuilt deterministically from `memory_events`. It is never directly written without a preceding `memory_events` append.
- The projector function `project_concept_memory()` replays all events for a given `(student, concept)` pair in timestamp order to recompute the current cognitive state.
- Configuration is stored in `memory_config`, not hardcoded. All Ebbinghaus parameters are read from the database at runtime.

### Key Properties

| Property | Description |
|---|---|
| **Append-only** | `memory_events` is never modified or deleted |
| **Deterministic** | Same events + same config → identical final state (Rule 11) |
| **Provenance** | Every event records `source_module`, `algorithm_version`, `config_version` |
| **Replayable** | Full event + transition log exposed via `GET /memory/replay/<student>/<concept>` |
| **Explainability** | `concept_memory.memory_explanation` contains human-readable rationale |

---

## Consequences

### Positive

- **Full audit trail**: Every state change traceable to a specific event and timestamp.
- **Deterministic replay**: Debug any student's history by replaying events.
- **Research-grade**: Event log provides a longitudinal dataset for future CogFM training.
- **Safe debugging**: Production memory states can be reproduced in staging.

### Negative

- **Additional write cost**: Every interaction writes to `memory_events` AND triggers a projection update on `concept_memory`.
- **Projection must stay in sync**: Any direct modification to `concept_memory` without a preceding event would corrupt the audit trail.

### Mitigations

- `ON CONFLICT DO UPDATE` in the `concept_memory` INSERT prevents duplicate rows.
- The `project_concept_memory()` projector is idempotent — calling it multiple times with the same input produces the same output.
- Tests verify both append-only behavior and idempotency.

---

## Alternatives Considered

| Alternative | Reason Rejected |
|---|---|
| Mutable `concept_memory` row only | No audit trail, no replay, breaks Rule 11 |
| Time-series DB | Over-engineering; SQLite with append-only tables is sufficient |
| Pure in-memory projection on every request | Too slow for large event histories; `concept_memory` cache balances correctness and performance |
