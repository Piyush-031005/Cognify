import sqlite3
import json
from datetime import datetime, timedelta
from database import get_conn

def calculate_recommendation_effectiveness(context_id):
    """
    Traces the full lifecycle: Generated -> Accepted -> Executed -> Outcome Measured -> Completed.
    Evaluates whether the student improved.
    """
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM teacher_recommendation_feedback WHERE context_id = ?", (context_id,))
    fb = cur.fetchone()
    
    if not fb:
        conn.close()
        return None
        
    fb_dict = dict(fb)
    
    if fb_dict["action_taken"] not in ["Accepted", "Modified"] or not fb_dict.get("executed_at"):
        cur.execute("UPDATE teacher_recommendation_feedback SET success_category = 'No Change', evidence_quality = 'Low' WHERE context_id = ?", (context_id,))
        conn.commit()
        conn.close()
        return {"success_category": "No Change", "evidence_quality": "Low"}
        
    executed_at = datetime.fromisoformat(fb_dict["executed_at"])
    outcome_window = fb_dict.get("outcome_window_days", 3)
    
    if datetime.now() < executed_at + timedelta(days=outcome_window):
        # Evaluation window hasn't passed yet
        conn.close()
        return {"success_category": "Pending"}
        
    # In a real system, we'd query student telemetry post-intervention to calculate `retrieval_strength`.
    # For now, we mock the evidence retrieval to demonstrate the categories.
    mock_telemetry_count = 6
    mock_improvement = 0.25
    
    evidence_quality = "High" if mock_telemetry_count > 5 else "Medium" if mock_telemetry_count > 1 else "Low"
    
    if mock_improvement > 0.2:
        success_category = "Strong Improvement"
    elif mock_improvement > 0.05:
        success_category = "Moderate Improvement"
    elif mock_improvement > -0.05:
        success_category = "No Change"
    else:
        success_category = "Regression"
        
    cur.execute("UPDATE teacher_recommendation_feedback SET success_category = ?, evidence_quality = ? WHERE context_id = ?", (success_category, evidence_quality, context_id))
    conn.commit()
    conn.close()
    
    return {"success_category": success_category, "evidence_quality": evidence_quality}

def get_teacher_trust_score(room_id):
    """
    Calculates Teacher Trust = Acceptance Rate x Execution Rate x Observed Success Rate
    """
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM teacher_recommendation_feedback")
    all_fb = cur.fetchall()
    conn.close()
    
    if not all_fb:
        return 0.0
        
    total_generated = len(all_fb) + 5 # mock some un-interacted recs
    total_interacted = len(all_fb)
    
    accepted = sum(1 for r in all_fb if r["action_taken"] in ["Accepted", "Modified"])
    executed = sum(1 for r in all_fb if r["executed_at"] is not None)
    successful = sum(1 for r in all_fb if r["success_category"] in ["Strong Improvement", "Moderate Improvement"])
    
    acceptance_rate = accepted / total_generated if total_generated > 0 else 0
    execution_rate = executed / accepted if accepted > 0 else 0
    success_rate = successful / executed if executed > 0 else 0
    
    trust_score = round(acceptance_rate * execution_rate * success_rate, 2)
    return trust_score

def generate_evidence_dashboard_metrics(room_id):
    """
    Generates time-series trends for the SIH Evidence Dashboard.
    """
    trust_score = get_teacher_trust_score(room_id)
    
    # Mocking trends for the dashboard
    trends = [
        {"week": "Week 1", "trust": max(0.0, trust_score - 0.2), "memory_recovery": 0.45, "misconception_resolution": 0.3},
        {"week": "Week 2", "trust": max(0.0, trust_score - 0.1), "memory_recovery": 0.55, "misconception_resolution": 0.4},
        {"week": "Week 3", "trust": trust_score, "memory_recovery": 0.72, "misconception_resolution": 0.65},
    ]
    
    return {
        "room_id": room_id,
        "current_teacher_trust": trust_score,
        "trends": trends,
        "evidence_quality_distribution": {
            "High": 45,
            "Medium": 35,
            "Low": 20
        }
    }
