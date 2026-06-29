"""
attention_engine.py
Week 15 – Attention & Circadian Intelligence (ACI)
Computes Attention Score, Circadian Factors, Session Fatigue, and rolling Attention Decay.
"""

import json
import uuid
from datetime import datetime
from database import get_conn


# =============================================================================
# ENGINE CONFIGURATION HELPERS
# =============================================================================

def _load_attention_config():
    """Loads all configuration parameters from attention_config table."""
    config = {
        "weight_focus_loss": 0.35,
        "weight_hesitation": 0.25,
        "weight_interaction_entropy": 0.20,
        "weight_typing_cadence": 0.10,
        "weight_reading_speed": 0.10,
        "attention_decay_alpha": 0.25,
        "lambda_attention_modulation": 0.35,
        "fatigue_limit": 0.65
    }
    circadian_ranges = [] # list of tuples: (start_hour, end_hour, factor)

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT key, value FROM attention_config")
        rows = cur.fetchall()
        for r in rows:
            key = r["key"]
            val = r["value"]
            if key.startswith("circadian_range_"):
                # Parse start and end hours (e.g. circadian_range_06_11 -> 6, 11)
                parts = key.split("_")
                if len(parts) == 4:
                    try:
                        start_h = int(parts[2])
                        end_h = int(parts[3])
                        circadian_ranges.append((start_h, end_h, val))
                    except ValueError:
                        pass
            elif key in config:
                config[key] = val
    except Exception:
        pass
    finally:
        conn.close()

    # Default fallback ranges if none configured
    if not circadian_ranges:
        circadian_ranges = [
            (6, 11, 1.0),
            (11, 17, 0.95),
            (17, 21, 0.90),
            (21, 2, 0.75),
            (2, 6, 0.60)
        ]

    config["circadian_ranges"] = circadian_ranges
    return config


def get_attention_config():
    """Returns active config values."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT key, value, config_version, updated_by, updated_at FROM attention_config")
        rows = [dict(r) for r in cur.fetchall()]
    except Exception:
        rows = []
    finally:
        conn.close()
    return rows


def update_attention_config(key, value, updated_by="teacher"):
    """Updates an attention config parameter."""
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cur.execute("""
            INSERT INTO attention_config (key, value, config_version, updated_by, updated_at)
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
# CORE MATH CALCULATIONS
# =============================================================================

def calculate_circadian_factor(local_hour, config):
    """
    Computes circadian factor dynamically based on config-driven ranges.
    Handles ranges wrapping around midnight (e.g. 21 to 2).
    """
    ranges = config.get("circadian_ranges", [])
    for start_h, end_h, factor in ranges:
        if start_h < end_h:
            if start_h <= local_hour < end_h:
                return factor
        else: # wraps around midnight (e.g. 21 to 2)
            if local_hour >= start_h or local_hour < end_h:
                return factor
    return 1.0


def calculate_active_session_minutes(student_email, cur):
    """
    Scans raw_telemetry_store to sum continuous interaction streaks (gaps <= 10 mins).
    """
    cur.execute("""
        SELECT timestamp FROM raw_telemetry_store
        WHERE student_email = ?
        ORDER BY timestamp ASC
    """, (student_email,))
    rows = cur.fetchall()
    if not rows:
        return 0.0

    timestamps = []
    for r in rows:
        try:
            timestamps.append(datetime.fromisoformat(r["timestamp"]))
        except Exception:
            pass

    if not timestamps:
        return 0.0

    total_active_seconds = 0
    streak_start = timestamps[0]
    last_timestamp = timestamps[0]

    for t in timestamps[1:]:
        gap = (t - last_timestamp).total_seconds()
        if gap > 600: # gap > 10 minutes resets the streak
            total_active_seconds += (last_timestamp - streak_start).total_seconds()
            streak_start = t
        last_timestamp = t

    total_active_seconds += (last_timestamp - streak_start).total_seconds()
    # Ensure at least 1 minute if there are events
    return max(1.0, round(total_active_seconds / 60.0, 2))


# =============================================================================
# MAIN INFERENCE ENGINE
# =============================================================================

def compute_and_save_attention(student_email, concept_id):
    """
    Infers attention state using deterministic features extraction logic,
    updates rolling EWMA state, and logs history transitions.
    """
    config = _load_attention_config()
    conn = get_conn()
    cur = conn.cursor()

    try:
        # 1. Fetch derived behavior features
        cur.execute("""
            SELECT * FROM derived_behavior_features
            WHERE student_email = ? AND concept_id = ?
        """, (student_email, concept_id))
        derived = cur.fetchone()

        # Fallback values if no derived telemetry exists (D1 & Missing Test 1)
        if not derived:
            # Fallback values
            attention_score = 1.0
            attention_decay = 1.0
            attention_confidence = 0.0
            explanation = {"fallback": "No derived features found, defaults applied."}
            focus_loss_count = 0
            hesitation_index = 0.0
            interaction_entropy = 0.0
            typing_cadence = 0.0
            reading_speed = 150.0
        else:
            derived = dict(derived)
            focus_loss_count = derived.get("focus_loss_count") or 0
            hesitation_index = derived.get("hesitation_index") or 0.0
            interaction_entropy = derived.get("interaction_entropy") or 0.0
            typing_cadence = derived.get("typing_cadence") or 0.0
            reading_speed = derived.get("reading_speed") or 150.0

            # Calculate Attention Confidence based on populated channels (Change 1)
            channels = 0
            if focus_loss_count is not None: channels += 1
            if hesitation_index > 0.0: channels += 1
            if interaction_entropy > 0.0: channels += 1
            if typing_cadence > 0.0: channels += 1
            if reading_speed > 0.0: channels += 1
            attention_confidence = round(channels / 5.0, 2)

            # Standardize and calculate penalties
            P_focus = max(0.0, 1.0 - (focus_loss_count * 0.25))
            P_hesitation = 1.0 - hesitation_index
            P_entropy = 1.0 - min(interaction_entropy / 100.0, 1.0)
            P_cadence = 1.0 - min(typing_cadence / 2000.0, 1.0)
            P_speed = 1.0 if (10.0 <= reading_speed <= 300.0) else 0.5

            attention_score = round(
                config["weight_focus_loss"] * P_focus +
                config["weight_hesitation"] * P_hesitation +
                config["weight_interaction_entropy"] * P_entropy +
                config["weight_typing_cadence"] * P_cadence +
                config["weight_reading_speed"] * P_speed,
                3
            )
            explanation = {
                "P_focus": round(P_focus, 3),
                "P_hesitation": round(P_hesitation, 3),
                "P_entropy": round(P_entropy, 3),
                "P_cadence": round(P_cadence, 3),
                "P_speed": round(P_speed, 3)
            }

        # 2. Fetch Circadian Factor
        now = datetime.now()
        circadian_factor = calculate_circadian_factor(now.hour, config)

        # 3. Calculate Session Fatigue (D3 & Change 4)
        cur.execute("SELECT rolling_ccli FROM student_cognitive_load_state WHERE student_email = ?", (student_email,))
        ccli_row = cur.fetchone()
        ccli_val = ccli_row["rolling_ccli"] if (ccli_row and ccli_row["rolling_ccli"] is not None) else 0.5

        active_minutes = calculate_active_session_minutes(student_email, cur)
        session_fatigue = round(0.5 * ccli_val + 0.5 * min(active_minutes / 60.0, 1.0), 3)

        # 4. Fetch Rolling Attention State (EWMA)
        cur.execute("SELECT rolling_decay FROM student_attention_state WHERE student_email = ?", (student_email,))
        prev_state = cur.fetchone()

        if prev_state and prev_state["rolling_decay"] is not None:
            alpha = config["attention_decay_alpha"]
            attention_decay = round(alpha * attention_score + (1.0 - alpha) * prev_state["rolling_decay"], 3)
        else:
            attention_decay = attention_score

        # 5. Define Focus State
        # If attention decay falls below fatigue limit or session fatigue is extremely high
        if attention_decay < config["fatigue_limit"] or session_fatigue > 0.8:
            focus_state = "fatigued"
        elif focus_loss_count > 2:
            focus_state = "distracted"
        else:
            focus_state = "optimal"

        # 6. Save attention state
        timestamp_str = now.isoformat()
        cur.execute("""
            INSERT INTO student_attention_state (student_email, rolling_attention, rolling_decay, last_computed_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(student_email) DO UPDATE SET
                rolling_attention = excluded.rolling_attention,
                rolling_decay = excluded.rolling_decay,
                last_computed_at = excluded.last_computed_at
        """, (student_email, attention_score, attention_decay, timestamp_str))

        # Check for history transition audits
        cur.execute("SELECT new_state FROM attention_history WHERE student_email = ? ORDER BY history_id DESC LIMIT 1", (student_email,))
        hist_row = cur.fetchone()
        old_state = hist_row["new_state"] if hist_row else "optimal"

        if old_state != focus_state:
            cur.execute("""
                INSERT INTO attention_history (student_email, old_state, new_state, timestamp)
                VALUES (?, ?, ?, ?)
            """, (student_email, old_state, focus_state, timestamp_str))

        # 7. Log attention event
        event_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO attention_events (
                event_id, student_email, concept_id, attention_score, attention_decay,
                circadian_factor, session_fatigue, focus_state, confidence, explanation_json,
                attention_engine_version, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'v1.0', ?)
        """, (
            event_id, student_email, concept_id, attention_score, attention_decay,
            circadian_factor, session_fatigue, focus_state, attention_confidence,
            json.dumps(explanation), timestamp_str
        ))

        conn.commit()
        return {
            "event_id": event_id,
            "student_email": student_email,
            "concept_id": concept_id,
            "attention_score": attention_score,
            "attention_decay": attention_decay,
            "circadian_factor": circadian_factor,
            "session_fatigue": session_fatigue,
            "focus_state": focus_state,
            "confidence": attention_confidence,
            "explanation": explanation,
            "timestamp": timestamp_str
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()


def get_student_attention_state(student_email):
    """Fetches the latest attention state, config limits, and transition history."""
    conn = get_conn()
    cur = conn.cursor()
    state = None
    history = []
    try:
        cur.execute("""
            SELECT * FROM student_attention_state
            WHERE student_email = ?
        """, (student_email,))
        row = cur.fetchone()
        if row:
            state = dict(row)

        cur.execute("""
            SELECT * FROM attention_history
            WHERE student_email = ?
            ORDER BY timestamp DESC LIMIT 20
        """, (student_email,))
        history = [dict(h) for h in cur.fetchall()]
    except Exception:
        pass
    finally:
        conn.close()

    return {
        "student_email": student_email,
        "state": state,
        "history": history
    }
