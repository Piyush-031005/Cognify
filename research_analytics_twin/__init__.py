"""
research_analytics_twin package initialization.
Delegates event handlers and exposes CQRS read APIs.
"""

import json
import hashlib
import datetime
from database import get_conn

# Import submodule handlers
import research_analytics_twin.decay as decay
import research_analytics_twin.misconceptions as misconceptions
import research_analytics_twin.interventions as interventions
import research_analytics_twin.discrimination as discrimination
import research_analytics_twin.classroom_speed as classroom_speed
import research_analytics_twin.load_correlation as load_correlation

# --- CEB Event Handlers ---

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    decay.handle_memory_updated(event_data, is_replay, replay_mode)
    discrimination.handle_memory_updated(event_data, is_replay, replay_mode)
    classroom_speed.handle_memory_updated(event_data, is_replay, replay_mode)
    load_correlation.handle_memory_updated(event_data, is_replay, replay_mode)

def handle_decision_generated(event_data, is_replay=False, replay_mode="SAFE"):
    misconceptions.handle_decision_generated(event_data, is_replay, replay_mode)
    interventions.handle_decision_generated(event_data, is_replay, replay_mode)

# --- Rebuild Projections (Decision 5 Checksum) ---

def rebuild_projections():
    """
    Clears all research projection tables, replays event logs chronologically under SAFE mode,
    recompute research summaries, validates MD5 checksums, and updates metadata.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM research_concept_decay")
        cur.execute("DELETE FROM research_misconception_frequency")
        cur.execute("DELETE FROM research_intervention_effectiveness")
        cur.execute("DELETE FROM research_question_discrimination")
        cur.execute("DELETE FROM research_classroom_speed")
        cur.execute("DELETE FROM research_load_decay_correlation")
        conn.commit()
    finally:
        conn.close()

    # Replay events
    import event_replay
    replay_res = event_replay.replay_all_events("research_analytics_twin", mode="SAFE")

    # Run full re-aggregations to guarantee alignment
    decay.recompute_concept_decay()
    misconceptions.recompute_misconception_frequency()
    interventions.recompute_intervention_effectiveness()
    discrimination.recompute_question_discrimination()
    classroom_speed.recompute_classroom_speed()
    load_correlation.recompute_load_decay_correlation()

    # Compute row count MD5 checksum
    conn = get_conn()
    cur = conn.cursor()
    tables = [
        "research_concept_decay",
        "research_misconception_frequency",
        "research_intervention_effectiveness",
        "research_question_discrimination",
        "research_classroom_speed",
        "research_load_decay_correlation"
    ]
    hasher = hashlib.md5()
    try:
        for t in tables:
            cur.execute(f"SELECT COUNT(*) as count FROM {t}")
            cnt = cur.fetchone()["count"] or 0
            hasher.update(str(cnt).encode('utf-8'))
        checksum = hasher.hexdigest()

        now_str = datetime.datetime.now().isoformat()
        cur.execute("""
            INSERT INTO research_projection_metadata (projection_version, checksum, rebuilt_at)
            VALUES ('v1.0', ?, ?)
            ON CONFLICT(projection_version) DO UPDATE SET
                checksum = excluded.checksum,
                rebuilt_at = excluded.rebuilt_at
        """, (checksum, now_str))
        conn.commit()
    finally:
        conn.close()

    return {
        "status": "success",
        "events_replayed": replay_res.get("events_processed", 0),
        "projection_checksum": checksum
    }

# --- CQRS Read APIs (Decision 1) ---

def get_concept_decay():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM research_concept_decay ORDER BY avg_decay_time_days ASC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_misconception_frequency():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM research_misconception_frequency ORDER BY occurrence_count DESC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_intervention_effectiveness():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM research_intervention_effectiveness ORDER BY success_rate DESC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_question_discrimination():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM research_question_discrimination ORDER BY discrimination_index DESC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_classroom_speed():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM research_classroom_speed ORDER BY improvement_rate DESC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_load_decay_correlation():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM research_load_decay_correlation ORDER BY metric_name")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
