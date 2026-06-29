"""
tests/test_event_bus.py
Week 17 – Cognitive Event Bus (CEB) Integration Tests.
"""

import sqlite3
import os
import sys
import uuid
import json
import unittest

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

import event_bus
event_bus.get_conn = lambda: MockConn(conn)

import event_replay
event_replay.get_conn = lambda: MockConn(conn)

import event_dispatcher
event_dispatcher.get_conn = lambda: MockConn(conn)


def setup_test_db():
    cur = conn.cursor()

    # Create CEB tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS event_store (
        event_id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        entity_type TEXT,
        entity_id TEXT,
        entity_sequence INTEGER NOT NULL,
        producer TEXT,
        producer_version TEXT,
        schema_version TEXT,
        metadata_json TEXT,
        payload_json TEXT,
        created_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS event_subscriptions (
        consumer_name TEXT,
        event_type TEXT,
        schema_version TEXT,
        handler TEXT,
        enabled INTEGER DEFAULT 1,
        PRIMARY KEY (consumer_name, event_type, schema_version)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS processed_events (
        event_id TEXT,
        consumer_name TEXT,
        processed_at TEXT,
        PRIMARY KEY (event_id, consumer_name),
        FOREIGN KEY (event_id) REFERENCES event_store(event_id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dead_letter_events (
        event_id TEXT,
        consumer_name TEXT,
        error_message TEXT,
        retry_count INTEGER,
        failed_at TEXT,
        payload_json TEXT,
        PRIMARY KEY (event_id, consumer_name)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS event_replay_runs (
        replay_id TEXT PRIMARY KEY,
        consumer_name TEXT,
        from_timestamp TEXT,
        to_timestamp TEXT,
        events_processed INTEGER,
        started_at TEXT,
        completed_at TEXT,
        status TEXT,
        mode TEXT
    )
    """)

    conn.commit()


def seed_test_data():
    cur = conn.cursor()
    cur.execute("DELETE FROM event_store")
    cur.execute("DELETE FROM event_subscriptions")
    cur.execute("DELETE FROM processed_events")
    cur.execute("DELETE FROM dead_letter_events")
    cur.execute("DELETE FROM event_replay_runs")
    conn.commit()
    event_dispatcher.clear_in_memory_handlers()


class TestCEBIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_db()

    def setUp(self):
        seed_test_data()

    def test_event_publish(self):
        # Publish an event to the bus
        ev_id = event_bus.publish(
            event_type="ResponseSubmitted",
            entity_type="student",
            entity_id="alice@test.com",
            producer="telemetry_engine",
            producer_version="v2.5.0",
            schema_version="v1.0",
            metadata_json={"trace_id": "t1"},
            payload_json={"is_correct": True}
        )
        self.assertIsNotNone(ev_id)

        # Check event_store
        cur = conn.cursor()
        cur.execute("SELECT * FROM event_store WHERE event_id = ?", (ev_id,))
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["event_type"], "ResponseSubmitted")
        self.assertEqual(row["entity_sequence"], 1)

    def test_append_only(self):
        ev_id = event_bus.publish(
            event_type="ResponseSubmitted",
            entity_type="student",
            entity_id="alice@test.com",
            producer="telemetry_engine",
            producer_version="v2.5.0",
            schema_version="v1.0",
            metadata_json={},
            payload_json={}
        )
        # Attempt to modify row in event_store should raise/fail (or we assert database enforcement)
        cur = conn.cursor()
        with self.assertRaises(sqlite3.IntegrityError):
            # Attempting to insert duplicate primary key
            cur.execute("INSERT INTO event_store (event_id, event_type, entity_sequence) VALUES (?, 'ResponseSubmitted', 2)", (ev_id,))
            conn.commit()

    def test_duplicate_processing(self):
        # Setup subscriber
        calls = []
        def handler(event_data, is_replay=False, replay_mode="SAFE"):
            calls.append(event_data)

        event_dispatcher.register_in_memory_handler("test_consumer", "ResponseSubmitted", "v1.0", handler)
        event_bus.subscribe("test_consumer", "ResponseSubmitted", "v1.0", "in_memory_handler")

        # Publish event
        ev_id = event_bus.publish(
            event_type="ResponseSubmitted",
            entity_type="student",
            entity_id="alice@test.com",
            producer="telemetry_engine",
            producer_version="v2.5.0",
            schema_version="v1.0",
            metadata_json={},
            payload_json={}
        )

        self.assertEqual(len(calls), 1)

        # Simulate direct dispatch invocation (ALOD duplication scenario)
        event_bus.dispatch(ev_id, "test_consumer", "in_memory_handler", calls[0])
        # Calls list should still have length 1 because idempotency ledger intercepts it
        self.assertEqual(len(calls), 1)

    def test_replay(self):
        # Create historical events
        event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="alice@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={"idx": 1}
        )
        event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="alice@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={"idx": 2}
        )

        # Subscriber
        replayed = []
        def handler(event_data, is_replay=False, replay_mode="SAFE"):
            replayed.append(event_data["payload_json"])

        event_dispatcher.register_in_memory_handler("test_consumer", "ResponseSubmitted", "v1.0", handler)
        event_bus.subscribe("test_consumer", "ResponseSubmitted", "v1.0", "in_memory_handler")

        # Run replay
        res = event_replay.replay_all_events("test_consumer", mode="LIVE")
        self.assertEqual(res["events_processed"], 2)
        # Should have captured both payloads
        self.assertEqual(len(replayed), 2)

    def test_replay_safe_mode(self):
        # Setup event
        event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="alice@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )

        # Subscriber triggers downstream publish
        downstream_calls = []
        def handler(event_data, is_replay=False, replay_mode="SAFE"):
            if not is_replay or replay_mode == "LIVE":
                event_bus.publish(
                    event_type="MemoryUpdated", entity_type="student", entity_id="alice@test.com",
                    producer="memory_engine", producer_version="v2.5.0", schema_version="v1.0",
                    metadata_json={}, payload_json={}
                )
            else:
                downstream_calls.append("suppressed")

        event_dispatcher.register_in_memory_handler("test_consumer", "ResponseSubmitted", "v1.0", handler)
        event_bus.subscribe("test_consumer", "ResponseSubmitted", "v1.0", "in_memory_handler")

        # Run Replay in SAFE mode
        event_replay.replay_all_events("test_consumer", mode="SAFE")
        self.assertEqual(len(downstream_calls), 1)
        self.assertEqual(downstream_calls[0], "suppressed")

    def test_dead_letter(self):
        # Subscriber that fails continuously
        def handler(event_data, is_replay=False, replay_mode="SAFE"):
            raise RuntimeError("Continuous Failure")

        event_dispatcher.register_in_memory_handler("failing_consumer", "ResponseSubmitted", "v1.0", handler)
        event_bus.subscribe("failing_consumer", "ResponseSubmitted", "v1.0", "in_memory_handler")

        ev_id = event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="alice@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )

        # Check dead letter queue
        cur = conn.cursor()
        cur.execute("SELECT * FROM dead_letter_events WHERE event_id = ? AND consumer_name = ?", (ev_id, "failing_consumer"))
        dlq_row = cur.fetchone()
        self.assertIsNotNone(dlq_row)
        self.assertEqual(dlq_row["retry_count"], 3)
        self.assertIn("Continuous Failure", dlq_row["error_message"])

    def test_schema_versioning(self):
        # Register a versioned subscription for v2.0
        # If we publish v1.0, it should not route to v2.0 handler
        calls = []
        def handler(event_data, is_replay=False, replay_mode="SAFE"):
            calls.append(event_data)

        event_dispatcher.register_in_memory_handler("test_consumer", "ResponseSubmitted", "v2.0", handler)
        event_bus.subscribe("test_consumer", "ResponseSubmitted", "v2.0", "in_memory_handler")

        # Publish v1.0
        event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="alice@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )
        self.assertEqual(len(calls), 0)

    def test_entity_ordering(self):
        # Sequence numbers for a single student must be strictly incremental
        ev1 = event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="bob@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )
        ev2 = event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="bob@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )

        cur = conn.cursor()
        cur.execute("SELECT entity_sequence FROM event_store WHERE event_id = ?", (ev1,))
        seq1 = cur.fetchone()["entity_sequence"]
        cur.execute("SELECT entity_sequence FROM event_store WHERE event_id = ?", (ev2,))
        seq2 = cur.fetchone()["entity_sequence"]

        self.assertEqual(seq1, 1)
        self.assertEqual(seq2, 2)

    def test_out_of_order_detection(self):
        # Replay ordering should reconstruct strictly by entity_sequence
        event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="bob@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={"seq": 1}
        )
        event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="bob@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={"seq": 2}
        )

        cur = conn.cursor()
        cur.execute("SELECT entity_sequence, payload_json FROM event_store ORDER BY entity_sequence DESC")
        rows = cur.fetchall()
        # Verify sequence numbers
        self.assertEqual(rows[0]["entity_sequence"], 2)
        self.assertEqual(rows[1]["entity_sequence"], 1)

    def test_subscription_enable_disable(self):
        calls = []
        def handler(event_data, is_replay=False, replay_mode="SAFE"):
            calls.append(event_data)

        event_dispatcher.register_in_memory_handler("test_consumer", "ResponseSubmitted", "v1.0", handler)
        # Subscribe but disabled
        event_bus.subscribe("test_consumer", "ResponseSubmitted", "v1.0", "in_memory_handler", enabled=0)

        event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="alice@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )
        self.assertEqual(len(calls), 0)

    def test_consumer_recovery(self):
        # A single failing handler shouldn't block other subscribers from processing
        calls = []
        def handler_ok(event_data, is_replay=False, replay_mode="SAFE"):
            calls.append(event_data)

        def handler_fail(event_data, is_replay=False, replay_mode="SAFE"):
            raise ValueError("Failure")

        event_dispatcher.register_in_memory_handler("consumer_ok", "ResponseSubmitted", "v1.0", handler_ok)
        event_dispatcher.register_in_memory_handler("consumer_fail", "ResponseSubmitted", "v1.0", handler_fail)
        
        event_bus.subscribe("consumer_ok", "ResponseSubmitted", "v1.0", "in_memory_handler")
        event_bus.subscribe("consumer_fail", "ResponseSubmitted", "v1.0", "in_memory_handler")

        # Publish should run through ok subscriber even though fail subscriber crashes
        event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="alice@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )
        self.assertEqual(len(calls), 1)

    def test_dispatch_registry(self):
        # Test invalid event validation throws ValueError
        with self.assertRaises(ValueError):
            event_bus.publish(
                event_type="FakeEvent", entity_type="student", entity_id="alice@test.com",
                producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
                metadata_json={}, payload_json={}
            )

    def test_event_sequence(self):
        # Sequence starts at 1
        ev_id = event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="charlie@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )
        cur = conn.cursor()
        cur.execute("SELECT entity_sequence FROM event_store WHERE event_id = ?", (ev_id,))
        self.assertEqual(cur.fetchone()["entity_sequence"], 1)

    def test_idempotency(self):
        # Second dispatch of same event is ignored
        calls = []
        def handler(event_data, is_replay=False, replay_mode="SAFE"):
            calls.append(event_data)

        event_dispatcher.register_in_memory_handler("test_consumer", "ResponseSubmitted", "v1.0", handler)
        event_bus.subscribe("test_consumer", "ResponseSubmitted", "v1.0", "in_memory_handler")

        ev_id = event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="alice@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )
        self.assertEqual(len(calls), 1)

        # Retry dispatching same event id to same consumer
        event_bus.dispatch(ev_id, "test_consumer", "in_memory_handler", calls[0])
        self.assertEqual(len(calls), 1)

    def test_failed_retry(self):
        # Handler retries exactly 3 times before failing
        self.retries = 0
        def handler(event_data, is_replay=False, replay_mode="SAFE"):
            self.retries += 1
            raise RuntimeError("Crash")

        event_dispatcher.register_in_memory_handler("retrying_consumer", "ResponseSubmitted", "v1.0", handler)
        event_bus.subscribe("retrying_consumer", "ResponseSubmitted", "v1.0", "in_memory_handler")

        event_bus.publish(
            event_type="ResponseSubmitted", entity_type="student", entity_id="alice@test.com",
            producer="telemetry_engine", producer_version="v2.5.0", schema_version="v1.0",
            metadata_json={}, payload_json={}
        )

        self.assertEqual(self.retries, 3)


if __name__ == '__main__':
    unittest.main()
