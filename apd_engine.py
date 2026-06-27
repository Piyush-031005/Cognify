import json
import math
import uuid
import time
from datetime import datetime
from database import get_conn

def detect_cycle(cur, new_source, new_target):
    """
    Returns True if adding new_source -> new_target would create a cycle.
    Basic DFS approach.
    """
    if new_source == new_target:
        return True
        
    cur.execute("SELECT source_id, target_id FROM kg_edges WHERE relation_type='prerequisite_of'")
    edges = cur.fetchall()
    
    graph = {}
    for edge in edges:
        s, t = edge["source_id"], edge["target_id"]
        if s not in graph:
            graph[s] = []
        graph[s].append(t)
        
    # Temporarily add the new edge to test for cycles
    if new_source not in graph:
        graph[new_source] = []
    graph[new_source].append(new_target)
    
    visited = set()
    rec_stack = set()
    
    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
                
        rec_stack.remove(node)
        return False
        
    # Check cycle starting from new_source
    return dfs(new_source)

def run_apd_discovery(subject, min_sample=50):
    start_time = time.time()
    conn = get_conn()
    cur = conn.cursor()
    
    print(f"[APD] Starting discovery for subject: {subject}")
    
    # 1. Fetch concepts for this subject
    cur.execute("SELECT id, name FROM kg_nodes WHERE subject = ? AND type = 'concept'", (subject,))
    concepts = cur.fetchall()
    concept_ids = [c["id"] for c in concepts]
    concept_names = {c["id"]: c["name"] for c in concepts}
    
    if len(concept_ids) < 2:
        print(f"[APD] Not enough concepts in {subject} to discover prerequisites.")
        return {"status": "error", "message": "Not enough concepts"}
        
    # 2. Fetch student mastery histories
    # To compute P(struggle_B | mastered_A), we look at students who have attempted B.
    # struggle_B means their mastery of B < 0.5 (or recent responses were incorrect).
    # mastered_A means their mastery of A >= 0.7.
    
    cur.execute("SELECT student_email, node_id, mastery_level FROM student_concept_mastery WHERE node_id IN ({seq})".format(seq=','.join(['?']*len(concept_ids))), concept_ids)
    mastery_data = cur.fetchall()
    
    student_profiles = {}
    for m in mastery_data:
        email = m["student_email"]
        if email not in student_profiles:
            student_profiles[email] = {}
        student_profiles[email][m["node_id"]] = m["mastery_level"]
        
    edges_tested = 0
    candidates_generated = 0
    now_str = datetime.now().isoformat()
    
    for c_a in concept_ids:
        for c_b in concept_ids:
            if c_a == c_b:
                continue
                
            edges_tested += 1
            
            # Find students who have a score for BOTH A and B
            valid_students = [email for email in student_profiles if c_a in student_profiles[email] and c_b in student_profiles[email]]
            
            sample_size = len(valid_students)
            if sample_size < min_sample:
                continue
                
            # Compute probabilities
            # Mastered A = mastery >= 0.7
            # Struggle B = mastery < 0.5
            
            mastered_a_count = 0
            struggle_b_given_mastered_a = 0
            
            not_mastered_a_count = 0
            struggle_b_given_not_mastered_a = 0
            
            for email in valid_students:
                mastery_a = student_profiles[email][c_a]
                mastery_b = student_profiles[email][c_b]
                
                struggling_b = mastery_b < 0.5
                
                if mastery_a >= 0.7:
                    mastered_a_count += 1
                    if struggling_b:
                        struggle_b_given_mastered_a += 1
                else:
                    not_mastered_a_count += 1
                    if struggling_b:
                        struggle_b_given_not_mastered_a += 1
                        
            # Need minimum counts to be statistically valid
            if mastered_a_count < 10 or not_mastered_a_count < 10:
                continue
                
            p_struggle_b_given_mastered_a = struggle_b_given_mastered_a / mastered_a_count
            p_struggle_b_given_not_mastered_a = struggle_b_given_not_mastered_a / not_mastered_a_count
            
            # Avoid division by zero in KL divergence
            epsilon = 1e-5
            p1 = max(epsilon, min(1 - epsilon, p_struggle_b_given_not_mastered_a))
            p2 = max(epsilon, min(1 - epsilon, p_struggle_b_given_mastered_a))
            
            # KL Divergence: D_KL(P || Q) = sum(P(x) * log(P(x) / Q(x)))
            # We want to see how much the distribution of B changes when A is NOT mastered vs when it IS mastered.
            # Large divergence means A has a strong causal effect on B.
            kl_div = p1 * math.log(p1 / p2) + (1 - p1) * math.log((1 - p1) / (1 - p2))
            
            # Mutual Information (simplified approximation for this binary split)
            p_struggle_b = (struggle_b_given_mastered_a + struggle_b_given_not_mastered_a) / sample_size
            p_mastered_a = mastered_a_count / sample_size
            
            # If KL divergence is high and P(Struggle B | ~Mastered A) > P(Struggle B | Mastered A)
            if kl_div > 0.1 and p_struggle_b_given_not_mastered_a > p_struggle_b_given_mastered_a + 0.15:
                # Cycle check
                if detect_cycle(cur, c_a, c_b):
                    continue
                    
                confidence = min(0.99, 0.5 + (kl_div * 0.5))
                
                # Check if edge already exists
                cur.execute("SELECT status FROM kg_edges WHERE source_id=? AND target_id=? AND relation_type='prerequisite_of'", (c_a, c_b))
                existing = cur.fetchone()
                
                if existing:
                    # Update confidence and stability if it exists
                    cur.execute("""
                        UPDATE kg_edges 
                        SET confidence = (confidence + ?) / 2.0, 
                            stability_score = min(1.0, stability_score + 0.05),
                            validation_count = validation_count + 1
                        WHERE source_id=? AND target_id=? AND relation_type='prerequisite_of'
                    """, (confidence, c_a, c_b))
                else:
                    # Create new candidate edge
                    cur.execute("""
                        INSERT INTO kg_edges (
                            source_id, target_id, relation_type, weight, confidence,
                            discovery_method, discovery_date, status, stability_score
                        ) VALUES (?, ?, 'prerequisite_of', 1.0, ?, 'kl_divergence', ?, 'candidate', 0.8)
                    """, (c_a, c_b, confidence, now_str))
                    
                    # Create evidence record
                    evidence_id = str(uuid.uuid4())
                    diff_pct = int((p_struggle_b_given_not_mastered_a - p_struggle_b_given_mastered_a) * 100)
                    explanation = f"Students who have not mastered '{concept_names[c_a]}' show a {diff_pct}% higher struggle rate on '{concept_names[c_b]}' compared to those who have."
                    
                    cur.execute("""
                        INSERT INTO kg_edge_evidence (
                            id, source_id, target_id, relation_type, student_sample_size,
                            p_struggle_given_mastered, p_struggle_given_not_mastered, kl_divergence,
                            confidence_score, explanation, last_recomputed
                        ) VALUES (?, ?, ?, 'prerequisite_of', ?, ?, ?, ?, ?, ?, ?)
                    """, (evidence_id, c_a, c_b, sample_size, p_struggle_b_given_mastered_a, 
                          p_struggle_b_given_not_mastered_a, kl_div, confidence, explanation, now_str))
                    
                    # Log evolution
                    cur.execute("""
                        INSERT INTO kg_evolution_log (operation, entity_id, old_state, new_state, actor, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ('edge_added', f"{c_a}->{c_b}", '{}', json.dumps({'status': 'candidate', 'method': 'kl_divergence'}), 'system', now_str))
                    
                    candidates_generated += 1

    exec_time_ms = int((time.time() - start_time) * 1000)
    
    # Save batch run metadata
    cur.execute("""
        INSERT INTO apd_batch_runs (
            run_date, subject, student_sample, concepts_analyzed, edges_tested, 
            candidates_generated, execution_time_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now_str, subject, len(student_profiles), len(concept_ids), edges_tested, candidates_generated, exec_time_ms))
    
    conn.commit()
    conn.close()
    
    print(f"[APD] Discovery complete. Generated {candidates_generated} candidates in {exec_time_ms}ms.")
    return {
        "status": "success",
        "candidates_generated": candidates_generated,
        "execution_time_ms": exec_time_ms
    }
