# Cognify v3.0 Administrator Guide

This guide describes operational and maintenance tasks for platform administrators.

---

## 1. User Role Management
Supported user roles:
- `super_admin`: Full system control, trigger database backups/restores, and read audit logs.
- `school_admin`: Access to school-wide metrics, class performance dashboards, and trigger rebuilds.
- `teacher`: Classroom management, feedback submission, and manual student overrides.
- `parent`: Linked child cognitive snapshot dashboards.
- `student`: Submit telemetry and answer assessments.
- `research_viewer`: Analytical access to concept decay and question template discrimination.

---

## 2. Rebuilding Projections
If metrics are out of sync or projection tables drift, trigger a SAFE chronological event replay.
Trigger School Twin rebuild:
```bash
curl -X POST http://localhost:10000/api/v1/admin/school/rebuild \
  -H "Authorization: Bearer <token>"
```
During rebuild, projections are wiped, events are replayed sequentially in SAFE mode, and validation checksums are re-calculated.

---

## 3. Auditing Mutations
Mutation actions write immutable logs to the database. Access audit logs via:
```bash
curl -X GET "http://localhost:10000/api/v1/admin/audit-logs?limit=50" \
  -H "Authorization: Bearer <superadmin_token>"
```
Logs display trace correlation IDs (`request_id`, `correlation_id`) and execution durations.
