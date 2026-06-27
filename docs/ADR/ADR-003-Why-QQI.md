# ADR 003: Why Question Quality Index (QQI)?

## Status
Accepted

## Context
Standard psychometrics (Facility Index, Discrimination Index) only look at correct/incorrect answers.

## Decision
We developed QQI, a multi-signal metric combining classical psychometrics with behavioral telemetry (response time, hover patterns, backspace count).

## Consequences
- We can detect "tricky" questions that students guess correctly.
- Questions are actively quarantined if their behavioral signature indicates poor quality.