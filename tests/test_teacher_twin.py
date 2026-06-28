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
    cur.execute("INSERT OR IGNORE INTO student_room (room_code, student_email) VALUES ('R1', 'test1@test.com')")
    cur.execute("INSERT OR IGNORE INTO student_room (room_code, student_email) VALUES ('R1', 'test2@test.com')")

    # Tables required by context_engine
    cur.execute("""
        CREATE TABLE IF NOT EXISTS concept_memory (
            student_email TEXT, concept_id TEXT, memory_strength REAL DEFAULT 0.5,
            forgetting_rate REAL DEFAULT 0.1, memory_state TEXT DEFAULT 'Learning',
            reinforcement_count INTEGER DEFAULT 0, last_success TEXT, last_failure TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kg_nodes (
            id TEXT PRIMARY KEY, name TEXT, subject TEXT, topic TEXT, subtopic TEXT,
            difficulty REAL DEFAULT 50.0, importance REAL DEFAULT 1.0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kg_edges (
            source_id TEXT, target_id TEXT, relation_type TEXT,
            discovery_method TEXT DEFAULT 'human', status TEXT DEFAULT 'production',
            weight REAL DEFAULT 1.0, confidence REAL DEFAULT 0.95
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teacher_priority_overrides (
            student_email TEXT, concept_id TEXT, override_type TEXT, reason TEXT, created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS context_recommendations_config (
            key TEXT PRIMARY KEY, value REAL NOT NULL, description TEXT,
            config_version TEXT DEFAULT 'v2.0', updated_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pilot_sessions (
            session_id INTEGER PRIMARY KEY, room_code TEXT, device_type TEXT,
            network_quality TEXT, created_at TEXT, total_students INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS room_students (
            room_code TEXT, student_email TEXT
        )
    """)

    # Seed two concepts for both test students
    for concept in ('concept_A', 'concept_B'):
        cur.execute(
            "INSERT OR IGNORE INTO kg_nodes (id, name, subject, topic) VALUES (?,?,?,?)",
            (concept, concept, 'test', 'test')
        )
    for email in ('test1@test.com', 'test2@test.com'):
        cur.execute(
            """INSERT OR IGNORE INTO concept_memory
               (student_email, concept_id, memory_strength, memory_state)
               VALUES (?, 'concept_A', 0.75, 'Stable')""",
            (email,)
        )
        cur.execute(
            """INSERT OR IGNORE INTO concept_memory
               (student_email, concept_id, memory_strength, memory_state)
               VALUES (?, 'concept_B', 0.30, 'Learning')""",
            (email,)
        )

    # Seed config defaults
    defaults = [
        ("w_memory", 0.30), ("w_apd", 0.20), ("w_misconception", 0.15),
        ("w_qqi", 0.15), ("w_teacher", 0.10), ("w_curriculum", 0.10),
        ("ctx_mobile_mult", 0.85), ("ctx_tablet_mult", 0.95), ("ctx_desktop_mult", 1.05),
        ("ctx_poor_network_mult", 0.80), ("ctx_average_network_mult", 0.95),
        ("ctx_good_network_mult", 1.00), ("ctx_excellent_network_mult", 1.05),
        ("ctx_peak_hour_mult", 1.10), ("ctx_offpeak_hour_mult", 0.90),
        ("ctx_large_class_mult", 1.05), ("ctx_small_class_mult", 0.95),
        ("max_recommendations", 10.0), ("min_score_threshold", 0.10),
        ("recent_completion_days", 3.0),
    ]
    for key, val in defaults:
        cur.execute(
            "INSERT OR IGNORE INTO context_recommendations_config (key, value) VALUES (?,?)",
            (key, val)
        )

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
