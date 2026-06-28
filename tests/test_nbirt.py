"""
tests/test_nbirt.py
Week 11 – Neural Bayesian Item Response Theory (NBIRT) Integration Tests.
Validates 2PL probability math, EM optimization loop, student ability estimation
with cognitive priors, context engine integration, and fallbacks.
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

import nbirt_engine
nbirt_engine.get_conn = lambda: MockConn(conn)

import context_engine
context_engine.get_conn = lambda: MockConn(conn)


def setup_test_db():
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT, topic TEXT, subtopic TEXT, difficulty TEXT,
        prompt TEXT, option_a TEXT, option_b TEXT, option_c TEXT, option_d TEXT,
        correct_index INTEGER, estimated_time INTEGER, status TEXT DEFAULT 'Draft',
        student_responses_count INTEGER DEFAULT 0, qqi_score REAL DEFAULT 80.0,
        irt_difficulty REAL, irt_discrimination REAL, irt_guessing REAL DEFAULT 0.0,
        irt_run_id TEXT, irt_confidence REAL, irt_version TEXT DEFAULT 'v1.0'
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
        response_time REAL DEFAULT 30.0
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
        reinforcement_count INTEGER, retrieval_success_rate REAL,
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
        status TEXT DEFAULT 'candidate'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS misconception_evidence (
        id TEXT PRIMARY KEY,
        cluster_id TEXT,
        student_email TEXT,
        status TEXT DEFAULT 'active'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS context_recommendations_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v2.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS nbirt_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS nbirt_runs (
        run_id TEXT PRIMARY KEY,
        started_at TEXT,
        completed_at TEXT,
        items_estimated INTEGER DEFAULT 0,
        students_estimated INTEGER DEFAULT 0,
        em_iterations INTEGER DEFAULT 0,
        max_parameter_delta REAL DEFAULT 0.0,
        status TEXT DEFAULT 'running',
        config_version TEXT DEFAULT 'v1.0',
        execution_time_ms REAL DEFAULT 0.0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS nbirt_item_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        run_id TEXT,
        old_b REAL,
        new_b REAL,
        old_a REAL,
        new_a REAL,
        irt_confidence REAL,
        n_responses INTEGER,
        algorithm_version TEXT DEFAULT 'v1.0',
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS nbirt_ability_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        run_id TEXT,
        old_ability REAL,
        new_ability REAL,
        old_se REAL,
        new_se REAL,
        old_percentile REAL,
        new_percentile REAL,
        prior_used TEXT,
        n_items_used INTEGER,
        irt_confidence REAL,
        algorithm_version TEXT DEFAULT 'v1.0',
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT
    )
    """)

    # --- Seed Default Configs ---
    now = datetime_now()
    nbirt_defaults = [
        ("min_responses_per_item", 5.0),  # Low threshold for testing
        ("min_items_per_student", 2.0),   # Low threshold for testing
        ("em_max_iterations", 10.0),
        ("em_convergence_threshold", 0.01),
        ("prior_ability_mean", 0.0),
        ("prior_ability_sd", 1.0),
        ("memory_weight_in_prior", 0.4),
        ("misconception_penalty_in_prior", 0.2),
        ("discrimination_bounds_low", 0.2),
        ("discrimination_bounds_high", 3.0),
        ("min_irt_confidence_for_context", 0.3),
        ("theta_grid_points", 21.0),
        ("theta_grid_min", -3.0),
        ("theta_grid_max", 3.0),
    ]
    for k, v in nbirt_defaults:
        cur.execute(
            "INSERT OR IGNORE INTO nbirt_config (key, value, config_version, updated_by, updated_at) VALUES (?, ?, 'v1.0', 'system', ?)",
            (k, v, now)
        )

    context_defaults = [
        ("WEIGHT_MEMORY_RISK", 0.2),
        ("WEIGHT_PREREQUISITE_IMPORTANCE", 0.1),
        ("WEIGHT_MISCONCEPTION_SEVERITY", 0.1),
        ("WEIGHT_QQI_CONFIDENCE", 0.1),
        ("WEIGHT_TEACHER_PRIORITY", 0.1),
        ("WEIGHT_EXAM_WEIGHT", 0.1),
        ("WEIGHT_IRT_ALIGNMENT", 0.3),
    ]
    for k, v in context_defaults:
        cur.execute(
            "INSERT OR IGNORE INTO context_recommendations_config (key, value, config_version, updated_by, updated_at) VALUES (?, ?, 'v2.0', 'system', ?)",
            (k, v, now)
        )

    conn.commit()


def datetime_now():
    from datetime import datetime as dt
    return dt.now().isoformat()


# ==================== TEST CASES ====================

def test_config_loading():
    """Test 1: Config parameters load from DB config table correctly."""
    cfg = nbirt_engine._load_nbirt_config()
    assert cfg["min_responses_per_item"] == 5.0
    assert cfg["min_items_per_student"] == 2.0
    assert cfg["theta_grid_points"] == 21.0
    print("[PASS] test_config_loading")


def test_2pl_probability():
    """Test 2: Standard 2PL probability function math is correct."""
    # P(correct | θ=0, a=1.0, b=0.0) = 0.5
    p1 = nbirt_engine._2pl_probability(0.0, 1.0, 0.0)
    assert abs(p1 - 0.5) < 1e-6

    # P(correct | θ=1.0, a=1.0, b=0.0) = 1 / (1 + e^-1) ≈ 0.731058
    p2 = nbirt_engine._2pl_probability(1.0, 1.0, 0.0)
    assert abs(p2 - 0.731058) < 1e-4
    print("[PASS] test_2pl_probability")


def test_cognitive_prior_shifts_ability():
    """Test 3: Student memory strength shifts ability prior positively."""
    cur = conn.cursor()
    cur.execute("DELETE FROM concept_memory")
    cur.execute("DELETE FROM misconception_clusters")
    cur.execute("DELETE FROM misconception_evidence")
    conn.commit()

    student_email = "prior_test@student.com"
    # Seed high memory strength (0.9)
    cur.execute("""
        INSERT INTO concept_memory (student_email, concept_id, memory_strength, memory_confidence, memory_state, last_updated)
        VALUES (?, 'c1', 0.9, 0.8, 'Stable', ?)
    """, (student_email, datetime_now()))
    conn.commit()

    cfg = nbirt_engine._load_nbirt_config()
    mu, sd, reasons = nbirt_engine._compute_cognitive_prior(student_email, cfg)
    
    assert mu > 0.0, f"Expected positive prior mean delta, got {mu}"
    assert sd < 1.0, f"Expected reduced standard deviation, got {sd}"
    assert reasons["memory_strength"] == 0.9
    print("[PASS] test_cognitive_prior_shifts_ability")


def test_misconception_penalizes_prior():
    """Test 4: Confirmed misconceptions penalize student ability prior mean."""
    cur = conn.cursor()
    cur.execute("DELETE FROM concept_memory")
    cur.execute("DELETE FROM misconception_clusters")
    cur.execute("DELETE FROM misconception_evidence")
    conn.commit()

    student_email = "mcp_test@student.com"
    cur.execute("INSERT INTO misconception_clusters (cluster_id, concept_id, misconception_name, severity, status) VALUES ('m1', 'c1', 'Divide by Zero', 'High', 'confirmed')")
    cur.execute("INSERT INTO misconception_evidence (id, cluster_id, student_email, status) VALUES ('e1', 'm1', ?, 'active')", (student_email,))
    conn.commit()

    cfg = nbirt_engine._load_nbirt_config()
    mu, sd, reasons = nbirt_engine._compute_cognitive_prior(student_email, cfg)
    
    assert mu < 0.0, f"Expected negative prior mean due to misconception penalty, got {mu}"
    assert reasons["active_misconceptions"] == 1
    print("[PASS] test_misconception_penalizes_prior")


def test_student_ability_estimation_cold_start():
    """Test 5: Ability estimation respects cold start criteria (theta is NULL when evidence count < minimum)."""
    cur = conn.cursor()
    cur.execute("DELETE FROM responses")
    cur.execute("DELETE FROM student_cognitive_profiles")
    conn.commit()

    student_email = "cold_start@student.com"
    # Seed only 1 response (minimum is 2.0)
    cur.execute("INSERT INTO responses (question_id, student_email, correct) VALUES (101, ?, 1)", (student_email,))
    conn.commit()

    res = nbirt_engine.estimate_student_ability(student_email)
    assert res["irt_ability"] is None
    assert res["status"] == "cold_start"
    print("[PASS] test_student_ability_estimation_cold_start")


def test_student_ability_calibrated_estimation():
    """Test 6: Latent ability theta, SE, and percentile are estimated correctly when minimum responses met."""
    cur = conn.cursor()
    cur.execute("DELETE FROM responses")
    cur.execute("DELETE FROM question_bank")
    conn.commit()

    student_email = "calibrated@student.com"
    # Seed 3 items with estimated parameters
    cur.execute("INSERT INTO question_bank (id, irt_difficulty, irt_discrimination, student_responses_count) VALUES (1, 0.0, 1.0, 10)")
    cur.execute("INSERT INTO question_bank (id, irt_difficulty, irt_discrimination, student_responses_count) VALUES (2, -1.0, 1.0, 10)")
    cur.execute("INSERT INTO question_bank (id, irt_difficulty, irt_discrimination, student_responses_count) VALUES (3, 1.0, 1.0, 10)")
    
    # Student answered all correct (ability should be positive)
    cur.execute("INSERT INTO responses (question_id, student_email, correct) VALUES (1, ?, 1)", (student_email,))
    cur.execute("INSERT INTO responses (question_id, student_email, correct) VALUES (2, ?, 1)", (student_email,))
    cur.execute("INSERT INTO responses (question_id, student_email, correct) VALUES (3, ?, 1)", (student_email,))
    conn.commit()

    res = nbirt_engine.estimate_student_ability(student_email)
    assert res["status"] == "calibrated"
    assert res["irt_ability"] > 0.0
    assert res["irt_ability_se"] > 0.0
    assert res["irt_ability_percentile"] > 50.0
    assert res["irt_confidence"] > 0.0
    print("[PASS] test_student_ability_calibrated_estimation")


def test_full_em_estimation_run():
    """Test 7: Full 2PL EM optimization run executes, converges, and writes parameters + histories."""
    cur = conn.cursor()
    cur.execute("DELETE FROM question_bank")
    cur.execute("DELETE FROM responses")
    cur.execute("DELETE FROM nbirt_runs")
    cur.execute("DELETE FROM nbirt_item_history")
    cur.execute("DELETE FROM nbirt_ability_history")
    conn.commit()

    # Seed 2 questions with 5 responses each (min_responses_per_item = 5.0)
    cur.execute("INSERT INTO question_bank (id, student_responses_count) VALUES (10, 5)")
    cur.execute("INSERT INTO question_bank (id, student_responses_count) VALUES (20, 5)")

    # Seed 2 students with 2 responses each (min_items_per_student = 2.0)
    students = ["s1@test.com", "s2@test.com"]
    for s in students:
        # s1 answers correct, s2 answers wrong
        cur.execute("INSERT INTO responses (question_id, student_email, correct) VALUES (10, ?, 1)", (s,))
        cur.execute("INSERT INTO responses (question_id, student_email, correct) VALUES (20, ?, 0)", (s,))
    conn.commit()

    run_id = str(uuid.uuid4())
    summary = nbirt_engine.run_nbirt_estimation(run_id=run_id)

    assert summary["run_id"] == run_id
    assert summary["status"] == "completed"
    assert summary["items_estimated"] == 2
    assert summary["students_estimated"] == 2

    # Verify database updates
    cur.execute("SELECT irt_difficulty, irt_discrimination, irt_guessing FROM question_bank WHERE id = 10")
    q_row = cur.fetchone()
    assert q_row["irt_difficulty"] is not None
    assert q_row["irt_discrimination"] is not None
    assert q_row["irt_guessing"] == 0.0  # 2PL model has guessing fixed to 0.0

    # Verify history logs
    cur.execute("SELECT count(*) FROM nbirt_item_history WHERE run_id = ?", (run_id,))
    assert cur.fetchone()[0] == 2
    cur.execute("SELECT count(*) FROM nbirt_ability_history WHERE run_id = ?", (run_id,))
    assert cur.fetchone()[0] == 2
    print("[PASS] test_full_em_estimation_run")


def test_context_engine_irt_alignment():
    """Test 8: Context Engine integrates IRT ability and item difficulty for aligned recommendations."""
    cur = conn.cursor()
    cur.execute("DELETE FROM concept_memory")
    cur.execute("DELETE FROM question_bank")
    cur.execute("DELETE FROM question_concepts")
    cur.execute("DELETE FROM student_cognitive_profiles")
    conn.commit()

    student_email = "context_irt@student.com"
    # Seed high ability θ = 1.5, confidence = 0.8
    cur.execute("""
        INSERT INTO student_cognitive_profiles (student_email, irt_ability, irt_ability_se, irt_ability_percentile, irt_confidence)
        VALUES (?, 1.5, 0.25, 93.3, 0.8)
    """, (student_email,))

    # Concept memory row
    cur.execute("""
        INSERT INTO concept_memory (student_email, concept_id, memory_strength, memory_confidence, memory_state, last_updated)
        VALUES (?, 'c100', 0.5, 0.5, 'Learning', ?)
    """, (student_email, datetime_now()))

    # Question matching the student's ability (b = 1.5)
    cur.execute("INSERT INTO question_bank (id, irt_difficulty, irt_discrimination, student_responses_count) VALUES (500, 1.5, 1.0, 20)")
    cur.execute("INSERT INTO question_concepts (question_id, concept_id) VALUES (500, 'c100')")
    conn.commit()

    res = context_engine.generate_contextual_recommendations(student_email)
    recs = res["recommendations"]
    assert len(recs) > 0

    # Verify breakdown has irt_alignment
    breakdown = recs[0]["scoring_breakdown"]
    assert "irt_alignment" in breakdown["base_components"]
    # theta=1.5, b=1.5 -> diff=0.0 -> P = 0.5 -> scaled by 2.0 = 1.0
    assert abs(breakdown["base_components"]["irt_alignment"] - 1.0) < 1e-3
    print("[PASS] test_context_engine_irt_alignment")


def test_context_engine_fallback():
    """Test 9: Context Engine falls back safely to 0.0 IRT alignment when data is absent or confidence is low."""
    cur = conn.cursor()
    cur.execute("DELETE FROM student_cognitive_profiles")
    conn.commit()

    student_email = "fallback_irt@student.com"
    cur.execute("""
        INSERT INTO concept_memory (student_email, concept_id, memory_strength, memory_confidence, memory_state, last_updated)
        VALUES (?, 'c100', 0.5, 0.5, 'Learning', ?)
    """, (student_email, datetime_now()))
    conn.commit()

    res = context_engine.generate_contextual_recommendations(student_email)
    recs = res["recommendations"]
    assert len(recs) > 0

    breakdown = recs[0]["scoring_breakdown"]
    assert "irt_alignment" in breakdown["base_components"]
    assert breakdown["base_components"]["irt_alignment"] == 0.0
    print("[PASS] test_context_engine_fallback")


if __name__ == "__main__":
    print("\n=== Week 11: NBIRT Integration Tests ===\n")
    setup_test_db()

    test_config_loading()
    test_2pl_probability()
    test_cognitive_prior_shifts_ability()
    test_misconception_penalizes_prior()
    test_student_ability_estimation_cold_start()
    test_student_ability_calibrated_estimation()
    test_full_em_estimation_run()
    test_context_engine_irt_alignment()
    test_context_engine_fallback()

    print("\n[PASS] ALL 9 Week 11 NBIRT Tests PASSED\n")
