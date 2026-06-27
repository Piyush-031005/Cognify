# ADR 009: Why Statistical Discovery (KL) before Causal ML (PC)?

## Status
Accepted

## Context
We need APD to run reliably on early pilot data. Deep causal discovery (like PC algorithm) requires massive sample sizes to be stable.

## Decision
V1 of APD uses KL Divergence and Mutual Information.

## Consequences
- Works on smaller datasets (min 50 students).
- Computationally cheap.
- Establishes the pipeline before scaling to complex causal graphs.