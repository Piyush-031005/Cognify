"""
school_admin_twin/classroom.py
Classroom Aggregator: aggregates classroom-level metrics from Teacher Twin and Student Twin projection tables (CQRS).
"""

import datetime
from database import get_conn

def recompute_classroom_summary(room_code):
    """
    Reads strictly from projection tables (Decision 1) to update school_classroom_summary.
    - room_students + rooms for roster
    - student_profile_projection for average cognitive health (projection-to-projection)
    - teacher_intervention_queue for at-risk count (projection-to-projection)
    - teacher_classroom_retention for concept mastery rate (projection-to-projection)
    - teacher_engagement_summary for engagement score (projection-to-projection)
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Get room metadata
        cur.execute("SELECT teacher_email, subject FROM rooms WHERE room_code = ?", (room_code,))
        room_row = cur.fetchone()
        if not room_row:
            return
        teacher_email = room_row["teacher_email"]
        subject = room_row["subject"]

        # Get all students in this room
        cur.execute("SELECT student_email FROM room_students WHERE room_code = ?", (room_code,))
        students = [r["student_email"] for r in cur.fetchall()]
        total_students = len(students)

        # 1. Avg Cognitive Health
        avg_health = 0.0
        if total_students > 0:
            placeholders = ",".join("?" for _ in students)
            cur.execute(f"""
                SELECT AVG(cognitive_health_score) as avg_score 
                FROM student_profile_projection 
                WHERE student_email IN ({placeholders})
            """, tuple(students))
            health_row = cur.fetchone()
            avg_health = round(health_row["avg_score"] or 0.0, 3)

        # 2. At Risk Count (risk_level is high or medium in teacher_intervention_queue)
        at_risk = 0
        if total_students > 0:
            placeholders = ",".join("?" for _ in students)
            cur.execute(f"""
                SELECT COUNT(*) as cnt 
                FROM teacher_intervention_queue 
                WHERE student_email IN ({placeholders}) AND risk_level IN ('high', 'medium')
            """, tuple(students))
            at_risk = cur.fetchone()["cnt"] or 0

        # 3. Mastery Rate
        cur.execute("""
            SELECT mastered_count, total_students as room_total 
            FROM teacher_classroom_retention 
            WHERE room_code = ?
        """, (room_code,))
        retention_rows = cur.fetchall()
        
        mastery_rate = 0.0
        if retention_rows:
            rates = [r["mastered_count"] / max(1, r["room_total"]) for r in retention_rows]
            mastery_rate = round(sum(rates) / len(rates), 3)

        # 4. Engagement Score
        cur.execute("""
            SELECT optimal_count, decay_count, fatigue_count, total_students as room_total 
            FROM teacher_engagement_summary 
            WHERE room_code = ?
        """, (room_code,))
        eng_row = cur.fetchone()
        
        engagement_score = 0.0
        if eng_row:
            total_eng = eng_row["room_total"] or 1
            engagement_score = round(
                (eng_row["optimal_count"] * 1.0 + 
                 eng_row["decay_count"] * 0.6 + 
                 eng_row["fatigue_count"] * 0.3) / max(1, total_eng),
                3
            )

        now_str = datetime.datetime.now().isoformat()
        cur.execute("""
            INSERT INTO school_classroom_summary (
                room_code, school_id, teacher_email, subject, total_students,
                avg_cognitive_health, at_risk_count, mastery_rate, engagement_score,
                projection_version, updated_at
            ) VALUES (?, 'default', ?, ?, ?, ?, ?, ?, ?, 'v1.0', ?)
            ON CONFLICT(room_code) DO UPDATE SET
                teacher_email = excluded.teacher_email,
                subject = excluded.subject,
                total_students = excluded.total_students,
                avg_cognitive_health = excluded.avg_cognitive_health,
                at_risk_count = excluded.at_risk_count,
                mastery_rate = excluded.mastery_rate,
                engagement_score = excluded.engagement_score,
                updated_at = excluded.updated_at
        """, (room_code, teacher_email, subject, total_students, avg_health, at_risk, mastery_rate, engagement_score, now_str))

        conn.commit()
    finally:
        conn.close()

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
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
        recompute_classroom_summary(room_code)

def handle_attention_updated(event_data, is_replay=False, replay_mode="SAFE"):
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
        recompute_classroom_summary(room_code)
