# ADR 001: Why SQLite for Production?

## Status
Accepted

## Context
Educational telemetry systems require high write throughput. Normally, this implies PostgreSQL or NoSQL. However, Cognify needs to be easily deployable on single-node instances for school premises (School Twin).

## Decision
We use SQLite in WAL (Write-Ahead Logging) mode with `busy_timeout=5000`.

## Consequences
- **Pros:** Zero-configuration, zero-network latency, easy to backup (single file), highly portable for localized school deployments.
- **Cons:** Multi-node horizontal scaling is difficult. Requires careful connection management to avoid `database is locked` errors during heavy concurrent test execution.