"""
teacher_twin/aggregator.py
Classroom Aggregator: aggregates memory, attention, and NBIRT state updates.
"""

import json
import datetime
from database import get_conn

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Consumes MemoryUpdated. Recalculates concept retention counts for the room.
    """
    if not isinstance(event_data, dict):
        event_data = dict(event_data)

    payload = event_data.get("payload_json", {})
    if isinstance(payload, str):
        payload = json.loads(payload)
        
    email = event_data.get("entity_id")
    concept_id = payload.get("concept_id")
    if not concept_id:
        return

    conn = get_conn()
    cur = conn.cursor()
    try:
        # Get room code
        cur.execute("SELECT room_code FROM student_room WHERE student_email = ?", (email,))
        row = cur.fetchone()
        room_code = row["room_code"] if row else "R1"
        
        # Get all students in this room
        cur.execute("SELECT student_email FROM student_room WHERE room_code = ?", (room_code,))
        students = [r["student_email"] for r in cur.fetchall()]
        total_students = len(students)
        
        mastered = 0
        forgetting = 0
        at_risk = 0
        
        for s_email in students:
            cur.execute("""
                SELECT memory_state FROM concept_memory 
                WHERE student_email = ? AND concept_id = ?
            """, (s_email, concept_id))
            mem_row = cur.fetchone()
            if mem_row:
                state = mem_row["memory_state"]
                if state in ("Stable", "mastered"):
                    mastered += 1
                elif state in ("Forgetting", "forgetting"):
                    forgetting += 1
                elif state in ("AtRisk", "at_risk"):
                    at_risk += 1
            else:
                # Default to at risk if no concept memory exists yet
                at_risk += 1
                
        now_str = datetime.datetime.now().isoformat()
        cur.execute("""
            INSERT INTO teacher_classroom_retention (
                room_code, concept_id, mastered_count, forgetting_count, at_risk_count,
                total_students, projection_version, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'v1.0', ?)
            ON CONFLICT(room_code, concept_id) DO UPDATE SET
                mastered_count = excluded.mastered_count,
                forgetting_count = excluded.forgetting_count,
                at_risk_count = excluded.at_risk_count,
                total_students = excluded.total_students,
                updated_at = excluded.updated_at
        """, (room_code, concept_id, mastered, forgetting, at_risk, total_students, now_str))
        conn.commit()
    finally:
        conn.close()

def handle_attention_updated(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Consumes AttentionUpdated. Updates engagement summaries per room.
    """
    if not isinstance(event_data, dict):
        event_data = dict(event_data)

    email = event_data.get("entity_id")
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT room_code FROM student_room WHERE student_email = ?", (email,))
        row = cur.fetchone()
        room_code = row["room_code"] if row else "R1"
        
        cur.execute("SELECT student_email FROM student_room WHERE room_code = ?", (room_code,))
        students = [r["student_email"] for r in cur.fetchall()]
        total_students = len(students)
        
        optimal = 0
        decay = 0
        fatigue = 0
        
        for s_email in students:
            cur.execute("SELECT focus_state FROM student_attention_state WHERE student_email = ?", (s_email,))
            att_row = cur.fetchone()
            if att_row:
                state = att_row["focus_state"]
                if state == "optimal":
                    optimal += 1
                elif state in ("decay", "distracted"):
                    decay += 1
                elif state in ("fatigued", "overloaded"):
                    fatigue += 1
            else:
                optimal += 1
                
        now_str = datetime.datetime.now().isoformat()
        cur.execute("""
            INSERT INTO teacher_engagement_summary (
                room_code, optimal_count, decay_count, fatigue_count, total_students, projection_version, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'v1.0', ?)
            ON CONFLICT(room_code) DO UPDATE SET
                optimal_count = excluded.optimal_count,
                decay_count = excluded.decay_count,
                fatigue_count = excluded.fatigue_count,
                total_students = excluded.total_students,
                updated_at = excluded.updated_at
        """, (room_code, optimal, decay, fatigue, total_students, now_str))
        conn.commit()
    finally:
        conn.close()

def handle_nbirt_updated(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Consumes NBIRTUpdated.
    """
    pass
