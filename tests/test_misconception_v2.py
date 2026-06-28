import sqlite3
import json
import uuid
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup global in-memory DB connection wrapper
_global_conn = sqlite3.connect(':memory:', check_same_thread=False)
_global_conn.row_factory = sqlite3.Row

class ConnectionWrapper:
    def __init__(self, c):
        self._conn = c
    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)
    def commit(self):
        self._conn.commit()
    def rollback(self):
        self._conn.rollback()
    def close(self):
        pass
    def __getattr__(self, name):
        return getattr(self._conn, name)

wrapped_conn = ConnectionWrapper(_global_conn)

import database
database.get_conn = lambda: wrapped_conn

import apd_engine
import md_engine
import app

apd_engine.get_conn = lambda: wrapped_conn
md_engine.get_conn = lambda: wrapped_conn
app.get_conn = lambda: wrapped_conn

from database import init_db, upgrade_database_schema

def setup_in_memory_db():
    conn = _global_conn
    init_db()
    upgrade_database_schema()
    
    cur = conn.cursor()
    # Clean tables
    cur.execute("DELETE FROM users")
    cur.execute("DELETE FROM kg_nodes")
    cur.execute("DELETE FROM kg_edges")
    cur.execute("DELETE FROM responses")
    cur.execute("DELETE FROM question_bank")
    cur.execute("DELETE FROM question_concepts")
    cur.execute("DELETE FROM misconception_clusters")
    cur.execute("DELETE FROM misconception_evidence")
    cur.execute("DELETE FROM misconception_evolution_log")
    
    # 1. Insert Concept node
    cur.execute("INSERT INTO kg_nodes (id, name, type, subject) VALUES ('c101', 'Arrays', 'concept', 'computer_science')")
    
    # 2. Insert Question mapped to c101
    cur.execute("""
        INSERT INTO question_bank (id, subject, topic, subtopic, prompt, option_a, option_b, option_c, option_d, correct_index)
        VALUES (5001, 'computer_science', 'arrays', 'indexing', 'What is array[0]?', 'First element', 'Second element', 'Size', 'None', 0)
    """)
    cur.execute("INSERT INTO question_concepts (question_id, concept_id, weight) VALUES (5001, 'c101', 1.0)")
    
    # 3. Seed users & mastery
    cohort_meta = json.dumps({"cohort_id": "cohort_A", "institution": "CS Academy", "grade": "10", "curriculum": "AP CS", "academic_year": "2026"})
    for i in range(10):
        email = f"student_{i}@academy.edu"
        cur.execute("INSERT INTO users (email, password, role, name, education) VALUES (?, 'hash', 'student', ?, ?)", (email, f"Student {i}", cohort_meta))
        cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'c101', 0.2)", (email,))
        
    # 4. Insert responses (wrong answers, Option B instead of Option A)
    # With low hesitation and average response time (15s) indicating true misconception
    for i in range(10):
        email = f"student_{i}@academy.edu"
        cur.execute("""
            INSERT INTO responses (
                student_email, question_id, correct, selected_option, correct_option, 
                hesitation_score, response_time, hover_count, backspace_count, idle_time
            ) VALUES (?, 5001, 0, 'Option B', 'Option A', 0.1, 15.0, 1, 0, 2.0)
        """, (email,))
        
    conn.commit()
    return conn

def test_misconception_suite():
    conn = setup_in_memory_db()
    client = app.app.test_client()
    cur = conn.cursor()
    
    print("[TEST 1] Triggering discovery...")
    response = client.post('/misconceptions/run')
    assert response.status_code == 200
    res_data = response.json
    assert res_data["status"] == "success"
    assert res_data["candidates_generated"] == 1
    
    # Get cluster_id
    cur.execute("SELECT * FROM misconception_clusters LIMIT 1")
    cluster = cur.fetchone()
    assert cluster is not None
    cluster_id = cluster["cluster_id"]
    
    print(f"[TEST 2] Verifying stable ID format and details: {cluster_id}")
    assert cluster_id.startswith("mcp_")
    assert cluster["concept_id"] == "c101"
    assert cluster["selected_option"] == "Option B"
    assert cluster["correct_option"] == "Option A"
    assert cluster["status"] == "candidate"
    
    print("[TEST 3] Verifying wrong option grouping...")
    # Clean and insert different option responses
    cur.execute("DELETE FROM responses")
    # Option C wrong answers
    for i in range(5):
        cur.execute("""
            INSERT INTO responses (
                student_email, question_id, correct, selected_option, correct_option, 
                hesitation_score, response_time, hover_count, backspace_count, idle_time
            ) VALUES (?, 5001, 0, 'Option C', 'Option A', 0.15, 12.0, 2, 1, 1.0)
        """, (f"student_{i}@academy.edu",))
    conn.commit()
    
    # Run discovery again
    response = client.post('/misconceptions/run')
    assert response.status_code == 200
    assert response.json["candidates_generated"] == 1 # Generated Option C candidate
    
    cur.execute("SELECT * FROM misconception_clusters WHERE selected_option = 'Option C'")
    opt_c_cluster = cur.fetchone()
    assert opt_c_cluster is not None
    opt_c_id = opt_c_cluster["cluster_id"]
    
    print("[TEST 4] Verifying behavioral consistency aggregation...")
    # Option C averages: hesitation=0.15, response_time=12.0, hover=2.0, backspace=1.0
    # behavioral_consistency = ((1.0 - 0.15) + (1.0 - 12/60) + (1.0 - 2/10) + (1.0 - 1/5)) / 4
    # = (0.85 + 0.8 + 0.8 + 0.8) / 4 = 3.25 / 4 = 0.8125
    assert abs(opt_c_cluster["confidence_behavior"] - 0.8125) < 0.01
    
    print("[TEST 5] Verifying explainable confidence components...")
    assert opt_c_cluster["confidence_size"] == 1.0 # 5 students / MIN_STUDENT_COUNT 5
    assert opt_c_cluster["confidence_mastery"] == 0.8 # 1 - avg_mastery (0.2) = 0.8
    assert opt_c_cluster["confidence_teacher"] == 0.5 # default
    assert opt_c_cluster["cluster_confidence"] > 0.5
    assert opt_c_cluster["confidence_level"] in ("Medium", "High")
    
    print("[TEST 6] Verifying severity calculation...")
    # student_count = 5. total_cohort_students = 10. avg_mastery = 0.2
    # severity_score = (5 / 10) * (1 - 0.2) = 0.5 * 0.8 = 0.4
    # 0.3 <= 0.4 < 0.5 -> severity should be High
    assert opt_c_cluster["severity"] == "High"
    
    print("[TEST 7] Verifying suggested interventions attachment...")
    assert opt_c_cluster["recommended_intervention_id"] == "int_mcp_c101"
    assert opt_c_cluster["intervention_source"] == "rule"
    assert opt_c_cluster["intervention_confidence"] == opt_c_cluster["cluster_confidence"]
    
    print("[TEST 8] Verifying teacher confirmation (confirm API)...")
    response = client.post('/misconceptions/confirm', json={
        "cluster_id": opt_c_id,
        "teacher_email": "head_teacher@school.edu"
    })
    assert response.status_code == 200
    confirm_data = response.json
    assert confirm_data["new_status"] == "validated"
    
    # Confirm status in misconception_clusters
    cur.execute("SELECT status, confidence_teacher FROM misconception_clusters WHERE cluster_id = ?", (opt_c_id,))
    mcp_row = cur.fetchone()
    assert mcp_row["status"] == "validated"
    assert mcp_row["confidence_teacher"] == 1.0 # 1 approval / 1 vote
    
    # Confirm promotion to Knowledge Graph nodes
    cur.execute("SELECT * FROM kg_nodes WHERE canonical_id = ?", (opt_c_id,))
    node = cur.fetchone()
    assert node is not None
    assert node["status"] == "validated"
    assert node["type"] == "misconception"
    
    # Confirm promotion to Knowledge Graph edges
    cur.execute("SELECT * FROM kg_edges WHERE target_id = ?", (node["id"],))
    edge = cur.fetchone()
    assert edge is not None
    assert edge["status"] == "validated"
    assert edge["relation_type"] == "causes_misconception"
    
    # Confirm addition to kg_evolution_log
    cur.execute("SELECT * FROM kg_evolution_log WHERE entity_id = ? ORDER BY id DESC LIMIT 1", (node["id"],))
    log_row = cur.fetchone()
    assert log_row is not None
    assert log_row["operation"] == "node_promoted"
    
    print("[TEST 9] Verifying teacher rejection (reject API)...")
    # Setup candidate for rejection
    cur.execute("UPDATE misconception_clusters SET status='candidate' WHERE cluster_id = ?", (cluster_id,))
    conn.commit()
    
    response = client.post('/misconceptions/reject', json={
        "cluster_id": cluster_id,
        "teacher_email": "assistant@school.edu"
    })
    assert response.status_code == 200
    assert response.json["new_status"] == "rejected"
    
    cur.execute("SELECT status FROM misconception_clusters WHERE cluster_id = ?", (cluster_id,))
    assert cur.fetchone()["status"] == "rejected"
    
    print("[TEST 10] Verifying chronological replay API...")
    response = client.get(f'/misconceptions/replay/{opt_c_id}')
    assert response.status_code == 200
    rep_data = response.json
    replay_history = rep_data["replay_history"]
    assert len(replay_history) >= 2
    assert replay_history[0]["old_status"] == "none"
    assert replay_history[-1]["teacher_action"] == "approve"
    
    print("[TEST 11] Verifying config updates...")
    response = client.get('/misconceptions/config')
    assert response.status_code == 200
    assert response.json["MIN_STUDENT_COUNT"] == 5
    
    # Update config
    response = client.post('/misconceptions/config', json={"MIN_STUDENT_COUNT": 15})
    assert response.status_code == 200
    assert response.json["config"]["MIN_STUDENT_COUNT"] == 15
    
    # Restore defaults
    client.post('/misconceptions/config', json={"MIN_STUDENT_COUNT": 5})
    
    print("[TEST 12] Verifying canonical cluster linking, memory hooks, and version propagation...")
    # Query cluster directly to inspect schema support
    cur.execute("SELECT parent_cluster_id, canonical_cluster_id, memory_event_id, memory_status, algorithm_version, graph_version, qqi_version, assessment_version, model_version FROM misconception_clusters WHERE cluster_id=?", (opt_c_id,))
    meta_row = cur.fetchone()
    # Canonical links
    assert "parent_cluster_id" in meta_row.keys()
    assert "canonical_cluster_id" in meta_row.keys()
    # Memory hooks
    assert "memory_event_id" in meta_row.keys()
    assert meta_row["memory_status"] == "pending"
    # Version propagation
    assert meta_row["algorithm_version"] == "v2.0"
    assert meta_row["graph_version"] == "v2.1"
    assert meta_row["qqi_version"] == "v1.2"
    assert meta_row["assessment_version"] == "v1.0"
    assert meta_row["model_version"] == "v2.0"
    
    print("[SUCCESS] All 12 misconception integration tests passed successfully!")

if __name__ == "__main__":
    test_misconception_suite()
