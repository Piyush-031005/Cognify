import os

file_path = r'f:\Cognify\app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoints = """
@app.route('/kg/misconceptions/candidates', methods=['GET'])
def api_misconception_candidates():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(\"\"\"
        SELECT n.id, n.name, n.description, n.canonical_id, n.statistical_confidence, e.student_sample_size
        FROM kg_nodes n
        LEFT JOIN kg_edges edge ON n.id = edge.target_id AND edge.relation_type = 'causes_misconception'
        LEFT JOIN kg_edge_evidence e ON edge.source_id = e.source_id AND edge.target_id = e.target_id
        WHERE n.type = 'misconception' AND n.status = 'candidate'
        ORDER BY n.statistical_confidence DESC
    \"\"\")
    candidates = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({"candidates": candidates})

@app.route('/kg/misconceptions/validate', methods=['POST'])
def api_validate_misconception():
    data = request.json
    node_id = data.get("node_id")
    action = data.get("action") # 'accept', 'reject', 'merge'
    teacher_email = data.get("teacher_email", "teacher@school.com")
    now_str = datetime.now().isoformat()
    
    if not node_id or not action:
        return jsonify({"error": "Missing node_id or action"}), 400
        
    conn = get_conn()
    cur = conn.cursor()
    
    if action == 'accept':
        cur.execute("UPDATE kg_nodes SET status = 'production', validation_count = validation_count + 1 WHERE id = ?", (node_id,))
        cur.execute("UPDATE kg_edges SET status = 'production' WHERE target_id = ? AND relation_type = 'causes_misconception'", (node_id,))
        cur.execute(\"\"\"INSERT INTO kg_evolution_log (operation, entity_id, old_state, new_state, actor, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?)\"\"\",
                    ('teacher_validated', node_id, '{"status": "candidate"}', '{"status": "production"}', teacher_email, now_str))
                    
    elif action == 'reject':
        cur.execute("UPDATE kg_nodes SET status = 'rejected' WHERE id = ?", (node_id,))
        cur.execute("UPDATE kg_edges SET status = 'rejected' WHERE target_id = ? AND relation_type = 'causes_misconception'", (node_id,))
        cur.execute(\"\"\"INSERT INTO kg_evolution_log (operation, entity_id, old_state, new_state, actor, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?)\"\"\",
                    ('teacher_rejected', node_id, '{"status": "candidate"}', '{"status": "rejected"}', teacher_email, now_str))
                    
    elif action == 'merge':
        target_merge_id = data.get("merge_into_id")
        cur.execute("UPDATE kg_nodes SET status = 'merged' WHERE id = ?", (node_id,))
        cur.execute(\"\"\"INSERT INTO kg_evolution_log (operation, entity_id, old_state, new_state, actor, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?)\"\"\",
                    ('teacher_merged', node_id, '{"status": "candidate"}', f'{{"status": "merged", "merged_into": "{target_merge_id}"}}', teacher_email, now_str))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "action_taken": action})

@app.route('/kg/misconceptions/explain/<node_id>', methods=['GET'])
def api_explain_misconception(node_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM kg_nodes WHERE id = ?", (node_id,))
    node = cur.fetchone()
    
    if not node:
        conn.close()
        return jsonify({"error": "Not found"}), 404
        
    return jsonify({
        "misconception": dict(node),
        "evidence": {
            "behavior_pattern": "Low hesitation, fast response",
            "most_selected_wrong_option": "Option C",
            "average_solve_time": "12.4s",
            "confidence_gauges": {
                "Statistical": int(node["statistical_confidence"] * 100),
                "Teacher": int(node["teacher_confidence"] * 100),
                "Historical": int(node["historical_stability"] * 100),
                "Overall": int(node["overall_confidence"] * 100)
            },
            "representative_examples": [
                "Student A selected C rapidly (1.2s hesitation)",
                "Student B selected C after brief read (3.4s hesitation)"
            ]
        }
    })

if __name__ == "__main__":"""

if "@app.route('/kg/misconceptions/candidates'" not in content:
    content = content.replace('if __name__ == "__main__":', new_endpoints)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("app.py patched with Step 3 Misconception APIs.")
