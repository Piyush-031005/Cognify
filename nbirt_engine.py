"""
nbirt_engine.py
Week 11 – Neural Bayesian Item Response Theory (NBIRT)
2PL Model Parameter Estimation (θ, b, a) with Cognitive Priors.
On-Demand Batch Runs & Individual Student Ability Queries.
"""

import math
import json
import sqlite3
import uuid
import time
from datetime import datetime
from database import get_conn


# =============================================================================
# CONFIGURATION LOADER
# =============================================================================

def _load_nbirt_config():
    """
    Loads all NBIRT parameters from nbirt_config table.
    Falls back to safe defaults if table is missing or empty.
    """
    defaults = {
        "min_responses_per_item": 20.0,
        "min_items_per_student": 5.0,
        "em_max_iterations": 50.0,
        "em_convergence_threshold": 0.001,
        "prior_ability_mean": 0.0,
        "prior_ability_sd": 1.0,
        "memory_weight_in_prior": 0.4,
        "misconception_penalty_in_prior": 0.2,
        "discrimination_bounds_low": 0.2,
        "discrimination_bounds_high": 3.0,
        "min_irt_confidence_for_context": 0.5,
        "theta_grid_points": 41.0,
        "theta_grid_min": -4.0,
        "theta_grid_max": 4.0,
    }
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT key, value FROM nbirt_config")
        rows = cur.fetchall()
        for r in rows:
            defaults[r["key"]] = r["value"]
    except Exception:
        pass
    finally:
        conn.close()
    return defaults


def get_nbirt_config():
    """Returns all active configuration records."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT key, value, config_version, updated_by, updated_at FROM nbirt_config")
        rows = [dict(r) for r in cur.fetchall()]
    except Exception:
        rows = []
    finally:
        conn.close()
    return rows


def update_nbirt_config(key, value, updated_by="teacher"):
    """Updates a single config parameter."""
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cur.execute("""
            INSERT INTO nbirt_config (key, value, config_version, updated_by, updated_at)
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
# IRT 2PL PROBABILITY & UTILITIES
# =============================================================================

def _2pl_probability(theta, a, b):
    """
    Standard 2-Parameter Logistic (2PL) function:
    P(correct | θ, a, b) = 1 / (1 + exp(-a * (θ - b)))
    """
    try:
        # Clamp to avoid overflow/underflow
        val = -a * (theta - b)
        val = max(-50.0, min(50.0, val))
        return 1.0 / (1.0 + math.exp(val))
    except Exception:
        return 0.5


def _logit_to_percentile(theta):
    """Converts a logit ability score to standard normal percentile (0-100)."""
    if theta is None:
        return 50.0
    try:
        # Standard Normal Cumulative Distribution Function approximation
        return round(0.5 * (1.0 + math.erf(theta / math.sqrt(2.0))) * 100.0, 2)
    except Exception:
        return 50.0


def _compute_cognitive_prior(student_email, config):
    """
    Derives personalized Bayesian prior mean (mu) and SD for student ability
    by fusing Educational Memory storage strength and confirmed misconceptions.
    Returns (prior_mu, prior_sd).
    """
    prior_mean = config["prior_ability_mean"]
    prior_sd = config["prior_ability_sd"]

    conn = get_conn()
    cur = conn.cursor()

    mem_strength = None
    mem_confidence = None
    try:
        # Fetch concept memory storage strength details
        cur.execute("""
            SELECT AVG(memory_strength) as avg_s, AVG(memory_confidence) as avg_c
            FROM concept_memory WHERE student_email = ?
        """, (student_email,))
        row = cur.fetchone()
        if row and row["avg_s"] is not None:
            mem_strength = row["avg_s"]
            mem_confidence = row["avg_c"] or 0.5
    except Exception:
        pass

    misconception_count = 0
    try:
        # Count confirmed active misconceptions for this student
        cur.execute("""
            SELECT COUNT(DISTINCT mc.cluster_id) as cnt
            FROM misconception_clusters mc
            JOIN misconception_evidence me ON me.cluster_id = mc.cluster_id
            WHERE me.student_email = ? AND me.status = 'active'
        """, (student_email,))
        row = cur.fetchone()
        if row:
            misconception_count = row["cnt"] or 0
    except Exception:
        pass

    conn.close()

    prior_reasons = {}

    # Adjust prior mean and sd based on cognitive profile
    if mem_strength is not None:
        # Map [0, 1] storage strength to [-1.5, 1.5] delta
        mem_delta = config["memory_weight_in_prior"] * (mem_strength - 0.5) * 3.0
        prior_mean += mem_delta
        # Enriched memory reduces prior uncertainty
        prior_sd = max(0.4, prior_sd - (mem_confidence * 0.3))
        prior_reasons["memory_strength"] = round(mem_strength, 3)
        prior_reasons["memory_confidence"] = round(mem_confidence, 3)

    if misconception_count > 0:
        penalty = config["misconception_penalty_in_prior"] * misconception_count
        prior_mean -= penalty
        prior_reasons["active_misconceptions"] = misconception_count

    return prior_mean, prior_sd, prior_reasons


# =============================================================================
# SINGLE-STUDENT ABILITY ESTIMATION (E-STEP BOUNDARY)
# =============================================================================

def estimate_student_ability(student_email):
    """
    Estimates θ (latent ability) and standard error for a single student.
    - Cold Start rule: Returns NULL if responses < min_items_per_student.
    - Uses Bayesian quadrature with Cognitive Prior.
    """
    config = _load_nbirt_config()
    min_items = int(config["min_items_per_student"])

    conn = get_conn()
    cur = conn.cursor()

    # Fetch all responses for this student where the question has estimated parameters
    cur.execute("""
        SELECT r.question_id, r.correct, qb.irt_difficulty as b, qb.irt_discrimination as a
        FROM responses r
        JOIN question_bank qb ON qb.id = r.question_id
        WHERE r.student_email = ? AND qb.irt_difficulty IS NOT NULL AND qb.irt_discrimination IS NOT NULL
    """, (student_email,))
    rows = cur.fetchall()
    conn.close()

    n_responses = len(rows)
    if n_responses < min_items:
        # Cold Start: Insufficient responses to estimate theta
        return {
            "student_email": student_email,
            "irt_ability": None,
            "irt_ability_se": None,
            "irt_ability_percentile": 50.0,
            "irt_confidence": 0.0,
            "items_used": n_responses,
            "status": "cold_start",
            "reason": f"Only {n_responses} responses recorded. Minimum required: {min_items}."
        }

    # Derive Cognitive Prior
    prior_mu, prior_sd, prior_reasons = _compute_cognitive_prior(student_email, config)

    # Gaussian Quadrature (grid-based posterior estimation)
    grid_points = int(config["theta_grid_points"])
    grid_min = config["theta_grid_min"]
    grid_max = config["theta_grid_max"]
    step = (grid_max - grid_min) / (grid_points - 1)

    theta_grid = [grid_min + i * step for i in range(grid_points)]
    
    # Calculate prior densities: Normal(prior_mu, prior_sd)
    prior_densities = []
    for theta in theta_grid:
        try:
            diff = theta - prior_mu
            density = math.exp(-0.5 * (diff / prior_sd) ** 2) / (prior_sd * math.sqrt(2.0 * math.pi))
            prior_densities.append(density)
        except Exception:
            prior_densities.append(1e-5)

    # Compute Likelihood for each grid point
    posteriors = []
    for theta_idx, theta in enumerate(theta_grid):
        likelihood = 1.0
        for r in rows:
            p = _2pl_probability(theta, r["a"], r["b"])
            if r["correct"] == 1:
                likelihood *= max(1e-10, p)
            else:
                likelihood *= max(1e-10, 1.0 - p)
        posteriors.append(likelihood * prior_densities[theta_idx])

    # Normalize posterior
    total_area = sum(posteriors)
    if total_area <= 0:
        posteriors = [1.0 / grid_points] * grid_points
        total_area = 1.0
    else:
        posteriors = [p / total_area for p in posteriors]

    # Expected Value (EAP - Expected A Posteriori ability)
    est_theta = sum(theta_grid[i] * posteriors[i] for i in range(grid_points))

    # Variance (Standard Error of EAP)
    variance = sum(((theta_grid[i] - est_theta) ** 2) * posteriors[i] for i in range(grid_points))
    se = math.sqrt(variance)

    # Reliability Confidence index: 1 / (1 + SE) -> scales to (0, 1]
    irt_confidence = round(1.0 / (1.0 + se), 3)

    return {
        "student_email": student_email,
        "irt_ability": round(est_theta, 4),
        "irt_ability_se": round(se, 4),
        "irt_ability_percentile": _logit_to_percentile(est_theta),
        "irt_confidence": irt_confidence,
        "items_used": n_responses,
        "prior_used": prior_reasons,
        "status": "calibrated"
    }


# =============================================================================
# FULL ON-DEMAND BATCH ESTIMATION PASS (EM LOOP)
# =============================================================================

def run_nbirt_estimation(run_id=None):
    """
    Runs a full 2PL Expectation-Maximization calibration pass.
    1. Ledger entry created in nbirt_runs.
    2. Identifies all eligible questions (responses >= min_responses_per_item).
    3. Identifies all eligible students (responses >= min_items_per_student).
    4. Runs EM optimization on item parameters (a, b) and ability values (θ).
    5. Saves final values and logs to nbirt_item_history and nbirt_ability_history.
    """
    import uuid
    import time

    if not run_id:
        run_id = str(uuid.uuid4())

    config = _load_nbirt_config()
    min_responses = int(config["min_responses_per_item"])
    min_items = int(config["min_items_per_student"])
    max_iter = int(config["em_max_iterations"])
    tolerance = config["em_convergence_threshold"]
    a_low = config["discrimination_bounds_low"]
    a_high = config["discrimination_bounds_high"]

    started_at = datetime.now().isoformat()
    wall_start = time.time()

    conn = get_conn()
    cur = conn.cursor()

    # Open ledger entry
    try:
        cur.execute("""
            INSERT INTO nbirt_runs (run_id, started_at, status)
            VALUES (?, ?, 'running')
        """, (run_id, started_at))
        conn.commit()
    except Exception:
        pass

    # 1. Fetch eligible items
    cur.execute("""
        SELECT id, qqi_score, irt_difficulty, irt_discrimination
        FROM question_bank
        WHERE student_responses_count >= ?
    """, (min_responses,))
    items = [dict(r) for r in cur.fetchall()]

    # 2. Fetch responses for eligible items
    item_ids = [it["id"] for it in items]
    if not item_ids:
        # No questions ready
        cur.execute("""
            UPDATE nbirt_runs SET completed_at = ?, status = 'completed',
                items_estimated = 0, students_estimated = 0, em_iterations = 0,
                max_parameter_delta = 0.0, execution_time_ms = ?
            WHERE run_id = ?
        """, (datetime.now().isoformat(), round((time.time() - wall_start)*1000, 2), run_id))
        conn.commit()
        conn.close()
        return {"run_id": run_id, "status": "completed", "items_estimated": 0, "students_estimated": 0}

    # Fetch all responses mapping to these items
    placeholders = ",".join("?" for _ in item_ids)
    cur.execute(f"""
        SELECT student_email, question_id, correct
        FROM responses
        WHERE question_id IN ({placeholders})
    """, tuple(item_ids))
    responses = [dict(r) for r in cur.fetchall()]

    # Count items per student to filter eligible students
    student_counts = {}
    for r in responses:
        student_counts[r["student_email"]] = student_counts.get(r["student_email"], 0) + 1
    
    eligible_students = {email for email, count in student_counts.items() if count >= min_items}

    if not eligible_students:
        # No students ready
        cur.execute("""
            UPDATE nbirt_runs SET completed_at = ?, status = 'completed',
                items_estimated = 0, students_estimated = 0, em_iterations = 0,
                max_parameter_delta = 0.0, execution_time_ms = ?
            WHERE run_id = ?
        """, (datetime.now().isoformat(), round((time.time() - wall_start)*1000, 2), run_id))
        conn.commit()
        conn.close()
        return {"run_id": run_id, "status": "completed", "items_estimated": 0, "students_estimated": 0}

    # Filter responses to only include eligible students
    responses = [r for r in responses if r["student_email"] in eligible_students]

    # Initialise parameters
    # Student θ initial values: Prior means
    student_thetas = {}
    student_priors = {}
    for email in eligible_students:
        mu, sd, prior_reasons = _compute_cognitive_prior(email, config)
        student_thetas[email] = mu
        student_priors[email] = (mu, sd)

    # Item parameters: b (0.0), a (1.0)
    item_params = {}
    for it in items:
        b_init = it["irt_difficulty"] if it["irt_difficulty"] is not None else 0.0
        a_init = it["irt_discrimination"] if it["irt_discrimination"] is not None else 1.0
        item_params[it["id"]] = {"b": b_init, "a": a_init}

    iter_count = 0
    max_delta = 1.0

    # Group responses by student & item for quick access
    responses_by_student = {}
    responses_by_item = {}
    for r in responses:
        email = r["student_email"]
        item_id = r["question_id"]
        if email not in responses_by_student:
            responses_by_student[email] = []
        responses_by_student[email].append(r)
        
        if item_id not in responses_by_item:
            responses_by_item[item_id] = []
        responses_by_item[item_id].append(r)

    # EM Optimization Loop
    while iter_count < max_iter and max_delta > tolerance:
        iter_count += 1
        max_delta = 0.0

        # E-Step: Re-estimate Student Ability (EAP)
        for email in eligible_students:
            prior_mu, prior_sd = student_priors[email]
            
            # Simple grid quadrature (41 points)
            grid_points = 41
            grid_min, grid_max = -4.0, 4.0
            step = (grid_max - grid_min) / (grid_points - 1)
            grid = [grid_min + i * step for i in range(grid_points)]
            
            posteriors = []
            for theta in grid:
                density = math.exp(-0.5 * ((theta - prior_mu) / prior_sd) ** 2) / (prior_sd * math.sqrt(2.0 * math.pi))
                likelihood = 1.0
                for r in responses_by_student.get(email, []):
                    params = item_params[r["question_id"]]
                    p = _2pl_probability(theta, params["a"], params["b"])
                    if r["correct"] == 1:
                        likelihood *= max(1e-10, p)
                    else:
                        likelihood *= max(1e-10, 1.0 - p)
                posteriors.append(likelihood * density)
                
            area = sum(posteriors)
            if area > 0:
                posteriors = [p / area for p in posteriors]
                new_theta = sum(grid[i] * posteriors[i] for i in range(grid_points))
                student_thetas[email] = new_theta

        # M-Step: Update Item Parameters via gradient ascent (Maximum Likelihood)
        learning_rate = 0.1
        for it in items:
            item_id = it["id"]
            params = item_params[item_id]
            old_b, old_a = params["b"], params["a"]

            # Gradient calculations
            grad_b = 0.0
            grad_a = 0.0
            for r in responses_by_item.get(item_id, []):
                theta = student_thetas[r["student_email"]]
                p = _2pl_probability(theta, old_a, old_b)
                error = r["correct"] - p
                # dP/db = -a * P * (1-P)
                # dP/da = (theta - b) * P * (1-P)
                # log likelihood gradient w.r.t b: -a * error
                grad_b += -old_a * error
                # log likelihood gradient w.r.t a: (theta - b) * error
                grad_a += (theta - old_b) * error

            # Apply gradient updates
            new_b = old_b + learning_rate * grad_b
            new_a = old_a + learning_rate * grad_a

            # Clamp parameters to bounds
            new_a = max(a_low, min(a_high, new_a))
            new_b = max(-4.0, min(4.0, new_b))

            item_params[item_id] = {"b": new_b, "a": new_a}

            delta_b = abs(new_b - old_b)
            delta_a = abs(new_a - old_a)
            max_delta = max(max_delta, delta_b, delta_a)

    # 4. Save Updates to database and append to histories
    now = datetime.now().isoformat()
    
    # Update question bank & item parameter history
    for it in items:
        item_id = it["id"]
        final_params = item_params[item_id]
        
        # In 2PL model, irt_guessing is stored as 0.0 (reserved for future)
        cur.execute("""
            UPDATE question_bank 
            SET irt_difficulty = ?, irt_discrimination = ?, irt_guessing = 0.0,
                irt_run_id = ?, irt_confidence = 0.9, irt_version = 'v1.0'
            WHERE id = ?
        """, (final_params["b"], final_params["a"], run_id, item_id))

        old_b = it["irt_difficulty"] if it["irt_difficulty"] is not None else 0.0
        cur.execute("""
            INSERT INTO nbirt_item_history (question_id, run_id, old_b, new_b, old_a, new_a, irt_confidence, n_responses, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, 0.9, ?, ?)
        """, (item_id, run_id, old_b, final_params["b"], it["irt_discrimination"] or 1.0, final_params["a"], len(responses_by_item.get(item_id, [])), now))

    # Update student abilities & ability history
    for email in eligible_students:
        summary = estimate_student_ability(email)
        
        cur.execute("""
            UPDATE student_cognitive_profiles
            SET irt_ability = ?, irt_ability_se = ?, irt_ability_percentile = ?, irt_confidence = ?, irt_ability_version = 'v1.0'
            WHERE student_email = ?
        """, (summary["irt_ability"], summary["irt_ability_se"], summary["irt_ability_percentile"], summary["irt_confidence"], email))

        # Check if record exists in profile, if not insert
        cur.execute("SELECT changes()")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO student_cognitive_profiles (student_email, irt_ability, irt_ability_se, irt_ability_percentile, irt_confidence, irt_ability_version, updated_at)
                VALUES (?, ?, ?, ?, ?, 'v1.0', ?)
            """, (email, summary["irt_ability"], summary["irt_ability_se"], summary["summary_percentile" if False else "irt_ability_percentile"], summary["irt_confidence"], now))

        # Append-only student history
        cur.execute("""
            SELECT irt_ability, irt_ability_se, irt_ability_percentile FROM student_cognitive_profiles WHERE student_email = ?
        """, (email,))
        old_prof = cur.fetchone()
        
        cur.execute("""
            INSERT INTO nbirt_ability_history (student_email, run_id, old_ability, new_ability, old_se, new_se, old_percentile, new_percentile, prior_used, n_items_used, irt_confidence, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email, run_id,
            old_prof["irt_ability"] if old_prof else None, summary["irt_ability"],
            old_prof["irt_ability_se"] if old_prof else None, summary["irt_ability_se"],
            old_prof["irt_ability_percentile"] if old_prof else 50.0, summary["irt_ability_percentile"],
            json.dumps(summary.get("prior_used", {})), summary["items_used"], summary["irt_confidence"], now
        ))

    # Close ledger entry
    elapsed_ms = round((time.time() - wall_start) * 1000, 2)
    cur.execute("""
        UPDATE nbirt_runs SET completed_at = ?, status = 'completed',
            items_estimated = ?, students_estimated = ?, em_iterations = ?,
            max_parameter_delta = ?, execution_time_ms = ?
        WHERE run_id = ?
    """, (datetime.now().isoformat(), len(items), len(eligible_students), iter_count, max_delta, elapsed_ms, run_id))

    conn.commit()
    conn.close()

    return {
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": now,
        "items_estimated": len(items),
        "students_estimated": len(eligible_students),
        "em_iterations": iter_count,
        "max_parameter_delta": round(max_delta, 5),
        "status": "completed",
        "execution_time_ms": elapsed_ms
    }
