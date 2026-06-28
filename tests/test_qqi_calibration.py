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
        self.conn.commit()
    def close(self):
        pass

import database
database.DB_PATH = ':memory:'
database.get_conn = lambda: MockConn(conn)

import memory_engine
memory_engine.get_conn = lambda: MockConn(conn)

import qqi_engine
qqi_engine.get_conn = lambda: MockConn(conn)

def setup_test_db():
    cur = conn.cursor()
    # Question Bank
    cur.execute('''
    CREATE TABLE IF NOT EXISTS question_bank (
        id TEXT PRIMARY KEY,
        qqi_score REAL,
        calibrated_qqi_score REAL,
        difficulty TEXT,
        calibrated_difficulty TEXT,
        current_version INTEGER DEFAULT 1
    )
    ''')
    # Question Versions
    cur.execute('''
    CREATE TABLE IF NOT EXISTS question_versions (
        id INTEGER PRIMARY KEY,
        question_id TEXT,
        version INTEGER,
        qqi_before REAL,
        qqi_after REAL,
        calibration_reason TEXT,
        edited_at TEXT,
        edited_by TEXT
    )
    ''')
    # Question Concepts
    cur.execute('''
    CREATE TABLE IF NOT EXISTS question_concepts (
        question_id TEXT,
        concept_id TEXT
    )
    ''')
    # Responses
    cur.execute('''
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY,
        question_id TEXT,
        student_email TEXT,
        correct INTEGER
    )
    ''')
    # Student Memory Events (v1.0 legacy table)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS student_memory_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        node_id TEXT,
        memory_type TEXT,
        retrieval_strength REAL,
        storage_strength REAL,
        confidence REAL,
        update_reason TEXT,
        evidence_count INTEGER,
        effectiveness_delta REAL,
        memory_model_version TEXT DEFAULT 'v1.0',
        timestamp TEXT
    )
    ''')
    # Week 8: v2.0 tables required by memory_engine
    cur.execute('''
    CREATE TABLE IF NOT EXISTS memory_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS memory_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT, concept_id TEXT, event_type TEXT, payload TEXT,
        event_version TEXT DEFAULT 'v2.0', source_module TEXT,
        algorithm_version TEXT DEFAULT 'v2.0', qqi_version TEXT DEFAULT 'v1.2',
        twin_version TEXT DEFAULT 'v2.0', config_version TEXT DEFAULT 'v1.0', timestamp TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS concept_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT, concept_id TEXT,
        memory_strength REAL, forgetting_rate REAL, memory_state TEXT,
        memory_confidence REAL, memory_explanation TEXT, derived_from TEXT,
        trigger_event_id INTEGER, config_version TEXT DEFAULT 'v1.0',
        reinforcement_count INTEGER, retrieval_success_rate REAL,
        last_success TEXT, last_failure TEXT, next_review_date TEXT, last_updated TEXT,
        UNIQUE(student_email, concept_id)
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS memory_state_transitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT, concept_id TEXT,
        old_state TEXT, new_state TEXT, trigger_event_id INTEGER, reason TEXT, timestamp TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS review_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT, concept_id TEXT,
        scheduled_date TEXT, status TEXT, priority REAL, created_at TEXT,
        UNIQUE(student_email, concept_id)
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS memory_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT, concept_id TEXT,
        alert_type TEXT, severity TEXT, description TEXT, status TEXT DEFAULT 'active', timestamp TEXT
    )
    ''')
    from datetime import datetime as _dt
    now_s = _dt.now().isoformat()
    defaults = [
        ("DEFAULT_DECAY_RATE", 0.05), ("DEFAULT_INITIAL_STRENGTH", 0.3),
        ("REINFORCE_BOOST", 0.15), ("FAILURE_PENALTY", 0.2),
        ("FORGETTING_THRESHOLD", 0.4), ("ALERT_THRESHOLD_STRENGTH", 0.3),
        ("REVIEW_INTERVAL_FACTOR", 7.0), ("WEIGHT_MEMORY_RISK", 0.3),
        ("WEIGHT_MISCONCEPTION_SEVERITY", 0.2), ("WEIGHT_PREREQUISITE_IMPORTANCE", 0.2),
        ("WEIGHT_TEACHER_PRIORITY", 0.15), ("WEIGHT_EXAM_WEIGHT", 0.15)
    ]
    for k, v in defaults:
        cur.execute("INSERT OR IGNORE INTO memory_config (key, value, config_version, updated_by, updated_at) VALUES (?,?,?,?,?)",
                    (k, v, 'v1.0', 'system', now_s))
    # Seed data
    cur.execute("INSERT INTO question_bank (id, qqi_score, difficulty) VALUES ('q1', 80.0, 'medium')")
    cur.execute("INSERT INTO question_concepts (question_id, concept_id) VALUES ('q1', 'c1')")
    conn.commit()
    return conn


def test_high_memory_failure_calibration():
    # Insert high memory student events
    for _ in range(30): # give them high storage strength (>0.8)
        memory_engine.record_memory_event('smart_student@test.com', 'c1', 'concept', 'correct_answer')
        
    state = memory_engine.derive_current_state('smart_student@test.com', 'c1')
    print(f"Student Storage Strength: {state['storage_strength']}")
        
    # But they failed this question
    cur = conn.cursor()
    cur.execute("INSERT INTO responses (question_id, student_email, correct) VALUES ('q1', 'smart_student@test.com', 0)")
    conn.commit()
    
    result = qqi_engine.calibrate_question('q1')
    print(f"Calibration Result: {result}")
    
    assert result['calibrated_qqi'] < result['base_qqi'], "QQI did not decrease for High Memory Failure!"
    assert 'High Memory Failure' in result['reason'], "Wrong calibration reason!"

if __name__ == "__main__":
    setup_test_db()
    print("\\nRunning QQI Calibration Test: High Memory Failure...")
    test_high_memory_failure_calibration()
    
    drift = qqi_engine.detect_calibration_drift()
    print(f"\\nCalibration Drift: {drift}")
    
    print("\\nALL QQI CALIBRATION TESTS PASSED.")
