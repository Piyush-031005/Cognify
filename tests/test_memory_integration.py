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
    # Misconception discovered 5 days ago
    inject_event('studentD@test.com', 'm1', 'misconception', 'initial_discovery', 5)
    state1 = memory_engine.derive_current_state('studentD@test.com', 'm1')
    assert state1['storage_strength'] > 0.5, "Misconception not initially strong"
    
    # Student corrected it today
    inject_event('studentD@test.com', 'm1', 'misconception', 'correct_answer', 0)
    state2 = memory_engine.derive_current_state('studentD@test.com', 'm1')
    
    assert state2['storage_strength'] < state1['storage_strength'], "Misconception storage strength did not decrease upon correction!"
    assert state2['retrieval_strength'] < state1['retrieval_strength'], "Misconception retrieval did not decrease!"

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
