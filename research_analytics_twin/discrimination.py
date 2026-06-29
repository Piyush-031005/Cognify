"""
research_analytics_twin/discrimination.py
Item Discrimination Engine: estimates item discrimination index (D) for questions (CQRS).
"""

import datetime
from database import get_conn

def recompute_question_discrimination():
    """
    Computes classical item discrimination index (D) for questions in the responses table.
    D = Correct Rate (High Health Cohort) - Correct Rate (Low Health Cohort)
    Uses projection-to-projection reads for cognitive health.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Get student cognitive health scores
        cur.execute("SELECT student_email, cognitive_health_score FROM student_profile_projection")
        health_map = {row["student_email"]: row["cognitive_health_score"] for row in cur.fetchall()}

        # Get all question responses
        cur.execute("SELECT question_id, student_email, correct FROM responses")
        responses = cur.fetchall()

        # Group responses by question_id
        grouped = {}
        for r in responses:
            q_id = r["question_id"]
            if q_id not in grouped:
                grouped[q_id] = []
            grouped[q_id].append(dict(r))

        now_str = datetime.datetime.now().isoformat()
        cur.execute("DELETE FROM research_question_discrimination")

        for q_id, resp_list in grouped.items():
            total_attempts = len(resp_list)
            correct_count = sum(1 for r in resp_list if r["correct"])
            overall_correct_rate = round(correct_count / max(1, total_attempts), 3)

            # Map health score to each response
            scores_with_health = []
            for r in resp_list:
                h_score = health_map.get(r["student_email"], 0.70)  # Default to median health
                scores_with_health.append((r["correct"], h_score))

            # Sort by health score
            scores_with_health.sort(key=lambda x: x[1])

            # Determine cohort split (27% top, 27% bottom)
            size = len(scores_with_health)
            split_size = max(1, int(size * 0.27))

            low_cohort = scores_with_health[:split_size]
            high_cohort = scores_with_health[-split_size:]

            low_correct = sum(1 for correct, _ in low_cohort if correct)
            high_correct = sum(1 for correct, _ in high_cohort if correct)

            low_rate = low_correct / len(low_cohort)
            high_rate = high_correct / len(high_cohort)

            discrimination_index = round(high_rate - low_rate, 3)

            cur.execute("""
                INSERT INTO research_question_discrimination (
                    question_id, discrimination_index, total_attempts, correct_rate, updated_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (q_id, discrimination_index, total_attempts, overall_correct_rate, now_str))

        conn.commit()
    finally:
        conn.close()

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    if not is_replay:
        recompute_question_discrimination()
