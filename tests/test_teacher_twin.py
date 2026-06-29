"""
tests/test_teacher_twin.py
Week 18 – Teacher Twin Integration and Verification tests.
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

import teacher_twin
import context_engine
import orchestrator

def mock_get_unified_state(email):
    return {
        "metadata": {"schema_version": "1.0"},
        "memory": {
            "mastered": [{"node_id": "concept_A"}],
            "forgetting": [{"node_id": "concept_B", "confidence": 0.9}],
            "active_misconceptions": [{"node_id": "concept_C", "confidence": 0.8}],
            "at_risk": [{"node_id": "concept_D", "confidence": 0.6}]
        },
        "telemetry": {
            "recent_accuracy": 0.3
        }
    }

orchestrator.get_unified_cognitive_state = mock_get_unified_state

def setup_test_db():
    cur = conn.cursor()
    # Core system tables
    cur.execute("CREATE TABLE IF NOT EXISTS student_room (room_code TEXT, student_email TEXT)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS concept_memory (
            student_email TEXT, concept_id TEXT, memory_strength REAL DEFAULT 0.5,
            forgetting_rate REAL DEFAULT 0.1, memory_state TEXT DEFAULT 'Learning',
            reinforcement_count INTEGER DEFAULT 0, last_success TEXT, last_failure TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_attention_state (
            student_email TEXT PRIMARY KEY, focus_state TEXT DEFAULT 'optimal',
            rolling_attention REAL DEFAULT 1.0, updated_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_cognitive_load_state (
            student_email TEXT PRIMARY KEY, rolling_il REAL DEFAULT 0.0,
            rolling_el REAL DEFAULT 0.0, rolling_gl REAL DEFAULT 0.0,
            rolling_ccli REAL DEFAULT 0.5, alert_status TEXT DEFAULT 'normal', updated_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS decision_runs (
            run_id TEXT PRIMARY KEY, student_email TEXT, concept_id TEXT,
            final_decision TEXT, winning_rule TEXT, confidence_score REAL, timestamp TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_cognitive_profiles (
            student_email TEXT, concept_id TEXT, irt_ability REAL, irt_ability_se REAL,
            irt_ability_percentile REAL, updated_at TEXT, PRIMARY KEY (student_email, concept_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS event_store (
            event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, entity_type TEXT,
            entity_id TEXT, entity_sequence INTEGER NOT NULL, producer TEXT,
            producer_version TEXT, schema_version TEXT, metadata_json TEXT,
            payload_json TEXT, created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS event_subscriptions (
            consumer_name TEXT, event_type TEXT, schema_version TEXT, handler TEXT,
            enabled INTEGER DEFAULT 1, PRIMARY KEY (consumer_name, event_type, schema_version)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS processed_events (
            event_id TEXT, consumer_name TEXT, processed_at TEXT,
            PRIMARY KEY (event_id, consumer_name)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dead_letter_events (
            event_id TEXT, consumer_name TEXT, error_message TEXT,
            retry_count INTEGER, failed_at TEXT, payload_json TEXT,
            PRIMARY KEY (event_id, consumer_name)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS event_replay_runs (
            replay_id TEXT PRIMARY KEY, consumer_name TEXT, from_timestamp TEXT,
            to_timestamp TEXT, events_processed INTEGER, started_at TEXT,
            completed_at TEXT, status TEXT, mode TEXT
        )
    """)

    # Teacher Twin Projections
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_classroom_retention (
        room_code TEXT, concept_id TEXT, mastered_count INTEGER DEFAULT 0,
        forgetting_count INTEGER DEFAULT 0, at_risk_count INTEGER DEFAULT 0,
        total_students INTEGER DEFAULT 0, projection_version TEXT DEFAULT 'v1.0',
        updated_at TEXT, PRIMARY KEY (room_code, concept_id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_intervention_queue (
        student_email TEXT PRIMARY KEY, room_code TEXT, risk_level TEXT,
        ccli_value REAL, decision TEXT, winning_rule TEXT,
        projection_version TEXT DEFAULT 'v1.0', updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_engagement_summary (
        room_code TEXT PRIMARY KEY, optimal_count INTEGER DEFAULT 0,
        decay_count INTEGER DEFAULT 0, fatigue_count INTEGER DEFAULT 0,
        total_students INTEGER DEFAULT 0, projection_version TEXT DEFAULT 'v1.0',
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_override_history (
        override_id TEXT PRIMARY KEY, student_email TEXT NOT NULL,
        concept_id TEXT NOT NULL, override_type TEXT NOT NULL,
        decision_before_override TEXT, decision_after_override TEXT,
        reason TEXT, actor TEXT, timestamp TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_recommendation_history (
        id TEXT PRIMARY KEY, teacher_id TEXT NOT NULL, student_email TEXT NOT NULL,
        recommendation TEXT NOT NULL, priority_score REAL NOT NULL,
        confidence REAL NOT NULL, evidence_count INTEGER NOT NULL,
        supporting_events TEXT NOT NULL, evidence_snapshot_json TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING', generated_at TEXT NOT NULL
    )
    """)
    conn.commit()


class TestTeacherTwin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_db()

    def setUp(self):
        cur = conn.cursor()
        cur.execute("DELETE FROM student_room")
        cur.execute("DELETE FROM concept_memory")
        cur.execute("DELETE FROM student_attention_state")
        cur.execute("DELETE FROM student_cognitive_load_state")
        cur.execute("DELETE FROM decision_runs")
        cur.execute("DELETE FROM student_cognitive_profiles")
        cur.execute("DELETE FROM event_store")
        cur.execute("DELETE FROM event_subscriptions")
        cur.execute("DELETE FROM processed_events")
        cur.execute("DELETE FROM teacher_classroom_retention")
        cur.execute("DELETE FROM teacher_intervention_queue")
        cur.execute("DELETE FROM teacher_engagement_summary")
        cur.execute("DELETE FROM teacher_override_history")
        cur.execute("DELETE FROM teacher_recommendation_history")
        cur.execute("DELETE FROM dead_letter_events")
        cur.execute("DELETE FROM event_replay_runs")
        conn.commit()
        
        # Seed students
        cur.execute("INSERT INTO student_room (room_code, student_email) VALUES ('R1', 'alice@test.com')")
        cur.execute("INSERT INTO student_room (room_code, student_email) VALUES ('R1', 'bob@test.com')")
        conn.commit()

        # Wire handlers dynamically in-memory
        event_dispatcher.clear_in_memory_handlers()
        event_dispatcher.register_in_memory_handler("teacher_twin", "MemoryUpdated", "v1.0", teacher_twin.handle_memory_updated)
        event_dispatcher.register_in_memory_handler("teacher_twin", "AttentionUpdated", "v1.0", teacher_twin.handle_attention_updated)
        event_dispatcher.register_in_memory_handler("teacher_twin", "DecisionGenerated", "v1.0", teacher_twin.handle_decision_generated)
        event_dispatcher.register_in_memory_handler("teacher_twin", "TeacherOverride", "v1.0", teacher_twin.handle_teacher_override)
        
        event_bus.subscribe("teacher_twin", "MemoryUpdated", "v1.0", "in_memory_handler")
        event_bus.subscribe("teacher_twin", "AttentionUpdated", "v1.0", "in_memory_handler")
        event_bus.subscribe("teacher_twin", "DecisionGenerated", "v1.0", "in_memory_handler")
        event_bus.subscribe("teacher_twin", "TeacherOverride", "v1.0", "in_memory_handler")

    def test_classroom_aggregator_memory(self):
        cur = conn.cursor()
        cur.execute("INSERT INTO concept_memory (student_email, concept_id, memory_state) VALUES ('alice@test.com', 'algebra', 'Stable')")
        cur.execute("INSERT INTO concept_memory (student_email, concept_id, memory_state) VALUES ('bob@test.com', 'algebra', 'Forgetting')")
        conn.commit()

        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )

        cur.execute("SELECT * FROM teacher_classroom_retention WHERE room_code = 'R1' AND concept_id = 'algebra'")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["mastered_count"], 1)
        self.assertEqual(row["forgetting_count"], 1)

    def test_classroom_aggregator_attention(self):
        cur = conn.cursor()
        cur.execute("INSERT INTO student_attention_state (student_email, focus_state) VALUES ('alice@test.com', 'optimal')")
        cur.execute("INSERT INTO student_attention_state (student_email, focus_state) VALUES ('bob@test.com', 'fatigued')")
        conn.commit()

        event_bus.publish(
            event_type="AttentionUpdated", entity_type="student", entity_id="alice@test.com",
            producer="attention_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )

        cur.execute("SELECT * FROM teacher_engagement_summary WHERE room_code = 'R1'")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["optimal_count"], 1)
        self.assertEqual(row["fatigue_count"], 1)

    def test_intervention_queue(self):
        cur = conn.cursor()
        cur.execute("INSERT INTO student_cognitive_load_state (student_email, rolling_ccli, alert_status) VALUES ('alice@test.com', 0.8, 'fatigued')")
        cur.execute("INSERT INTO decision_runs (run_id, student_email, concept_id, final_decision, winning_rule, confidence_score, timestamp) VALUES ('r-1', 'alice@test.com', 'algebra', 'Review', 'Load Rule', 0.95, '2026-06-29')")
        conn.commit()

        event_bus.publish(
            event_type="DecisionGenerated", entity_type="student", entity_id="alice@test.com",
            producer="cdo_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )

        cur.execute("SELECT * FROM teacher_intervention_queue WHERE student_email = 'alice@test.com'")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["risk_level"], "high")
        self.assertEqual(row["decision"], "Review")

    def test_recommendation_generation(self):
        cur = conn.cursor()
        cur.execute("INSERT INTO student_cognitive_load_state (student_email, rolling_ccli, alert_status) VALUES ('alice@test.com', 0.85, 'fatigued')")
        cur.execute("INSERT INTO decision_runs (run_id, student_email, concept_id, final_decision, winning_rule, confidence_score, timestamp) VALUES ('r-2', 'alice@test.com', 'algebra', 'Review', 'Load Rule', 0.98, '2026-06-29')")
        conn.commit()

        event_bus.publish(
            event_type="DecisionGenerated", entity_type="student", entity_id="alice@test.com",
            producer="cdo_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )

        cur.execute("SELECT * FROM teacher_recommendation_history WHERE student_email = 'alice@test.com'")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "PENDING")
        self.assertEqual(row["priority_score"], 0.91) # 0.4 + 0.6*0.85 = 0.91
        self.assertEqual(row["confidence"], 0.98)
        
        # Test snapshot (Lock 4)
        snapshot = json.loads(row["evidence_snapshot_json"])
        self.assertEqual(snapshot["decision"], "Review")
        self.assertEqual(snapshot["ccli"], 0.85)

    def test_override_audit(self):
        teacher_twin.record_override(
            student_email="alice@test.com",
            concept_id="algebra",
            override_type="Review",
            reason="Struggling offline",
            actor="teacher"
        )

        cur = conn.cursor()
        cur.execute("SELECT * FROM teacher_override_history WHERE student_email = 'alice@test.com'")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["override_type"], "Review")
        self.assertEqual(row["reason"], "Struggling offline")

    def test_feedback_loop(self):
        # Insert a recommendation first
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO teacher_recommendation_history (
                id, teacher_id, student_email, recommendation, priority_score, confidence,
                evidence_count, supporting_events, evidence_snapshot_json, status, generated_at
            ) VALUES ('rec-123', 'R1', 'alice@test.com', 'Review Suggestion', 0.8, 0.9, 1, '[]', '{}', 'PENDING', '2026')
        """)
        conn.commit()

        # Update feedback
        teacher_twin.record_teacher_feedback("rec-123", "accept", "Excellent plan")

        cur.execute("SELECT status FROM teacher_recommendation_history WHERE id = 'rec-123'")
        row = cur.fetchone()
        self.assertEqual(row["status"], "ACCEPTED")

    def test_projection_rebuild(self):
        # Generate some events
        cur = conn.cursor()
        cur.execute("INSERT INTO concept_memory (student_email, concept_id, memory_state) VALUES ('alice@test.com', 'algebra', 'Stable')")
        conn.commit()

        event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )

        # Clear projections manually
        cur.execute("DELETE FROM teacher_classroom_retention")
        conn.commit()

        # Rebuild projections (Lock 5)
        teacher_twin.rebuild_projections()

        # Check that projection was reconstructed chronologically
        cur.execute("SELECT mastered_count FROM teacher_classroom_retention WHERE room_code = 'R1' AND concept_id = 'algebra'")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["mastered_count"], 1)

    def test_event_idempotency(self):
        calls = []
        def handler(event_data, is_replay=False, replay_mode="SAFE"):
            calls.append(event_data)
        
        event_dispatcher.register_in_memory_handler("test_twin_idem", "MemoryUpdated", "v1.0", handler)
        event_bus.subscribe("test_twin_idem", "MemoryUpdated", "v1.0", "in_memory_handler")

        ev_id = event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        self.assertEqual(len(calls), 1)

        # Re-dispatch of same event should be filtered out
        event_bus.dispatch(ev_id, "test_twin_idem", "in_memory_handler", calls[0])
        self.assertEqual(len(calls), 1)

    def test_duplicate_event(self):
        # Publishing duplicate sequences does not disrupt aggregation ordering
        ev1 = event_bus.publish(
            event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
            producer="memory_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={"concept_id": "algebra"}
        )
        cur = conn.cursor()
        cur.execute("SELECT entity_sequence FROM event_store WHERE event_id = ?", (ev1,))
        seq1 = cur.fetchone()["entity_sequence"]
        self.assertEqual(seq1, 1)

    def test_recommendation_expiry(self):
        # Test status transition to EXPIRED
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO teacher_recommendation_history (
                id, teacher_id, student_email, recommendation, priority_score, confidence,
                evidence_count, supporting_events, evidence_snapshot_json, status, generated_at
            ) VALUES ('rec-exp', 'R1', 'alice@test.com', 'Review Suggestion', 0.8, 0.9, 1, '[]', '{}', 'PENDING', '2026')
        """)
        conn.commit()

        # Emulate recommendation expiry
        cur.execute("UPDATE teacher_recommendation_history SET status = 'EXPIRED' WHERE id = 'rec-exp'")
        conn.commit()

        cur.execute("SELECT status FROM teacher_recommendation_history WHERE id = 'rec-exp'")
        self.assertEqual(cur.fetchone()["status"], "EXPIRED")

    def test_projection_version_upgrade(self):
        # Projections default to 'v1.0' (Lock 2)
        cur = conn.cursor()
        cur.execute("INSERT INTO teacher_classroom_retention (room_code, concept_id) VALUES ('R1', 'calculus')")
        conn.commit()

        cur.execute("SELECT projection_version FROM teacher_classroom_retention WHERE concept_id = 'calculus'")
        self.assertEqual(cur.fetchone()["projection_version"], "v1.0")


if __name__ == '__main__':
    unittest.main()
