"""
tests/test_cognitive_load.py
Week 12 – Cognitive Load Intelligence Engine (CCLI) Integration Tests.
Validates Intrinsic, Extraneous, and Germane Load computation, EWMA-based rolling averages,
Cognitive Recovery Mode gating, and overload alerts.
"""

import sqlite3
import os
import sys
import uuid
import json
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- In-Memory DB Setup ---
conn = sqlite3.connect(':memory:', check_same_thread=False)
conn.row_factory = sqlite3.Row

class MockConn:
    def __init__(self, c): self.conn = c
    def cursor(self): return self.conn.cursor()
    def commit(self): self.conn.commit()
    def close(self): pass

import database
database.DB_PATH = ':memory:'
database.get_conn = lambda: MockConn(conn)

import cognitive_load_engine
cognitive_load_engine.get_conn = lambda: MockConn(conn)

import context_engine
context_engine.get_conn = lambda: MockConn(conn)


def setup_test_db():
    cur = conn.cursor()

    # Create Core Tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT, topic TEXT, subtopic TEXT, difficulty TEXT,
        prompt TEXT, option_a TEXT, option_b TEXT, option_c TEXT, option_d TEXT,
        correct_index INTEGER, estimated_time INTEGER, status TEXT DEFAULT 'Draft',
        student_responses_count INTEGER DEFAULT 0, qqi_score REAL DEFAULT 80.0,
        irt_difficulty REAL, irt_discrimination REAL, irt_guessing REAL DEFAULT 0.0,
        irt_run_id TEXT, irt_confidence REAL, irt_version TEXT DEFAULT 'v1.0',
        cognitive_type TEXT, cognitive_load TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_concepts (
        question_id INTEGER,
        concept_id TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        student_email TEXT,
        correct INTEGER,
        response_time REAL DEFAULT 30.0,
        hesitation_score REAL DEFAULT 0.0,
        backspace_count INTEGER DEFAULT 0,
        rewrite_count INTEGER DEFAULT 0,
        same_option_clicks INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_cognitive_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT UNIQUE,
        irt_ability REAL,
        irt_ability_se REAL,
        irt_ability_percentile REAL,
        irt_confidence REAL,
        irt_ability_version TEXT DEFAULT 'v1.0',
        updated_at TEXT
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
    CREATE TABLE IF NOT EXISTS misconception_clusters (
        cluster_id TEXT PRIMARY KEY,
        concept_id TEXT,
        misconception_name TEXT,
        severity TEXT,
        evidence_id TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS misconception_evidences (
        evidence_id TEXT PRIMARY KEY,
        student_email TEXT,
        concept_id TEXT,
        status TEXT DEFAULT 'active'
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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS assessment_blueprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT,
        subtopic TEXT
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

    # Week 12 Tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cognitive_load_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cognitive_load_events (
        event_id TEXT PRIMARY KEY,
        response_id INTEGER,
        student_email TEXT,
        concept_id TEXT,
        intrinsic_load REAL,
        extraneous_load REAL,
        germane_load REAL,
        composite_load REAL,
        explanation_json TEXT,
        algorithm_version TEXT DEFAULT 'v1.0',
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT,
        FOREIGN KEY (response_id) REFERENCES responses(id)
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
        last_computed_at TEXT,
        alert_status TEXT DEFAULT 'normal',
        config_version TEXT DEFAULT 'v1.0'
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cognitive_load_alerts (
        alert_id TEXT PRIMARY KEY,
        student_email TEXT,
        ccli_value REAL,
        severity TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT,
        resolved_at TEXT,
        resolution_note TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cognitive_load_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        old_ccli REAL,
        new_ccli REAL,
        alert_status TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()


def seed_test_data():
    cur = conn.cursor()

    # Clear tables
    cur.execute("DELETE FROM question_bank")
    cur.execute("DELETE FROM question_concepts")
    cur.execute("DELETE FROM responses")
    cur.execute("DELETE FROM student_cognitive_profiles")
    cur.execute("DELETE FROM concept_memory")
    cur.execute("DELETE FROM kg_edges")
    cur.execute("DELETE FROM cognitive_load_config")
    cur.execute("DELETE FROM student_cognitive_load_state")
    cur.execute("DELETE FROM cognitive_load_events")
    cur.execute("DELETE FROM cognitive_load_alerts")
    cur.execute("DELETE FROM cognitive_load_history")

    # Seed configs
    ccli_defaults = {
        "weight_intrinsic_load": 0.4,
        "weight_extraneous_load": 0.3,
        "weight_germane_load": 0.3,
        "weight_bloom_level": 0.3,
        "weight_irt_difficulty": 0.4,
        "weight_prereq_complexity": 0.3,
        "weight_prompt_length": 0.5,
        "weight_interaction_complexity": 0.5,
        "weight_sat": 0.4,
        "weight_hesitation": 0.3,
        "weight_backspace_efficiency": 0.3,
        "ewma_alpha": 0.25,
        "fatigue_threshold": 0.7,
        "recovery_threshold": 0.5,
        "memory_discount_factor": 0.3,
    }
    for k, v in ccli_defaults.items():
        cur.execute("INSERT OR IGNORE INTO cognitive_load_config (key, value) VALUES (?, ?)", (k, v))

    # Context Engine Config Defaults
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

    # Add 2 questions
    cur.execute("""
        INSERT INTO question_bank (id, prompt, cognitive_type, estimated_time, qqi_score, irt_difficulty, irt_discrimination)
        VALUES (1, 'Find 5 + 3', 'remember', 10, 95.0, -1.0, 1.2),
               (2, 'Solve for x if 3x + 5 = 20. Outline your working and write steps.', 'apply', 40, 70.0, 1.5, 1.8)
    """)

    cur.execute("""
        INSERT INTO question_concepts (question_id, concept_id)
        VALUES (1, 'addition'),
               (2, 'linear-equations')
    """)

    cur.execute("""
        INSERT INTO kg_edges (source_id, target_id, relation_type, weight)
        VALUES ('addition', 'linear-equations', 'prerequisite_of', 1.0)
    """)

    cur.execute("""
        INSERT INTO student_cognitive_profiles (student_email, irt_ability, irt_confidence)
        VALUES ('alice@test.com', 0.5, 0.8)
    """)

    cur.execute("""
        INSERT INTO concept_memory (student_email, concept_id, memory_strength, memory_state, reinforcement_count)
        VALUES ('alice@test.com', 'addition', 0.8, 'Mastered', 3),
               ('alice@test.com', 'linear-equations', 0.5, 'Review', 1)
    """)

    conn.commit()


import unittest

class TestCognitiveLoad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_db()

    def setUp(self):
        seed_test_data()

    def test_config_loading_and_update(self):
        config = cognitive_load_engine._load_ccli_config()
        self.assertEqual(config["ewma_alpha"], 0.25)
        self.assertEqual(config["fatigue_threshold"], 0.7)

        cognitive_load_engine.update_ccli_config("ewma_alpha", 0.35)
        config2 = cognitive_load_engine._load_ccli_config()
        self.assertEqual(config2["ewma_alpha"], 0.35)

    def test_ccli_load_calculation_flow(self):
        cur = conn.cursor()
        # Add response for alice on subtraction/addition (low struggle)
        cur.execute("""
            INSERT INTO responses (id, question_id, student_email, correct, response_time, hesitation_score, backspace_count)
            VALUES (101, 1, 'alice@test.com', 1, 8.0, 0.1, 0)
        """)
        conn.commit()

        res = cognitive_load_engine.compute_and_save_cognitive_load(101)
        self.assertIn("ccli", res)
        self.assertEqual(res["student_email"], "alice@test.com")
        self.assertEqual(res["status"], "normal")

        # Verify event saved and explanation JSON populated
        cur.execute("SELECT * FROM cognitive_load_events WHERE response_id = 101")
        evt = cur.fetchone()
        self.assertIsNotNone(evt)
        self.assertEqual(evt["concept_id"], "addition")
        
        explanation = json.loads(evt["explanation_json"])
        self.assertIn("intrinsic", explanation)
        self.assertIn("extraneous", explanation)
        self.assertIn("germane", explanation)

    def test_rolling_state_updates_and_overload_alert(self):
        cur = conn.cursor()
        # Insert multiple highly fatigued responses for alice (long time, incorrect, high clicks/backspaces)
        cur.execute("""
            INSERT INTO responses (id, question_id, student_email, correct, response_time, hesitation_score, backspace_count, same_option_clicks)
            VALUES (201, 2, 'alice@test.com', 0, 120.0, 0.9, 10, 8),
                   (202, 2, 'alice@test.com', 0, 150.0, 0.8, 12, 10),
                   (203, 2, 'alice@test.com', 0, 180.0, 0.9, 15, 9)
        """)
        conn.commit()

        # Update config to ensure high reactivity (EWMA_ALPHA = 0.5)
        cognitive_load_engine.update_ccli_config("ewma_alpha", 0.5)
        cognitive_load_engine.update_ccli_config("fatigue_threshold", 0.35)
        cognitive_load_engine.update_ccli_config("recovery_threshold", 0.2)

        # Trigger sequence
        res1 = cognitive_load_engine.compute_and_save_cognitive_load(201)
        res2 = cognitive_load_engine.compute_and_save_cognitive_load(202)
        res3 = cognitive_load_engine.compute_and_save_cognitive_load(203)

        # Alice should transition to fatigued
        self.assertEqual(res3["status"], "fatigued")

        # Check alert exists
        cur.execute("SELECT status, severity FROM cognitive_load_alerts WHERE student_email = 'alice@test.com'")
        alert = cur.fetchone()
        self.assertIsNotNone(alert)
        self.assertEqual(alert["status"], "active")

        # Now trigger a recovery response (Correct, super fast, 0 hesitation)
        cur.execute("""
            INSERT INTO responses (id, question_id, student_email, correct, response_time, hesitation_score, backspace_count)
            VALUES (204, 1, 'alice@test.com', 1, 2.0, 0.0, 0)
        """)
        conn.commit()

        # Set alpha higher for testing recovery shift
        cognitive_load_engine.update_ccli_config("ewma_alpha", 0.9)
        cognitive_load_engine.update_ccli_config("recovery_threshold", 0.25)

        res4 = cognitive_load_engine.compute_and_save_cognitive_load(204)
        self.assertEqual(res4["status"], "normal")

        # Alert should be marked resolved
        cur.execute("SELECT status FROM cognitive_load_alerts WHERE student_email = 'alice@test.com' ORDER BY resolved_at DESC LIMIT 1")
        alert_post = cur.fetchone()
        self.assertEqual(alert_post["status"], "resolved")

    def test_context_engine_cognitive_recovery_mode(self):
        cur = conn.cursor()
        # Ensure student is marked fatigued
        cur.execute("""
            INSERT INTO student_cognitive_load_state (student_email, rolling_il, rolling_el, rolling_gl, rolling_ccli, confidence, alert_status)
            VALUES ('alice@test.com', 0.8, 0.8, 0.1, 0.8, 1.0, 'fatigued')
        """)
        # Seed a new concept in alice's memory profile with reinforcement_count = 0
        cur.execute("""
            INSERT INTO concept_memory (student_email, concept_id, memory_strength, memory_state, reinforcement_count)
            VALUES ('alice@test.com', 'new-concept', 0.5, 'Unknown', 0)
        """)
        conn.commit()

        recs = context_engine.generate_contextual_recommendations('alice@test.com')
        
        # Verify new-concept is BLOCKED (no new concepts allowed when fatigued)
        new_concept_recs = [r for r in recs["blocked_candidates"] if r["target"] == "new-concept" and r["status"] == "blocked"]
        self.assertTrue(len(new_concept_recs) > 0)
        self.assertIn("Blocked new concept recommendation under Cognitive Recovery Mode", new_concept_recs[0]["reason"])

        # Check standard Practice on non-prereq is blocked
        # addition is a prereq of linear-equations, but linear-equations is not a prereq
        equations_recs = [r for r in recs["blocked_candidates"] if r["target"] == "linear-equations" and r["category"] == "Practice"]
        self.assertTrue(len(equations_recs) > 0)
        self.assertEqual(equations_recs[0]["status"], "blocked")
        self.assertIn("Blocked standard Practice under Cognitive Recovery Mode", equations_recs[0]["reason"])


if __name__ == '__main__':
    unittest.main()
