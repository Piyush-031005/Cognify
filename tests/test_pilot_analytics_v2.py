import os
import sys
import sqlite3
import math
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

import pilot_analytics

def setup_test_db():
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
        intervention_id TEXT PRIMARY KEY,
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
    
    past_date = (datetime.now() - timedelta(days=5)).isoformat()
    cur.execute('''
        INSERT INTO teacher_recommendation_feedback 
        (context_id, action_taken, executed_at, outcome_window_days) 
        VALUES ('CTX-1', 'Accepted', ?, 3)
    ''', (past_date,))
    
    cur.execute('''
        INSERT INTO teacher_recommendation_feedback 
        (context_id, action_taken, executed_at, outcome_window_days) 
        VALUES ('CTX-2', 'Accepted', ?, 3)
    ''', (past_date,))
    conn.commit()
    return conn

def test_statistical_validation():
    # CTX-1 with sample_size < 30
    res1 = pilot_analytics.calculate_recommendation_effectiveness('CTX-1', sample_size=12)
    assert res1["statistical_validation"] == "Insufficient Statistical Evidence"
    assert "Verified" not in res1["success_category"]
    
    # CTX-2 with sample_size >= 30
    res2 = pilot_analytics.calculate_recommendation_effectiveness('CTX-2', sample_size=35)
    assert isinstance(res2["statistical_validation"], dict)
    assert "p_value" in res2["statistical_validation"]
    assert "Verified" in res2["success_category"]

def test_log_intervention():
    pilot_analytics.log_intervention_history(
        'INT-1', 'CTX-99', 's1@test.com', 't1@test.com', 'Q-1', 'C-1', 0.2, 0.8, 'Assigned Flashcards'
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM intervention_history WHERE intervention_id = 'INT-1'")
    row = dict(cur.fetchone())
    assert math.isclose(row["mastery_gain"], 0.6)
    assert row["qqi_version"] == 'v1.1'

if __name__ == "__main__":
    setup_test_db()
    print("\\nRunning Pilot Analytics V2 Tests...")
    test_statistical_validation()
    test_log_intervention()
    print("\\nALL PILOT ANALYTICS V2 TESTS PASSED.")
