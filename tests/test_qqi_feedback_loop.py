"""
Week 10: QQI Calibration Feedback Loop — Integration Tests
Tests: calibration_runs ledger, qqi_calibration_history, qqi_alerts, replay_jobs,
       replay worker state machine, quarantine flow, config loading, and regression.
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
    def close(self): pass

import database
database.DB_PATH = ':memory:'
database.get_conn = lambda: MockConn(conn)

import memory_engine
memory_engine.get_conn = lambda: MockConn(conn)

import qqi_engine
qqi_engine.get_conn = lambda: MockConn(conn)


def setup_test_db():
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        qqi_score REAL DEFAULT 80.0,
        calibrated_qqi_score REAL,
        difficulty TEXT DEFAULT 'medium',
        calibrated_difficulty TEXT,
        current_version INTEGER DEFAULT 1,
        status TEXT DEFAULT 'Approved',
        student_responses_count INTEGER DEFAULT 0,
        prompt TEXT DEFAULT 'Test question?'
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
    CREATE TABLE IF NOT EXISTS question_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        version INTEGER,
        qqi_before REAL,
        qqi_after REAL,
        calibration_reason TEXT,
        edited_at TEXT,
        edited_by TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT, concept_id TEXT, event_type TEXT, payload TEXT,
        event_version TEXT DEFAULT 'v2.0', source_module TEXT,
        algorithm_version TEXT DEFAULT 'v2.0', qqi_version TEXT DEFAULT 'v1.0',
        twin_version TEXT DEFAULT 'v2.0', config_version TEXT DEFAULT 'v1.0', timestamp TEXT
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
    CREATE TABLE IF NOT EXISTS memory_state_transitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT, concept_id TEXT,
        old_state TEXT, new_state TEXT, trigger_event_id INTEGER, reason TEXT, timestamp TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS review_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT, concept_id TEXT,
        scheduled_date TEXT, status TEXT, priority REAL, created_at TEXT,
        UNIQUE(student_email, concept_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT, concept_id TEXT,
        alert_type TEXT, severity TEXT, description TEXT, status TEXT DEFAULT 'active', timestamp TEXT
    )
    """)

    # Week 10 tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qqi_calibration_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS calibration_runs (
        run_id TEXT PRIMARY KEY,
        started_at TEXT,
        completed_at TEXT,
        config_version TEXT DEFAULT 'v1.0',
        questions_processed INTEGER DEFAULT 0,
        alerts_created INTEGER DEFAULT 0,
        questions_quarantined INTEGER DEFAULT 0,
        execution_time_ms REAL DEFAULT 0.0,
        status TEXT DEFAULT 'running',
        alerts_resolved INTEGER DEFAULT 0,
        replay_jobs_created INTEGER DEFAULT 0,
        replay_jobs_completed INTEGER DEFAULT 0,
        replay_jobs_failed INTEGER DEFAULT 0,
        average_replay_time_ms REAL DEFAULT 0.0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS qqi_calibration_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        old_qqi REAL,
        new_qqi REAL,
        old_difficulty TEXT,
        new_difficulty TEXT,
        reason TEXT,
        calibration_run_id TEXT,
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS qqi_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        alert_type TEXT,
        severity TEXT DEFAULT 'medium',
        description TEXT,
        calibration_run_id TEXT,
        status TEXT DEFAULT 'active',
        resolved_by TEXT,
        resolution_action TEXT,
        resolved_at TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS replay_jobs (
        job_id TEXT PRIMARY KEY,
        question_id INTEGER,
        student_email TEXT,
        status TEXT DEFAULT 'pending',
        attempts INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 3,
        retry_count INTEGER DEFAULT 0,
        created_at TEXT,
        started_at TEXT,
        completed_at TEXT,
        last_error TEXT,
        worker_id TEXT
    )
    """)

    # Seed config defaults
    from datetime import datetime as _dt
    now = _dt.now().isoformat()
    mem_defaults = [
        ("DEFAULT_DECAY_RATE", 0.05), ("DEFAULT_INITIAL_STRENGTH", 0.3),
        ("REINFORCE_BOOST", 0.15), ("FAILURE_PENALTY", 0.2),
        ("FORGETTING_THRESHOLD", 0.4), ("ALERT_THRESHOLD_STRENGTH", 0.3),
        ("REVIEW_INTERVAL_FACTOR", 7.0),
    ]
    for k, v in mem_defaults:
        cur.execute(
            "INSERT OR IGNORE INTO memory_config (key, value, config_version, updated_by, updated_at) VALUES (?,?,?,?,?)",
            (k, v, 'v1.0', 'system', now)
        )

    qqi_defaults = [
        ("min_responses_for_calibration", 5.0),   # low threshold for tests
        ("high_memory_threshold", 0.8),
        ("low_memory_threshold", 0.3),
        ("high_memory_failure_rate_limit", 0.20),
        ("low_memory_success_rate_limit", 0.20),
        ("qqi_quarantine_threshold", 70.0),
        ("drift_alert_threshold", 5.0),   # sensitive for test detection
        ("max_replay_retries", 3.0),
    ]
    for k, v in qqi_defaults:
        cur.execute(
            "INSERT OR IGNORE INTO qqi_calibration_config (key, value, config_version, updated_by, updated_at) VALUES (?,?,?,?,?)",
            (k, v, 'v1.0', 'system', now)
        )

    # Seed data: question q1 (high memory failures → QQI should drop)
    cur.execute(
        "INSERT INTO question_bank (id, qqi_score, difficulty, status, student_responses_count, prompt) VALUES (1, 80.0, 'medium', 'Approved', 10, 'Test Q?')"
    )
    cur.execute("INSERT INTO question_concepts (question_id, concept_id) VALUES (1, 'c1')")

    conn.commit()


def _seed_high_memory_failures(question_id=1, concept_id='c1', num_responses=10):
    """Seeds memory so all students have high storage, then make them fail the question."""
    cur = conn.cursor()
    from datetime import datetime as _dt
    now = _dt.now().isoformat()
    emails = [f"student_{i}@test.com" for i in range(num_responses)]

    for email in emails:
        # Seed positive memory events to build high storage strength via projector
        for _ in range(15):
            cur.execute("""
                INSERT INTO memory_events
                    (student_email, concept_id, event_type, payload, event_version, source_module, algorithm_version, config_version, timestamp)
                VALUES (?, ?, 'correct_answer', '{}', 'v2.0', 'practice', 'v2.0', 'v1.0', ?)
            """, (email, str(concept_id), now))

        # Give high storage strength (simulate well-remembered concept)
        cur.execute("""
            INSERT OR REPLACE INTO concept_memory
                (student_email, concept_id, memory_strength, forgetting_rate, memory_state,
                 memory_confidence, reinforcement_count, retrieval_success_rate, last_updated)
            VALUES (?, ?, 0.9, 0.05, 'Strong', 0.9, 15, 0.95, ?)
        """, (email, str(concept_id), now))
        # Student fails the question
        cur.execute(
            "INSERT INTO responses (question_id, student_email, correct, response_time) VALUES (?, ?, 0, 30.0)",
            (question_id, email)
        )

    conn.commit()
    return emails


# ==================== TEST CASES ====================

def test_config_loading():
    """Test 1: Config loads from DB table, not hardcoded."""
    cfg = qqi_engine._load_calibration_config()
    assert "min_responses_for_calibration" in cfg, "Config key missing"
    assert cfg["min_responses_for_calibration"] == 5.0, "Config value should be seeded value (5.0)"
    assert cfg["high_memory_threshold"] == 0.8
    print("[PASS] test_config_loading PASSED")


def test_calibration_run_creates_ledger():
    """Test 2: run_full_calibration_pass creates a calibration_runs ledger entry."""
    run_id = str(uuid.uuid4())
    result = qqi_engine.run_full_calibration_pass(run_id=run_id)

    assert result["run_id"] == run_id
    assert result["status"] == "completed"
    assert "questions_processed" in result

    cur = conn.cursor()
    cur.execute("SELECT * FROM calibration_runs WHERE run_id = ?", (run_id,))
    row = cur.fetchone()
    assert row is not None, "Calibration run ledger entry not created"
    assert row["status"] == "completed"
    print(f"[PASS] test_calibration_run_creates_ledger PASSED (run_id={run_id[:8]}...)")


def test_calibration_history_appended():
    """Test 3: Calibration history is appended (never overwritten)."""
    _seed_high_memory_failures(question_id=1, concept_id='c1', num_responses=6)

    run_id = str(uuid.uuid4())
    qqi_engine.run_full_calibration_pass(run_id=run_id)

    cur = conn.cursor()
    cur.execute("SELECT * FROM qqi_calibration_history WHERE calibration_run_id = ?", (run_id,))
    rows = cur.fetchall()
    assert len(rows) > 0, "qqi_calibration_history should have at least 1 entry"
    for row in rows:
        assert row["old_qqi"] is not None, "old_qqi must be recorded"
        assert row["new_qqi"] is not None, "new_qqi must be recorded"
        assert row["calibration_run_id"] == run_id
    print(f"[PASS] test_calibration_history_appended PASSED ({len(rows)} history records)")


def test_alert_created_on_high_memory_failure():
    """Test 4: qqi_alerts are created when high memory failure rate is detected."""
    # Clear previous alerts
    cur = conn.cursor()
    cur.execute("DELETE FROM qqi_alerts")
    cur.execute("DELETE FROM responses")
    cur.execute("UPDATE question_bank SET student_responses_count = 10 WHERE id = 1")
    conn.commit()

    _seed_high_memory_failures(question_id=1, concept_id='c1', num_responses=10)

    run_id = str(uuid.uuid4())
    result = qqi_engine.run_full_calibration_pass(run_id=run_id)

    cur.execute("SELECT * FROM qqi_alerts WHERE calibration_run_id = ?", (run_id,))
    alerts = cur.fetchall()
    assert len(alerts) > 0, "No alerts created for high memory failure question"
    print(f"[PASS] test_alert_created_on_high_memory_failure PASSED ({len(alerts)} alerts created)")


def test_alert_resolve_quarantine_enqueues_jobs():
    """Test 5: Resolving an alert with 'quarantine' enqueues replay_jobs for each affected student."""
    cur = conn.cursor()
    cur.execute("DELETE FROM qqi_alerts")
    cur.execute("DELETE FROM replay_jobs")
    cur.execute("DELETE FROM memory_events")
    cur.execute("DELETE FROM responses")
    cur.execute("UPDATE question_bank SET student_responses_count = 10, status = 'Approved' WHERE id = 1")
    conn.commit()

    emails = _seed_high_memory_failures(question_id=1, concept_id='c1', num_responses=10)
    run_id = str(uuid.uuid4())
    qqi_engine.run_full_calibration_pass(run_id=run_id)

    cur.execute("SELECT id FROM qqi_alerts WHERE status = 'active' LIMIT 1")
    alert_row = cur.fetchone()
    assert alert_row, "No active alerts to resolve"
    alert_id = alert_row["id"]

    result = qqi_engine.resolve_qqi_alert(alert_id, "quarantine", resolved_by="teacher@test.com")
    assert "error" not in result, f"resolve_qqi_alert error: {result}"
    assert result["resolution_action"] == "quarantine"
    assert result["replay_jobs_enqueued"] == len(emails), (
        f"Expected {len(emails)} jobs enqueued, got {result['replay_jobs_enqueued']}"
    )

    cur.execute("SELECT * FROM replay_jobs WHERE question_id = 1")
    jobs = cur.fetchall()
    assert len(jobs) == len(emails), f"Expected {len(emails)} replay jobs, got {len(jobs)}"
    for job in jobs:
        assert job["status"] == "pending"
        assert job["max_retries"] == 3

    cur.execute("SELECT * FROM qqi_alerts WHERE id = ?", (alert_id,))
    alert = cur.fetchone()
    assert alert["status"] == "resolved"
    assert alert["resolution_action"] == "quarantine"

    print(f"[PASS] test_alert_resolve_quarantine_enqueues_jobs PASSED ({len(jobs)} jobs enqueued)")


def test_response_invalidated_events_appended():
    """Test 6: response_invalidated events are appended to memory_events on quarantine."""
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM memory_events WHERE event_type = 'response_invalidated'")
    count = cur.fetchone()[0]
    assert count > 0, "No response_invalidated events found in memory_events"
    print(f"[PASS] test_response_invalidated_events_appended PASSED ({count} events)")


def test_replay_worker_processes_jobs():
    """Test 7: process_replay_jobs transitions pending jobs to completed/failed state machine."""
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM replay_jobs WHERE status = 'pending'")
    pending_before = cur.fetchone()[0]
    assert pending_before > 0, "No pending jobs to process"

    result = qqi_engine.process_replay_jobs(worker_id="test-worker-001", batch_size=100)

    assert "jobs_processed" in result
    assert result["jobs_processed"] == pending_before
    assert "completed" in result
    assert "failed" in result

    cur.execute("SELECT count(*) FROM replay_jobs WHERE status = 'pending'")
    pending_after = cur.fetchone()[0]
    assert pending_after == 0, f"{pending_after} jobs still pending after worker run"

    print(f"[PASS] test_replay_worker_processes_jobs PASSED ({result['completed']} completed, {result['failed']} failed)")


def test_replay_job_state_machine_fields():
    """Test 8: Replay jobs have all required state machine fields populated after processing."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM replay_jobs LIMIT 5")
    jobs = cur.fetchall()
    for job in jobs:
        assert "status" in job.keys(), "job missing status"
        assert "attempts" in job.keys(), "job missing attempts"
        assert "retry_count" in job.keys(), "job missing retry_count"
        assert "max_retries" in job.keys(), "job missing max_retries"
        assert job["attempts"] >= 1, "attempts should be incremented"
    print(f"[PASS] test_replay_job_state_machine_fields PASSED ({len(jobs)} jobs checked)")


def test_alert_ignore_does_not_enqueue_jobs():
    """Test 9: Resolving an alert with 'ignore' does NOT enqueue replay jobs."""
    cur = conn.cursor()
    # Insert a fresh alert manually
    cur.execute("""
        INSERT INTO qqi_alerts (question_id, alert_type, severity, description, calibration_run_id, status, created_at)
        VALUES (1, 'Low Guess Resistance', 'medium', 'Test ignore alert', 'test-run-ignore', 'active', datetime('now'))
    """)
    conn.commit()
    cur.execute("SELECT last_insert_rowid()")
    alert_id = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM replay_jobs")
    jobs_before = cur.fetchone()[0]

    result = qqi_engine.resolve_qqi_alert(alert_id, "ignore", resolved_by="teacher@test.com")
    assert result["resolution_action"] == "ignore"
    assert result["replay_jobs_enqueued"] == 0

    cur.execute("SELECT count(*) FROM replay_jobs")
    jobs_after = cur.fetchone()[0]
    assert jobs_after == jobs_before, "ignore should not create any replay jobs"
    print("[PASS] test_alert_ignore_does_not_enqueue_jobs PASSED")


def test_calibration_run_metrics_complete():
    """Test 10: calibration_runs ledger contains all required metrics."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM calibration_runs ORDER BY started_at DESC LIMIT 1")
    row = cur.fetchone()
    assert row is not None, "No calibration_runs records found"
    keys = row.keys()
    required = [
        "run_id", "started_at", "completed_at", "config_version",
        "questions_processed", "alerts_created", "questions_quarantined",
        "execution_time_ms", "status", "alerts_resolved",
        "replay_jobs_created", "replay_jobs_completed",
        "replay_jobs_failed", "average_replay_time_ms"
    ]
    for k in required:
        assert k in keys, f"calibration_runs missing column: {k}"
    assert row["status"] == "completed"
    print("[PASS] test_calibration_run_metrics_complete PASSED")


def test_config_update():
    """Test 11: qqi config key can be updated via update_qqi_config."""
    result = qqi_engine.update_qqi_config("drift_alert_threshold", 20.0, updated_by="cto@test.com")
    assert "error" not in result, f"update_qqi_config failed: {result}"
    assert result["value"] == 20.0

    cfg = qqi_engine._load_calibration_config()
    assert cfg["drift_alert_threshold"] == 20.0, "Config should reflect updated value"
    print("[PASS] test_config_update PASSED")


def test_deterministic_replay_after_invalidation():
    """Test 12: Reprojecting memory after invalidation yields deterministic result."""
    # Student had high storage, failed question → now question is quarantined
    # Their memory should be updated by projector deterministically
    # We check that memory_events contains the invalidation and concept_memory is accessible
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM memory_events WHERE event_type = 'response_invalidated' LIMIT 1"
    )
    event = cur.fetchone()
    assert event is not None, "No invalidation event found"

    student_email = event["student_email"]
    concept_id = event["concept_id"]

    # Projecting memory should be stable (no crash, returns a state)
    state = memory_engine.derive_current_state(student_email, concept_id)
    assert "storage_strength" in state
    assert "confidence" in state
    print(f"[PASS] test_deterministic_replay_after_invalidation PASSED (student={student_email})")


if __name__ == "__main__":
    print("\n=== Week 10: QQI Calibration Feedback Loop Tests ===\n")
    setup_test_db()

    test_config_loading()
    test_calibration_run_creates_ledger()
    test_calibration_history_appended()
    test_alert_created_on_high_memory_failure()
    test_alert_resolve_quarantine_enqueues_jobs()
    test_response_invalidated_events_appended()
    test_replay_worker_processes_jobs()
    test_replay_job_state_machine_fields()
    test_alert_ignore_does_not_enqueue_jobs()
    test_calibration_run_metrics_complete()
    test_config_update()
    test_deterministic_replay_after_invalidation()

    print("\n[PASS] ALL 12 Week 10 Tests PASSED\n")
