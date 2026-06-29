"""
school_admin_twin/teacher_summary.py
Teacher Summary Aggregator: aggregates metrics per teacher from rooms, teacher_override_history, and teacher_recommendation_history (CQRS).
"""

import datetime
from database import get_conn

def recompute_teacher_summary(teacher_email):
    """
    Recomputes school_teacher_summary for a specific teacher.
    Uses projection-to-projection reads (Decision 1 & 3).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 1. Total rooms
        cur.execute("SELECT COUNT(*) as cnt FROM rooms WHERE teacher_email = ?", (teacher_email,))
        total_rooms = cur.fetchone()["cnt"] or 0

        # 2. Total students (unique enrollment across all teacher's rooms)
        cur.execute("""
            SELECT COUNT(DISTINCT s.student_email) as cnt
            FROM room_students s
            JOIN rooms r ON s.room_code = r.room_code
            WHERE r.teacher_email = ?
        """, (teacher_email,))
        total_students = cur.fetchone()["cnt"] or 0

        # 3. Avg Class Health
        cur.execute("""
            SELECT AVG(avg_cognitive_health) as avg_health
            FROM school_classroom_summary
            WHERE teacher_email = ?
        """, (teacher_email,))
        health_row = cur.fetchone()
        avg_class_health = round(health_row["avg_health"] or 0.0, 3)

        # 4. Override count
        cur.execute("""
            SELECT COUNT(*) as cnt FROM teacher_override_history 
            WHERE actor = ?
        """, (teacher_email,))
        override_count = cur.fetchone()["cnt"] or 0

        # 5. Intervention count
        cur.execute("""
            SELECT COUNT(*) as cnt FROM teacher_recommendation_history
            WHERE teacher_id = ? AND status = 'ACCEPTED'
        """, (teacher_email,))
        intervention_count = cur.fetchone()["cnt"] or 0

        now_str = datetime.datetime.now().isoformat()
        cur.execute("""
            INSERT INTO school_teacher_summary (
                teacher_email, school_id, total_rooms, total_students,
                avg_class_health, override_count, intervention_count,
                projection_version, updated_at
            ) VALUES (?, 'default', ?, ?, ?, ?, ?, 'v1.0', ?)
            ON CONFLICT(teacher_email) DO UPDATE SET
                total_rooms = excluded.total_rooms,
                total_students = excluded.total_students,
                avg_class_health = excluded.avg_class_health,
                override_count = excluded.override_count,
                intervention_count = excluded.intervention_count,
                updated_at = excluded.updated_at
        """, (teacher_email, total_rooms, total_students, avg_class_health, override_count, intervention_count, now_str))

        conn.commit()
    finally:
        conn.close()

def handle_teacher_override_applied(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Increments override_count and triggers recomputation.
    """
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    
    payload = event_data.get("payload_json", {})
    if isinstance(payload, str):
        import json
        payload = json.loads(payload)
        
    actor = payload.get("actor")
    student_email = event_data.get("entity_id")
    event_id = event_data.get("event_id") or "evt_override"

    if not actor and student_email:
        # Try to look up by room or student email
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT r.teacher_email FROM rooms r
                JOIN room_students s ON r.room_code = s.room_code
                WHERE s.student_email = ?
                LIMIT 1
            """, (student_email,))
            row = cur.fetchone()
            actor = row["teacher_email"] if row else None
        finally:
            conn.close()

    if actor and student_email:
        # Auto-populate teacher_override_history projection (if missing)
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM teacher_override_history WHERE override_id = ?", (event_id,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO teacher_override_history (
                        override_id, student_email, concept_id, override_type, reason, actor, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_id,
                    student_email,
                    payload.get("concept_id", "general"),
                    payload.get("override_type", "Override"),
                    payload.get("reason", "CEB Event"),
                    actor,
                    event_data.get("created_at", datetime.datetime.now().isoformat())
                ))
                conn.commit()
        finally:
            conn.close()

    if actor:
        recompute_teacher_summary(actor)

