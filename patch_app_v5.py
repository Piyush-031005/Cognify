import os

file_path = r'f:\Cognify\app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoints = """
import orchestrator
import context_engine

@app.route('/api/v1/student/<email>/unified_state', methods=['GET'])
def api_unified_state(email):
    state = orchestrator.get_unified_cognitive_state(email)
    return jsonify(state)

@app.route('/api/v1/student/<email>/context', methods=['GET'])
def api_context_recommendations(email):
    recommendations = context_engine.generate_contextual_recommendations(email)
    return jsonify(recommendations)

if __name__ == "__main__":"""

if "@app.route('/api/v1/student/<email>/context'" not in content:
    content = content.replace('if __name__ == "__main__":', new_endpoints)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("app.py patched with Context Engine and Orchestrator APIs.")
else:
    print("APIs already exist in app.py")
