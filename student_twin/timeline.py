"""
student_twin/timeline.py
Timeline Engine: chronicles chronological event timelines.
"""

import json
import uuid
import datetime
from database import get_conn

def log_timeline_event(student_email, event_type, description, importance="medium", event_id=None):
    """
    Appends a formatted chronological entry to student_timeline_projection.
    """
    if not event_id:
        event_id = str(uuid.uuid4())
    now_str = datetime.datetime.now().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO student_timeline_projection (
                student_email, event_id, event_type, event_description, importance, timestamp, projection_version
            ) VALUES (?, ?, ?, ?, ?, ?, 'v1.0')
        """, (student_email, event_id, event_type, description, importance, now_str))
        conn.commit()
    finally:
        conn.close()

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    email = event_data.get("entity_id")
    payload = event_data.get("payload_json", {})
    if isinstance(payload, str):
        payload = json.loads(payload)
    concept_id = payload.get("concept_id")
    event_id = event_data.get("event_id")
    
    log_timeline_event(
        student_email=email,
        event_type="MemoryUpdated",
        description=f"Memory strength recalibrated for concept: {concept_id}",
        importance="medium",
        event_id=event_id
    )

def handle_nbirt_updated(event_data, is_replay=False, replay_mode="SAFE"):
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    email = event_data.get("entity_id")
    payload = event_data.get("payload_json", {})
    if isinstance(payload, str):
        payload = json.loads(payload)
    concept_id = payload.get("concept_id")
    event_id = event_data.get("event_id")

    log_timeline_event(
        student_email=email,
        event_type="NBIRTUpdated",
        description=f"Bayesian proficiency estimation calculated for concept: {concept_id}",
        importance="medium",
        event_id=event_id
    )

def handle_attention_updated(event_data, is_replay=False, replay_mode="SAFE"):
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    email = event_data.get("entity_id")
    event_id = event_data.get("event_id")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT focus_state FROM student_attention_state WHERE student_email = ?", (email,))
    row = cur.fetchone()
    conn.close()

    focus = row["focus_state"] if row else "optimal"
    if focus in ("fatigued", "overloaded"):
        log_timeline_event(
            student_email=email,
            event_type="AttentionUpdated",
            description=f"High cognitive fatigue detected: attention focus is {focus}",
            importance="high",
            event_id=event_id
        )

def handle_teacher_override_applied(event_data, is_replay=False, replay_mode="SAFE"):
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    email = event_data.get("entity_id")
    payload = event_data.get("payload_json", {})
    if isinstance(payload, str):
        payload = json.loads(payload)
    concept_id = payload.get("concept_id")
    override_type = payload.get("override_type")
    event_id = event_data.get("event_id")

    log_timeline_event(
        student_email=email,
        event_type="TeacherOverride",
        description=f"Teacher override applied on concept {concept_id}: status set to {override_type}",
        importance="critical",
        event_id=event_id
    )

def handle_teacher_recommendation(event_data, is_replay=False, replay_mode="SAFE"):
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    payload = event_data.get("payload_json", {})
    if isinstance(payload, str):
        payload = json.loads(payload)
    email = payload.get("student_email")
    rec_text = payload.get("recommendation")
    event_id = event_data.get("event_id")

    if email:
        log_timeline_event(
            student_email=email,
            event_type="TeacherAssignment",
            description=f"New study assignment from teacher: {rec_text}",
            importance="high",
            event_id=event_id
        )
