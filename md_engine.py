import json
import math
import uuid
import time
import os
from datetime import datetime
from database import get_conn
from apd_engine import config, get_teacher_reliability

def discover_misconceptions():
    """
    Misconception Discovery Engine.
    Pipeline:
    Student Responses -> Wrong Answer Patterns -> Behavior Signals -> Candidate Misconception -> Teacher Validation
    """
    start_time = time.time()
    conn = get_conn()
    cur = conn.cursor()
    now_str = datetime.now().isoformat()
    
    print("[MD Engine] Starting Misconception Discovery...")
    
    # 1. Find frequent wrong answer patterns
    # We look at questions with multiple wrong attempts and extract the most selected wrong option.
    # We join responses with raw_telemetry_events to find the selected option.
    # In a real system, we'd look for event_type='final_answer' or similar.
    # Since this is v1, we simulate extracting the most selected wrong option via telemetry.
    
    cur.execute("""
        SELECT r.question_id, 
               qb.semantic_id, qb.topic, qb.subtopic,
               COUNT(r.id) as wrong_count,
               AVG(r.response_time) as avg_time,
               AVG(r.hesitation_score) as avg_hesitation
        FROM responses r
        JOIN question_bank qb ON r.question_id = qb.id
        WHERE r.correct = 0
        GROUP BY r.question_id
        HAVING wrong_count >= 3
    """)
    
    patterns = cur.fetchall()
    candidates_generated = 0
    
    for pattern in patterns:
        q_id = pattern["question_id"]
        wrong_count = pattern["wrong_count"]
        avg_time = pattern["avg_time"]
        avg_hes = pattern["avg_hesitation"]
        topic = pattern["topic"]
        
        # 2. Consistency & Behavior Check
        # A true misconception usually has low hesitation (student is confident in their wrong answer).
        # And it shouldn't take excessively long.
        if avg_hes < 0.4 and avg_time < 45.0:
            # Consistent pattern detected. 
            
            # Simulated telemetry extraction for the exact distractor
            cur.execute("""
                SELECT event_value, COUNT(*) as selection_count 
                FROM raw_telemetry_events 
                WHERE question_id = ? AND event_type = 'option_selected'
                GROUP BY event_value
                ORDER BY selection_count DESC LIMIT 1
            """, (q_id,))
            telemetry = cur.fetchone()
            
            most_selected = telemetry["event_value"] if telemetry else "Option C"
            selection_rate = 0.85 # Simulated rate for demo
            
            canonical_id = f"MCP-{topic.upper()[:4]}-{str(q_id).zfill(5)}"
            
            # Check if this misconception already exists or was rejected
            cur.execute("SELECT id, status, validation_count FROM kg_nodes WHERE canonical_id = ?", (canonical_id,))
            existing = cur.fetchone()
            
            if existing:
                if existing["status"] == 'rejected':
                    # Never rediscover rejected misconceptions
                    continue
                else:
                    # Update confidence components if it already exists (Rediscovery)
                    node_id = existing["id"]
                    cur.execute("""
                        UPDATE kg_nodes 
                        SET statistical_confidence = min(1.0, statistical_confidence + 0.1),
                            historical_stability = min(1.0, historical_stability + 0.05)
                        WHERE id = ?
                    """, (node_id,))
                    
                    cur.execute("""
                        UPDATE kg_edge_evidence
                        SET student_sample_size = student_sample_size + ?
                        WHERE target_id = ?
                    """, (wrong_count, node_id))
            else:
                # Generate new Candidate Misconception
                node_id = str(uuid.uuid4())
                name = f"Common error in {topic}"
                desc = f"Students consistently select '{most_selected}'. They display low hesitation ({round(avg_hes, 2)}), indicating a persistent cognitive error rather than a guess."
                
                # Insert into kg_nodes
                cur.execute("""
                    INSERT INTO kg_nodes (
                        id, name, type, description, subject, topic, 
                        status, discovery_method, statistical_confidence, historical_stability, canonical_id
                    ) VALUES (?, ?, 'misconception', ?, 'Unknown', ?, 'candidate', 'md_engine', 0.6, 0.5, ?)
                """, (node_id, name, desc, topic, canonical_id))
                
                # Create candidate edge (Concept -> Misconception)
                # We need to find a parent concept for this question.
                cur.execute("""
                    SELECT concept_id FROM question_concepts WHERE question_id = ? LIMIT 1
                """, (q_id,))
                concept_rel = cur.fetchone()
                
                if concept_rel:
                    c_id = concept_rel["concept_id"]
                    
                    # Create edge: Concept causes_misconception Misconception
                    cur.execute("""
                        INSERT INTO kg_edges (
                            source_id, target_id, relation_type, weight, confidence,
                            discovery_method, discovery_date, status, stability_score,
                            statistical_confidence, teacher_confidence, historical_stability, overall_confidence
                        ) VALUES (?, ?, 'causes_misconception', 1.0, 0.6, 'md_engine', ?, 'candidate', 0.5, 0.6, 0.0, 0.5, 0.6)
                    """, (c_id, node_id, now_str))
                    
                    evidence_id = str(uuid.uuid4())
                    explanation = f"Based on {wrong_count} wrong attempts on Q{q_id} with low hesitation."
                    
                    cur.execute("""
                        INSERT INTO kg_edge_evidence (
                            id, source_id, target_id, relation_type, student_sample_size,
                            confidence_score, explanation, last_recomputed
                        ) VALUES (?, ?, ?, 'causes_misconception', ?, 0.6, ?, ?)
                    """, (evidence_id, c_id, node_id, wrong_count, explanation, now_str))
                    
                    cur.execute("""
                        INSERT INTO kg_evolution_log (operation, entity_id, old_state, new_state, actor, timestamp, confidence_delta)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, ('node_added', node_id, '{}', json.dumps({'status': 'candidate', 'type': 'misconception'}), 'system', now_str, 0.6))
                    
                    candidates_generated += 1

    conn.commit()
    conn.close()
    
    exec_time_ms = int((time.time() - start_time) * 1000)
    print(f"[MD Engine] Discovery complete. Generated {candidates_generated} misconception candidates in {exec_time_ms}ms.")
    return {
        "status": "success",
        "candidates_generated": candidates_generated,
        "execution_time_ms": exec_time_ms
    }
