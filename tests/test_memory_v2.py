"""
tests/test_memory_v2.py
Week 8 – Educational Memory v2.0 Integration Test Suite

Uses the live cognify.db with unique per-test emails to ensure isolation.
No DB patching — consistent with every other test suite in Cognify.

Tests:
  1.  DB migration idempotency (memory_config, memory_events, concept_memory,
      memory_state_transitions, review_schedule, memory_alerts)
  2.  memory_config seeded with defaults
  3.  record_memory_event appends to memory_events (append-only)
  4.  Source module stored in event
  5.  Algorithm version stored in event
  6.  Multiple events all appended
  7.  State machine: Unknown → Learning on first event
  8.  State transitions are logged
  9.  Failure moves concept toward At Risk
  10. Recovery after Forgotten state
  11. Retrieval strength in valid range [0, 1]
  12. Strength increases on success
  13. Predictions 7/14/30 days present in derive_current_state
  14. Next review date populated
  15. Deterministic replay (Rule 11): same events → same final state
  16. Replay event log is chronologically ordered
  17. Review schedule created after projection
  18. Priority score in valid range [0, 1]
  19. Alert raised for At Risk / Forgotten concept
  20. Config is not hardcoded (read from memory_config table)
  21. Config version present
  22. Full student profile structure correct
  23. Full profile bucketing places concept in correct bucket
  24. GET /memory/health returns 200 + engine_version
  25. GET /memory/statistics returns 200 + total_memory_events
  26. GET /memory/student/<student> returns success
  27. GET /memory/concept/<student>/<concept> returns explainability fields
  28. GET /memory/review_queue/<student> returns prioritised list
  29. GET /memory/replay/<student>/<concept> returns events + transitions ordered
  30. POST /memory/update records event + returns projection
  31. POST /memory/update with missing fields returns 400
  32. POST /memory/review_complete marks schedule completed
  33. GET /memory/concept for nonexistent concept returns 404
"""

import sys
import os
import json
import time
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import get_conn, init_db, upgrade_database_schema
import memory_engine


def setUpModule():
    """Ensure all Week 8 memory v2.0 tables exist before any test runs."""
    upgrade_database_schema()


def _uid():
    """Generate a unique student email per test invocation."""
    return f"mem_v2_test_{int(time.time() * 1000000)}@cognify.test"


# ─────────────────────────────────────────────
# 1. DB SCHEMA
# ─────────────────────────────────────────────

class TestDatabaseSchema(unittest.TestCase):

    def test_migration_idempotent(self):
        """Running init_db a second time must not raise or corrupt data."""
        try:
            init_db()
        except Exception as e:
            self.fail(f"init_db raised on second call: {e}")

    def test_memory_tables_exist(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing = {r["name"] for r in cur.fetchall()}
        conn.close()
        required = {"memory_config", "memory_events", "concept_memory",
                    "memory_state_transitions", "review_schedule", "memory_alerts"}
        for t in required:
            self.assertIn(t, existing, f"Table '{t}' missing from schema")

    def test_memory_config_seeded(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM memory_config")
        count = cur.fetchone()["c"]
        conn.close()
        self.assertGreaterEqual(count, 12)

    def test_required_config_keys(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT key FROM memory_config")
        keys = {r["key"] for r in cur.fetchall()}
        conn.close()
        required = {
            "DEFAULT_DECAY_RATE", "DEFAULT_INITIAL_STRENGTH", "REINFORCE_BOOST",
            "FAILURE_PENALTY", "FORGETTING_THRESHOLD", "WEIGHT_MEMORY_RISK",
            "WEIGHT_MISCONCEPTION_SEVERITY", "WEIGHT_PREREQUISITE_IMPORTANCE",
            "WEIGHT_TEACHER_PRIORITY", "WEIGHT_EXAM_WEIGHT"
        }
        for k in required:
            self.assertIn(k, keys, f"Config key '{k}' not seeded")


# ─────────────────────────────────────────────
# 2. EVENT SOURCING
# ─────────────────────────────────────────────

class TestEventSourcing(unittest.TestCase):

    def test_record_event_appends_row(self):
        email, concept = _uid(), "algebra_basics"
        memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM memory_events WHERE student_email=? AND concept_id=?",
                    (email, concept))
        count = cur.fetchone()["c"]
        conn.close()
        self.assertEqual(count, 1)

    def test_multiple_events_all_appended(self):
        email, concept = _uid(), "algebra_multi"
        for _ in range(5):
            memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM memory_events WHERE student_email=? AND concept_id=?",
                    (email, concept))
        self.assertEqual(cur.fetchone()["c"], 5)
        conn.close()

    def test_event_stores_source_module(self):
        email, concept = _uid(), "misconception_src"
        memory_engine.record_memory_event(email, concept, "misconception_confirmed", {},
                                          source_module="misconception")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT source_module FROM memory_events WHERE student_email=? ORDER BY id DESC LIMIT 1",
                    (email,))
        self.assertEqual(cur.fetchone()["source_module"], "misconception")
        conn.close()

    def test_event_stores_algorithm_version(self):
        email, concept = _uid(), "alg_version_concept"
        memory_engine.record_memory_event(email, concept, "correct_answer", {})
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT algorithm_version FROM memory_events WHERE student_email=? ORDER BY id DESC LIMIT 1",
                    (email,))
        self.assertEqual(cur.fetchone()["algorithm_version"], memory_engine.MEMORY_MODEL_VERSION)
        conn.close()


# ─────────────────────────────────────────────
# 3. STATE MACHINE
# ─────────────────────────────────────────────

class TestStateMachine(unittest.TestCase):

    def _get_state(self, email, concept):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT memory_state FROM concept_memory WHERE student_email=? AND concept_id=?",
                    (email, concept))
        row = cur.fetchone()
        conn.close()
        return row["memory_state"] if row else None

    def test_unknown_to_learning_on_first_event(self):
        email, concept = _uid(), "quadratic"
        memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        state = self._get_state(email, concept)
        self.assertIn(state, ["Learning", "Stable", "Recovered"])

    def test_transitions_logged(self):
        email, concept = _uid(), "transitions_test"
        for _ in range(4):
            memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM memory_state_transitions WHERE student_email=? AND concept_id=?",
                    (email, concept))
        count = cur.fetchone()["c"]
        conn.close()
        self.assertGreaterEqual(count, 1)

    def test_failure_moves_toward_at_risk_or_forgotten(self):
        email, concept = _uid(), "failure_test"
        memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        for _ in range(8):
            memory_engine.record_memory_event(email, concept, "wrong_answer", {}, source_module="qqi")
        state = self._get_state(email, concept)
        self.assertIn(state, ["At Risk", "Forgotten"])

    def test_recovery_after_heavy_failures(self):
        email, concept = _uid(), "recovery_test"
        for _ in range(10):
            memory_engine.record_memory_event(email, concept, "wrong_answer", {}, source_module="qqi")
        memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        state = self._get_state(email, concept)
        # After heavy failures + one success, state should be Recovered, Learning, or still At Risk (weak)
        self.assertIn(state, ["Recovered", "Learning", "At Risk"])


# ─────────────────────────────────────────────
# 4. EBBINGHAUS DECAY
# ─────────────────────────────────────────────

class TestEbbinghausDecay(unittest.TestCase):

    def test_retrieval_strength_in_valid_range(self):
        email, concept = _uid(), "physics_kin"
        memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        result = memory_engine.derive_current_state(email, concept)
        R = result["retrieval_strength"]
        self.assertGreaterEqual(R, 0.0)
        self.assertLessEqual(R, 1.0)

    def test_storage_strength_increases_on_success(self):
        email, concept = _uid(), "chem_bonding"
        memory_engine.record_memory_event(email, concept, "wrong_answer", {}, source_module="qqi")
        s_before = memory_engine.derive_current_state(email, concept)["storage_strength"]
        memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        s_after = memory_engine.derive_current_state(email, concept)["storage_strength"]
        self.assertGreaterEqual(s_after, s_before)

    def test_predictions_present(self):
        email, concept = _uid(), "bio_mitosis"
        memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        result = memory_engine.derive_current_state(email, concept)
        self.assertIn("predictions", result)
        self.assertIn("7_days", result["predictions"])
        self.assertIn("14_days", result["predictions"])
        self.assertIn("30_days", result["predictions"])

    def test_next_review_date_populated(self):
        email, concept = _uid(), "history_ww2"
        memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT next_review_date FROM concept_memory WHERE student_email=? AND concept_id=?",
                    (email, concept))
        row = cur.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertIsNotNone(row["next_review_date"])


# ─────────────────────────────────────────────
# 5. DETERMINISTIC REPLAY (RULE 11)
# ─────────────────────────────────────────────

class TestDeterministicReplay(unittest.TestCase):

    def test_replay_is_deterministic(self):
        """Identical event sequence must produce identical concept_memory state (Rule 11)."""
        email, concept = _uid(), "math_deriv"
        events = [
            ("correct_answer", "qqi"),
            ("correct_answer", "qqi"),
            ("wrong_answer", "qqi"),
            ("correct_answer", "qqi"),
        ]
        for ev_type, src in events:
            memory_engine.record_memory_event(email, concept, ev_type, {}, source_module=src)

        fixed_time = datetime.now().isoformat()
        result1 = memory_engine.project_concept_memory(email, concept, current_time=fixed_time)
        result2 = memory_engine.project_concept_memory(email, concept, current_time=fixed_time)

        self.assertEqual(result1["state"], result2["state"])
        self.assertAlmostEqual(result1["derived_S"], result2["derived_S"], places=6)
        self.assertAlmostEqual(result1["derived_R"], result2["derived_R"], places=6)

    def test_replay_event_log_ordered(self):
        email, concept = _uid(), "geo_continents"
        memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        memory_engine.record_memory_event(email, concept, "wrong_answer", {}, source_module="qqi")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp FROM memory_events
            WHERE student_email=? AND concept_id=?
            ORDER BY timestamp ASC, id ASC
        """, (email, concept))
        timestamps = [r["timestamp"] for r in cur.fetchall()]
        conn.close()
        self.assertEqual(timestamps, sorted(timestamps))


# ─────────────────────────────────────────────
# 6. REVIEW SCHEDULE & PRIORITY
# ─────────────────────────────────────────────

class TestReviewSchedule(unittest.TestCase):

    def test_review_schedule_created(self):
        email, concept = _uid(), "calc_int"
        memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM review_schedule WHERE student_email=? AND concept_id=?",
                    (email, concept))
        row = cur.fetchone()
        conn.close()
        self.assertIsNotNone(row)

    def test_priority_in_valid_range(self):
        email, concept = _uid(), "stats_reg"
        memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT priority FROM review_schedule WHERE student_email=? AND concept_id=?",
                    (email, concept))
        row = cur.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        p = row["priority"]
        self.assertGreaterEqual(p, 0.0)
        self.assertLessEqual(p, 1.0)


# ─────────────────────────────────────────────
# 7. ALERTS
# ─────────────────────────────────────────────

class TestMemoryAlerts(unittest.TestCase):

    def test_alert_raised_for_at_risk_state(self):
        email, concept = _uid(), "physics_thermo"
        for _ in range(8):
            memory_engine.record_memory_event(email, concept, "wrong_answer", {}, source_module="qqi")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM memory_alerts WHERE student_email=? AND concept_id=?",
                    (email, concept))
        alerts = cur.fetchall()
        conn.close()
        self.assertGreater(len(alerts), 0)


# ─────────────────────────────────────────────
# 8. CONFIG NOT HARDCODED
# ─────────────────────────────────────────────

class TestConfigNotHardcoded(unittest.TestCase):

    def test_config_loaded_from_db(self):
        config = memory_engine.get_memory_config()
        self.assertIn("DEFAULT_DECAY_RATE", config)
        self.assertIn("REINFORCE_BOOST", config)
        self.assertAlmostEqual(config["DEFAULT_DECAY_RATE"], 0.05)

    def test_config_version_present(self):
        config = memory_engine.get_memory_config()
        self.assertIn("config_version", config)
        self.assertEqual(config["config_version"], "v1.0")


# ─────────────────────────────────────────────
# 9. FULL STUDENT PROFILE
# ─────────────────────────────────────────────

class TestFullStudentProfile(unittest.TestCase):

    def test_profile_structure(self):
        email = _uid()
        memory_engine.record_memory_event(email, "concept_a", "correct_answer", {}, source_module="qqi")
        memory_engine.record_memory_event(email, "concept_b", "wrong_answer", {}, source_module="qqi")
        profile = memory_engine.get_full_student_memory(email)
        self.assertEqual(profile["student_email"], email)
        self.assertIn("mastered", profile)
        self.assertIn("at_risk", profile)
        self.assertIn("forgetting", profile)
        self.assertIn("active_misconceptions", profile)

    def test_profile_bucketing(self):
        email, concept = _uid(), "strong_concept"
        for _ in range(8):
            memory_engine.record_memory_event(email, concept, "correct_answer", {}, source_module="qqi")
        profile = memory_engine.get_full_student_memory(email)
        all_ids = ([c["node_id"] for c in profile["mastered"]] +
                   [c["node_id"] for c in profile["at_risk"]] +
                   [c["node_id"] for c in profile["forgetting"]])
        self.assertIn(concept, all_ids)


# ─────────────────────────────────────────────
# 10. REST API TESTS
# ─────────────────────────────────────────────

class TestRESTAPIs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import app as flask_app
        flask_app.app.config["TESTING"] = True
        cls.client = flask_app.app.test_client()
        cls.email = _uid()
        cls.concept = "api_test_algebra"
        for _ in range(3):
            memory_engine.record_memory_event(cls.email, cls.concept, "correct_answer", {},
                                              source_module="qqi")

    def test_health_returns_200(self):
        resp = self.client.get("/memory/health")
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["status"], "success")
        self.assertIn("engine_version", body)
        self.assertEqual(body["engine_version"], memory_engine.MEMORY_MODEL_VERSION)

    def test_statistics_returns_200(self):
        resp = self.client.get("/memory/statistics")
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["status"], "success")
        self.assertIn("total_memory_events", body["data"])

    def test_get_student_memory_returns_success(self):
        resp = self.client.get(f"/memory/student/{self.email}")
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["status"], "success")
        self.assertIn("data", body)

    def test_get_concept_detail_returns_explainability(self):
        resp = self.client.get(f"/memory/concept/{self.email}/{self.concept}")
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["status"], "success")
        self.assertIn("memory_explanation", body["data"])
        self.assertIn("memory_state", body["data"])

    def test_get_review_queue_returns_list(self):
        resp = self.client.get(f"/memory/review_queue/{self.email}")
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["status"], "success")
        self.assertIn("data", body)
        self.assertIn("total", body)

    def test_get_replay_log_returns_events_and_transitions(self):
        resp = self.client.get(f"/memory/replay/{self.email}/{self.concept}")
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["status"], "success")
        self.assertIn("events", body)
        self.assertIn("state_transitions", body)
        # Rule 11: chronological ordering
        ts = [ev["timestamp"] for ev in body["events"]]
        self.assertEqual(ts, sorted(ts))

    def test_post_memory_update_records_event(self):
        resp = self.client.post(
            "/memory/update",
            json={
                "student_email": self.email,
                "concept_id": self.concept,
                "event_type": "correct_answer",
                "source_module": "test_runner"
            },
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["status"], "success")
        self.assertIn("projection", body)

    def test_post_memory_update_missing_fields_returns_400(self):
        resp = self.client.post(
            "/memory/update",
            json={"student_email": self.email},
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_post_review_complete_marks_schedule_completed(self):
        resp = self.client.post(
            "/memory/review_complete",
            json={
                "student_email": self.email,
                "concept_id": self.concept,
                "outcome": "success"
            },
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["status"], "success")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT status FROM review_schedule WHERE student_email=? AND concept_id=?",
                    (self.email, self.concept))
        row = cur.fetchone()
        conn.close()
        self.assertEqual(row["status"], "completed")

    def test_get_nonexistent_concept_returns_404(self):
        resp = self.client.get(f"/memory/concept/{self.email}/DEFINITELY_NONEXISTENT_CONCEPT_XYZ")
        self.assertEqual(resp.status_code, 404)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("Educational Memory v2.0 – Integration Test Suite (Week 8)")
    print("=" * 65)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2, failfast=False)
    result = runner.run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    print(f"\n{'='*65}")
    print(f"RESULT: {passed}/{result.testsRun} tests PASSED")
    if result.failures or result.errors:
        print("STATUS: FAIL")
        sys.exit(1)
    else:
        print("STATUS: PASS")
        sys.exit(0)
