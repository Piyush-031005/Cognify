import json
import math
import uuid
import time
import os
import yaml
from datetime import datetime
from database import get_conn, get_apd_config

# Load configuration - prioritizing DB config, falling back to YAML/defaults
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'confidence.yaml')
def load_config():
    db_cfg = get_apd_config()
    if db_cfg:
        return db_cfg
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {
        "STAT_WEIGHT": 0.4,
        "TEACHER_WEIGHT": 0.3,
        "HISTORY_WEIGHT": 0.2,
        "SAMPLE_WEIGHT": 0.1,
        "MIN_SAMPLE_SIZE": 30,
        "EFFECT_SIZE_THRESHOLD": 0.15,
        "DEPRECATE_THRESHOLD": 0.4,
        "DECAY_LAMBDA": 0.005,
        "HISTORY_WINDOW": 30
    }

def get_teacher_reliability(email):
    # Mock implementation of teacher reliability matching standard values
    if "senior" in email:
        return 1.0
    elif "new" in email:
        return 0.4
    return 0.8

def get_student_cohort_metadata(email, cur):
    """
    Retrieves student cohort metadata from the users table.
    """
    cur.execute("SELECT education FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    edu = row["education"] if row else None
    
    metadata = {
        "cohort_id": "default_cohort",
        "institution": "default_institution",
        "grade": "undergraduate",
        "curriculum": "default_curriculum",
        "academic_year": "2026"
    }
    
    if edu:
        try:
            parsed = json.loads(edu)
            if isinstance(parsed, dict):
                metadata["cohort_id"] = parsed.get("cohort_id", metadata["cohort_id"])
                metadata["institution"] = parsed.get("institution", metadata["institution"])
                metadata["grade"] = parsed.get("grade", metadata["grade"])
                metadata["curriculum"] = parsed.get("curriculum", metadata["curriculum"])
                metadata["academic_year"] = parsed.get("academic_year", metadata["academic_year"])
        except Exception:
            metadata["grade"] = edu
            
    return metadata

def apply_confidence_decay(subject):
    """
    Applies temporal exponential confidence decay to prerequisite edges.
    Formula: confidence_today = confidence_previous * e^(-lambda * days)
    """
    cfg = load_config()
    decay_lambda = cfg.get("DECAY_LAMBDA", 0.005)
    deprecate_threshold = cfg.get("DEPRECATE_THRESHOLD", 0.4)
    
    conn = get_conn()
    cur = conn.cursor()
    now_str = datetime.now().isoformat()
    now_dt = datetime.now()
    
    cur.execute("""
        SELECT e.source_id, e.target_id, e.overall_confidence, e.historical_stability, e.status, e.edge_id,
               (SELECT MAX(last_updated) FROM kg_edge_evidence WHERE source_id = e.source_id AND target_id = e.target_id) as last_updated
        FROM kg_edges e
        JOIN kg_nodes n ON e.source_id = n.id
        WHERE n.subject = ? AND e.relation_type = 'prerequisite_of' AND e.status IN ('candidate', 'reviewing', 'validated')
    """, (subject,))
    
    edges = cur.fetchall()
    decayed_count = 0
    
    for edge in edges:
        s_id, t_id, overall, stability, status, edge_id, last_updated_str = (
            edge["source_id"], edge["target_id"], edge["overall_confidence"], 
            edge["historical_stability"], edge["status"], edge["edge_id"], edge["last_updated"]
        )
        
        days = 1.0
        if last_updated_str:
            try:
                last_dt = datetime.fromisoformat(last_updated_str)
                days = max(0.0, (now_dt - last_dt).total_seconds() / 86400.0)
            except Exception:
                pass
                
        # Decay historical stability
        new_stability = max(0.0, stability * math.exp(-decay_lambda * days))
        
        # Recalculate overall confidence
        stat_weight = cfg.get("STAT_WEIGHT", 0.4)
        teacher_weight = cfg.get("TEACHER_WEIGHT", 0.3)
        history_weight = cfg.get("HISTORY_WEIGHT", 0.2)
        sample_weight = cfg.get("SAMPLE_WEIGHT", 0.1)
        
        # Get latest evidence values
        cur.execute("""
            SELECT confidence_score, sample_size 
            FROM kg_edge_evidence 
            WHERE source_id = ? AND target_id = ? 
            ORDER BY last_updated DESC LIMIT 1
        """, (s_id, t_id))
        ev = cur.fetchone()
        stat_conf = ev["confidence_score"] if ev else 0.5
        total_samples = ev["sample_size"] if ev else 0
        
        # Get teacher reliability confidence
        cur.execute("""
            SELECT SUM(teacher_support) as support, SUM(teacher_rejections) as rejections 
            FROM kg_edge_evidence 
            WHERE source_id = ? AND target_id = ?
        """, (s_id, t_id))
        votes = cur.fetchone()
        support = votes["support"] or 0
        rejections = votes["rejections"] or 0
        teacher_conf = support / (support + rejections) if (support + rejections) > 0 else 0.5
        
        min_sample = cfg.get("MIN_SAMPLE_SIZE", 30)
        sample_reliability = min(1.0, total_samples / min_sample) if min_sample > 0 else 1.0
        
        new_overall = (stat_weight * stat_conf) + (teacher_weight * teacher_conf) + (history_weight * new_stability) + (sample_weight * sample_reliability)
        
        new_status = status
        # If overall confidence drops below deprecate threshold, move to deprecated
        if new_overall < deprecate_threshold and status != 'deprecated':
            new_status = 'deprecated'
            decayed_count += 1
            
            cur.execute("""
                INSERT INTO kg_evolution_log (operation, entity_id, edge_id, old_confidence, new_confidence, reason, actor, timestamp, model_version, confidence_delta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'v2.0', ?)
            """, ('edge_deprecated', f"{s_id}->{t_id}", edge_id, overall, new_overall, f"Confidence decayed below deprecation threshold ({deprecate_threshold}) after {round(days, 2)} days", 'system', now_str, new_overall - overall))
        else:
            cur.execute("""
                INSERT INTO kg_evolution_log (operation, entity_id, edge_id, old_confidence, new_confidence, reason, actor, timestamp, model_version, confidence_delta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'v2.0', ?)
            """, ('edge_decayed', f"{s_id}->{t_id}", edge_id, overall, new_overall, f"Confidence decayed after {round(days, 2)} days", 'system', now_str, new_overall - overall))
            
        cur.execute("""
            UPDATE kg_edges 
            SET historical_stability = ?, overall_confidence = ?, status = ?
            WHERE source_id = ? AND target_id = ?
        """, (new_stability, new_overall, new_status, s_id, t_id))
        
    conn.commit()
    conn.close()
    print(f"[APD] Temporal decay applied for {subject}. Deprecated {decayed_count} edges.")

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
    cfg = load_config()
    min_sample_size = min_sample or cfg.get("MIN_SAMPLE_SIZE", 30)
    effect_size_threshold = cfg.get("EFFECT_SIZE_THRESHOLD", 0.15)
    deprecate_threshold = cfg.get("DEPRECATE_THRESHOLD", 0.4)
    
    stat_weight = cfg.get("STAT_WEIGHT", 0.4)
    teacher_weight = cfg.get("TEACHER_WEIGHT", 0.3)
    history_weight = cfg.get("HISTORY_WEIGHT", 0.2)
    sample_weight = cfg.get("SAMPLE_WEIGHT", 0.1)
    
    start_time = time.time()
    conn = get_conn()
    cur = conn.cursor()
    
    print(f"[APD] Starting APD v2 discovery for subject: {subject}")
    
    # Fetch concepts
    cur.execute("SELECT id, name FROM kg_nodes WHERE subject = ? AND type = 'concept'", (subject,))
    concepts = cur.fetchall()
    concept_ids = [c["id"] for c in concepts]
    concept_names = {c["id"]: c["name"] for c in concepts}
    
    if len(concept_ids) < 2:
        conn.close()
        return {"status": "error", "message": "Not enough concepts"}
        
    # Fetch student concept mastery
    cur.execute("SELECT student_email, node_id, mastery_level FROM student_concept_mastery WHERE node_id IN ({seq})".format(seq=','.join(['?']*len(concept_ids))), concept_ids)
    mastery_data = cur.fetchall()
    
    # Fetch student metadata for cohort grouping
    student_cohorts = {}
    unique_emails = list({m["student_email"] for m in mastery_data})
    for email in unique_emails:
        student_cohorts[email] = get_student_cohort_metadata(email, cur)
        
    student_profiles = {}
    for m in mastery_data:
        email = m["student_email"]
        if email not in student_profiles:
            student_profiles[email] = {}
        student_profiles[email][m["node_id"]] = m["mastery_level"]
        
    edges_tested = 0
    candidates_generated = 0
    now_str = datetime.now().isoformat()
    
    # Process pairs
    for c_a in concept_ids:
        for c_b in concept_ids:
            if c_a == c_b:
                continue
                
            edges_tested += 1
            valid_students = [email for email in student_profiles if c_a in student_profiles[email] and c_b in student_profiles[email]]
            if len(valid_students) < min_sample_size:
                continue
                
            # Group valid students by cohort_id
            cohort_groups = {}
            for email in valid_students:
                ch_id = student_cohorts[email]["cohort_id"]
                if ch_id not in cohort_groups:
                    cohort_groups[ch_id] = []
                cohort_groups[ch_id].append(email)
                
            cohort_evidence = []
            
            # Analyze each cohort independently
            for ch_id, ch_students in cohort_groups.items():
                ch_sample = len(ch_students)
                if ch_sample < 5: # Cohort too small for analysis
                    continue
                    
                subset = [(student_profiles[email][c_a], student_profiles[email][c_b]) for email in ch_students]
                kl_div, p1_raw, p2_raw = compute_kl_divergence(subset, c_a, c_b)
                
                # Check for prerequisite logic: struggle rate diff
                effect_size = p1_raw - p2_raw
                if kl_div > 0.05 and effect_size > 0.05:
                    # Supporting students:
                    # A struggle, B struggle: mastery_a < 0.5 and mastery_b < 0.5
                    # A master, B master: mastery_a >= 0.7 and mastery_b >= 0.7
                    supporting = sum(1 for ma, mb in subset if (ma < 0.5 and mb < 0.5) or (ma >= 0.7 and mb >= 0.7))
                    
                    # Contradicting students:
                    # B mastered, A struggle: mastery_b >= 0.7 and mastery_a < 0.5
                    contradicting = sum(1 for ma, mb in subset if mb >= 0.7 and ma < 0.5)
                    
                    contradiction_penalty = contradicting / ch_sample if ch_sample > 0 else 0.0
                    stat_conf = min(1.0, max(0.0, (0.5 + kl_div * 0.5) * (1.0 - contradiction_penalty)))
                    
                    meta = student_cohorts[ch_students[0]]
                    
                    cohort_evidence.append({
                        "cohort_id": ch_id,
                        "institution": meta["institution"],
                        "grade": meta["grade"],
                        "curriculum": meta["curriculum"],
                        "academic_year": meta["academic_year"],
                        "supporting_students": supporting,
                        "contradicting_students": contradicting,
                        "sample_size": ch_sample,
                        "kl_divergence": kl_div,
                        "effect_size": effect_size,
                        "confidence_score": stat_conf,
                        "p1_raw": p1_raw,
                        "p2_raw": p2_raw
                    })
            
            # Weighted aggregation across cohorts
            if not cohort_evidence:
                continue
                
            total_samples = sum(c["sample_size"] for c in cohort_evidence)
            if total_samples < min_sample_size:
                continue
                
            weighted_stat_conf = sum(c["confidence_score"] * c["sample_size"] for c in cohort_evidence) / total_samples
            weighted_effect_size = sum(c["effect_size"] * c["sample_size"] for c in cohort_evidence) / total_samples
            
            # APD prerequisite discovery threshold checks
            if weighted_stat_conf > 0.4 and weighted_effect_size >= effect_size_threshold:
                if detect_cycle(cur, c_a, c_b):
                    continue
                    
                # Stable edge ID mapping
                cur.execute("SELECT edge_id, status, overall_confidence, historical_stability FROM kg_edges WHERE source_id=? AND target_id=?", (c_a, c_b))
                existing_edge = cur.fetchone()
                
                if existing_edge and existing_edge["edge_id"]:
                    edge_id = existing_edge["edge_id"]
                else:
                    cur.execute("SELECT edge_id FROM kg_edge_evidence WHERE source_id=? AND target_id=? AND edge_id IS NOT NULL LIMIT 1", (c_a, c_b))
                    ev_row = cur.fetchone()
                    if ev_row and ev_row["edge_id"]:
                        edge_id = ev_row["edge_id"]
                    else:
                        cur.execute("SELECT MAX(CAST(SUBSTR(edge_id, 5) AS INTEGER)) as max_val FROM kg_edges WHERE edge_id LIKE 'apd_%'")
                        max_val = cur.fetchone()["max_val"]
                        if max_val is None:
                            cur.execute("SELECT MAX(CAST(SUBSTR(edge_id, 5) AS INTEGER)) as max_val FROM kg_edge_evidence WHERE edge_id LIKE 'apd_%'")
                            max_val = cur.fetchone()["max_val"]
                        val = (max_val or 0) + 1
                        edge_id = f"apd_{str(val).zfill(6)}"
                
                # Retrieve teacher validations
                cur.execute("SELECT SUM(teacher_support) as support, SUM(teacher_rejections) as rejections FROM kg_edge_evidence WHERE source_id=? AND target_id=?", (c_a, c_b))
                votes = cur.fetchone()
                support = votes["support"] or 0
                rejections = votes["rejections"] or 0
                teacher_conf = support / (support + rejections) if (support + rejections) > 0 else 0.5
                
                historical_stability = existing_edge["historical_stability"] if existing_edge else 0.8
                sample_reliability = min(1.0, total_samples / min_sample_size)
                
                overall_confidence = (stat_weight * weighted_stat_conf) + (teacher_weight * teacher_conf) + (history_weight * historical_stability) + (sample_weight * sample_reliability)
                
                old_conf = existing_edge["overall_confidence"] if existing_edge else 0.0
                
                # Status progression:
                # If rejected or deprecated, we respect human status choices.
                status = existing_edge["status"] if existing_edge else "candidate"
                if status not in ("rejected", "deprecated", "validated"):
                    status = "candidate"
                        
                # Deprecated transition check
                if overall_confidence < deprecate_threshold and status != "rejected":
                    status = "deprecated"
                
                # Append-Only Evidence Ledger insertion
                for ch in cohort_evidence:
                    evidence_uuid = str(uuid.uuid4())
                    explanation = f"Prerequisite {concept_names[c_a]} -> {concept_names[c_b]} discovered in cohort {ch['cohort_id']}. Effect size is {round(ch['effect_size'], 2)}."
                    cur.execute("""
                        INSERT INTO kg_edge_evidence (
                            id, edge_id, source_id, target_id, relation_type, 
                            teacher_support, teacher_rejections, student_sample_size,
                            p_struggle_given_mastered, p_struggle_given_not_mastered, kl_divergence,
                            confidence_score, explanation, last_recomputed, conflict_detected, conflict_details,
                            supporting_students, contradicting_students, effect_size, last_updated,
                            algorithm_version, sample_size, status, cohort_id, institution, grade, curriculum, academic_year,
                            graph_version, qqi_version, model_version
                        ) VALUES (?, ?, ?, ?, 'prerequisite_of', 0, 0, ?, ?, ?, ?, ?, ?, ?, 0, '', ?, ?, ?, ?, 'v2.0', ?, ?, ?, ?, ?, ?, ?, 'v2.1', 'v1.2', 'v2.0')
                    """, (
                        evidence_uuid, edge_id, c_a, c_b, ch["sample_size"],
                        ch["p2_raw"], ch["p1_raw"], ch["kl_divergence"], ch["confidence_score"],
                        explanation, now_str, ch["supporting_students"], ch["contradicting_students"],
                        ch["effect_size"], now_str, ch["sample_size"], status, ch["cohort_id"],
                        ch["institution"], ch["grade"], ch["curriculum"], ch["academic_year"]
                    ))
                
                # Write to kg_edges
                if existing_edge:
                    cur.execute("""
                        UPDATE kg_edges
                        SET overall_confidence = ?, status = ?, historical_stability = min(1.0, historical_stability + 0.02),
                            validation_count = validation_count + 1
                        WHERE source_id = ? AND target_id = ? AND relation_type = 'prerequisite_of'
                    """, (overall_confidence, status, c_a, c_b))
                else:
                    cur.execute("""
                        INSERT INTO kg_edges (
                            source_id, target_id, relation_type, weight, confidence, 
                            discovery_method, discovery_date, status, stability_score,
                            statistical_confidence, teacher_confidence, historical_stability, overall_confidence, edge_id
                        ) VALUES (?, ?, 'prerequisite_of', 1.0, ?, 'kl_divergence', ?, ?, 0.8, ?, ?, 0.8, ?, ?)
                    """, (c_a, c_b, overall_confidence, now_str, status, weighted_stat_conf, teacher_conf, overall_confidence, edge_id))
                    candidates_generated += 1
                
                # Append to Evolution history log
                cur.execute("""
                    INSERT INTO kg_evolution_log (
                        operation, entity_id, edge_id, old_confidence, new_confidence, reason, actor, timestamp, model_version, confidence_delta
                    ) VALUES (?, ?, ?, ?, ?, ?, 'system', ?, 'v2.0', ?)
                """, (
                    'node_added' if not existing_edge else 'edge_evolved',
                    f"{c_a}->{c_b}", edge_id, old_conf, overall_confidence,
                    f"Evolution run updated overall confidence to {round(overall_confidence, 2)}. Status is {status}.",
                    now_str, overall_confidence - old_conf
                ))
                
    # Insert batch run log
    cur.execute("""
        INSERT INTO apd_batch_runs (run_date, subject, student_sample, concepts_analyzed, edges_tested, candidates_generated, execution_time_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now_str, subject, len(unique_emails), len(concept_ids), edges_tested, candidates_generated, int((time.time() - start_time) * 1000)))
    
    conn.commit()
    conn.close()
    
    # Trigger temporal decay
    apply_confidence_decay(subject)
    
    exec_time_ms = int((time.time() - start_time) * 1000)
    print(f"[APD] APD v2 discovery complete. Generated {candidates_generated} candidates in {exec_time_ms}ms.")
    
    return {
        "status": "success",
        "candidates_generated": candidates_generated,
        "execution_time_ms": exec_time_ms
    }

class ConfigDict(dict):
    def __getitem__(self, key):
        cfg = load_config()
        if key == "weights":
            return {
                "statistical": cfg.get("STAT_WEIGHT", 0.4),
                "teacher": cfg.get("TEACHER_WEIGHT", 0.3),
                "historical": cfg.get("HISTORY_WEIGHT", 0.2),
                "sample": cfg.get("SAMPLE_WEIGHT", 0.1)
            }
        elif key == "decay_rates":
            return {"Default": cfg.get("DECAY_LAMBDA", 0.005), "Math": cfg.get("DECAY_LAMBDA", 0.005)}
        elif key == "thresholds":
            return {
                "min_evidence_sample": cfg.get("MIN_SAMPLE_SIZE", 30),
                "min_stability_for_production": cfg.get("DEPRECATE_THRESHOLD", 0.4),
                "retirement_confidence": cfg.get("DEPRECATE_THRESHOLD", 0.4)
            }
        return super().__getitem__(key)
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

config = ConfigDict()
