import uuid
import orchestrator

def generate_contextual_recommendations(student_email):
    """
    Stateless consumer. Returns a categorized, prioritized list of explainable recommendations.
    """
    state = orchestrator.get_unified_cognitive_state(student_email)
    recommendations = []

    # Safe access to memory structures
    memory = state.get("memory", {})
    forgetting = memory.get("forgetting", [])
    at_risk = memory.get("at_risk", [])
    active_misconceptions = memory.get("active_misconceptions", [])
    
    # Optional Mock Check for QQI Conflict (In a real system, we'd query QQI Engine for the target's recent difficulty)
    # We will simulate conflict detection for testing purposes if target == 'conflict_c1'
    
    # 1. Remediation for Active Misconceptions
    for mcp in active_misconceptions:
        confidence = mcp.get("confidence", 0.5)
        priority = round(0.9 * confidence * 0.9, 2)
        uncertainty = round(1.0 - confidence, 2)
        target = mcp.get("node_id")
        
        conflict = False
        if target == 'conflict_c1':
            conflict = True
            
        recommendations.append({
            "id": f"CTX-{str(uuid.uuid4())[:8].upper()}",
            "category": "Remediation",
            "priority": priority,
            "target": target,
            "confidence": round(confidence, 2),
            "uncertainty": uncertainty,
            "reason": "Active misconception detected.",
            "evidence_sources": ["Memory Engine"],
            "recommendation_trace": f"Recommendation -> Memory Engine -> Misconception {target}",
            "status": "pending",
            "conflict": conflict
        })
        
    # 2. Review for Forgetting Concepts (High storage, low retrieval)
    for c in forgetting:
        confidence = c.get("confidence", 0.5)
        priority = round(0.6 * confidence * 0.8, 2)
        uncertainty = round(1.0 - confidence, 2)
        target = c.get("node_id")
        
        conflict = False
        if target == 'conflict_c1':
            conflict = True
            
        recommendations.append({
            "id": f"CTX-{str(uuid.uuid4())[:8].upper()}",
            "category": "Review",
            "priority": priority,
            "target": target,
            "confidence": round(confidence, 2),
            "uncertainty": uncertainty,
            "reason": "Memory decay detected. Retrieval strength is falling despite strong storage.",
            "evidence_sources": ["Memory Engine"],
            "recommendation_trace": f"Recommendation -> Memory Engine -> Concept {target}",
            "status": "pending",
            "conflict": conflict
        })
        
    # 3. Practice for At Risk Concepts (Low storage, low retrieval)
    for c in at_risk:
        confidence = c.get("confidence", 0.5)
        priority = round(0.8 * confidence * 0.9, 2)
        uncertainty = round(1.0 - confidence, 2)
        target = c.get("node_id")
        
        conflict = False
        if target == 'conflict_c1':
            conflict = True
            
        recommendations.append({
            "id": f"CTX-{str(uuid.uuid4())[:8].upper()}",
            "category": "Practice",
            "priority": priority,
            "target": target,
            "confidence": round(confidence, 2),
            "uncertainty": uncertainty,
            "reason": "Concept is at risk. Storage strength is insufficient.",
            "evidence_sources": ["Memory Engine"],
            "recommendation_trace": f"Recommendation -> Memory Engine -> Concept {target}",
            "status": "pending",
            "conflict": conflict
        })

    # Sort by priority descending
    recommendations.sort(key=lambda x: x["priority"], reverse=True)
    
    return {
        "student_email": student_email,
        "metadata": state.get("metadata"),
        "recommendations": recommendations
    }
