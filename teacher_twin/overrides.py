"""
teacher_twin/overrides.py
Teacher Override Manager: handles teacher override events and history tracking.
"""

import json
import uuid
import datetime
from database import get_conn

def handle_teacher_override(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Consumes TeacherOverride event. Logs override details into history.
    """
    if not isinstance(event_data, dict):
        event_data = dict(event_data)

    payload = event_data.get("payload_json", {})
    if isinstance(payload, str):
        payload = json.loads(payload)
        
    email = event_data.get("entity_id")
    concept_id = payload.get("concept_id")
    override_type = payload.get("override_type")
    reason = payload.get("reason")
    dec_before = payload.get("decision_before_override", "Default")
    dec_after = payload.get("decision_after_override", "Review")
    actor = payload.get("actor", "teacher")
    timestamp = event_data.get("created_at") or datetime.datetime.now().isoformat()

    if not concept_id:
        return

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO teacher_override_history (
                override_id, student_email, concept_id, override_type,
                decision_before_override, decision_after_override, reason, actor, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), email, concept_id, override_type, dec_before, dec_after, reason, actor, timestamp))
        conn.commit()
    finally:
        conn.close()

def record_override(student_email, concept_id, override_type, reason, actor="teacher"):
    """
    UI-facing action method: publishes TeacherOverride event to CEB.
    """
    # Fetch decision before override
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT final_decision FROM decision_runs 
        WHERE student_email = ? 
        ORDER BY timestamp DESC LIMIT 1
    """, (student_email,))
    row = cur.fetchone()
    conn.close()
    
    dec_before = row["final_decision"] if row else "Default"
    dec_after = override_type  # The override enforces the action

    # Publish TeacherOverride onto the CEB
    import event_bus
    event_bus.publish(
        event_type="TeacherOverride",
        entity_type="student",
        entity_id=student_email,
        producer="teacher_twin",
        producer_version="v2.6.0",
        schema_version="v1.0",
        metadata_json={},
        payload_json={
            "concept_id": concept_id,
            "override_type": override_type,
            "reason": reason,
            "decision_before_override": dec_before,
            "decision_after_override": dec_after,
            "actor": actor
        }
    )
    
    return {"status": "success", "recorded_action": override_type}
