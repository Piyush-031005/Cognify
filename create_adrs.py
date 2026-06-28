import os

adrs = {
    "ADR-001-Why-SQLite.md": """# ADR 001: Why SQLite for Production?

## Status
Accepted

## Context
Educational telemetry systems require high write throughput. Normally, this implies PostgreSQL or NoSQL. However, Cognify needs to be easily deployable on single-node instances for school premises (School Twin).

## Decision
We use SQLite in WAL (Write-Ahead Logging) mode with `busy_timeout=5000`.

## Consequences
- **Pros:** Zero-configuration, zero-network latency, easy to backup (single file), highly portable for localized school deployments.
- **Cons:** Multi-node horizontal scaling is difficult. Requires careful connection management to avoid `database is locked` errors during heavy concurrent test execution.""",

    "ADR-002-Why-Knowledge-Graph.md": """# ADR 002: Why a Living Knowledge Graph?

## Status
Accepted

## Context
Traditional LMS uses a flat list of tags or topics. This fails to capture the causal dependencies of learning (e.g., you cannot learn arrays without pointers).

## Decision
We model educational concepts as a directed acyclic graph (DAG) where nodes are concepts/misconceptions and edges are prerequisites/relationships. The graph is "Living", meaning it evolves based on student interaction telemetry rather than being statically defined by experts.

## Consequences
- Allows predictive diagnostic reasoning.
- Enables Automatic Prerequisite Discovery.
- Becomes the primary startup moat.""",

    "ADR-003-Why-QQI.md": """# ADR 003: Why Question Quality Index (QQI)?

## Status
Accepted

## Context
Standard psychometrics (Facility Index, Discrimination Index) only look at correct/incorrect answers.

## Decision
We developed QQI, a multi-signal metric combining classical psychometrics with behavioral telemetry (response time, hover patterns, backspace count).

## Consequences
- We can detect "tricky" questions that students guess correctly.
- Questions are actively quarantined if their behavioral signature indicates poor quality.""",

    "ADR-004-Why-Random-Forest.md": """# ADR 004: Why Random Forest for Strategy Prediction?

## Status
Accepted

## Context
We need to predict the cognitive strategy a student uses (e.g., memory recall vs. conceptual reasoning) based on telemetry.

## Decision
We use Random Forest over deep learning (like MLP or LSTM) for this specific task because the feature space (confidence + reflection timings) is small, highly non-linear, and requires high explainability.

## Consequences
- Model inferences can be directly traced back to feature splits (e.g., "High hesitation + correct answer -> overthinking").""",

    "ADR-005-Why-EWMA.md": """# ADR 005: Why Exponential Weighted Moving Average (EWMA) for Evidence Fusion?

## Status
Accepted

## Context
Student cognitive states are volatile and affected by noise (e.g., a student guessing one question correctly).

## Decision
We use EWMA to smooth cognitive state updates in the Digital Twin. `New_State = alpha * Observation + (1-alpha) * Old_State`.

## Consequences
- Prevents drastic jumps in inferred student ability.
- Requires tuning of the alpha parameter based on empirical pilot data.""",

    "ADR-006-Automatic-Prerequisite-Discovery.md": """# ADR 006: Automatic Prerequisite Discovery (APD)

## Status
Accepted

## Context
Manual curation of knowledge graphs is expensive and subjective. 

## Decision
We use student struggle telemetry to automatically infer prerequisite relationships between concepts.

## Consequences
- The knowledge graph scales autonomously.
- Edge creation is statistically backed.""",

    "ADR-007-Why-Human-Validation.md": """# ADR 007: Why Human-in-the-Loop Validation?

## Status
Accepted

## Context
AI can confidently discover relationships that are statistically valid but pedagogically unsound (e.g., correlations due to alphabetical order of teaching).

## Decision
No AI-discovered edge enters production automatically. Teachers must validate them.

## Consequences
- Builds trust with educators.
- Provides a source of ground-truth labels (accept/reject) for future model training.""",

    "ADR-008-Why-Candidate-Edge-Pipeline.md": """# ADR 008: Why a Candidate Edge Pipeline?

## Status
Accepted

## Context
APD can generate thousands of potential edges.

## Decision
Edges are created in a 'candidate' state, prioritized by KL Divergence confidence, and queued for human review.

## Consequences
- Prevents graph pollution.
- Requires a dedicated UI for teachers to review graph candidates.""",

    "ADR-009-Why-Statistical-Discovery-First.md": """# ADR 009: Why Statistical Discovery (KL) before Causal ML (PC)?

## Status
Accepted

## Context
We need APD to run reliably on early pilot data. Deep causal discovery (like PC algorithm) requires massive sample sizes to be stable.

## Decision
V1 of APD uses KL Divergence and Mutual Information.

## Consequences
- Works on smaller datasets (min 50 students).
- Computationally cheap.
- Establishes the pipeline before scaling to complex causal graphs."""
}

os.makedirs(r'f:\Cognify\docs\ADR', exist_ok=True)
for filename, content in adrs.items():
    with open(os.path.join(r'f:\Cognify\docs\ADR', filename), 'w', encoding='utf-8') as f:
        f.write(content)
print("Created 9 ADRs.")
