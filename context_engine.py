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
    
    # 1. Remediation for Active Misconceptions
    for mcp in active_misconceptions:
        confidence = mcp.get("confidence", 0.5)
        # Priority = Impact(High=0.9) * Confidence * Urgency(High=0.9)
        priority = round(0.9 * confidence * 0.9, 2)
        
        recommendations.append({
            "category": "Remediation",
            "priority": priority,
            "target": mcp.get("node_id"),
            "confidence": round(confidence, 2),
            "reason": "Active misconception detected.",
            "evidence_sources": ["Memory Engine"],
            "recommendation_trace": f"Recommendation -> Memory Engine -> Misconception {mcp.get('node_id')}"
        })
        
    # 2. Review for Forgetting Concepts (High storage, low retrieval)
    for c in forgetting:
        confidence = c.get("confidence", 0.5)
        # Impact is medium (0.6), Urgency is medium-high (0.8)
        priority = round(0.6 * confidence * 0.8, 2)
        
        recommendations.append({
            "category": "Review",
            "priority": priority,
            "target": c.get("node_id"),
            "confidence": round(confidence, 2),
            "reason": "Memory decay detected. Retrieval strength is falling despite strong storage.",
            "evidence_sources": ["Memory Engine"],
            "recommendation_trace": f"Recommendation -> Memory Engine -> Concept {c.get('node_id')}"
        })
        
    # 3. Practice for At Risk Concepts (Low storage, low retrieval)
    for c in at_risk:
        confidence = c.get("confidence", 0.5)
        # Impact is high (0.8), Urgency is high (0.9)
        priority = round(0.8 * confidence * 0.9, 2)
        
        recommendations.append({
            "category": "Practice",
            "priority": priority,
            "target": c.get("node_id"),
            "confidence": round(confidence, 2),
            "reason": "Concept is at risk. Storage strength is insufficient.",
            "evidence_sources": ["Memory Engine"],
            "recommendation_trace": f"Recommendation -> Memory Engine -> Concept {c.get('node_id')}"
        })

    # Sort by priority descending
    recommendations.sort(key=lambda x: x["priority"], reverse=True)
    
    return {
        "student_email": student_email,
        "metadata": state.get("metadata"),
        "recommendations": recommendations
    }
