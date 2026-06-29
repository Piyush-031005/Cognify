"""
tests/test_research_analytics_twin.py
Week 22 — Research & Analytics Twin (RAT) integration tests.
15 tests validating the learning science metrics, data isolation, and event bus handlers.
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

import research_analytics_twin
import research_analytics_twin.decay as decay
import research_analytics_twin.misconceptions as misconceptions
import research_analytics_twin.interventions as interventions
import research_analytics_twin.discrimination as discrimination
import research_analytics_twin.classroom_speed as classroom_speed
import research_analytics_twin.load_correlation as load_correlation


def setup_test_db():
    cur = conn.cursor()
    
    # Org/Rooms tables
    cur.execute("CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY, room_code TEXT UNIQUE, teacher_email TEXT, subject TEXT, created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS room_students (id INTEGER PRIMARY KEY, room_code TEXT, student_email TEXT, joined_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, role TEXT, email TEXT UNIQUE)")

    # Core engine tables
    cur.execute("CREATE TABLE IF NOT EXISTS concept_memory (student_email TEXT, concept_id TEXT, memory_state TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS memory_state_transitions (id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT, concept_id TEXT, old_state TEXT, new_state TEXT, timestamp TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS cognitive_load_events (event_id TEXT PRIMARY KEY, student_email TEXT, composite_load REAL, timestamp TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS responses (id INTEGER PRIMARY KEY, question_id INTEGER, student_email TEXT, correct INTEGER, created_at TEXT)")

    # Misconception tables
    cur.execute("CREATE TABLE IF NOT EXISTS misconception_clusters (cluster_id TEXT PRIMARY KEY, misconception_name TEXT, concept_id TEXT, cluster_confidence REAL)")
    cur.execute("CREATE TABLE IF NOT EXISTS misconception_evidence (id TEXT PRIMARY KEY, cluster_id TEXT, wrong_answer_count INTEGER, student_count INTEGER)")

    # Other Twins' projections (Needed for analytics)
    cur.execute("CREATE TABLE IF NOT EXISTS student_profile_projection (student_email TEXT PRIMARY KEY, cognitive_health_score REAL DEFAULT 1.0)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_progress_projection (student_email TEXT PRIMARY KEY, total_attempts INTEGER DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_recommendation_history (id TEXT PRIMARY KEY, student_email TEXT, recommendation TEXT, status TEXT, generated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_trend_projection (student_email TEXT, metric_name TEXT, metric_value REAL, recorded_at TEXT)")

    # Event tables
    cur.execute("CREATE TABLE IF NOT EXISTS event_store (event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, entity_type TEXT, entity_id TEXT, entity_sequence INTEGER NOT NULL, producer TEXT, producer_version TEXT, schema_version TEXT, metadata_json TEXT, payload_json TEXT, created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS event_subscriptions (consumer_name TEXT, event_type TEXT, schema_version TEXT, handler TEXT, enabled INTEGER DEFAULT 1, PRIMARY KEY (consumer_name, event_type, schema_version))")
    cur.execute("CREATE TABLE IF NOT EXISTS processed_events (event_id TEXT, consumer_name TEXT, processed_at TEXT, PRIMARY KEY (event_id, consumer_name))")
    cur.execute("CREATE TABLE IF NOT EXISTS dead_letter_events (event_id TEXT, consumer_name TEXT, error_message TEXT, retry_count INTEGER, failed_at TEXT, payload_json TEXT, PRIMARY KEY (event_id, consumer_name))")
    cur.execute("CREATE TABLE IF NOT EXISTS event_replay_runs (replay_id TEXT PRIMARY KEY, consumer_name TEXT, from_timestamp TEXT, to_timestamp TEXT, events_processed INTEGER, started_at TEXT, completed_at TEXT, status TEXT, mode TEXT)")

    # Research & Analytics Twin tables
    cur.execute("CREATE TABLE IF NOT EXISTS research_concept_decay (concept_id TEXT PRIMARY KEY, decay_count INTEGER DEFAULT 0, avg_decay_time_days REAL DEFAULT 0.0, total_students INTEGER DEFAULT 0, updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS research_misconception_frequency (cluster_id TEXT PRIMARY KEY, misconception_name TEXT NOT NULL, concept_id TEXT, occurrence_count INTEGER DEFAULT 0, student_impact_count INTEGER DEFAULT 0, updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS research_intervention_effectiveness (recommendation_type TEXT PRIMARY KEY, total_generated INTEGER DEFAULT 0, total_completed INTEGER DEFAULT 0, total_successful INTEGER DEFAULT 0, success_rate REAL DEFAULT 0.0, updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS research_question_discrimination (question_id INTEGER PRIMARY KEY, discrimination_index REAL DEFAULT 0.0, total_attempts INTEGER DEFAULT 0, correct_rate REAL DEFAULT 0.0, updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS research_classroom_speed (room_code TEXT PRIMARY KEY, initial_health REAL DEFAULT 0.0, current_health REAL DEFAULT 0.0, improvement_rate REAL DEFAULT 0.0, updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS research_load_decay_correlation (metric_name TEXT PRIMARY KEY, average_value REAL DEFAULT 0.0, sample_size INTEGER DEFAULT 0, updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS research_projection_metadata (projection_version TEXT PRIMARY KEY, checksum TEXT NOT NULL, rebuilt_at TEXT NOT NULL)")
    conn.commit()


class TestResearchAnalyticsTwin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_db()

    def setUp(self):
        cur = conn.cursor()
        for t in [
            "rooms", "room_students", "users", "concept_memory", "memory_state_transitions",
            "cognitive_load_events", "responses", "misconception_clusters", "misconception_evidence",
            "student_profile_projection", "student_progress_projection", "student_recommendation_history",
            "student_trend_projection",
            "event_store", "event_subscriptions", "processed_events", "dead_letter_events",
            "event_replay_runs", "research_concept_decay", "research_misconception_frequency",
            "research_intervention_effectiveness", "research_question_discrimination",
            "research_classroom_speed", "research_load_decay_correlation", "research_projection_metadata"
        ]:
            cur.execute(f"DELETE FROM {t}")
        conn.commit()

        # Seed initial datasets
        cur.execute("INSERT INTO users (email, name, role) VALUES ('s1@test.com', 'Alice', 'student')")
        cur.execute("INSERT INTO users (email, name, role) VALUES ('s2@test.com', 'Bob', 'student')")
        cur.execute("INSERT INTO rooms (room_code, teacher_email, subject, created_at) VALUES ('R202', 't1@test.com', 'math', '2026-06-29')")
        cur.execute("INSERT INTO room_students (room_code, student_email) VALUES ('R202', 's1@test.com')")
        cur.execute("INSERT INTO room_students (room_code, student_email) VALUES ('R202', 's2@test.com')")

        # Projections
        cur.execute("INSERT INTO student_profile_projection (student_email, cognitive_health_score) VALUES ('s1@test.com', 0.85)")
        cur.execute("INSERT INTO student_profile_projection (student_email, cognitive_health_score) VALUES ('s2@test.com', 0.45)")
        cur.execute("INSERT INTO student_progress_projection (student_email, total_attempts) VALUES ('s1@test.com', 10)")
        cur.execute("INSERT INTO student_progress_projection (student_email, total_attempts) VALUES ('s2@test.com', 5)")

        # Transitions
        t0 = "2026-06-29T10:00:00"
        t1 = "2026-06-29T12:00:00" # 2 hours stable before decay (0.083 days)
        cur.execute("INSERT INTO memory_state_transitions (student_email, concept_id, old_state, new_state, timestamp) VALUES ('s1@test.com', 'algebra', 'Learning', 'Stable', ?)", (t0,))
        cur.execute("INSERT INTO memory_state_transitions (student_email, concept_id, old_state, new_state, timestamp) VALUES ('s1@test.com', 'algebra', 'Stable', 'Forgetting', ?)", (t1,))

        # Misconceptions
        cur.execute("INSERT INTO misconception_clusters (cluster_id, misconception_name, concept_id) VALUES ('m1', 'NegSigns', 'algebra')")
        cur.execute("INSERT INTO misconception_evidence (id, cluster_id, wrong_answer_count, student_count) VALUES ('e1', 'm1', 12, 4)")

        # Recommendations
        cur.execute("INSERT INTO student_recommendation_history (id, student_email, recommendation, status, generated_at) VALUES ('rec1', 's1@test.com', 'Practice algebra questions', 'COMPLETED', ?)", (t0,))
        
        # Responses for Discrimination Index
        cur.execute("INSERT INTO responses (question_id, student_email, correct, created_at) VALUES (101, 's1@test.com', 1, ?)", (t0,)) # High Health (Correct)
        cur.execute("INSERT INTO responses (question_id, student_email, correct, created_at) VALUES (101, 's2@test.com', 0, ?)", (t0,)) # Low Health (Incorrect)

        # Cognitive Load
        cur.execute("INSERT INTO cognitive_load_events (event_id, student_email, composite_load, timestamp) VALUES ('cl1', 's1@test.com', 0.65, ?)", (t0,))

        conn.commit()

        event_dispatcher.clear_in_memory_handlers()
        event_dispatcher.register_in_memory_handler("research_analytics_twin", "MemoryUpdated", "v1.0", research_analytics_twin.handle_memory_updated)
        event_dispatcher.register_in_memory_handler("research_analytics_twin", "DecisionGenerated", "v1.0", research_analytics_twin.handle_decision_generated)

        event_bus.subscribe("research_analytics_twin", "MemoryUpdated", "v1.0", "in_memory_handler")
        event_bus.subscribe("research_analytics_twin", "DecisionGenerated", "v1.0", "in_memory_handler")

    # 1. Concept decay speeds calculation logic
    def test_concept_decay(self):
        decay.recompute_concept_decay()
        res = research_analytics_twin.get_concept_decay()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["concept_id"], "algebra")
        self.assertEqual(res[0]["decay_count"], 1)
        self.assertAlmostEqual(res[0]["avg_decay_time_days"], 0.083, places=3)

    # 2. Misconception occurrences and impact aggregations
    def test_misconception_aggregations(self):
        misconceptions.recompute_misconception_frequency()
        res = research_analytics_twin.get_misconception_frequency()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["cluster_id"], "m1")
        self.assertEqual(res[0]["occurrence_count"], 12)
        self.assertEqual(res[0]["student_impact_count"], 4)

    # 3. Intervention success rates evaluation
    def test_intervention_success_rate(self):
        # We have a recommendation generated at t0 for s1@test.com. We also have a positive state transition to Stable for s1@test.com at t0.
        interventions.recompute_intervention_effectiveness()
        res = research_analytics_twin.get_intervention_effectiveness()
        # Find Practice Exercises category
        pe = next(x for x in res if x["recommendation_type"] == "Practice Exercises")
        self.assertEqual(pe["total_generated"], 1)
        self.assertEqual(pe["total_completed"], 1)
        self.assertEqual(pe["total_successful"], 1)
        self.assertAlmostEqual(pe["success_rate"], 1.0)

    # 4. Item discrimination index
    def test_item_discrimination(self):
        discrimination.recompute_question_discrimination()
        res = research_analytics_twin.get_question_discrimination()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["question_id"], 101)
        self.assertEqual(res[0]["total_attempts"], 2)
        self.assertAlmostEqual(res[0]["correct_rate"], 0.5)
        # s1 (High health: 0.85) is correct. s2 (Low health: 0.45) is incorrect. D = 1.0 - 0.0 = 1.0
        self.assertAlmostEqual(res[0]["discrimination_index"], 1.0)

    # 5. Classroom growth speed rankings
    def test_classroom_speed(self):
        # Earliest recorded health score per student is retrieved from student_trend_projection
        # Let's seed student trend projection records
        cur = conn.cursor()
        cur.execute("INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at) VALUES ('s1@test.com', 'Health Score', 0.60, '2026-06-29T09:00:00')")
        cur.execute("INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at) VALUES ('s2@test.com', 'Health Score', 0.40, '2026-06-29T09:00:00')")
        conn.commit()

        classroom_speed.recompute_classroom_speed()
        res = research_analytics_twin.get_classroom_speed()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["room_code"], "R202")
        # Initial health = (0.60 + 0.40)/2 = 0.50. Current health = (0.85 + 0.45)/2 = 0.65. Improvement = 0.15
        self.assertAlmostEqual(res[0]["initial_health"], 0.50)
        self.assertAlmostEqual(res[0]["current_health"], 0.65)
        self.assertAlmostEqual(res[0]["improvement_rate"], 0.15)

    # 6. Load-decay correlation averages
    def test_load_decay_correlation(self):
        # We have a decay at t1. cl1 load event is at t0 (within 24h prior window)
        load_correlation.recompute_load_decay_correlation()
        res = research_analytics_twin.get_load_decay_correlation()
        # Should have Load Prior to Decay (24h) and Baseline Cognitive Load
        pd = next(x for x in res if x["metric_name"] == "Load Prior to Decay (24h)")
        self.assertAlmostEqual(pd["average_value"], 0.65)
        self.assertEqual(pd["sample_size"], 1)

    # 7. Rebuild checksum consistency
    def test_rebuild_checksum(self):
        decay.recompute_concept_decay()
        r1 = research_analytics_twin.rebuild_projections()
        r2 = research_analytics_twin.rebuild_projections()
        self.assertEqual(r1["projection_checksum"], r2["projection_checksum"])

    # 8. CQRS isolation (raw engine tables never queried at API read time)
    def test_cqrs_isolation(self):
        decay.recompute_concept_decay()
        # Drop raw memory_state_transitions
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS memory_state_transitions")
        conn.commit()
        try:
            res = research_analytics_twin.get_concept_decay()
            self.assertEqual(len(res), 1)
        finally:
            cur.execute("CREATE TABLE IF NOT EXISTS memory_state_transitions (id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT, concept_id TEXT, old_state TEXT, new_state TEXT, timestamp TEXT)")
            conn.commit()

    # 9. CEB memory updated triggers recalculations
    def test_ceb_memory_updated_trigger(self):
        # Add another transition
        t2 = "2026-06-29T14:00:00"
        cur = conn.cursor()
        cur.execute("INSERT INTO memory_state_transitions (student_email, concept_id, old_state, new_state, timestamp) VALUES ('s2@test.com', 'calculus', 'Stable', 'Forgetting', ?)", (t2,))
        conn.commit()

        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="s2@test.com",
            producer="memory_engine", producer_version="v2.8.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "calculus"}
        )
        res = research_analytics_twin.get_concept_decay()
        # Calculus should be present now
        concepts = [x["concept_id"] for x in res]
        self.assertIn("calculus", concepts)

    # 10. CEB decision generated triggers recalculations
    def test_ceb_decision_trigger(self):
        # Add another misconception
        cur = conn.cursor()
        cur.execute("INSERT INTO misconception_clusters (cluster_id, misconception_name, concept_id) VALUES ('m2', 'CalcError', 'calculus')")
        cur.execute("INSERT INTO misconception_evidence (id, cluster_id, wrong_answer_count, student_count) VALUES ('e2', 'm2', 5, 2)")
        conn.commit()

        event_bus.publish(
            event_type="DecisionGenerated", entity_type="student", entity_id="s1@test.com",
            producer="cdo_engine", producer_version="v2.8.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )
        res = research_analytics_twin.get_misconception_frequency()
        ids = [x["cluster_id"] for x in res]
        self.assertIn("m2", ids)

    # 11. E2E Concept Decay route returns list
    def test_get_concept_decay_list(self):
        decay.recompute_concept_decay()
        res = research_analytics_twin.get_concept_decay()
        self.assertIsInstance(res, list)

    # 12. E2E Misconceptions route returns list
    def test_get_misconceptions_list(self):
        misconceptions.recompute_misconception_frequency()
        res = research_analytics_twin.get_misconception_frequency()
        self.assertIsInstance(res, list)

    # 13. E2E Interventions route returns list
    def test_get_interventions_list(self):
        interventions.recompute_intervention_effectiveness()
        res = research_analytics_twin.get_intervention_effectiveness()
        self.assertIsInstance(res, list)

    # 14. E2E Discrimination route returns list
    def test_get_discrimination_list(self):
        discrimination.recompute_question_discrimination()
        res = research_analytics_twin.get_question_discrimination()
        self.assertIsInstance(res, list)

    # 15. E2E Classroom Speed route returns list
    def test_get_classroom_speed_list(self):
        # Seed student trend projection records
        cur = conn.cursor()
        cur.execute("INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at) VALUES ('s1@test.com', 'Health Score', 0.60, '2026-06-29T09:00:00')")
        cur.execute("INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at) VALUES ('s2@test.com', 'Health Score', 0.40, '2026-06-29T09:00:00')")
        conn.commit()

        classroom_speed.recompute_classroom_speed()
        res = research_analytics_twin.get_classroom_speed()
        self.assertIsInstance(res, list)


if __name__ == '__main__':
    unittest.main()
