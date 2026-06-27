import json
import math
import uuid
import time
import os
import yaml
from datetime import datetime
from database import get_conn

# Load Adaptive Weights Config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'confidence.yaml')
def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {
        "weights": {"statistical": 0.5, "teacher": 0.3, "historical": 0.2},
        "decay_rates": {"Default": 0.05},
        "teacher_reliability": {"senior_reviewer": 1.0, "regular_reviewer": 0.8, "new_reviewer": 0.4},
        "thresholds": {"min_evidence_sample": 50, "min_stability_for_production": 0.5, "retirement_confidence": 0.3}
    }

config = load_config()

def get_teacher_reliability(email):
    # Mock implementation - in reality this would query a teacher profile table
    if "senior" in email:
        return config["teacher_reliability"].get("senior_reviewer", 1.0)
    elif "new" in email:
        return config["teacher_reliability"].get("new_reviewer", 0.4)
    return config["teacher_reliability"].get("regular_reviewer", 0.8)

def get_domain_decay(subject):
    decay_rates = config.get("decay_rates", {})
    return decay_rates.get(subject, decay_rates.get("Default", 0.05))

def apply_confidence_decay(subject):
    """
    Decay historical stability over time based on domain.
    If overall confidence drops below retirement threshold, retire the edge.
    """
    conn = get_conn()
    cur = conn.cursor()
    now_str = datetime.now().isoformat()
    
    decay_rate = get_domain_decay(subject)
    
    # We apply decay to all candidates and production edges in the subject
    cur.execute("""
        SELECT e.source_id, e.target_id, e.historical_stability, e.overall_confidence, e.status
        FROM kg_edges e
        JOIN kg_nodes n ON e.source_id = n.id
        WHERE n.subject = ? AND e.status IN ('candidate', 'validated', 'production')
    """, (subject,))
    
    edges = cur.fetchall()
    retired_count = 0
    
    for edge in edges:
        s_id, t_id, stability, overall, status = edge["source_id"], edge["target_id"], edge["historical_stability"], edge["overall_confidence"], edge["status"]
        
        # Apply decay to historical stability
        new_stability = max(0.0, stability - decay_rate)
        
        # Recalculate overall confidence
        # Fetch current statistical and teacher confidences to recalculate
        cur.execute("SELECT statistical_confidence, teacher_confidence FROM kg_edges WHERE source_id=? AND target_id=?", (s_id, t_id))
        conf = cur.fetchone()
        stat_conf = conf["statistical_confidence"] if conf else 0.0
        teach_conf = conf["teacher_confidence"] if conf else 0.0
        
        w = config["weights"]
        new_overall = (w["statistical"] * stat_conf) + (w["teacher"] * teach_conf) + (w["historical"] * new_stability)
        
        new_status = status
        retirement_threshold = config["thresholds"].get("retirement_confidence", 0.3)
        if new_overall < retirement_threshold:
            new_status = 'retired'
            retired_count += 1
            
            cur.execute("""
                INSERT INTO kg_evolution_log (operation, entity_id, old_state, new_state, actor, timestamp, confidence_delta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('edge_retired', f"{s_id}->{t_id}", json.dumps({"status": status}), json.dumps({"status": new_status}), 'system', now_str, new_overall - overall))
        
        cur.execute("""
            UPDATE kg_edges 
            SET historical_stability = ?, overall_confidence = ?, status = ?
            WHERE source_id = ? AND target_id = ?
        """, (new_stability, new_overall, new_status, s_id, t_id))
        
    conn.commit()
    conn.close()
    print(f"[APD] Applied decay ({decay_rate}) for {subject}. Retired {retired_count} edges.")


def detect_cycle(cur, new_source, new_target):
    if new_source == new_target:
        return True
    cur.execute("SELECT source_id, target_id FROM kg_edges WHERE relation_type='prerequisite_of'")
    edges = cur.fetchall()
    graph = {}
    for edge in edges:
        s, t = edge["source_id"], edge["target_id"]
        if s not in graph: graph[s] = []
        graph[s].append(t)
    if new_source not in graph: graph[new_source] = []
    graph[new_source].append(new_target)
    visited = set()
    rec_stack = set()
    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor): return True
            elif neighbor in rec_stack: return True
        rec_stack.remove(node)
        return False
    return dfs(new_source)

def compute_kl_divergence(mastery_data_subset, c_a, c_b):
    mastered_a_count = 0
    struggle_b_given_mastered_a = 0
    not_mastered_a_count = 0
    struggle_b_given_not_mastered_a = 0
    
    for mastery_a, mastery_b in mastery_data_subset:
        struggling_b = mastery_b < 0.5
        if mastery_a >= 0.7:
            mastered_a_count += 1
            if struggling_b: struggle_b_given_mastered_a += 1
        else:
            not_mastered_a_count += 1
            if struggling_b: struggle_b_given_not_mastered_a += 1
            
    if mastered_a_count < 5 or not_mastered_a_count < 5:
        return 0, 0, 0
        
    p1_raw = struggle_b_given_not_mastered_a / not_mastered_a_count
    p2_raw = struggle_b_given_mastered_a / mastered_a_count
    
    epsilon = 1e-5
    p1 = max(epsilon, min(1 - epsilon, p1_raw))
    p2 = max(epsilon, min(1 - epsilon, p2_raw))
    
    kl_div = p1 * math.log(p1 / p2) + (1 - p1) * math.log((1 - p1) / (1 - p2))
    return kl_div, p1_raw, p2_raw

def run_apd_discovery(subject, min_sample=None):
    if min_sample is None:
        min_sample = config["thresholds"].get("min_evidence_sample", 50)
        
    start_time = time.time()
    conn = get_conn()
    cur = conn.cursor()
    
    print(f"[APD] Starting discovery for subject: {subject}")
    
    cur.execute("SELECT id, name FROM kg_nodes WHERE subject = ? AND type = 'concept'", (subject,))
    concepts = cur.fetchall()
    concept_ids = [c["id"] for c in concepts]
    concept_names = {c["id"]: c["name"] for c in concepts}
    
    if len(concept_ids) < 2:
        return {"status": "error", "message": "Not enough concepts"}
        
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
    
    w = config["weights"]
    
    for c_a in concept_ids:
        for c_b in concept_ids:
            if c_a == c_b:
                continue
                
            edges_tested += 1
            valid_students = [email for email in student_profiles if c_a in student_profiles[email] and c_b in student_profiles[email]]
            sample_size = len(valid_students)
            if sample_size < min_sample:
                continue
                
            # Compute global KL
            subset = [(student_profiles[email][c_a], student_profiles[email][c_b]) for email in valid_students]
            kl_div, p1_raw, p2_raw = compute_kl_divergence(subset, c_a, c_b)
            
            # Simulated Conflicting Evidence Detection (School A vs School B)
            # In a real system, we'd group by actual school_id metadata
            # Here we split by a hash of the email just to simulate sub-populations
            school_a_subset = []
            school_b_subset = []
            for email in valid_students:
                if hash(email) % 2 == 0:
                    school_a_subset.append((student_profiles[email][c_a], student_profiles[email][c_b]))
                else:
                    school_b_subset.append((student_profiles[email][c_a], student_profiles[email][c_b]))
                    
            kl_a, _, _ = compute_kl_divergence(school_a_subset, c_a, c_b)
            kl_b, _, _ = compute_kl_divergence(school_b_subset, c_a, c_b)
            
            conflict_detected = False
            conflict_details = ""
            if abs(kl_a - kl_b) > 0.5 and min(len(school_a_subset), len(school_b_subset)) >= min_sample / 2:
                conflict_detected = True
                conflict_details = json.dumps({
                    "school_a_kl": round(kl_a, 3), 
                    "school_b_kl": round(kl_b, 3),
                    "divergence_diff": round(abs(kl_a - kl_b), 3)
                })
            
            if kl_div > 0.1 and p1_raw > p2_raw + 0.15:
                if detect_cycle(cur, c_a, c_b):
                    continue
                    
                statistical_confidence = min(1.0, 0.5 + (kl_div * 0.5))
                teacher_confidence = 0.0 # Initial AI discovery
                historical_stability = 0.8
                
                overall_confidence = (w["statistical"] * statistical_confidence) + (w["teacher"] * teacher_confidence) + (w["historical"] * historical_stability)
                
                cur.execute("SELECT status, validation_count FROM kg_edges WHERE source_id=? AND target_id=? AND relation_type='prerequisite_of'", (c_a, c_b))
                existing = cur.fetchone()
                
                if existing:
                    # Update edge
                    cur.execute("""
                        UPDATE kg_edges 
                        SET statistical_confidence = (statistical_confidence + ?) / 2.0, 
                            historical_stability = min(1.0, historical_stability + 0.05),
                            overall_confidence = (? + (overall_confidence*validation_count)) / (validation_count + 1),
                            validation_count = validation_count + 1
                        WHERE source_id=? AND target_id=? AND relation_type='prerequisite_of'
                    """, (statistical_confidence, overall_confidence, c_a, c_b))
                    
                    cur.execute("""
                        UPDATE kg_edge_evidence
                        SET conflict_detected = ?, conflict_details = ?, kl_divergence = ?
                        WHERE source_id=? AND target_id=?
                    """, (conflict_detected, conflict_details, kl_div, c_a, c_b))
                else:
                    cur.execute("""
                        INSERT INTO kg_edges (
                            source_id, target_id, relation_type, weight, confidence,
                            discovery_method, discovery_date, status, stability_score,
                            statistical_confidence, teacher_confidence, historical_stability, overall_confidence
                        ) VALUES (?, ?, 'prerequisite_of', 1.0, ?, 'kl_divergence', ?, 'candidate', 0.8, ?, ?, ?, ?)
                    """, (c_a, c_b, overall_confidence, now_str, statistical_confidence, teacher_confidence, historical_stability, overall_confidence))
                    
                    evidence_id = str(uuid.uuid4())
                    diff_pct = int((p1_raw - p2_raw) * 100)
                    explanation = f"Students who have not mastered '{concept_names[c_a]}' show a {diff_pct}% higher struggle rate on '{concept_names[c_b]}' compared to those who have."
                    
                    cur.execute("""
                        INSERT INTO kg_edge_evidence (
                            id, source_id, target_id, relation_type, student_sample_size,
                            p_struggle_given_mastered, p_struggle_given_not_mastered, kl_divergence,
                            confidence_score, explanation, last_recomputed, conflict_detected, conflict_details
                        ) VALUES (?, ?, ?, 'prerequisite_of', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (evidence_id, c_a, c_b, sample_size, p2_raw, p1_raw, kl_div, overall_confidence, explanation, now_str, conflict_detected, conflict_details))
                    
                    cur.execute("""
                        INSERT INTO kg_evolution_log (operation, entity_id, old_state, new_state, actor, timestamp, confidence_delta)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, ('edge_added', f"{c_a}->{c_b}", '{}', json.dumps({'status': 'candidate', 'method': 'kl_divergence'}), 'system', now_str, overall_confidence))
                    
                    candidates_generated += 1

    exec_time_ms = int((time.time() - start_time) * 1000)
    
    cur.execute("""
        INSERT INTO apd_batch_runs (
            run_date, subject, student_sample, concepts_analyzed, edges_tested, 
            candidates_generated, execution_time_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now_str, subject, len(student_profiles), len(concept_ids), edges_tested, candidates_generated, exec_time_ms))
    
    conn.commit()
    conn.close()
    
    apply_confidence_decay(subject)
    
    print(f"[APD] Discovery complete. Generated {candidates_generated} candidates in {exec_time_ms}ms.")
    return {
        "status": "success",
        "candidates_generated": candidates_generated,
        "execution_time_ms": exec_time_ms
    }
