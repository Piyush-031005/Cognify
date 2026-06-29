"""
tests/test_student_twin.py
Week 19 – Student Twin Personal Cognitive Companion integration tests.
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

import student_twin
import student_twin.profile as profile
import student_twin.progression as progression
import student_twin.recommendations as recommendations
import student_twin.timeline as timeline
import student_twin.reports as reports


def setup_test_db():
    cur = conn.cursor()
    # Core tables
    cur.execute("CREATE TABLE IF NOT EXISTS concept_memory (student_email TEXT, concept_id TEXT, memory_strength REAL DEFAULT 0.5, forgetting_rate REAL DEFAULT 0.1, memory_state TEXT DEFAULT 'Learning', reinforcement_count INTEGER DEFAULT 0, last_success TEXT, last_failure TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_attention_state (student_email TEXT PRIMARY KEY, focus_state TEXT DEFAULT 'optimal', rolling_attention REAL DEFAULT 1.0, updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_cognitive_load_state (student_email TEXT PRIMARY KEY, rolling_il REAL DEFAULT 0.0, rolling_el REAL DEFAULT 0.0, rolling_gl REAL DEFAULT 0.0, rolling_ccli REAL DEFAULT 0.5, alert_status TEXT DEFAULT 'normal', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_cognitive_profiles (student_email TEXT, concept_id TEXT, irt_ability REAL, irt_ability_se REAL, irt_ability_percentile REAL, updated_at TEXT, PRIMARY KEY (student_email, concept_id))")
    cur.execute("CREATE TABLE IF NOT EXISTS decision_runs (run_id TEXT PRIMARY KEY, student_email TEXT, concept_id TEXT, final_decision TEXT, winning_rule TEXT, confidence_score REAL, timestamp TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS event_store (event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, entity_type TEXT, entity_id TEXT, entity_sequence INTEGER NOT NULL, producer TEXT, producer_version TEXT, schema_version TEXT, metadata_json TEXT, payload_json TEXT, created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS event_subscriptions (consumer_name TEXT, event_type TEXT, schema_version TEXT, handler TEXT, enabled INTEGER DEFAULT 1, PRIMARY KEY (consumer_name, event_type, schema_version))")
    cur.execute("CREATE TABLE IF NOT EXISTS processed_events (event_id TEXT, consumer_name TEXT, processed_at TEXT, PRIMARY KEY (event_id, consumer_name))")
    cur.execute("CREATE TABLE IF NOT EXISTS dead_letter_events (event_id TEXT, consumer_name TEXT, error_message TEXT, retry_count INTEGER, failed_at TEXT, payload_json TEXT, PRIMARY KEY (event_id, consumer_name))")
    cur.execute("CREATE TABLE IF NOT EXISTS event_replay_runs (replay_id TEXT PRIMARY KEY, consumer_name TEXT, from_timestamp TEXT, to_timestamp TEXT, events_processed INTEGER, started_at TEXT, completed_at TEXT, status TEXT, mode TEXT)")

    # Student Twin Projections
    cur.execute("CREATE TABLE IF NOT EXISTS student_profile_projection (student_email TEXT PRIMARY KEY, strengths_json TEXT NOT NULL, weaknesses_json TEXT NOT NULL, memory_health_json TEXT NOT NULL, cognitive_health_score REAL DEFAULT 1.0, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_progress_projection (student_email TEXT PRIMARY KEY, streak_count INTEGER DEFAULT 0, last_activity_date TEXT, completed_concepts_count INTEGER DEFAULT 0, total_attempts INTEGER DEFAULT 0, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_goal_projection (goal_id TEXT PRIMARY KEY, student_email TEXT NOT NULL, target_concept TEXT NOT NULL, target_mastery REAL NOT NULL, current_mastery REAL NOT NULL, status TEXT DEFAULT 'IN_PROGRESS', projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_daily_summary (student_email TEXT, summary_date TEXT, avg_ccli REAL, focus_state_counts_json TEXT, response_count INTEGER DEFAULT 0, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT, PRIMARY KEY (student_email, summary_date))")
    cur.execute("CREATE TABLE IF NOT EXISTS student_timeline_projection (student_email TEXT, event_id TEXT, event_type TEXT NOT NULL, event_description TEXT NOT NULL, importance TEXT DEFAULT 'medium', timestamp TEXT NOT NULL, projection_version TEXT DEFAULT 'v1.0', PRIMARY KEY (student_email, event_id))")
    cur.execute("CREATE TABLE IF NOT EXISTS student_recommendation_history (id TEXT PRIMARY KEY, student_email TEXT NOT NULL, recommendation TEXT NOT NULL, priority_score REAL NOT NULL, confidence REAL NOT NULL, evidence_snapshot_json TEXT NOT NULL, status TEXT DEFAULT 'PENDING', generated_at TEXT NOT NULL, projection_version TEXT DEFAULT 'v1.0')")
    cur.execute("CREATE TABLE IF NOT EXISTS student_trend_projection (id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT NOT NULL, metric_name TEXT NOT NULL, metric_value REAL NOT NULL, recorded_at TEXT NOT NULL, projection_version TEXT DEFAULT 'v1.0')")
    cur.execute("CREATE TABLE IF NOT EXISTS student_achievements (id TEXT PRIMARY KEY, student_email TEXT NOT NULL, achievement_type TEXT NOT NULL, unlocked_at TEXT NOT NULL, projection_version TEXT DEFAULT 'v1.0')")
    cur.execute("CREATE TABLE IF NOT EXISTS student_projection_metadata (projection_version TEXT PRIMARY KEY, checksum TEXT NOT NULL, rebuilt_at TEXT NOT NULL)")
    conn.commit()


class TestStudentTwin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_db()

    def setUp(self):
        cur = conn.cursor()
        for t in [
            "concept_memory", "student_attention_state", "student_cognitive_load_state",
            "student_cognitive_profiles", "decision_runs", "event_store", "event_subscriptions",
            "processed_events", "dead_letter_events", "event_replay_runs",
            "student_profile_projection", "student_progress_projection", "student_goal_projection",
            "student_daily_summary", "student_timeline_projection", "student_recommendation_history",
            "student_trend_projection", "student_achievements", "student_projection_metadata"
        ]:
            cur.execute(f"DELETE FROM {t}")
        conn.commit()

        # Seed a student with memory data
        cur.execute("INSERT INTO concept_memory (student_email, concept_id, memory_strength, memory_state) VALUES ('alice@test.com', 'algebra', 0.8, 'Stable')")
        cur.execute("INSERT INTO concept_memory (student_email, concept_id, memory_strength, memory_state) VALUES ('alice@test.com', 'calculus', 0.3, 'Forgetting')")
        conn.commit()

        event_dispatcher.clear_in_memory_handlers()
        event_dispatcher.register_in_memory_handler("student_twin", "MemoryUpdated", "v1.0", student_twin.handle_memory_updated)
        event_dispatcher.register_in_memory_handler("student_twin", "AttentionUpdated", "v1.0", student_twin.handle_attention_updated)
        event_dispatcher.register_in_memory_handler("student_twin", "CCLIUpdated", "v1.0", student_twin.handle_ccli_updated)
        event_dispatcher.register_in_memory_handler("student_twin", "DecisionGenerated", "v1.0", student_twin.handle_decision_generated)

        event_bus.subscribe("student_twin", "MemoryUpdated", "v1.0", "in_memory_handler")
        event_bus.subscribe("student_twin", "AttentionUpdated", "v1.0", "in_memory_handler")
        event_bus.subscribe("student_twin", "CCLIUpdated", "v1.0", "in_memory_handler")
        event_bus.subscribe("student_twin", "DecisionGenerated", "v1.0", "in_memory_handler")

    # 1. Profile Projection Test
    def test_profile_projection(self):
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        prof = student_twin.get_student_profile("alice@test.com")
        self.assertIn("algebra", prof["strengths"])
        self.assertIn("calculus", prof["weaknesses"])
        self.assertGreater(prof["cognitive_health_score"], 0.0)
        self.assertLessEqual(prof["cognitive_health_score"], 1.0)

    # 2. Streak Computation
    def test_streak_computation(self):
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        prog = student_twin.get_student_progress("alice@test.com")
        self.assertGreaterEqual(prog["progress"].get("streak_count", 0), 1)

    # 3. Goal Tracking
    def test_goal_tracking(self):
        progression.add_student_goal("alice@test.com", "algebra", 0.75)
        
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        prog = student_twin.get_student_progress("alice@test.com")
        goal = next((g for g in prog["goals"] if g["target_concept"] == "algebra"), None)
        self.assertIsNotNone(goal)
        self.assertEqual(goal["status"], "COMPLETED")

    # 4. Daily Summary
    def test_daily_summary(self):
        cur = conn.cursor()
        cur.execute("INSERT INTO student_cognitive_load_state (student_email, rolling_ccli, alert_status) VALUES ('alice@test.com', 0.6, 'normal')")
        cur.execute("INSERT INTO student_attention_state (student_email, focus_state) VALUES ('alice@test.com', 'optimal')")
        conn.commit()

        event_bus.publish(
            event_type="CCLIUpdated", entity_type="student", entity_id="alice@test.com",
            producer="ccli_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )
        today = datetime.date.today().isoformat()
        cur.execute("SELECT * FROM student_daily_summary WHERE student_email = 'alice@test.com' AND summary_date = ?", (today,))
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row["avg_ccli"], 0.6, places=2)

    # 5. Timeline Ordering
    def test_timeline_ordering(self):
        timeline.log_timeline_event("alice@test.com", "MemoryUpdated", "Event A", "medium")
        timeline.log_timeline_event("alice@test.com", "NBIRTUpdated", "Event B", "high")
        result = student_twin.get_student_timeline("alice@test.com")
        self.assertGreaterEqual(len(result), 2)
        # Should be ordered by timestamp DESC
        timestamps = [r["timestamp"] for r in result]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    # 6. Projection Rebuild
    def test_projection_rebuild(self):
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        # Delete projections
        cur = conn.cursor()
        cur.execute("DELETE FROM student_profile_projection")
        conn.commit()

        # Rebuild
        result = student_twin.rebuild_projections()
        self.assertIn("projection_checksum", result)
        self.assertIsNotNone(result["projection_checksum"])

        cur.execute("SELECT * FROM student_projection_metadata WHERE projection_version = 'v1.0'")
        meta = cur.fetchone()
        self.assertIsNotNone(meta)
        self.assertIsNotNone(meta["checksum"])

    # 7. Recommendation Lifecycle
    def test_recommendation_lifecycle(self):
        cur = conn.cursor()
        cur.execute("INSERT INTO student_cognitive_load_state (student_email, rolling_ccli, alert_status) VALUES ('alice@test.com', 0.9, 'fatigued')")
        cur.execute("INSERT INTO decision_runs (run_id, student_email, concept_id, final_decision, winning_rule, confidence_score, timestamp) VALUES ('r1', 'alice@test.com', 'algebra', 'Review', 'Load', 0.95, '2026')")
        conn.commit()

        event_bus.publish(
            event_type="DecisionGenerated", entity_type="student", entity_id="alice@test.com",
            producer="cdo_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        recs = student_twin.get_student_recommendations("alice@test.com")
        self.assertGreater(len(recs), 0)
        rec_id = recs[0]["id"]
        
        # Cycle lifecycle
        for status in ("VIEWED", "STARTED", "COMPLETED"):
            recommendations.update_recommendation_status(rec_id, status)
        cur.execute("SELECT status FROM student_recommendation_history WHERE id = ?", (rec_id,))
        self.assertEqual(cur.fetchone()["status"], "COMPLETED")

    # 8. Idempotency
    def test_idempotency(self):
        calls = []
        def handler(event_data, is_replay=False, replay_mode="SAFE"):
            calls.append(event_data)

        event_dispatcher.register_in_memory_handler("student_twin_idem", "MemoryUpdated", "v1.0", handler)
        event_bus.subscribe("student_twin_idem", "MemoryUpdated", "v1.0", "in_memory_handler")

        ev_id = event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        self.assertEqual(len(calls), 1)
        # Re-dispatch should be filtered
        event_bus.dispatch(ev_id, "student_twin_idem", "in_memory_handler", calls[0])
        self.assertEqual(len(calls), 1)

    # 9. Projection Version Check
    def test_projection_version(self):
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        cur = conn.cursor()
        cur.execute("SELECT projection_version FROM student_profile_projection WHERE student_email = 'alice@test.com'")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["projection_version"], "v1.0")

    # 10. Cognitive Trends
    def test_cognitive_trends(self):
        cur = conn.cursor()
        cur.execute("INSERT INTO student_cognitive_load_state (student_email, rolling_ccli, alert_status) VALUES ('alice@test.com', 0.85, 'fatigued')")
        cur.execute("INSERT INTO student_attention_state (student_email, focus_state) VALUES ('alice@test.com', 'fatigued')")
        conn.commit()

        event_bus.publish(
            event_type="CCLIUpdated", entity_type="student", entity_id="alice@test.com",
            producer="ccli_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )
        cur.execute("SELECT metric_value FROM student_trend_projection WHERE student_email = 'alice@test.com' AND metric_name = 'CCLI'")
        rows = cur.fetchall()
        self.assertGreater(len(rows), 0)
        self.assertAlmostEqual(rows[0]["metric_value"], 0.85, places=2)

    # 11. Projection Checksum Validation
    def test_projection_checksum_validation(self):
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        result = student_twin.rebuild_projections()
        self.assertIn("projection_checksum", result)
        checksum1 = result["projection_checksum"]

        result2 = student_twin.rebuild_projections()
        checksum2 = result2["projection_checksum"]
        # Both rebuilds should produce consistent checksums
        self.assertEqual(checksum1, checksum2)

    # 12. Achievement Generation
    def test_achievement_generation(self):
        # Insert >100 total_attempts and concept mastered
        cur = conn.cursor()
        cur.execute("INSERT INTO student_progress_projection (student_email, streak_count, total_attempts) VALUES ('alice@test.com', 6, 99)")
        conn.commit()

        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        cur.execute("SELECT achievement_type FROM student_achievements WHERE student_email = 'alice@test.com'")
        ach = [r["achievement_type"] for r in cur.fetchall()]
        # algebra is Stable (mastered), so should count > 0 and trigger concept mastered achievement
        self.assertTrue(any("mastered" in a or "solved" in a or "streak" in a for a in ach))

    # 13. Trend History Recording
    def test_trend_history_recording(self):
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM student_trend_projection WHERE student_email = 'alice@test.com'")
        cnt = cur.fetchone()["cnt"]
        self.assertGreater(cnt, 0)

    # 14. Recommendation Expiry
    def test_recommendation_expiry(self):
        cur = conn.cursor()
        rec_id = "rec-exp-456"
        cur.execute("""
            INSERT INTO student_recommendation_history (
                id, student_email, recommendation, priority_score, confidence,
                evidence_snapshot_json, status, generated_at
            ) VALUES (?, 'alice@test.com', 'Practice algebra', 0.9, 0.85, '{}', 'PENDING', '2026')
        """, (rec_id,))
        conn.commit()
        
        recommendations.update_recommendation_status(rec_id, "EXPIRED")
        cur.execute("SELECT status FROM student_recommendation_history WHERE id = ?", (rec_id,))
        self.assertEqual(cur.fetchone()["status"], "EXPIRED")

    # 15. End-to-End Projection Rebuild Consistency
    def test_end_to_end_rebuild(self):
        cur = conn.cursor()
        cur.execute("INSERT INTO student_cognitive_load_state (student_email, rolling_ccli, alert_status) VALUES ('alice@test.com', 0.7, 'normal')")
        cur.execute("INSERT INTO student_attention_state (student_email, focus_state) VALUES ('alice@test.com', 'optimal')")
        conn.commit()
        
        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.7.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        
        # Record state before rebuild
        cur.execute("SELECT cognitive_health_score FROM student_profile_projection WHERE student_email = 'alice@test.com'")
        pre_row = cur.fetchone()
        pre_score = pre_row["cognitive_health_score"] if pre_row else None
        
        result = student_twin.rebuild_projections()
        self.assertEqual(result["status"], "success")
        
        cur.execute("SELECT cognitive_health_score FROM student_profile_projection WHERE student_email = 'alice@test.com'")
        post_row = cur.fetchone()
        post_score = post_row["cognitive_health_score"] if post_row else None
        
        if pre_score is not None and post_score is not None:
            self.assertAlmostEqual(pre_score, post_score, places=2)


if __name__ == '__main__':
    unittest.main()
