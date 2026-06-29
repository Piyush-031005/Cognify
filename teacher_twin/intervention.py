"""
teacher_twin/intervention.py
Intervention Engine: handles decision generated events, priority queue, and recommendations.
"""

import json
import uuid
import datetime
from database import get_conn

def handle_decision_generated(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Consumes DecisionGenerated. Updates intervention queue and generates recommendations.
    """
    if not isinstance(event_data, dict):
        event_data = dict(event_data)

    payload = event_data.get("payload_json", {})
    if isinstance(payload, str):
        payload = json.loads(payload)
        
    email = event_data.get("entity_id")
    concept_id = payload.get("concept_id")
    event_id = event_data.get("event_id")

    conn = get_conn()
    cur = conn.cursor()
    try:
        # Get room code
        cur.execute("SELECT room_code FROM student_room WHERE student_email = ?", (email,))
        row = cur.fetchone()
        room_code = row["room_code"] if row else "R1"

        # Fetch latest CCLI state
        cur.execute("SELECT rolling_ccli, alert_status FROM student_cognitive_load_state WHERE student_email = ?", (email,))
        ccli_row = cur.fetchone()
        ccli_val = ccli_row["rolling_ccli"] if ccli_row else 0.5
        ccli_status = ccli_row["alert_status"] if ccli_row else "normal"

        # Fetch latest CDO decision
        cur.execute("SELECT final_decision, winning_rule, confidence_score FROM decision_runs WHERE student_email = ? ORDER BY timestamp DESC LIMIT 1", (email,))
        dec_row = cur.fetchone()
        decision = dec_row["final_decision"] if dec_row else "Review"
        winning_rule = dec_row["winning_rule"] if dec_row else "Default"
        confidence = dec_row["confidence_score"] if dec_row else 0.8

        # Determine risk level
        risk_level = "low"
        if decision == "Review" or decision == "review":
            if ccli_val > 0.7 or ccli_status == "fatigued":
                risk_level = "high"
            else:
                risk_level = "medium"

        # Update teacher_intervention_queue projection
        now_str = datetime.datetime.now().isoformat()
        cur.execute("""
            INSERT INTO teacher_intervention_queue (
                student_email, room_code, risk_level, ccli_value, decision, winning_rule, projection_version, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'v1.0', ?)
            ON CONFLICT(student_email) DO UPDATE SET
                room_code = excluded.room_code,
                risk_level = excluded.risk_level,
                ccli_value = excluded.ccli_value,
                decision = excluded.decision,
                winning_rule = excluded.winning_rule,
                updated_at = excluded.updated_at
        """, (email, room_code, risk_level, ccli_val, decision, winning_rule, now_str))

        # Generate recommendation if high or medium risk
        if risk_level in ("high", "medium"):
            rec_id = str(uuid.uuid4())
            rec_text = f"Teacher to assign 3 practice questions on {concept_id} to assist student mastery."
            
            # Lock 6: separate priority_score from confidence
            priority_score = min(1.0, round(0.4 + (0.6 * ccli_val), 2))
            if risk_level == "high":
                priority_score = max(0.8, priority_score)

            # Fetch extra evidence for snapshot (Lock 4)
            cur.execute("SELECT focus_state FROM student_attention_state WHERE student_email = ?", (email,))
            att_row = cur.fetchone()
            focus_state = att_row["focus_state"] if att_row else "optimal"

            cur.execute("SELECT irt_ability FROM student_cognitive_profiles WHERE student_email = ? AND concept_id = ?", (email, concept_id))
            prof_row = cur.fetchone()
            theta = prof_row["irt_ability"] if prof_row else 0.0

            evidence_snapshot = {
                "memory_state": "forgetting" if risk_level == "high" else "stable",
                "theta": round(theta, 3),
                "attention": focus_state,
                "decision": decision,
                "ccli": round(ccli_val, 3)
            }

            cur.execute("""
                INSERT INTO teacher_recommendation_history (
                    id, teacher_id, student_email, recommendation, priority_score, confidence,
                    evidence_count, supporting_events, evidence_snapshot_json, status, generated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, 'PENDING', ?)
            """, (
                rec_id, room_code, email, rec_text, priority_score, confidence,
                json.dumps([event_id]), json.dumps(evidence_snapshot), now_str
            ))

            # Downstream publish (Decision Generated -> TeacherRecommendationGenerated)
            if not is_replay or replay_mode == "LIVE":
                import event_bus
                event_bus.publish(
                    event_type="TeacherRecommendationGenerated",
                    entity_type="teacher",
                    entity_id=room_code,
                    producer="teacher_twin",
                    producer_version="v2.6.0",
                    schema_version="v1.0",
                    metadata_json=event_data.get("metadata_json", {}),
                    payload_json={
                        "recommendation_id": rec_id,
                        "student_email": email,
                        "recommendation": rec_text,
                        "priority_score": priority_score,
                        "confidence": confidence,
                        "evidence_snapshot": evidence_snapshot
                    }
                )

        conn.commit()
    finally:
        conn.close()
