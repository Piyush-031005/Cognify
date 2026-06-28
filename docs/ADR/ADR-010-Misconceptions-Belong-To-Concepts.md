# ADR-010: Misconceptions Belong to Concepts, Not Questions

## Status
Proposed

## Context
In previous iterations of the Cognify platform, misconceptions were tied directly to individual questions (assessment items). However, this creates a tight coupling between specific questions and the overall cognitive model. If a question is retired, edited, or added, the associated misconception tracking must be updated, causing index fragmentation and losing historical alignment of student cognitive profiles.

To build a robust startup data moat and support the future Cognition Foundation Model (CogFM), misconceptions must represent fundamental cognitive gaps rather than specific testing instruments.

## Decision
We establish **Cognify Rule #9**: **Misconceptions belong to concepts, not assessment items.**

Under this decision:
1. **Questions remain measurement instruments**: A student's wrong response to a question serves as telemetry to detect a misconception, but the misconception itself is structurally attached to the underlying academic concept.
2. **Concepts remain the source of truth**: The living Knowledge Graph contains concepts as core nodes. Validated misconceptions are promoted as child nodes of these concept nodes.
3. **Cluster mapping**: Different questions that test the same concept and reveal the same underlying misunderstanding are grouped together into a single, canonical misconception cluster.

## Consequences
* **Decoupled Architecture**: Questions can be dynamically added, updated, or removed from the question bank without invalidating the Knowledge Graph or student memory profiles.
* **Explainability**: Misconceptions now represent general learning gaps (e.g., "0-based indexing shift") rather than question-specific errors.
* **CogFM Compatibility**: Standardizing misconceptions under concepts provides clean, normalized input data for training future foundational learning models.
