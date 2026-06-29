"""
research_analytics_twin/classroom_speed.py
Classroom Growth Speed Engine: measures learning rate improvements of classrooms (CQRS).
"""

import datetime
from database import get_conn

def recompute_classroom_speed():
    """
    Calculates initial vs current health to compute the improvement rate of classrooms.
    Uses projection-to-projection reads.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Get all rooms
        cur.execute("SELECT room_code FROM rooms")
        rooms = [r["room_code"] for r in cur.fetchall()]

        now_str = datetime.datetime.now().isoformat()
        cur.execute("DELETE FROM research_classroom_speed")

        for r_code in rooms:
            # Get students in room
            cur.execute("SELECT student_email FROM room_students WHERE room_code = ?", (r_code,))
            students = [r["student_email"] for r in cur.fetchall()]
            if not students:
                continue

            # 1. Earliest health score per student
            earliest_scores = []
            placeholders = ",".join("?" for _ in students)
            cur.execute(f"""
                SELECT student_email, metric_value, MIN(recorded_at)
                FROM student_trend_projection
                WHERE student_email IN ({placeholders}) AND metric_name = 'Health Score'
                GROUP BY student_email
            """, tuple(students))
            
            for row in cur.fetchall():
                earliest_scores.append(row["metric_value"])

            initial_health = round(sum(earliest_scores) / len(earliest_scores), 3) if earliest_scores else 0.50

            # 2. Current average health score
            cur.execute(f"""
                SELECT AVG(cognitive_health_score) as avg_score
                FROM student_profile_projection
                WHERE student_email IN ({placeholders})
            """, tuple(students))
            
            health_row = cur.fetchone()
            current_health = round(health_row["avg_score"] or 0.50, 3)

            improvement_rate = round(current_health - initial_health, 3)

            cur.execute("""
                INSERT INTO research_classroom_speed (
                    room_code, initial_health, current_health, improvement_rate, updated_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (r_code, initial_health, current_health, improvement_rate, now_str))

        conn.commit()
    finally:
        conn.close()

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    if not is_replay:
        recompute_classroom_speed()
