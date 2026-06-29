"""
research_analytics_twin/load_correlation.py
Cognitive Load & Decay Correlation Engine (CQRS).
"""

import datetime
from database import get_conn

def recompute_load_decay_correlation():
    """
    Correlates cognitive load composite values before memory decay events.
    Compares average composite load before decay vs baseline composite load.
    Uses projection-to-projection and event history reads.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Get all decay transitions
        cur.execute("""
            SELECT student_email, timestamp
            FROM memory_state_transitions
            WHERE new_state IN ('Forgetting', 'AtRisk', 'forgetting', 'at_risk')
        """)
        decays = cur.fetchall()

        pre_decay_loads = []
        for d in decays:
            student = d["student_email"]
            decay_time = None
            try:
                decay_time = datetime.datetime.fromisoformat(d["timestamp"])
            except ValueError:
                pass

            if decay_time:
                # 24 hours prior window
                start_time = (decay_time - datetime.timedelta(hours=24)).isoformat()
                cur.execute("""
                    SELECT composite_load FROM cognitive_load_events
                    WHERE student_email = ? AND timestamp BETWEEN ? AND ?
                """, (student, start_time, d["timestamp"]))
                
                for row in cur.fetchall():
                    pre_decay_loads.append(row["composite_load"])

        # Baseline composite load (overall average)
        cur.execute("SELECT AVG(composite_load) as avg_load, COUNT(*) as cnt FROM cognitive_load_events")
        baseline_row = cur.fetchone()
        baseline_avg = round(baseline_row["avg_load"] or 0.50, 3)
        baseline_count = baseline_row["cnt"] or 0

        pre_decay_avg = round(sum(pre_decay_loads) / len(pre_decay_loads), 3) if pre_decay_loads else 0.50

        now_str = datetime.datetime.now().isoformat()
        cur.execute("DELETE FROM research_load_decay_correlation")

        cur.execute("""
            INSERT INTO research_load_decay_correlation (
                metric_name, average_value, sample_size, updated_at
            ) VALUES (?, ?, ?, ?)
        """, ("Load Prior to Decay (24h)", pre_decay_avg, len(pre_decay_loads), now_str))

        cur.execute("""
            INSERT INTO research_load_decay_correlation (
                metric_name, average_value, sample_size, updated_at
            ) VALUES (?, ?, ?, ?)
        """, ("Baseline Cognitive Load", baseline_avg, baseline_count, now_str))

        conn.commit()
    finally:
        conn.close()

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    if not is_replay:
        recompute_load_decay_correlation()
