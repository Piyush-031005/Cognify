import os

file_path = r'f:\Cognify\app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoints = """
from memory_engine import get_full_student_memory, derive_current_state

@app.route('/kg/misconceptions/similar/<node_id>', methods=['GET'])
def api_similar_misconceptions(node_id):
    # Placeholder for Graph Embedding similarity search
    # This helps teachers merge duplicates during validation
    return jsonify({
        "similar_misconceptions": [
            {
                "id": "mcp_dummy_1",
                "canonical_id": "MCP-MATH-00102",
                "similarity_score": 0.92,
                "name": "Sign Error in Algebra",
                "description": "Student flips negative to positive."
            }
        ]
    })

@app.route('/memory/student/<email>', methods=['GET'])
def api_student_memory(email):
    memory = get_full_student_memory(email)
    return jsonify(memory)

@app.route('/memory/student/<email>/timeline/<node_id>', methods=['GET'])
def api_student_memory_timeline(email, node_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(\"\"\"
        SELECT * FROM student_memory_events 
        WHERE student_email = ? AND node_id = ?
        ORDER BY timestamp ASC
    \"\"\", (email, node_id))
    events = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    current_state = derive_current_state(email, node_id)
    
    return jsonify({
        "student_email": email,
        "node_id": node_id,
        "current_state": current_state,
        "event_timeline": events
    })

if __name__ == "__main__":"""

if "@app.route('/memory/student/<email>'" not in content:
    content = content.replace('if __name__ == "__main__":', new_endpoints)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("app.py patched with Phase 3 Memory APIs.")
