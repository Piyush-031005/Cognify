# ADR 007: Why Human-in-the-Loop Validation?

## Status
Accepted

## Context
AI can confidently discover relationships that are statistically valid but pedagogically unsound (e.g., correlations due to alphabetical order of teaching).

## Decision
No AI-discovered edge enters production automatically. Teachers must validate them.

## Consequences
- Builds trust with educators.
- Provides a source of ground-truth labels (accept/reject) for future model training.