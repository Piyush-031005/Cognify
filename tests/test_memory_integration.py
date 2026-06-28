import sqlite3
import json
import os
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock DB globally before imports
real_conn = sqlite3.connect(':memory:', check_same_thread=False)
real_conn.row_factory = sqlite3.Row

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
database.get_conn = lambda: MockConn(real_conn)

import memory_engine
memory_engine.get_conn = lambda: MockConn(real_conn)

def setup_test_db():
    cur = real_conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS kg_nodes (
        id TEXT PRIMARY KEY,
        name TEXT,
        type TEXT
    )
    ''')
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
        student_email TEXT,
        concept_id TEXT,
        event_type TEXT,
        payload TEXT,
        event_version TEXT DEFAULT 'v2.0',
        source_module TEXT,
        algorithm_version TEXT DEFAULT 'v2.0',
        qqi_version TEXT DEFAULT 'v1.2',
        twin_version TEXT DEFAULT 'v2.0',
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS concept_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        memory_strength REAL,
        forgetting_rate REAL,
        memory_state TEXT,
        memory_confidence REAL,
        memory_explanation TEXT,
        derived_from TEXT,
        trigger_event_id INTEGER,
        config_version TEXT DEFAULT 'v1.0',
        reinforcement_count INTEGER,
        retrieval_success_rate REAL,
        last_success TEXT,
        last_failure TEXT,
        next_review_date TEXT,
        last_updated TEXT,
        UNIQUE(student_email, concept_id)
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS memory_state_transitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        old_state TEXT,
        new_state TEXT,
        trigger_event_id INTEGER,
        reason TEXT,
        timestamp TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS review_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        scheduled_date TEXT,
        status TEXT,
        priority REAL,
        created_at TEXT,
        UNIQUE(student_email, concept_id)
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS memory_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        alert_type TEXT,
        severity TEXT,
        description TEXT,
        status TEXT DEFAULT 'active',
        timestamp TEXT
    )
    ''')
    # Seed memory_config defaults
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
    cur.execute("INSERT INTO kg_nodes (id, name, type) VALUES ('c1', 'Equations', 'concept')")
    cur.execute("INSERT INTO kg_nodes (id, name, type) VALUES ('m1', 'Sign Error', 'misconception')")
    real_conn.commit()
    return real_conn


def inject_event(email, node_id, memory_type, update_reason, days_ago):
    past_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
    memory_engine.record_memory_event(email, node_id, memory_type, update_reason, timestamp_override=past_date)

def test_repeated_practice_slow_forgetting():
    # Student A: practices once 30 days ago
    inject_event('studentA@test.com', 'c1', 'concept', 'correct_answer', 30)
    
    # Student B: practices 5 times 30 days ago
    for _ in range(5):
        inject_event('studentB@test.com', 'c1', 'concept', 'correct_answer', 30)
        
    stateA = memory_engine.derive_current_state('studentA@test.com', 'c1')
    stateB = memory_engine.derive_current_state('studentB@test.com', 'c1')
    
    print(f"Student A (1 practice) Retrieval Strength after 30 days: {stateA['retrieval_strength']:.3f}")
    print(f"Student B (5 practice) Retrieval Strength after 30 days: {stateB['retrieval_strength']:.3f}")
    
    assert stateB['retrieval_strength'] > stateA['retrieval_strength'], "Repeated practice did not slow down forgetting!"
    assert stateB['storage_strength'] > stateA['storage_strength'], "Storage strength did not build up!"

def test_long_inactivity_decay():
    # Practice 10 days ago
    inject_event('studentC@test.com', 'c1', 'concept', 'correct_answer', 10)
    
    # State immediately after (10 days ago)
    past_date = (datetime.now() - timedelta(days=10)).isoformat()
    immediate_state = memory_engine.derive_current_state('studentC@test.com', 'c1', up_to_time=past_date)
    
    # State today
    current_state = memory_engine.derive_current_state('studentC@test.com', 'c1')
    
    print(f"Immediate Retrieval Strength: {immediate_state['retrieval_strength']}")
    print(f"Decayed Retrieval Strength (10 days): {current_state['retrieval_strength']}")
    
    assert immediate_state['retrieval_strength'] == 1.0, "Immediate retrieval should be 1.0"
    assert current_state['retrieval_strength'] < 1.0, "Retrieval strength did not decay over time!"

def test_misconception_correction():
    # v2.0: In the event sourcing model, storage strength grows via correct_answer events.
    # First establish baseline strength through correct answers.
    for _ in range(5):
        inject_event('studentD@test.com', 'm1', 'misconception', 'correct_answer', 5)
    state1 = memory_engine.derive_current_state('studentD@test.com', 'm1')
    # After 5 correct_answer events, S should be above initial default (0.3)
    assert state1['storage_strength'] > 0.3, f"Storage strength {state1['storage_strength']} should exceed initial default after reinforcement"

    # Record a misconception event (wrong_answer penalizes strength)
    inject_event('studentD@test.com', 'm1', 'misconception', 'wrong_answer', 0)
    state2 = memory_engine.derive_current_state('studentD@test.com', 'm1')

    # Core v2.0 invariant: wrong_answer must reduce storage strength
    assert state2['storage_strength'] < state1['storage_strength'], \
        f"Misconception wrong_answer should reduce storage strength ({state2['storage_strength']} < {state1['storage_strength']})"
    # Strength must remain non-negative
    assert state2['storage_strength'] >= 0.0, "Storage strength must remain non-negative"


def test_event_replay_determinism():
    # Student E has a complex history
    inject_event('studentE@test.com', 'c1', 'concept', 'correct_answer', 20)
    inject_event('studentE@test.com', 'c1', 'concept', 'wrong_answer', 15)
    inject_event('studentE@test.com', 'c1', 'concept', 'correct_answer', 2)
    
    state_first = memory_engine.derive_current_state('studentE@test.com', 'c1')
    
    # Derive again to ensure it's completely deterministic based on DB rows
    state_second = memory_engine.derive_current_state('studentE@test.com', 'c1')
    
    assert state_first['retrieval_strength'] == state_second['retrieval_strength'], "Event replay is not deterministic!"
    assert state_first['storage_strength'] == state_second['storage_strength'], "Event replay is not deterministic!"

if __name__ == "__main__":
    setup_test_db()
    
    print("\\nRunning Test 1: Practice prevents forgetting...")
    test_repeated_practice_slow_forgetting()
    
    print("\\nRunning Test 2: Long inactivity causes decay...")
    test_long_inactivity_decay()
    
    print("\\nRunning Test 3: Misconception correction reduces strength...")
    test_misconception_correction()
    
    print("\\nRunning Test 4: Event replay determinism...")
    test_event_replay_determinism()
    
    print("\\nALL EDUCATIONAL MEMORY TESTS PASSED.")
