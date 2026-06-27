import context_engine
import orchestrator
from database import get_conn
from datetime import datetime

def get_classroom_heatmap(room_id):
    """
    Aggregates the Unified Cognitive States of all students in a classroom.
    Aggregates by Learning Objective, not just concept.
    """
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT student_email FROM student_room WHERE room_code = ?", (room_id,))
    students = [row["student_email"] for row in cur.fetchall()]
    
    heatmap = {}
    
    for email in students:
        state = orchestrator.get_unified_cognitive_state(email)
        memory = state.get("memory", {})
        
        # In a real system, we map concepts to Learning Objectives (LOs).
        # We will mock the LO mapping for now.
        
        for c in memory.get("mastered", []):
            lo = f"LO: {c['node_id']}"
            if lo not in heatmap:
                heatmap[lo] = {"mastered": 0, "forgetting": 0, "at_risk": 0, "misconceptions": 0}
            heatmap[lo]["mastered"] += 1
            
        for c in memory.get("forgetting", []):
            lo = f"LO: {c['node_id']}"
            if lo not in heatmap:
                heatmap[lo] = {"mastered": 0, "forgetting": 0, "at_risk": 0, "misconceptions": 0}
            heatmap[lo]["forgetting"] += 1
            
        for c in memory.get("at_risk", []):
            lo = f"LO: {c['node_id']}"
            if lo not in heatmap:
                heatmap[lo] = {"mastered": 0, "forgetting": 0, "at_risk": 0, "misconceptions": 0}
            heatmap[lo]["at_risk"] += 1
            
        for m in memory.get("active_misconceptions", []):
            lo = f"LO: {m['node_id']}"
            if lo not in heatmap:
                heatmap[lo] = {"mastered": 0, "forgetting": 0, "at_risk": 0, "misconceptions": 0}
            heatmap[lo]["misconceptions"] += 1
            
    conn.close()
    
    # Calculate % mastery
    total_students = len(students)
    if total_students > 0:
        for lo, stats in heatmap.items():
            stats["mastery_percentage"] = round((stats["mastered"] / total_students) * 100, 1)
            
    return {
        "room_id": room_id,
        "total_students": total_students,
        "heatmap": heatmap
    }

def get_student_prioritization(room_id, session_context=None):
    """
    Returns a ranked list of students requiring immediate attention.
    Teacher Priority = Learning Risk × Urgency × Impact × Confidence
    Session-aware: Boosts priority if the recommendation aligns with session_context.
    """
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT student_email FROM student_room WHERE room_code = ?", (room_id,))
    students = [row["student_email"] for row in cur.fetchall()]
    conn.close()
    
    prioritization = []
    
    for email in students:
        res = context_engine.generate_contextual_recommendations(email)
        recs = res.get("recommendations", [])
        
        if not recs:
            continue
            
        # Get highest priority recommendation for this student
        top_rec = recs[0]
        base_priority = top_rec["priority"]
        
        # Re-calculate as Teacher Priority
        # We assume base_priority = Impact * Confidence * Urgency (approx)
        # We add Learning Risk (e.g. recent accuracy)
        state = orchestrator.get_unified_cognitive_state(email)
        recent_acc = state.get("telemetry", {}).get("recent_accuracy", 0.5)
        if recent_acc is None:
            recent_acc = 0.5
            
        learning_risk = 1.0 - recent_acc
        
        teacher_priority = round(base_priority * max(0.1, learning_risk), 2)
        
        # Session-aware boost
        if session_context and top_rec["target"] == session_context:
            teacher_priority = min(1.0, round(teacher_priority * 1.5, 2))
            
        prioritization.append({
            "student_email": email,
            "teacher_priority": teacher_priority,
            "top_recommendation": top_rec,
            "learning_risk": round(learning_risk, 2)
        })
        
    prioritization.sort(key=lambda x: x["teacher_priority"], reverse=True)
    return prioritization

def plan_intervention(student_email, context_id):
    """
    Translates a Context Engine recommendation into an actionable teaching plan.
    Must contain success criteria.
    """
    res = context_engine.generate_contextual_recommendations(student_email)
    recs = res.get("recommendations", [])
    
    target_rec = next((r for r in recs if r["id"] == context_id), None)
    
    if not target_rec:
        return {"error": "Recommendation not found."}
        
    plan = {
        "student_email": student_email,
        "recommendation_id": context_id,
        "action": f"Teacher to assign 3 practice questions on {target_rec['target']}.",
        "success_criteria": "3 consecutive correct answers",
        "human_authority_note": "AI suggests this intervention. Teacher must manually approve and assign."
    }
    
    return plan

def record_teacher_feedback(context_id, action_taken, outcome_notes=""):
    """
    Tracks whether a teacher Accepted, Ignored, or Modified a recommendation.
    """
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO teacher_recommendation_feedback (context_id, action_taken, outcome_notes, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (context_id, action_taken, outcome_notes, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return {"status": "success", "recorded_action": action_taken}
