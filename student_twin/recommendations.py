"""
student_twin/recommendations.py
Recommendations Engine: generates student-facing personalized study recommendations.
"""

import json
import uuid
import datetime
from database import get_conn

def handle_decision_generated(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Consumes DecisionGenerated event. Builds student-facing explainable recommendations (Lock 3).
    """
    if not isinstance(event_data, dict):
        event_data = dict(event_data)

    payload = event_data.get("payload_json", {})
    if isinstance(payload, str):
        payload = json.loads(payload)
        
    email = event_data.get("entity_id")
    concept_id = payload.get("concept_id")
    event_id = event_data.get("event_id")
    if not email:
        return

    conn = get_conn()
    cur = conn.cursor()
    try:
        # Fetch latest CCLI load state
        cur.execute("SELECT rolling_ccli, alert_status FROM student_cognitive_load_state WHERE student_email = ?", (email,))
        ccli_row = cur.fetchone()
        ccli_val = ccli_row["rolling_ccli"] if ccli_row else 0.5
        ccli_status = ccli_row["alert_status"] if ccli_row else "normal"

        # Fetch latest Attention focus state
        cur.execute("SELECT focus_state FROM student_attention_state WHERE student_email = ?", (email,))
        att_row = cur.fetchone()
        focus_state = att_row["focus_state"] if att_row else "optimal"

        # Fetch latest CDO decision
        cur.execute("SELECT final_decision, confidence_score FROM decision_runs WHERE student_email = ? ORDER BY timestamp DESC LIMIT 1", (email,))
        dec_row = cur.fetchone()
        decision = dec_row["final_decision"] if dec_row else "Review"
        confidence = dec_row["confidence_score"] if dec_row else 0.85

        # Fetch memory state
        cur.execute("SELECT memory_strength FROM concept_memory WHERE student_email = ? AND concept_id = ?", (email, concept_id))
        mem_row = cur.fetchone()
        m_strength = mem_row["memory_strength"] if mem_row else 0.5

        # Fetch NBIRT theta
        cur.execute("SELECT irt_ability FROM student_cognitive_profiles WHERE student_email = ? AND concept_id = ?", (email, concept_id))
        prof_row = cur.fetchone()
        theta = prof_row["irt_ability"] if prof_row else 0.0

        # Construct evidence snapshot (Lock 4)
        evidence_snapshot = {
            "memory": round(m_strength, 3),
            "theta": round(theta, 3),
            "attention": focus_state,
            "decision": decision,
            "ccli": round(ccli_val, 3)
        }

        # Formulate study recommendation
        rec_id = str(uuid.uuid4())
        now_str = datetime.datetime.now().isoformat()
        
        if focus_state == "fatigued" or ccli_val > 0.8:
            rec_text = "Take a 5-minute cognitive break to recover focus before continuing."
            priority_score = 0.95
        elif decision == "Review":
            rec_text = f"Practice 5 quick quiz questions on {concept_id} to refresh your memory decay."
            priority_score = min(1.0, round(0.5 + (0.5 * ccli_val), 2))
        else:
            rec_text = f"Advance to new concepts related to {concept_id}."
            priority_score = 0.50

        # Insert to student recommendation history (Lock 3: PENDING, VIEWED, STARTED, COMPLETED, IGNORED, EXPIRED)
        cur.execute("""
            INSERT INTO student_recommendation_history (
                id, student_email, recommendation, priority_score, confidence,
                evidence_snapshot_json, status, generated_at, projection_version
            ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?, 'v1.0')
        """, (rec_id, email, rec_text, priority_score, confidence, json.dumps(evidence_snapshot), now_str))
        conn.commit()
    finally:
        conn.close()

def update_recommendation_status(rec_id, status):
    """
    Updates the recommendation lifecycle status (Lock 3).
    """
    valid_statuses = ("PENDING", "VIEWED", "STARTED", "COMPLETED", "IGNORED", "EXPIRED")
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}")

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE student_recommendation_history
            SET status = ?
            WHERE id = ?
        """, (status, rec_id))
        conn.commit()
    finally:
        conn.close()
