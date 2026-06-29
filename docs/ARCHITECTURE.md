# Cognify v3.0 Architecture Guide

This document describes the platform's multi-layered cognitive architecture, data flows, and design principles.

---

## 1. Modular Platform Layers

Cognify is structured as a decoupled cognitive operating system composed of five main layers:

```
┌─────────────────────────────────────────────────────────┐
│              Research & Analytics Layer (RAT)           │
├─────────────────────────────────────────────────────────┤
│                    Digital Twins Layer                  │
├─────────────────────────────────────────────────────────┤
│               Cognitive Event Bus (CEB)                 │
├─────────────────────────────────────────────────────────┤
│                 Cognitive Engines Layer                 │
├─────────────────────────────────────────────────────────┤
│                      Database Layer                     │
└─────────────────────────────────────────────────────────┘
```

### Database Layer (Append-Only Event Store)
All platform activity is persisted as immutable domain events inside the `event_store` table. This provides a complete audit trail for state transitions.

### Cognitive Engines Layer
Includes internal ML models and heuristics that calculate student cognitive metrics:
- **Memory Engine**: Computes memory half-life decay and state transitions.
- **QQI Engine**: Estimates question template discrimination and difficulty metrics.
- **NBIRT Engine**: Item Response Theory estimation.
- **Cognitive Load Engine (CCLI)**: Estimates mental effort load during quiz response inputs.
- **Attention Engine**: Measures focus states.
- **Decision Engine (CDO)**: Aggregates indicators to output recommendation decisions.

### Cognitive Event Bus (CEB)
A structured event broker directing messages from producers (engines) to consumers (twins & other engines) based on permission configurations mapped in `event_registry.py`.

### Digital Twins Layer
Maintains student, teacher, parent, and administrator projections:
- **Student Twin**: Tracks personal progress dashboards.
- **Teacher Twin**: Class heatmaps and prioritization queues.
- **Parent Twin**: Translates raw states to parent summaries.
- **School Admin Twin**: School-wide coverage, usage, and curriculum reports.

### Research & Analytics Twin (RAT)
Surfaces learning science evidence without modifying student profile states.

---

## 2. CQRS Pattern & Replayability
- **Write Path**: Telemetry processed by Cognitive Engines is published onto the CEB and persisted in `event_store`.
- **Read Path**: Digital Twins construct read-only projections by subscribing to relevant events.
- **Replayability**: If database projections are corrupted, they can be entirely reconstructed by replaying event logs in safe chronological order using `event_replay` modules.
