"""
research_analytics_twin/decay.py
Concept Decay Engine: tracks memory decay speed per concept (CQRS).
"""

import datetime
from database import get_conn

def recompute_concept_decay():
    """
    Analyzes memory_state_transitions to determine how long concepts stay in a Stable state
    before decaying (transitioning to Forgetting/AtRisk).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Get all transitions ordered by student, concept, and timestamp
        cur.execute("""
            SELECT student_email, concept_id, old_state, new_state, timestamp
            FROM memory_state_transitions
            ORDER BY student_email, concept_id, timestamp ASC
        """)
        rows = cur.fetchall()

        # Group transitions by (student_email, concept_id)
        grouped = {}
        for r in rows:
            key = (r["student_email"], r["concept_id"])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(dict(r))

        decay_data = {}  # concept_id -> list of decay deltas in days
        decay_counts = {}  # concept_id -> count of decay events
        students_per_concept = {}  # concept_id -> set of student_emails

        for (student, concept), trans_list in grouped.items():
            last_stable_time = None
            for t in trans_list:
                new_state = (t["new_state"] or "").lower()
                old_state = (t["old_state"] or "").lower()

                # Record when the concept became stable/mastered
                if new_state in ("stable", "mastered"):
                    try:
                        last_stable_time = datetime.datetime.fromisoformat(t["timestamp"])
                    except ValueError:
                        last_stable_time = None

                # Record when it decayed
                elif new_state in ("forgetting", "atrisk", "at_risk") and old_state in ("stable", "mastered"):
                    if concept not in decay_counts:
                        decay_counts[concept] = 0
                    decay_counts[concept] += 1
                    
                    if concept not in students_per_concept:
                        students_per_concept[concept] = set()
                    students_per_concept[concept].add(student)

                    if last_stable_time:
                        try:
                            decay_time = datetime.datetime.fromisoformat(t["timestamp"])
                            delta = (decay_time - last_stable_time).total_seconds() / 86400.0  # convert to days
                            if delta > 0:
                                if concept not in decay_data:
                                    decay_data[concept] = []
                                decay_data[concept].append(delta)
                        except ValueError:
                            pass
                        last_stable_time = None  # Reset

        now_str = datetime.datetime.now().isoformat()
        
        # WIPE before re-populating to keep clean
        cur.execute("DELETE FROM research_concept_decay")

        # Select all concept_ids present in the transitions to populate
        all_concepts = set(decay_counts.keys()).union(decay_data.keys()).union(students_per_concept.keys())

        for c_id in all_concepts:
            count = decay_counts.get(c_id, 0)
            deltas = decay_data.get(c_id, [])
            avg_days = round(sum(deltas) / len(deltas), 3) if deltas else 0.0
            total_students = len(students_per_concept.get(c_id, set()))

            cur.execute("""
                INSERT INTO research_concept_decay (
                    concept_id, decay_count, avg_decay_time_days, total_students, updated_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (c_id, count, avg_days, total_students, now_str))

        conn.commit()
    finally:
        conn.close()

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    if not is_replay:
        recompute_concept_decay()
