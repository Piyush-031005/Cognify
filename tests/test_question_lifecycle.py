"""
tests/test_question_lifecycle.py
Week 16 – Question Blueprint Intelligence & Lifecycle Engine (QBL) Integration Tests.
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

import question_lifecycle_engine
question_lifecycle_engine.get_conn = lambda: MockConn(conn)


def setup_test_db():
    cur = conn.cursor()

    # Core tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        difficulty TEXT,
        cognitive_type TEXT,
        semantic_id TEXT,
        variant_id TEXT,
        prompt TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_index INTEGER,
        explanation TEXT,
        image_url TEXT,
        source_exam TEXT,
        teacher_added INTEGER DEFAULT 0,
        teacher_email TEXT,
        tags TEXT,
        estimated_time INTEGER,
        purpose TEXT DEFAULT 'practice',
        cognitive_load TEXT DEFAULT 'medium',
        created_at TEXT,
        status TEXT DEFAULT 'Draft',
        version INTEGER DEFAULT 1,
        qqi_score REAL DEFAULT 80.0,
        qqi_confidence REAL DEFAULT 0.1,
        calibrated_qqi_score REAL,
        calibrated_difficulty TEXT,
        student_responses_count INTEGER DEFAULT 0,
        parent_question_id INTEGER,
        current_version INTEGER DEFAULT 1,
        edited_by TEXT,
        edited_at TEXT,
        change_reason TEXT,
        irt_difficulty REAL,
        irt_discrimination REAL,
        irt_guessing REAL,
        irt_confidence REAL,
        irt_drift REAL
    )
    """)

    # QBL Tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_blueprints (
        blueprint_id TEXT PRIMARY KEY,
        concept_id TEXT,
        learning_objective TEXT,
        bloom_level TEXT,
        canonical_solution TEXT,
        template TEXT,
        expected_solve_time REAL DEFAULT 120.0,
        difficulty_prior REAL DEFAULT 0.0,
        discrimination_prior REAL DEFAULT 1.0,
        guessing_prior REAL DEFAULT 0.0,
        blueprint_version TEXT DEFAULT 'v1.0',
        created_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_families (
        family_id TEXT PRIMARY KEY,
        blueprint_id TEXT,
        family_name TEXT,
        family_type TEXT,
        created_at TEXT,
        FOREIGN KEY(blueprint_id) REFERENCES question_blueprints(blueprint_id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_versions (
        question_id INTEGER PRIMARY KEY,
        family_id TEXT,
        version_number INTEGER NOT NULL,
        lineage_depth INTEGER DEFAULT 0,
        root_blueprint_id TEXT,
        generation INTEGER DEFAULT 1,
        derived_from_question_id INTEGER,
        ancestor_path TEXT,
        expected_solve_time REAL,
        observed_solve_time REAL DEFAULT 0.0,
        time_drift REAL DEFAULT 0.0,
        difficulty_prior REAL DEFAULT 0.0,
        difficulty_current REAL DEFAULT 0.0,
        difficulty_drift REAL DEFAULT 0.0,
        discrimination_prior REAL DEFAULT 1.0,
        discrimination_current REAL DEFAULT 1.0,
        guessing_prior REAL DEFAULT 0.0,
        guessing_current REAL DEFAULT 0.0,
        FOREIGN KEY(question_id) REFERENCES question_bank(id),
        FOREIGN KEY(family_id) REFERENCES question_families(family_id),
        FOREIGN KEY(derived_from_question_id) REFERENCES question_bank(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_lifecycle (
        question_id INTEGER PRIMARY KEY,
        lifecycle_status TEXT DEFAULT 'Draft',
        last_status_change TEXT,
        retired_at TEXT,
        retirement_reason TEXT,
        retirement_metrics_json TEXT,
        replaced_by_question_id INTEGER,
        FOREIGN KEY(question_id) REFERENCES question_bank(id),
        FOREIGN KEY(replaced_by_question_id) REFERENCES question_bank(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_retirement_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        old_status TEXT,
        new_status TEXT,
        transition_reason TEXT,
        retirement_metrics_json TEXT,
        actor TEXT,
        timestamp TEXT,
        FOREIGN KEY(question_id) REFERENCES question_bank(id)
    )
    """)

    conn.commit()


def seed_test_data():
    cur = conn.cursor()
    cur.execute("DELETE FROM question_bank")
    cur.execute("DELETE FROM question_blueprints")
    cur.execute("DELETE FROM question_families")
    cur.execute("DELETE FROM question_versions")
    cur.execute("DELETE FROM question_lifecycle")
    cur.execute("DELETE FROM question_retirement_history")

    # Seed blueprints
    cur.execute("""
        INSERT INTO question_blueprints (
            blueprint_id, concept_id, bloom_level, expected_solve_time,
            difficulty_prior, discrimination_prior, blueprint_version, created_at
        ) VALUES ('BP001', 'algebra', 'Application', 90.0, 0.5, 1.2, 'v1.0', '2026-06-29')
    """)
    # Seed blueprint version 2
    cur.execute("""
        INSERT INTO question_blueprints (
            blueprint_id, concept_id, bloom_level, expected_solve_time,
            difficulty_prior, discrimination_prior, blueprint_version, created_at
        ) VALUES ('BP002', 'geometry', 'Evaluation', 150.0, -0.2, 0.9, 'v2.0', '2026-06-29')
    """)

    # Seed families
    cur.execute("""
        INSERT INTO question_families (family_id, blueprint_id, family_name, created_at)
        VALUES ('FAM001', 'BP001', 'Word Problem MCQ Sibling', '2026-06-29')
    """)

    conn.commit()


import unittest

class TestQBLIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_db()

    def setUp(self):
        seed_test_data()

    def test_blueprint_inheritance(self):
        res = question_lifecycle_engine.create_question_version(
            blueprint_id="BP001",
            family_id="FAM001",
            derived_from_question_id=None,
            prompt="BP MCQ Prompt 1",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_index=0,
            explanation="Explanation",
            subject="math", topic="algebra", subtopic="equations"
        )
        self.assertNotIn("error", res)
        self.assertEqual(res["difficulty_prior"], 0.5)
        self.assertEqual(res["expected_solve_time"], 90.0)
        self.assertEqual(res["ancestor_path"], "BP001/v1")
        self.assertEqual(res["generation"], 1)

    def test_parent_prior_inheritance(self):
        # 1. Create parent question version
        p_res = question_lifecycle_engine.create_question_version(
            blueprint_id="BP001",
            family_id="FAM001",
            derived_from_question_id=None,
            prompt="Parent MCQ Prompt",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_index=1,
            explanation="Parent Explanation",
            subject="math", topic="algebra", subtopic="equations"
        )
        parent_id = p_res["question_id"]

        # 2. Simulate NBIRT calibration on parent (autoritative single source of truth)
        cur = conn.cursor()
        cur.execute("UPDATE question_bank SET irt_difficulty = -0.8, irt_discrimination = 1.4 WHERE id = ?", (parent_id,))
        conn.commit()

        # 3. Create child version derived from parent
        c_res = question_lifecycle_engine.create_question_version(
            blueprint_id="BP001",
            family_id="FAM001",
            derived_from_question_id=parent_id,
            prompt="Child MCQ Prompt",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_index=2,
            explanation="Child Explanation",
            subject="math", topic="algebra", subtopic="equations"
        )

        self.assertNotIn("error", c_res)
        # Inherits calibrated values from parent question_bank
        self.assertEqual(c_res["difficulty_prior"], -0.8)
        self.assertEqual(c_res["ancestor_path"], "BP001/v1/v2")
        self.assertEqual(c_res["generation"], 2)

    def test_independent_retirement(self):
        # Create v1 and v2 siblings
        v1 = question_lifecycle_engine.create_question_version(
            blueprint_id="BP001", family_id="FAM001", derived_from_question_id=None,
            prompt="v1", option_a="A", option_b="B", option_c="C", option_d="D", correct_index=0, explanation=""
        )
        v2 = question_lifecycle_engine.create_question_version(
            blueprint_id="BP001", family_id="FAM001", derived_from_question_id=None,
            prompt="v2", option_a="A", option_b="B", option_c="C", option_d="D", correct_index=1, explanation=""
        )

        # Retire v2 only
        ret_res = question_lifecycle_engine.retire_question_version(v2["question_id"], "Low discrimination index", replaced_by_question_id=v1["question_id"])
        self.assertEqual(ret_res["status"], "success")

        # Verify states
        cur = conn.cursor()
        cur.execute("SELECT lifecycle_status FROM question_lifecycle WHERE question_id = ?", (v1["question_id"],))
        self.assertEqual(cur.fetchone()["lifecycle_status"], "Pilot")

        cur.execute("SELECT lifecycle_status FROM question_lifecycle WHERE question_id = ?", (v2["question_id"],))
        self.assertEqual(cur.fetchone()["lifecycle_status"], "Retired")

    def test_lineage_reconstruction(self):
        # Create BP001 -> v1 -> v2 -> v3
        v1 = question_lifecycle_engine.create_question_version(
            blueprint_id="BP001", family_id="FAM001", derived_from_question_id=None,
            prompt="v1", option_a="A", option_b="B", option_c="C", option_d="D", correct_index=0, explanation=""
        )
        v2 = question_lifecycle_engine.create_question_version(
            blueprint_id="BP001", family_id="FAM001", derived_from_question_id=v1["question_id"],
            prompt="v2", option_a="A", option_b="B", option_c="C", option_d="D", correct_index=0, explanation=""
        )
        v3 = question_lifecycle_engine.create_question_version(
            blueprint_id="BP001", family_id="FAM001", derived_from_question_id=v2["question_id"],
            prompt="v3", option_a="A", option_b="B", option_c="C", option_d="D", correct_index=0, explanation=""
        )

        lin = question_lifecycle_engine.get_question_lineage(v3["question_id"])
        self.assertEqual(lin["ancestor_path"], "BP001/v1/v2/v3")
        self.assertEqual(lin["root_blueprint_id"], "BP001")
        self.assertEqual(lin["derived_from_question_id"], v2["question_id"])

    def test_drift_metrics(self):
        v1 = question_lifecycle_engine.create_question_version(
            blueprint_id="BP001", family_id="FAM001", derived_from_question_id=None,
            prompt="v1", option_a="A", option_b="B", option_c="C", option_d="D", correct_index=0, explanation=""
        )
        # Update current parameters in NBIRT source
        cur = conn.cursor()
        cur.execute("UPDATE question_bank SET irt_difficulty = 1.25 WHERE id = ?", (v1["question_id"],))
        # Update observed time details
        cur.execute("UPDATE question_versions SET observed_solve_time = 115.5 WHERE question_id = ?", (v1["question_id"],))
        conn.commit()

        drifts = question_lifecycle_engine.compute_and_cache_drifts(v1["question_id"])
        # difficulty_prior = 0.5 (inherited from BP001)
        # current = 1.25 -> drift = 1.25 - 0.5 = 0.75
        # expected_time = 90.0, observed_time = 115.5 -> drift = 115.5 - 90 = 25.5
        self.assertEqual(drifts["difficulty_drift"], 0.75)
        self.assertEqual(drifts["time_drift"], 25.5)

    def test_blueprint_versioning(self):
        # BP002 has blueprint_version = 'v2.0'
        res = question_lifecycle_engine.create_question_version(
            blueprint_id="BP002",
            family_id=None,
            derived_from_question_id=None,
            prompt="MCQ Prompt 2",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_index=0,
            explanation="Explanation",
            subject="math", topic="geometry", subtopic="lines"
        )
        self.assertEqual(res["blueprint_version"], "v2.0")

    def test_retirement_evidence(self):
        v1 = question_lifecycle_engine.create_question_version(
            blueprint_id="BP001", family_id="FAM001", derived_from_question_id=None,
            prompt="v1", option_a="A", option_b="B", option_c="C", option_d="D", correct_index=0, explanation=""
        )
        metrics = {"qqi": 31, "irt_discrimination": 0.18, "teacher_reports": 12}
        ret_res = question_lifecycle_engine.retire_question_version(
            question_id=v1["question_id"],
            reason="Ambiguous options causing low QQI",
            metrics_json=metrics
        )
        self.assertEqual(ret_res["retirement_metrics"], metrics)

        # Verify DB storage
        cur = conn.cursor()
        cur.execute("SELECT retirement_metrics_json FROM question_lifecycle WHERE question_id = ?", (v1["question_id"],))
        db_row = cur.fetchone()
        self.assertIsNotNone(db_row)
        metrics_db = json.loads(db_row["retirement_metrics_json"])
        self.assertEqual(metrics_db["qqi"], 31)

    def test_parent_path_reconstruction(self):
        # Create BP001 -> v1 -> v2
        v1 = question_lifecycle_engine.create_question_version(
            blueprint_id="BP001", family_id="FAM001", derived_from_question_id=None,
            prompt="v1", option_a="A", option_b="B", option_c="C", option_d="D", correct_index=0, explanation=""
        )
        v2 = question_lifecycle_engine.create_question_version(
            blueprint_id="BP001", family_id="FAM001", derived_from_question_id=v1["question_id"],
            prompt="v2", option_a="A", option_b="B", option_c="C", option_d="D", correct_index=0, explanation=""
        )
        
        lin = question_lifecycle_engine.get_question_lineage(v2["question_id"])
        self.assertEqual(lin["ancestor_path"], "BP001/v1/v2")


if __name__ == '__main__':
    unittest.main()
