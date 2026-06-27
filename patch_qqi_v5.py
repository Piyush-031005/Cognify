import os

file_path = r'f:\Cognify\qqi_engine.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

calibration_func = """
def calibrate_question(question_id):
    \"\"\"
    Phase 3: QQI Calibration Feedback Loop
    Calibrates the QQI score based on actual student cognitive memory states.
    Does NOT overwrite original qqi_score. Sets calibrated_qqi_score.
    \"\"\"
    from memory_engine import derive_current_state
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT qqi_score, difficulty FROM question_bank WHERE id = ?", (question_id,))
    q_row = cur.fetchone()
    if not q_row or q_row["qqi_score"] is None:
        conn.close()
        return None
        
    base_qqi = q_row["qqi_score"]
    base_difficulty = q_row["difficulty"]
    
    # Fetch all responses for this question
    cur.execute("SELECT student_email, correct FROM responses WHERE question_id = ?", (question_id,))
    responses = cur.fetchall()
    
    if not responses:
        conn.close()
        return None

    # Fetch concepts tested by this question
    cur.execute("SELECT concept_id FROM question_concepts WHERE question_id = ?", (question_id,))
    concept_ids = [r["concept_id"] for r in cur.fetchall()]
    
    total_weight = 0.0
    weighted_correct = 0.0
    high_memory_failures = 0
    low_memory_successes = 0
    
    for r in responses:
        email = r["student_email"]
        correct = r["correct"]
        
        # We need the memory state of the student for the tested concepts
        student_confidence = 0.1
        student_storage = 0.1
        
        if concept_ids:
            # Average memory state across concepts
            conf_sum = 0
            storage_sum = 0
            for cid in concept_ids:
                state = derive_current_state(email, cid)
                conf_sum += state["confidence"]
                storage_sum += state["storage_strength"]
                
            student_confidence = conf_sum / len(concept_ids)
            student_storage = storage_sum / len(concept_ids)
            
        # Weight by student memory confidence
        weight = max(0.1, student_confidence) # even low confidence students count a little
        total_weight += weight
        
        if correct:
            weighted_correct += weight
            if student_storage < 0.3:
                low_memory_successes += 1
        else:
            if student_storage > 0.8:
                high_memory_failures += 1
                
    if total_weight == 0:
        conn.close()
        return None
        
    actual_difficulty_ratio = 1.0 - (weighted_correct / total_weight) # 0.0 means everyone got it right, 1.0 means everyone got it wrong
    
    # Analyze drift and calibrate
    calibration_reason = "Normal calibration."
    calibrated_qqi = base_qqi
    
    if high_memory_failures > len(responses) * 0.2:
        # >20% of responses are from high memory students who failed
        calibrated_qqi -= 10.0
        calibration_reason = f"High Memory Failure detected ({high_memory_failures} instances)."
    
    if low_memory_successes > len(responses) * 0.2:
        # >20% of responses are from low memory students who succeeded
        calibrated_qqi -= 5.0
        calibration_reason = f"Low Guess Resistance detected ({low_memory_successes} instances)."
        
    calibrated_qqi = max(0.0, min(100.0, calibrated_qqi))
    
    # Re-evaluate difficulty label based on actual_difficulty_ratio
    calibrated_difficulty = base_difficulty
    if actual_difficulty_ratio > 0.7:
        calibrated_difficulty = 'hard'
    elif actual_difficulty_ratio < 0.3:
        calibrated_difficulty = 'easy'
    else:
        calibrated_difficulty = 'medium'
        
    cur.execute(\"\"\"
        UPDATE question_bank 
        SET calibrated_qqi_score = ?, calibrated_difficulty = ?
        WHERE id = ?
    \"\"\", (calibrated_qqi, calibrated_difficulty, question_id))
    
    cur.execute(\"\"\"
        INSERT INTO question_versions (
            question_id, version, qqi_before, qqi_after, calibration_reason, edited_at, edited_by
        ) VALUES (?, (SELECT current_version FROM question_bank WHERE id = ?), ?, ?, ?, ?, 'system')
    \"\"\", (question_id, question_id, base_qqi, calibrated_qqi, calibration_reason, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return {
        "base_qqi": base_qqi,
        "calibrated_qqi": calibrated_qqi,
        "shift": calibrated_qqi - base_qqi,
        "reason": calibration_reason
    }

def detect_calibration_drift():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT qqi_score, calibrated_qqi_score FROM question_bank WHERE calibrated_qqi_score IS NOT NULL")
    rows = cur.fetchall()
    conn.close()
    
    if not rows:
        return None
        
    shifts = [r["calibrated_qqi_score"] - r["qqi_score"] for r in rows]
    
    return {
        "average_shift": sum(shifts) / len(shifts),
        "largest_increase": max(shifts),
        "largest_decrease": min(shifts)
    }
"""

if "def calibrate_question" not in content:
    content += "\n" + calibration_func
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

print("qqi_engine.py patched with calibration feedback loop.")
