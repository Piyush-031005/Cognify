"""
research_analytics_twin/interventions.py
Interventions Engine: evaluates effectiveness of student recommendations (CQRS).
"""

import datetime
from database import get_conn

def _categorize_recommendation(text):
    text = (text or "").lower()
    if "break" in text or "sleep" in text:
        return "Rest & Recovery"
    elif "review" in text or "prerequisite" in text:
        return "Prerequisite Review"
    elif "practice" in text or "quiz" in text:
        return "Practice Exercises"
    elif "override" in text:
        return "Teacher Override"
    return "Study Concept"

def recompute_intervention_effectiveness():
    """
    Analyzes student_recommendation_history and memory_state_transitions
    to measure the success rate of various recommendation types.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Get all student recommendations
        cur.execute("""
            SELECT id, student_email, recommendation, status, generated_at
            FROM student_recommendation_history
        """)
        recs = cur.fetchall()

        # Group metrics by category
        stats = {}  # category -> {generated, completed, successful}

        for r in recs:
            category = _categorize_recommendation(r["recommendation"])
            if category not in stats:
                stats[category] = {"generated": 0, "completed": 0, "successful": 0}
            
            stats[category]["generated"] += 1
            
            # For simplicity, count status IN ('COMPLETED', 'ACCEPTED', 'DONE') as completed
            status = (r["status"] or "").upper()
            is_completed = status in ("COMPLETED", "ACCEPTED", "DONE")
            if is_completed:
                stats[category]["completed"] += 1

                # Check if student had a positive memory transition within 7 days after generated_at
                gen_time = None
                try:
                    gen_time = datetime.datetime.fromisoformat(r["generated_at"])
                except ValueError:
                    pass

                if gen_time:
                    limit_time = (gen_time + datetime.timedelta(days=7)).isoformat()
                    cur.execute("""
                        SELECT 1 FROM memory_state_transitions
                        WHERE student_email = ? 
                          AND timestamp BETWEEN ? AND ?
                          AND new_state IN ('Stable', 'mastered', 'stable')
                        LIMIT 1
                    """, (r["student_email"], r["generated_at"], limit_time))
                    
                    if cur.fetchone():
                        stats[category]["successful"] += 1

        now_str = datetime.datetime.now().isoformat()
        cur.execute("DELETE FROM research_intervention_effectiveness")

        # If empty (e.g. no recs yet), seed default categories to avoid empty GET responses
        default_cats = ["Rest & Recovery", "Prerequisite Review", "Practice Exercises", "Study Concept"]
        for cat in default_cats:
            if cat not in stats:
                stats[cat] = {"generated": 0, "completed": 0, "successful": 0}

        for cat, data in stats.items():
            gen = data["generated"]
            comp = data["completed"]
            succ = data["successful"]
            rate = round(succ / max(1, comp), 3)

            cur.execute("""
                INSERT INTO research_intervention_effectiveness (
                    recommendation_type, total_generated, total_completed, total_successful, success_rate, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (cat, gen, comp, succ, rate, now_str))

        conn.commit()
    finally:
        conn.close()

def handle_decision_generated(event_data, is_replay=False, replay_mode="SAFE"):
    if not is_replay:
        recompute_intervention_effectiveness()
