"""
tests/test_cdo.py
Week 13 – Cognitive Decision Orchestrator (CDO) Integration Tests.
Validates modular rule objects, priority sorting, conflict logging, and Context Engine integration.
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

import decision_engine
decision_engine.get_conn = lambda: MockConn(conn)

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

    # Week 13 Tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decision_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decision_runs (
        run_id TEXT PRIMARY KEY,
        student_email TEXT,
        concept_id TEXT,
        final_decision TEXT,
        confidence_score REAL,
        decision_policy_version TEXT DEFAULT 'v1.0',
        trigger_source TEXT,
        timestamp TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decision_explanations (
        run_id TEXT PRIMARY KEY,
        student_email TEXT,
        concept_id TEXT,
        winning_rule TEXT,
        candidates_json TEXT,
        conflicts_json TEXT,
        decision_reason TEXT,
        decision_policy_version TEXT DEFAULT 'v1.0',
        FOREIGN KEY (run_id) REFERENCES decision_runs(run_id)
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
    cur.execute("DELETE FROM teacher_notes")
    cur.execute("DELETE FROM student_cognitive_load_state")
    cur.execute("DELETE FROM decision_config")
    cur.execute("DELETE FROM decision_runs")
    cur.execute("DELETE FROM decision_explanations")
    cur.execute("DELETE FROM misconception_evidences")
    cur.execute("DELETE FROM misconception_clusters")

    # Seed configs
    cdo_defaults = {
        "priority_rule_teacher": 100.0,
        "priority_rule_load": 90.0,
        "priority_rule_misconception": 80.0,
        "priority_rule_apd": 70.0,
        "priority_rule_memory": 60.0,
        "priority_rule_nbirt": 50.0,
    }
    for k, v in cdo_defaults.items():
        cur.execute("INSERT OR IGNORE INTO decision_config (key, value) VALUES (?, ?)", (k, v))

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

    # Seed memory profile for alice
    cur.execute("""
        INSERT INTO concept_memory (student_email, concept_id, memory_strength, memory_state, reinforcement_count)
        VALUES ('alice@test.com', 'arrays', 0.8, 'Mastered', 4),
               ('alice@test.com', 'sorting', 0.2, 'Forgotten', 2)
    """)

    # Seed prerequisite array -> sorting
    cur.execute("""
        INSERT INTO kg_edges (source_id, target_id, relation_type, weight)
        VALUES ('arrays', 'sorting', 'prerequisite_of', 1.0)
    """)

    # Seed student profiles
    cur.execute("""
        INSERT INTO student_cognitive_profiles (student_email, irt_ability, irt_confidence)
        VALUES ('alice@test.com', 1.2, 0.8)
    """)

    conn.commit()


import unittest

class TestCDOOrchestrator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_db()

    def setUp(self):
        seed_test_data()

    def test_cdo_priorities_loading(self):
        priorities = decision_engine._load_cdo_priorities()
        self.assertEqual(priorities["TeacherRule"], 100.0)
        self.assertEqual(priorities["NBIRTRule"], 50.0)

    def test_teacher_override_wins_with_highest_priority(self):
        cur = conn.cursor()
        # Seed a blocking teacher note for alice on concept 'sorting'
        cur.execute("""
            INSERT INTO teacher_notes (student_email, observation, reason)
            VALUES ('alice@test.com', 'Block sorting practice.', 'Need to review basics first.')
        """)
        conn.commit()

        # Run pipeline
        res = decision_engine.execute_decision_pipeline('alice@test.com', 'sorting')
        self.assertEqual(res["final_decision"], "Pause")
        self.assertEqual(res["winning_rule"], "TeacherRule")
        self.assertTrue(len(res["conflicts"]) > 0) # Other rules were triggered but lost

        # Verify DB logs
        cur.execute("SELECT final_decision, confidence_score FROM decision_runs WHERE run_id = ?", (res["run_id"],))
        run_row = cur.fetchone()
        self.assertEqual(run_row["final_decision"], "Pause")
        self.assertEqual(run_row["confidence_score"], 1.0)

    def test_conflict_logging_and_tracing(self):
        cur = conn.cursor()
        # Seed both CCLI fatigue and Memory decay
        cur.execute("""
            INSERT INTO student_cognitive_load_state (student_email, rolling_il, rolling_el, rolling_gl, rolling_ccli, confidence, alert_status)
            VALUES ('alice@test.com', 0.8, 0.8, 0.1, 0.85, 1.0, 'fatigued')
        """)
        conn.commit()

        res = decision_engine.execute_decision_pipeline('alice@test.com', 'sorting')
        # LoadRule has priority 90, MemoryRule has priority 60, NBIRTRule has priority 50.
        # LoadRule should win: final_decision = 'Review'
        self.assertEqual(res["final_decision"], "Review")
        self.assertEqual(res["winning_rule"], "LoadRule")
        self.assertEqual(res["confidence_score"], 0.85)

        # Check that conflicts includes MemoryRule and NBIRTRule
        conflict_names = [c["rule_name"] for c in res["conflicts"]]
        self.assertIn("MemoryRule", conflict_names)
        self.assertIn("NBIRTRule", conflict_names)

        # Check DB explanation logs
        cur.execute("SELECT candidates_json, conflicts_json FROM decision_explanations WHERE run_id = ?", (res["run_id"],))
        exp_row = cur.fetchone()
        self.assertIsNotNone(exp_row)
        candidates = json.loads(exp_row["candidates_json"])
        conflicts = json.loads(exp_row["conflicts_json"])
        self.assertEqual(len(candidates), 3) # Load, Memory, NBIRT
        self.assertEqual(len(conflicts), 2) # Memory, NBIRT

    def test_context_engine_integration_blocks_by_cdo(self):
        cur = conn.cursor()
        # Seed a misconception for 'arrays' (remediation)
        cur.execute("""
            INSERT INTO misconception_evidences (evidence_id, student_email, concept_id, status)
            VALUES ('mcp_001', 'alice@test.com', 'arrays', 'active')
        """)
        cur.execute("""
            INSERT INTO misconception_clusters (cluster_id, concept_id, misconception_name, severity, evidence_id)
            VALUES ('cluster_001', 'arrays', 'Index out of bounds confusion', 'High', 'mcp_001')
        """)
        conn.commit()

        # CDO will output 'Remediation' due to the active misconception
        cdo_res = decision_engine.execute_decision_pipeline('alice@test.com', 'arrays')
        self.assertEqual(cdo_res["final_decision"], "Remediation")

        # Now query recommendations from the Context Engine
        recs = context_engine.generate_contextual_recommendations('alice@test.com')
        
        # Verify that 'Practice' and 'Review' actions are BLOCKED by CDO Orchestrator
        blocked_practice = [r for r in recs["blocked_candidates"] if r["target"] == "arrays" and r["category"] == "Practice"]
        self.assertTrue(len(blocked_practice) > 0)
        self.assertIn("Blocked by CDO Orchestrator. Winning decision was Remediation", blocked_practice[0]["reason"])

        # Remediation should be generated/active
        remed_recs = [r for r in recs["recommendations"] if r["target"] == "arrays" and r["category"] == "Remediation"]
        self.assertTrue(len(remed_recs) > 0)
        self.assertEqual(remed_recs[0]["status"], "generated")


if __name__ == '__main__':
    unittest.main()
