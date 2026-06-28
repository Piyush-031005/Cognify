import sqlite3
import json
import uuid
import os
import sys

# Add parent directory to path so it can import app and apd_engine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import init_db, get_conn, upgrade_database_schema
from apd_engine import run_apd_discovery
from datetime import datetime

def setup_test_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    class MockConn:
        def __init__(self, c):
            self.conn = c
        def cursor(self):
            return self.conn.cursor()
        def commit(self):
            self.conn.commit()
        def close(self):
            pass
        def __getattr__(self, name):
            return getattr(self.conn, name)
            
    mock_conn = MockConn(conn)
    
    import database
    database.DB_PATH = ':memory:'
    database.get_conn = lambda: mock_conn
    
    import apd_engine
    import app
    apd_engine.get_conn = lambda: mock_conn
    app.get_conn = lambda: mock_conn

    upgrade_database_schema()

    cur = conn.cursor()
    cur.execute("INSERT INTO kg_nodes (id, name, type, subject) VALUES ('c1', 'Fractions', 'concept', 'Math')")
    cur.execute("INSERT INTO kg_nodes (id, name, type, subject) VALUES ('c2', 'Decimals', 'concept', 'Math')")
    cur.execute("INSERT INTO kg_nodes (id, name, type, subject) VALUES ('c3', 'Algebra', 'concept', 'Math')")

    for i in range(15):
        email = f"student_g1_{i}@test.com"
        cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, ?, ?)", (email, 'c1', 0.8))
        cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, ?, ?)", (email, 'c2', 0.8))
        
    for i in range(5):
        email = f"student_g2_{i}@test.com"
        cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, ?, ?)", (email, 'c1', 0.8))
        cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, ?, ?)", (email, 'c2', 0.4))
        
    for i in range(35):
        email = f"student_g3_{i}@test.com"
        cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, ?, ?)", (email, 'c1', 0.3))
        cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, ?, ?)", (email, 'c2', 0.3))
        
    for i in range(5):
        email = f"student_g4_{i}@test.com"
        cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, ?, ?)", (email, 'c3', 0.9))

    conn.commit()
    return conn

def test_low_sample_rejection(test_db):
    print("Running test_low_sample_rejection...")
    run_apd_discovery('Math', min_sample=50)
    cur = test_db.cursor()
    cur.execute("SELECT * FROM kg_edges WHERE source_id='c3' OR target_id='c3'")
    assert len(cur.fetchall()) == 0, "Low sample concept generated an edge."

def test_discovery_and_duplicate_handling(test_db):
    print("Running test_discovery_and_duplicate_handling...")
    cur = test_db.cursor()
    cur.execute("DELETE FROM kg_edges")
    cur.execute("DELETE FROM kg_edge_evidence")
    test_db.commit()
    run_apd_discovery('Math', min_sample=50)
    cur = test_db.cursor()
    cur.execute("SELECT * FROM kg_edges WHERE source_id='c1' AND target_id='c2'")
    edges = cur.fetchall()
    assert len(edges) == 1, "Edge was not discovered or was duplicated."
    assert edges[0]["status"] == 'candidate'
    
    run_apd_discovery('Math', min_sample=50)
    cur.execute("SELECT * FROM kg_edges WHERE source_id='c1' AND target_id='c2'")
    edges_after = cur.fetchall()
    assert len(edges_after) == 1, "Duplicate edge created instead of update."
    assert edges_after[0]["validation_count"] == 1, "Validation count didn't increment on subsequent discovery."

def test_teacher_rejection_retains_evidence(test_db):
    print("Running test_teacher_rejection_retains_evidence...")
    from app import app
    client = app.test_client()
    response = client.post('/kg/prerequisites/validate', json={
        "source_id": "c1",
        "target_id": "c2",
        "action": "reject",
        "teacher_email": "test@teacher.com"
    })
    assert response.status_code == 200
    
    cur = test_db.cursor()
    cur.execute("SELECT status FROM kg_edges WHERE source_id='c1' AND target_id='c2'")
    assert cur.fetchone()["status"] == 'rejected', "Edge status not rejected."
    
    cur.execute("SELECT * FROM kg_edge_evidence WHERE source_id='c1' AND target_id='c2'")
    evidence = cur.fetchall()
    assert len(evidence) >= 1, "Evidence deleted."
    assert evidence[0]["teacher_rejections"] == 1, "Rejection count not incremented."

def test_graph_cycle_detection(test_db):
    print("Running test_graph_cycle_detection...")
    cur = test_db.cursor()
    cur.execute("INSERT INTO kg_edges (source_id, target_id, relation_type, status) VALUES ('c2', 'c1', 'prerequisite_of', 'production')")
    test_db.commit()
    
    cur.execute("DELETE FROM kg_edges WHERE source_id='c1' AND target_id='c2'")
    test_db.commit()
    
    run_apd_discovery('Math', min_sample=50)
    cur.execute("SELECT * FROM kg_edges WHERE source_id='c1' AND target_id='c2'")
    assert len(cur.fetchall()) == 0, "Cycle detection failed."

def test_rollback_graph_evolution(test_db):
    print("Running test_rollback_graph_evolution...")
    cur = test_db.cursor()
    cur.execute("SELECT * FROM kg_evolution_log ORDER BY timestamp DESC")
    logs = cur.fetchall()
    assert len(logs) > 0, "Evolution log is empty."
    
    rejection_logs = [log for log in logs if log["operation"] == "edge_rejected"]
    assert len(rejection_logs) > 0, "Teacher rejection not logged."
    
    log = rejection_logs[0]
    old_state = json.loads(log["old_state"])
    new_state = json.loads(log["new_state"])
    assert old_state["status"] == "candidate"
    assert new_state["status"] == "rejected"

if __name__ == "__main__":
    test_db = setup_test_db()
    test_low_sample_rejection(test_db)
    test_discovery_and_duplicate_handling(test_db)
    test_teacher_rejection_retains_evidence(test_db)
    test_graph_cycle_detection(test_db)
    test_rollback_graph_evolution(test_db)
    print("ALL TESTS PASSED SUCCESSFULLY.")
