# ADR 008: Why a Candidate Edge Pipeline?

## Status
Accepted

## Context
APD can generate thousands of potential edges.

## Decision
Edges are created in a 'candidate' state, prioritized by KL Divergence confidence, and queued for human review.

## Consequences
- Prevents graph pollution.
- Requires a dedicated UI for teachers to review graph candidates.