"""
school_admin_twin/adoption.py
Adoption Metrics Engine: aggregates system adoption and platform usage statistics (CQRS).
"""

import datetime
from database import get_conn

def recompute_adoption_metrics():
    """
    Recalculates school_adoption_metrics.
    Uses projection-to-projection reads.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 1. Total teachers
        cur.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'teacher'")
        total_teachers = cur.fetchone()["cnt"] or 0

        # 2. Active teachers (teachers who have created at least one room)
        cur.execute("SELECT COUNT(DISTINCT teacher_email) as cnt FROM rooms")
        active_teachers = cur.fetchone()["cnt"] or 0

        # 3. Total students
        cur.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'student'")
        total_students = cur.fetchone()["cnt"] or 0

        # 4. Active students (students with at least one recorded attempt/progress)
        cur.execute("SELECT COUNT(DISTINCT student_email) as cnt FROM student_progress_projection WHERE total_attempts > 0")
        active_students = cur.fetchone()["cnt"] or 0

        # 5. Total rooms
        cur.execute("SELECT COUNT(*) as cnt FROM rooms")
        total_rooms = cur.fetchone()["cnt"] or 0

        # 6. Avg session/cognitive health
        cur.execute("SELECT AVG(cognitive_health_score) as avg_score FROM student_profile_projection")
        avg_score_row = cur.fetchone()
        avg_session_health = round(avg_score_row["avg_score"] or 0.0, 3)

        now_str = datetime.datetime.now().isoformat()
        cur.execute("""
            INSERT INTO school_adoption_metrics (
                school_id, total_teachers, active_teachers, total_students, active_students,
                total_rooms, avg_session_health, projection_version, updated_at
            ) VALUES ('default', ?, ?, ?, ?, ?, ?, 'v1.0', ?)
            ON CONFLICT(school_id) DO UPDATE SET
                total_teachers = excluded.total_teachers,
                active_teachers = excluded.active_teachers,
                total_students = excluded.total_students,
                active_students = excluded.active_students,
                total_rooms = excluded.total_rooms,
                avg_session_health = excluded.avg_session_health,
                updated_at = excluded.updated_at
        """, (total_teachers, active_teachers, total_students, active_students, total_rooms, avg_session_health, now_str))

        conn.commit()
    finally:
        conn.close()
