import sqlite3
import json
import uuid
import os
import sys
import yaml
import math
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup global in-memory DB connection wrapper
_global_conn = sqlite3.connect(':memory:', check_same_thread=False)
_global_conn.row_factory = sqlite3.Row

class ConnectionWrapper:
    def __init__(self, c):
        self._conn = c
    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)
    def commit(self):
        self._conn.commit()
    def rollback(self):
        self._conn.rollback()
    def close(self):
        pass
    def __getattr__(self, name):
        return getattr(self._conn, name)

wrapped_conn = ConnectionWrapper(_global_conn)

import database
database.get_conn = lambda: wrapped_conn

import apd_engine
import app
apd_engine.get_conn = lambda: wrapped_conn
app.get_conn = lambda: wrapped_conn

from database import init_db, upgrade_database_schema

def setup_in_memory_db():
    conn = _global_conn
    init_db()
    upgrade_database_schema()
    
    # Insert mock nodes
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO kg_nodes (id, name, type, subject) VALUES ('c1', 'Concept 1', 'concept', 'math')")
    cur.execute("INSERT OR REPLACE INTO kg_nodes (id, name, type, subject) VALUES ('c2', 'Concept 2', 'concept', 'math')")
    
    # Insert mock user profiles with cohort information in 'education'
    for i in range(60):
        email = f"student_{i}@test.com"
        cohort = "cohort_A" if i < 30 else "cohort_B"
        edu_json = json.dumps({
            "cohort_id": cohort,
            "institution": "Stanford University" if cohort == "cohort_A" else "Harvard University",
            "grade": "sophomore",
            "curriculum": "CS_V2",
            "academic_year": "2026"
        })
        cur.execute("INSERT OR REPLACE INTO users (email, role, education) VALUES (?, 'student', ?)", (email, edu_json))
        
        # Concept mastery values
        # cohort_A: Support prerequisite c1 -> c2 (c1 mastered -> c2 mastered, c1 struggles -> c2 struggles)
        if i < 30:
            if i % 3 == 0:
                cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'c1', 0.8)", (email,))
                cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'c2', 0.9)", (email,))
            else:
                cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'c1', 0.2)", (email,))
                cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'c2', 0.1)", (email,))
        # cohort_B: Medium support with contradictions
        else:
            if (i - 30) % 3 == 0:
                # Mastered both
                cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'c1', 0.8)", (email,))
                cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'c2', 0.85)", (email,))
            elif (i - 30) % 3 == 1:
                # Struggle both
                cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'c1', 0.3)", (email,))
                cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'c2', 0.3)", (email,))
            else:
                # Contradictory: Mastered B, struggled A
                cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'c1', 0.3)", (email,))
                cur.execute("INSERT INTO student_concept_mastery (student_email, node_id, mastery_level) VALUES (?, 'c2', 0.85)", (email,))
            
    conn.commit()
    return conn

def test_apd_v2_suite():
    conn = setup_in_memory_db()
    client = app.app.test_client()
    
    # Clear any seeded edges to start clean
    cur = conn.cursor()
    cur.execute("DELETE FROM kg_edges WHERE relation_type='prerequisite_of'")
    cur.execute("DELETE FROM kg_edge_evidence")
    cur.execute("DELETE FROM kg_evolution_log")
    
    # 1. Run APD v2 discovery
    print("[TEST] Running APD discovery via API POST /apd/run...")
    response = client.post('/apd/run', json={"subject": "math", "min_sample": 10})
    assert response.status_code == 200
    res_data = response.json
    assert res_data["status"] == "success"
    
    # 2. Check GET /apd/discovered
    print("[TEST] Verifying discovered candidate edges...")
    response = client.get('/apd/discovered')
    assert response.status_code == 200
    disc_data = response.json
    edges = disc_data["discovered_edges"]
    assert len(edges) > 0, "No candidate edges discovered."
    
    candidate_edge = edges[0]
    edge_id = candidate_edge["edge_id"]
    assert edge_id.startswith("apd_"), f"Edge ID {edge_id} does not follow apd_000001 format"
    assert candidate_edge["status"] == "candidate"
    
    # 3. Check GET /apd/evidence/<edge_id>
    print("[TEST] Checking detailed evidence history...")
    response = client.get(f'/apd/evidence/{edge_id}')
    assert response.status_code == 200
    ev_data = response.json
    assert ev_data["edge_id"] == edge_id
    history = ev_data["evidence_history"]
    assert len(history) >= 2, "Cohort isolation failed. Should have separate rows per cohort."
    
    # Verify cohort awareness fields
    for row in history:
        assert row["cohort_id"] in ("cohort_A", "cohort_B")
        assert row["institution"] in ("Stanford University", "Harvard University")
        assert row["academic_year"] == "2026"
        assert "algorithm_version" in row
        
    # 4. Check GET /apd/config & POST /apd/config
    print("[TEST] Fetching and updating apd_config...")
    response = client.get('/apd/config')
    assert response.status_code == 200
    cfg = response.json
    assert "STAT_WEIGHT" in cfg
    
    # Modify weights
    new_weights = {"STAT_WEIGHT": 0.5, "TEACHER_WEIGHT": 0.2, "HISTORY_WEIGHT": 0.2, "SAMPLE_WEIGHT": 0.1}
    response = client.post('/apd/config', json=new_weights)
    assert response.status_code == 200
    updated_cfg = response.json["config"]
    assert updated_cfg["STAT_WEIGHT"] == 0.5
    
    # 5. POST /apd/approve validation
    print("[TEST] Verifying teacher approval validation flow...")
    response = client.post('/apd/approve', json={
        "edge_id": edge_id,
        "teacher_email": "senior@school.edu"
    })
    assert response.status_code == 200
    app_data = response.json
    assert app_data["status"] == "validated"
    
    # Confirm DB updates
    cur.execute("SELECT status, validation_count FROM kg_edges WHERE edge_id=?", (edge_id,))
    edge_row = cur.fetchone()
    assert edge_row["status"] == "validated"
    assert edge_row["validation_count"] == 1
    
    # 6. GET /apd/replay/<edge_id>
    print("[TEST] Verifying confidence replay tracking...")
    response = client.get(f'/apd/replay/{edge_id}')
    assert response.status_code == 200
    rep_data = response.json
    replay_history = rep_data["replay_history"]
    assert len(replay_history) >= 2, "Evolution logging failed to capture transitions."
    assert replay_history[-1]["teacher_action"] == "approve"
    
    # 7. POST /apd/reject
    print("[TEST] Verifying teacher rejection flow...")
    response = client.post('/apd/reject', json={
        "edge_id": edge_id,
        "teacher_email": "regular@school.edu"
    })
    assert response.status_code == 200
    rej_data = response.json
    assert rej_data["status"] == "rejected"
    
    # Confirm status in DB
    cur.execute("SELECT status FROM kg_edges WHERE edge_id=?", (edge_id,))
    assert cur.fetchone()["status"] == "rejected"
    
    # 8. Temporal decay & Deprecation transition check
    print("[TEST] Verifying exponential decay deprecation transition...")
    # Change status back to validated for decay testing, setting low base values
    cur.execute("UPDATE kg_edges SET status='validated', overall_confidence=0.35, historical_stability=0.1 WHERE edge_id=?", (edge_id,))
    cur.execute("UPDATE kg_edge_evidence SET confidence_score=0.1 WHERE edge_id=?", (edge_id,))
    
    # Simulate 100 days of inactivity
    cur.execute("UPDATE kg_edge_evidence SET last_updated = ? WHERE edge_id=?", 
                ((datetime.now() - timedelta(days=100)).isoformat(), edge_id))
    conn.commit()
    
    # Trigger decay
    apd_engine.apply_confidence_decay("math")
    
    cur.execute("SELECT status, overall_confidence FROM kg_edges WHERE edge_id=?", (edge_id,))
    decayed_row = cur.fetchone()
    # Since confidence decayed and dropped below deprecate threshold (0.4), it should transition to deprecated
    assert decayed_row["status"] == "deprecated", f"Status is {decayed_row['status']}, expected deprecated"
    
    # 9. Replay evolution logs
    print("[TEST] Verifying GET /apd/evolution...")
    response = client.get('/apd/evolution')
    assert response.status_code == 200
    evol_data = response.json
    assert len(evol_data["evolution_logs"]) > 0
    
    # 10. Statistics endpoint
    print("[TEST] Verifying GET /apd/statistics...")
    response = client.get('/apd/statistics')
    assert response.status_code == 200
    stats = response.json["statistics"]
    assert "validated_edges" in stats
    assert "candidate_edges" in stats
    assert "deprecated_edges" in stats
    assert stats["total_runs"] > 0
    
    print("[SUCCESS] All APD v2 integration tests passed successfully.")
    conn.close()

if __name__ == "__main__":
    test_apd_v2_suite()
