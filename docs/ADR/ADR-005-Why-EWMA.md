# ADR 005: Why Exponential Weighted Moving Average (EWMA) for Evidence Fusion?

## Status
Accepted

## Context
Student cognitive states are volatile and affected by noise (e.g., a student guessing one question correctly).

## Decision
We use EWMA to smooth cognitive state updates in the Digital Twin. `New_State = alpha * Observation + (1-alpha) * Old_State`.

## Consequences
- Prevents drastic jumps in inferred student ability.
- Requires tuning of the alpha parameter based on empirical pilot data.