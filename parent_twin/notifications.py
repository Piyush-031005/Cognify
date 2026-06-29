"""
parent_twin/notifications.py
Decision 5 — Notification log only in Week 20. Delivery deferred to Week 23.
"""

import json
import uuid
import datetime
from database import get_conn


def log_notification(parent_email: str, student_email: str,
                     notification_type: str, payload: dict = None):
    """
    Appends a notification record to parent_notification_log.
    Does NOT send any email/push — that is Week 23 work.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        now_str = datetime.datetime.now().isoformat()
        cur.execute(
            """
            INSERT INTO parent_notification_log (
                id, parent_email, student_email, notification_type,
                payload_json, sent_at, projection_version
            ) VALUES (?, ?, ?, ?, ?, ?, 'v1.0')
            """,
            (
                str(uuid.uuid4()),
                parent_email,
                student_email,
                notification_type,
                json.dumps(payload or {}),
                now_str,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def mark_report_read(parent_email: str, student_email: str, report_id: str):
    """
    Records a read receipt for a weekly report notification.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        now_str = datetime.datetime.now().isoformat()
        cur.execute(
            """
            UPDATE parent_notification_log
            SET read_at = ?
            WHERE parent_email = ? AND student_email = ? AND payload_json LIKE ?
            """,
            (now_str, parent_email, student_email, f'%{report_id}%'),
        )

        # Also mark the report row itself
        cur.execute(
            """
            INSERT INTO parent_notification_log (
                id, parent_email, student_email, notification_type,
                payload_json, sent_at, read_at, projection_version
            ) VALUES (?, ?, ?, 'WeeklyReportRead', ?, ?, ?, 'v1.0')
            """,
            (
                str(uuid.uuid4()),
                parent_email,
                student_email,
                json.dumps({"report_id": report_id}),
                now_str,
                now_str,
            ),
        )
        conn.commit()
    finally:
        conn.close()
