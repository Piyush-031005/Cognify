import sqlite3
import json
import uuid
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock DB globally before imports
conn = sqlite3.connect(':memory:', check_same_thread=False)
conn.row_factory = sqlite3.Row

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

wrapped_conn = ConnectionWrapper(conn)

import database
database.DB_PATH = ':memory:'
database.get_conn = lambda: wrapped_conn

import md_engine
import app
md_engine.get_conn = lambda: wrapped_conn
app.get_conn = lambda: wrapped_conn

def setup_test_db():
    database.upgrade_database_schema()
    cur = conn.cursor()
    
    # Insert question
    cur.execute('''INSERT INTO question_bank (id, subject, topic, subtopic, prompt, option_a, option_b, option_c, option_d, correct_index) 
                   VALUES (101, 'Math', 'Algebra', 'Equations', 'Solve X', 'A', 'B', 'C', 'D', 0)''')
    # Insert concept mapping
    cur.execute("INSERT INTO kg_nodes (id, name, type) VALUES ('c1', 'Equations', 'concept')")
    cur.execute("INSERT INTO question_concepts (question_id, concept_id, weight) VALUES (101, 'c1', 1.0)")
    
    conn.commit()
    return conn

def reset_telemetry():
    cur = conn.cursor()
    cur.execute("DELETE FROM responses")
    cur.execute("DELETE FROM raw_telemetry_events")
    conn.commit()

def test_no_behavior_no_discovery():
    reset_telemetry()
    cur = conn.cursor()
    # 5 wrong answers, but HIGH hesitation and HIGH response time (guessing)
    for i in range(5):
        cur.execute('''INSERT INTO responses (question_id, correct, hesitation_score, response_time) 
                       VALUES (101, 0, 0.9, 120.0)''')
    conn.commit()
    
    res = md_engine.discover_misconceptions()
    assert res["candidates_generated"] == 0, "Generated misconception for guessing behavior!"

def test_behavior_triggers_discovery():
    reset_telemetry()
    cur = conn.cursor()
    # 5 wrong answers, LOW hesitation and LOW response time (genuine misconception)
    for i in range(5):
        cur.execute('''INSERT INTO responses (question_id, correct, hesitation_score, response_time) 
                       VALUES (101, 0, 0.1, 15.0)''')
    conn.commit()
    
    res = md_engine.discover_misconceptions()
    assert res["candidates_generated"] == 1, "Failed to generate candidate for genuine misconception behavior!"
    
    cur.execute("SELECT * FROM kg_nodes WHERE type='misconception' AND status='candidate'")
    node = cur.fetchone()
    assert node is not None
    assert node["status"] == 'candidate'
    return node["id"]

def test_duplicate_updates_confidence_not_node(node_id):
    # Run again with same telemetry
    res = md_engine.discover_misconceptions()
    assert res["candidates_generated"] == 0, "Duplicated an existing misconception!"
    
    cur = conn.cursor()
    cur.execute("SELECT statistical_confidence FROM kg_nodes WHERE id=?", (node_id,))
    conf = cur.fetchone()["statistical_confidence"]
    assert conf > 0.6, "Confidence was not updated on rediscovery!"

def test_rejected_never_rediscovered(node_id):
    # Reject it via API
    client = app.app.test_client()
    response = client.post('/kg/misconceptions/validate', json={
        "node_id": node_id,
        "action": "reject"
    })
    
    # Run discovery again
    res = md_engine.discover_misconceptions()
    assert res["candidates_generated"] == 0, "Rediscovered a rejected misconception!"

def test_teacher_merge_history():
    # Insert a new candidate directly
    cur = conn.cursor()
    cur.execute("INSERT INTO kg_nodes (id, type, status) VALUES ('m_merge1', 'misconception', 'candidate')")
    conn.commit()
    
    client = app.app.test_client()
    response = client.post('/kg/misconceptions/validate', json={
        "node_id": 'm_merge1',
        "action": "merge",
        "merge_into_id": "m_target"
    })
    
    cur.execute("SELECT status FROM kg_nodes WHERE id='m_merge1'")
    assert cur.fetchone()["status"] == 'merged'
    
    cur.execute("SELECT new_state FROM kg_evolution_log WHERE entity_id='m_merge1' AND operation='teacher_merged'")
    log = cur.fetchone()
    assert log is not None
    assert 'merged_into' in log["new_state"]

if __name__ == "__main__":
    test_db = setup_test_db()
    
    print("Testing Test 1 & 5: Behavior requirement...")
    test_no_behavior_no_discovery()
    
    print("Testing Discovery...")
    node_id = test_behavior_triggers_discovery()
    
    print("Testing Test 2: Rediscovery confidence update...")
    test_duplicate_updates_confidence_not_node(node_id)
    
    print("Testing Test 4: Rejected never rediscovered...")
    test_rejected_never_rediscovered(node_id)
    
    print("Testing Test 3: Teacher merge...")
    test_teacher_merge_history()
    
    print("ALL MISCONCEPTION TESTS PASSED.")
