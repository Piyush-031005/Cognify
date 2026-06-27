import os

file_path = r'f:\Cognify\app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoints = """
import pilot_analytics
from datetime import datetime

@app.route('/api/v1/pilot/dashboard/<room_id>', methods=['GET'])
def api_pilot_dashboard(room_id):
    dashboard = pilot_analytics.generate_evidence_dashboard_metrics(room_id)
    return jsonify(dashboard)

@app.route('/api/v1/pilot/feedback/<context_id>/execute', methods=['POST'])
def api_pilot_execute(context_id):
    data = request.json or {}
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        UPDATE teacher_recommendation_feedback 
        SET executed_at = ?, outcome_window_days = ?, intervention_attribution = ?
        WHERE context_id = ?
    ''', (datetime.now().isoformat(), data.get("outcome_window_days", 3), data.get("intervention_attribution", "Unknown"), context_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Execution logged for {context_id}"})

@app.route('/api/v1/pilot/evaluate_outcomes', methods=['POST'])
def api_pilot_evaluate_outcomes():
    # In a real system, this would be a background job scanning all pending items
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT context_id FROM teacher_recommendation_feedback WHERE success_category = 'Pending' AND executed_at IS NOT NULL")
    pending = [r["context_id"] for r in cur.fetchall()]
    conn.close()
    
    results = []
    for ctx_id in pending:
        res = pilot_analytics.calculate_recommendation_effectiveness(ctx_id)
        if res:
            res["context_id"] = ctx_id
            results.append(res)
            
    return jsonify({"evaluated": len(results), "results": results})

if __name__ == "__main__":"""

if "@app.route('/api/v1/pilot/dashboard/<room_id>'" not in content:
    content = content.replace('if __name__ == "__main__":', new_endpoints)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("app.py patched with Pilot Analytics APIs.")
else:
    print("APIs already exist in app.py")
