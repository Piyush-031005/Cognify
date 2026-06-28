"""
tests/test_context_engine_v2.py
Week 9 – Context Engine v2.0 Integration Test Suite

Uses the live database to verify contextual recommendation logic.
"""

import sys
import os
import json
import time
import unittest
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import get_conn, upgrade_database_schema
import context_engine
import memory_engine


def _uid():
    return f"ctx_v2_test_{int(time.time() * 1000000)}@cognify.test"


def setUpModule():
    """Ensure all database schema updates and config seeding are applied."""
    upgrade_database_schema()


class TestContextEngineV2(unittest.TestCase):

    def setUp(self):
        self.student = _uid()
        self.concept_a = "algebra_basics_ctx"
        self.concept_b = "quadratic_equations_ctx"
        
        # Seed student memory events so they exist in concept_memory
        memory_engine.record_memory_event(
            self.student, self.concept_a, "correct_answer", {}, source_module="qqi"
        )
        memory_engine.record_memory_event(
            self.student, self.concept_b, "wrong_answer", {}, source_module="qqi"
        )
        
        # Build prerequisite link in kg_edges: A is prerequisite of B
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT OR IGNORE INTO kg_edges (source_id, target_id, relation_type, discovery_method, status)
                VALUES (?, ?, 'prerequisite_of', 'human', 'production')
            """, (self.concept_a, self.concept_b))
            conn.commit()
        except Exception as e:
            pass
        conn.close()

    def test_config_retrieval(self):
        """Verify weights and multipliers are successfully retrieved from DB config."""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM context_recommendations_config")
        count = cur.fetchone()["c"]
        conn.close()
        self.assertGreaterEqual(count, 10)

    def test_context_quality_fallback(self):
        """Verify quality is FALLBACK and all 4 missing signals are reported when no overrides are passed."""
        res = context_engine.generate_contextual_recommendations(self.student)
        self.assertEqual(res["context_quality"], "FALLBACK")
        self.assertEqual(res["confidence"], 0.5)
        self.assertEqual(len(res["missing_telemetry_signals"]), 4)
        self.assertIn("device_type", res["missing_telemetry_signals"])
        self.assertIn("network_quality", res["missing_telemetry_signals"])

    def test_context_quality_full(self):
        """Verify quality is FULL and missing signals list is empty when all overrides are provided."""
        overrides = {
            "device_type": "mobile",
            "network_quality": "poor",
            "session_start_hour": 14,
            "class_size": 30
        }
        res = context_engine.generate_contextual_recommendations(self.student, overrides)
        self.assertEqual(res["context_quality"], "FULL")
        self.assertEqual(res["confidence"], 1.0)
        self.assertEqual(len(res["missing_telemetry_signals"]), 0)

    def test_context_quality_partial(self):
        """Verify quality is PARTIAL when only some overrides are passed."""
        overrides = {
            "device_type": "tablet"
        }
        res = context_engine.generate_contextual_recommendations(self.student, overrides)
        self.assertEqual(res["context_quality"], "PARTIAL")
        self.assertGreater(res["confidence"], 0.5)
        self.assertLess(res["confidence"], 1.0)
        self.assertIn("network_quality", res["missing_telemetry_signals"])

    def test_eligibility_prerequisite_blocking(self):
        """Verify that if a prerequisite is Forgotten, standard reviews and practice are blocked."""
        # 1. Force prerequisite concept A to 'Forgotten' state by injecting many consecutive failures
        for _ in range(30):
            memory_engine.record_memory_event(
                self.student, self.concept_a, "wrong_answer", {}, source_module="qqi"
            )
            
        # Get memory status of A to confirm from DB
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT memory_state FROM concept_memory WHERE student_email=? AND concept_id=?", (self.student, self.concept_a))
        row = cur.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row["memory_state"], "Forgotten")

        
        # 2. Generate recommendations and verify Concept B (quadratic_equations) is blocked
        res = context_engine.generate_contextual_recommendations(self.student)
        
        # Algebra A should be in the generated active recommendations queue
        active_targets = [r["target"] for r in res["recommendations"]]
        self.assertIn(self.concept_a, active_targets)
        
        # Quadratic B should be blocked for Practice/Review
        blocked_targets = [b["target"] for b in res["blocked_candidates"]]
        self.assertIn(self.concept_b, blocked_targets)
        
        for blocked_item in res["blocked_candidates"]:
            if blocked_item["target"] == self.concept_b:
                self.assertEqual(blocked_item["status"], "blocked")
                self.assertEqual(blocked_item["conflict"], True)
                self.assertIn("prerequisite", blocked_item["reason"])

    def test_scoring_determinism(self):
        """Verify that scoring is strictly deterministic under identical context."""
        overrides = {
            "device_type": "mobile",
            "network_quality": "average",
            "session_start_hour": 10,
            "class_size": 25
        }
        res1 = context_engine.generate_contextual_recommendations(self.student, overrides)
        res2 = context_engine.generate_contextual_recommendations(self.student, overrides)
        
        self.assertEqual(len(res1["recommendations"]), len(res2["recommendations"]))
        for r1, r2 in zip(res1["recommendations"], res2["recommendations"]):
            self.assertEqual(r1["target"], r2["target"])
            self.assertEqual(r1["category"], r2["category"])
            self.assertAlmostEqual(r1["priority"], r2["priority"], places=6)

    def test_explainability_trace(self):
        """Verify recommendations include the justification, scoring breakdown, and trace string."""
        res = context_engine.generate_contextual_recommendations(self.student)
        self.assertGreaterEqual(len(res["recommendations"]), 1)
        r = res["recommendations"][0]
        
        self.assertIn("reason", r)
        self.assertIn("scoring_breakdown", r)
        self.assertIn("recommendation_trace", r)
        
        breakdown = r["scoring_breakdown"]
        self.assertIn("base_components", breakdown)
        self.assertIn("multipliers", breakdown)
        self.assertIn("clamped_final", breakdown)
        
        # Assert clamping is in [0, 1] range
        self.assertGreaterEqual(breakdown["clamped_final"], 0.0)
        self.assertLessEqual(breakdown["clamped_final"], 1.0)


class TestContextRESTAPIs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import app as flask_app
        flask_app.app.config["TESTING"] = True
        cls.client = flask_app.app.test_client()
        cls.student = _uid()
        
        # Seed at least one memory event so student has concept_memory
        memory_engine.record_memory_event(
            cls.student, "physics_thermo_api", "correct_answer", {}, source_module="qqi"
        )

    def test_post_recommendations_success(self):
        resp = self.client.post(
            "/memory/recommendations",
            json={
                "student_email": self.student,
                "device_type": "mobile",
                "network_quality": "poor"
            },
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["status"], "success")
        self.assertIn("data", body)
        self.assertEqual(body["data"]["context_quality"], "PARTIAL")
        self.assertIn("session_start_hour", body["data"]["missing_telemetry_signals"])

    def test_post_recommendations_missing_fields_returns_400(self):
        resp = self.client.post(
            "/memory/recommendations",
            json={"device_type": "desktop"},
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_get_config_success(self):
        resp = self.client.get("/memory/recommendations/config")
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["status"], "success")
        self.assertGreaterEqual(len(body["data"]), 10)

    def test_post_config_updates_table(self):
        # Update WEIGHT_TEACHER_PRIORITY to 0.15
        resp = self.client.post(
            "/memory/recommendations/config",
            json={"WEIGHT_TEACHER_PRIORITY": 0.15},
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["status"], "success")
        
        # Fetch config to verify
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT value FROM context_recommendations_config WHERE key = 'WEIGHT_TEACHER_PRIORITY'")
        val = cur.fetchone()["value"]
        conn.close()
        self.assertAlmostEqual(val, 0.15)

    def test_student_memory_route_includes_recommendations(self):
        resp = self.client.get(f"/memory/student/{self.student}")
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["status"], "success")
        data = body["data"]
        self.assertIn("contextual_recommendations", data)
        self.assertIn("context_telemetry_status", data)
        self.assertEqual(data["context_telemetry_status"]["quality"], "FALLBACK")


if __name__ == "__main__":
    unittest.main()
