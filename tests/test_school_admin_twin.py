"""
tests/test_school_admin_twin.py
Week 21 — School/Admin Twin integration tests.
15 tests validating the CQRS boundaries, data isolation, re-aggregations,
safe rebuild replaying, and CEB subscriptions.
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

import school_admin_twin
import school_admin_twin.classroom as classroom
import school_admin_twin.teacher_summary as teacher_summary
import school_admin_twin.curriculum as curriculum
import school_admin_twin.risk_dashboard as risk_dashboard
import school_admin_twin.adoption as adoption
import school_admin_twin.snapshots as snapshots


def setup_test_db():
    cur = conn.cursor()
    
    # Org / Rooms tables
    cur.execute("CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY, room_code TEXT UNIQUE, teacher_email TEXT, subject TEXT, topic TEXT, subtopic TEXT, difficulty TEXT, question_mix TEXT, question_count INTEGER, created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS room_students (id INTEGER PRIMARY KEY, room_code TEXT, student_email TEXT, joined_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, email TEXT UNIQUE, password TEXT, education TEXT, learning_style TEXT, subjects TEXT, confidence REAL, role TEXT, created_at TEXT)")

    # Core engine tables
    cur.execute("CREATE TABLE IF NOT EXISTS concept_memory (student_email TEXT, concept_id TEXT, memory_strength REAL DEFAULT 0.5, memory_state TEXT DEFAULT 'Learning')")
    cur.execute("CREATE TABLE IF NOT EXISTS student_attention_state (student_email TEXT PRIMARY KEY, focus_state TEXT DEFAULT 'optimal', rolling_attention REAL DEFAULT 1.0, updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_cognitive_load_state (student_email TEXT PRIMARY KEY, rolling_ccli REAL DEFAULT 0.5, alert_status TEXT DEFAULT 'normal', updated_at TEXT)")
    
    # Event tables
    cur.execute("CREATE TABLE IF NOT EXISTS event_store (event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, entity_type TEXT, entity_id TEXT, entity_sequence INTEGER NOT NULL, producer TEXT, producer_version TEXT, schema_version TEXT, metadata_json TEXT, payload_json TEXT, created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS event_subscriptions (consumer_name TEXT, event_type TEXT, schema_version TEXT, handler TEXT, enabled INTEGER DEFAULT 1, PRIMARY KEY (consumer_name, event_type, schema_version))")
    cur.execute("CREATE TABLE IF NOT EXISTS processed_events (event_id TEXT, consumer_name TEXT, processed_at TEXT, PRIMARY KEY (event_id, consumer_name))")
    cur.execute("CREATE TABLE IF NOT EXISTS dead_letter_events (event_id TEXT, consumer_name TEXT, error_message TEXT, retry_count INTEGER, failed_at TEXT, payload_json TEXT, PRIMARY KEY (event_id, consumer_name))")
    cur.execute("CREATE TABLE IF NOT EXISTS event_replay_runs (replay_id TEXT PRIMARY KEY, consumer_name TEXT, from_timestamp TEXT, to_timestamp TEXT, events_processed INTEGER, started_at TEXT, completed_at TEXT, status TEXT, mode TEXT)")

    # Other Twins' projections (Needed for school twin aggregation)
    cur.execute("CREATE TABLE IF NOT EXISTS teacher_classroom_retention (room_code TEXT, concept_id TEXT, mastered_count INTEGER, forgetting_count INTEGER, at_risk_count INTEGER, total_students INTEGER, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT, PRIMARY KEY (room_code, concept_id))")
    cur.execute("CREATE TABLE IF NOT EXISTS teacher_engagement_summary (room_code TEXT PRIMARY KEY, optimal_count INTEGER, decay_count INTEGER, fatigue_count INTEGER, total_students INTEGER, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS teacher_intervention_queue (student_email TEXT PRIMARY KEY, room_code TEXT, risk_level TEXT, ccli_value REAL, decision TEXT, winning_rule TEXT, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS teacher_override_history (override_id TEXT PRIMARY KEY, student_email TEXT, concept_id TEXT, override_type TEXT, decision_before_override TEXT, decision_after_override TEXT, reason TEXT, actor TEXT, timestamp TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS teacher_recommendation_history (id TEXT PRIMARY KEY, teacher_id TEXT, student_email TEXT, recommendation TEXT, priority_score REAL, confidence REAL, evidence_count INTEGER, supporting_events TEXT, evidence_snapshot_json TEXT, status TEXT DEFAULT 'PENDING', generated_at TEXT)")
    
    cur.execute("CREATE TABLE IF NOT EXISTS student_profile_projection (student_email TEXT PRIMARY KEY, strengths_json TEXT, weaknesses_json TEXT, memory_health_json TEXT, cognitive_health_score REAL DEFAULT 1.0, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_progress_projection (student_email TEXT PRIMARY KEY, streak_count INTEGER DEFAULT 0, last_activity_date TEXT, completed_concepts_count INTEGER DEFAULT 0, total_attempts INTEGER DEFAULT 0, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")

    # School/Admin Twin tables
    cur.execute("CREATE TABLE IF NOT EXISTS school_org (school_id TEXT PRIMARY KEY, school_name TEXT NOT NULL, created_at TEXT NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS school_classroom_summary (room_code TEXT PRIMARY KEY, school_id TEXT NOT NULL DEFAULT 'default', teacher_email TEXT NOT NULL, subject TEXT, total_students INTEGER DEFAULT 0, avg_cognitive_health REAL DEFAULT 0.0, at_risk_count INTEGER DEFAULT 0, mastery_rate REAL DEFAULT 0.0, engagement_score REAL DEFAULT 0.0, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS school_teacher_summary (teacher_email TEXT PRIMARY KEY, school_id TEXT NOT NULL DEFAULT 'default', total_rooms INTEGER DEFAULT 0, total_students INTEGER DEFAULT 0, avg_class_health REAL DEFAULT 0.0, override_count INTEGER DEFAULT 0, intervention_count INTEGER DEFAULT 0, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS school_concept_coverage (school_id TEXT NOT NULL DEFAULT 'default', subject TEXT NOT NULL, concept_id TEXT NOT NULL, school_mastery_rate REAL DEFAULT 0.0, total_students INTEGER DEFAULT 0, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT, PRIMARY KEY (school_id, subject, concept_id))")
    cur.execute("CREATE TABLE IF NOT EXISTS school_risk_dashboard (school_id TEXT NOT NULL DEFAULT 'default', room_code TEXT NOT NULL, high_risk_count INTEGER DEFAULT 0, medium_risk_count INTEGER DEFAULT 0, low_risk_count INTEGER DEFAULT 0, total_students INTEGER DEFAULT 0, updated_at TEXT, projection_version TEXT DEFAULT 'v1.0', PRIMARY KEY (school_id, room_code))")
    cur.execute("CREATE TABLE IF NOT EXISTS school_adoption_metrics (school_id TEXT PRIMARY KEY DEFAULT 'default', total_teachers INTEGER DEFAULT 0, active_teachers INTEGER DEFAULT 0, total_students INTEGER DEFAULT 0, active_students INTEGER DEFAULT 0, total_rooms INTEGER DEFAULT 0, avg_session_health REAL DEFAULT 0.0, projection_version TEXT DEFAULT 'v1.0', updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS school_weekly_snapshot (snapshot_id TEXT PRIMARY KEY, school_id TEXT NOT NULL DEFAULT 'default', week_start_date TEXT NOT NULL, week_end_date TEXT NOT NULL, summary_json TEXT NOT NULL, is_latest INTEGER DEFAULT 1, generated_at TEXT NOT NULL, projection_version TEXT DEFAULT 'v1.0')")
    cur.execute("CREATE TABLE IF NOT EXISTS school_projection_metadata (projection_version TEXT PRIMARY KEY, checksum TEXT NOT NULL, rebuilt_at TEXT NOT NULL)")
    conn.commit()


class TestSchoolAdminTwin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_db()

    def setUp(self):
        cur = conn.cursor()
        for t in [
            "rooms", "room_students", "users", "concept_memory", "student_attention_state",
            "student_cognitive_load_state", "event_store", "event_subscriptions", "processed_events",
            "dead_letter_events", "event_replay_runs", "teacher_classroom_retention",
            "teacher_engagement_summary", "teacher_intervention_queue", "teacher_override_history",
            "teacher_recommendation_history", "student_profile_projection", "student_progress_projection",
            "school_org", "school_classroom_summary", "school_teacher_summary",
            "school_concept_coverage", "school_risk_dashboard", "school_adoption_metrics",
            "school_weekly_snapshot", "school_projection_metadata"
        ]:
            cur.execute(f"DELETE FROM {t}")
        conn.commit()

        # Seed school org
        cur.execute("INSERT INTO school_org (school_id, school_name, created_at) VALUES ('default', 'Default School', '2026-06-29')")
        
        # Seed users (teachers & students)
        cur.execute("INSERT INTO users (email, name, role) VALUES ('t1@test.com', 'Teacher One', 'teacher')")
        cur.execute("INSERT INTO users (email, name, role) VALUES ('s1@test.com', 'Student One', 'student')")
        cur.execute("INSERT INTO users (email, name, role) VALUES ('s2@test.com', 'Student Two', 'student')")
        
        # Seed room
        cur.execute("INSERT INTO rooms (room_code, teacher_email, subject, created_at) VALUES ('R101', 't1@test.com', 'math', '2026-06-29')")
        cur.execute("INSERT INTO room_students (room_code, student_email) VALUES ('R101', 's1@test.com')")
        cur.execute("INSERT INTO room_students (room_code, student_email) VALUES ('R101', 's2@test.com')")

        # Seed other twin projections
        cur.execute("INSERT INTO teacher_classroom_retention (room_code, concept_id, mastered_count, total_students) VALUES ('R101', 'algebra', 1, 2)")
        cur.execute("INSERT INTO teacher_engagement_summary (room_code, optimal_count, decay_count, fatigue_count, total_students) VALUES ('R101', 1, 1, 0, 2)")
        cur.execute("INSERT INTO teacher_intervention_queue (student_email, room_code, risk_level) VALUES ('s1@test.com', 'R101', 'high')")
        
        cur.execute("INSERT INTO student_profile_projection (student_email, cognitive_health_score, strengths_json, weaknesses_json, memory_health_json) VALUES ('s1@test.com', 0.8, '[]', '[]', '{}')")
        cur.execute("INSERT INTO student_profile_projection (student_email, cognitive_health_score, strengths_json, weaknesses_json, memory_health_json) VALUES ('s2@test.com', 0.6, '[]', '[]', '{}')")
        cur.execute("INSERT INTO student_progress_projection (student_email, streak_count, total_attempts) VALUES ('s1@test.com', 3, 15)")
        cur.execute("INSERT INTO student_progress_projection (student_email, streak_count, total_attempts) VALUES ('s2@test.com', 0, 0)")
        conn.commit()

        event_dispatcher.clear_in_memory_handlers()
        event_dispatcher.register_in_memory_handler("school_admin_twin", "MemoryUpdated", "v1.0", school_admin_twin.handle_memory_updated)
        event_dispatcher.register_in_memory_handler("school_admin_twin", "DecisionGenerated", "v1.0", school_admin_twin.handle_decision_generated)
        event_dispatcher.register_in_memory_handler("school_admin_twin", "AttentionUpdated", "v1.0", school_admin_twin.handle_attention_updated)
        event_dispatcher.register_in_memory_handler("school_admin_twin", "TeacherOverrideApplied", "v1.0", school_admin_twin.handle_teacher_override_applied)

        event_bus.subscribe("school_admin_twin", "MemoryUpdated", "v1.0", "in_memory_handler")
        event_bus.subscribe("school_admin_twin", "DecisionGenerated", "v1.0", "in_memory_handler")
        event_bus.subscribe("school_admin_twin", "AttentionUpdated", "v1.0", "in_memory_handler")
        event_bus.subscribe("school_admin_twin", "TeacherOverrideApplied", "v1.0", "in_memory_handler")

    # 1. Classroom summary populated from Teacher Twin projections
    def test_classroom_summary_population(self):
        classroom.recompute_classroom_summary("R101")
        summary = school_admin_twin.get_classroom_detail("R101")
        self.assertEqual(summary["total_students"], 2)
        self.assertAlmostEqual(summary["avg_cognitive_health"], 0.7)
        self.assertEqual(summary["at_risk_count"], 1)
        self.assertAlmostEqual(summary["mastery_rate"], 0.5)
        self.assertAlmostEqual(summary["engagement_score"], 0.8) # (1*1 + 1*0.6)/2 = 0.8

    # 2. Teacher summary aggregated correctly across rooms
    def test_teacher_summary_aggregation(self):
        classroom.recompute_classroom_summary("R101")
        teacher_summary.recompute_teacher_summary("t1@test.com")
        summary = school_admin_twin.get_teacher_detail("t1@test.com")
        self.assertEqual(summary["total_rooms"], 1)
        self.assertEqual(summary["total_students"], 2)
        self.assertAlmostEqual(summary["avg_class_health"], 0.7)

    # 3. School-wide concept coverage computed from classroom retention
    def test_curriculum_coverage(self):
        curriculum.recompute_curriculum_coverage()
        coverage = school_admin_twin.get_curriculum_coverage()
        self.assertEqual(len(coverage), 1)
        self.assertEqual(coverage[0]["concept_id"], "algebra")
        self.assertAlmostEqual(coverage[0]["school_mastery_rate"], 0.5)

    # 4. Risk dashboard counts match intervention queue
    def test_risk_dashboard(self):
        risk_dashboard.recompute_risk_dashboard("R101")
        dash = school_admin_twin.get_risk_dashboard()
        self.assertEqual(len(dash), 1)
        self.assertEqual(dash[0]["room_code"], "R101")
        self.assertEqual(dash[0]["high_risk_count"], 1)

    # 5. Adoption metrics count active vs total users correctly
    def test_adoption_metrics(self):
        adoption.recompute_adoption_metrics()
        overview = school_admin_twin.get_school_overview()
        metrics = overview["metrics"]
        self.assertEqual(metrics["total_teachers"], 1)
        self.assertEqual(metrics["active_teachers"], 1)
        self.assertEqual(metrics["total_students"], 2)
        self.assertEqual(metrics["active_students"], 1) # s1@test.com has attempts > 0

    # 6. Weekly snapshot generated on-demand
    def test_weekly_snapshot_generation(self):
        classroom.recompute_classroom_summary("R101")
        adoption.recompute_adoption_metrics()
        snap = snapshots.get_latest_weekly_snapshot()
        self.assertIsNotNone(snap)
        self.assertEqual(snap["is_latest"], True)
        self.assertEqual(snap["summary"]["total_classrooms_count"], 1)

    # 7. Weekly snapshot append-only (Decision 4)
    def test_weekly_snapshot_append_only(self):
        s1 = snapshots.generate_weekly_snapshot()
        s2 = snapshots.generate_weekly_snapshot()
        
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM school_weekly_snapshot")
        self.assertEqual(cur.fetchone()["cnt"], 2)

        cur.execute("SELECT COUNT(*) as cnt FROM school_weekly_snapshot WHERE is_latest = 1")
        self.assertEqual(cur.fetchone()["cnt"], 1)
        self.assertNotEqual(s1["snapshot_id"], s2["snapshot_id"])

    # 8. CQRS isolation: raw engine tables never read at query time (Decision 1)
    def test_cqrs_isolation(self):
        classroom.recompute_classroom_summary("R101")
        
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS concept_memory")
        cur.execute("DROP TABLE IF EXISTS student_attention_state")
        conn.commit()

        try:
            summary = school_admin_twin.get_classroom_detail("R101")
            self.assertEqual(summary["total_students"], 2)
        finally:
            cur.execute("CREATE TABLE IF NOT EXISTS concept_memory (student_email TEXT, concept_id TEXT, memory_strength REAL DEFAULT 0.5, memory_state TEXT DEFAULT 'Learning')")
            cur.execute("CREATE TABLE IF NOT EXISTS student_attention_state (student_email TEXT PRIMARY KEY, focus_state TEXT DEFAULT 'optimal', rolling_attention REAL DEFAULT 1.0, updated_at TEXT)")
            conn.commit()

    # 9. Projection-to-projection reads work correctly
    def test_projection_reads(self):
        # The classroom summary directly reads from student_profile_projection and teacher_intervention_queue
        classroom.recompute_classroom_summary("R101")
        summary = school_admin_twin.get_classroom_detail("R101")
        self.assertAlmostEqual(summary["avg_cognitive_health"], 0.7)

    # 10. Rebuild checksum consistent across sequential rebuilds (Decision 5)
    def test_rebuild_checksum(self):
        classroom.recompute_classroom_summary("R101")
        r1 = school_admin_twin.rebuild_projections()
        r2 = school_admin_twin.rebuild_projections()
        self.assertEqual(r1["projection_checksum"], r2["projection_checksum"])

    # 11. CEB MemoryUpdated triggers classroom summary update
    def test_ceb_memory_updated_trigger(self):
        # Update teacher retention
        cur = conn.cursor()
        cur.execute("UPDATE teacher_classroom_retention SET mastered_count = 2 WHERE room_code = 'R101'")
        conn.commit()

        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="s1@test.com",
            producer="memory_engine", producer_version="v2.8.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        summary = school_admin_twin.get_classroom_detail("R101")
        self.assertAlmostEqual(summary["mastery_rate"], 1.0) # 2 mastered / 2 students

    # 12. CEB DecisionGenerated triggers risk dashboard update
    def test_ceb_decision_trigger(self):
        # Add another student to risk queue
        cur = conn.cursor()
        cur.execute("INSERT INTO teacher_intervention_queue (student_email, room_code, risk_level) VALUES ('s2@test.com', 'R101', 'medium')")
        conn.commit()

        event_bus.publish(
            event_type="DecisionGenerated", entity_type="student", entity_id="s2@test.com",
            producer="cdo_engine", producer_version="v2.8.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        dash = school_admin_twin.get_risk_dashboard()
        self.assertEqual(dash[0]["medium_risk_count"], 1)

    # 13. CEB AttentionUpdated triggers engagement score update
    def test_ceb_attention_trigger(self):
        cur = conn.cursor()
        cur.execute("UPDATE teacher_engagement_summary SET optimal_count = 2, decay_count = 0 WHERE room_code = 'R101'")
        conn.commit()

        event_bus.publish(
            event_type="AttentionUpdated", entity_type="student", entity_id="s1@test.com",
            producer="attention_engine", producer_version="v2.8.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )
        summary = school_admin_twin.get_classroom_detail("R101")
        self.assertAlmostEqual(summary["engagement_score"], 1.0)

    # 14. CEB TeacherOverrideApplied increments teacher override count
    def test_ceb_override_trigger(self):
        event_bus.publish(
            event_type="TeacherOverrideApplied", entity_type="s1@test.com", entity_id="s1@test.com",
            producer="teacher_twin", producer_version="v2.8.0", schema_version="v1.0",
            metadata_json={}, payload_json={"actor": "t1@test.com"}
        )
        summary = school_admin_twin.get_teacher_detail("t1@test.com")
        self.assertEqual(summary["override_count"], 1)

    # 15. E2E school overview endpoint returns all required fields
    def test_e2e_overview(self):
        adoption.recompute_adoption_metrics()
        overview = school_admin_twin.get_school_overview()
        self.assertEqual(overview["school_id"], "default")
        self.assertEqual(overview["school_name"], "Default School")
        self.assertIn("metrics", overview)
        self.assertEqual(overview["metrics"]["total_teachers"], 1)


if __name__ == '__main__':
    unittest.main()
