import sqlite3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock DB globally before imports
conn = sqlite3.connect(':memory:', check_same_thread=False)
conn.row_factory = sqlite3.Row

class MockConn:
    def __init__(self, conn):
        self.conn = conn
    def cursor(self):
        return self.conn.cursor()
    def commit(self):
        # We assert in the test that this is never called, or we could just pass
        self.conn.commit()
    def close(self):
        pass

import database
database.DB_PATH = ':memory:'
database.get_conn = lambda: MockConn(conn)

import memory_engine
memory_engine.get_conn = lambda: MockConn(conn)
memory_engine.get_full_student_memory = lambda email: {
    "mastered": [{"node_id": "c1"}],
    "at_risk": [],
    "forgetting": [],
    "active_misconceptions": []
}

import orchestrator

def setup_test_db():
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY,
        question_id TEXT,
        student_email TEXT,
        correct INTEGER,
        timestamp TEXT
    )
    ''')
    cur.execute("INSERT INTO responses (question_id, student_email, correct, timestamp) VALUES ('q1', 'test@test.com', 1, '2023-10-01T10:00:00')")
    cur.execute("INSERT INTO responses (question_id, student_email, correct, timestamp) VALUES ('q2', 'test@test.com', 0, '2023-10-02T10:00:00')")
    conn.commit()
    return conn

def test_unified_state_read_only():
    # Replace commit with a function that raises an exception if called
    original_commit = MockConn.commit
    def fail_commit(self):
        raise Exception("Orchestrator should NEVER write to the DB!")
    MockConn.commit = fail_commit
    
    state = orchestrator.get_unified_cognitive_state('test@test.com')
    
    # Restore
    MockConn.commit = original_commit
    
    assert state['metadata']['schema_version'] == "1.0", "Missing versioning"
    assert state['telemetry']['recent_accuracy'] == 0.5, "Telemetry aggregation failed"
    assert state['memory']['mastered'][0]['node_id'] == "c1", "Memory aggregation failed"

if __name__ == "__main__":
    setup_test_db()
    print("\\nRunning Orchestrator Tests...")
    test_unified_state_read_only()
    print("\\nALL ORCHESTRATOR TESTS PASSED.")
