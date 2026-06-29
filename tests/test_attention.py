"""
tests/test_attention.py
Week 15 – Attention & Circadian Intelligence (ACI) Integration Tests.
"""

import sqlite3
import os
import sys
import uuid
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- In-Memory DB Setup ---
conn = sqlite3.connect(':memory:', check_same_thread=False)
conn.row_factory = sqlite3.Row

class MockConn:
    def __init__(self, c): self.conn = c
    def cursor(self): return self.conn.cursor()
    def commit(self): self.conn.commit()
    def rollback(self): self.conn.rollback()
    def close(self): pass

import database
database.DB_PATH = ':memory:'
database.get_conn = lambda: MockConn(conn)

import attention_engine
attention_engine.get_conn = lambda: MockConn(conn)

import context_engine
context_engine.get_conn = lambda: MockConn(conn)


def setup_test_db():
    cur = conn.cursor()

    # Core tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_cognitive_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT UNIQUE,
        irt_ability REAL,
        irt_confidence REAL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS concept_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT, concept_id TEXT,
        memory_strength REAL, forgetting_rate REAL, memory_state TEXT,
        memory_confidence REAL, memory_explanation TEXT, derived_from TEXT,
        trigger_event_id INTEGER, config_version TEXT DEFAULT 'v1.0',
        reinforcement_count INTEGER DEFAULT 1, retrieval_success_rate REAL,
        last_success TEXT, last_failure TEXT, next_review_date TEXT, last_updated TEXT,
        UNIQUE(student_email, concept_id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_cognitive_load_state (
        student_email TEXT PRIMARY KEY,
        rolling_il REAL,
        rolling_el REAL,
        rolling_gl REAL,
        rolling_ccli REAL,
        confidence REAL,
        alert_status TEXT DEFAULT 'normal'
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS context_recommendations_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS misconception_clusters (
        cluster_id TEXT PRIMARY KEY,
        concept_id TEXT,
        misconception_name TEXT,
        severity TEXT,
        evidence_id TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS misconception_evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        cluster_id TEXT,
        status TEXT DEFAULT 'active'
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS assessment_blueprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT,
        subtopic TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kg_edges (
        source_id TEXT,
        target_id TEXT,
        relation_type TEXT,
        weight REAL,
        PRIMARY KEY (source_id, target_id, relation_type)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        observation TEXT,
        reason TEXT
    )
    """)

    # Week 14 Telemetry tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_telemetry_store (
        event_id TEXT PRIMARY KEY,
        student_email TEXT,
        device_type TEXT,
        event_type TEXT,
        payload_json TEXT,
        timestamp TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS derived_behavior_features (
        student_email TEXT,
        concept_id TEXT,
        interaction_entropy REAL DEFAULT 0.0,
        hesitation_index REAL DEFAULT 0.0,
        reading_speed REAL DEFAULT 0.0,
        correction_rate REAL DEFAULT 0.0,
        focus_loss_count INTEGER DEFAULT 0,
        typing_cadence REAL DEFAULT 0.0,
        scroll_entropy REAL DEFAULT 0.0,
        last_computed_at TEXT,
        PRIMARY KEY (student_email, concept_id)
    )
    """)

    # Week 15 ACI Tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attention_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attention_events (
        event_id TEXT PRIMARY KEY,
        student_email TEXT,
        concept_id TEXT,
        attention_score REAL,
        attention_decay REAL,
        circadian_factor REAL,
        session_fatigue REAL,
        focus_state TEXT,
        confidence REAL,
        explanation_json TEXT,
        attention_engine_version TEXT DEFAULT 'v1.0',
        timestamp TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_attention_state (
        student_email TEXT PRIMARY KEY,
        rolling_attention REAL,
        rolling_decay REAL,
        last_computed_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attention_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        old_state TEXT,
        new_state TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()


def seed_test_data():
    cur = conn.cursor()
    cur.execute("DELETE FROM attention_config")
    cur.execute("DELETE FROM attention_events")
    cur.execute("DELETE FROM student_attention_state")
    cur.execute("DELETE FROM attention_history")
    cur.execute("DELETE FROM derived_behavior_features")
    cur.execute("DELETE FROM raw_telemetry_store")
    cur.execute("DELETE FROM student_cognitive_load_state")
    cur.execute("DELETE FROM concept_memory")
    cur.execute("DELETE FROM misconception_clusters")
    cur.execute("DELETE FROM misconception_evidence")
    cur.execute("DELETE FROM assessment_blueprints")
    cur.execute("DELETE FROM kg_edges")
    cur.execute("DELETE FROM teacher_notes")

    # Seed configuration priorities
    aci_defaults = {
        "circadian_range_06_11": 1.0,
        "circadian_range_11_17": 0.95,
        "circadian_range_17_21": 0.90,
        "circadian_range_21_02": 0.75,
        "circadian_range_02_06": 0.60,
        "weight_focus_loss": 0.35,
        "weight_hesitation": 0.25,
        "weight_interaction_entropy": 0.20,
        "weight_typing_cadence": 0.10,
        "weight_reading_speed": 0.10,
        "attention_decay_alpha": 0.25,
        "lambda_attention_modulation": 0.35,
        "fatigue_limit": 0.65
    }
    for k, v in aci_defaults.items():
        cur.execute("INSERT OR IGNORE INTO attention_config (key, value) VALUES (?, ?)", (k, v))

    # Context Config Defaults
    context_defaults = {
        "WEIGHT_MEMORY_RISK": 0.3,
        "WEIGHT_PREREQUISITE_IMPORTANCE": 0.2,
        "WEIGHT_MISCONCEPTION_SEVERITY": 0.2,
        "WEIGHT_QQI_CONFIDENCE": 0.1,
        "WEIGHT_TEACHER_PRIORITY": 0.1,
        "WEIGHT_EXAM_WEIGHT": 0.1,
        "WEIGHT_IRT_ALIGNMENT": 0.15,
        "min_irt_confidence_for_context": 0.5
    }
    for k, v in context_defaults.items():
        cur.execute("INSERT OR IGNORE INTO context_recommendations_config (key, value) VALUES (?, ?)", (k, v))

    conn.commit()


import unittest

class TestACIIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_db()

    def setUp(self):
        seed_test_data()

    def test_configurable_circadian_ranges(self):
        config = attention_engine._load_attention_config()
        # Test 9:00 AM (expected 1.0)
        f_9 = attention_engine.calculate_circadian_factor(9, config)
        self.assertEqual(f_9, 1.0)

        # Test 11:30 PM (expected 0.75)
        f_23 = attention_engine.calculate_circadian_factor(23, config)
        self.assertEqual(f_23, 0.75)

        # Modify Config to different ranges
        cur = conn.cursor()
        cur.execute("UPDATE attention_config SET value = 0.5 WHERE key = 'circadian_range_06_11'")
        conn.commit()

        config2 = attention_engine._load_attention_config()
        f_9_updated = attention_engine.calculate_circadian_factor(9, config2)
        self.assertEqual(f_9_updated, 0.5)

    def test_missing_features_fallback(self):
        res = attention_engine.compute_and_save_attention("charlie@test.com", "math")
        self.assertEqual(res["attention_score"], 1.0)
        self.assertEqual(res["attention_decay"], 1.0)
        self.assertEqual(res["confidence"], 0.0)

    def test_low_confidence_attention(self):
        cur = conn.cursor()
        # Seed derived behavior with only 3 populated channels (focus_loss_count, hesitation_index, reading_speed)
        # interaction_entropy and typing_cadence are 0
        cur.execute("""
            INSERT INTO derived_behavior_features (
                student_email, concept_id, focus_loss_count, hesitation_index, reading_speed,
                interaction_entropy, typing_cadence
            ) VALUES ('charlie@test.com', 'math', 1, 0.4, 180.0, 0.0, 0.0)
        """)
        conn.commit()

        res = attention_engine.compute_and_save_attention("charlie@test.com", "math")
        # channels populated: focus_loss, hesitation, reading_speed -> 3/5 = 0.60
        self.assertEqual(res["confidence"], 0.60)

    def test_long_break_resets_session(self):
        cur = conn.cursor()
        # Seed raw telemetry events with a 15-minute gap
        t0 = datetime.now() - timedelta(minutes=30)
        t1 = t0 + timedelta(minutes=5)
        t2 = t1 + timedelta(minutes=15) # 15 minutes gap resets streak
        t3 = t2 + timedelta(minutes=5)

        events = [
            ("charlie@test.com", t0.isoformat()),
            ("charlie@test.com", t1.isoformat()),
            ("charlie@test.com", t2.isoformat()),
            ("charlie@test.com", t3.isoformat())
        ]
        for email, ts in events:
            cur.execute("""
                INSERT INTO raw_telemetry_store (event_id, student_email, timestamp)
                VALUES (?, ?, ?)
            """, (str(uuid.uuid4()), email, ts))
        conn.commit()

        active_mins = attention_engine.calculate_active_session_minutes("charlie@test.com", cur)
        # Streak 1: t0 to t1 = 5 minutes
        # Streak 2: t2 to t3 = 5 minutes
        # Total active minutes = 10 minutes
        self.assertAlmostEqual(active_mins, 10.0, delta=0.5)

    def test_context_engine_score_modulations(self):
        cur = conn.cursor()
        # Seed concept memory
        cur.execute("""
            INSERT INTO concept_memory (student_email, concept_id, memory_strength, memory_state)
            VALUES ('charlie@test.com', 'math', 0.5, 'At Risk')
        """)
        # Seed attention state with low attention decay (0.4)
        cur.execute("""
            INSERT INTO student_attention_state (student_email, rolling_attention, rolling_decay, last_computed_at)
            VALUES ('charlie@test.com', 0.4, 0.4, ?)
        """, (datetime.now().isoformat(),))
        # Seed latest circadian factor to 0.75
        cur.execute("""
            INSERT INTO attention_events (event_id, student_email, concept_id, circadian_factor, timestamp)
            VALUES ('evt_001', 'charlie@test.com', 'math', 0.75, ?)
        """, (datetime.now().isoformat(),))
        conn.commit()

        # Query contextual recommendations
        recs = context_engine.generate_contextual_recommendations("charlie@test.com")
        self.assertTrue(len(recs["recommendations"]) > 0)
        
        # Verify that scores are modulated softly:
        # CF * AD = 0.75 * 0.4 = 0.3
        # score = score * (1 - 0.35) + score * 0.3 * 0.35 = score * 0.755
        math_rec = [r for r in recs["recommendations"] if r["target"] == "math"]
        self.assertTrue(len(math_rec) > 0)


if __name__ == '__main__':
    unittest.main()
