"""
student_twin/profile.py
Profile Manager: manages student strengths, weaknesses, memory health, and cognitive health score.
"""

import json
import datetime
from database import get_conn

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Consumes MemoryUpdated event. Triggers profile recalculation.
    """
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    email = event_data.get("entity_id")
    if email:
        update_profile_projection(email)

def handle_nbirt_updated(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Consumes NBIRTUpdated event. Triggers profile recalculation.
    """
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    email = event_data.get("entity_id")
    if email:
        update_profile_projection(email)

def clamp(val, low=0.0, high=1.0):
    return max(low, min(high, val))

def update_profile_projection(email):
    """
    Aggregates strengths, weaknesses, memory health and computes the unified cognitive health score (Lock 1).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 1. Fetch memory strengths & weaknesses
        cur.execute("""
            SELECT concept_id, memory_strength, memory_state 
            FROM concept_memory WHERE student_email = ?
        """, (email,))
        memories = cur.fetchall()
        
        strengths = []
        weaknesses = []
        memory_healths = {}
        total_strength = 0.0
        
        for m in memories:
            cid = m["concept_id"]
            strength = m["memory_strength"] or 0.5
            state = m["memory_state"]
            total_strength += strength
            
            memory_healths[cid] = {
                "strength": round(strength, 3),
                "state": state,
                "forgetting_prediction": "high" if state in ("Forgetting", "forgetting", "AtRisk", "at_risk") else "low"
            }
            
            if strength >= 0.7 or state in ("Stable", "mastered"):
                strengths.append(cid)
            if strength <= 0.4 or state in ("Forgetting", "forgetting", "AtRisk", "at_risk"):
                weaknesses.append(cid)
                
        avg_memory_health = (total_strength / len(memories)) if memories else 1.0

        # 2. Fetch Attention focus score
        cur.execute("SELECT focus_state FROM student_attention_state WHERE student_email = ?", (email,))
        att_row = cur.fetchone()
        focus_state = att_row["focus_state"] if att_row else "optimal"
        att_score = 1.0
        if focus_state in ("decay", "distracted"):
            att_score = 0.6
        elif focus_state in ("fatigued", "overloaded"):
            att_score = 0.3

        # 3. Fetch Cognitive Load (CCLI)
        cur.execute("SELECT rolling_ccli FROM student_cognitive_load_state WHERE student_email = ?", (email,))
        ccli_row = cur.fetchone()
        ccli_val = ccli_row["rolling_ccli"] if ccli_row else 0.5
        ccli_score = 1.0 - ccli_val

        # 4. Fetch NBIRT Ability
        cur.execute("SELECT AVG(irt_ability) as avg_theta FROM student_cognitive_profiles WHERE student_email = ?", (email,))
        prof_row = cur.fetchone()
        avg_theta = prof_row["avg_theta"] if prof_row and prof_row["avg_theta"] is not None else 0.0
        ability_score = clamp((avg_theta + 3.0) / 6.0)

        # 5. Fetch Goal Progress
        cur.execute("""
            SELECT AVG(current_mastery / target_mastery) as avg_progress 
            FROM student_goal_projection 
            WHERE student_email = ? AND status = 'IN_PROGRESS'
        """, (email,))
        goal_row = cur.fetchone()
        goal_score = goal_row["avg_progress"] if goal_row and goal_row["avg_progress"] is not None else 1.0

        # Lock 1: Compute weighted cognitive health score
        cog_health = round(
            (0.30 * avg_memory_health) +
            (0.25 * att_score) +
            (0.20 * ccli_score) +
            (0.15 * ability_score) +
            (0.10 * goal_score),
            3
        )
        cog_health = clamp(cog_health)

        now_str = datetime.datetime.now().isoformat()
        cur.execute("""
            INSERT INTO student_profile_projection (
                student_email, strengths_json, weaknesses_json, memory_health_json,
                cognitive_health_score, projection_version, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'v1.0', ?)
            ON CONFLICT(student_email) DO UPDATE SET
                strengths_json = excluded.strengths_json,
                weaknesses_json = excluded.weaknesses_json,
                memory_health_json = excluded.memory_health_json,
                cognitive_health_score = excluded.cognitive_health_score,
                updated_at = excluded.updated_at
        """, (email, json.dumps(strengths), json.dumps(weaknesses), json.dumps(memory_healths), cog_health, now_str))

        # Lock 2: Record in trend projection
        cur.execute("""
            INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at)
            VALUES (?, 'Health Score', ?, ?)
        """, (email, cog_health, now_str))
        cur.execute("""
            INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at)
            VALUES (?, 'Memory Health', ?, ?)
        """, (email, avg_memory_health, now_str))

        conn.commit()
    finally:
        conn.close()
