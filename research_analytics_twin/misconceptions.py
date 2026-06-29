"""
research_analytics_twin/misconceptions.py
Misconception frequency and impact statistics (CQRS).
"""

import datetime
from database import get_conn

def recompute_misconception_frequency():
    """
    Aggregates misconception evidence to compute occurrences and student impact.
    Uses projection-to-projection reads.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT c.cluster_id, c.misconception_name, c.concept_id,
                   COALESCE(SUM(e.wrong_answer_count), 0) as occurrences,
                   COALESCE(SUM(e.student_count), 0) as student_impact
            FROM misconception_clusters c
            LEFT JOIN misconception_evidence e ON c.cluster_id = e.cluster_id
            GROUP BY c.cluster_id, c.misconception_name, c.concept_id
        """)
        rows = cur.fetchall()

        now_str = datetime.datetime.now().isoformat()
        cur.execute("DELETE FROM research_misconception_frequency")

        for r in rows:
            cur.execute("""
                INSERT INTO research_misconception_frequency (
                    cluster_id, misconception_name, concept_id,
                    occurrence_count, student_impact_count, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                r["cluster_id"],
                r["misconception_name"],
                r["concept_id"],
                r["occurrences"],
                r["student_impact"],
                now_str
            ))

        conn.commit()
    finally:
        conn.close()

def handle_decision_generated(event_data, is_replay=False, replay_mode="SAFE"):
    if not is_replay:
        recompute_misconception_frequency()
