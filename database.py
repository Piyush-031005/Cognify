import sqlite3
from datetime import datetime
import random
import string
import json

DB_NAME = "cognify.db"


# =========================
# CONNECTION
# =========================
def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def get_apd_config():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT key, value FROM apd_config")
        rows = cur.fetchall()
        config = {}
        for r in rows:
            key = r["key"]
            val = r["value"]
            try:
                if '.' in val:
                    config[key] = float(val)
                else:
                    config[key] = int(val)
            except ValueError:
                config[key] = val
        return config
    except sqlite3.OperationalError:
        return {}
    finally:
        conn.close()


def get_misconception_config():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT key, value FROM misconception_config")
        rows = cur.fetchall()
        config = {}
        for r in rows:
            key = r["key"]
            val = r["value"]
            try:
                if '.' in val:
                    config[key] = float(val)
                else:
                    config[key] = int(val)
            except ValueError:
                config[key] = val
        return config
    except sqlite3.OperationalError:
        return {}
    finally:
        conn.close()


# =========================
# INIT DATABASE
# =========================
def init_db():
    print("DATABASE INIT RUNNING...")
    conn = get_conn()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        email TEXT UNIQUE,
        password TEXT,
        education TEXT,
        learning_style TEXT,
        subjects TEXT,
        confidence REAL,
        role TEXT,
        created_at TEXT
    )
    """)

    # Create kg_edge_evidence table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kg_edge_evidence (
        id TEXT PRIMARY KEY,
        source_id TEXT,
        target_id TEXT,
        relation_type TEXT,
        teacher_support INTEGER DEFAULT 0,
        teacher_rejections INTEGER DEFAULT 0,
        student_sample_size INTEGER DEFAULT 0,
        p_struggle_given_mastered REAL,
        p_struggle_given_not_mastered REAL,
        kl_divergence REAL,
        confidence_score REAL,
        explanation TEXT,
        last_recomputed TEXT,
        conflict_detected BOOLEAN DEFAULT 0,
        conflict_details TEXT,
        FOREIGN KEY (source_id, target_id, relation_type) REFERENCES kg_edges(source_id, target_id, relation_type)
    )
    """)

    # Create apd_batch_runs table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS apd_batch_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_date TEXT,
        subject TEXT,
        student_sample INTEGER,
        concepts_analyzed INTEGER,
        edges_tested INTEGER,
        candidates_generated INTEGER,
        execution_time_ms INTEGER
    )
    """)

    # Create apd_config table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS apd_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    # Seed apd_config defaults
    defaults = {
        "STAT_WEIGHT": 0.4,
        "TEACHER_WEIGHT": 0.3,
        "HISTORY_WEIGHT": 0.2,
        "SAMPLE_WEIGHT": 0.1,
        "MIN_SAMPLE_SIZE": 30,
        "EFFECT_SIZE_THRESHOLD": 0.15,
        "DEPRECATE_THRESHOLD": 0.4,
        "DECAY_LAMBDA": 0.005,
        "HISTORY_WINDOW": 30
    }
    for k, v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO apd_config (key, value) VALUES (?, ?)", (k, str(v)))

    # Create kg_evolution_log table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kg_evolution_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation TEXT,
        entity_id TEXT,
        old_state TEXT,
        new_state TEXT,
        actor TEXT,
        timestamp TEXT,
        confidence_delta REAL DEFAULT 0.0
    )
    """)

    # Create misconception_config table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS misconception_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    # Seed misconception_config defaults
    mcp_defaults = {
        "MIN_STUDENT_COUNT": 5,
        "MIN_WRONG_ANSWERS": 10,
        "CONFIDENCE_THRESHOLD": 0.5,
        "SEVERITY_THRESHOLD": 0.5,
        "CLUSTER_SIZE_WEIGHT": 0.3,
        "BEHAVIOR_CONSISTENCY_WEIGHT": 0.3,
        "MASTERY_CONSISTENCY_WEIGHT": 0.2,
        "TEACHER_AGREEMENT_WEIGHT": 0.2
    }
    for k, v in mcp_defaults.items():
        cur.execute("INSERT OR IGNORE INTO misconception_config (key, value) VALUES (?, ?)", (k, str(v)))

    # Create misconception_clusters table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS misconception_clusters (
        cluster_id TEXT PRIMARY KEY,
        concept_id TEXT,
        misconception_name TEXT,
        description TEXT,
        selected_option TEXT,
        correct_option TEXT,
        confidence_size REAL,
        confidence_behavior REAL,
        confidence_mastery REAL,
        confidence_teacher REAL,
        cluster_confidence REAL,
        confidence_level TEXT,
        severity TEXT,
        status TEXT DEFAULT 'candidate',
        parent_cluster_id TEXT,
        canonical_cluster_id TEXT,
        recommended_intervention_id TEXT,
        intervention_confidence REAL,
        intervention_source TEXT,
        memory_event_id TEXT,
        memory_status TEXT DEFAULT 'pending',
        created_at TEXT,
        last_updated TEXT,
        algorithm_version TEXT DEFAULT 'v2.0',
        graph_version TEXT DEFAULT 'v2.1',
        qqi_version TEXT DEFAULT 'v1.2',
        assessment_version TEXT DEFAULT 'v1.0',
        model_version TEXT DEFAULT 'v2.0',
        FOREIGN KEY (concept_id) REFERENCES kg_nodes(id)
    )
    """)

    # Create misconception_evidence table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS misconception_evidence (
        id TEXT PRIMARY KEY,
        cluster_id TEXT,
        question_id INTEGER,
        student_count INTEGER,
        wrong_answer_count INTEGER,
        avg_hesitation REAL,
        avg_response_time REAL,
        cohort_id TEXT,
        institution TEXT,
        grade TEXT,
        curriculum TEXT,
        academic_year TEXT,
        explanation TEXT,
        created_at TEXT,
        FOREIGN KEY (cluster_id) REFERENCES misconception_clusters(cluster_id)
    )
    """)

    # Create misconception_evolution_log table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS misconception_evolution_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_id TEXT,
        old_status TEXT,
        new_status TEXT,
        old_confidence REAL,
        new_confidence REAL,
        reason TEXT,
        actor TEXT,
        timestamp TEXT,
        teacher_action TEXT,
        FOREIGN KEY (cluster_id) REFERENCES misconception_clusters(cluster_id)
    )
    """)

    # CONCEPTS (Academic Knowledge Graph)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS concepts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        parent_concept_id INTEGER,
        learning_outcome TEXT,
        kg_version TEXT DEFAULT 'v1.0',
        FOREIGN KEY (parent_concept_id) REFERENCES concepts(id)
    )
    """)

    # QUESTIONS MASTER (SYSTEM GENERATED)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        exam_level TEXT,
        prompt TEXT,
        options_json TEXT,
        correct_index INTEGER,
        question_type TEXT,
        difficulty TEXT,
        cognitive_skill TEXT,
        misconception_tag TEXT,
        bloom_level TEXT,
        estimated_time INTEGER,
        image_url TEXT,
        created_at TEXT
    )
    """)

    # QUESTION BANK META TABLE (Knowledge Repository)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        difficulty TEXT,
        cognitive_type TEXT,
        semantic_id TEXT,
        variant_id TEXT,
        prompt TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_index INTEGER,
        explanation TEXT,
        image_url TEXT,
        source_exam TEXT,
        teacher_added INTEGER DEFAULT 0,
        teacher_email TEXT,
        tags TEXT,
        estimated_time INTEGER,
        purpose TEXT DEFAULT 'practice',
        cognitive_load TEXT DEFAULT 'medium',
        created_at TEXT,
        status TEXT DEFAULT 'Draft',
        version INTEGER DEFAULT 1,
        qqi_score REAL DEFAULT 80.0,
        qqi_confidence REAL DEFAULT 0.1,
        calibrated_qqi_score REAL,
        calibrated_difficulty TEXT,
        student_responses_count INTEGER DEFAULT 0,
        purity_score REAL DEFAULT 80.0,
        discrimination_score REAL DEFAULT 80.0,
        difficulty_stability_score REAL DEFAULT 80.0,
        guess_resistance_score REAL DEFAULT 80.0,
        language_quality_score REAL DEFAULT 80.0,
        behavior_signal_score REAL DEFAULT 80.0,
        kg_mapping_score REAL DEFAULT 80.0,
        time_stability_score REAL DEFAULT 80.0,
        teacher_rating_score REAL DEFAULT 80.0,
        historical_reliability_score REAL DEFAULT 80.0,
        parent_question_id INTEGER,
        current_version INTEGER DEFAULT 1,
        edited_by TEXT,
        edited_at TEXT,
        change_reason TEXT
    )
    """)

    # QUESTION CONCEPTS (Concept Weight Mapping)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_concepts (
        question_id INTEGER,
        concept_id INTEGER,
        weight REAL,
        PRIMARY KEY (question_id, concept_id),
        FOREIGN KEY (question_id) REFERENCES question_bank(id),
        FOREIGN KEY (concept_id) REFERENCES concepts(id)
    )
    """)

    # TEACHER CUSTOM QUESTIONS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_custom_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_email TEXT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        prompt TEXT,
        options_json TEXT,
        correct_index INTEGER,
        question_category TEXT,
        image_url TEXT,
        created_at TEXT
    )
    """)

    # TEACHER REVIEWS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        teacher_email TEXT,
        difficulty INTEGER,
        concept_correct INTEGER,
        language_rating INTEGER,
        useful INTEGER,
        recommended INTEGER,
        estimated_solve_time INTEGER,
        submitted_at TEXT,
        FOREIGN KEY (question_id) REFERENCES question_bank(id)
    )
    """)

    # ROOMS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT UNIQUE,
        teacher_email TEXT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        difficulty TEXT,
        question_mix TEXT,
        question_count INTEGER,
        assessment_strategy TEXT DEFAULT 'balanced',
        created_at TEXT
    )
    """)

    # ROOM QUESTION MAP
    cur.execute("""
    CREATE TABLE IF NOT EXISTS room_questions_map (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT,
        question_id INTEGER,
        source_type TEXT,
        created_at TEXT
    )
    """)

    # ROOM STUDENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS room_students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT,
        student_email TEXT,
        joined_at TEXT
    )
    """)

    # RAW TELEMETRY EVENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_telemetry_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        attempt_id TEXT,
        question_id INTEGER,
        event_type TEXT,
        event_value TEXT,
        timestamp TEXT
    )
    """)

    # FEATURE STORE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS feature_store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        attempt_id TEXT,
        question_id INTEGER,
        response_time REAL,
        idle_time REAL,
        rewrite_count INTEGER,
        backspace_count INTEGER,
        attempts INTEGER,
        hover_count INTEGER,
        same_option_clicks INTEGER,
        reflection_length INTEGER,
        focus_lost_count INTEGER
    )
    """)

    # RESPONSES EXPANDED
    cur.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT,
        student_email TEXT,
        attempt_id TEXT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        question_id INTEGER,
        question_text TEXT,
        response_time REAL,
        idle_time REAL,
        rewrite_count INTEGER,
        backspace_count INTEGER,
        attempts INTEGER,
        confidence REAL,
        correct INTEGER,
        hesitation_score REAL,
        confidence_error REAL,
        engagement_score REAL,
        understanding_pred INTEGER,
        behavior_pred TEXT,
        strategy_pred TEXT,
        cognitive_flag TEXT,
        hover_count INTEGER,
        same_option_clicks INTEGER,
        reflection_length INTEGER,
        behavior_model_version TEXT DEFAULT 'v2.4',
        understanding_model_version TEXT DEFAULT 'v1.9',
        strategy_model_version TEXT DEFAULT 'v3.1',
        dataset_version TEXT DEFAULT 'v1.0',
        selected_option TEXT,
        correct_option TEXT,
        created_at TEXT
    )
    """)

    # REPORTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        room_code TEXT,
        attempt_id TEXT,
        report_json TEXT,
        dataset_version TEXT DEFAULT 'v1.0',
        kg_version TEXT DEFAULT 'v1.0',
        model_version TEXT DEFAULT 'v2.0',
        created_at TEXT
    )
    """)

    # PERSISTENT COGNITIVE DIGITAL TWIN PROFILE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_cognitive_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT UNIQUE,
        learning_velocity REAL DEFAULT 0.5,
        conceptual_depth REAL DEFAULT 0.5,
        confidence_stability REAL DEFAULT 0.5,
        attention_stability REAL DEFAULT 0.5,
        persistence REAL DEFAULT 0.5,
        memory_dependence REAL DEFAULT 0.5,
        transfer_ability REAL DEFAULT 0.5,
        curiosity REAL DEFAULT 0.5,
        attempt_count INTEGER DEFAULT 0,
        updated_at TEXT
    )
    """)

    # HUMAN FEEDBACK LOGS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS human_feedback_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type TEXT,
        record_id INTEGER,
        user_email TEXT,
        override_label TEXT,
        override_reason TEXT,
        submitted_at TEXT
    )
    """)

    # EVIDENCE PIPELINE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS evidence_pipeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        response_id INTEGER,
        telemetry_summary TEXT,
        probabilities_json TEXT,
        triggered_overrides TEXT,
        confidence_score REAL,
        FOREIGN KEY (response_id) REFERENCES responses(id)
    )
    """)

    # Fallback legacy student_profiles
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT UNIQUE,
        avg_conceptual REAL,
        avg_hesitation REAL,
        avg_confidence REAL,
        dominant_pattern TEXT,
        weak_subjects TEXT,
        tests_taken INTEGER,
        updated_at TEXT
    )
    """)

    # TEACHER NOTES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT,
        teacher_email TEXT,
        observation TEXT,
        reason TEXT,
        action_taken TEXT,
        outcome TEXT,
        created_at TEXT
    )
    """)

    # ASSESSMENT BLUEPRINTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS assessment_blueprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        teacher_email TEXT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        purpose TEXT,
        duration INTEGER,
        question_count INTEGER,
        conceptual_pct REAL,
        application_pct REAL,
        reasoning_pct REAL,
        memory_pct REAL,
        difficulty TEXT,
        assessment_strategy TEXT,
        version INTEGER DEFAULT 1,
        parent_blueprint_id INTEGER,
        created_at TEXT
    )
    """)


    # Append-only Cognitive Memory Events
    cur.execute('''
    CREATE TABLE IF NOT EXISTS student_memory_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        node_id TEXT,
        memory_type TEXT, -- 'concept', 'misconception', 'intervention'
        retrieval_strength REAL,
        storage_strength REAL,
        confidence REAL,
        update_reason TEXT,
        evidence_count INTEGER,
        effectiveness_delta REAL,
        memory_model_version TEXT DEFAULT 'v1.0',
        timestamp TEXT
    )
    ''')

    # --- Week 8: Educational Memory v2.0 Tables ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)

    # Seed default parameters in memory_config table
    mem_defaults = {
        "DEFAULT_DECAY_RATE": 0.05,
        "DEFAULT_INITIAL_STRENGTH": 0.3,
        "REINFORCE_BOOST": 0.15,
        "FAILURE_PENALTY": 0.2,
        "FORGETTING_THRESHOLD": 0.4,
        "ALERT_THRESHOLD_STRENGTH": 0.3,
        "REVIEW_INTERVAL_FACTOR": 7.0,
        "WEIGHT_MEMORY_RISK": 0.3,
        "WEIGHT_MISCONCEPTION_SEVERITY": 0.2,
        "WEIGHT_PREREQUISITE_IMPORTANCE": 0.2,
        "WEIGHT_TEACHER_PRIORITY": 0.15,
        "WEIGHT_EXAM_WEIGHT": 0.15
    }
    now_str = datetime.now().isoformat()
    for k, val in mem_defaults.items():
        try:
            cur.execute("""
                INSERT OR IGNORE INTO memory_config (key, value, config_version, updated_by, updated_at)
                VALUES (?, ?, 'v1.0', 'system', ?)
            """, (k, val, now_str))
        except Exception:
            pass

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        event_type TEXT,
        payload TEXT,
        event_version TEXT DEFAULT 'v2.0',
        source_module TEXT,
        algorithm_version TEXT DEFAULT 'v2.0',
        qqi_version TEXT DEFAULT 'v1.2',
        twin_version TEXT DEFAULT 'v2.0',
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS concept_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        memory_strength REAL,
        forgetting_rate REAL,
        memory_state TEXT,
        memory_confidence REAL,
        memory_explanation TEXT,
        derived_from TEXT,
        trigger_event_id INTEGER,
        config_version TEXT DEFAULT 'v1.0',
        reinforcement_count INTEGER,
        retrieval_success_rate REAL,
        last_success TEXT,
        last_failure TEXT,
        next_review_date TEXT,
        last_updated TEXT,
        UNIQUE(student_email, concept_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory_state_transitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        old_state TEXT,
        new_state TEXT,
        trigger_event_id INTEGER,
        reason TEXT,
        timestamp TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS review_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        scheduled_date TEXT,
        status TEXT,
        priority REAL,
        created_at TEXT,
        UNIQUE(student_email, concept_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        alert_type TEXT,
        severity TEXT,
        description TEXT,
        status TEXT DEFAULT 'active',
        timestamp TEXT
    )
    """)

    # --- Week 10: QQI Calibration Feedback Loop ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qqi_calibration_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS calibration_runs (
        run_id TEXT PRIMARY KEY,
        started_at TEXT,
        completed_at TEXT,
        config_version TEXT DEFAULT 'v1.0',
        questions_processed INTEGER DEFAULT 0,
        alerts_created INTEGER DEFAULT 0,
        questions_quarantined INTEGER DEFAULT 0,
        execution_time_ms REAL DEFAULT 0.0,
        status TEXT DEFAULT 'running',
        alerts_resolved INTEGER DEFAULT 0,
        replay_jobs_created INTEGER DEFAULT 0,
        replay_jobs_completed INTEGER DEFAULT 0,
        replay_jobs_failed INTEGER DEFAULT 0,
        average_replay_time_ms REAL DEFAULT 0.0
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qqi_calibration_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        old_qqi REAL,
        new_qqi REAL,
        old_difficulty TEXT,
        new_difficulty TEXT,
        reason TEXT,
        calibration_run_id TEXT,
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qqi_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        alert_type TEXT,
        severity TEXT DEFAULT 'medium',
        description TEXT,
        calibration_run_id TEXT,
        status TEXT DEFAULT 'active',
        resolved_by TEXT,
        resolution_action TEXT,
        resolved_at TEXT,
        created_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS replay_jobs (
        job_id TEXT PRIMARY KEY,
        question_id INTEGER,
        student_email TEXT,
        status TEXT DEFAULT 'pending',
        attempts INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 3,
        retry_count INTEGER DEFAULT 0,
        created_at TEXT,
        started_at TEXT,
        completed_at TEXT,
        last_error TEXT,
        worker_id TEXT
    )
    """)

    # --- Week 11: NBIRT (Neural Bayesian Item Response Theory) ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS nbirt_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS nbirt_runs (
        run_id TEXT PRIMARY KEY,
        started_at TEXT,
        completed_at TEXT,
        items_estimated INTEGER DEFAULT 0,
        students_estimated INTEGER DEFAULT 0,
        em_iterations INTEGER DEFAULT 0,
        max_parameter_delta REAL DEFAULT 0.0,
        status TEXT DEFAULT 'running',
        config_version TEXT DEFAULT 'v1.0',
        execution_time_ms REAL DEFAULT 0.0
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS nbirt_item_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        run_id TEXT,
        old_b REAL,
        new_b REAL,
        old_a REAL,
        new_a REAL,
        irt_confidence REAL,
        n_responses INTEGER,
        algorithm_version TEXT DEFAULT 'v1.0',
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS nbirt_ability_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        run_id TEXT,
        old_ability REAL,
        new_ability REAL,
        old_se REAL,
        new_se REAL,
        old_percentile REAL,
        new_percentile REAL,
        prior_used TEXT,
        n_items_used INTEGER,
        irt_confidence REAL,
        algorithm_version TEXT DEFAULT 'v1.0',
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT
    )
    """)

    now_nbirt = datetime.now().isoformat()
    nbirt_defaults = {
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
    for k, v in nbirt_defaults.items():
        cur.execute(
            "INSERT OR IGNORE INTO nbirt_config (key, value, config_version, updated_by, updated_at) VALUES (?, ?, 'v1.0', 'system', ?)",
            (k, v, now_nbirt)
        )

    # --- Week 12: Cognitive Load Intelligence Engine (CCLI) ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cognitive_load_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cognitive_load_events (
        event_id TEXT PRIMARY KEY,
        response_id INTEGER,
        student_email TEXT,
        concept_id TEXT,
        intrinsic_load REAL,
        extraneous_load REAL,
        germane_load REAL,
        composite_load REAL,
        explanation_json TEXT,
        algorithm_version TEXT DEFAULT 'v1.0',
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT,
        FOREIGN KEY (response_id) REFERENCES responses(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_cognitive_load_state (
        student_email TEXT PRIMARY KEY,
        rolling_il REAL,
        rolling_el REAL,
        rolling_gl REAL,
        rolling_ccli REAL,
        confidence REAL,
        last_computed_at TEXT,
        alert_status TEXT DEFAULT 'normal',
        config_version TEXT DEFAULT 'v1.0'
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cognitive_load_alerts (
        alert_id TEXT PRIMARY KEY,
        student_email TEXT,
        ccli_value REAL,
        severity TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT,
        resolved_at TEXT,
        resolution_note TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cognitive_load_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        old_ccli REAL,
        new_ccli REAL,
        alert_status TEXT,
        timestamp TEXT
    )
    """)

    now_ccli = datetime.now().isoformat()
    ccli_defaults = {
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
    for k, v in ccli_defaults.items():
        cur.execute(
            "INSERT OR IGNORE INTO cognitive_load_config (key, value, config_version, updated_by, updated_at) VALUES (?, ?, 'v1.0', 'system', ?)",
            (k, v, now_ccli)
        )

    # --- Week 13: Cognitive Decision Orchestrator (CDO) ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decision_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decision_runs (
        run_id TEXT PRIMARY KEY,
        student_email TEXT,
        concept_id TEXT,
        final_decision TEXT,
        confidence_score REAL,
        decision_stability TEXT,
        stability_score REAL,
        decision_policy_version TEXT DEFAULT 'v1.0',
        trigger_source TEXT,
        timestamp TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decision_explanations (
        run_id TEXT PRIMARY KEY,
        student_email TEXT,
        concept_id TEXT,
        winning_rule TEXT,
        candidates_json TEXT,
        conflicts_json TEXT,
        decision_reason TEXT,
        decision_stability TEXT,
        stability_score REAL,
        decision_policy_version TEXT DEFAULT 'v1.0',
        FOREIGN KEY (run_id) REFERENCES decision_runs(run_id)
    )
    """)

    # --- Week 14: Cross-Platform Cognitive Telemetry Engine (CTE) ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_telemetry_store (
        event_id TEXT PRIMARY KEY,
        student_email TEXT,
        device_type TEXT,
        event_type TEXT,
        payload_json TEXT,
        timestamp TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS derived_behavior_features (
        student_email TEXT,
        concept_id TEXT,
        interaction_entropy REAL DEFAULT 0.0,
        hesitation_index REAL DEFAULT 0.0,
        reading_speed REAL DEFAULT 0.0,
        correction_rate REAL DEFAULT 0.0,
        focus_loss_count INTEGER DEFAULT 0,
        typing_cadence REAL DEFAULT 0.0,
        scroll_entropy REAL DEFAULT 0.0,
        last_computed_at TEXT,
        PRIMARY KEY (student_email, concept_id)
    )
    """)

    now_cdo = datetime.now().isoformat()
    cdo_defaults = {
        "priority_rule_teacher": 100.0,
        "priority_rule_load": 90.0,
        "priority_rule_misconception": 80.0,
        "priority_rule_apd": 70.0,
        "priority_rule_memory": 60.0,
        "priority_rule_nbirt": 50.0,
    }
    for k, v in cdo_defaults.items():
        cur.execute(
            "INSERT OR IGNORE INTO decision_config (key, value, config_version, updated_by, updated_at) VALUES (?, ?, 'v1.0', 'system', ?)",
            (k, v, now_cdo)
        )

    conn.commit()
    conn.close()

def upgrade_semantic_schema():

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
        ALTER TABLE question_bank
        ADD COLUMN semantic_id TEXT
        """)
    except:
        pass

    try:
        cur.execute("""
        ALTER TABLE question_bank
        ADD COLUMN variant_id TEXT
        """)
    except:
        pass

    conn.commit()
    conn.close()
    
# =========================
# USER FUNCTIONS
# =========================
def create_user(data):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users
        (name, age, email, password, education, learning_style, subjects, confidence, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["age"],
        data["email"],
        data["password"],
        data["education"],
        data["learningStyle"],
        ", ".join(data["subjects"]),
        data["confidence"],
        data["role"],
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_user(email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# =========================
# ROOM FUNCTIONS
# =========================
def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def create_room(data):
    conn = get_conn()
    cur = conn.cursor()

    room_code = generate_room_code()

    cur.execute("""
        INSERT INTO rooms (
            room_code,
            teacher_email,
            subject,
            topic,
            subtopic,
            difficulty,
            question_mix,
            question_count,
            assessment_strategy,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        room_code,
        data["teacher_email"],
        data["subject"],
        data["topic"],
        data["subtopic"],
        data.get("difficulty", "mixed"),
        data.get("question_mix", "mixed"),
        data.get("question_count", 5),
        data.get("assessment_strategy", "balanced"),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return room_code


def get_teacher_rooms(email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM rooms WHERE teacher_email = ? ORDER BY id DESC", (email,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def join_room(data):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM rooms WHERE room_code = ?", (data["room_code"],))
    room = cur.fetchone()

    if not room:
        conn.close()
        return None

    cur.execute("""
        INSERT INTO room_students (room_code, student_email, joined_at)
        VALUES (?, ?, ?)
    """, (
        data["room_code"],
        data["student_email"],
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return dict(room)


def get_student_room(email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT rooms.* FROM rooms
        JOIN room_students ON rooms.room_code = room_students.room_code
        WHERE room_students.student_email = ?
        ORDER BY room_students.id DESC
        LIMIT 1
    """, (email,))

    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None


# =========================
# RESPONSE + REPORT SAVE
# =========================
def save_response(student_email, obj):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO responses (
            room_code, student_email, attempt_id, subject, topic, subtopic,
            question_id, question_text,
            response_time, idle_time, rewrite_count, backspace_count,
            attempts, confidence, correct,
            hesitation_score, confidence_error, engagement_score,
            understanding_pred, behavior_pred, strategy_pred,
            cognitive_flag, hover_count, same_option_clicks, reflection_length,
            behavior_model_version, understanding_model_version, strategy_model_version, dataset_version,
            assessment_blueprint_id, assessment_version,
            selected_option_index,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        obj.get("room_code", "solo"),
        student_email,
        obj.get("attempt_id", "default_attempt"),
        obj.get("subject", ""),
        obj.get("topic", ""),
        obj.get("subtopic", ""),
        obj.get("question_id"),
        obj.get("question_text"),
        obj.get("response_time"),
        obj.get("idle_time"),
        obj.get("rewrite_count"),
        obj.get("backspace_count"),
        obj.get("attempts"),
        obj.get("confidence"),
        obj.get("correct"),
        obj.get("hesitation_score"),
        obj.get("confidence_error"),
        obj.get("engagement_score"),
        obj.get("understanding_pred"),
        obj.get("behavior_pred"),
        obj.get("strategy_pred"),
        obj.get("cognitive_flag"),
        obj.get("hover_count"),
        obj.get("same_option_clicks"),
        obj.get("reflection_length"),
        obj.get("behavior_model_version", "v2.4"),
        obj.get("understanding_model_version", "v1.9"),
        obj.get("strategy_model_version", "v3.1"),
        obj.get("dataset_version", "v1.0"),
        obj.get("assessment_blueprint_id"),
        obj.get("assessment_version"),
        obj.get("selected_option_index")
    ))

    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id



def save_final_report(student_email, report_obj, room_code="solo"):
    conn = get_conn()
    cur = conn.cursor()

    blueprint_id = None
    blueprint_version = None

    if room_code and room_code != "solo":
        cur.execute("SELECT assessment_blueprint_id, assessment_version FROM rooms WHERE room_code = ?", (room_code,))
        r_row = cur.fetchone()
        if r_row:
            blueprint_id = r_row["assessment_blueprint_id"]
            blueprint_version = r_row["assessment_version"]

    cur.execute("""
        INSERT INTO reports (
            student_email, room_code, attempt_id, report_json, dataset_version, kg_version, model_version,
            assessment_blueprint_id, assessment_version, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_email,
        room_code,
        report_obj.get("attempt_id", "default_attempt"),
        json.dumps(report_obj),
        report_obj.get("dataset_version", "v1.0"),
        report_obj.get("kg_version", "v1.0"),
        report_obj.get("model_version", "v2.0"),
        blueprint_id,
        blueprint_version,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_all_subjects():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT subject FROM question_bank ORDER BY subject")
    rows = cur.fetchall()
    conn.close()
    return [r["subject"] for r in rows]


def get_topics_by_subject(subject):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT topic FROM question_bank WHERE subject=? ORDER BY topic", (subject,))
    rows = cur.fetchall()
    conn.close()
    return [r["topic"] for r in rows]


def get_subtopics(subject, topic):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT subtopic FROM question_bank
        WHERE subject=? AND topic=?
        ORDER BY subtopic
    """, (subject, topic))
    rows = cur.fetchall()
    conn.close()
    return [r["subtopic"] for r in rows]


def get_room_questions(subject, topic, subtopic, limit_count=5, question_source="system", teacher_email=None):
    conn = get_conn()
    cur = conn.cursor()

    cognitive_types = ["memory", "conceptual", "tricky", "application", "reasoning", "elimination"]
    final_questions = []

    # Build SQL filter
    filters = "subject=? AND topic=? AND subtopic=?"
    params = [subject, topic, subtopic]
    
    if question_source == "custom" and teacher_email:
        filters += " AND teacher_added = 1 AND teacher_email = ?"
        params.append(teacher_email)
    elif question_source == "system":
        filters += " AND (teacher_added = 0 OR teacher_added IS NULL)"
    elif question_source == "mixed":
        if teacher_email:
            filters += " AND ((teacher_added = 0 OR teacher_added IS NULL) OR (teacher_added = 1 AND teacher_email = ?))"
            params.append(teacher_email)
        else:
            filters += " AND (teacher_added = 0 OR teacher_added IS NULL)"

    # 1. try cognitive distribution (1 from each type)
    for ct in cognitive_types:
        cur.execute(f"""
            SELECT * FROM question_bank
            WHERE {filters} AND cognitive_type=?
            ORDER BY RANDOM()
            LIMIT 1
        """, params + [ct])

        row = cur.fetchone()
        if row:
            final_questions.append(row)

    # 2. fallback if not enough questions
    if len(final_questions) < limit_count:
        remaining = limit_count - len(final_questions)
        exclude_ids = ",".join([str(q['id']) for q in final_questions]) if final_questions else "0"
        
        cur.execute(f"""
            SELECT * FROM question_bank
            WHERE {filters} AND id NOT IN ({exclude_ids})
            ORDER BY RANDOM()
            LIMIT ?
        """, params + [remaining])

        extra_rows = cur.fetchall()
        final_questions.extend(extra_rows)

    conn.close()

    # format output
    formatted = []
    for r in final_questions:
        formatted.append({
            "id": r["id"],
            "prompt": r["prompt"],
            "options": [
                r["option_a"],
                r["option_b"],
                r["option_c"],
                r["option_d"]
            ],
            "correctIndex": r["correct_index"],
            "cognitive_type": r["cognitive_type"] or "conceptual",
            "difficulty": r["difficulty"] or "medium"
        })

    return formatted

def map_questions_to_room(room_code, question_list):
    conn = get_conn()
    cur = conn.cursor()

    for q in question_list:
        cur.execute("""
            INSERT INTO room_questions_map (room_code, question_id, source_type, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            room_code,
            q["id"],
            "question_bank",
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()


def get_locked_room_questions(room_code):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT qb.*
        FROM room_questions_map rqm
        JOIN question_bank qb ON qb.id = rqm.question_id
        WHERE rqm.room_code = ?
        ORDER BY rqm.id ASC
    """, (room_code,))

    rows = cur.fetchall()
    conn.close()

    final = []

    for r in rows:
        final.append({
            "id": r["id"],
            "prompt": r["prompt"],
            "options": [
                r["option_a"],
                r["option_b"],
                r["option_c"],
                r["option_d"]
            ],
            "correctIndex": r["correct_index"]
        })

    return final

# =========================
# FETCH STUDENT RESPONSES
# =========================
def get_student_responses(student_email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM responses
        WHERE student_email = ?
        ORDER BY id ASC
    """, (student_email,))

    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]


# =========================
# CLEAR STUDENT RESPONSES AFTER REPORT
# =========================
def clear_student_responses(student_email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM responses
        WHERE student_email = ?
    """, (student_email,))

    conn.commit()
    conn.close()


def get_student_responses(student_email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM responses
        WHERE student_email = ?
        ORDER BY id ASC
    """, (student_email,))

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_attempt_responses(student_email, attempt_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM responses
        WHERE student_email = ? AND attempt_id = ?
        ORDER BY id ASC
    """, (student_email, attempt_id))

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_adaptive_question(subject, topic, subtopic, current_difficulty, cognitive_type):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM question_bank
        WHERE subject=? AND topic=? AND subtopic=?
        AND difficulty=? AND cognitive_type=?
        ORDER BY RANDOM()
        LIMIT 1
    """, (subject, topic, subtopic, current_difficulty, cognitive_type))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "prompt": row["prompt"],
        "options": [
            row["option_a"],
            row["option_b"],
            row["option_c"],
            row["option_d"]
        ],
        "correctIndex": row["correct_index"]
    }


def upgrade_question_bank_schema():
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE question_bank ADD COLUMN cognitive_type TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE question_bank ADD COLUMN explanation TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE question_bank ADD COLUMN image_url TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE question_bank ADD COLUMN source_exam TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE question_bank ADD COLUMN teacher_added INTEGER DEFAULT 0")
    except:
        pass

    try:
        cur.execute("ALTER TABLE question_bank ADD COLUMN tags TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE question_bank ADD COLUMN created_at TEXT")
    except:
        pass
    try:
        cur.execute("ALTER TABLE question_bank ADD COLUMN estimated_time INTEGER")
    except:
        pass

    conn.commit()
    conn.close()


def upgrade_database_schema():
    conn = get_conn()
    cur = conn.cursor()

    # responses table extensions
    alterations_responses = [
        ("behavior_model_version", "TEXT DEFAULT 'v2.4'"),
        ("understanding_model_version", "TEXT DEFAULT 'v1.9'"),
        ("strategy_model_version", "TEXT DEFAULT 'v3.1'"),
        ("dataset_version", "TEXT DEFAULT 'v1.0'"),
        ("assessment_blueprint_id", "INTEGER"),
        ("assessment_version", "INTEGER"),
        ("selected_option_index", "INTEGER"),
        ("selected_option", "TEXT"),
        ("correct_option", "TEXT")
    ]
    for col_name, col_type in alterations_responses:
        try:
            cur.execute(f"ALTER TABLE responses ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass # column already exists

    # reports table extensions
    alterations_reports = [
        ("attempt_id", "TEXT"),
        ("dataset_version", "TEXT DEFAULT 'v1.0'"),
        ("kg_version", "TEXT DEFAULT 'v1.0'"),
        ("model_version", "TEXT DEFAULT 'v2.0'"),
        ("assessment_blueprint_id", "INTEGER"),
        ("assessment_version", "INTEGER")
    ]
    for col_name, col_type in alterations_reports:
        try:
            cur.execute(f"ALTER TABLE reports ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass # column already exists

    # question_bank additions (concept mapping details)
    alterations_question_bank = [
        ("explanation", "TEXT"),
        ("image_url", "TEXT"),
        ("source_exam", "TEXT"),
        ("teacher_added", "INTEGER DEFAULT 0"),
        ("teacher_email", "TEXT"),
        ("tags", "TEXT"),
        ("estimated_time", "INTEGER"),
        ("purpose", "TEXT DEFAULT 'practice'"),
        ("cognitive_load", "TEXT DEFAULT 'medium'"),
        ("status", "TEXT DEFAULT 'Draft'"),
        ("version", "INTEGER DEFAULT 1"),
        ("qqi_score", "REAL DEFAULT 80.0"),
        ("qqi_confidence", "REAL DEFAULT 0.1"),
        ("student_responses_count", "INTEGER DEFAULT 0"),
        ("purity_score", "REAL DEFAULT 80.0"),
        ("discrimination_score", "REAL DEFAULT 80.0"),
        ("difficulty_stability_score", "REAL DEFAULT 80.0"),
        ("guess_resistance_score", "REAL DEFAULT 80.0"),
        ("language_quality_score", "REAL DEFAULT 80.0"),
        ("behavior_signal_score", "REAL DEFAULT 80.0"),
        ("kg_mapping_score", "REAL DEFAULT 80.0"),
        ("time_stability_score", "REAL DEFAULT 80.0"),
        ("teacher_rating_score", "REAL DEFAULT 80.0"),
        ("historical_reliability_score", "REAL DEFAULT 80.0"),
        ("parent_question_id", "INTEGER"),
        ("current_version", "INTEGER DEFAULT 1"),
        ("edited_by", "TEXT"),
        ("edited_at", "TEXT"),
        ("change_reason", "TEXT"),
        ("irt_difficulty", "REAL"),
        ("irt_discrimination", "REAL"),
        ("irt_guessing", "REAL DEFAULT 0.0"),
        ("irt_run_id", "TEXT"),
        ("irt_confidence", "REAL"),
        ("irt_version", "TEXT DEFAULT 'v1.0'")
    ]
    for col_name, col_type in alterations_question_bank:
        try:
            cur.execute(f"ALTER TABLE question_bank ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    # rooms additions (assessment strategy)
    alterations_rooms = [
        ("assessment_strategy", "TEXT DEFAULT 'balanced'"),
        ("assessment_blueprint_id", "INTEGER"),
        ("assessment_version", "INTEGER")
    ]
    for col_name, col_type in alterations_rooms:
        try:
            cur.execute(f"ALTER TABLE rooms ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    # student_cognitive_profiles additions
    alterations_student_profiles = [
        ("irt_ability", "REAL"),
        ("irt_ability_se", "REAL"),
        ("irt_ability_percentile", "REAL"),
        ("irt_confidence", "REAL"),
        ("irt_ability_version", "TEXT DEFAULT 'v1.0'")
    ]
    for col_name, col_type in alterations_student_profiles:
        try:
            cur.execute(f"ALTER TABLE student_cognitive_profiles ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    # Ensure teacher_reviews table is created for existing DBs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        teacher_email TEXT,
        difficulty INTEGER,
        concept_correct INTEGER,
        language_rating INTEGER,
        useful INTEGER,
        recommended INTEGER,
        submitted_at TEXT,
        FOREIGN KEY (question_id) REFERENCES question_bank(id)
    )
    """)

    # Alter teacher_reviews table extensions
    alterations_reviews = [
        ("estimated_solve_time", "INTEGER"),
        ("action", "TEXT DEFAULT 'Submitted'"),
        ("change_reason", "TEXT")
    ]
    for col_name, col_type in alterations_reviews:
        try:
            cur.execute(f"ALTER TABLE teacher_reviews ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    # Create qqi_history table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qqi_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        qqi_score REAL,
        qqi_confidence REAL,
        trigger_event TEXT,
        timestamp TEXT,
        score_delta REAL DEFAULT 0.0,
        confidence_delta REAL DEFAULT 0.0,
        sub_score_deltas TEXT,
        FOREIGN KEY (question_id) REFERENCES question_bank(id)
    )
    """)

    # Create question_versions table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        version INTEGER,
        prompt TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_index INTEGER,
        explanation TEXT,
        difficulty TEXT,
        cognitive_type TEXT,
        edited_by TEXT,
        change_reason TEXT,
        calibration_reason TEXT,
        edited_at TEXT,
        qqi_before REAL,
        qqi_after REAL,
        confidence_before REAL,
        confidence_after REAL,
        change_summary TEXT,
        FOREIGN KEY (question_id) REFERENCES question_bank(id)
    )
    """)

    # Check if we need to migrate
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kg_nodes'")
    table_exists = cur.fetchone() is not None
    
    need_migration = False
    if table_exists:
        cur.execute("PRAGMA table_info(kg_nodes)")
        info = cur.fetchall()
        for col in info:
            if col["name"] == "id" and "INTEGER" in col["type"].upper():
                need_migration = True
                break
                
    if need_migration:
        print("[MIGRATION] Old integer ID graph tables detected. Renaming to backup...")
        cur.execute("DROP TABLE IF EXISTS backup_kg_nodes_v1")
        cur.execute("DROP TABLE IF EXISTS backup_kg_edges_v1")
        cur.execute("DROP TABLE IF EXISTS backup_student_concept_mastery_v1")
        
        cur.execute("ALTER TABLE kg_nodes RENAME TO backup_kg_nodes_v1")
        cur.execute("ALTER TABLE kg_edges RENAME TO backup_kg_edges_v1")
        cur.execute("ALTER TABLE student_concept_mastery RENAME TO backup_student_concept_mastery_v1")
        conn.commit()

    # Create new kg_nodes table with TEXT primary key
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kg_nodes (
        id TEXT PRIMARY KEY,
        name TEXT,
        type TEXT, -- 'subject', 'topic', 'subtopic', 'concept', 'micro_concept', 'learning_objective', 'skill', 'misconception', 'question'
        description TEXT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        difficulty REAL DEFAULT 50.0,
        expected_time INTEGER DEFAULT 60,
        bloom_level TEXT DEFAULT 'remember',
        grade TEXT DEFAULT 'undergraduate',
        importance REAL DEFAULT 1.0,
        version INTEGER DEFAULT 1,
        mastery_level REAL DEFAULT 0.0,
        created_at TEXT,
        updated_at TEXT,
        metadata TEXT,
        status TEXT DEFAULT 'production',
        discovery_method TEXT DEFAULT 'expert',
        validation_count INTEGER DEFAULT 0,
        statistical_confidence REAL DEFAULT 0.0,
        teacher_confidence REAL DEFAULT 0.0,
        historical_stability REAL DEFAULT 1.0,
        overall_confidence REAL DEFAULT 0.0,
        canonical_id TEXT,
        severity TEXT DEFAULT 'moderate',
        recommended_intervention TEXT
    )
    """)

    # Create new kg_edges table referencing TEXT primary key and with confidence column
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kg_edges (
        source_id TEXT,
        target_id TEXT,
        relation_type TEXT, -- 'parent_of', 'prerequisite_of', 'targets_concept', 'remedies_misconception', 'strengthens', 'weakens', 'related_to', 'tested_by'
        weight REAL DEFAULT 1.0,
        confidence REAL DEFAULT 0.95,
        discovery_method TEXT DEFAULT 'human',
        discovery_date TEXT,
        validation_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'production',
        stability_score REAL DEFAULT 1.0,
        statistical_confidence REAL DEFAULT 0.0,
        teacher_confidence REAL DEFAULT 0.0,
        historical_stability REAL DEFAULT 1.0,
        overall_confidence REAL DEFAULT 0.0,
        PRIMARY KEY (source_id, target_id, relation_type),
        FOREIGN KEY (source_id) REFERENCES kg_nodes(id),
        FOREIGN KEY (target_id) REFERENCES kg_nodes(id)
    )
    """)

    # Alter kg_edges table extensions for existing DBs
    alterations_kg_edges = [
        ("discovery_method", "TEXT DEFAULT 'human'"),
        ("discovery_date", "TEXT"),
        ("validation_count", "INTEGER DEFAULT 0"),
        ("status", "TEXT DEFAULT 'production'"),
        ("stability_score", "REAL DEFAULT 1.0"),
        ("statistical_confidence", "REAL DEFAULT 0.0"),
        ("teacher_confidence", "REAL DEFAULT 0.0"),
        ("historical_stability", "REAL DEFAULT 1.0"),
        ("overall_confidence", "REAL DEFAULT 0.0")
    ]
    for col_name, col_type in alterations_kg_edges:
        try:
            cur.execute(f"ALTER TABLE kg_edges ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    # Create new student_concept_mastery table referencing TEXT primary key
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_concept_mastery (
        student_email TEXT,
        node_id TEXT,
        mastery_level REAL DEFAULT 0.0,
        last_attempt_at TEXT,
        PRIMARY KEY (student_email, node_id),
        FOREIGN KEY (node_id) REFERENCES kg_nodes(id)
    )
    """)

    # Create kg_versions table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kg_versions (
        version INTEGER PRIMARY KEY AUTOINCREMENT,
        graph_version TEXT,
        nodes_count INTEGER,
        edges_count INTEGER,
        nodes_added INTEGER,
        nodes_removed INTEGER,
        edges_added INTEGER,
        edges_removed INTEGER,
        migration_type TEXT,
        edited_by TEXT,
        change_summary TEXT,
        created_at TEXT
    )
    """)

    # --- Week 5: recommendations_log lifecycle migration ---
    # Check if recommendations_log exists with old schema (missing 'status' col)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recommendations_log'")
    rec_log_exists = cur.fetchone() is not None

    if rec_log_exists:
        cur.execute("PRAGMA table_info(recommendations_log)")
        rec_cols = {c[1] for c in cur.fetchall()}
        # Add any missing lifecycle and Context Engine v2 columns (safe ALTER TABLE)
        lifecycle_cols = [
            ("status", "TEXT DEFAULT 'generated'"),
            ("pre_score", "REAL DEFAULT 0.0"),
            ("post_score", "REAL DEFAULT 0.0"),
            ("improvement_percentage", "REAL DEFAULT 0.0"),
            ("validation_window_days", "REAL DEFAULT 0.0"),
            ("applied_at", "TEXT"),
            ("completed_at", "TEXT"),
            ("recommendation_confidence", "REAL DEFAULT 0.95"),
            ("expected_mastery_gain", "REAL DEFAULT 0.20"),
            ("actual_mastery_gain", "REAL DEFAULT 0.0"),
            ("outcome_label", "TEXT DEFAULT 'Insufficient Evidence'"),
            ("telemetry_audit", "TEXT"),
            ("context_device_type", "TEXT DEFAULT 'desktop'"),
            ("context_network_quality", "TEXT DEFAULT 'excellent'"),
            ("context_session_hour", "INTEGER DEFAULT 10"),
            ("context_class_size", "INTEGER DEFAULT 25"),
            ("scoring_breakdown", "TEXT"),
            ("config_version", "TEXT DEFAULT 'v2.0'"),
            ("context_quality", "TEXT DEFAULT 'FALLBACK'"),
            ("confidence_score", "REAL DEFAULT 1.0"),
            ("confidence_reason", "TEXT"),
        ]
        for col_name, col_def in lifecycle_cols:
            if col_name not in rec_cols:
                try:
                    cur.execute(f"ALTER TABLE recommendations_log ADD COLUMN {col_name} {col_def}")
                except Exception:
                    pass
    else:
        # Create fresh with full schema
        cur.execute("""
        CREATE TABLE recommendations_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT,
            concept_id TEXT,
            priority TEXT,
            reason TEXT,
            evidence_backing TEXT,
            suggested_action TEXT,
            timestamp TEXT,
            status TEXT DEFAULT 'generated',
            pre_score REAL DEFAULT 0.0,
            post_score REAL DEFAULT 0.0,
            improvement_percentage REAL DEFAULT 0.0,
            validation_window_days REAL DEFAULT 0.0,
            applied_at TEXT,
            completed_at TEXT,
            recommendation_confidence REAL DEFAULT 0.95,
            expected_mastery_gain REAL DEFAULT 0.20,
            actual_mastery_gain REAL DEFAULT 0.0,
            outcome_label TEXT DEFAULT 'Insufficient Evidence',
            telemetry_audit TEXT,
            context_device_type TEXT DEFAULT 'desktop',
            context_network_quality TEXT DEFAULT 'excellent',
            context_session_hour INTEGER DEFAULT 10,
            context_class_size INTEGER DEFAULT 25,
            scoring_breakdown TEXT,
            config_version TEXT DEFAULT 'v2.0',
            context_quality TEXT DEFAULT 'FALLBACK',
            confidence_score REAL DEFAULT 1.0,
            confidence_reason TEXT
        )
        """)

    # Create pilot_sessions table (Refinement 2)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pilot_sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        classroom_id TEXT,
        teacher TEXT,

        subject TEXT,
        topic TEXT,
        total_students INTEGER DEFAULT 0,
        total_attempts INTEGER DEFAULT 0,
        average_latency REAL DEFAULT 0.0,
        completion_rate REAL DEFAULT 0.0,
        recommendation_count INTEGER DEFAULT 0,
        created_at TEXT,
        assessment_type TEXT,
        device_type TEXT,
        browser TEXT,
        network_quality TEXT,
        session_duration REAL
    )
    """)

    # Create validation_snapshots table (Refinement 3)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS validation_snapshots (
        snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        recommendation_acceptance REAL,
        application_rate REAL,
        success_rate REAL,
        QQI_error REAL,
        KG_coverage REAL,
        report_latency REAL,
        telemetry_events INTEGER,
        student_count INTEGER,
        teacher_count INTEGER
    )
    """)

    # Ensure kg_evolution_log has confidence_delta column
    try:
        cur.execute("ALTER TABLE kg_evolution_log ADD COLUMN confidence_delta REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass

    # Create apd_config table if not exists (upgrade scenario)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS apd_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    defaults = {
        "STAT_WEIGHT": 0.4,
        "TEACHER_WEIGHT": 0.3,
        "HISTORY_WEIGHT": 0.2,
        "SAMPLE_WEIGHT": 0.1,
        "MIN_SAMPLE_SIZE": 30,
        "EFFECT_SIZE_THRESHOLD": 0.15,
        "DEPRECATE_THRESHOLD": 0.4,
        "DECAY_LAMBDA": 0.005,
        "HISTORY_WINDOW": 30
    }
    for k, v in defaults.items():
        try:
            cur.execute("INSERT OR IGNORE INTO apd_config (key, value) VALUES (?, ?)", (k, str(v)))
        except sqlite3.OperationalError:
            pass

    # Alter kg_edges
    try:
        cur.execute("ALTER TABLE kg_edges ADD COLUMN edge_id TEXT")
    except sqlite3.OperationalError:
        pass

    # Alter kg_edge_evidence
    evidence_alters = [
        ("edge_id", "TEXT"),
        ("supporting_students", "INTEGER DEFAULT 0"),
        ("contradicting_students", "INTEGER DEFAULT 0"),
        ("effect_size", "REAL DEFAULT 0.0"),
        ("last_updated", "TEXT"),
        ("algorithm_version", "TEXT DEFAULT 'v2.0'"),
        ("sample_size", "INTEGER DEFAULT 0"),
        ("status", "TEXT DEFAULT 'ai_candidate'"),
        ("cohort_id", "TEXT DEFAULT 'default_cohort'"),
        ("institution", "TEXT DEFAULT 'default_institution'"),
        ("grade", "TEXT DEFAULT 'default_grade'"),
        ("curriculum", "TEXT DEFAULT 'default_curriculum'"),
        ("academic_year", "TEXT DEFAULT '2026'"),
        ("graph_version", "TEXT DEFAULT 'v2.1'"),
        ("qqi_version", "TEXT DEFAULT 'v1.2'"),
        ("model_version", "TEXT DEFAULT 'v2.0'")
    ]
    for col_name, col_type in evidence_alters:
        try:
            cur.execute(f"ALTER TABLE kg_edge_evidence ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    # Alter kg_evolution_log
    log_alters = [
        ("edge_id", "TEXT"),
        ("old_confidence", "REAL DEFAULT 0.0"),
        ("new_confidence", "REAL DEFAULT 0.0"),
        ("reason", "TEXT"),
        ("model_version", "TEXT DEFAULT 'v2.0'"),
        ("teacher_action", "TEXT")
    ]
    for col_name, col_type in log_alters:
        try:
            cur.execute(f"ALTER TABLE kg_evolution_log ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    # Create misconception_config table if not exists (upgrade scenario)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS misconception_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    mcp_defaults = {
        "MIN_STUDENT_COUNT": 5,
        "MIN_WRONG_ANSWERS": 10,
        "CONFIDENCE_THRESHOLD": 0.5,
        "SEVERITY_THRESHOLD": 0.5,
        "CLUSTER_SIZE_WEIGHT": 0.3,
        "BEHAVIOR_CONSISTENCY_WEIGHT": 0.3,
        "MASTERY_CONSISTENCY_WEIGHT": 0.2,
        "TEACHER_AGREEMENT_WEIGHT": 0.2
    }
    for k, v in mcp_defaults.items():
        try:
            cur.execute("INSERT OR IGNORE INTO misconception_config (key, value) VALUES (?, ?)", (k, str(v)))
        except sqlite3.OperationalError:
            pass

    # Create misconception_clusters table if not exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS misconception_clusters (
        cluster_id TEXT PRIMARY KEY,
        concept_id TEXT,
        misconception_name TEXT,
        description TEXT,
        selected_option TEXT,
        correct_option TEXT,
        confidence_size REAL,
        confidence_behavior REAL,
        confidence_mastery REAL,
        confidence_teacher REAL,
        cluster_confidence REAL,
        confidence_level TEXT,
        severity TEXT,
        status TEXT DEFAULT 'candidate',
        parent_cluster_id TEXT,
        canonical_cluster_id TEXT,
        recommended_intervention_id TEXT,
        intervention_confidence REAL,
        intervention_source TEXT,
        memory_event_id TEXT,
        memory_status TEXT DEFAULT 'pending',
        created_at TEXT,
        last_updated TEXT,
        algorithm_version TEXT DEFAULT 'v2.0',
        graph_version TEXT DEFAULT 'v2.1',
        qqi_version TEXT DEFAULT 'v1.2',
        assessment_version TEXT DEFAULT 'v1.0',
        model_version TEXT DEFAULT 'v2.0',
        FOREIGN KEY (concept_id) REFERENCES kg_nodes(id)
    )
    """)

    # Create misconception_evidence table if not exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS misconception_evidence (
        id TEXT PRIMARY KEY,
        cluster_id TEXT,
        question_id INTEGER,
        student_count INTEGER,
        wrong_answer_count INTEGER,
        avg_hesitation REAL,
        avg_response_time REAL,
        cohort_id TEXT,
        institution TEXT,
        grade TEXT,
        curriculum TEXT,
        academic_year TEXT,
        explanation TEXT,
        created_at TEXT,
        FOREIGN KEY (cluster_id) REFERENCES misconception_clusters(cluster_id)
    )
    """)

    # Create misconception_evolution_log table if not exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS misconception_evolution_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_id TEXT,
        old_status TEXT,
        new_status TEXT,
        old_confidence REAL,
        new_confidence REAL,
        reason TEXT,
        actor TEXT,
        timestamp TEXT,
        teacher_action TEXT,
        FOREIGN KEY (cluster_id) REFERENCES misconception_clusters(cluster_id)
    )
    """)

    conn.commit()

    # Perform migration if backups exist
    if need_migration:
        print("[MIGRATION] Migrating data to the new schema...")
        cur.execute("SELECT * FROM backup_kg_nodes_v1")
        old_nodes = [dict(row) for row in cur.fetchall()]
        
        # Helper to generate permanent IDs
        import re
        def make_permanent_id(sub, top, subt, name, typ):
            parts = []
            if sub: parts.append(sub.lower().strip())
            if top: parts.append(top.lower().strip())
            if subt: parts.append(subt.lower().strip())
            if typ not in ('subject', 'topic', 'subtopic'):
                parts.append(name.lower().strip())
            raw = ".".join(parts)
            s_id = re.sub(r'[^a-z0-9._-]', '_', raw)
            s_id = re.sub(r'\.+', '.', s_id).strip('.')
            return s_id

        # Insert migrated nodes
        id_mapping = {} # old_int_id -> new_string_id
        now_str = datetime.utcnow().isoformat()
        
        for n in old_nodes:
            old_id = n["id"]
            if n["type"] == "question":
                new_id = f"question.{n['name'].replace('question_', '')}"
            else:
                new_id = make_permanent_id(n["subject"], n["topic"], n["subtopic"], n["name"], n["type"])
                
            base_new_id = new_id
            suffix = 1
            while new_id in id_mapping.values():
                new_id = f"{base_new_id}_{suffix}"
                suffix += 1
                
            id_mapping[old_id] = new_id
            
            cur.execute("""
                INSERT OR IGNORE INTO kg_nodes (
                    id, name, type, description, subject, topic, subtopic,
                    difficulty, expected_time, bloom_level, grade, importance,
                    version, mastery_level, created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_id, n["name"], n["type"], n["description"], n["subject"],
                n["topic"], n["subtopic"], n["difficulty"], n["expected_time"],
                n["bloom_level"], n["grade"], n["importance"], n["version"],
                n["mastery_level"], n["created_at"] or now_str, n["updated_at"] or now_str,
                n["metadata"] or '{}'
            ))

        # Insert migrated edges
        cur.execute("SELECT * FROM backup_kg_edges_v1")
        old_edges = [dict(row) for row in cur.fetchall()]
        edges_migrated = 0
        for e in old_edges:
            new_source = id_mapping.get(e["source_id"])
            new_target = id_mapping.get(e["target_id"])
            if new_source and new_target:
                cur.execute("""
                    INSERT OR IGNORE INTO kg_edges (source_id, target_id, relation_type, weight, confidence)
                    VALUES (?, ?, ?, ?, 0.95)
                """, (new_source, new_target, e["relation_type"], e["weight"]))
                edges_migrated += 1

        # Insert migrated mastery
        cur.execute("SELECT * FROM backup_student_concept_mastery_v1")
        old_mastery = [dict(row) for row in cur.fetchall()]
        for m in old_mastery:
            new_node = id_mapping.get(m["node_id"])
            if new_node:
                cur.execute("""
                    INSERT OR IGNORE INTO student_concept_mastery (student_email, node_id, mastery_level, last_attempt_at)
                    VALUES (?, ?, ?, ?)
                """, (m["student_email"], new_node, m["mastery_level"], m["last_attempt_at"]))
                
        # Log version record
        cur.execute("""
            INSERT INTO kg_versions (
                graph_version, nodes_count, edges_count, nodes_added, nodes_removed,
                edges_added, edges_removed, migration_type, edited_by, change_summary, created_at
            ) VALUES (?, ?, ?, ?, 0, ?, 0, 'database_migration', 'system', ?, ?)
        """, (
            "v1.0-migration", len(id_mapping), edges_migrated, len(id_mapping), edges_migrated,
            "Migrated Knowledge Graph tables from Integer IDs to permanent Hierarchical String IDs", now_str
        ))
        
        conn.commit()
        print(f"[MIGRATION] Migration complete. Migrated {len(id_mapping)} nodes and {edges_migrated} edges successfully.")

    # --- Week 8: Educational Memory v2.0 Tables ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)

    # Seed default parameters in memory_config table
    mem_defaults = {
        "DEFAULT_DECAY_RATE": 0.05,
        "DEFAULT_INITIAL_STRENGTH": 0.3,
        "REINFORCE_BOOST": 0.15,
        "FAILURE_PENALTY": 0.2,
        "FORGETTING_THRESHOLD": 0.4,
        "ALERT_THRESHOLD_STRENGTH": 0.3,
        "REVIEW_INTERVAL_FACTOR": 7.0,
        "WEIGHT_MEMORY_RISK": 0.3,
        "WEIGHT_MISCONCEPTION_SEVERITY": 0.2,
        "WEIGHT_PREREQUISITE_IMPORTANCE": 0.2,
        "WEIGHT_TEACHER_PRIORITY": 0.15,
        "WEIGHT_EXAM_WEIGHT": 0.15
    }
    now_str = datetime.now().isoformat()
    for k, val in mem_defaults.items():
        try:
            cur.execute("""
                INSERT OR IGNORE INTO memory_config (key, value, config_version, updated_by, updated_at)
                VALUES (?, ?, 'v1.0', 'system', ?)
            """, (k, val, now_str))
        except Exception:
            pass

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        event_type TEXT,
        payload TEXT,
        event_version TEXT DEFAULT 'v2.0',
        source_module TEXT,
        algorithm_version TEXT DEFAULT 'v2.0',
        qqi_version TEXT DEFAULT 'v1.2',
        twin_version TEXT DEFAULT 'v2.0',
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS concept_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        memory_strength REAL,
        forgetting_rate REAL,
        memory_state TEXT,
        memory_confidence REAL,
        memory_explanation TEXT,
        derived_from TEXT,
        trigger_event_id INTEGER,
        config_version TEXT DEFAULT 'v1.0',
        reinforcement_count INTEGER,
        retrieval_success_rate REAL,
        last_success TEXT,
        last_failure TEXT,
        next_review_date TEXT,
        last_updated TEXT,
        UNIQUE(student_email, concept_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory_state_transitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        old_state TEXT,
        new_state TEXT,
        trigger_event_id INTEGER,
        reason TEXT,
        timestamp TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS review_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        scheduled_date TEXT,
        status TEXT,
        priority REAL,
        created_at TEXT,
        UNIQUE(student_email, concept_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        concept_id TEXT,
        alert_type TEXT,
        severity TEXT,
        description TEXT,
        status TEXT DEFAULT 'active',
        timestamp TEXT
    )
    """)

    # --- Week 9: Context Engine v2.0 Configuration ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS context_recommendations_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v2.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)

    context_defaults = {
        # Cognitive weights (must sum to 1.0)
        "WEIGHT_MEMORY_RISK": 0.3,
        "WEIGHT_PREREQUISITE_IMPORTANCE": 0.2,
        "WEIGHT_MISCONCEPTION_SEVERITY": 0.2,
        "WEIGHT_QQI_CONFIDENCE": 0.1,
        "WEIGHT_TEACHER_PRIORITY": 0.1,
        "WEIGHT_EXAM_WEIGHT": 0.1,
        "WEIGHT_IRT_ALIGNMENT": 0.15,
        
        # Device multipliers
        "MULTIPLIER_DEVICE_MOBILE_REMEDIATION": 0.6,
        "MULTIPLIER_DEVICE_MOBILE_PRACTICE": 0.8,
        "MULTIPLIER_DEVICE_MOBILE_REVIEW": 1.2,
        "MULTIPLIER_DEVICE_TABLET_REMEDIATION": 0.9,
        "MULTIPLIER_DEVICE_TABLET_PRACTICE": 1.0,
        "MULTIPLIER_DEVICE_TABLET_REVIEW": 1.1,
        "MULTIPLIER_DEVICE_DESKTOP_REMEDIATION": 1.0,
        "MULTIPLIER_DEVICE_DESKTOP_PRACTICE": 1.0,
        "MULTIPLIER_DEVICE_DESKTOP_REVIEW": 1.0,
        
        # Network multipliers
        "MULTIPLIER_NETWORK_POOR_REMEDIATION": 0.2,
        "MULTIPLIER_NETWORK_POOR_PRACTICE": 0.7,
        "MULTIPLIER_NETWORK_POOR_REVIEW": 1.1,
        "MULTIPLIER_NETWORK_AVERAGE_REMEDIATION": 0.7,
        "MULTIPLIER_NETWORK_AVERAGE_PRACTICE": 0.9,
        "MULTIPLIER_NETWORK_AVERAGE_REVIEW": 1.0,
        "MULTIPLIER_NETWORK_GOOD_REMEDIATION": 1.0,
        "MULTIPLIER_NETWORK_GOOD_PRACTICE": 1.0,
        "MULTIPLIER_NETWORK_GOOD_REVIEW": 1.0,
        "MULTIPLIER_NETWORK_EXCELLENT_REMEDIATION": 1.0,
        "MULTIPLIER_NETWORK_EXCELLENT_PRACTICE": 1.0,
        "MULTIPLIER_NETWORK_EXCELLENT_REVIEW": 1.0,
        
        # Time-of-day multipliers
        "MULTIPLIER_TIME_LATE_NIGHT_REMEDIATION": 0.5,
        "MULTIPLIER_TIME_LATE_NIGHT_PRACTICE": 0.8,
        "MULTIPLIER_TIME_LATE_NIGHT_REVIEW": 1.2,
        "MULTIPLIER_TIME_SCHOOL_HOURS_REMEDIATION": 1.1,
        "MULTIPLIER_TIME_SCHOOL_HOURS_PRACTICE": 1.1,
        "MULTIPLIER_TIME_SCHOOL_HOURS_REVIEW": 0.9,
        "MULTIPLIER_TIME_STANDARD_REMEDIATION": 1.0,
        "MULTIPLIER_TIME_STANDARD_PRACTICE": 1.0,
        "MULTIPLIER_TIME_STANDARD_REVIEW": 1.0,
        
        # Class-size multipliers
        "MULTIPLIER_CLASS_LARGE_REMEDIATION": 0.8,
        "MULTIPLIER_CLASS_LARGE_PRACTICE": 1.1,
        "MULTIPLIER_CLASS_LARGE_REVIEW": 1.0,
        "MULTIPLIER_CLASS_SMALL_REMEDIATION": 1.1,
        "MULTIPLIER_CLASS_SMALL_PRACTICE": 1.0,
        "MULTIPLIER_CLASS_SMALL_REVIEW": 1.0,
    }

    now_str_ctx = datetime.now().isoformat()
    for k, val in context_defaults.items():
        try:
            cur.execute("""
                INSERT OR IGNORE INTO context_recommendations_config (key, value, config_version, updated_by, updated_at)
                VALUES (?, ?, 'v2.0', 'system', ?)
            """, (k, val, now_str_ctx))
        except Exception:
            pass

    # --- Week 10: QQI Calibration Feedback Loop ---

    # QQI Calibration Configuration table (all thresholds read from DB)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qqi_calibration_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)

    qqi_cal_defaults = {
        "min_responses_for_calibration": 10.0,
        "high_memory_threshold": 0.8,
        "low_memory_threshold": 0.3,
        "high_memory_failure_rate_limit": 0.20,
        "low_memory_success_rate_limit": 0.20,
        "qqi_quarantine_threshold": 70.0,
        "drift_alert_threshold": 15.0,
        "max_replay_retries": 3.0,
    }
    now_str_qqi = datetime.now().isoformat()
    for k, val in qqi_cal_defaults.items():
        try:
            cur.execute("""
                INSERT OR IGNORE INTO qqi_calibration_config (key, value, config_version, updated_by, updated_at)
                VALUES (?, ?, 'v1.0', 'system', ?)
            """, (k, val, now_str_qqi))
        except Exception:
            pass

    # Calibration Run Ledger
    cur.execute("""
    CREATE TABLE IF NOT EXISTS calibration_runs (
        run_id TEXT PRIMARY KEY,
        started_at TEXT,
        completed_at TEXT,
        config_version TEXT DEFAULT 'v1.0',
        questions_processed INTEGER DEFAULT 0,
        alerts_created INTEGER DEFAULT 0,
        questions_quarantined INTEGER DEFAULT 0,
        execution_time_ms REAL DEFAULT 0.0,
        status TEXT DEFAULT 'running',
        alerts_resolved INTEGER DEFAULT 0,
        replay_jobs_created INTEGER DEFAULT 0,
        replay_jobs_completed INTEGER DEFAULT 0,
        replay_jobs_failed INTEGER DEFAULT 0,
        average_replay_time_ms REAL DEFAULT 0.0
    )
    """)

    # QQI Calibration History (append-only, never overwritten)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qqi_calibration_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        old_qqi REAL,
        new_qqi REAL,
        old_difficulty TEXT,
        new_difficulty TEXT,
        reason TEXT,
        calibration_run_id TEXT,
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT,
        FOREIGN KEY (calibration_run_id) REFERENCES calibration_runs(run_id)
    )
    """)

    # QQI Alerts for teacher review
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qqi_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        alert_type TEXT,
        severity TEXT DEFAULT 'medium',
        description TEXT,
        calibration_run_id TEXT,
        status TEXT DEFAULT 'active',
        resolved_by TEXT,
        resolution_action TEXT,
        resolved_at TEXT,
        created_at TEXT,
        FOREIGN KEY (calibration_run_id) REFERENCES calibration_runs(run_id)
    )
    """)

    # Replay Jobs Queue (asynchronous, never synchronous during quarantine)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS replay_jobs (
        job_id TEXT PRIMARY KEY,
        question_id INTEGER,
        student_email TEXT,
        status TEXT DEFAULT 'pending',
        attempts INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 3,
        retry_count INTEGER DEFAULT 0,
        created_at TEXT,
        started_at TEXT,
        completed_at TEXT,
        last_error TEXT,
        worker_id TEXT
    )
    """)

    # --- Week 12: Cognitive Load Intelligence Engine (CCLI) ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cognitive_load_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cognitive_load_events (
        event_id TEXT PRIMARY KEY,
        response_id INTEGER,
        student_email TEXT,
        concept_id TEXT,
        intrinsic_load REAL,
        extraneous_load REAL,
        germane_load REAL,
        composite_load REAL,
        explanation_json TEXT,
        algorithm_version TEXT DEFAULT 'v1.0',
        config_version TEXT DEFAULT 'v1.0',
        timestamp TEXT,
        FOREIGN KEY (response_id) REFERENCES responses(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_cognitive_load_state (
        student_email TEXT PRIMARY KEY,
        rolling_il REAL,
        rolling_el REAL,
        rolling_gl REAL,
        rolling_ccli REAL,
        confidence REAL,
        last_computed_at TEXT,
        alert_status TEXT DEFAULT 'normal',
        config_version TEXT DEFAULT 'v1.0'
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cognitive_load_alerts (
        alert_id TEXT PRIMARY KEY,
        student_email TEXT,
        ccli_value REAL,
        severity TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT,
        resolved_at TEXT,
        resolution_note TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cognitive_load_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        old_ccli REAL,
        new_ccli REAL,
        alert_status TEXT,
        timestamp TEXT
    )
    """)

    now_ccli = datetime.now().isoformat()
    ccli_defaults = {
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
    for k, v in ccli_defaults.items():
        cur.execute(
            "INSERT OR IGNORE INTO cognitive_load_config (key, value, config_version, updated_by, updated_at) VALUES (?, ?, 'v1.0', 'system', ?)",
            (k, v, now_ccli)
        )

    # --- Week 13: Cognitive Decision Orchestrator (CDO) ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decision_config (
        key TEXT PRIMARY KEY,
        value REAL,
        config_version TEXT DEFAULT 'v1.0',
        updated_by TEXT DEFAULT 'system',
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decision_runs (
        run_id TEXT PRIMARY KEY,
        student_email TEXT,
        concept_id TEXT,
        final_decision TEXT,
        confidence_score REAL,
        decision_stability TEXT,
        stability_score REAL,
        decision_policy_version TEXT DEFAULT 'v1.0',
        trigger_source TEXT,
        timestamp TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decision_explanations (
        run_id TEXT PRIMARY KEY,
        student_email TEXT,
        concept_id TEXT,
        winning_rule TEXT,
        candidates_json TEXT,
        conflicts_json TEXT,
        decision_reason TEXT,
        decision_stability TEXT,
        stability_score REAL,
        decision_policy_version TEXT DEFAULT 'v1.0',
        FOREIGN KEY (run_id) REFERENCES decision_runs(run_id)
    )
    """)

    # --- Week 14: Cross-Platform Cognitive Telemetry Engine (CTE) ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_telemetry_store (
        event_id TEXT PRIMARY KEY,
        student_email TEXT,
        device_type TEXT,
        event_type TEXT,
        payload_json TEXT,
        timestamp TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS derived_behavior_features (
        student_email TEXT,
        concept_id TEXT,
        interaction_entropy REAL DEFAULT 0.0,
        hesitation_index REAL DEFAULT 0.0,
        reading_speed REAL DEFAULT 0.0,
        correction_rate REAL DEFAULT 0.0,
        focus_loss_count INTEGER DEFAULT 0,
        typing_cadence REAL DEFAULT 0.0,
        scroll_entropy REAL DEFAULT 0.0,
        last_computed_at TEXT,
        PRIMARY KEY (student_email, concept_id)
    )
    """)

    now_cdo = datetime.now().isoformat()
    cdo_defaults = {
        "priority_rule_teacher": 100.0,
        "priority_rule_load": 90.0,
        "priority_rule_misconception": 80.0,
        "priority_rule_apd": 70.0,
        "priority_rule_memory": 60.0,
        "priority_rule_nbirt": 50.0,
    }
    for k, v in cdo_defaults.items():
        cur.execute(
            "INSERT OR IGNORE INTO decision_config (key, value, config_version, updated_by, updated_at) VALUES (?, ?, 'v1.0', 'system', ?)",
            (k, v, now_cdo)
        )

    conn.commit()
    conn.close()

    
    # Seed the Knowledge Graph
    seed_knowledge_graph()



def save_raw_telemetry_event(student_email, attempt_id, question_id, event_type, event_value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO raw_telemetry_events (student_email, attempt_id, question_id, event_type, event_value, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (student_email, attempt_id, question_id, event_type, str(event_value), datetime.now().isoformat()))
    conn.commit()
    conn.close()


def save_feature_store(student_email, attempt_id, question_id, features):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO feature_store (
            student_email, attempt_id, question_id, response_time, idle_time,
            rewrite_count, backspace_count, attempts, hover_count,
            same_option_clicks, reflection_length, focus_lost_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_email,
        attempt_id,
        question_id,
        features.get("response_time", 0.0),
        features.get("idle_time", 0.0),
        features.get("rewrite_count", 0),
        features.get("backspace_count", 0),
        features.get("attempts", 1),
        features.get("hover_count", 0),
        features.get("same_option_clicks", 0),
        features.get("reflection_length", 0),
        features.get("focus_lost_count", 0)
    ))
    conn.commit()
    conn.close()


def save_evidence_pipeline(response_id, telemetry_summary, probabilities_json, triggered_overrides, confidence_score):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO evidence_pipeline (response_id, telemetry_summary, probabilities_json, triggered_overrides, confidence_score)
        VALUES (?, ?, ?, ?, ?)
    """, (response_id, json.dumps(telemetry_summary), json.dumps(probabilities_json), json.dumps(triggered_overrides), confidence_score))
    conn.commit()
    conn.close()


def get_student_cognitive_profile(student_email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM student_cognitive_profiles WHERE student_email = ?", (student_email,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_student_cognitive_profile(student_email, profile):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO student_cognitive_profiles (
            student_email, learning_velocity, conceptual_depth, confidence_stability,
            attention_stability, persistence, memory_dependence, transfer_ability,
            curiosity, attempt_count, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        ON CONFLICT(student_email) DO UPDATE SET
            learning_velocity = excluded.learning_velocity,
            conceptual_depth = excluded.conceptual_depth,
            confidence_stability = excluded.confidence_stability,
            attention_stability = excluded.attention_stability,
            persistence = excluded.persistence,
            memory_dependence = excluded.memory_dependence,
            transfer_ability = excluded.transfer_ability,
            curiosity = excluded.curiosity,
            attempt_count = student_cognitive_profiles.attempt_count + 1,
            updated_at = excluded.updated_at
    """, (
        student_email,
        profile.get("learning_velocity", 0.5),
        profile.get("conceptual_depth", 0.5),
        profile.get("confidence_stability", 0.5),
        profile.get("attention_stability", 0.5),
        profile.get("persistence", 0.5),
        profile.get("memory_dependence", 0.5),
        profile.get("transfer_ability", 0.5),
        profile.get("curiosity", 0.5),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def save_human_feedback(source_type, record_id, user_email, override_label, override_reason):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO human_feedback_logs (source_type, record_id, user_email, override_label, override_reason, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (source_type, record_id, user_email, override_label, override_reason, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def seed_dynamic_concepts():
    conn = get_conn()
    cur = conn.cursor()

    # Define concepts
    concepts_list = [
        # Math Quadratic concepts
        ("Formula Recall", "Recalling the standard quadratic formula and coefficients", "math", "algebra", "quadratic", None, "Recall standard form and coefficients"),
        ("Discriminant", "Calculating and understanding the discriminant value", "math", "algebra", "quadratic", None, "Determine root nature using D = b^2 - 4ac"),
        ("Roots", "Finding and determining the nature of quadratic roots", "math", "algebra", "quadratic", None, "Solve for roots and categorize real vs imaginary"),
        ("Graph Interpretation", "Visualizing quadratic functions as parabolas", "math", "algebra", "quadratic", None, "Analyze parabolic graphs and orientation"),
        ("Application", "Applying quadratic equations to real-world scenarios", "math", "algebra", "quadratic", None, "Solve word problems using quadratic equations"),

        # Physics Mechanics concepts
        ("Inertia", "First law concepts and rotational mass properties", "physics", "mechanics", "laws_of_motion", None, "Explain state of motion resistance"),
        ("Force Dynamics", "Second law equation F = ma and acceleration responses", "physics", "mechanics", "laws_of_motion", None, "Calculate dynamics under net forces"),
        ("Action Reaction", "Third law action-reaction force pair cancellation checks", "physics", "mechanics", "laws_of_motion", None, "Identify paired forces acting on separate bodies"),
        ("Motion Graphs", "Slope and area calculations on mechanics graphs", "physics", "mechanics", "kinematics", None, "Compute velocity and acceleration from plots"),

        # DSA Arrays concepts
        ("Array Indexing", "Direct indexing limits and indexing offsets", "dsa", "arrays", "basics", None, "Access elements in O(1) complexity"),
        ("Contiguous Memory", "Memory addressing and size allocation properties", "dsa", "arrays", "basics", None, "Contrast memory layouts of static lists"),
        ("Complexity Analysis", "Worst case and average bounds on insertions or lookups", "dsa", "arrays", "basics", None, "Evaluate Big-O complexities"),
        ("Searching Algorithms", "Linear search vs binary search and sorting preconditions", "dsa", "arrays", "basics", None, "Execute searches on lists")
    ]

    for name, desc, sub, top, subt, parent, outcome in concepts_list:
        try:
            cur.execute("""
                INSERT INTO concepts (name, description, subject, topic, subtopic, parent_concept_id, learning_outcome)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, desc, sub, top, subt, parent, outcome))
        except sqlite3.IntegrityError:
            pass # concept already exists

    # Now let's map some existing questions to these concepts!
    cur.execute("SELECT id, prompt, tags, subject, subtopic FROM question_bank")
    questions = cur.fetchall()

    for q in questions:
        qid = q["id"]
        prompt = q["prompt"].lower()
        tags = (q["tags"] or "").lower()
        subject = q["subject"]
        subtopic = q["subtopic"]

        target_concept = None

        if subject == "math" and subtopic == "quadratic":
            if "discriminant" in prompt or "discriminant" in tags:
                target_concept = "Discriminant"
            elif "formula" in prompt or "formula" in tags:
                target_concept = "Formula Recall"
            elif "roots" in prompt or "roots" in tags:
                target_concept = "Roots"
            elif "graph" in prompt or "graph" in tags:
                target_concept = "Graph Interpretation"
            else:
                target_concept = "Application"

        elif subject == "physics" and subtopic == "laws_of_motion":
            if "inertia" in prompt or "inertia" in tags:
                target_concept = "Inertia"
            elif "force" in prompt or "acceleration" in prompt or "force" in tags:
                target_concept = "Force Dynamics"
            elif "action" in prompt or "cancel" in prompt:
                target_concept = "Action Reaction"
            else:
                target_concept = "Inertia"

        elif subject == "dsa" and subtopic == "basics":
            if "memory" in prompt or "contiguous" in prompt:
                target_concept = "Contiguous Memory"
            elif "index" in prompt or "indexing" in prompt:
                target_concept = "Array Indexing"
            elif "search" in prompt or "searching" in prompt:
                target_concept = "Searching Algorithms"
            elif "insert" in prompt or "complexity" in prompt or "worst case" in prompt:
                target_concept = "Complexity Analysis"
            else:
                target_concept = "Array Indexing"

        if target_concept:
            # Get concept id
            cur.execute("SELECT id FROM concepts WHERE name = ?", (target_concept,))
            c_row = cur.fetchone()
            if c_row:
                cid = c_row["id"]
                try:
                    cur.execute("""
                        INSERT INTO question_concepts (question_id, concept_id, weight)
                        VALUES (?, ?, ?)
                    """, (qid, cid, 1.0))
                except sqlite3.IntegrityError:
                    pass

    conn.commit()
    conn.close()


def seed_knowledge_graph():
    from datetime import datetime
    import json
    import re
    conn = get_conn()
    cur = conn.cursor()
    
    # Helper to generate permanent IDs
    def make_permanent_id(sub, top, subt, name, typ):
        parts = []
        if sub: parts.append(sub.lower().strip())
        if top: parts.append(top.lower().strip())
        if subt: parts.append(subt.lower().strip())
        if typ not in ('subject', 'topic', 'subtopic'):
            parts.append(name.lower().strip())
        raw = ".".join(parts)
        s_id = re.sub(r'[^a-z0-9._-]', '_', raw)
        s_id = re.sub(r'\.+', '.', s_id).strip('.')
        return s_id

    # List of nodes to seed:
    nodes = [
        # DSA Graph Nodes
        ("dsa", "subject", "Data Structures and Algorithms", "dsa", "", "", 50.0, 0, "remember", "undergraduate", 100.0),
        
        ("arrays", "topic", "Contiguous linear memory data structures", "dsa", "arrays", "", 30.0, 600, "understand", "undergraduate", 90.0),
        ("searching_algorithms", "topic", "Algorithms for locating items in collections", "dsa", "searching_algorithms", "", 45.0, 800, "apply", "undergraduate", 85.0),
        
        ("array_operations", "subtopic", "Insertions, deletions, and updates in arrays", "dsa", "arrays", "array_operations", 40.0, 300, "apply", "undergraduate", 80.0),
        ("binary_search", "subtopic", "Logarithmic interval division search on sorted lists", "dsa", "searching_algorithms", "binary_search", 60.0, 450, "analyze", "undergraduate", 85.0),
        
        ("array_deletion", "concept", "Removing elements from contiguous memory arrays", "dsa", "arrays", "array_operations", 50.0, 180, "analyze", "undergraduate", 75.0),
        ("divide_and_conquer", "concept", "Algorithmic design paradigm based on dividing problem space", "dsa", "searching_algorithms", "binary_search", 65.0, 240, "analyze", "undergraduate", 80.0),
        
        ("element_shifting", "micro_concept", "Moving subsequent elements to adjust index alignments after deletion", "dsa", "arrays", "array_operations", 55.0, 120, "apply", "undergraduate", 70.0),
        ("midpoint_calculation", "micro_concept", "Locating the center element in a boundary window", "dsa", "searching_algorithms", "binary_search", 60.0, 90, "apply", "undergraduate", 75.0),
        
        ("understand_linear_time_shifting", "learning_objective", "Verify why deletion of a middle element takes linear time O(n)", "dsa", "arrays", "array_operations", 50.0, 60, "understand", "undergraduate", 80.0),
        ("prevent_integer_overflow", "learning_objective", "Calculate middle index safely using low + (high - low)/2", "dsa", "searching_algorithms", "binary_search", 65.0, 90, "apply", "undergraduate", 85.0),
        
        ("index_manipulation_skill", "skill", "Perform manual index transformations without off-by-one errors", "dsa", "arrays", "array_operations", 60.0, 300, "apply", "undergraduate", 80.0),
        ("binary_search_index_tuning", "skill", "Configure search windows and shift pointers properly", "dsa", "searching_algorithms", "binary_search", 70.0, 400, "create", "undergraduate", 90.0),
        
        ("forgetting_to_shift_subsequent_items", "misconception", "Assuming deletion automatically shifts elements or replaces with null", "dsa", "arrays", "array_operations", 40.0, 0, "remember", "undergraduate", 50.0),
        ("midpoint_overflow_bug", "misconception", "Using (low + high) / 2 which overflows standard 32-bit integers", "dsa", "searching_algorithms", "binary_search", 55.0, 0, "understand", "undergraduate", 60.0),
        
        # Math Graph Nodes
        ("math", "subject", "Mathematics", "math", "", "", 50.0, 0, "remember", "undergraduate", 100.0),
        ("quadratic_equations", "topic", "Polynomial equations of degree 2", "math", "quadratic_equations", "", 40.0, 600, "understand", "undergraduate", 90.0),
        ("roots_of_quadratic", "subtopic", "Analyzing solution roots to quadratic equations", "math", "quadratic_equations", "roots_of_quadratic", 45.0, 300, "apply", "undergraduate", 85.0),
        ("discriminant_analysis", "concept", "Evaluating b^2 - 4ac to check solution nature", "math", "quadratic_equations", "roots_of_quadratic", 50.0, 180, "analyze", "undergraduate", 80.0),
        ("negative_discriminant", "micro_concept", "Roots behavior when discriminant is strictly negative", "math", "quadratic_equations", "roots_of_quadratic", 55.0, 120, "apply", "undergraduate", 75.0),
        ("determine_complex_roots", "learning_objective", "Solve and express complex roots in form a + bi", "math", "quadratic_equations", "roots_of_quadratic", 60.0, 90, "apply", "undergraduate", 80.0),
        ("complex_number_parsing", "skill", "Differentiate and represent real versus imaginary parts of algebraic equations", "math", "quadratic_equations", "roots_of_quadratic", 65.0, 240, "apply", "undergraduate", 85.0),
        ("assuming_negative_discriminant_means_no_roots", "misconception", "Believing quadratic equations have no solutions when D < 0, ignoring complex domain", "math", "quadratic_equations", "roots_of_quadratic", 45.0, 0, "understand", "undergraduate", 60.0),
        
        # Physics Graph Nodes
        ("physics", "subject", "Physics Foundations", "physics", "", "", 50.0, 0, "remember", "undergraduate", 100.0),
        ("classical_mechanics", "topic", "Study of motion of macroscopic bodies", "physics", "classical_mechanics", "", 45.0, 700, "understand", "undergraduate", 90.0),
        ("laws_of_motion", "subtopic", "Newtonian motion principles", "physics", "classical_mechanics", "laws_of_motion", 50.0, 400, "apply", "undergraduate", 85.0),
        ("inertia_and_mass", "concept", "Resistance to state changes of motion", "physics", "classical_mechanics", "laws_of_motion", 55.0, 200, "analyze", "undergraduate", 80.0),
        ("rotational_mass", "micro_concept", "Moment of inertia in angular acceleration rotational systems", "physics", "classical_mechanics", "laws_of_motion", 65.0, 150, "apply", "undergraduate", 75.0),
        ("rotational_inertia_calculation", "learning_objective", "Calculate moment of inertia for standard rigid shapes", "physics", "classical_mechanics", "laws_of_motion", 70.0, 120, "apply", "undergraduate", 80.0),
        ("angular_momentum_balancing", "skill", "Determine torque interactions and angular dynamics equilibrium", "physics", "classical_mechanics", "laws_of_motion", 75.0, 300, "apply", "undergraduate", 85.0),
        ("confusing_mass_with_rotational_inertia", "misconception", "Assuming moment of inertia depends purely on object mass, ignoring mass distribution", "physics", "classical_mechanics", "laws_of_motion", 50.0, 0, "understand", "undergraduate", 65.0),
        
        # Chemistry Graph Nodes
        ("chemistry", "subject", "Chemical Sciences", "chemistry", "", "", 50.0, 0, "remember", "undergraduate", 100.0),
        ("organic_chemistry", "topic", "Chemistry of carbon compound transformations", "chemistry", "organic_chemistry", "", 55.0, 700, "understand", "undergraduate", 90.0),
        ("functional_groups", "subtopic", "Functional group reactivities", "chemistry", "organic_chemistry", "functional_groups", 60.0, 400, "apply", "undergraduate", 85.0),
        ("isomerism", "concept", "Compounds with identical formulas but unique structural arrangements", "chemistry", "organic_chemistry", "functional_groups", 65.0, 220, "analyze", "undergraduate", 80.0),
        ("stereoisomerism", "micro_concept", "Three-dimensional orientation isomers", "chemistry", "organic_chemistry", "functional_groups", 70.0, 180, "apply", "undergraduate", 75.0),
        ("identify_chiral_centers", "learning_objective", "Locate chiral carbons and assign R/S stereocenters", "chemistry", "organic_chemistry", "functional_groups", 75.0, 150, "apply", "undergraduate", 80.0),
        ("stereocenter_determination", "skill", "Trace spatial symmetry and Cahn-Ingold-Prelog priority rules", "chemistry", "organic_chemistry", "functional_groups", 80.0, 300, "apply", "undergraduate", 85.0),
        ("confusing_enantiomers_with_diastereomers", "misconception", "Failing to distinguish between non-superimposable mirror images and non-mirror stereoisomers", "chemistry", "organic_chemistry", "functional_groups", 55.0, 0, "understand", "undergraduate", 60.0),
        
        # Biology Graph Nodes
        ("biology", "subject", "Biological Systems", "biology", "", "", 50.0, 0, "remember", "undergraduate", 100.0),
        ("genetics", "topic", "Study of heredity and genetic variation", "biology", "genetics", "", 45.0, 600, "understand", "undergraduate", 90.0),
        ("mendelian_inheritance", "subtopic", "Gregor Mendel laws of segregation and inheritance", "biology", "genetics", "mendelian_inheritance", 50.0, 300, "apply", "undergraduate", 85.0),
        ("punnett_squares", "concept", "Predicting genetic cross outcomes visually", "biology", "genetics", "mendelian_inheritance", 55.0, 180, "analyze", "undergraduate", 80.0),
        ("dihybrid_crosses", "micro_concept", "Genotypic distributions involving two independent traits", "biology", "genetics", "mendelian_inheritance", 65.0, 120, "apply", "undergraduate", 75.0),
        ("predict_genotypic_ratios", "learning_objective", "Calculate phenotypic ratios for dihybrid crossings", "biology", "genetics", "mendelian_inheritance", 70.0, 90, "apply", "undergraduate", 80.0),
        ("probability_multiplication_in_genetics", "skill", "Apply probability product rule for compound genetic events", "biology", "genetics", "mendelian_inheritance", 75.0, 200, "apply", "undergraduate", 85.0),
        ("assuming_independent_assortment_for_linked_genes", "misconception", "Ignoring linkage distance and assuming genes on the same chromosome assort independently", "biology", "genetics", "mendelian_inheritance", 50.0, 0, "understand", "undergraduate", 65.0),
        
        # English Graph Nodes
        ("english", "subject", "English Language and Linguistics", "english", "", "", 30.0, 0, "remember", "undergraduate", 100.0),
        ("grammar", "topic", "Rules governing sentence composition syntax", "english", "grammar", "", 35.0, 400, "understand", "undergraduate", 90.0),
        ("sentence_structure", "subtopic", "Phrase clauses construction clauses structure", "english", "grammar", "sentence_structure", 40.0, 200, "apply", "undergraduate", 85.0),
        ("modifiers", "concept", "Words/phrases modifying structural elements of sentences", "english", "grammar", "sentence_structure", 45.0, 120, "analyze", "undergraduate", 80.0),
        ("dangling_modifiers", "micro_concept", "Modifiers whose intended subject is missing or ambiguous", "english", "grammar", "sentence_structure", 50.0, 90, "apply", "undergraduate", 75.0),
        ("identify_modifier_placement", "learning_objective", "Detect and restructure dangling and misplaced clauses", "english", "grammar", "sentence_structure", 55.0, 60, "apply", "undergraduate", 80.0),
        ("modifier_dangling_correction", "skill", "Reconstruct sentences by inserting logical actor subjects", "english", "grammar", "sentence_structure", 60.0, 180, "apply", "undergraduate", 85.0),
        ("assuming_subject_is_implied", "misconception", "Assuming the reader naturally infers the missing subject in a modifier clause", "english", "grammar", "sentence_structure", 40.0, 0, "understand", "undergraduate", 60.0)
    ]
    
    # Save Nodes with their permanent IDs
    now_str = datetime.now().isoformat()
    id_map = {} # name -> generated_id
    for row in nodes:
        node_id = make_permanent_id(row[3], row[4], row[5], row[0], row[1])
        id_map[row[0]] = node_id
        
        cur.execute("""
            INSERT OR IGNORE INTO kg_nodes (
                id, name, type, description, subject, topic, subtopic,
                difficulty, expected_time, bloom_level, grade, importance,
                version, mastery_level, created_at, updated_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0.0, ?, ?, '{}')
        """, (node_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], now_str, now_str))
        
    conn.commit()
    
    # Edges: (source_name, target_name, relation_type, weight)
    edges = [
        # DSA Hierarchy
        ("dsa", "arrays", "parent_of", 1.0),
        ("dsa", "searching_algorithms", "parent_of", 1.0),
        ("arrays", "array_operations", "parent_of", 1.0),
        ("searching_algorithms", "binary_search", "parent_of", 1.0),
        ("array_operations", "array_deletion", "parent_of", 1.0),
        ("binary_search", "divide_and_conquer", "parent_of", 1.0),
        ("array_deletion", "element_shifting", "parent_of", 1.0),
        ("divide_and_conquer", "midpoint_calculation", "parent_of", 1.0),
        ("element_shifting", "understand_linear_time_shifting", "parent_of", 1.0),
        ("midpoint_calculation", "prevent_integer_overflow", "parent_of", 1.0),
        ("understand_linear_time_shifting", "index_manipulation_skill", "parent_of", 1.0),
        ("prevent_integer_overflow", "binary_search_index_tuning", "parent_of", 1.0),
        ("index_manipulation_skill", "forgetting_to_shift_subsequent_items", "parent_of", 1.0),
        ("binary_search_index_tuning", "midpoint_overflow_bug", "parent_of", 1.0),
        
        # DSA Prerequisites
        ("array_operations", "binary_search", "prerequisite_of", 1.0),
        ("index_manipulation_skill", "binary_search_index_tuning", "prerequisite_of", 1.0),
        
        # Math Hierarchy
        ("math", "quadratic_equations", "parent_of", 1.0),
        ("quadratic_equations", "roots_of_quadratic", "parent_of", 1.0),
        ("roots_of_quadratic", "discriminant_analysis", "parent_of", 1.0),
        ("discriminant_analysis", "negative_discriminant", "parent_of", 1.0),
        ("negative_discriminant", "determine_complex_roots", "parent_of", 1.0),
        ("determine_complex_roots", "complex_number_parsing", "parent_of", 1.0),
        ("complex_number_parsing", "assuming_negative_discriminant_means_no_roots", "parent_of", 1.0),
        
        # Physics Hierarchy
        ("physics", "classical_mechanics", "parent_of", 1.0),
        ("classical_mechanics", "laws_of_motion", "parent_of", 1.0),
        ("laws_of_motion", "inertia_and_mass", "parent_of", 1.0),
        ("inertia_and_mass", "rotational_mass", "parent_of", 1.0),
        ("rotational_mass", "rotational_inertia_calculation", "parent_of", 1.0),
        ("rotational_mass", "angular_momentum_balancing", "parent_of", 1.0),
        ("angular_momentum_balancing", "confusing_mass_with_rotational_inertia", "parent_of", 1.0),
        
        # Chemistry Hierarchy
        ("chemistry", "organic_chemistry", "parent_of", 1.0),
        ("organic_chemistry", "functional_groups", "parent_of", 1.0),
        ("functional_groups", "isomerism", "parent_of", 1.0),
        ("isomerism", "stereoisomerism", "parent_of", 1.0),
        ("stereoisomerism", "identify_chiral_centers", "parent_of", 1.0),
        ("identify_chiral_centers", "stereocenter_determination", "parent_of", 1.0),
        ("stereocenter_determination", "confusing_enantiomers_with_diastereomers", "parent_of", 1.0),
        
        # Biology Hierarchy
        ("biology", "genetics", "parent_of", 1.0),
        ("genetics", "mendelian_inheritance", "parent_of", 1.0),
        ("mendelian_inheritance", "punnett_squares", "parent_of", 1.0),
        ("punnett_squares", "dihybrid_crosses", "parent_of", 1.0),
        ("dihybrid_crosses", "predict_genotypic_ratios", "parent_of", 1.0),
        ("predict_genotypic_ratios", "probability_multiplication_in_genetics", "parent_of", 1.0),
        ("probability_multiplication_in_genetics", "assuming_independent_assortment_for_linked_genes", "parent_of", 1.0),
        
        # English Hierarchy
        ("english", "grammar", "parent_of", 1.0),
        ("grammar", "sentence_structure", "parent_of", 1.0),
        ("sentence_structure", "modifiers", "parent_of", 1.0),
        ("modifiers", "dangling_modifiers", "parent_of", 1.0),
        ("dangling_modifiers", "identify_modifier_placement", "parent_of", 1.0),
        ("identify_modifier_placement", "modifier_dangling_correction", "parent_of", 1.0),
        ("modifier_dangling_correction", "assuming_subject_is_implied", "parent_of", 1.0)
    ]
    
    # Save Edges with edge confidence defaulting to 0.95
    for src, tgt, rel, wt in edges:
        src_id = id_map.get(src)
        tgt_id = id_map.get(tgt)
        if src_id and tgt_id:
            cur.execute("""
                INSERT OR IGNORE INTO kg_edges (source_id, target_id, relation_type, weight, confidence)
                VALUES (?, ?, ?, ?, 0.95)
            """, (src_id, tgt_id, rel, wt))
            
    conn.commit()
    
    # Connect existing question_bank questions to the graph dynamically!
    cur.execute("SELECT id, prompt, subject, subtopic, topic FROM question_bank")
    questions = cur.fetchall()
    
    for q in questions:
        qid = q["id"]
        prompt = q["prompt"].lower()
        subject = q["subject"]
        subtopic = q["subtopic"]
        
        # Create a unique node name for this question (following period separator style)
        q_node_name = f"question.{qid}"
        
        # Check if question node already exists in kg_nodes
        cur.execute("SELECT id FROM kg_nodes WHERE id = ?", (q_node_name,))
        qn_row = cur.fetchone()
        
        if qn_row:
            qn_id = qn_row["id"]
        else:
            cur.execute("""
                INSERT INTO kg_nodes (
                    id, name, type, description, subject, topic, subtopic,
                    difficulty, expected_time, bloom_level, grade, importance,
                    version, mastery_level, created_at, updated_at, metadata
                ) VALUES (?, ?, 'question', ?, ?, ?, ?, 50.0, 45, 'apply', 'undergraduate', 1.0, 1, 0.0, ?, ?, '{}')
            """, (q_node_name, q_node_name, q["prompt"], subject, q["topic"], subtopic, now_str, now_str))
            qn_id = q_node_name
            
        # Determine which concept node in the graph this question targets
        target_concept = None
        
        if subject == "math" and subtopic == "quadratic":
            target_concept = "determine_complex_roots"
        elif subject == "physics" and subtopic == "laws_of_motion":
            target_concept = "rotational_inertia_calculation"
        elif subject == "dsa":
            if "index" in prompt or "indexing" in prompt or "delete" in prompt:
                target_concept = "understand_linear_time_shifting"
            else:
                target_concept = "prevent_integer_overflow"
        elif subject == "chemistry":
            target_concept = "identify_chiral_centers"
        elif subject == "biology":
            target_concept = "predict_genotypic_ratios"
        elif subject == "english":
            target_concept = "identify_modifier_placement"
            
        # Create tested_by relation between concept and question node
        if target_concept and target_concept in id_map:
            concept_nid = id_map[target_concept]
            # Relation: Concept is tested_by Question
            cur.execute("""
                INSERT OR IGNORE INTO kg_edges (source_id, target_id, relation_type, weight, confidence)
                VALUES (?, ?, ?, ?, 0.95)
            """, (concept_nid, qn_id, 'tested_by', 1.0))
            
    conn.commit()
    conn.close()
    print("[OK] Seeding of living Knowledge Graph completed successfully.")


def save_teacher_notes(room_code, teacher_email, observation, reason, action_taken, outcome):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO teacher_notes (room_code, teacher_email, observation, reason, action_taken, outcome, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (room_code, teacher_email, observation, reason, action_taken, outcome, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_teacher_notes(room_code):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM teacher_notes WHERE room_code = ? ORDER BY id DESC", (room_code,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =========================
# ASSESSMENT BLUEPRINTS & LIFECYCLE
# =========================
def create_assessment_blueprint(data):
    conn = get_conn()
    cur = conn.cursor()

    name = data["name"]
    teacher_email = data["teacher_email"]

    # Check version history
    cur.execute("""
        SELECT id, version, parent_blueprint_id FROM assessment_blueprints
        WHERE name = ? AND teacher_email = ?
        ORDER BY version DESC LIMIT 1
    """, (name, teacher_email))
    row = cur.fetchone()

    if row:
        version = row["version"] + 1
        parent_id = row["parent_blueprint_id"] if row["parent_blueprint_id"] else row["id"]
    else:
        version = 1
        parent_id = None

    cur.execute("""
        INSERT INTO assessment_blueprints (
            name, teacher_email, subject, topic, subtopic, purpose, duration, question_count,
            conceptual_pct, application_pct, reasoning_pct, memory_pct, difficulty,
            assessment_strategy, version, parent_blueprint_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        teacher_email,
        data["subject"],
        data["topic"],
        data["subtopic"],
        data["purpose"],
        int(data.get("duration", 30)),
        int(data.get("question_count", 10)),
        float(data.get("conceptual_pct", 25.0)),
        float(data.get("application_pct", 25.0)),
        float(data.get("reasoning_pct", 25.0)),
        float(data.get("memory_pct", 25.0)),
        data["difficulty"],
        data.get("assessment_strategy", "balanced"),
        version,
        parent_id,
        datetime.now().isoformat()
    ))

    blueprint_id = cur.lastrowid

    # If this was the first version, update its parent_blueprint_id to point to itself
    if parent_id is None:
        cur.execute("""
            UPDATE assessment_blueprints SET parent_blueprint_id = ? WHERE id = ?
        """, (blueprint_id, blueprint_id))

    conn.commit()
    conn.close()
    return blueprint_id


def get_assessment_blueprints(email):
    conn = get_conn()
    cur = conn.cursor()
    # Fetch only latest version of each blueprint name
    cur.execute("""
        SELECT b1.* FROM assessment_blueprints b1
        INNER JOIN (
            SELECT name, MAX(version) as max_ver FROM assessment_blueprints
            WHERE teacher_email = ?
            GROUP BY name
        ) b2 ON b1.name = b2.name AND b1.version = b2.max_ver
        WHERE b1.teacher_email = ?
        ORDER BY b1.id DESC
    """, (email, email))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_blueprint_versions(parent_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM assessment_blueprints
        WHERE parent_blueprint_id = ?
        ORDER BY version DESC
    """, (parent_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_question_status(question_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE question_bank SET status = ? WHERE id = ?
    """, (status, question_id))
    conn.commit()
    conn.close()


def get_questions_by_status(status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM question_bank WHERE status = ? ORDER BY id DESC
    """, (status,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_room_questions_from_blueprint(blueprint_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM assessment_blueprints WHERE id = ?", (blueprint_id,))
    bp = cur.fetchone()
    if not bp:
        conn.close()
        return []

    subject = bp["subject"]
    topic = bp["topic"]
    subtopic = bp["subtopic"]
    q_count = bp["question_count"] or 5
    strategy = bp["assessment_strategy"] or "balanced"
    difficulty = bp["difficulty"] or "medium"

    conceptual_pct = bp["conceptual_pct"] or 25.0
    application_pct = bp["application_pct"] or 25.0
    reasoning_pct = bp["reasoning_pct"] or 25.0
    memory_pct = bp["memory_pct"] or 25.0

    # Calculate target counts
    target_conceptual = max(0, round(q_count * conceptual_pct / 100))
    target_application = max(0, round(q_count * application_pct / 100))
    target_reasoning = max(0, round(q_count * reasoning_pct / 100))
    target_memory = max(0, round(q_count * memory_pct / 100))

    # Adjust to sum up to q_count if rounding caused offsets
    diff_sum = q_count - (target_conceptual + target_application + target_reasoning + target_memory)
    if diff_sum != 0:
        target_conceptual = max(0, target_conceptual + diff_sum)

    # Status must be 'Approved'
    filters = "subject=? AND topic=? AND subtopic=? AND status='Approved'"
    params = [subject, topic, subtopic]

    final_questions = []
    
    # 1. Fetch conceptual
    if target_conceptual > 0:
        cur.execute(f"SELECT * FROM question_bank WHERE {filters} AND cognitive_type='conceptual' ORDER BY RANDOM() LIMIT {target_conceptual}", params)
        final_questions.extend(cur.fetchall())
    # 2. Fetch application
    if target_application > 0:
        cur.execute(f"SELECT * FROM question_bank WHERE {filters} AND cognitive_type='application' ORDER BY RANDOM() LIMIT {target_application}", params)
        final_questions.extend(cur.fetchall())
    # 3. Fetch reasoning
    if target_reasoning > 0:
        cur.execute(f"SELECT * FROM question_bank WHERE {filters} AND cognitive_type='reasoning' ORDER BY RANDOM() LIMIT {target_reasoning}", params)
        final_questions.extend(cur.fetchall())
    # 4. Fetch memory
    if target_memory > 0:
        cur.execute(f"SELECT * FROM question_bank WHERE {filters} AND cognitive_type='memory' ORDER BY RANDOM() LIMIT {target_memory}", params)
        final_questions.extend(cur.fetchall())

    # Fallback if not enough questions
    if len(final_questions) < q_count:
        remaining = q_count - len(final_questions)
        exclude_ids = ",".join([str(q['id']) for q in final_questions]) if final_questions else "0"
        cur.execute(f"SELECT * FROM question_bank WHERE {filters} AND id NOT IN ({exclude_ids}) ORDER BY RANDOM() LIMIT {remaining}", params)
        final_questions.extend(cur.fetchall())

    conn.close()

    formatted = []
    for r in final_questions:
        formatted.append({
            "id": r["id"],
            "prompt": r["prompt"],
            "options": [
                r["option_a"],
                r["option_b"],
                r["option_c"],
                r["option_d"]
            ],
            "correctIndex": r["correct_index"],
            "cognitive_type": r["cognitive_type"] or "conceptual",
            "difficulty": r["difficulty"] or "medium"
        })

    return formatted


def check_duplicate_question(prompt, subject, topic, subtopic):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT prompt FROM question_bank
        WHERE subject = ? AND topic = ? AND subtopic = ? AND status = 'Approved'
    """, (subject, topic, subtopic))
    rows = cur.fetchall()
    conn.close()

    p_clean = "".join(c for c in prompt.lower() if c.isalnum())
    for r in rows:
        existing_clean = "".join(c for c in r["prompt"].lower() if c.isalnum())
        if p_clean in existing_clean or existing_clean in p_clean:
            return True
    return False


def get_field_diff_summary(old_state, new_state):
    diffs = []
    if old_state.get("prompt") != new_state.get("prompt"):
        diffs.append(f"Prompt changed from '{old_state.get('prompt')}' to '{new_state.get('prompt')}'")
    if old_state.get("option_a") != new_state.get("option_a"):
        diffs.append(f"Option A changed from '{old_state.get('option_a')}' to '{new_state.get('option_a')}'")
    if old_state.get("option_b") != new_state.get("option_b"):
        diffs.append(f"Option B changed from '{old_state.get('option_b')}' to '{new_state.get('option_b')}'")
    if old_state.get("option_c") != new_state.get("option_c"):
        diffs.append(f"Option C changed from '{old_state.get('option_c')}' to '{new_state.get('option_c')}'")
    if old_state.get("option_d") != new_state.get("option_d"):
        diffs.append(f"Option D changed from '{old_state.get('option_d')}' to '{new_state.get('option_d')}'")
    try:
        old_idx = int(old_state.get("correct_index", 0))
        new_idx = int(new_state.get("correct_index", 0))
        if old_idx != new_idx:
            old_opt = ["A", "B", "C", "D"][old_idx]
            new_opt = ["A", "B", "C", "D"][new_idx]
            diffs.append(f"Correct option changed from {old_opt} to {new_opt}")
    except:
        pass
    if old_state.get("difficulty") != new_state.get("difficulty"):
        diffs.append(f"Difficulty changed from '{old_state.get('difficulty')}' to '{new_state.get('difficulty')}'")
    if old_state.get("cognitive_type") != new_state.get("cognitive_type"):
        diffs.append(f"Cognitive type changed from '{old_state.get('cognitive_type')}' to '{new_state.get('cognitive_type')}'")
    if old_state.get("explanation") != new_state.get("explanation"):
        diffs.append("Explanation updated")
    return " | ".join(diffs) if diffs else "No material changes"


def save_question_version(question_id, edited_by, change_reason, qqi_before=None, qqi_after=None, confidence_before=None, confidence_after=None, change_summary=None):
    conn = get_conn()
    cur = conn.cursor()
    
    # Fetch current values of the question
    cur.execute("SELECT * FROM question_bank WHERE id = ?", (question_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
        
    current_version = row["version"] or 1
    
    cur.execute("""
        INSERT INTO question_versions (
            question_id, version, prompt, option_a, option_b, option_c, option_d,
            correct_index, explanation, difficulty, cognitive_type,
            edited_by, change_reason, edited_at,
            qqi_before, qqi_after, confidence_before, confidence_after, change_summary
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?)
    """, (
        question_id,
        current_version,
        row["prompt"],
        row["option_a"],
        row["option_b"],
        row["option_c"],
        row["option_d"],
        row["correct_index"],
        row["explanation"],
        row["difficulty"],
        row["cognitive_type"],
        edited_by,
        change_reason,
        qqi_before,
        qqi_after,
        confidence_before,
        confidence_after,
        change_summary
    ))
    conn.commit()
    conn.close()
    return True
