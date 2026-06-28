# ADR-012: Concept Memory Is a Derived Projection

**Status:** Accepted  
**Date:** 2026-06-28  
**Sprint:** Week 8 – Educational Memory v2.0  
**Author:** Cognify CTO Review

---

## Context

After adopting Event Sourcing (see ADR-011), Cognify needed a strategy for how to serve read queries about a student's current cognitive state efficiently. Two options exist:

1. **Project on every read**: Replay all `memory_events` for a `(student, concept)` pair on every API call.
2. **Materialized projection**: Maintain a derived `concept_memory` table that is rebuilt after every write, and serve reads directly from that table.

Option 1 is mathematically pure but operationally expensive — a student with 200 events per concept would require 200 event replays per read request, which is unacceptable for a real-time recommendation engine.

---

## Decision

**`concept_memory` is a materialized projection, not a source of truth.**

Rules:

1. `concept_memory` is **never written directly**. The only path to update `concept_memory` is through the projector function `project_concept_memory()`, which is called after every `memory_events` append.
2. `concept_memory` stores the **current derived state** of Ebbinghaus parameters (S, f), memory_state, explainability, next review date, and config version.
3. Any query that needs the current memory state reads from `concept_memory` (O(1)) — not from a replay.
4. Replay queries (audit, debugging, research) use `GET /memory/replay/<student>/<concept>` which directly reads `memory_events` and `memory_state_transitions`.

### Projection Schema

`concept_memory` stores:

| Column | Description |
|---|---|
| `memory_strength` | Current storage strength S |
| `forgetting_rate` | Current decay rate f |
| `memory_state` | Current state machine state |
| `memory_confidence` | Evidence confidence (0.0–1.0) |
| `memory_explanation` | JSON explainability breakdown |
| `derived_from` | JSON list of source modules that contributed |
| `trigger_event_id` | ID of last `memory_events` row that triggered this projection |
| `config_version` | Config snapshot version used during projection |
| `reinforcement_count` | Total number of events processed |
| `retrieval_success_rate` | successes / total reinforcements |
| `next_review_date` | Calculated from Ebbinghaus schedule formula |
| `last_updated` | Timestamp of last projection |

### Projection Invariants

- `ON CONFLICT(student_email, concept_id) DO UPDATE` ensures only one row per student-concept pair.
- Every projection overwrites ALL derived fields — no partial updates.
- The `config_version` field records which config snapshot was used, enabling audit of how configuration changes affected projections.

---

## Consequences

### Positive

- **O(1) read access** to current memory state without replay overhead.
- **Explainability is persisted** — teachers can inspect WHY a state was derived without running a full replay.
- **Config versioning** — the projection records which config was in effect, supporting research comparisons across config changes.

### Negative

- **Dual-write complexity**: every event write triggers a projection write. If the projection fails, the event is still persisted (event sourcing guarantee preserved), but `concept_memory` may be stale.
- **Stale projections**: If `project_concept_memory()` crashes mid-write, concept_memory may lag. On next read, the API re-triggers projection before returning.

### Mitigations

- `GET /memory/concept/<student>/<concept>` automatically re-triggers projection if no `concept_memory` row exists.
- All projection writes are wrapped in transactions — either the full projection commits or it rolls back.
- Integration tests verify that identical events produce identical projection states (Rule 11).

---

## References

- [ADR-011](./ADR-011-Educational-Memory-Uses-Event-Sourcing.md) — Event Sourcing decision
- [memory_engine.py](../../memory_engine.py) — Projector implementation
- Rule 11: "Educational Memory is deterministic. Given identical memory_events and identical configuration, replay must always produce an identical concept_memory state."
