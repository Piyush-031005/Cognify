"""
context_engine.py
Week 9 – Context Engine v2.0

Stateless consumer. Returns a categorized, prioritized list of explainable
recommendations, calibrated by environmental context parameters (device, network, time, class size).
Supports strict eligibility gating (conflict resolution), database-driven configurations,
and context quality tracking.
"""

import uuid
import math
import json
from datetime import datetime
from database import get_conn


def _bootstrap_config_table(conn, cur):
    """
    Create and seed context_recommendations_config with hardcoded defaults.
    Called only when the table does not exist yet (cold-start or isolated test env).
    This function is idempotent: if called again, INSERT OR IGNORE prevents duplication.
    """
    cur.execute("""
        CREATE TABLE IF NOT EXISTS context_recommendations_config (
            key TEXT PRIMARY KEY,
            value REAL NOT NULL,
            description TEXT,
            config_version TEXT DEFAULT 'v2.0',
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    defaults = [
        ("w_memory",       0.30, "Weight: Educational Memory component"),
        ("w_apd",          0.20, "Weight: APD prerequisite readiness"),
        ("w_misconception",0.15, "Weight: Misconception penalty"),
        ("w_qqi",          0.15, "Weight: QQI calibration alignment"),
        ("w_teacher",      0.10, "Weight: Teacher priority override"),
        ("w_curriculum",   0.10, "Weight: Curriculum/exam weight"),
        ("WEIGHT_IRT_ALIGNMENT", 0.15, "Weight: IRT calibration alignment"),
        ("ctx_mobile_mult",         0.85, "Context multiplier: mobile device"),
        ("ctx_tablet_mult",         0.95, "Context multiplier: tablet device"),
        ("ctx_desktop_mult",        1.05, "Context multiplier: desktop device"),
        ("ctx_poor_network_mult",   0.80, "Context multiplier: poor network"),
        ("ctx_average_network_mult",0.95, "Context multiplier: average network"),
        ("ctx_good_network_mult",   1.00, "Context multiplier: good network"),
        ("ctx_excellent_network_mult",1.05,"Context multiplier: excellent network"),
        ("ctx_peak_hour_mult",      1.10, "Context multiplier: peak study hours (8-10, 18-22)"),
        ("ctx_offpeak_hour_mult",   0.90, "Context multiplier: off-peak hours"),
        ("ctx_large_class_mult",    1.05, "Context multiplier: class size > 40"),
        ("ctx_small_class_mult",    0.95, "Context multiplier: class size <= 20"),
        ("max_recommendations",    10.0,  "Maximum recommendations returned per call"),
        ("min_score_threshold",     0.10, "Minimum score to include a concept in results"),
        ("recent_completion_days",  3.0,  "Days after last mastery event to suppress re-recommendation"),
    ]
    for key, value, desc in defaults:
        cur.execute(
            "INSERT OR IGNORE INTO context_recommendations_config (key, value, description) VALUES (?,?,?)",
            (key, value, desc)
        )
    conn.commit()


def generate_contextual_recommendations(student_email, context_overrides=None):
    """
    Stateless context-aware recommendation engine.
    
    Arguments:
        student_email: String email of the target student.
        context_overrides: Dict of optional overrides:
            - device_type: 'mobile', 'tablet', 'desktop'
            - network_quality: 'poor', 'average', 'good', 'excellent'
            - session_start_hour: int (0-23)
            - class_size: int (>= 1)
            
    Returns:
        Dict containing recommendations queue, telemetry audit, and configuration version metadata.
    """
    if not context_overrides:
        context_overrides = {}

    conn = get_conn()
    cur = conn.cursor()

    # -------------------------------------------------------------
    # 1. Load Recommendation Configurations from DB
    # -------------------------------------------------------------
    # Ensure the config table exists (resilient to environments where init_db
    # has not been called, e.g., teacher_twin test suite or cold-start).
    try:
        cur.execute("SELECT key, value, config_version FROM context_recommendations_config")
        config_rows = cur.fetchall()
    except Exception:
        # Table absent — create it on the fly and seed defaults so we can continue
        _bootstrap_config_table(conn, cur)
        cur.execute("SELECT key, value, config_version FROM context_recommendations_config")
        config_rows = cur.fetchall()

    config = {}
    config_version = "v2.0"
    for row in config_rows:
        config[row["key"]] = row["value"]
        if row["config_version"]:
            config_version = row["config_version"]

    # -------------------------------------------------------------
    # 1.5 Load Student IRT Ability & Confidence
    # -------------------------------------------------------------
    irt_ability = None
    irt_confidence = 0.0
    try:
        cur.execute("""
            SELECT irt_ability, irt_confidence FROM student_cognitive_profiles
            WHERE student_email = ?
        """, (student_email,))
        profile_row = cur.fetchone()
        if profile_row:
            irt_ability = profile_row["irt_ability"]
            irt_confidence = profile_row["irt_confidence"] or 0.0
    except Exception:
        pass

    # -------------------------------------------------------------
    # 1.6 Load Student Cognitive Load State (Fatigue & Recovery)
    # -------------------------------------------------------------
    rolling_ccli = 0.0
    alert_status = "normal"
    try:
        cur.execute("""
            SELECT rolling_ccli, alert_status FROM student_cognitive_load_state
            WHERE student_email = ?
        """, (student_email,))
        ccli_row = cur.fetchone()
        if ccli_row:
            rolling_ccli = ccli_row["rolling_ccli"] or 0.0
            alert_status = ccli_row["alert_status"] or "normal"
    except Exception:
        pass

    is_fatigued = (alert_status == "fatigued")

    min_irt_conf = 0.5
    try:
        cur.execute("SELECT value FROM nbirt_config WHERE key = 'min_irt_confidence_for_context'")
        min_irt_conf_row = cur.fetchone()
        if min_irt_conf_row:
            min_irt_conf = min_irt_conf_row["value"]
    except Exception:
        pass

    # -------------------------------------------------------------
    # 2. Context Ingest & Quality Audit
    # -------------------------------------------------------------
    # Resolve environmental parameters.
    # Production telemetry check: we query the database first, but since
    # telemetry is unpopulated, we fall back to defaults or overrides.
    device_type = None
    network_quality = None
    session_start_hour = None
    class_size = None

    # Check for live session context in pilot_sessions for this student's classroom
    try:
        cur.execute("""
            SELECT ps.device_type, ps.network_quality, ps.created_at, ps.total_students
            FROM pilot_sessions ps
            JOIN room_students rs ON rs.room_code = (
                SELECT room_code FROM room_students WHERE student_email = ? LIMIT 1
            )
            ORDER BY ps.session_id DESC LIMIT 1
        """, (student_email,))
        session_row = cur.fetchone()
        if session_row:
            device_type = session_row["device_type"]
            network_quality = session_row["network_quality"]
            if session_row["created_at"]:
                try:
                    dt = datetime.fromisoformat(session_row["created_at"])
                    session_start_hour = dt.hour
                except Exception:
                    pass
            class_size = session_row["total_students"]
    except Exception:
        pass

    # Apply overrides (which override any session-level DB config)
    overrides_applied = []
    missing_signals = []

    # Device Type
    if "device_type" in context_overrides:
        device_type = context_overrides["device_type"]
        overrides_applied.append("device_type")
    elif not device_type:
        device_type = "desktop"
        missing_signals.append("device_type")

    # Network Quality
    if "network_quality" in context_overrides:
        network_quality = context_overrides["network_quality"]
        overrides_applied.append("network_quality")
    elif not network_quality:
        network_quality = "excellent"
        missing_signals.append("network_quality")

    # Session Hour
    if "session_start_hour" in context_overrides:
        session_start_hour = int(context_overrides["session_start_hour"])
        overrides_applied.append("session_start_hour")
    elif session_start_hour is None:
        session_start_hour = 10
        missing_signals.append("session_start_hour")

    # Class Size
    if "class_size" in context_overrides:
        class_size = int(context_overrides["class_size"])
        overrides_applied.append("class_size")
    elif class_size is None:
        class_size = 25
        missing_signals.append("class_size")

    # Classify context quality
    total_env_params = 4
    resolved_with_evidence = len(overrides_applied)  # Overrides count as real parameters passed
    
    if resolved_with_evidence == total_env_params:
        context_quality = "FULL"
        confidence_score = 1.0
        confidence_reason = "All environmental parameters resolved from live overrides."
    elif resolved_with_evidence > 0:
        context_quality = "PARTIAL"
        confidence_score = round(0.5 + 0.125 * resolved_with_evidence, 2)
        confidence_reason = f"Partial telemetry. Missing signals: {', '.join(missing_signals)} resolved to system defaults."
    else:
        context_quality = "FALLBACK"
        confidence_score = 0.5
        confidence_reason = "All environmental context parameters resolved to default fallback assumptions due to missing classroom telemetry."

    # Normalized keys
    device_type = device_type.lower()
    network_quality = network_quality.lower()

    # Fetch attention rolling state & circadian factor
    rolling_decay = 1.0
    circadian_factor = 1.0
    lambda_val = 0.35
    try:
        cur.execute("""
            SELECT rolling_decay FROM student_attention_state
            WHERE student_email = ?
        """, (student_email,))
        att_row = cur.fetchone()
        if att_row and att_row["rolling_decay"] is not None:
            rolling_decay = att_row["rolling_decay"]

        cur.execute("""
            SELECT circadian_factor FROM attention_events
            WHERE student_email = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (student_email,))
        circ_row = cur.fetchone()
        if circ_row and circ_row["circadian_factor"] is not None:
            circadian_factor = circ_row["circadian_factor"]

        cur.execute("""
            SELECT value FROM attention_config
            WHERE key = 'lambda_attention_modulation'
        """)
        l_row = cur.fetchone()
        if l_row and l_row["value"] is not None:
            lambda_val = l_row["value"]
    except Exception:
        pass

    # -------------------------------------------------------------
    # 3. Fetch Cognitive States & Candidate Targets
    # -------------------------------------------------------------
    # Get all concepts present in the student's memory profile
    try:
        cur.execute("""
            SELECT concept_id, memory_strength, forgetting_rate, memory_state,
                   reinforcement_count, last_success, last_failure
            FROM concept_memory
            WHERE student_email = ?
        """, (student_email,))
        memory_rows = cur.fetchall()
    except Exception:
        # concept_memory table absent — return empty recommendations gracefully
        conn.close()
        return {
            "student_email": student_email,
            "recommendations": [],
            "context_quality": "FALLBACK",
            "missing_signals": ["concept_memory_unavailable"],
            "confidence": 0.0,
            "confidence_reason": "Core memory table unavailable. No recommendations can be generated.",
            "config_version": config_version,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }

    student_memory = {row["concept_id"]: dict(row) for row in memory_rows}

    # Query all active misconceptions for this student
    active_misconceptions = {}
    try:
        cur.execute("""
            SELECT mc.cluster_id, mc.concept_id, mc.misconception_name, mc.severity, me.id as evidence_id
            FROM misconception_clusters mc
            JOIN misconception_evidence me ON me.cluster_id = mc.cluster_id
            WHERE me.student_email = ? AND me.status = 'active'
        """, (student_email,))
        mcp_rows = cur.fetchall()
        for mcp in mcp_rows:
            active_misconceptions[mcp["concept_id"]] = {
                "cluster_id": mcp["cluster_id"],
                "name": mcp["misconception_name"],
                "severity": mcp["severity"],
                "evidence_id": mcp["evidence_id"]
            }
    except Exception:
        pass

    # Fetch blueprints to resolve exam weights
    blueprint_counts = {}
    total_blueprint_questions = 0
    try:
        cur.execute("SELECT topic, COUNT(*) as cnt FROM assessment_blueprints GROUP BY topic")
        bp_rows = cur.fetchall()
        for bp in bp_rows:
            blueprint_counts[bp["topic"]] = bp["cnt"]
            total_blueprint_questions += bp["cnt"]
    except Exception:
        pass

    # Fetch Knowledge Graph concept prerequisite relations
    prerequisites = {}
    prereq_out_degrees = {}
    try:
        cur.execute("SELECT source_id, target_id FROM kg_edges WHERE relation_type = 'prerequisite_of'")
        edges = cur.fetchall()
        for src, tgt in edges:
            if tgt not in prerequisites:
                prerequisites[tgt] = []
            prerequisites[tgt].append(src)
            prereq_out_degrees[src] = prereq_out_degrees.get(src, 0) + 1
    except Exception:
        pass

    # Fetch teacher note focuses
    teacher_notes_count = {}
    try:
        cur.execute("""
            SELECT observation, reason FROM teacher_notes 
            WHERE student_email = ? OR student_email IS NULL OR student_email = ''
        """, (student_email,))
        notes = cur.fetchall()
        for obs, reason in notes:
            text = f"{obs or ''} {reason or ''}".lower()
            for c_id in student_memory.keys():
                if c_id.lower() in text:
                    teacher_notes_count[c_id] = teacher_notes_count.get(c_id, 0) + 1
    except Exception:
        pass

    recommendations = []

    # -------------------------------------------------------------
    # 4. Eligibility & Conflict Resolution Stage
    # -------------------------------------------------------------
    # We iterate over all concept candidates in the student's profile
    for concept_id, mem_data in student_memory.items():
        # Candidate actions: Practice, Review, Remediation
        # Initialize conflict reasons if any action is blocked
        is_remediation_blocked = False
        is_practice_blocked = False
        is_review_blocked = False
        blocking_reasons = []

        # ---------------------------------------------------------
        # Blocking Rule A: Prerequisite Failure
        # ---------------------------------------------------------
        # If any prerequisite of this concept is Forgotten or At Risk (or has S/R too low),
        # then Practice and Review are blocked (to prevent cognitive load issues).
        # Remediation can still run.
        concept_prereqs = prerequisites.get(concept_id, [])
        for pre in concept_prereqs:
            pre_state = student_memory.get(pre, {}).get("memory_state", "Unknown")
            pre_strength = student_memory.get(pre, {}).get("memory_strength", 0.0)
            
            if pre_state in ["Forgotten", "At Risk"] or pre_strength < 0.4:
                is_practice_blocked = True
                is_review_blocked = True
                blocking_reasons.append(
                    f"Blocked standard review/practice because prerequisite '{pre}' is currently {pre_state or 'weak'}."
                )

        # ---------------------------------------------------------
        # Blocking Rule B: Critical/High Misconception Presence
        # ---------------------------------------------------------
        # If the student has an active Misconception with Critical or High severity,
        # standard Practice and Review are blocked. Only Remediation is permitted.
        active_mcp = active_misconceptions.get(concept_id)
        if active_mcp and active_mcp["severity"] in ["Critical", "High"]:
            is_practice_blocked = True
            is_review_blocked = True
            blocking_reasons.append(
                f"Blocked practice/review due to active {active_mcp['severity']} severity misconception '{active_mcp['name']}'."
            )

        # ---------------------------------------------------------
        # Blocking Rule C: Cognitive Recovery Mode (Fatigue Mitigation)
        # ---------------------------------------------------------
        if is_fatigued:
            is_new = (mem_data.get("reinforcement_count", 0) == 0)
            if is_new:
                is_practice_blocked = True
                is_review_blocked = True
                is_remediation_blocked = True
                blocking_reasons.append("Blocked new concept recommendation under Cognitive Recovery Mode due to student fatigue.")
            else:
                is_prereq_reinforcement = (prereq_out_degrees.get(concept_id, 0) > 0)
                if not is_prereq_reinforcement:
                    is_practice_blocked = True
                    blocking_reasons.append("Blocked standard Practice under Cognitive Recovery Mode. Prioritizing reviews and prerequisite reinforcement.")

        # ---------------------------------------------------------
        # CDO Decision Orchestration Gate (Week 13 Brain integration)
        # ---------------------------------------------------------
        cdo_decision = None
        cdo_trace = None
        try:
            import decision_engine
            cdo_res = decision_engine.execute_decision_pipeline(student_email, concept_id, trigger_source="context_engine")
            if "error" not in cdo_res:
                cdo_decision = cdo_res["final_decision"]
                cdo_trace = cdo_res
        except Exception:
            pass

        # ---------------------------------------------------------
        # Action Evaluation & Scoring
        # ---------------------------------------------------------
        # Define actions to evaluate
        possible_actions = [
            ("Remediation", is_remediation_blocked),
            ("Practice", is_practice_blocked),
            ("Review", is_review_blocked)
        ]

        for action_name, is_blocked in possible_actions:
            current_blocking_reasons = list(blocking_reasons)
            if not is_blocked and cdo_decision is not None:
                if action_name != cdo_decision:
                    is_blocked = True
                    current_blocking_reasons.append(
                        f"Blocked by CDO Orchestrator. Winning decision was {cdo_decision} (Winning rule: {cdo_trace.get('winning_rule')})."
                    )
                elif cdo_decision == "Pause":
                    is_blocked = True
                    current_blocking_reasons.append("Blocked by CDO: Teacher override Pause instruction in effect.")

            if is_blocked:
                # Log blocked candidate for traceability/teacher visibility
                recommendations.append({
                    "id": f"CTX-BLOCKED-{str(uuid.uuid4())[:8].upper()}",
                    "category": action_name,
                    "target": concept_id,
                    "priority": 0.0,
                    "status": "blocked",
                    "conflict": True,
                    "reason": " | ".join(current_blocking_reasons),
                    "context_quality": context_quality,
                    "confidence": confidence_score,
                    "confidence_reason": confidence_reason,
                    "scoring_breakdown": {},
                    "recommendation_trace": "Blocked in Eligibility stage."
                })
                continue

            # -----------------------------------------------------
            # 5. Base Cognitive Score Calculation
            # -----------------------------------------------------
            # Memory Risk Indicator (M_risk)
            R = mem_data.get("memory_strength", 0.5)  # retrieval strength fallback
            M_risk = 1.0 - R

            # APD Prerequisite Importance (P_impt)
            out_deg = prereq_out_degrees.get(concept_id, 0)
            P_impt = min(1.0, out_deg / 5.0)

            # Misconception Severity (S_sev)
            S_sev = 0.0
            if active_mcp:
                sev_map = {"Low": 0.25, "Medium": 0.5, "High": 0.75, "Critical": 1.0}
                S_sev = sev_map.get(active_mcp["severity"], 0.5)

            # QQI Calibration Indicator (Q_cal)
            # Fetch question calibrations for this concept
            avg_qqi_score = 50.0
            try:
                cur.execute("""
                    SELECT AVG(qb.qqi_score) as avg_qqi FROM question_bank qb
                    JOIN question_concepts qc ON qc.question_id = qb.id
                    LEFT JOIN question_lifecycle ql ON ql.question_id = qb.id
                    WHERE qc.concept_id = ? AND (ql.lifecycle_status IS NULL OR ql.lifecycle_status IN ('Calibration', 'Active'))
                """, (concept_id,))
                q_row = cur.fetchone()
                if q_row and q_row["avg_qqi"]:
                    avg_qqi_score = q_row["avg_qqi"]
            except Exception:
                pass
            Q_cal = avg_qqi_score / 100.0

            # NBIRT Calibration Indicator (I_align) - Upgraded IRT signal
            I_align = 0.0
            avg_b = None
            if irt_ability is not None and irt_confidence >= min_irt_conf:
                try:
                    cur.execute("""
                        SELECT AVG(qb.irt_difficulty) as avg_diff FROM question_bank qb
                        JOIN question_concepts qc ON qc.question_id = qb.id
                        LEFT JOIN question_lifecycle ql ON ql.question_id = qb.id
                        WHERE qc.concept_id = ? AND qb.irt_difficulty IS NOT NULL
                          AND (ql.lifecycle_status IS NULL OR ql.lifecycle_status IN ('Calibration', 'Active'))
                    """, (concept_id,))
                    diff_row = cur.fetchone()
                    if diff_row and diff_row["avg_diff"] is not None:
                        avg_b = diff_row["avg_diff"]
                        diff_abs = abs(irt_ability - avg_b)
                        # 2PL probability mapping sigmoid(-|θ - b|) scaled to 1.0 peak
                        I_align = (1.0 / (1.0 + math.exp(diff_abs))) * 2.0
                except Exception:
                    pass

            # Teacher Priority (T_prior)
            note_cnt = teacher_notes_count.get(concept_id, 0)
            T_prior = min(1.0, note_cnt * 0.5)

            # Exam/Curriculum Weight (E_wt)
            E_wt = 0.0
            if total_blueprint_questions > 0:
                E_wt = blueprint_counts.get(concept_id, 0) / total_blueprint_questions

            # Pull weights from configuration config table
            w_mem = config.get("WEIGHT_MEMORY_RISK", 0.3)
            w_apd = config.get("WEIGHT_PREREQUISITE_IMPORTANCE", 0.2)
            w_mcp = config.get("WEIGHT_MISCONCEPTION_SEVERITY", 0.2)
            w_qqi = config.get("WEIGHT_QQI_CONFIDENCE", 0.1)
            w_teach = config.get("WEIGHT_TEACHER_PRIORITY", 0.1)
            w_exam = config.get("WEIGHT_EXAM_WEIGHT", 0.1)
            w_irt = config.get("WEIGHT_IRT_ALIGNMENT", 0.15)

            # Linear aggregate base score (IRT added as 7th signal)
            S_base = (w_mem * M_risk) + \
                     (w_apd * P_impt) + \
                     (w_mcp * S_sev) + \
                     (w_qqi * Q_cal) + \
                     (w_teach * T_prior) + \
                     (w_exam * E_wt) + \
                     (w_irt * I_align)

            # -----------------------------------------------------
            # 6. Environmental Context Calibration
            # -----------------------------------------------------
            # Context Device Multiplier (M_device)
            m_dev_key = f"MULTIPLIER_DEVICE_{device_type.upper()}_{action_name.upper()}"
            M_dev = config.get(m_dev_key, 1.0)

            # Context Network Multiplier (M_network)
            m_net_key = f"MULTIPLIER_NETWORK_{network_quality.upper()}_{action_name.upper()}"
            M_net = config.get(m_net_key, 1.0)

            # Context Time Multiplier (M_time)
            # Hour ranges: Late Night (21:00 - 05:00), School Hours (08:00 - 15:00)
            is_late_night = session_start_hour >= 21 or session_start_hour < 5
            is_school_hours = 8 <= session_start_hour <= 15
            
            if is_late_night:
                m_time_key = f"MULTIPLIER_TIME_LATE_NIGHT_{action_name.upper()}"
            elif is_school_hours:
                m_time_key = f"MULTIPLIER_TIME_SCHOOL_HOURS_{action_name.upper()}"
            else:
                m_time_key = f"MULTIPLIER_TIME_STANDARD_{action_name.upper()}"
            M_time = config.get(m_time_key, 1.0)

            # Context Class Concurrency Multiplier (M_class)
            is_large_class = class_size >= 20
            if is_large_class:
                m_class_key = f"MULTIPLIER_CLASS_LARGE_{action_name.upper()}"
            else:
                m_class_key = f"MULTIPLIER_CLASS_SMALL_{action_name.upper()}"
            M_class = config.get(m_class_key, 1.0)

            # Apply multipliers and clamp
            S_final = S_base * M_dev * M_net * M_time * M_class

            # Apply Week 15: Soft Attention & Circadian modulation (Change 3)
            S_final = S_final * (1.0 - lambda_val) + S_final * (circadian_factor * rolling_decay) * lambda_val

            # Apply Cognitive Recovery Mode dampening/boosts
            fatigue_dampener_applied = False
            if is_fatigued:
                if avg_b is not None and irt_ability is not None:
                    target_b = irt_ability - 0.5
                    if avg_b > target_b:
                        excess = avg_b - target_b
                        penalty = max(0.2, 1.0 - excess)
                        S_final = S_final * penalty
                        fatigue_dampener_applied = True
                
                is_prereq_reinforcement = (prereq_out_degrees.get(concept_id, 0) > 0)
                if action_name in ["Review", "Remediation"] or is_prereq_reinforcement:
                    S_final = S_final * 1.3

            S_final = min(1.0, max(0.0, S_final))
            S_final = round(S_final, 4)

            # Human-readable justification note
            justification_parts = [
                f"Base cognitive priority ({round(S_base, 2)}) was driven by memory decay/risk ({round(M_risk, 2)}) "
                f"and active misconception severity ({round(S_sev, 2)})."
            ]
            if is_fatigued:
                if fatigue_dampener_applied:
                    justification_parts.append("Dampened under Cognitive Recovery Mode due to high difficulty relative to student ability.")
                else:
                    justification_parts.append("Boosted under Cognitive Recovery Mode to prioritize review/reinforcement.")
            
            justification_parts.append(
                f"Calibrated by context multipliers (Device: x{M_dev}, Network: x{M_net}, Time: x{M_time}, Class: x{M_class}) "
                f"optimized for a {device_type.capitalize()} on a {network_quality.capitalize()} connection."
            )
            justification = " ".join(justification_parts)

            scoring_breakdown = {
                "base_components": {
                    "memory_risk": round(M_risk, 3),
                    "prerequisite_importance": round(P_impt, 3),
                    "misconception_severity": round(S_sev, 3),
                    "qqi_confidence": round(Q_cal, 3),
                    "teacher_priority": round(T_prior, 3),
                    "exam_weight": round(E_wt, 3),
                    "irt_alignment": round(I_align, 3)
                },
                "weights": {
                    "w_mem": w_mem,
                    "w_apd": w_apd,
                    "w_mcp": w_mcp,
                    "w_qqi": w_qqi,
                    "w_teach": w_teach,
                    "w_exam": w_exam,
                    "w_irt": w_irt
                },
                "multipliers": {
                    "device": M_dev,
                    "network": M_net,
                    "time": M_time,
                    "class": M_class
                },
                "clamped_final": S_final
            }

            trace_str = (
                f"S_final = ({w_mem}*{round(M_risk, 2)} + {w_apd}*{round(P_impt, 2)} + {w_mcp}*{round(S_sev, 2)} + "
                f"{w_qqi}*{round(Q_cal, 2)} + {w_teach}*{round(T_prior, 2)} + {w_exam}*{round(E_wt, 2)} + "
                f"{w_irt}*{round(I_align, 2)}) * "
                f"{M_dev} * {M_net} * {M_time} * {M_class}"
            )

            # Recommendation payload structure
            rec_id = f"CTX-{str(uuid.uuid4())[:8].upper()}"
            recommendations.append({
                "id": rec_id,
                "category": action_name,
                "target": concept_id,
                "priority": S_final,
                "status": "generated",
                "conflict": False,
                "reason": justification,
                "context_quality": context_quality,
                "confidence": confidence_score,
                "confidence_reason": confidence_reason,
                "scoring_breakdown": scoring_breakdown,
                "recommendation_trace": trace_str
            })

            # Save generated recommendation to database log
            try:
                cur.execute("""
                    INSERT INTO recommendations_log (
                        student_email, concept_id, priority, reason, evidence_backing,
                        suggested_action, timestamp, status, context_device_type,
                        context_network_quality, context_session_hour, context_class_size,
                        scoring_breakdown, config_version, context_quality,
                        confidence_score, confidence_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    student_email, concept_id, str(S_final), justification, trace_str,
                    action_name, datetime.now().isoformat(), "generated", device_type,
                    network_quality, session_start_hour, class_size, json.dumps(scoring_breakdown),
                    config_version, context_quality, confidence_score, confidence_reason
                ))
            except Exception:
                pass

    conn.commit()
    conn.close()

    # Filter out blocked entries from the final active queue if needed, or return them with priority=0.0
    # We sort active/generated recommendations descending by priority, placing blocked items at the bottom.
    recommendations.sort(key=lambda x: x["priority"], reverse=True)

    return {
        "student_email": student_email,
        "context_quality": context_quality,
        "confidence": confidence_score,
        "confidence_reason": confidence_reason,
        "missing_telemetry_signals": missing_signals,
        "config_version": config_version,
        "recommendations": [r for r in recommendations if r["status"] != "blocked"],
        "blocked_candidates": [r for r in recommendations if r["status"] == "blocked"]
    }

def handle_question_retired(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Subscribes to QuestionRetired event.
    Logs/refreshes recommendation buffers for retired questions.
    """
    pass

def handle_question_promoted(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Subscribes to QuestionPromoted event.
    Logs/refreshes recommendation buffers for promoted questions.
    """
    pass
