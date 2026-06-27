import os

file_path = r'f:\Cognify\memory_engine.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace derive_current_state to include confidence decay and predictions
new_derive = """def derive_current_state(email, node_id, up_to_time=None):
    \"\"\"
    Replays the event log to derive the exact cognitive state at `up_to_time`.
    Implements Ebbinghaus forgetting: R = e^(-t / S)
    Also decays confidence based on time elapsed since last evidence.
    Returns predicted states at 7, 14, and 30 days with uncertainty.
    \"\"\"
    if not up_to_time:
        up_to_time = datetime.now().isoformat()
        
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute(\"\"\"
        SELECT * FROM student_memory_events 
        WHERE student_email = ? AND node_id = ? AND timestamp <= ?
        ORDER BY timestamp ASC
    \"\"\", (email, node_id, up_to_time))
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
"""

if "predictions" not in content:
    # Use split to replace the old derive_current_state
    parts = content.split("def derive_current_state(email, node_id, up_to_time=None):")
    next_func = parts[1].split("def get_full_student_memory(email):")
    new_content = parts[0] + new_derive + "\ndef get_full_student_memory(email):" + next_func[1]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

print("memory_engine.py patched with predictions and confidence decay.")
