import sqlite3
import json
import uuid
import os
import sys
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock DB globally before imports
conn = sqlite3.connect(':memory:', check_same_thread=False)
conn.row_factory = sqlite3.Row

import database
database.DB_PATH = ':memory:'
database.get_conn = lambda: conn

import apd_engine
import app
apd_engine.get_conn = lambda: conn
app.get_conn = lambda: conn

def setup_test_db():
    database.upgrade_database_schema()
    cur = conn.cursor()
    cur.execute("INSERT INTO kg_nodes (id, name, type, subject) VALUES ('c1', 'Fractions', 'concept', 'Math')")
    cur.execute("INSERT INTO kg_nodes (id, name, type, subject) VALUES ('c2', 'Decimals', 'concept', 'Math')")

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

    conn.commit()
    return conn

def test_adaptive_confidence_and_decay(test_db):
    print("Running test_adaptive_confidence_and_decay...")
    apd_engine.run_apd_discovery('Math', min_sample=50)
    
    cur = test_db.cursor()
    cur.execute("SELECT * FROM kg_edges WHERE source_id='c1' AND target_id='c2'")
    edge = cur.fetchone()
    
    w = apd_engine.config["weights"]
    expected_overall = (w["statistical"] * edge["statistical_confidence"]) + (w["teacher"] * edge["teacher_confidence"]) + (w["historical"] * edge["historical_stability"])
    assert abs(edge["overall_confidence"] - expected_overall) < 0.001, "Overall confidence not computing correctly from weights."
    
    initial_stability = edge["historical_stability"]
    
    # Run manual decay
    apd_engine.apply_confidence_decay('Math')
    
    cur.execute("SELECT * FROM kg_edges WHERE source_id='c1' AND target_id='c2'")
    edge_decayed = cur.fetchone()
    
    decay_rate = apd_engine.config["decay_rates"]["Math"]
    assert abs(edge_decayed["historical_stability"] - (initial_stability - decay_rate)) < 0.001, "Domain specific decay not applied correctly."

def test_promotion_policy_blocks_conflict(test_db):
    print("Running test_promotion_policy_blocks_conflict...")
    # Force a conflict
    cur = test_db.cursor()
    cur.execute("UPDATE kg_edge_evidence SET conflict_detected = 1 WHERE source_id='c1' AND target_id='c2'")
    test_db.commit()
    
    client = app.app.test_client()
    
    response = client.post('/kg/prerequisites/validate', json={
        "source_id": "c1",
        "target_id": "c2",
        "action": "accept",
        "teacher_email": "senior@school.com"
    })
    
    assert response.status_code == 200
    
    cur.execute("SELECT status FROM kg_edges WHERE source_id='c1' AND target_id='c2'")
    status = cur.fetchone()["status"]
    
    assert status == 'validated', "Edge promoted to production despite conflict!"

if __name__ == "__main__":
    test_db = setup_test_db()
    test_adaptive_confidence_and_decay(test_db)
    test_promotion_policy_blocks_conflict(test_db)
    print("ALL STEP 2 TESTS PASSED SUCCESSFULLY.")
