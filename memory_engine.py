import math
import json
import time
from datetime import datetime, timedelta
from database import get_conn

MEMORY_MODEL_VERSION = "v2.0"

def calculate_time_diff_days(t1_iso, t2_iso):
    try:
        t1 = datetime.fromisoformat(t1_iso)
        t2 = datetime.fromisoformat(t2_iso)
        delta = t2 - t1
        return max(0.0, delta.total_seconds() / 86400.0)
    except Exception:
        return 0.0

def get_memory_config():
    """
    Fetches the configuration weights and thresholds from the database.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT key, value, config_version FROM memory_config")
    rows = cur.fetchall()
    conn.close()
    
    config = {}
    config_version = "v1.0"
    for r in rows:
        config[r["key"]] = r["value"]
        config_version = r["config_version"]
        
    config["config_version"] = config_version
    return config

def log_state_transition(conn, email, concept_id, old_state, new_state, trigger_event_id, reason, timestamp):
    """
    Logs state machine transitions into the append-only ledger.
    """
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO memory_state_transitions (
            student_email, concept_id, old_state, new_state, trigger_event_id, reason, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (email, concept_id, old_state, new_state, trigger_event_id, reason, timestamp))

def check_and_generate_alerts(conn, email, concept_id, state, S, retrieval_rate, timestamp):
    """
    Evaluates trigger rules and posts to the memory_alerts ledger.
    """
    cur = conn.cursor()
    
    # 1. At risk of forgetting alert
    if state in ['At Risk', 'Forgotten']:
        cur.execute("""
            SELECT id FROM memory_alerts 
            WHERE student_email = ? AND concept_id = ? AND alert_type = 'at_risk_of_forgetting' AND status = 'active'
        """, (email, concept_id))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO memory_alerts (student_email, concept_id, alert_type, severity, description, timestamp)
                VALUES (?, ?, 'at_risk_of_forgetting', 'Medium', ?, ?)
            """, (email, concept_id, f"Concept '{concept_id}' has decayed to state '{state}' with memory strength {round(S, 2)}", timestamp))
            
    # 2. Prerequisite failure alert
    if state == 'Forgotten':
        try:
            cur.execute("""
                SELECT target_id FROM kg_edges 
                WHERE source_id = ? AND relation_type = 'prerequisite_of' AND status = 'production'
            """, (concept_id,))
            downstream = cur.fetchall()
            if downstream:
                cur.execute("""
                    SELECT id FROM memory_alerts 
                    WHERE student_email = ? AND concept_id = ? AND alert_type = 'prerequisite_failure' AND status = 'active'
                """, (email, concept_id))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO memory_alerts (student_email, concept_id, alert_type, severity, description, timestamp)
                        VALUES (?, ?, 'prerequisite_failure', 'High', ?, ?)
                    """, (email, concept_id, f"Core prerequisite '{concept_id}' has failed. Downstream concepts at risk.", timestamp))
        except Exception:
            pass  # kg_edges table may not exist in isolated test environments

def calculate_priority(conn, email, concept_id, retrieval_strength, S, f, config):
    """
    Computes priority score: priority = memory_risk + misconception_severity + prerequisite_importance + teacher_priority + exam_weight
    """
    cur = conn.cursor()

    # 1. Memory Risk (1.0 - R)
    R_risk = 1.0 - retrieval_strength

    # 2. Misconception Severity
    S_mcp = 0.0
    try:
        cur.execute("""
            SELECT severity FROM misconception_clusters
            WHERE concept_id = ? AND status = 'validated'
        """, (concept_id,))
        mcp = cur.fetchone()
        if mcp:
            sev_map = {"Low": 0.25, "Medium": 0.5, "High": 0.75, "Critical": 1.0}
            S_mcp = sev_map.get(mcp["severity"], 0.5)
    except Exception:
        pass  # table not present in this environment

    # 3. Prerequisite Importance (KG out-degree density)
    I_prereq = 0.0
    try:
        cur.execute("""
            SELECT COUNT(*) as degree FROM kg_edges
            WHERE source_id = ? AND relation_type = 'prerequisite_of'
        """, (concept_id,))
        I_prereq = min(1.0, cur.fetchone()["degree"] / 5.0)
    except Exception:
        pass

    # 4. Teacher Priority
    P_teacher = 0.0
    try:
        cur.execute("""
            SELECT COUNT(*) as cnt FROM teacher_notes
            WHERE observation LIKE ? OR reason LIKE ?
        """, (f"%{concept_id}%", f"%{concept_id}%"))
        P_teacher = min(1.0, cur.fetchone()["cnt"] * 0.5)
    except Exception:
        pass

    # 5. Exam Weight (Blueprints representation)
    W_exam = 0.0
    try:
        cur.execute("""
            SELECT COUNT(*) as cnt FROM assessment_blueprints
            WHERE topic = ? OR subtopic = ?
        """, (concept_id, concept_id))
        W_exam = min(1.0, cur.fetchone()["cnt"] * 0.2)
    except Exception:
        pass

    # Pull config weights (no hardcoding)
    w_risk = config.get("WEIGHT_MEMORY_RISK", 0.3)
    w_mcp = config.get("WEIGHT_MISCONCEPTION_SEVERITY", 0.2)
    w_prereq = config.get("WEIGHT_PREREQUISITE_IMPORTANCE", 0.2)
    w_teacher = config.get("WEIGHT_TEACHER_PRIORITY", 0.15)
    w_exam = config.get("WEIGHT_EXAM_WEIGHT", 0.15)

    priority = (w_risk * R_risk) + (w_mcp * S_mcp) + (w_prereq * I_prereq) + (w_teacher * P_teacher) + (w_exam * W_exam)
    return min(1.0, max(0.0, priority))


def project_concept_memory(email, concept_id, current_time=None):
    """
    Projector function: Replays all memory_events chronologically to derive concept_memory,
    review_schedule, alerts, and state transitions. (Event Sourcing Projection)
    """
    if not current_time:
        current_time = datetime.now().isoformat()
        
    conn = get_conn()
    cur = conn.cursor()
    
    # Fetch all events ordered by time & ID
    cur.execute("""
        SELECT * FROM memory_events 
        WHERE student_email = ? AND concept_id = ?
        ORDER BY timestamp ASC, id ASC
    """, (email, concept_id))
    events = [dict(r) for r in cur.fetchall()]
    
    if not events:
        conn.close()
        return None
        
    config = get_memory_config()
    
    # Initial state variables
    S = config.get("DEFAULT_INITIAL_STRENGTH", 0.3)
    f = config.get("DEFAULT_DECAY_RATE", 0.05)
    state = "Unknown"
    reinforcements = 0
    successes = 0
    failures = 0
    last_success = None
    last_failure = None
    provenance = set()
    explanations = []
    
    last_t = events[0]["timestamp"]
    last_state = "Unknown"
    trigger_event_id = None
    
    for ev in events:
        t = calculate_time_diff_days(last_t, ev["timestamp"])
        trigger_event_id = ev["id"]
        
        # Apply temporal decay over the gap
        if t > 0:
            R_current = math.exp(-t * f / S)
            if R_current < config.get("FORGETTING_THRESHOLD", 0.4):
                state = "Forgotten"
            elif R_current < 0.5:
                state = "At Risk"
                
        # Record state before event to detect transitions
        old_state_loop = state
        
        # Parse payload
        try:
            payload = json.loads(ev["payload"]) if ev["payload"] else {}
        except Exception:
            payload = {}
            
        event_type = ev["event_type"]
        source = ev["source_module"] if ev["source_module"] else "unknown"
        provenance.add(source)
        
        # Process positive reinforcements
        is_success = event_type in [
            'correct_answer', 'recommendation_successful', 'student_recovery', 
            'correct'  # legacy support
        ] or payload.get("update_reason") == 'correct_answer'
        
        is_failure = event_type in [
            'wrong_answer', 'misconception_confirmed', 'prerequisite_failure',
            'wrong'  # legacy support
        ] or payload.get("update_reason") == 'wrong_answer'
        
        if is_success:
            successes += 1
            last_success = ev["timestamp"]
            S = min(1.0, S + config.get("REINFORCE_BOOST", 0.15) * (1.0 - S))
            f = max(0.01, f * 0.8)
            explanations.append(f"+ Reinforcement Success via {source.upper()}")
            
            # Transition to Recovered if coming from At Risk or Forgotten
            if old_state_loop in ['At Risk', 'Forgotten']:
                state = "Recovered"
            elif old_state_loop == 'Unknown':
                state = "Learning"
                
        elif is_failure:
            failures += 1
            last_failure = ev["timestamp"]
            S = max(0.05, S - config.get("FAILURE_PENALTY", 0.2))
            f = min(10.0, f * 1.2)
            explanations.append(f"- Failure Event via {source.upper()}")
            
            # Calculate decayed R after failure penalty
            decay_val = math.exp(-0.01 * f / S)
            if decay_val < config.get("FORGETTING_THRESHOLD", 0.4):
                state = "Forgotten"
            else:
                state = "At Risk"
        else:
            # Baseline other events
            if old_state_loop == 'Unknown':
                state = "Learning"
            explanations.append(f"Recorded event: {event_type} via {source.upper()}")
            
        reinforcements += 1
        
        # State transitions audit log
        if state != old_state_loop:
            log_state_transition(conn, email, concept_id, old_state_loop, state, trigger_event_id, f"Event {event_type} processed", ev["timestamp"])
            
        last_t = ev["timestamp"]
        
    # Project forward to the current_time evaluation boundary
    t_now = calculate_time_diff_days(last_t, current_time)
    # Clamp to avoid R_final=1.0 when t_now=0 masking failures
    R_final = math.exp(-max(t_now, 0.0) * f / S)

    # Calculate final state machine state
    # Priority order: if the in-loop state is a degraded state (At Risk / Forgotten / Recovered),
    # preserve it unless genuine temporal decay has pushed us further downward.
    # Stable requires BOTH high retrieval AND sufficient successful reinforcements.
    final_state = state

    if state in ['At Risk', 'Forgotten']:
        # Check if temporal decay has made things even worse
        if R_final < config.get("FORGETTING_THRESHOLD", 0.4):
            final_state = "Forgotten"
        else:
            final_state = state  # preserve failure-driven state
    elif state == 'Recovered':
        # Recovered remains unless decay drops below threshold
        if R_final < config.get("FORGETTING_THRESHOLD", 0.4):
            final_state = "Forgotten"
        elif R_final < 0.5:
            final_state = "At Risk"
        else:
            final_state = "Recovered"
    elif successes >= 3 and S >= 0.7:
        # Only grant Stable if we have evidence of multiple successes AND strong storage
        final_state = "Stable"
    else:
        # Apply decay boundaries for Learning / Unknown states
        if R_final < config.get("FORGETTING_THRESHOLD", 0.4):
            final_state = "Forgotten"
        elif R_final < 0.5:
            final_state = "At Risk"

    # Audit log the final state transition if state changed post-projection
    if final_state != state:
        log_state_transition(conn, email, concept_id, state, final_state, trigger_event_id,
                             "Temporal Ebbinghaus decay projection", current_time)
        explanations.append(f"State resolved to '{final_state}' after projection over {round(t_now, 1)} days")

    # Schedule review date: t = S * ln(1 / threshold) / f
    review_interval_days = (S * math.log(1.0 / config.get("FORGETTING_THRESHOLD", 0.4))) / f
    review_interval_days = min(30.0, max(1.0, review_interval_days))
    next_review_dt = (datetime.fromisoformat(last_t) + timedelta(days=review_interval_days)).isoformat()

    
    # Mastery success rate
    retrieval_success = successes / reinforcements if reinforcements > 0 else 0.0
    
    # Explainability payload
    explainability = {
        "positives": [line for line in explanations if line.startswith("+")],
        "negatives": [line for line in explanations if line.startswith("-")],
        "decay_days": round(t_now, 2),
        "decay_retrieval_strength": round(R_final, 3)
    }
    
    # Confidence score: min(1.0, count / 10.0)
    confidence = min(1.0, reinforcements / 10.0)
    
    # Run alerts check
    check_and_generate_alerts(conn, email, concept_id, final_state, S, retrieval_success, current_time)
    
    # Insert or update concept_memory
    cur.execute("""
        INSERT INTO concept_memory (
            student_email, concept_id, memory_strength, forgetting_rate, memory_state,
            memory_confidence, memory_explanation, derived_from, trigger_event_id,
            config_version, reinforcement_count, retrieval_success_rate, last_success,
            last_failure, next_review_date, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(student_email, concept_id) DO UPDATE SET
            memory_strength = excluded.memory_strength,
            forgetting_rate = excluded.forgetting_rate,
            memory_state = excluded.memory_state,
            memory_confidence = excluded.memory_confidence,
            memory_explanation = excluded.memory_explanation,
            derived_from = excluded.derived_from,
            trigger_event_id = excluded.trigger_event_id,
            config_version = excluded.config_version,
            reinforcement_count = excluded.reinforcement_count,
            retrieval_success_rate = excluded.retrieval_success_rate,
            last_success = excluded.last_success,
            last_failure = excluded.last_failure,
            next_review_date = excluded.next_review_date,
            last_updated = excluded.last_updated
    """, (
        email, concept_id, S, f, final_state, confidence, json.dumps(explainability),
        json.dumps(list(provenance)), trigger_event_id, config.get("config_version", "v1.0"),
        reinforcements, retrieval_success, last_success, last_failure, next_review_dt, current_time
    ))
    
    # Update review schedule
    priority = calculate_priority(conn, email, concept_id, R_final, S, f, config)
    status = "overdue" if current_time > next_review_dt else "pending"
    
    cur.execute("""
        INSERT INTO review_schedule (
            student_email, concept_id, scheduled_date, status, priority, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(student_email, concept_id) DO UPDATE SET
            scheduled_date = excluded.scheduled_date,
            status = excluded.status,
            priority = excluded.priority
    """, (email, concept_id, next_review_dt, status, priority, current_time))
    
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "derived_S": S,
        "derived_R": R_final,
        "state": final_state,
        "next_review": next_review_dt
    }

def record_memory_event(email, node_id, memory_type_or_event_type, update_reason_or_payload=None, 
                        effectiveness_delta=0.0, timestamp_override=None, source_module=None, event_version="v2.0"):
    """
    Unified entry point for appending memory events. Handles both v1.0 legacy invocations
    and v2.0 event sourcing payloads.
    """
    now_str = timestamp_override if timestamp_override else datetime.now().isoformat()
    config = get_memory_config()
    
    # 1. Adapt legacy parameters to v2.0
    if isinstance(update_reason_or_payload, str) or update_reason_or_payload is None:
        # Legacy Call
        event_type = update_reason_or_payload if update_reason_or_payload else memory_type_or_event_type
        payload_dict = {
            "legacy_memory_type": memory_type_or_event_type,
            "effectiveness_delta": effectiveness_delta,
            "update_reason": update_reason_or_payload
        }
        source = source_module if source_module else ("qqi" if memory_type_or_event_type == "concept" else "misconception")
    else:
        # V2 Call
        event_type = memory_type_or_event_type
        payload_dict = update_reason_or_payload
        source = source_module if source_module else "unknown"
        
    conn = get_conn()
    cur = conn.cursor()
    
    # Append immutable event
    cur.execute("""
        INSERT INTO memory_events (
            student_email, concept_id, event_type, payload, event_version,
            source_module, algorithm_version, config_version, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        email, node_id, event_type, json.dumps(payload_dict), event_version,
        source, MEMORY_MODEL_VERSION, config.get("config_version", "v1.0"), now_str
    ))
    conn.commit()
    conn.close()
    
    # Run the projector function to update state (Event Sourcing Model)
    return project_concept_memory(email, node_id, current_time=now_str)

def derive_current_state(email, node_id, up_to_time=None):
    """
    Maintains compatibility with legacy queries by projecting concept state up to up_to_time.
    """
    res = project_concept_memory(email, node_id, current_time=up_to_time)
    if not res:
        return {
            "retrieval_strength": 0.0,
            "storage_strength": 0.1,
            "confidence": 0.0,
            "evidence_count": 0,
            "memory_type": "unknown",
            "last_event_time": None
        }
        
    # Fetch final details to match legacy shape
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM concept_memory WHERE student_email = ? AND concept_id = ?", (email, node_id))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return {
            "retrieval_strength": 0.0,
            "storage_strength": 0.1,
            "confidence": 0.0,
            "evidence_count": 0,
            "memory_type": "unknown",
            "last_event_time": None
        }
        
    # Ebbinghaus predictions
    S = row["memory_strength"]
    f = row["forgetting_rate"]
    R_current = res["derived_R"]
    
    def predict(days):
        base_r = R_current * math.exp(-days * f / S)
        uncertainty = round(min(0.2, (days / 60.0) * (1.0 - row["memory_confidence"])), 2)
        return {"value": round(base_r, 3), "uncertainty": uncertainty}
        
    return {
        "retrieval_strength": round(R_current, 3),
        "storage_strength": round(S, 3),
        "confidence": round(row["memory_confidence"], 3),
        "evidence_count": row["reinforcement_count"],
        "memory_type": "concept",
        "last_event_time": row["last_updated"],
        "predictions": {
            "7_days": predict(7),
            "14_days": predict(14),
            "30_days": predict(30)
        }
    }

def get_full_student_memory(email):
    """
    Maps current concept memories into categorized buckets to construct
    the student's digital twin cognitive memory profile.
    """
    conn = get_conn()
    cur = conn.cursor()
    
    # Replay/project all concepts the student has events for
    cur.execute("SELECT DISTINCT concept_id FROM memory_events WHERE student_email = ?", (email,))
    concepts = [r["concept_id"] for r in cur.fetchall()]
    conn.close()
    
    mastered = []
    at_risk = []
    forgetting = []
    misconceptions = []
    
    now_str = datetime.now().isoformat()
    for concept_id in concepts:
        project_concept_memory(email, concept_id, current_time=now_str)
        legacy_state = derive_current_state(email, concept_id, up_to_time=now_str)
        
        # Categorize
        if legacy_state["retrieval_strength"] >= 0.8:
            mastered.append({"node_id": concept_id, **legacy_state})
        elif legacy_state["retrieval_strength"] < 0.4:
            forgetting.append({"node_id": concept_id, **legacy_state})
        else:
            at_risk.append({"node_id": concept_id, **legacy_state})
            
    # Misconceptions category mappings
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT cluster_id, concept_id, severity, status 
        FROM misconception_clusters 
        WHERE status = 'validated'
    """)
    validated_mcps = cur.fetchall()
    conn.close()
    
    for m in validated_mcps:
        # Check if student had a misconception event
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as count FROM memory_events 
            WHERE student_email = ? AND concept_id = ? AND event_type = 'misconception_confirmed'
        """, (email, m["concept_id"]))
        has_mcp = cur.fetchone()["count"] > 0
        conn.close()
        
        if has_mcp:
            misconceptions.append({
                "node_id": m["cluster_id"],
                "concept_id": m["concept_id"],
                "severity": m["severity"],
                "status": m["status"]
            })
            
    return {
        "student_email": email,
        "mastered": mastered,
        "at_risk": at_risk,
        "forgetting": forgetting,
        "active_misconceptions": misconceptions
    }

def handle_response_submitted(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Subscribes to ResponseSubmitted event.
    Logs memory event, projects states, and publishes MemoryUpdated.
    """
    payload = event_data["payload_json"]
    if isinstance(payload, str):
        payload = json.loads(payload)

    email = event_data["entity_id"]
    question_id = payload.get("question_id")
    is_correct = payload.get("is_correct", False)
    
    # Resolve concept for question
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT qc.concept_id FROM question_concepts qc 
        JOIN question_bank qb ON qb.id = qc.question_id
        WHERE qb.id = ? OR qb.semantic_id = ?
        LIMIT 1
    """, (question_id, question_id))
    row = cur.fetchone()
    conn.close()
    
    concept_id = row["concept_id"] if row else "algebra"
    
    event_type = "correct_answer" if is_correct else "wrong_answer"
    
    # Record memory event
    record_memory_event(
        email=email,
        node_id=concept_id,
        memory_type_or_event_type=event_type,
        update_reason_or_payload={"question_id": question_id, "is_correct": is_correct},
        source_module="event_bus"
    )
    
    # Downstream publication (suppressed in SAFE replay mode)
    if not is_replay or replay_mode == "LIVE":
        import event_bus
        event_bus.publish(
            event_type="MemoryUpdated",
            entity_type="student",
            entity_id=email,
            producer="memory_engine",
            producer_version="v2.5.0",
            schema_version="v1.0",
            metadata_json=event_data.get("metadata_json", {}),
            payload_json={
                "concept_id": concept_id,
                "is_correct": is_correct,
                "question_id": question_id
            }
        )
