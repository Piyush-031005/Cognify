"""
tests/test_production_hardening.py
Week 23 — Production Hardening Integration Tests.
"""

import os
import sys
import json
import sqlite3
import unittest
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
config.COGNIFY_BYPASS_AUTH = False  # Enable auth verification for these tests

from app import app
import auth
import permissions
import validation
import audit_logger
import backup_recovery
import swagger
import feature_flags

class TestProductionHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def setUp(self):
        # We can use the active test database for testing, but let's make sure it is clean for backups
        # Create a backup path in workspace
        self.backup_filename = "test_run_backup.db"
        self.backup_path = os.path.join(os.getcwd(), self.backup_filename)
        if os.path.exists(self.backup_path):
            try:
                os.remove(self.backup_path)
            except Exception:
                pass
        if os.path.exists(f"{self.backup_path}.meta.json"):
            try:
                os.remove(f"{self.backup_path}.meta.json")
            except Exception:
                pass

    def tearDown(self):
        if os.path.exists(self.backup_path):
            try:
                os.remove(self.backup_path)
            except Exception:
                pass
        if os.path.exists(f"{self.backup_path}.meta.json"):
            try:
                os.remove(f"{self.backup_path}.meta.json")
            except Exception:
                pass

    # 1. Token signing & verification
    def test_token_issue_and_verify(self):
        token = auth.auth_provider.issue_token("test_user@school.edu", "teacher")
        self.assertIsNotNone(token)
        
        payload = auth.auth_provider.verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["email"], "test_user@school.edu")
        self.assertEqual(payload["role"], "teacher")

    # 2. RBAC access control permissions
    def test_rbac_unauthorized_missing_token(self):
        # Request restricted route without token
        resp = self.client.get('/api/v1/admin/school/overview')
        self.assertEqual(resp.status_code, 401)
        data = json.loads(resp.data)
        self.assertEqual(data["error_code"], "UNAUTHORIZED")

    def test_rbac_forbidden_insufficient_role(self):
        # Generate token for student role
        token = auth.auth_provider.issue_token("student@school.edu", "student")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Request restricted admin route
        resp = self.client.get('/api/v1/admin/school/overview', headers=headers)
        self.assertEqual(resp.status_code, 403)
        data = json.loads(resp.data)
        self.assertEqual(data["error_code"], "FORBIDDEN")

    # 3. JSON request validation errors
    def test_json_validation_auth_routes(self):
        # Signup with missing fields
        resp = self.client.post('/signup', json={"email": "bad_req"})
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertEqual(data["error_code"], "VALIDATION_ERROR")

    # 4. Health and Readiness endpoints
    def test_health_endpoint(self):
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "healthy")

    def test_readiness_endpoint(self):
        resp = self.client.get('/readiness')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "ready")

    # 5. Metrics statistics
    def test_metrics_endpoint(self):
        resp = self.client.get('/metrics')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("dead_letter_queue_size", data)
        self.assertIn("database_size_bytes", data)

    # 6. Database online backup, restore, and validation
    def test_db_backup_and_restore(self):
        # Perform backup
        res_backup = backup_recovery.backup_database(self.backup_path)
        self.assertEqual(res_backup["status"], "success")
        self.assertTrue(os.path.exists(self.backup_path))
        self.assertTrue(os.path.exists(f"{self.backup_path}.meta.json"))

        # Verify metadata sidecar
        with open(f"{self.backup_path}.meta.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["database_version"], config.DATABASE_VERSION)
        self.assertEqual(meta["release_tag"], config.RELEASE_TAG)

        # Perform restore
        res_restore = backup_recovery.restore_database(self.backup_path)
        self.assertEqual(res_restore["status"], "success")

    # 7. Audit log mutations
    def test_audit_logging_insertion(self):
        # Manually write an audit log
        audit_logger.log_mutation(
            actor="test_admin@school.edu", role="super_admin",
            action="TEST_MUTATION", resource="test_resource",
            reason="Integration testing", request_id="req-123"
        )
        # Fetch audit logs
        logs = audit_logger.get_audit_logs(limit=5)
        self.assertTrue(len(logs) > 0)
        latest_log = logs[0]
        self.assertEqual(latest_log["actor"], "test_admin@school.edu")
        self.assertEqual(latest_log["action"], "TEST_MUTATION")
        self.assertEqual(latest_log["request_id"], "req-123")

    # 8. Feature flag check
    def test_feature_flag_is_enabled(self):
        self.assertTrue(feature_flags.is_enabled("ENABLE_SWAGGER"))
        
    # 9. Centralized permissions check
    def test_permissions_can_rebuild(self):
        self.assertTrue(permissions.can_rebuild("admin@school.edu", "super_admin"))
        self.assertFalse(permissions.can_rebuild("student@school.edu", "student"))

    # 10. Swagger Generation Check
    def test_swagger_dynamic_spec(self):
        spec = swagger.get_swagger_spec()
        self.assertEqual(spec["openapi"], "3.0.0")
        self.assertIn("/health", spec["paths"])

    # 11. Blueprint validations
    def test_assessment_blueprint_validations(self):
        # 11.1 Test invalid sum (not 100%)
        resp = self.client.post('/assessment-blueprints', json={
            "name": "Invalid Sum",
            "teacher_email": "teacher1@cognify.edu",
            "subject": "math",
            "topic": "algebra",
            "subtopic": "quadratic",
            "purpose": "practice",
            "difficulty": "medium",
            "conceptual_pct": 20,
            "application_pct": 20,
            "reasoning_pct": 20,
            "memory_pct": 20
        })
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["error_code"], "VALIDATION_ERROR")

        # 11.2 Test invalid values (< 0)
        resp = self.client.post('/assessment-blueprints', json={
            "name": "Negative Val",
            "teacher_email": "teacher1@cognify.edu",
            "subject": "math",
            "topic": "algebra",
            "subtopic": "quadratic",
            "purpose": "practice",
            "difficulty": "medium",
            "conceptual_pct": -10,
            "application_pct": 50,
            "reasoning_pct": 30,
            "memory_pct": 30
        })
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["error_code"], "VALIDATION_ERROR")

        # 11.3 Test valid blueprint success response contract
        resp = self.client.post('/assessment-blueprints', json={
            "name": "Valid BP",
            "teacher_email": "teacher1@cognify.edu",
            "subject": "math",
            "topic": "algebra",
            "subtopic": "quadratic",
            "purpose": "practice",
            "conceptual_pct": 25,
            "application_pct": 25,
            "reasoning_pct": 25,
            "memory_pct": 25,
            "duration": 30,
            "question_count": 10,
            "difficulty": "medium",
            "assessment_strategy": "adaptive_mixed"
        })
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["success"], True)
        self.assertIn("blueprint_id", data["data"])

    # 12. Quiz submission contracts
    def test_quiz_submission_contract(self):
        # 12.1 Missing required field
        token = auth.auth_provider.issue_token("student1@cognify.edu", "student")
        headers = {"Authorization": f"Bearer {token}"}
        resp = self.client.post('/submit', headers=headers, json={
            "student_email": "student1@cognify.edu"
        })
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["error_code"], "VALIDATION_ERROR")

        # 12.2 Successful submission contract
        resp = self.client.post('/submit', headers=headers, json={
            "student_email": "student1@cognify.edu",
            "question_id": 2044, # real seeded ID
            "question_text": "Which law explains inertia?",
            "correct": 1,
            "response_time": 5.0,
            "idle_time": 1.0,
            "rewrite_count": 0,
            "backspace_count": 0,
            "attempts": 1,
            "confidence": 0.8,
            "room_code": "R101"
        })
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["success"], True)
        self.assertIn("session", data["data"])
        self.assertEqual(data["data"]["message"], "Processed")


if __name__ == '__main__':
    unittest.main()
