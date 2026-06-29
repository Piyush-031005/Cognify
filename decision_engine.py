"""
decision_engine.py
Week 13 – Cognitive Decision Orchestrator (CDO)
Decoupled Rule Object Pipeline for deterministic conflict resolution,
consensus confidence, and decision explainability.
"""

import json
import uuid
from datetime import datetime
from database import get_conn


# =============================================================================
# DECISION ENGINE CONFIGURATION
# =============================================================================

def _load_cdo_priorities():
    """Loads rule priorities from decision_config table."""
    priorities = {
        "TeacherRule": 100.0,
        "LoadRule": 90.0,
        "MisconceptionRule": 80.0,
        "APDRule": 70.0,
        "MemoryRule": 60.0,
        "NBIRTRule": 50.0
    }
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT key, value FROM decision_config")
        rows = cur.fetchall()
        for r in rows:
            # Map database keys (e.g. priority_rule_teacher) to Class Names
            key = r["key"].lower()
            if "teacher" in key:
                priorities["TeacherRule"] = r["value"]
            elif "load" in key:
                priorities["LoadRule"] = r["value"]
            elif "misconception" in key:
                priorities["MisconceptionRule"] = r["value"]
            elif "apd" in key:
                priorities["APDRule"] = r["value"]
            elif "memory" in key:
                priorities["MemoryRule"] = r["value"]
            elif "nbirt" in key:
                priorities["NBIRTRule"] = r["value"]
    except Exception:
        pass
    finally:
        conn.close()
    return priorities


def get_cdo_config():
    """Returns active config values."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT key, value, config_version, updated_by, updated_at FROM decision_config")
        rows = [dict(r) for r in cur.fetchall()]
    except Exception:
        rows = []
    finally:
        conn.close()
    return rows


def update_cdo_config(key, value, updated_by="teacher"):
    """Updates a decision config parameter."""
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cur.execute("""
            INSERT INTO decision_config (key, value, config_version, updated_by, updated_at)
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
# MODULAR RULE OBJECTS
# =============================================================================

class TeacherRule:
    def evaluate(self, student_email, concept_id, cur):
        cur.execute("""
            SELECT observation, reason FROM teacher_notes
            WHERE (student_email = ? OR student_email IS NULL OR student_email = '')
        """, (student_email,))
        notes = cur.fetchall()
        for note in notes:
            obs = (note["observation"] or "").lower()
            reason = (note["reason"] or "").lower()
            text = f"{obs} {reason}"
            if concept_id.lower() in text:
                if any(x in text for x in ["block", "pause", "hold", "stop"]):
                    return {
                        "action": "Pause",
                        "confidence": 1.0,
                        "reason": f"Teacher Override: note matches concept '{concept_id}' with blocking intent.",
                        "parameters_used": {"observation": note["observation"], "reason": note["reason"]}
                    }
        return None


class LoadRule:
    def evaluate(self, student_email, concept_id, cur):
        cur.execute("""
            SELECT rolling_il, rolling_el, rolling_gl, rolling_ccli, alert_status
            FROM student_cognitive_load_state WHERE student_email = ?
        """, (student_email,))
        row = cur.fetchone()
        if row and row["alert_status"] == "fatigued":
            return {
                "action": "Review",
                "confidence": float(row["rolling_ccli"] or 0.8),
                "reason": f"Cognitive Recovery Mode: student is fatigued (CCLI = {row['rolling_ccli']}).",
                "parameters_used": {
                    "rolling_il": row["rolling_il"],
                    "rolling_el": row["rolling_el"],
                    "rolling_gl": row["rolling_gl"],
                    "rolling_ccli": row["rolling_ccli"]
                }
            }
        return None


class MisconceptionRule:
    def evaluate(self, student_email, concept_id, cur):
        cur.execute("""
            SELECT me.evidence_id, mc.severity, mc.misconception_name
            FROM misconception_evidences me
            JOIN misconception_clusters mc ON mc.evidence_id = me.evidence_id
            WHERE me.student_email = ? AND me.concept_id = ? AND me.status = 'active'
            ORDER BY CASE mc.severity
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
                ELSE 5
            END LIMIT 1
        """, (student_email, concept_id))
        row = cur.fetchone()
        if row:
            return {
                "action": "Remediation",
                "confidence": 1.0,
                "reason": f"Active Misconception: '{row['misconception_name']}' ({row['severity']}).",
                "parameters_used": {
                    "evidence_id": row["evidence_id"],
                    "severity": row["severity"],
                    "misconception_name": row["misconception_name"]
                }
            }
        return None


class APDRule:
    def evaluate(self, student_email, concept_id, cur):
        # Fetch prerequisites of the target concept
        cur.execute("""
            SELECT source_id FROM kg_edges
            WHERE target_id = ? AND relation_type = 'prerequisite_of'
        """, (concept_id,))
        prereqs = [r["source_id"] for r in cur.fetchall()]

        for pre in prereqs:
            cur.execute("""
                SELECT memory_strength, memory_state FROM concept_memory
                WHERE student_email = ? AND concept_id = ?
            """, (student_email, pre))
            mem = cur.fetchone()
            if mem:
                state = mem["memory_state"]
                strength = mem["memory_strength"] or 0.0
                if state in ["Forgotten", "At Risk"] or strength < 0.4:
                    return {
                        "action": "Remediation",
                        "confidence": 0.8,
                        "reason": f"Unmet Prerequisite: '{pre}' is {state} (strength: {strength}).",
                        "parameters_used": {
                            "prerequisite_concept": pre,
                            "memory_state": state,
                            "memory_strength": strength
                        }
                    }
        return None


class MemoryRule:
    def evaluate(self, student_email, concept_id, cur):
        cur.execute("""
            SELECT memory_strength, memory_state FROM concept_memory
            WHERE student_email = ? AND concept_id = ?
        """, (student_email, concept_id))
        row = cur.fetchone()
        if row:
            state = row["memory_state"]
            strength = row["memory_strength"] or 0.5
            if state in ["Forgotten", "At Risk"] or strength < 0.4:
                return {
                    "action": "Review",
                    "confidence": round(1.0 - strength, 3),
                    "reason": f"Memory Decay: concept trace is {state} (strength: {strength}).",
                    "parameters_used": {
                        "memory_state": state,
                        "memory_strength": strength
                    }
                }
        return None


class NBIRTRule:
    def evaluate(self, student_email, concept_id, cur):
        cur.execute("""
            SELECT irt_ability, irt_confidence FROM student_cognitive_profiles
            WHERE student_email = ?
        """, (student_email,))
        row = cur.fetchone()
        if row and row["irt_ability"] is not None:
            return {
                "action": "Practice",
                "confidence": float(row["irt_confidence"] or 0.6),
                "reason": f"Ability Calibrated: aligned Practice matching theta = {row['irt_ability']}.",
                "parameters_used": {
                    "irt_ability": row["irt_ability"],
                    "irt_confidence": row["irt_confidence"]
                }
            }
        return {
            "action": "Practice",
            "confidence": 0.5,
            "reason": "Default Exploration: student ability not yet calibrated.",
            "parameters_used": {}
        }


# =============================================================================
# ORCHESTRATOR EXECUTION ENGINE
# =============================================================================

def execute_decision_pipeline(student_email, concept_id, trigger_source="api"):
    """
    Runs all rule objects, resolves conflicts based on database priority mapping,
    logs candidates and conflicts, and returns the final decision trace.
    """
    priorities = _load_cdo_priorities()
    rules = {
        "TeacherRule": TeacherRule(),
        "LoadRule": LoadRule(),
        "MisconceptionRule": MisconceptionRule(),
        "APDRule": APDRule(),
        "MemoryRule": MemoryRule(),
        "NBIRTRule": NBIRTRule()
    }

    conn = get_conn()
    cur = conn.cursor()

    candidates = []

    # 1. Run all rule objects
    for rule_name, rule_obj in rules.items():
        try:
            res = rule_obj.evaluate(student_email, concept_id, cur)
            if res and res.get("action"):
                priority = priorities.get(rule_name, 50.0)
                candidates.append({
                    "rule_name": rule_name,
                    "action": res["action"],
                    "priority": priority,
                    "confidence": res["confidence"],
                    "reason": res["reason"],
                    "parameters_used": res["parameters_used"]
                })
        except Exception as e:
            # Resilient to failures in individual rules
            pass

    if not candidates:
        conn.close()
        return {"error": "No candidates generated by any decision rule."}

    # 2. Sort candidates descending by Priority
    candidates.sort(key=lambda x: x["priority"], reverse=True)

    # 3. Resolve conflicts
    winning_candidate = candidates[0]
    final_decision = winning_candidate["action"]
    confidence_score = winning_candidate["confidence"]
    winning_rule = winning_candidate["rule_name"]
    decision_reason = winning_candidate["reason"]

    # Losing candidates are conflicts
    conflicts = [c for c in candidates if c != winning_candidate]

    # Calculate Decision Stability
    # Filter conflicts that recommend a DIFFERENT action from the winning action
    conflicting_candidates = [c for c in conflicts if c["action"] != final_decision]
    if conflicting_candidates:
        max_alt_conf = max(c["confidence"] for c in conflicting_candidates)
        if confidence_score > 0.0:
            stability_score = max(0.0, min(1.0, 1.0 - (max_alt_conf / confidence_score)))
        else:
            stability_score = 0.0
    else:
        stability_score = 1.0

    # Classify stability level
    if stability_score >= 0.7:
        decision_stability = "HIGH"
    elif stability_score >= 0.4:
        decision_stability = "MEDIUM"
    else:
        decision_stability = "LOW"

    run_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    policy_version = "v1.0"

    # 4. Save audit log to database inside a single transaction
    try:
        cur.execute("""
            INSERT INTO decision_runs (
                run_id, student_email, concept_id, final_decision,
                confidence_score, decision_stability, stability_score,
                decision_policy_version, trigger_source, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, student_email, concept_id, final_decision,
            round(confidence_score, 3), decision_stability, round(stability_score, 3),
            policy_version, trigger_source, now
        ))

        cur.execute("""
            INSERT INTO decision_explanations (
                run_id, student_email, concept_id, winning_rule,
                candidates_json, conflicts_json, decision_reason,
                decision_stability, stability_score, decision_policy_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, student_email, concept_id, winning_rule,
            json.dumps(candidates), json.dumps(conflicts), decision_reason,
            decision_stability, round(stability_score, 3), policy_version
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"error": f"Failed to save decision records: {str(e)}"}

    conn.close()

    return {
        "run_id": run_id,
        "student_email": student_email,
        "concept_id": concept_id,
        "final_decision": final_decision,
        "confidence_score": round(confidence_score, 3),
        "decision_stability": decision_stability,
        "stability_score": round(stability_score, 3),
        "winning_rule": winning_rule,
        "decision_reason": decision_reason,
        "candidates": candidates,
        "conflicts": conflicts,
        "policy_version": policy_version,
        "timestamp": now
    }


def get_student_decision_state(student_email):
    """Fetches the latest decision and history trace logs for a student."""
    conn = get_conn()
    cur = conn.cursor()
    latest_decision = None
    history = []
    try:
        cur.execute("""
            SELECT dr.*, de.winning_rule, de.candidates_json, de.conflicts_json, de.decision_reason
            FROM decision_runs dr
            JOIN decision_explanations de ON de.run_id = dr.run_id
            WHERE dr.student_email = ?
            ORDER BY dr.timestamp DESC LIMIT 1
        """, (student_email,))
        row = cur.fetchone()
        if row:
            latest_decision = dict(row)
            latest_decision["candidates_json"] = json.loads(latest_decision["candidates_json"])
            latest_decision["conflicts_json"] = json.loads(latest_decision["conflicts_json"])

        cur.execute("""
            SELECT run_id, concept_id, final_decision, confidence_score, timestamp
            FROM decision_runs WHERE student_email = ?
            ORDER BY timestamp DESC LIMIT 20
        """, (student_email,))
        history = [dict(r) for r in cur.fetchall()]
    except Exception:
        pass
    finally:
        conn.close()

    return {
        "student_email": student_email,
        "latest_decision": latest_decision,
        "history": history
    }

def handle_attention_updated(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Subscribes to AttentionUpdated event.
    Evaluates CDO rules conflict resolution and publishes DecisionGenerated.
    """
    payload = event_data["payload_json"]
    if isinstance(payload, str):
        import json
        payload = json.loads(payload)

    email = event_data["entity_id"]
    concept_id = payload.get("concept_id")

    if email and concept_id:
        execute_decision_pipeline(email, concept_id)

    if not is_replay or replay_mode == "LIVE":
        import event_bus
        event_bus.publish(
            event_type="DecisionGenerated",
            entity_type="student",
            entity_id=email,
            producer="cdo_engine",
            producer_version="v2.5.0",
            schema_version="v1.0",
            metadata_json=event_data.get("metadata_json", {}),
            payload_json={
                "concept_id": concept_id
            }
        )
