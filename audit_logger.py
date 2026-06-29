"""
audit_logger.py
Week 23 — Central Audit Logging System (Refinement 3).
"""

import json
import datetime
from database import get_conn

def log_mutation(
    actor, role, action, resource, 
    old_value=None, new_value=None, reason=None,
    event_id=None, request_id=None, correlation_id=None,
    ip_address=None, user_agent=None, duration_ms=None
):
    """
    Saves an immutable audit log record to the database (Decision 3 & Refinement 3).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        now_str = datetime.datetime.now().isoformat()
        
        # Serialize dicts/objects to JSON strings if needed
        old_val_str = json.dumps(old_value) if isinstance(old_value, (dict, list)) else (str(old_value) if old_value is not None else None)
        new_val_str = json.dumps(new_value) if isinstance(new_value, (dict, list)) else (str(new_value) if new_value is not None else None)

        cur.execute("""
            INSERT INTO audit_logs (
                actor, role, action, resource, old_value, new_value, reason, timestamp,
                request_id, correlation_id, event_id, ip_address, user_agent, duration_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            actor, role, action, resource, old_val_str, new_val_str, reason, now_str,
            request_id, correlation_id, event_id, ip_address, user_agent, duration_ms
        ))
        conn.commit()
    except Exception as e:
        # Avoid crashing application if audit logging fails (log to stderr)
        import sys
        print(f"[AUDIT LOG ERROR] Failed to write mutation log: {e}", file=sys.stderr)
    finally:
        conn.close()

def get_audit_logs(limit=100, offset=0):
    """Retrieves list of audit logs (Super Admin only)."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT * FROM audit_logs 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
