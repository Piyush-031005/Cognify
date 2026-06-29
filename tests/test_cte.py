"""
tests/test_cte.py
Week 14 – Cross-Platform Cognitive Telemetry Engine (CTE) Integration Tests.
Validates adapters, normalizers, feature extractors, and CDO stability scores.
"""

import sqlite3
import os
import sys
import uuid
import json

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

import decision_engine
decision_engine.get_conn = lambda: MockConn(conn)

import feature_extractor
feature_extractor.get_conn = lambda: MockConn(conn)


def setup_test_db():
    cur = conn.cursor()

    # Core tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        observation TEXT,
        reason TEXT
    )
    """)
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
        memory_confidence REAL, UNIQUE(student_email, concept_id)
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
        weight REAL
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
        decision_stability TEXT,
        stability_score REAL,
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
        decision_stability TEXT,
        stability_score REAL,
        decision_policy_version TEXT DEFAULT 'v1.0',
        FOREIGN KEY (run_id) REFERENCES decision_runs(run_id)
    )
    """)

    # CTE Tables
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

    conn.commit()


def seed_test_data():
    cur = conn.cursor()
    cur.execute("DELETE FROM decision_config")
    cur.execute("DELETE FROM decision_runs")
    cur.execute("DELETE FROM decision_explanations")
    cur.execute("DELETE FROM raw_telemetry_store")
    cur.execute("DELETE FROM derived_behavior_features")
    cur.execute("DELETE FROM student_cognitive_load_state")
    cur.execute("DELETE FROM concept_memory")

    # Seed configuration priorities
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
    conn.commit()


import unittest

class TestCTEIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_db()

    def setUp(self):
        seed_test_data()

    def test_desktop_telemetry_adapter(self):
        import desktop_telemetry_adapter
        raw = {"event_type": "mouse_movement", "coordinates": [10.5, 20.0], "speed": 1.5}
        norm = desktop_telemetry_adapter.normalize_desktop_event(raw)
        self.assertEqual(norm["event_type"], "mouse_movement")
        self.assertEqual(norm["payload"]["x"], 10.5)
        self.assertEqual(norm["payload"]["speed"], 1.5)

    def test_android_telemetry_adapter(self):
        import android_telemetry_adapter
        raw = {"event_type": "touch", "x": 150.0, "y": 300.0, "pressure": 0.8}
        norm = android_telemetry_adapter.normalize_android_event(raw)
        self.assertEqual(norm["event_type"], "touch")
        self.assertEqual(norm["payload"]["x"], 150.0)
        self.assertEqual(norm["payload"]["pressure"], 0.8)

    def test_normalizer_and_feature_extraction(self):
        cur = conn.cursor()
        import telemetry_normalizer

        # Simulate raw event streams from mobile and desktop
        events = [
            {"student_email": "bob@school.edu", "device_type": "desktop", "event_type": "mouse_movement", "coordinates": [100.0, 100.0]},
            {"student_email": "bob@school.edu", "device_type": "desktop", "event_type": "mouse_movement", "coordinates": [120.0, 110.0]},
            {"student_email": "bob@school.edu", "device_type": "desktop", "event_type": "hover", "element_id": "btn_A", "duration_ms": 2500},
            {"student_email": "bob@school.edu", "device_type": "android", "event_type": "app_lifecycle", "state": "background"},
        ]

        for ev in events:
            norm = telemetry_normalizer.normalize_telemetry_payload(ev)
            cur.execute("""
                INSERT INTO raw_telemetry_store (event_id, student_email, device_type, event_type, payload_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (norm["event_id"], norm["student_email"], norm["device_type"], norm["event_type"], norm["payload_json"], norm["timestamp"]))
        conn.commit()

        # Run Feature Extractor
        res = feature_extractor.extract_and_cache_behavior_features("bob@school.edu", "math")
        self.assertEqual(res["status"], "success")
        features = res["features"]
        self.assertTrue(features["interaction_entropy"] > 0.0)
        self.assertEqual(features["hesitation_index"], 0.5) # 2500 / 5000 = 0.5
        self.assertEqual(features["focus_loss_count"], 1)

        # Retrieve from cache
        cached = feature_extractor.get_cached_behavior_features("bob@school.edu", "math")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["hesitation_index"], 0.5)

    def test_cdo_stability_computation(self):
        cur = conn.cursor()
        # Seed student profile to satisfy NBIRTRule (exploratory Practice, confidence 0.5)
        cur.execute("""
            INSERT INTO student_cognitive_profiles (student_email, irt_ability, irt_confidence)
            VALUES ('bob@school.edu', 0.5, 0.5)
        """)
        conn.commit()

        # Case 1: All rules align (only NBIRT triggered) -> Stability: HIGH (1.0)
        res1 = decision_engine.execute_decision_pipeline("bob@school.edu", "math")
        self.assertEqual(res1["decision_stability"], "HIGH")
        self.assertEqual(res1["stability_score"], 1.0)

        # Case 2: Conflicts with different action (e.g. Memory says Review (0.9), NBIRT says Practice (0.5))
        # MemoryRule priority 60, NBIRTRule priority 50. MemoryRule wins with 'Review' (0.9), NBIRTRule conflicts with 'Practice' (0.5)
        # stability = 1.0 - (0.5 / 0.9) = 0.444 -> Stability: MEDIUM
        cur.execute("""
            INSERT INTO concept_memory (student_email, concept_id, memory_strength, memory_state, memory_confidence)
            VALUES ('bob@school.edu', 'math', 0.1, 'Forgotten', 0.9)
        """)
        conn.commit()

        res2 = decision_engine.execute_decision_pipeline("bob@school.edu", "math")
        self.assertEqual(res2["final_decision"], "Review")
        self.assertEqual(res2["decision_stability"], "MEDIUM")
        self.assertAlmostEqual(res2["stability_score"], 0.444, places=3)


if __name__ == '__main__':
    unittest.main()
