"""
teacher_twin package initialization.
Exposes public APIs and delegates event handlers to submodules.
"""

from database import get_conn

# Import submodule handlers
from teacher_twin.aggregator import (
    handle_memory_updated,
    handle_nbirt_updated,
    handle_attention_updated
)
from teacher_twin.intervention import (
    handle_decision_generated
)
from teacher_twin.overrides import (
    handle_teacher_override,
    record_override
)
from teacher_twin.reports import (
    handle_question_retired,
    handle_question_promoted,
    generate_classroom_report
)

def rebuild_projections():
    """
    Clears all projection tables and chronologically replays events in SAFE mode.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM teacher_classroom_retention")
        cur.execute("DELETE FROM teacher_intervention_queue")
        cur.execute("DELETE FROM teacher_engagement_summary")
        cur.execute("DELETE FROM teacher_override_history")
        cur.execute("DELETE FROM teacher_recommendation_history")
        conn.commit()
    finally:
        conn.close()

    import event_replay
    res = event_replay.replay_all_events("teacher_twin", mode="SAFE")
    return res

def get_classroom_heatmap(room_id):
    """
    CQRS projection query: reads strictly from teacher_classroom_retention.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT concept_id, mastered_count, forgetting_count, at_risk_count, total_students
            FROM teacher_classroom_retention WHERE room_code = ?
        """, (room_id,))
        rows = cur.fetchall()
        
        heatmap = {}
        total_students = 0
        for row in rows:
            lo = f"LO: {row['concept_id']}"
            heatmap[lo] = {
                "mastered": row["mastered_count"],
                "forgetting": row["forgetting_count"],
                "at_risk": row["at_risk_count"],
                "misconceptions": 0,
                "mastery_percentage": round((row["mastered_count"] / max(1, row["total_students"])) * 100, 1)
            }
            total_students = max(total_students, row["total_students"])
        return {
            "room_id": room_id,
            "total_students": total_students,
            "heatmap": heatmap
        }
    finally:
        conn.close()

def get_student_prioritization(room_id, session_context=None):
    """
    CQRS projection query: reads from teacher_intervention_queue.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT q.*, r.recommendation, r.priority_score, r.confidence, r.id as rec_id
            FROM teacher_intervention_queue q
            LEFT JOIN teacher_recommendation_history r 
              ON r.student_email = q.student_email AND r.status = 'PENDING'
            WHERE q.room_code = ?
        """, (room_id,))
        rows = cur.fetchall()
        
        prioritization = []
        for r in rows:
            p_score = r["priority_score"] or 0.5
            # Apply boost if matching session context
            if session_context and r["recommendation"] and session_context in r["recommendation"]:
                p_score = min(1.0, round(p_score * 1.5, 2))
                
            prioritization.append({
                "student_email": r["student_email"],
                "teacher_priority": p_score,
                "top_recommendation": {
                    "id": r["rec_id"] or "none",
                    "target": session_context or "general",
                    "action": r["recommendation"] or "No recommendation",
                    "priority": p_score,
                    "confidence": r["confidence"] or 0.8
                },
                "learning_risk": 0.8 if r["risk_level"] == "high" else (0.5 if r["risk_level"] == "medium" else 0.2)
            })
            
        prioritization.sort(key=lambda x: x["teacher_priority"], reverse=True)
        return prioritization
    finally:
        conn.close()

def plan_intervention(student_email, context_id):
    """
    CQRS query reading details for intervention planning.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT * FROM teacher_recommendation_history 
            WHERE student_email = ? AND id = ?
        """, (student_email, context_id))
        row = cur.fetchone()
        if not row:
            return {"error": "Recommendation not found."}
            
        return {
            "student_email": student_email,
            "recommendation_id": context_id,
            "action": row["recommendation"],
            "success_criteria": "3 consecutive correct answers",
            "human_authority_note": "AI suggests this intervention. Teacher must manually approve and assign."
        }
    finally:
        conn.close()

def record_teacher_feedback(context_id, action_taken, outcome_notes=""):
    """
    Updates the recommendation lifecycle status (Lock 3) and logs feedback.
    """
    status_map = {
        "accept": "ACCEPTED",
        "Accepted": "ACCEPTED",
        "ignore": "REJECTED",
        "Ignored": "REJECTED",
        "reject": "REJECTED",
        "view": "VIEWED"
    }
    status = status_map.get(action_taken, "ACCEPTED")
    
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE teacher_recommendation_history
            SET status = ?
            WHERE id = ?
        """, (status, context_id))
        conn.commit()
    finally:
        conn.close()
        
    # Publish TeacherOverrideApplied event
    try:
        import event_bus
        event_bus.publish(
            event_type="TeacherOverride",
            entity_type="recommendation",
            entity_id=context_id,
            producer="teacher_twin",
            producer_version="v2.6.0",
            schema_version="v1.0",
            metadata_json={},
            payload_json={"action": action_taken, "status": status, "notes": outcome_notes}
        )
    except Exception:
        pass
        
    return {"status": "success", "recorded_action": action_taken}
