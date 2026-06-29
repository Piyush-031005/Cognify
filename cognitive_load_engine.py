"""
cognitive_load_engine.py
Week 12 – Cognitive Load Intelligence Engine (CCLI)
Deterministic estimation of Intrinsic, Extraneous, and Germane Loads.
Calculates EWMA-based student load states, triggers pacing alerts, and updates history.
"""

import math
import json
import uuid
from datetime import datetime
from database import get_conn


# =============================================================================
# CONFIGURATION LOADER
# =============================================================================

def _load_ccli_config():
    """
    Loads all CCLI parameters from cognitive_load_config table.
    Falls back to safe defaults if table is missing or empty.
    """
    defaults = {
        "weight_intrinsic_load": 0.4,
        "weight_extraneous_load": 0.3,
        "weight_germane_load": 0.3,
        "weight_bloom_level": 0.3,
        "weight_irt_difficulty": 0.4,
        "weight_prereq_complexity": 0.3,
        "weight_prompt_length": 0.5,
        "weight_interaction_complexity": 0.5,
        "weight_sat": 0.4,
        "weight_hesitation": 0.3,
        "weight_backspace_efficiency": 0.3,
        "ewma_alpha": 0.25,
        "fatigue_threshold": 0.7,
        "recovery_threshold": 0.5,
        "memory_discount_factor": 0.3,
    }
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT key, value FROM cognitive_load_config")
        rows = cur.fetchall()
        for r in rows:
            defaults[r["key"]] = r["value"]
    except Exception:
        pass
    finally:
        conn.close()
    return defaults


def get_ccli_config():
    """Returns all active configuration records."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT key, value, config_version, updated_by, updated_at FROM cognitive_load_config")
        rows = [dict(r) for r in cur.fetchall()]
    except Exception:
        rows = []
    finally:
        conn.close()
    return rows


def update_ccli_config(key, value, updated_by="teacher"):
    """Updates a single config parameter."""
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cur.execute("""
            INSERT INTO cognitive_load_config (key, value, config_version, updated_by, updated_at)
            VALUES (?, ?, 'v1.0', ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_by=excluded.updated_by,
                updated_at=excluded.updated_at
        """, (key, float(value), updated_by, now))
        conn.commit()
        return {"key": key, "value": float(value), "updated_by": updated_by, "updated_at": now}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


# =============================================================================
# COGNITIVE LOAD CALCULATION ENGINE
# =============================================================================

def compute_and_save_cognitive_load(response_id):
    """
    Computes IL, EL, GL, and CCLI for a response ID, saves the event,
    updates student rolling state using EWMA, and handles overload alerts.
    """
    config = _load_ccli_config()
    conn = get_conn()
    cur = conn.cursor()

    # 1. Fetch response, question, and student context
    try:
        cur.execute("""
            SELECT r.*, qb.prompt, qb.cognitive_type, qb.cognitive_load, qb.qqi_score,
                   qb.irt_difficulty, qb.irt_discrimination, qb.estimated_time
            FROM responses r
            JOIN question_bank qb ON qb.id = r.question_id
            WHERE r.id = ?
        """, (response_id,))
        res_row = cur.fetchone()
    except Exception as e:
        conn.close()
        return {"error": f"Failed to query response: {str(e)}"}

    if not res_row:
        conn.close()
        return {"error": f"Response ID {response_id} not found."}

    res_row = dict(res_row)
    student_email = res_row["student_email"]
    question_id = res_row["question_id"]
    correct = res_row["correct"]
    response_time = res_row["response_time"] or 30.0
    hesitation_score = res_row.get("hesitation_score", 0.0) or 0.0
    backspace_count = res_row.get("backspace_count", 0) or 0
    rewrite_count = res_row.get("rewrite_count", 0) or 0
    same_option_clicks = res_row.get("same_option_clicks", 0) or 0

    # Match topic/concept mappings for the question
    concept_id = None
    try:
        cur.execute("SELECT concept_id FROM question_concepts WHERE question_id = ? LIMIT 1", (question_id,))
        qc_row = cur.fetchone()
        if qc_row:
            concept_id = qc_row["concept_id"]
    except Exception:
        pass

    # Read Bloom level from question or defaults
    bloom_level_val = 3.0 # default to 'apply'
    bloom_map = {"remember": 1.0, "understand": 2.0, "apply": 3.0, "analyze": 4.0, "evaluate": 5.0, "create": 6.0}
    cog_type = (res_row["cognitive_type"] or "").lower()
    if cog_type in bloom_map:
        bloom_level_val = bloom_map[cog_type]

    # Prerequisite Complexity
    prereq_count = 0
    if concept_id:
        try:
            cur.execute("SELECT COUNT(*) FROM kg_edges WHERE target_id = ? AND relation_type = 'prerequisite_of'", (concept_id,))
            prereq_count = cur.fetchone()[0] or 0
        except Exception:
            pass

    # Long-term memory storage strength modulation
    memory_strength = None
    if concept_id:
        try:
            cur.execute("SELECT memory_strength FROM concept_memory WHERE student_email = ? AND concept_id = ?", (student_email, concept_id))
            mem_row = cur.fetchone()
            if mem_row:
                memory_strength = mem_row["memory_strength"]
        except Exception:
            pass

    # Latent difficulty b from NBIRT
    b_val = res_row["irt_difficulty"]
    if b_val is None:
        # Fallback to QQI-score derived difficulty
        qqi_score = res_row["qqi_score"] if res_row["qqi_score"] is not None else 80.0
        b_val = 1.0 - (qqi_score / 100.0)
    else:
        # Sigmoid map b into (0, 1] range
        b_val = 1.0 / (1.0 + math.exp(-b_val))

    # --- 1. Compute Intrinsic Load (IL) ---
    il_bloom = bloom_level_val / 6.0
    il_diff = b_val
    il_prereq = min(1.0, prereq_count / 5.0)

    il_base = (
        config["weight_bloom_level"] * il_bloom +
        config["weight_irt_difficulty"] * il_diff +
        config["weight_prereq_complexity"] * il_prereq
    )
    # Adjust for student memory familiarity
    if memory_strength is not None:
        il_adjusted = il_base * (1.0 - config["memory_discount_factor"] * memory_strength)
    else:
        il_adjusted = il_base

    # --- 2. Compute Extraneous Load (EL) ---
    prompt_words = len((res_row["prompt"] or "").split())
    el_prompt_len = min(1.0, math.log(prompt_words + 1) / math.log(151))
    
    # Interaction struggle: same option clicks, rewrite counts
    el_struggle = min(1.0, (same_option_clicks + rewrite_count) / 5.0)

    el_base = (
        config["weight_prompt_length"] * el_prompt_len +
        config["weight_interaction_complexity"] * el_struggle
    )

    # --- 3. Compute Germane Load (GL) ---
    # Speed Accuracy Trade-off (SAT)
    estimated_time = res_row["estimated_time"] or 30.0
    time_factor = min(1.0, response_time / (3.0 * estimated_time))
    sat_val = correct * (1.0 - time_factor)

    gl_sat = sat_val
    gl_hesitation = 1.0 - hesitation_score
    gl_backspace = correct * min(1.0, backspace_count / 5.0)

    gl_base = (
        config["weight_sat"] * gl_sat +
        config["weight_hesitation"] * gl_hesitation +
        config["weight_backspace_efficiency"] * gl_backspace
    )

    # --- 4. Composite Cognitive Load Index (CCLI) ---
    ccli = (
        config["weight_intrinsic_load"] * il_adjusted +
        config["weight_extraneous_load"] * el_base -
        config["weight_germane_load"] * gl_base
    )
    ccli = min(1.0, max(0.0, ccli))

    # Compile explainability payload
    explanation = {
        "intrinsic": {
            "bloom_level": round(il_bloom, 3),
            "irt_difficulty": round(il_diff, 3),
            "prerequisite_complexity": round(il_prereq, 3),
            "memory_discount_applied": memory_strength is not None,
            "raw_total": round(il_adjusted, 3)
        },
        "extraneous": {
            "prompt_length": round(el_prompt_len, 3),
            "interaction_struggle": round(el_struggle, 3),
            "raw_total": round(el_base, 3)
        },
        "germane": {
            "speed_accuracy_tradeoff": round(gl_sat, 3),
            "hesitation_avoidance": round(gl_hesitation, 3),
            "self_correction_efficiency": round(gl_backspace, 3),
            "raw_total": round(gl_base, 3)
        },
        "composite": {
            "ccli": round(ccli, 4)
        }
    }

    event_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    # Save event record to database
    try:
        cur.execute("""
            INSERT INTO cognitive_load_events (
                event_id, response_id, student_email, concept_id,
                intrinsic_load, extraneous_load, germane_load, composite_load,
                explanation_json, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, response_id, student_email, concept_id,
            round(il_adjusted, 4), round(el_base, 4), round(gl_base, 4), round(ccli, 4),
            json.dumps(explanation), now
        ))
    except Exception as e:
        conn.close()
        return {"error": f"Failed to insert CCLI event: {str(e)}"}

    # --- 5. Update Student EWMA State ---
    cur.execute("""
        SELECT rolling_il, rolling_el, rolling_gl, rolling_ccli, alert_status
        FROM student_cognitive_load_state WHERE student_email = ?
    """, (student_email,))
    state_row = cur.fetchone()

    alpha = config["ewma_alpha"]
    if state_row:
        old_il = state_row["rolling_il"] or 0.0
        old_el = state_row["rolling_el"] or 0.0
        old_gl = state_row["rolling_gl"] or 0.0
        old_ccli = state_row["rolling_ccli"] or 0.5
        old_status = state_row["alert_status"] or "normal"

        new_il = alpha * il_adjusted + (1.0 - alpha) * old_il
        new_el = alpha * el_base + (1.0 - alpha) * old_el
        new_gl = alpha * gl_base + (1.0 - alpha) * old_gl
        new_ccli = alpha * ccli + (1.0 - alpha) * old_ccli
    else:
        # First calculations
        old_ccli = 0.5
        old_status = "normal"
        new_il = il_adjusted
        new_el = el_base
        new_gl = gl_base
        new_ccli = ccli

    # Determine confidence based on responses count
    cur.execute("SELECT COUNT(*) FROM responses WHERE student_email = ?", (student_email,))
    attempts = cur.fetchone()[0] or 1
    confidence = min(1.0, attempts / 10.0)

    new_status = old_status

    # --- 6. Overload Alert Handling ---
    alert_details = None
    fatigue_threshold = config["fatigue_threshold"]
    recovery_threshold = config["recovery_threshold"]

    if new_status == "normal" and new_ccli > fatigue_threshold:
        new_status = "fatigued"
        alert_id = str(uuid.uuid4())
        severity = "severe" if new_ccli > 0.85 else "moderate"
        cur.execute("""
            INSERT INTO cognitive_load_alerts (alert_id, student_email, ccli_value, severity, status, created_at)
            VALUES (?, ?, ?, ?, 'active', ?)
        """, (alert_id, student_email, round(new_ccli, 4), severity, now))
        alert_details = {"alert_id": alert_id, "severity": severity, "status": "active"}

    elif new_status == "fatigued" and new_ccli < recovery_threshold:
        new_status = "normal"
        # Resolve active alerts
        cur.execute("""
            UPDATE cognitive_load_alerts
            SET status = 'resolved', resolved_at = ?, resolution_note = 'CCLI recovered below threshold.'
            WHERE student_email = ? AND status = 'active'
        """, (now, student_email))
        alert_details = {"status": "resolved"}

    # Save student state
    cur.execute("""
        INSERT INTO student_cognitive_load_state (
            student_email, rolling_il, rolling_el, rolling_gl, rolling_ccli, confidence, last_computed_at, alert_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(student_email) DO UPDATE SET
            rolling_il=excluded.rolling_il,
            rolling_el=excluded.rolling_el,
            rolling_gl=excluded.rolling_gl,
            rolling_ccli=excluded.rolling_ccli,
            confidence=excluded.confidence,
            last_computed_at=excluded.last_computed_at,
            alert_status=excluded.alert_status
    """, (
        student_email, round(new_il, 4), round(new_el, 4), round(new_gl, 4), round(new_ccli, 4),
        round(confidence, 3), now, new_status
    ))

    # Append to history ledger
    cur.execute("""
        INSERT INTO cognitive_load_history (student_email, old_ccli, new_ccli, alert_status, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (student_email, round(old_ccli, 4), round(new_ccli, 4), new_status, now))

    conn.commit()
    conn.close()

    return {
        "event_id": event_id,
        "student_email": student_email,
        "ccli": round(ccli, 4),
        "rolling_ccli": round(new_ccli, 4),
        "status": new_status,
        "alert_triggered": alert_details
    }


def get_student_load_state(student_email):
    """Fetches rolling states, active alerts, and history for a student."""
    conn = get_conn()
    cur = conn.cursor()
    state = None
    alerts = []
    history = []
    try:
        cur.execute("SELECT * FROM student_cognitive_load_state WHERE student_email = ?", (student_email,))
        row = cur.fetchone()
        if row:
            state = dict(row)

        cur.execute("SELECT * FROM cognitive_load_alerts WHERE student_email = ? ORDER BY created_at DESC", (student_email,))
        alerts = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM cognitive_load_history WHERE student_email = ? ORDER BY timestamp DESC LIMIT 20", (student_email,))
        history = [dict(r) for r in cur.fetchall()]
    except Exception:
        pass
    finally:
        conn.close()

    return {
        "student_email": student_email,
        "state": state,
        "alerts": alerts,
        "history": history
    }

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Subscribes to MemoryUpdated event.
    Calculates cognitive load and publishes CCLIUpdated.
    """
    payload = event_data["payload_json"]
    if isinstance(payload, str):
        import json
        payload = json.loads(payload)

    email = event_data["entity_id"]
    concept_id = payload.get("concept_id")
    question_id = payload.get("question_id")
    is_correct = payload.get("is_correct", False)

    # Defaults
    response_time = 45.0
    idle_time = 5.0
    rewrite_count = 0
    backspace_count = 0
    focus_lost_count = 0

    conn = get_conn()
    cur = conn.cursor()
    try:
        # Fetch latest response details
        if question_id:
            cur.execute("""
                SELECT response_time FROM responses
                WHERE student_email = ? AND question_id = ?
                ORDER BY id DESC LIMIT 1
            """, (email, question_id))
            r_row = cur.fetchone()
            if r_row:
                response_time = r_row["response_time"] or 45.0

        # Fetch latest derived behavior features
        cur.execute("""
            SELECT hesitation_index, focus_loss_count, correction_rate
            FROM derived_behavior_features
            WHERE student_email = ? AND concept_id = ?
            LIMIT 1
        """, (email, concept_id))
        f_row = cur.fetchone()
        if f_row:
            idle_time = (f_row["hesitation_index"] or 0.2) * response_time
            focus_lost_count = f_row["focus_loss_count"] or 0
            rewrite_count = int((f_row["correction_rate"] or 0.1) * 10)
    except Exception:
        pass
    finally:
        conn.close()

    compute_cognitive_load_state(
        email, concept_id, is_correct, response_time,
        idle_time, rewrite_count, backspace_count, focus_lost_count
    )

    if not is_replay or replay_mode == "LIVE":
        import event_bus
        event_bus.publish(
            event_type="CCLIUpdated",
            entity_type="student",
            entity_id=email,
            producer="ccli_engine",
            producer_version="v2.5.0",
            schema_version="v1.0",
            metadata_json=event_data.get("metadata_json", {}),
            payload_json={
                "concept_id": concept_id,
                "is_correct": is_correct
            }
        )
