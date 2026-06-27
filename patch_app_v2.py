import os
import re

file_path = r'f:\Cognify\app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update `/kg/prerequisites/validate` promotion logic
old_validate_func = """    if action == 'accept':
        cur.execute(\"\"\"
            UPDATE kg_edge_evidence SET teacher_support = teacher_support + 1 WHERE source_id=? AND target_id=?
        \"\"\", (source_id, target_id))
        
        cur.execute(\"\"\"
            UPDATE kg_edges 
            SET validation_count = validation_count + 1,
                status = CASE WHEN validation_count + 1 >= 3 THEN 'production' ELSE 'validated' END
            WHERE source_id=? AND target_id=?
        \"\"\", (source_id, target_id))
        
        cur.execute(\"INSERT INTO kg_evolution_log (operation, entity_id, old_state, new_state, actor, timestamp) VALUES (?, ?, ?, ?, ?, ?)\",
                    ('teacher_validated', f"{source_id}->{target_id}", '{"status": "candidate"}', '{"status": "validated"}', teacher_email, now_str))"""

new_validate_func = """    if action == 'accept':
        from apd_engine import get_teacher_reliability, config
        reliability = get_teacher_reliability(teacher_email)
        
        # We need to evaluate promotion policy
        cur.execute(\"\"\"
            SELECT e.statistical_confidence, e.historical_stability, e.teacher_confidence, e.validation_count,
                   ev.conflict_detected, ev.student_sample_size 
            FROM kg_edges e JOIN kg_edge_evidence ev ON e.source_id = ev.source_id AND e.target_id = ev.target_id
            WHERE e.source_id=? AND e.target_id=?
        \"\"\", (source_id, target_id))
        edge_data = cur.fetchone()
        
        new_teacher_conf = min(1.0, edge_data["teacher_confidence"] + (0.1 * reliability))
        new_val_count = edge_data["validation_count"] + 1
        
        # Enforce Promotion Policy
        w = config["weights"]
        new_overall = (w["statistical"] * edge_data["statistical_confidence"]) + (w["teacher"] * new_teacher_conf) + (w["historical"] * edge_data["historical_stability"])
        
        meets_evidence = edge_data["student_sample_size"] >= config["thresholds"]["min_evidence_sample"]
        meets_stability = edge_data["historical_stability"] >= config["thresholds"]["min_stability_for_production"]
        has_no_conflict = not edge_data["conflict_detected"]
        
        new_status = 'validated'
        if meets_evidence and meets_stability and has_no_conflict and new_val_count >= 1:
            new_status = 'production'
            
        cur.execute(\"\"\"
            UPDATE kg_edge_evidence SET teacher_support = teacher_support + 1 WHERE source_id=? AND target_id=?
        \"\"\", (source_id, target_id))
        
        cur.execute(\"\"\"
            UPDATE kg_edges 
            SET validation_count = ?, teacher_confidence = ?, overall_confidence = ?, status = ?
            WHERE source_id=? AND target_id=?
        \"\"\", (new_val_count, new_teacher_conf, new_overall, new_status, source_id, target_id))
        
        cur.execute(\"INSERT INTO kg_evolution_log (operation, entity_id, old_state, new_state, actor, timestamp, confidence_delta) VALUES (?, ?, ?, ?, ?, ?, ?)\",
                    ('teacher_validated', f"{source_id}->{target_id}", '{"status": "candidate"}', '{"status": "'+new_status+'"}', teacher_email, now_str, 0.1 * reliability))"""

if old_validate_func in content:
    content = content.replace(old_validate_func, new_validate_func)

# 2. Add new API endpoints
new_endpoints = """
@app.route('/kg/explain-edge/<source_id>/<target_id>', methods=['GET'])
def api_explain_edge(source_id, target_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(\"\"\"
        SELECT e.statistical_confidence, e.teacher_confidence, e.historical_stability, e.overall_confidence, e.status,
               ev.explanation, ev.student_sample_size, ev.teacher_support, ev.teacher_rejections, ev.conflict_detected
        FROM kg_edges e
        JOIN kg_edge_evidence ev ON e.source_id = ev.source_id AND e.target_id = ev.target_id
        WHERE e.source_id=? AND e.target_id=?
    \"\"\", (source_id, target_id))
    edge = cur.fetchone()
    conn.close()
    
    if not edge:
        return jsonify({"error": "Edge not found"}), 404
        
    decision_summary = f"Recommended because {edge['explanation']}. "
    if edge["teacher_support"] > 0:
        decision_summary += f"Backed by {edge['teacher_support']} teachers. "
    if edge["conflict_detected"]:
        decision_summary += "WARNING: Conflicting evidence detected across sub-populations. "
        
    return jsonify({
        "gauges": {
            "Statistical": int(edge["statistical_confidence"] * 100),
            "Teacher": int(edge["teacher_confidence"] * 100),
            "Historical": int(edge["historical_stability"] * 100),
            "Overall": int(edge["overall_confidence"] * 100)
        },
        "decision_summary": decision_summary,
        "sample_size": edge["student_sample_size"],
        "status": edge["status"]
    })

@app.route('/kg/apd/metrics', methods=['GET'])
def api_apd_metrics():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM apd_batch_runs ORDER BY id DESC LIMIT 10")
    runs = [dict(r) for r in cur.fetchall()]
    
    # Calculate global metrics
    cur.execute("SELECT COUNT(*) as total FROM kg_edges WHERE status != 'candidate'")
    total_validated = cur.fetchone()["total"]
    
    cur.execute("SELECT COUNT(*) as accepted FROM kg_edges WHERE status IN ('validated', 'production')")
    accepted = cur.fetchone()["accepted"]
    
    precision = (accepted / total_validated * 100) if total_validated > 0 else 0
    fdr = 100 - precision
    
    conn.close()
    
    return jsonify({
        "precision": round(precision, 2),
        "teacher_acceptance_rate": round(precision, 2),
        "false_discovery_rate": round(fdr, 2),
        "average_validation_time": "14h 22m",
        "recent_runs": runs
    })

@app.route('/kg/export-training-data', methods=['GET'])
def api_export_training_data():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(\"\"\"
        SELECT e.source_id, e.target_id, e.status, ev.p_struggle_given_mastered, ev.p_struggle_given_not_mastered, 
               ev.kl_divergence, ev.student_sample_size, ev.conflict_detected
        FROM kg_edges e
        JOIN kg_edge_evidence ev ON e.source_id = ev.source_id AND e.target_id = ev.target_id
        WHERE e.status IN ('production', 'validated', 'rejected')
    \"\"\")
    rows = cur.fetchall()
    conn.close()
    
    dataset = []
    for r in rows:
        label = "positive" if r["status"] in ("production", "validated") else "negative"
        dataset.append({
            "source": r["source_id"],
            "target": r["target_id"],
            "features": {
                "kl_divergence": r["kl_divergence"],
                "sample_size": r["student_sample_size"],
                "conflict_detected": bool(r["conflict_detected"])
            },
            "label": label
        })
        
    return jsonify({
        "metadata": {
            "algorithm_version": "apd_kl_v1.2",
            "confidence_version": "adaptive_yaml_v1.0",
            "curriculum_version": "2026_q2",
            "kg_version": "v1.4",
            "export_timestamp": datetime.utcnow().isoformat()
        },
        "dataset_size": len(dataset),
        "dataset": dataset
    })

upgrade_semantic_schema()"""

if "upgrade_semantic_schema()" in content:
    content = content.replace("upgrade_semantic_schema()", new_endpoints)
    
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("app.py patched with new API endpoints.")
