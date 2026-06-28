# ADR-013: Context Engine v2.0 Architecture

**Status:** Proposed  
**Date:** 2026-06-28  
**Sprint:** Week 9 – Context Engine v2.0  
**Author:** Cognify Technical Co-founder & CTO  

---

## Context

In Cognify v1.0, the recommendation system was a simple, stateless rule-based engine that mapped student memory states directly to three generic action types: Remediation, Review, and Practice. It had several critical limitations:
1. **Context-Insensitivity:** It suggested heavy remediation content (like videos) even if the student was on a mobile device or a poor cellular connection, causing timeouts and user frustration.
2. **Pedagogical Blindness:** It did not consider structural dependencies (from APD), misconception clusters, teacher reviews, or exam weightings.
3. **No Explainability:** Recommendations were presented without a trace explaining *why* they were generated.
4. **No Conflict Resolution:** Suggesting practice on a concept when the prerequisite is completely unmastered (or has active misconceptions) creates cognitive overload.

To address these, the **Context Engine v2.0** must ingest all cross-module states (Educational Memory, APD, Misconception clusters, QQI, Teacher notes, Exam blueprints) and adjust recommendation priority based on **environmental context signals** (device type, network quality, time of day, class size).

---

## Decision

We will implement **Context Engine v2.0** as a stateless orchestrator with the following design patterns:

1. **Unified Context Scoring Pipeline:** Recommendations will be scored using a multi-factor linear equation combining core cognitive risks, adjusted by multiplicative context filters.
2. **Context-Driven Action Selection:** The system will dynamically select the appropriate delivery format based on environment signals:
   - **Network Quality (Poor, Average, Good, Excellent):** If network is Poor, filter out rich media (video, heavy assets) and fall back to low-bandwidth text-based practice.
   - **Device Type (Mobile, Tablet, Desktop):** If device is Mobile, prioritize short-form micro-quizzes or audio flashcards instead of long reading or complex interactive tools.
   - **Session Start Hour (0-23):** If time is late at night (e.g. 21:00 - 06:00), prioritize low-cognitive-load reviews. If during school hours (08:00 - 15:00), prioritize teacher-aligned topics.
   - **Class Size / Concurrency:** If class size is large, prioritize self-guided practice. If individual, suggest deeper diagnostic tasks.
3. **Traceability and Explainability:** Every recommendation payload must expose a `recommendation_trace` detailing:
   - The exact contributions of each factor (Memory, APD, Misconception, Teacher, Exam).
   - The active context multipliers applied.
   - A localized, human-readable justification for the teacher dashboard.
4. **Pre-flight Telemetry Audit Integration:** Since a production database audit revealed that `device_type` and `network_quality` are currently unpopulated (0 rows in `pilot_sessions` and `raw_telemetry_events`) and `session_start_hour` and `class_size` do not exist in the active schema, the engine will use **robust default fallback states** (e.g., Desktop device, Excellent network, standard school hour, average class size) until telemetry starts collecting them.

---

## Schema Changes

We will introduce a `context_recommendations_config` table to hold the weights and multipliers, ensuring the scoring engine is entirely database-configured and contains no hardcoded weights:

```sql
CREATE TABLE IF NOT EXISTS context_recommendations_config (
    key TEXT PRIMARY KEY,
    value REAL,
    config_version TEXT DEFAULT 'v2.0',
    updated_at TEXT
);
```

We will also update `recommendations_log` to capture context metadata, scoring breakdown, and explanation traces:

```sql
ALTER TABLE recommendations_log ADD COLUMN context_device_type TEXT DEFAULT 'desktop';
ALTER TABLE recommendations_log ADD COLUMN context_network_quality TEXT DEFAULT 'excellent';
ALTER TABLE recommendations_log ADD COLUMN context_session_hour INTEGER DEFAULT 10;
ALTER TABLE recommendations_log ADD COLUMN context_class_size INTEGER DEFAULT 25;
ALTER TABLE recommendations_log ADD COLUMN scoring_breakdown TEXT; -- JSON string
ALTER TABLE recommendations_log ADD COLUMN config_version TEXT DEFAULT 'v2.0';
```

---

## Consequences

### Positive
- **Wow Factor:** Deliver customized, bandwidth-appropriate learning tasks, enhancing UX and preventing session crashes in schools with poor connectivity.
- **Pedagogically Sound:** Resolves recommendation conflicts (e.g., blocks practice on advanced concepts if a prerequisite has an active misconception).
- **Audit-ready:** Explains recommendations to teachers and administrators, enhancing the platform's defensibility.

### Negative
- **Stateless Orchestration Latency:** Pulling from multiple databases (Memory, Misconceptions, APD, Blueprints) increases read latency.
- **Mitigation:** We will implement structured fallback checks, transaction isolation (read-only), and query optimizations.

---

## Alternatives Considered
- **ML-based Collaborative Filtering:** Rejected because of Rule #8 (Evidence Before Intelligence). In the absence of massive clean historical recommendation telemetry, a deterministic, configurable heuristic formula is much safer and more explainable.
