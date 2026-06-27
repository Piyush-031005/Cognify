import os

file_path = r'f:\Cognify\app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoints = """
import teacher_twin

@app.route('/api/v1/teacher/rooms/<room_id>/heatmap', methods=['GET'])
def api_teacher_heatmap(room_id):
    heatmap = teacher_twin.get_classroom_heatmap(room_id)
    return jsonify(heatmap)

@app.route('/api/v1/teacher/rooms/<room_id>/prioritization', methods=['POST'])
def api_teacher_prioritization(room_id):
    data = request.json or {}
    session_context = data.get("session_context")
    prioritization = teacher_twin.get_student_prioritization(room_id, session_context=session_context)
    return jsonify(prioritization)
    
@app.route('/api/v1/teacher/feedback', methods=['POST'])
def api_teacher_feedback():
    data = request.json
    if not data or "context_id" not in data or "action_taken" not in data:
        return jsonify({"error": "Missing required fields"}), 400
        
    result = teacher_twin.record_teacher_feedback(
        data["context_id"],
        data["action_taken"],
        data.get("outcome_notes", "")
    )
    return jsonify(result)

if __name__ == "__main__":"""

if "@app.route('/api/v1/teacher/rooms/<room_id>/heatmap'" not in content:
    content = content.replace('if __name__ == "__main__":', new_endpoints)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("app.py patched with Teacher Twin APIs.")
else:
    print("APIs already exist in app.py")
