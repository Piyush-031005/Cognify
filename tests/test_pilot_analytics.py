import os
import sys
import sqlite3
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
    
    # 1. Accepted, Executed, Outcome Window passed (Past)
    past_date = (datetime.now() - timedelta(days=5)).isoformat()
    cur.execute('''
        INSERT INTO teacher_recommendation_feedback 
        (context_id, action_taken, executed_at, outcome_window_days) 
        VALUES ('CTX-1', 'Accepted', ?, 3)
    ''', (past_date,))
    
    # 2. Accepted, Executed, Outcome Window pending (Future)
    recent_date = (datetime.now() - timedelta(days=1)).isoformat()
    cur.execute('''
        INSERT INTO teacher_recommendation_feedback 
        (context_id, action_taken, executed_at, outcome_window_days) 
        VALUES ('CTX-2', 'Accepted', ?, 3)
    ''', (recent_date,))
    
    # 3. Ignored
    cur.execute('''
        INSERT INTO teacher_recommendation_feedback 
        (context_id, action_taken) 
        VALUES ('CTX-3', 'Ignored')
    ''')
    conn.commit()
    return conn

def test_recommendation_effectiveness():
    # CTX-1 window passed, should calculate effectiveness
    res1 = pilot_analytics.calculate_recommendation_effectiveness('CTX-1')
    assert res1["success_category"] in ["Strong Improvement", "Moderate Improvement", "No Change", "Regression"]
    assert res1["evidence_quality"] in ["Low", "Medium", "High"]
    
    # CTX-2 window pending
    res2 = pilot_analytics.calculate_recommendation_effectiveness('CTX-2')
    assert res2["success_category"] == "Pending"
    
    # CTX-3 ignored
    res3 = pilot_analytics.calculate_recommendation_effectiveness('CTX-3')
    assert res3["success_category"] == "No Change"

def test_teacher_trust():
    trust = pilot_analytics.get_teacher_trust_score('room_1')
    assert 0.0 <= trust <= 1.0, "Trust score must be bounded between 0 and 1"

def test_evidence_dashboard():
    dashboard = pilot_analytics.generate_evidence_dashboard_metrics('room_1')
    assert len(dashboard['trends']) == 3, "Should return 3 weeks of trends"
    assert "current_teacher_trust" in dashboard

if __name__ == "__main__":
    setup_test_db()
    print("\\nRunning Pilot Analytics Tests...")
    test_recommendation_effectiveness()
    test_teacher_trust()
    test_evidence_dashboard()
    print("\\nALL PILOT ANALYTICS TESTS PASSED.")
