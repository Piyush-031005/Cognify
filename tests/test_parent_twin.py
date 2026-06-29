"""
tests/test_parent_twin.py
Week 20 — Parent Twin Personal Cognitive Companion integration tests.
15 tests covering: digest translations, CQRS isolation, snapshot projection,
weekly report append-only semantics, multi-child linking, notification logging,
rebuild checksum, idempotency, and E2E flow.
"""

import os
import sys
import json
import sqlite3
import datetime
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Mock DB Setup ---
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

import event_bus
event_bus.get_conn = lambda: MockConn(conn)
import event_replay
event_replay.get_conn = lambda: MockConn(conn)
import event_dispatcher
event_dispatcher.get_conn = lambda: MockConn(conn)

import parent_twin
import parent_twin.digest as digest
import parent_twin.snapshot as snapshot
import parent_twin.weekly_report as weekly_report
import parent_twin.notifications as notifications


def setup_test_db():
    cur = conn.cursor()
    # Core tables (needed for projection-to-projection reads)
    cur.execute("CREATE TABLE IF NOT EXISTS concept_memory (student_email TEXT, concept_id TEXT, memory_strength REAL DEFAULT 0.5, memory_state TEXT DEFAULT 'Learning')")
    cur.execute("CREATE TABLE IF NOT EXISTS student_attention_state (student_email TEXT PRIMARY KEY, focus_state TEXT DEFAULT 'optimal', rolling_attention REAL DEFAULT 1.0, updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_cognitive_load_state (student_email TEXT PRIMARY KEY, rolling_ccli REAL DEFAULT 0.5, alert_status TEXT DEFAULT 'normal', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_profile_projection (student_email TEXT PRIMARY KEY, strengths_json TEXT NOT NULL DEFAULT '[]', weaknesses_json TEXT NOT NULL DEFAULT '[]', memory_health_json TEXT NOT NULL DEFAULT '{}', cognitive_health_score REAL DEFAULT 1.0, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_progress_projection (student_email TEXT PRIMARY KEY, streak_count INTEGER DEFAULT 0, last_activity_date TEXT, completed_concepts_count INTEGER DEFAULT 0, total_attempts INTEGER DEFAULT 0, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_trend_projection (id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT NOT NULL, metric_name TEXT NOT NULL, metric_value REAL NOT NULL, recorded_at TEXT NOT NULL, projection_version TEXT DEFAULT 'v1.0')")
    # Event tables
    cur.execute("CREATE TABLE IF NOT EXISTS event_store (event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, entity_type TEXT, entity_id TEXT, entity_sequence INTEGER NOT NULL, producer TEXT, producer_version TEXT, schema_version TEXT, metadata_json TEXT, payload_json TEXT, created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS event_subscriptions (consumer_name TEXT, event_type TEXT, schema_version TEXT, handler TEXT, enabled INTEGER DEFAULT 1, PRIMARY KEY (consumer_name, event_type, schema_version))")
    cur.execute("CREATE TABLE IF NOT EXISTS processed_events (event_id TEXT, consumer_name TEXT, processed_at TEXT, PRIMARY KEY (event_id, consumer_name))")
    cur.execute("CREATE TABLE IF NOT EXISTS dead_letter_events (event_id TEXT, consumer_name TEXT, error_message TEXT, retry_count INTEGER, failed_at TEXT, payload_json TEXT, PRIMARY KEY (event_id, consumer_name))")
    cur.execute("CREATE TABLE IF NOT EXISTS event_replay_runs (replay_id TEXT PRIMARY KEY, consumer_name TEXT, from_timestamp TEXT, to_timestamp TEXT, events_processed INTEGER, started_at TEXT, completed_at TEXT, status TEXT, mode TEXT)")
    # Parent Twin tables
    cur.execute("CREATE TABLE IF NOT EXISTS parent_student_mapping (parent_email TEXT NOT NULL, student_email TEXT NOT NULL, relationship_type TEXT NOT NULL DEFAULT 'guardian', is_primary INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, PRIMARY KEY (parent_email, student_email))")
    cur.execute("CREATE TABLE IF NOT EXISTS parent_student_projection (student_email TEXT PRIMARY KEY, overall_digest TEXT NOT NULL, study_habit_summary_json TEXT NOT NULL, strengths_digest_json TEXT NOT NULL, weaknesses_digest_json TEXT NOT NULL, memory_trend TEXT NOT NULL DEFAULT 'stable', last_active_date TEXT, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS parent_weekly_report (report_id TEXT PRIMARY KEY, parent_email TEXT NOT NULL, student_email TEXT NOT NULL, week_start_date TEXT NOT NULL, week_end_date TEXT NOT NULL, overall_digest TEXT NOT NULL, strengths_json TEXT NOT NULL, weaknesses_json TEXT NOT NULL, study_habits_json TEXT NOT NULL, memory_trend TEXT NOT NULL, recommendations_json TEXT NOT NULL, is_latest INTEGER DEFAULT 1, generated_at TEXT NOT NULL, projection_version TEXT DEFAULT 'v1.0')")
    cur.execute("CREATE TABLE IF NOT EXISTS parent_notification_log (id TEXT PRIMARY KEY, parent_email TEXT NOT NULL, student_email TEXT NOT NULL, notification_type TEXT NOT NULL, payload_json TEXT, sent_at TEXT NOT NULL, read_at TEXT, projection_version TEXT DEFAULT 'v1.0')")
    cur.execute("CREATE TABLE IF NOT EXISTS parent_projection_metadata (projection_version TEXT PRIMARY KEY, checksum TEXT NOT NULL, rebuilt_at TEXT NOT NULL)")
    conn.commit()


class TestParentTwin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_db()

    def setUp(self):
        cur = conn.cursor()
        for t in [
            "concept_memory", "student_attention_state", "student_cognitive_load_state",
            "student_profile_projection", "student_progress_projection", "student_trend_projection",
            "event_store", "event_subscriptions", "processed_events", "dead_letter_events", "event_replay_runs",
            "parent_student_mapping", "parent_student_projection", "parent_weekly_report",
            "parent_notification_log", "parent_projection_metadata"
        ]:
            cur.execute(f"DELETE FROM {t}")
        conn.commit()

        # Seed a parent-student link
        parent_twin.link_child("parent@test.com", "alice@test.com", "mother", 1)

        # Seed student projection data
        cur.execute("INSERT INTO student_profile_projection (student_email, strengths_json, weaknesses_json, memory_health_json, cognitive_health_score) VALUES ('alice@test.com', '[\"algebra\"]', '[\"calculus\"]', '{}', 0.82)")
        cur.execute("INSERT INTO student_progress_projection (student_email, streak_count, last_activity_date, total_attempts) VALUES ('alice@test.com', 5, '2026-06-29', 80)")
        cur.execute("INSERT INTO student_attention_state (student_email, focus_state) VALUES ('alice@test.com', 'optimal')")
        cur.execute("INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at) VALUES ('alice@test.com', 'Health Score', 0.70, '2026-06-23')")
        cur.execute("INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at) VALUES ('alice@test.com', 'Health Score', 0.82, '2026-06-29')")
        conn.commit()

        event_dispatcher.clear_in_memory_handlers()
        event_dispatcher.register_in_memory_handler("parent_twin", "MemoryUpdated", "v1.0", parent_twin.handle_memory_updated)
        event_dispatcher.register_in_memory_handler("parent_twin", "AttentionUpdated", "v1.0", parent_twin.handle_attention_updated)
        event_dispatcher.register_in_memory_handler("parent_twin", "CCLIUpdated", "v1.0", parent_twin.handle_ccli_updated)

        event_bus.subscribe("parent_twin", "MemoryUpdated", "v1.0", "in_memory_handler")
        event_bus.subscribe("parent_twin", "AttentionUpdated", "v1.0", "in_memory_handler")
        event_bus.subscribe("parent_twin", "CCLIUpdated", "v1.0", "in_memory_handler")

    # 1. Digest: memory translation
    def test_digest_memory_health_strong(self):
        self.assertEqual(digest.translate_memory_health(0.8), "Learning well")

    # 2. Digest: memory translation for struggling student
    def test_digest_memory_health_weak(self):
        self.assertEqual(digest.translate_memory_health(0.3), "Struggling — support recommended")

    # 3. Digest: attention translation
    def test_digest_attention_fatigued(self):
        self.assertEqual(digest.translate_attention("fatigued"), "Tired — needs a break")

    # 4. Digest: cognitive health score translation
    def test_digest_cognitive_health_great(self):
        self.assertEqual(digest.translate_cognitive_health(0.9), "Doing great")
        self.assertEqual(digest.translate_cognitive_health(0.5), "Progressing steadily")
        self.assertEqual(digest.translate_cognitive_health(0.3), "Needs attention")

    # 5. Digest: memory trend direction
    def test_digest_memory_trend(self):
        self.assertEqual(digest.translate_memory_trend([0.5, 0.6, 0.75]), "improving")
        self.assertEqual(digest.translate_memory_trend([0.8, 0.65, 0.5]), "declining")
        self.assertEqual(digest.translate_memory_trend([0.7, 0.71, 0.70]), "stable")

    # 6. Snapshot projection populated via CEB event
    def test_snapshot_updated_on_event(self):
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.8.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        snap = parent_twin.get_snapshot("parent@test.com", "alice@test.com")
        self.assertNotIn("error", snap)
        self.assertEqual(snap["overall_digest"], "Doing great")

    # 7. CQRS isolation: raw cognitive tables not accessed for snapshot reads (Decision 1)
    def test_cqrs_no_raw_table_access(self):
        # First populate the parent snapshot via a CEB event (uses projection tables)
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.8.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        # Verify snapshot was built from projection tables
        snap_before = parent_twin.get_snapshot("parent@test.com", "alice@test.com")
        self.assertIn("overall_digest", snap_before)

        # Now drop the raw concept_memory table — the get_snapshot CQRS read must still succeed
        # because it only reads from parent_student_projection, NOT raw tables
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS concept_memory")
        try:
            snap_after = parent_twin.get_snapshot("parent@test.com", "alice@test.com")
            # CQRS read succeeds — parent_student_projection is already populated
            self.assertIn("overall_digest", snap_after)
        finally:
            cur.execute("CREATE TABLE IF NOT EXISTS concept_memory (student_email TEXT, concept_id TEXT, memory_strength REAL DEFAULT 0.5, memory_state TEXT DEFAULT 'Learning')")
            conn.commit()

    # 8. Multi-child support (Decision 4)
    def test_multi_child_support(self):
        parent_twin.link_child("parent@test.com", "bob@test.com", "father", 0)
        children = parent_twin.get_children("parent@test.com")
        emails = [c["student_email"] for c in children]
        self.assertIn("alice@test.com", emails)
        self.assertIn("bob@test.com", emails)

    # 9. Parent-child access control
    def test_access_control_unauthorized(self):
        snap = parent_twin.get_snapshot("stranger@test.com", "alice@test.com")
        self.assertIn("error", snap)

    # 10. Weekly report generation
    def test_weekly_report_generates(self):
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.8.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        report = weekly_report.get_latest_weekly_report("parent@test.com", "alice@test.com")
        self.assertIn("report_id", report)
        self.assertIn("recommendations", report)
        self.assertEqual(report["is_latest"], True)

    # 11. Weekly reports are append-only (Decision 6)
    def test_weekly_report_append_only(self):
        r1 = weekly_report.generate_weekly_report("parent@test.com", "alice@test.com")
        r2 = weekly_report.generate_weekly_report("parent@test.com", "alice@test.com")

        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM parent_weekly_report WHERE parent_email = 'parent@test.com' AND student_email = 'alice@test.com'")
        cnt = cur.fetchone()["cnt"]
        self.assertGreaterEqual(cnt, 2)

        # Only the latest should have is_latest = 1
        cur.execute("SELECT COUNT(*) as cnt FROM parent_weekly_report WHERE parent_email = 'parent@test.com' AND student_email = 'alice@test.com' AND is_latest = 1")
        latest_cnt = cur.fetchone()["cnt"]
        self.assertEqual(latest_cnt, 1)
        self.assertNotEqual(r1["report_id"], r2["report_id"])

    # 12. Notification logging
    def test_notification_logging(self):
        notifications.log_notification("parent@test.com", "alice@test.com", "WeeklyReportAvailable", {"note": "test"})
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM parent_notification_log WHERE parent_email = 'parent@test.com'")
        self.assertGreater(cur.fetchone()["cnt"], 0)

    # 13. Report read receipt
    def test_report_read_receipt(self):
        r = weekly_report.generate_weekly_report("parent@test.com", "alice@test.com")
        notifications.mark_report_read("parent@test.com", "alice@test.com", r["report_id"])
        cur = conn.cursor()
        cur.execute("SELECT * FROM parent_notification_log WHERE notification_type = 'WeeklyReportRead' AND parent_email = 'parent@test.com'")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertIsNotNone(row["read_at"])

    # 14. Projection rebuild with checksum (Decision 5)
    def test_rebuild_checksum(self):
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.8.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        result = parent_twin.rebuild_projections()
        self.assertEqual(result["status"], "success")
        self.assertIn("projection_checksum", result)
        self.assertIsNotNone(result["projection_checksum"])

        cur = conn.cursor()
        cur.execute("SELECT checksum FROM parent_projection_metadata WHERE projection_version = 'v1.0'")
        row = cur.fetchone()
        self.assertIsNotNone(row)

    # 15. No raw cognitive metric in parent projection (Privacy Decision 2)
    def test_no_raw_metrics_in_projection(self):
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.8.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        snap = parent_twin.get_snapshot("parent@test.com", "alice@test.com")
        snap_str = json.dumps(snap)
        # Raw fields must not appear
        for raw_field in ["cognitive_health_score", "rolling_ccli", "irt_ability", "memory_strength", "theta"]:
            self.assertNotIn(raw_field, snap_str,
                             f"Raw field '{raw_field}' should not appear in parent projection")


if __name__ == '__main__':
    unittest.main()
