# Cognify v3.0 Database Schema

This document details the SQLite database schemas, transaction tables, and read-only projection tables.

---

## 1. Append-Only Store (Ledger)

### `event_store`
Holds all historical published domain events.
- `event_id` (TEXT PRIMARY KEY): Unique identifier.
- `event_type` (TEXT NOT NULL): Event name (e.g. `MemoryUpdated`).
- `entity_type` (TEXT): Entity type affected.
- `entity_id` (TEXT): Entity ID affected.
- `entity_sequence` (INTEGER NOT NULL): Sequential index.
- `producer` (TEXT): Issuing service name.
- `payload_json` (TEXT): JSON representation of the payload.
- `created_at` (TEXT): ISO timestamp.

---

## 2. Core Projections

### `student_profile_projection`
Active summary of a student's cognitive progress.
- `student_email` (TEXT PRIMARY KEY)
- `strengths_json` (TEXT NOT NULL)
- `weaknesses_json` (TEXT NOT NULL)
- `memory_health_json` (TEXT NOT NULL)
- `cognitive_health_score` (REAL)

### `student_recommendation_history`
History of recommendations generated for a student.
- `id` (TEXT PRIMARY KEY)
- `student_email` (TEXT NOT NULL)
- `recommendation` (TEXT NOT NULL)
- `priority_score` (REAL NOT NULL)
- `confidence` (REAL NOT NULL)
- `status` (TEXT DEFAULT 'PENDING')
- `generated_at` (TEXT NOT NULL)

---

## 3. Production Hardening Tables

### `audit_logs`
Immutable log of all mutation operations (Week 23).
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `actor` (TEXT NOT NULL): Email of user.
- `role` (TEXT NOT NULL): Role of user.
- `action` (TEXT NOT NULL): Mutating action.
- `resource` (TEXT NOT NULL): Affected resource.
- `old_value` / `new_value` (TEXT)
- `reason` (TEXT)
- `request_id` / `correlation_id` (TEXT)
- `duration_ms` (INTEGER)
- `timestamp` (TEXT NOT NULL)
