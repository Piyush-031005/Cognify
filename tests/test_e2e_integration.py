import sqlite3
import json
import uuid
import os
import sys
from datetime import datetime, timedelta

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
import pilot_analytics
import context_engine

apd_engine.get_conn = lambda: wrapped_conn
md_engine.get_conn = lambda: wrapped_conn
app.get_conn = lambda: wrapped_conn
pilot_analytics.get_conn = lambda: wrapped_conn
context_engine.get_conn = lambda: wrapped_conn

from database import init_db, upgrade_database_schema

def setup_e2e_database():
    conn = _global_conn
    init_db()
    upgrade_database_schema()
    
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS teacher_recommendation_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        context_id TEXT,
        action_taken TEXT,
        outcome_notes TEXT,
        timestamp TEXT,
        executed_at TEXT,
        outcome_window_days INTEGER,
        success_category TEXT DEFAULT 'Pending',
        evidence_quality TEXT,
        intervention_attribution TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS intervention_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intervention_id TEXT,
        recommendation_id TEXT,
        student_email TEXT,
        teacher_email TEXT,
        question_id TEXT,
        concept_id TEXT,
        kg_version TEXT,
        qqi_version TEXT,
        model_version TEXT,
        pre_mastery REAL,
        post_mastery REAL,
        mastery_gain REAL,
        teacher_action TEXT,
        timestamp TEXT
    )
    ''')
    cur.execute("DELETE FROM users")
    cur.execute("DELETE FROM kg_nodes")
    cur.execute("DELETE FROM kg_edges")
    cur.execute("DELETE FROM responses")
    cur.execute("DELETE FROM question_bank")
    cur.execute("DELETE FROM question_concepts")
    cur.execute("DELETE FROM misconception_clusters")
    cur.execute("DELETE FROM misconception_evidence")
    cur.execute("DELETE FROM misconception_evolution_log")
    cur.execute("DELETE FROM teacher_recommendation_feedback")
    cur.execute("DELETE FROM intervention_history")
    
    # 1. Insert Concept nodes (Algebra A -> Equations B)
    cur.execute("INSERT INTO kg_nodes (id, name, type, subject, status) VALUES ('alg_101', 'Algebra Basis', 'concept', 'math', 'validated')")
    cur.execute("INSERT INTO kg_nodes (id, name, type, subject, status) VALUES ('eq_202', 'Equations Solving', 'concept', 'math', 'validated')")
    
    # 2. Insert Questions mapped to concepts
    cur.execute("""
        INSERT INTO question_bank (id, subject, topic, subtopic, prompt, option_a, option_b, option_c, option_d, correct_index)
        VALUES (6001, 'math', 'algebra', 'basis', 'Solve 2x = 4', '2', '4', '1', '0', 0)
    """)
    cur.execute("INSERT INTO question_concepts (question_id, concept_id, weight) VALUES (6001, 'alg_101', 1.0)")
    
    cur.execute("""
        INSERT INTO question_bank (id, subject, topic, subtopic, prompt, option_a, option_b, option_c, option_d, correct_index)
        VALUES (6002, 'math', 'algebra', 'equations', 'Solve x + 2 = 6', '4', '2', '6', '1', 0)
    """)
    cur.execute("INSERT INTO question_concepts (question_id, concept_id, weight) VALUES (6002, 'eq_202', 1.0)")
    
    # 3. Seed student cohort
    cohort_meta = json.dumps({
        "cohort_id": "math_cohort_beta",
        "institution": "Stanford Ed",
        "grade": "9",
        "curriculum": "AP Math",
        "academic_year": "2026"
    })
    
    # We create 40 students to pass the sample size check for Pilot Analytics validation (sample_size >= 30)
    for i in range(40):
        email = f"learner_{i}@stanford.edu"
        cur.execute("INSERT INTO users (email, password, role, name, education) VALUES (?, 'pwd', 'student', ?, ?)", (email, f"Learner {i}", cohort_meta))
        
        if i < 20:
            # 20 Mastering Students
            cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'alg_101', 0.9)", (email,))
            cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'eq_202', 0.85)", (email,))
            
            # Correct responses
            cur.execute("""
                INSERT INTO responses (
                    student_email, question_id, correct, selected_option, correct_option, 
                    hesitation_score, response_time, hover_count, backspace_count, idle_time
                ) VALUES (?, 6001, 1, 'Option A', 'Option A', 0.05, 5.0, 0, 0, 0.2)
            """, (email,))
            cur.execute("""
                INSERT INTO responses (
                    student_email, question_id, correct, selected_option, correct_option, 
                    hesitation_score, response_time, hover_count, backspace_count, idle_time
                ) VALUES (?, 6002, 1, 'Option A', 'Option A', 0.05, 5.0, 0, 0, 0.2)
            """, (email,))
        else:
            # 20 Struggling Students
            cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'alg_101', 0.2)", (email,))
            cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'eq_202', 0.3)", (email,))
            
            # Incorrect responses (exposing misconception Option B)
            cur.execute("""
                INSERT INTO responses (
                    student_email, question_id, correct, selected_option, correct_option, 
                    hesitation_score, response_time, hover_count, backspace_count, idle_time
                ) VALUES (?, 6001, 0, 'Option B', 'Option A', 0.1, 15.0, 1, 0, 1.0)
            """, (email,))
            cur.execute("""
                INSERT INTO responses (
                    student_email, question_id, correct, selected_option, correct_option, 
                    hesitation_score, response_time, hover_count, backspace_count, idle_time
                ) VALUES (?, 6002, 0, 'Option B', 'Option A', 0.05, 12.0, 0, 0, 0.5)
            """, (email,))
            
    conn.commit()
    return conn

def run_e2e_integration_test():
    setup_e2e_database()
    client = app.app.test_client()
    cur = _global_conn.cursor()
    
    print("[E2E] Step 1: Running QQI & Ingestion Verification...")
    cur.execute("SELECT COUNT(*) as count FROM responses")
    assert cur.fetchone()["count"] == 80
    
    print("[E2E] Step 2: Triggering APD Discovery v2...")
    # Trigger discovery via route
    response = client.post('/apd/run', json={"subject": "math", "min_sample": 10})
    assert response.status_code == 200
    assert response.json["status"] == "success"
    
    # Verify candidate edge generated
    cur.execute("SELECT * FROM kg_edges WHERE relation_type='prerequisite_of' AND status='candidate'")
    edge = cur.fetchone()
    assert edge is not None
    edge_id = edge["edge_id"]
    
    print(f"[E2E] Step 3: Teacher approving APD candidate edge: {edge_id}...")
    response = client.post('/apd/approve', json={"edge_id": edge_id, "teacher_email": "dean@stanford.edu"})
    assert response.status_code == 200
    assert response.json["status"] == "validated"
    
    print("[E2E] Step 4: Triggering Misconception Discovery v2...")
    response = client.post('/misconceptions/run')
    assert response.status_code == 200
    assert response.json["status"] == "success"
    
    # Verify candidate cluster generated
    cur.execute("SELECT * FROM misconception_clusters WHERE status='candidate'")
    cluster = cur.fetchone()
    assert cluster is not None
    cluster_id = cluster["cluster_id"]
    
    print(f"[E2E] Step 5: Teacher confirming misconception cluster: {cluster_id}...")
    response = client.post('/misconceptions/confirm', json={"cluster_id": cluster_id, "teacher_email": "dean@stanford.edu"})
    assert response.status_code == 200
    assert response.json["status"] == "success"
    
    # Verify cluster is validated and promoted to KG nodes/edges
    cur.execute("SELECT status FROM misconception_clusters WHERE cluster_id=?", (cluster_id,))
    assert cur.fetchone()["status"] == "validated"
    
    cur.execute("SELECT type, status FROM kg_nodes WHERE canonical_id=?", (cluster_id,))
    node = cur.fetchone()
    assert node["type"] == "misconception"
    assert node["status"] == "validated"
    
    print("[E2E] Step 6: Querying Digital Twin & Unified Cognitive State...")
    response = client.get('/api/v1/student/learner_0@stanford.edu/unified_state')
    assert response.status_code == 200
    state_data = response.json
    assert "memory" in state_data
    assert state_data["metadata"]["student_email"] == "learner_0@stanford.edu"
    
    print("[E2E] Step 7: Generating Contextual Recommendations...")
    response = client.get('/api/v1/student/learner_0@stanford.edu/context')
    assert response.status_code == 200
    recs = response.json
    # Expect recommended items
    assert len(recs) > 0
    
    print("[E2E] Step 8: Log execute recommendation & Outcome validation in Pilot Analytics...")
    # Inject recommendation feedback record with context_id
    context_id = "recomm_math_001"
    past_date = (datetime.now() - timedelta(days=5)).isoformat()
    
    cur.execute("""
        INSERT INTO teacher_recommendation_feedback 
        (context_id, action_taken, timestamp, executed_at, outcome_window_days) 
        VALUES (?, 'Accepted', ?, ?, 3)
    """, (context_id, past_date, past_date))
    
    # Seed intervention history for students to satisfy pilot analytics effectiveness calculation
    # Simulate positive mastery gains (0.25 -> 0.8)
    for i in range(35):
        cur.execute("""
            INSERT INTO intervention_history (
                intervention_id, recommendation_id, student_email, teacher_email, 
                question_id, concept_id, kg_version, qqi_version, model_version, 
                pre_mastery, post_mastery, mastery_gain, teacher_action, timestamp
            ) VALUES (?, ?, ?, 'dean@stanford.edu', '6001', 'alg_101', 'v2.1', 'v1.2', 'v2.0', 0.25, 0.85, 0.60, 'Accepted', ?)
        """, (f"int_e2e_{i}", context_id, f"learner_{i}@stanford.edu", past_date))
        
    _global_conn.commit()
    
    # 1. Trigger execution via pilot execution endpoint
    response = client.post(f'/api/v1/pilot/feedback/{context_id}/execute', json={
        "outcome_window_days": 3,
        "intervention_attribution": "Alg Remediation"
    })
    assert response.status_code == 200
    
    # Manually backdate the executed_at timestamp so that the outcome window check passes (days > 3)
    cur.execute("UPDATE teacher_recommendation_feedback SET executed_at = ? WHERE context_id = ?", 
                (past_date, context_id))
    _global_conn.commit()
    
    # 2. Trigger evaluate outcomes endpoint (closed-loop verification)
    response = client.post('/api/v1/pilot/evaluate_outcomes')
    assert response.status_code == 200
    res_outcomes = response.json
    assert res_outcomes["evaluated"] > 0
    
    # Verify outcome results
    outcome_run = res_outcomes["results"][0]
    assert outcome_run["success_category"] == "Strong Improvement"
    assert outcome_run["evidence_quality"] == "Medium"
    
    print("[SUCCESS] End-to-End unified learning lifecycle verified successfully!")

if __name__ == "__main__":
    run_e2e_integration_test()
