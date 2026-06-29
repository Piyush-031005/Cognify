"""
school_admin_twin/risk_dashboard.py
Risk Dashboard Engine: aggregates risk levels from teacher_intervention_queue projections (CQRS).
"""

import datetime
from database import get_conn

def recompute_risk_dashboard(room_code=None):
    """
    Recalculates school_risk_dashboard.
    If room_code is None, recalcs for all rooms.
    Uses projection-to-projection reads.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        if room_code:
            rooms_to_update = [room_code]
        else:
            cur.execute("SELECT DISTINCT room_code FROM rooms")
            rooms_to_update = [r["room_code"] for r in cur.fetchall()]

        now_str = datetime.datetime.now().isoformat()
        for r_code in rooms_to_update:
            # Count total students in room
            cur.execute("SELECT COUNT(*) as cnt FROM room_students WHERE room_code = ?", (r_code,))
            total_students = cur.fetchone()["cnt"] or 0

            # Count risk levels in teacher_intervention_queue
            cur.execute("""
                SELECT 
                    SUM(CASE WHEN risk_level = 'high' THEN 1 ELSE 0 END) as high_cnt,
                    SUM(CASE WHEN risk_level = 'medium' THEN 1 ELSE 0 END) as med_cnt,
                    SUM(CASE WHEN risk_level = 'low' THEN 1 ELSE 0 END) as low_cnt
                FROM teacher_intervention_queue
                WHERE room_code = ?
            """, (r_code,))
            row = cur.fetchone()
            
            high = row["high_cnt"] or 0
            med = row["med_cnt"] or 0
            low = row["low_cnt"] or 0

            cur.execute("""
                INSERT INTO school_risk_dashboard (
                    school_id, room_code, high_risk_count, medium_risk_count, low_risk_count,
                    total_students, updated_at, projection_version
                ) VALUES ('default', ?, ?, ?, ?, ?, ?, 'v1.0')
                ON CONFLICT(school_id, room_code) DO UPDATE SET
                    high_risk_count = excluded.high_risk_count,
                    medium_risk_count = excluded.medium_risk_count,
                    low_risk_count = excluded.low_risk_count,
                    total_students = excluded.total_students,
                    updated_at = excluded.updated_at
            """, (r_code, high, med, low, total_students, now_str))

        conn.commit()
    finally:
        conn.close()

def handle_decision_generated(event_data, is_replay=False, replay_mode="SAFE"):
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    email = event_data.get("entity_id")
    if not email:
        return
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT room_code FROM room_students WHERE student_email = ?", (email,))
        row = cur.fetchone()
        room_code = row["room_code"] if row else None
    finally:
        conn.close()
    if room_code:
        recompute_risk_dashboard(room_code)
