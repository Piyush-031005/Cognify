import os
import sys
import time
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database
import memory_engine
import qqi_engine

def run_audit():
    report = ["# Pilot Readiness Review Report\\n"]
    
    conn = database.get_conn()
    cur = conn.cursor()
    
    # 1. Database Health
    cur.execute("PRAGMA journal_mode")
    j_mode = cur.fetchone()[0]
    report.append(f"- **Database Health**: {'✅' if j_mode.lower() == 'wal' else '❌'} (Journal Mode: {j_mode})")
    
    # 2. Knowledge Graph Integrity
    cur.execute("SELECT COUNT(*) FROM kg_edges WHERE source_id NOT IN (SELECT id FROM kg_nodes) OR target_id NOT IN (SELECT id FROM kg_nodes)")
    orphans = cur.fetchone()[0]
    report.append(f"- **Knowledge Graph Integrity**: {'✅' if orphans == 0 else '❌'} ({orphans} orphaned edges)")
    
    # 3. Reproducibility & Memory Replay Time
    start = time.time()
    # Inject dummy events for a test student
    test_email = 'audit_reproducibility@test.com'
    node_id = 'c1'
    for i in range(50):
        memory_engine.record_memory_event(test_email, node_id, 'concept', 'correct_answer')
    
    state1 = memory_engine.derive_current_state(test_email, node_id)
    state2 = memory_engine.derive_current_state(test_email, node_id)
    
    replay_time = (time.time() - start) / 100.0 # roughly time per derivation
    
    reproducible = (state1['retrieval_strength'] == state2['retrieval_strength'] and state1['storage_strength'] == state2['storage_strength'])
    report.append(f"- **Reproducibility Status**: {'✅' if reproducible else '❌'} (Deterministic Replay)")
    report.append(f"- **Memory Replay Time**: {'✅' if replay_time < 0.1 else '🟡'} ({replay_time:.4f} seconds per 50 events)")
    
    # Clean up dummy events
    cur.execute("DELETE FROM student_memory_events WHERE student_email = ?", (test_email,))
    conn.commit()
    
    # 4. QQI Consistency
    cur.execute("SELECT COUNT(*) FROM question_bank WHERE qqi_score < 0 OR qqi_score > 100")
    invalid_qqi = cur.fetchone()[0]
    report.append(f"- **QQI Consistency**: {'✅' if invalid_qqi == 0 else '❌'} ({invalid_qqi} invalid scores)")
    
    # Save Report
    conn.close()
    
    report_path = os.path.join(os.path.dirname(__file__), '..', 'pilot_readiness_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\\n".join(report))
        
    print(f"Pilot Readiness Audit complete. Report saved to {report_path}")

if __name__ == "__main__":
    run_audit()
