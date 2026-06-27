# ADR 002: Why a Living Knowledge Graph?

## Status
Accepted

## Context
Traditional LMS uses a flat list of tags or topics. This fails to capture the causal dependencies of learning (e.g., you cannot learn arrays without pointers).

## Decision
We model educational concepts as a directed acyclic graph (DAG) where nodes are concepts/misconceptions and edges are prerequisites/relationships. The graph is "Living", meaning it evolves based on student interaction telemetry rather than being statically defined by experts.

## Consequences
- Allows predictive diagnostic reasoning.
- Enables Automatic Prerequisite Discovery.
- Becomes the primary startup moat.