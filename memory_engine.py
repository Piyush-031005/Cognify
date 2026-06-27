import math
import time
from datetime import datetime
from database import get_conn

MEMORY_MODEL_VERSION = "v1.0"

def calculate_time_diff_days(t1_iso, t2_iso):
    try:
        t1 = datetime.fromisoformat(t1_iso)
        t2 = datetime.fromisoformat(t2_iso)
        delta = t2 - t1
        return max(0.0, delta.total_seconds() / 86400.0) # return days
    except Exception:
        return 0.0

def record_memory_event(email, node_id, memory_type, update_reason, effectiveness_delta=0.0, timestamp_override=None):
    """
    Appends an event to the immutable student_memory_events log.
    Then derives the new state.
    """
    conn = get_conn()
    cur = conn.cursor()
    now_str = timestamp_override if timestamp_override else datetime.now().isoformat()
    
    # 1. First, we need to know what the derived state WAS right before this event
    prev_state = derive_current_state(email, node_id, up_to_time=now_str)
    
    # 2. Calculate new storage strength and retrieval strength based on the reason
    S = prev_state["storage_strength"]
    R = prev_state["retrieval_strength"]
    conf = prev_state["confidence"]
    evidence = prev_state["evidence_count"]
    
    if memory_type == 'concept':
        if update_reason == 'correct_answer':
            # Practice boosts storage strength and resets retrieval strength
            S = min(1.0, S + 0.1 * (1.0 - S))
            R = 1.0
            evidence += 1
            conf = min(1.0, conf + 0.05)
        elif update_reason == 'wrong_answer':
            # Wrong answers don't destroy storage, but hit retrieval confidence
            R = max(0.0, R - 0.2)
            evidence += 1
            conf = max(0.0, conf - 0.1)
            
    elif memory_type == 'misconception':
        if update_reason == 'initial_discovery':
            S = 0.8 # high initial storage for a misconception
            R = 1.0
            evidence = 1
            conf = 0.7
        elif update_reason == 'wrong_answer': # Student selected it again
            S = min(1.0, S + 0.1)
            R = 1.0
            evidence += 1
        elif update_reason == 'correct_answer': # Student avoided the misconception
            S = max(0.0, S - 0.2)
            R = max(0.0, R - 0.3)
            evidence += 1
            
    elif memory_type == 'intervention':
        if update_reason == 'intervention_applied':
            # effectiveness_delta impacts the related concept or misconception later
            R = 1.0
            S = min(1.0, S + effectiveness_delta)
            evidence += 1

    cur.execute("""
        INSERT INTO student_memory_events (
            student_email, node_id, memory_type, retrieval_strength, storage_strength,
            confidence, update_reason, evidence_count, effectiveness_delta,
            memory_model_version, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (email, node_id, memory_type, R, S, conf, update_reason, evidence, effectiveness_delta, MEMORY_MODEL_VERSION, now_str))
    
    conn.commit()
    conn.close()
    
    return {"status": "success", "derived_S": S, "derived_R": R}

def derive_current_state(email, node_id, up_to_time=None):
    """
    Replays the event log to derive the exact cognitive state at `up_to_time`.
    Implements Ebbinghaus forgetting: R = e^(-t / S)
    Also decays confidence based on time elapsed since last evidence.
    Returns predicted states at 7, 14, and 30 days with uncertainty.
    """
    if not up_to_time:
        up_to_time = datetime.now().isoformat()
        
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT * FROM student_memory_events 
        WHERE student_email = ? AND node_id = ? AND timestamp <= ?
        ORDER BY timestamp ASC
    """, (email, node_id, up_to_time))
    events = cur.fetchall()
    conn.close()
    
    if not events:
        return {
            "retrieval_strength": 0.0,
            "storage_strength": 0.1,
            "confidence": 0.0,
            "evidence_count": 0,
            "memory_type": "unknown",
            "last_event_time": None
        }
    
    current_S = 0.1
    current_R = 0.0
    current_conf = 0.0
    evidence = 0
    mem_type = events[0]["memory_type"]
    last_t = events[0]["timestamp"]
    
    for ev in events:
        days_passed = calculate_time_diff_days(last_t, ev["timestamp"])
        if days_passed > 0 and current_S > 0:
            effective_S = current_S * (1.0 + math.log1p(evidence)) 
            decay_factor = math.exp(-days_passed / effective_S)
            current_R = current_R * decay_factor
            
            # Confidence decay
            current_conf = current_conf * math.exp(-days_passed / 60.0)
            
        current_R = ev["retrieval_strength"]
        current_S = ev["storage_strength"]
        current_conf = ev["confidence"]
        evidence = ev["evidence_count"]
        last_t = ev["timestamp"]
        mem_type = ev["memory_type"]
        
    final_days_passed = calculate_time_diff_days(last_t, up_to_time)
    if final_days_passed > 0 and current_S > 0:
        effective_S = current_S * (1.0 + math.log1p(evidence))
        decay_factor = math.exp(-final_days_passed / effective_S)
        current_R = current_R * decay_factor
        current_conf = current_conf * math.exp(-final_days_passed / 60.0)
        
    # Predictions
    effective_S = current_S * (1.0 + math.log1p(evidence)) if current_S > 0 else 0.1
    def predict(days):
        base_r = current_R * math.exp(-days / effective_S)
        uncertainty = round(min(0.2, (days / 60.0) * (1.0 - current_conf)), 2)
        return {"value": round(base_r, 3), "uncertainty": uncertainty}
        
    return {
        "retrieval_strength": current_R,
        "storage_strength": current_S,
        "confidence": current_conf,
        "evidence_count": evidence,
        "memory_type": mem_type,
        "last_event_time": last_t,
        "predictions": {
            "7_days": predict(7),
            "14_days": predict(14),
            "30_days": predict(30)
        }
    }

def get_full_student_memory(email):
    """
    Returns the categorized cognitive state for the entire student.
    Categories: Mastered, At Risk, Forgetting, Misconceptions.
    """
    conn = get_conn()
    cur = conn.cursor()
    # Find all unique nodes the student has interacted with
    cur.execute("SELECT DISTINCT node_id FROM student_memory_events WHERE student_email = ?", (email,))
    nodes = [r["node_id"] for r in cur.fetchall()]
    conn.close()
    
    mastered = []
    at_risk = []
    forgetting = []
    misconceptions = []
    
    for node_id in nodes:
        state = derive_current_state(email, node_id)
        if state["memory_type"] == 'concept':
            if state["retrieval_strength"] >= 0.8:
                mastered.append({"node_id": node_id, **state})
            elif state["retrieval_strength"] < 0.5 and state["storage_strength"] > 0.6:
                # Strong storage but poor retrieval = Forgetting (needs review)
                forgetting.append({"node_id": node_id, **state})
            else:
                at_risk.append({"node_id": node_id, **state})
        elif state["memory_type"] == 'misconception':
            if state["retrieval_strength"] > 0.3:
                # Still holds the misconception
                misconceptions.append({"node_id": node_id, **state})
                
    return {
        "student_email": email,
        "mastered": mastered,
        "at_risk": at_risk,
        "forgetting": forgetting,
        "active_misconceptions": misconceptions
    }
