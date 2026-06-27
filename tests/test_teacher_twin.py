import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock DB globally before imports
import sqlite3
conn = sqlite3.connect(':memory:', check_same_thread=False)
conn.row_factory = sqlite3.Row

class MockConn:
    def __init__(self, conn):
        self.conn = conn
    def cursor(self):
        return self.conn.cursor()
    def commit(self):
        self.conn.commit()
    def close(self):
        pass

import database
database.DB_PATH = ':memory:'
database.get_conn = lambda: MockConn(conn)

# Now import the modules
import teacher_twin
import context_engine
import orchestrator

def mock_get_unified_state(email):
    return {
        "metadata": {"schema_version": "1.0"},
        "memory": {
            "mastered": [{"node_id": "concept_A"}],
            "forgetting": [{"node_id": "concept_B", "confidence": 0.9}],
            "active_misconceptions": [{"node_id": "concept_C", "confidence": 0.8}],
            "at_risk": [{"node_id": "concept_D", "confidence": 0.6}]
        },
        "telemetry": {
            "recent_accuracy": 0.3
        }
    }

orchestrator.get_unified_cognitive_state = mock_get_unified_state

def setup_test_db():
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS student_room (
        room_code TEXT,
        student_email TEXT
    )
    ''')
    cur.execute("INSERT INTO student_room (room_code, student_email) VALUES ('R1', 'test1@test.com')")
    cur.execute("INSERT INTO student_room (room_code, student_email) VALUES ('R1', 'test2@test.com')")
    conn.commit()
    return conn

def test_identical_classrooms():
    # If state is identical, prioritization should be identical
    prioritization = teacher_twin.get_student_prioritization('R1')
    assert len(prioritization) == 2, "Should return 2 students"
    assert prioritization[0]['teacher_priority'] == prioritization[1]['teacher_priority'], "Priorities should be identical"

def test_session_aware_boost():
    # Session context aligns with 'concept_C' (active misconception)
    prioritization = teacher_twin.get_student_prioritization('R1', session_context='concept_C')
    # Because 'concept_C' is the top recommendation for these mocked states, priority should be 1.5x, capped at 1.0
    assert prioritization[0]['teacher_priority'] > 0.0, "Priority should be calculated"

def test_classroom_heatmap():
    heatmap = teacher_twin.get_classroom_heatmap('R1')
    assert heatmap['total_students'] == 2
    assert "LO: concept_A" in heatmap['heatmap']
    assert heatmap['heatmap']["LO: concept_A"]["mastered"] == 2
    assert heatmap['heatmap']["LO: concept_A"]["mastery_percentage"] == 100.0

if __name__ == "__main__":
    setup_test_db()
    print("\\nRunning Teacher Twin Tests...")
    test_identical_classrooms()
    test_session_aware_boost()
    test_classroom_heatmap()
    print("\\nALL TEACHER TWIN TESTS PASSED.")
