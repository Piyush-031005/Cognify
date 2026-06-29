"""
feature_extractor.py
Week 14 – Cross-Platform Cognitive Telemetry Engine (CTE)
Feature Extractor calculating derived behavior features from raw_telemetry_store.
"""

import json
import math
from datetime import datetime
from database import get_conn

def extract_and_cache_behavior_features(student_email, concept_id):
    """
    Reads raw telemetry events for the student, calculates high-level behavior indicators,
    and updates the derived_behavior_features cache.
    """
    conn = get_conn()
    cur = conn.cursor()

    try:
        # 1. Fetch raw telemetry events
        cur.execute("""
            SELECT event_type, payload_json, timestamp FROM raw_telemetry_store
            WHERE student_email = ?
            ORDER BY timestamp ASC
        """, (student_email,))
        rows = [dict(r) for r in cur.fetchall()]

        if not rows:
            return {"status": "skipped", "reason": "No raw telemetry events found."}

        # Sub-metrics variables
        mouse_coords = []
        hover_durations = []
        focus_lost_count = 0
        key_delays = []
        scroll_deltas = []
        correction_rate = 0.0

        for r in rows:
            payload = json.loads(r["payload_json"] or "{}")
            etype = r["event_type"]

            if etype == "mouse_movement" or etype == "touch":
                if "x" in payload and "y" in payload:
                    mouse_coords.append((payload["x"], payload["y"]))
            elif etype == "drag":
                path = payload.get("path", [])
                for coord in path:
                    if len(coord) == 2:
                        mouse_coords.append((coord[0], coord[1]))
            elif etype == "hover":
                dur = payload.get("duration_ms", 0)
                if dur > 0:
                    hover_durations.append(dur)
            elif etype == "focus":
                state = payload.get("state")
                if state == "lost":
                    focus_lost_count += 1
            elif etype == "key_cadence":
                delay = payload.get("delay_ms", 0)
                if delay > 0:
                    key_delays.append(delay)
            elif etype == "scroll":
                delta = payload.get("delta_y", 0.0)
                scroll_deltas.append(delta)

        # 2. Calculate derived behavior features
        # A. Interaction Entropy (Variability in coordinate path)
        interaction_entropy = 0.0
        if len(mouse_coords) > 1:
            xs = [c[0] for c in mouse_coords]
            ys = [c[1] for c in mouse_coords]
            mean_x = sum(xs) / len(xs)
            mean_y = sum(ys) / len(ys)
            var_x = sum((x - mean_x) ** 2 for x in xs) / len(xs)
            var_y = sum((y - mean_y) ** 2 for y in ys) / len(ys)
            interaction_entropy = round(math.sqrt(var_x + var_y), 3)

        # B. Hesitation Index (Derived from hovers average duration)
        hesitation_index = 0.0
        if hover_durations:
            avg_hover = sum(hover_durations) / len(hover_durations)
            # Scale average hover: 0.0 to 1.0 (clipping at 5000ms)
            hesitation_index = round(min(avg_hover / 5000.0, 1.0), 3)

        # C. Reading Speed (WPS simulation: based on hover rate and response duration)
        reading_speed = 150.0  # default baseline
        if len(rows) > 1:
            try:
                t0 = datetime.fromisoformat(rows[0]["timestamp"])
                tn = datetime.fromisoformat(rows[-1]["timestamp"])
                total_duration = (tn - t0).total_seconds()
                if total_duration > 2.0:
                    # Assume 300 words average per session
                    reading_speed = round(300.0 / total_duration, 2)
            except Exception:
                pass

        # D. Typing Cadence (Average delay)
        typing_cadence = 0.0
        if key_delays:
            typing_cadence = round(sum(key_delays) / len(key_delays), 2)

        # E. Scroll Entropy
        scroll_entropy = 0.0
        if len(scroll_deltas) > 1:
            mean_s = sum(scroll_deltas) / len(scroll_deltas)
            var_s = sum((s - mean_s) ** 2 for s in scroll_deltas) / len(scroll_deltas)
            scroll_entropy = round(math.sqrt(var_s), 3)

        # 3. Update derived_behavior_features cache
        now = datetime.now().isoformat()
        cur.execute("""
            INSERT INTO derived_behavior_features (
                student_email, concept_id, interaction_entropy, hesitation_index,
                reading_speed, correction_rate, focus_loss_count, typing_cadence,
                scroll_entropy, last_computed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_email, concept_id) DO UPDATE SET
                interaction_entropy = excluded.interaction_entropy,
                hesitation_index = excluded.hesitation_index,
                reading_speed = excluded.reading_speed,
                correction_rate = excluded.correction_rate,
                focus_loss_count = excluded.focus_loss_count,
                typing_cadence = excluded.typing_cadence,
                scroll_entropy = excluded.scroll_entropy,
                last_computed_at = excluded.last_computed_at
        """, (
            student_email, concept_id, interaction_entropy, hesitation_index,
            reading_speed, correction_rate, focus_lost_count, typing_cadence,
            scroll_entropy, now
        ))

        conn.commit()
        return {
            "status": "success",
            "student_email": student_email,
            "concept_id": concept_id,
            "features": {
                "interaction_entropy": interaction_entropy,
                "hesitation_index": hesitation_index,
                "reading_speed": reading_speed,
                "correction_rate": correction_rate,
                "focus_loss_count": focus_lost_count,
                "typing_cadence": typing_cadence,
                "scroll_entropy": scroll_entropy
            }
        }
    except Exception as e:
        conn.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        conn.close()


def get_cached_behavior_features(student_email, concept_id):
    """Retrieves cached derived features for a student and concept."""
    conn = get_conn()
    cur = conn.cursor()
    row = None
    try:
        cur.execute("""
            SELECT * FROM derived_behavior_features
            WHERE student_email = ? AND concept_id = ?
        """, (student_email, concept_id))
        r = cur.fetchone()
        if r:
            row = dict(r)
    except Exception:
        pass
    finally:
        conn.close()
    return row
