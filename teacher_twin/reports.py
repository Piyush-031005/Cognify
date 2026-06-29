"""
teacher_twin/reports.py
Report Generator: compiles classroom statistics and reports from projection tables.
"""

import json
from database import get_conn

def handle_question_retired(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Consumes QuestionRetired event.
    """
    pass

def handle_question_promoted(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Consumes QuestionPromoted event.
    """
    pass

def generate_classroom_report(room_code, period="daily"):
    """
    Compiles report by reading strictly from projection tables (CQRS separation).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 1. Fetch classroom retention summaries
        cur.execute("""
            SELECT concept_id, mastered_count, forgetting_count, at_risk_count, total_students
            FROM teacher_classroom_retention
            WHERE room_code = ?
        """, (room_code,))
        retention = [dict(row) for row in cur.fetchall()]

        # 2. Fetch engagement summaries
        cur.execute("""
            SELECT optimal_count, decay_count, fatigue_count, total_students
            FROM teacher_engagement_summary
            WHERE room_code = ?
        """, (room_code,))
        eng_row = cur.fetchone()
        engagement = dict(eng_row) if eng_row else {
            "optimal_count": 0, "decay_count": 0, "fatigue_count": 0, "total_students": 0
        }

        # 3. Fetch overrides count
        cur.execute("""
            SELECT COUNT(*) as count FROM teacher_override_history toh
            JOIN student_room sr ON sr.student_email = toh.student_email
            WHERE sr.room_code = ?
        """, (room_code,))
        overrides_row = cur.fetchone()
        overrides_count = overrides_row["count"] if overrides_row else 0

        # 4. Fetch pending recommendations count
        cur.execute("""
            SELECT COUNT(*) as count FROM teacher_recommendation_history
            WHERE teacher_id = ? AND status = 'PENDING'
        """, (room_code,))
        recs_row = cur.fetchone()
        pending_recs = recs_row["count"] if recs_row else 0

        return {
            "room_code": room_code,
            "period": period,
            "retention": retention,
            "engagement": engagement,
            "overrides_applied": overrides_count,
            "pending_recommendations_count": pending_recs
        }
    finally:
        conn.close()
