# ADR 004: Why Random Forest for Strategy Prediction?

## Status
Accepted

## Context
We need to predict the cognitive strategy a student uses (e.g., memory recall vs. conceptual reasoning) based on telemetry.

## Decision
We use Random Forest over deep learning (like MLP or LSTM) for this specific task because the feature space (confidence + reflection timings) is small, highly non-linear, and requires high explainability.

## Consequences
- Model inferences can be directly traced back to feature splits (e.g., "High hesitation + correct answer -> overthinking").