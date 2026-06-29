"""
question_lifecycle_engine.py
Week 16 – Question Blueprint Intelligence & Lifecycle Engine (QBL)
Handles question lineages, blueprint inheritance, drift calculations, and lifecycle transitions.
"""

import json
from datetime import datetime
from database import get_conn


# =============================================================================
# LIFECYCLE CREATION & PROMOTION
# =============================================================================

def create_question_version(
    blueprint_id, family_id, derived_from_question_id,
    prompt, option_a, option_b, option_c, option_d, correct_index, explanation,
    subject="math", topic="algebra", subtopic="equations", difficulty="medium",
    cognitive_type="application", tags=None, created_by="system"
):
    """
    Creates a new question version, populates question_bank, computes lineage/ancestor paths,
    inherits psychometric priors, and initializes lifecycle status to 'Draft' or 'Pilot'.
    """
    conn = get_conn()
    cur = conn.cursor()

    try:
        now = datetime.now().isoformat()

        # 1. Initialize inherited parameters
        expected_solve_time = 120.0
        difficulty_prior = 0.0
        discrimination_prior = 1.0
        guessing_prior = 0.0
        root_blueprint_id = blueprint_id
        generation = 1
        lineage_depth = 1
        parent_ancestor_path = ""

        # Fetch blueprint info if specified
        blueprint_version = "v1.0"
        if blueprint_id:
            cur.execute("""
                SELECT concept_id, expected_solve_time, difficulty_prior, discrimination_prior, guessing_prior, blueprint_version
                FROM question_blueprints WHERE blueprint_id = ?
            """, (blueprint_id,))
            bp = cur.fetchone()
            if bp:
                expected_solve_time = bp["expected_solve_time"] or 120.0
                difficulty_prior = bp["difficulty_prior"] or 0.0
                discrimination_prior = bp["discrimination_prior"] or 1.0
                guessing_prior = bp["guessing_prior"] or 0.0
                blueprint_version = bp["blueprint_version"] or "v1.0"
                parent_ancestor_path = blueprint_id

        # Fetch parent question details if specified (inheritance rule)
        if derived_from_question_id:
            cur.execute("""
                SELECT qb.estimated_time, qb.irt_difficulty, qb.irt_discrimination, qb.irt_guessing,
                       qv.generation, qv.lineage_depth, qv.ancestor_path, qv.root_blueprint_id, qv.family_id
                FROM question_bank qb
                JOIN question_versions qv ON qv.question_id = qb.id
                WHERE qb.id = ?
            """, (derived_from_question_id,))
            parent = cur.fetchone()
            if parent:
                # Inherit priors from parent's current calibrated metrics (Autoritative Single Source)
                expected_solve_time = parent["estimated_time"] or expected_solve_time
                difficulty_prior = parent["irt_difficulty"] if parent["irt_difficulty"] is not None else difficulty_prior
                discrimination_prior = parent["irt_discrimination"] if parent["irt_discrimination"] is not None else discrimination_prior
                guessing_prior = parent["irt_guessing"] if parent["irt_guessing"] is not None else guessing_prior
                generation = (parent["generation"] or 1) + 1
                lineage_depth = (parent["lineage_depth"] or 0) + 1
                parent_ancestor_path = parent["ancestor_path"] or ""
                root_blueprint_id = parent["root_blueprint_id"] or root_blueprint_id
                if not family_id:
                    family_id = parent["family_id"]

        # Calculate version number inside the family
        version_number = 1
        if family_id:
            cur.execute("""
                SELECT COUNT(*) as cnt FROM question_versions WHERE family_id = ?
            """, (family_id,))
            cnt_row = cur.fetchone()
            version_number = (cnt_row["cnt"] or 0) + 1

        # Cache Ancestor Path (O(1) lineages Change 4)
        v_tag = f"v{version_number}"
        if parent_ancestor_path:
            ancestor_path = f"{parent_ancestor_path}/{v_tag}"
        else:
            ancestor_path = v_tag

        # 2. Insert into question_bank
        cur.execute("""
            INSERT INTO question_bank (
                subject, topic, subtopic, difficulty, cognitive_type,
                prompt, option_a, option_b, option_c, option_d, correct_index,
                explanation, estimated_time, status, version, created_at,
                irt_difficulty, irt_discrimination, irt_guessing, irt_confidence,
                tags, teacher_added, teacher_email
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pilot', ?, ?, ?, ?, ?, 0.1, ?, 0, ?)
        """, (
            subject, topic, subtopic, difficulty, cognitive_type,
            prompt, option_a, option_b, option_c, option_d, correct_index,
            explanation, expected_solve_time, version_number, now,
            difficulty_prior, discrimination_prior, guessing_prior,
            tags, created_by
        ))
        question_id = cur.lastrowid

        # 3. Insert into question_versions
        cur.execute("""
            INSERT INTO question_versions (
                question_id, family_id, version_number, lineage_depth, root_blueprint_id,
                generation, derived_from_question_id, ancestor_path, expected_solve_time,
                difficulty_prior, difficulty_current, discrimination_prior, discrimination_current,
                guessing_prior, guessing_current
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question_id, family_id, version_number, lineage_depth, root_blueprint_id,
            generation, derived_from_question_id, ancestor_path, expected_solve_time,
            difficulty_prior, difficulty_prior, discrimination_prior, discrimination_prior,
            guessing_prior, guessing_prior
        ))

        # 4. Insert into question_lifecycle
        cur.execute("""
            INSERT INTO question_lifecycle (question_id, lifecycle_status, last_status_change)
            VALUES (?, 'Pilot', ?)
        """, (question_id, now))

        # Log retirement/lifecycle history
        cur.execute("""
            INSERT INTO question_retirement_history (question_id, old_status, new_status, transition_reason, actor, timestamp)
            VALUES (?, 'Draft', 'Pilot', 'Initial Creation', ?, ?)
        """, (question_id, created_by, now))

        conn.commit()
        return {
            "question_id": question_id,
            "version_number": version_number,
            "ancestor_path": ancestor_path,
            "lineage_depth": lineage_depth,
            "generation": generation,
            "difficulty_prior": difficulty_prior,
            "expected_solve_time": expected_solve_time,
            "blueprint_version": blueprint_version
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()


def promote_question_status(question_id, new_status, actor="system"):
    """
    Transitions the lifecycle status of a question version.
    Valid statuses: 'Draft', 'Pilot', 'Calibration', 'Active', 'Retired', 'Archived'
    """
    valid_statuses = ['Draft', 'Pilot', 'Calibration', 'Active', 'Retired', 'Archived']
    if new_status not in valid_statuses:
        return {"error": f"Invalid status: {new_status}"}

    conn = get_conn()
    cur = conn.cursor()
    try:
        now = datetime.now().isoformat()
        cur.execute("SELECT lifecycle_status FROM question_lifecycle WHERE question_id = ?", (question_id,))
        row = cur.fetchone()
        old_status = row["lifecycle_status"] if row else "Draft"

        if old_status == new_status:
            return {"status": "success", "message": f"Already in {new_status} status."}

        cur.execute("""
            INSERT INTO question_lifecycle (question_id, lifecycle_status, last_status_change)
            VALUES (?, ?, ?)
            ON CONFLICT(question_id) DO UPDATE SET
                lifecycle_status = excluded.lifecycle_status,
                last_status_change = excluded.last_status_change
        """, (question_id, new_status, now))

        cur.execute("""
            INSERT INTO question_retirement_history (question_id, old_status, new_status, transition_reason, actor, timestamp)
            VALUES (?, ?, ?, 'Status Promotion', ?, ?)
        """, (question_id, old_status, new_status, actor, now))

        conn.commit()

        if new_status == 'Active':
            try:
                import event_bus
                event_bus.publish(
                    event_type="QuestionPromoted",
                    entity_type="question",
                    entity_id=str(question_id),
                    producer="qbl_engine",
                    producer_version="v2.5.0",
                    schema_version="v1.0",
                    metadata_json={},
                    payload_json={"new_status": new_status, "old_status": old_status}
                )
            except Exception:
                pass

        return {"status": "success", "old_status": old_status, "new_status": new_status}
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()


# =============================================================================
# RETIREMENT & EVIDENCE LOGGING
# =============================================================================

def retire_question_version(question_id, reason, replaced_by_question_id=None, metrics_json=None, actor="system"):
    """
    Retires a specific version with metrics evidence and replacements links (Change 3).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        now = datetime.now().isoformat()
        cur.execute("SELECT lifecycle_status FROM question_lifecycle WHERE question_id = ?", (question_id,))
        row = cur.fetchone()
        old_status = row["lifecycle_status"] if row else "Draft"

        # Serialize metrics json
        m_json_str = json.dumps(metrics_json) if metrics_json else None

        cur.execute("""
            INSERT INTO question_lifecycle (
                question_id, lifecycle_status, last_status_change, retired_at,
                retirement_reason, retirement_metrics_json, replaced_by_question_id
            ) VALUES (?, 'Retired', ?, ?, ?, ?, ?)
            ON CONFLICT(question_id) DO UPDATE SET
                lifecycle_status = excluded.lifecycle_status,
                last_status_change = excluded.last_status_change,
                retired_at = excluded.retired_at,
                retirement_reason = excluded.retirement_reason,
                retirement_metrics_json = excluded.retirement_metrics_json,
                replaced_by_question_id = excluded.replaced_by_question_id
        """, (question_id, now, now, reason, m_json_str, replaced_by_question_id))

        cur.execute("""
            INSERT INTO question_retirement_history (
                question_id, old_status, new_status, transition_reason,
                retirement_metrics_json, actor, timestamp
            ) VALUES (?, ?, 'Retired', ?, ?, ?, ?)
        """, (question_id, old_status, reason, m_json_str, actor, now))

        conn.commit()

        try:
            import event_bus
            event_bus.publish(
                event_type="QuestionRetired",
                entity_type="question",
                entity_id=str(question_id),
                producer="qbl_engine",
                producer_version="v2.5.0",
                schema_version="v1.0",
                metadata_json={},
                payload_json={"reason": reason, "replaced_by_question_id": replaced_by_question_id, "metrics": metrics_json}
            )
        except Exception:
            pass

        return {
            "status": "success",
            "question_id": question_id,
            "lifecycle_status": "Retired",
            "retirement_metrics": metrics_json
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()


# =============================================================================
# DRIFT & LINEAGE QUERIES
# =============================================================================

def compute_and_cache_drifts(question_id):
    """
    Queries current psychometric parameters from authorative single source,
    updates caches in question_versions, and calculates drifts.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Fetch current calibrated NBIRT values from question_bank
        cur.execute("""
            SELECT qb.irt_difficulty, qb.irt_discrimination, qb.irt_guessing,
                   qv.difficulty_prior, qv.discrimination_prior, qv.guessing_prior,
                   qv.expected_solve_time, qv.observed_solve_time
            FROM question_bank qb
            JOIN question_versions qv ON qv.question_id = qb.id
            WHERE qb.id = ?
        """, (question_id,))
        row = cur.fetchone()
        if not row:
            return {"error": f"Question version details not found for ID: {question_id}"}

        diff_current = row["irt_difficulty"] if row["irt_difficulty"] is not None else row["difficulty_prior"]
        disc_current = row["irt_discrimination"] if row["irt_discrimination"] is not None else row["discrimination_prior"]
        guess_current = row["irt_guessing"] if row["irt_guessing"] is not None else row["guessing_prior"]

        diff_drift = round(diff_current - row["difficulty_prior"], 3)
        time_drift = round(row["observed_solve_time"] - row["expected_solve_time"], 3)

        cur.execute("""
            UPDATE question_versions SET
                difficulty_current = ?,
                difficulty_drift = ?,
                discrimination_current = ?,
                guessing_current = ?,
                time_drift = ?
            WHERE question_id = ?
        """, (diff_current, diff_drift, disc_current, guess_current, time_drift, question_id))

        conn.commit()
        return {
            "question_id": question_id,
            "difficulty_current": diff_current,
            "difficulty_drift": diff_drift,
            "time_drift": time_drift
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()


def get_question_lineage(question_id):
    """
    Reconstructs lineage paths using the O(1) ancestor path cache (Change 4).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT ancestor_path, root_blueprint_id, generation, derived_from_question_id
            FROM question_versions WHERE question_id = ?
        """, (question_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Question version not found."}

        return {
            "question_id": question_id,
            "ancestor_path": row["ancestor_path"],
            "root_blueprint_id": row["root_blueprint_id"],
            "generation": row["generation"],
            "derived_from_question_id": row["derived_from_question_id"]
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


def get_question_family(family_id):
    """Returns all siblings and versions under the same family."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT qv.*, qb.prompt, ql.lifecycle_status
            FROM question_versions qv
            JOIN question_bank qb ON qb.id = qv.question_id
            LEFT JOIN question_lifecycle ql ON ql.question_id = qv.question_id
            WHERE qv.family_id = ?
            ORDER BY qv.version_number ASC
        """, (family_id,))
        rows = [dict(r) for r in cur.fetchall()]
        return {"family_id": family_id, "versions": rows}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
