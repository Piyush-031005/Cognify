"""
event_replay.py
Week 17 – Cognitive Event Bus (CEB)
Implements query-driven event replay execution modes (SAFE and LIVE) for cognitive state rebuilding.
"""

import uuid
import json
import logging
from datetime import datetime
from database import get_conn
import event_bus

logger = logging.getLogger(__name__)

def execute_replay_query(query, params, consumer_name, mode="SAFE"):
    """
    Executes chronological event replay based on query results, bypassing processed_events checks.
    Logs replay execution results to event_replay_runs.
    """
    replay_id = str(uuid.uuid4())
    now_start = datetime.now().isoformat()

    conn = get_conn()
    cur = conn.cursor()
    try:
        # Create replay run entry
        cur.execute("""
            INSERT INTO event_replay_runs (
                replay_id, consumer_name, from_timestamp, to_timestamp,
                events_processed, started_at, status, mode
            ) VALUES (?, ?, ?, ?, 0, ?, 'running', ?)
        """, (replay_id, consumer_name, params.get("from_time"), params.get("to_time"), now_start, mode))
        conn.commit()

        # Query events ordered by entity sequence to preserve strict causality
        cur.execute(query, params.get("sql_params", ()))
        events = [dict(r) for r in cur.fetchall()]

        processed_count = 0
        for ev in events:
            # Parse payload & metadata
            try:
                ev["payload_json"] = json.loads(ev["payload_json"]) if isinstance(ev["payload_json"], str) else ev["payload_json"]
            except Exception:
                pass
            try:
                ev["metadata_json"] = json.loads(ev["metadata_json"]) if isinstance(ev["metadata_json"], str) else ev["metadata_json"]
            except Exception:
                pass

            # Resolve subscriber handler string from subscriptions
            cur.execute("""
                SELECT handler FROM event_subscriptions
                WHERE consumer_name = ? AND event_type = ? AND schema_version = ?
            """, (consumer_name, ev["event_type"], ev["schema_version"]))
            sub_row = cur.fetchone()
            handler_str = sub_row["handler"] if sub_row else None

            if handler_str:
                # Dispatch event in Replay mode
                event_bus.dispatch(ev["event_id"], consumer_name, handler_str, ev, is_replay=True, replay_mode=mode)
                processed_count += 1

        # Mark replay run complete
        now_end = datetime.now().isoformat()
        cur.execute("""
            UPDATE event_replay_runs SET
                events_processed = ?,
                completed_at = ?,
                status = 'success'
            WHERE replay_id = ?
        """, (processed_count, now_end, replay_id))
        conn.commit()

        return {
            "replay_id": replay_id,
            "status": "success",
            "events_processed": processed_count,
            "started_at": now_start,
            "completed_at": now_end
        }
    except Exception as e:
        conn.rollback()
        now_end = datetime.now().isoformat()
        try:
            cur.execute("""
                UPDATE event_replay_runs SET
                    completed_at = ?,
                    status = 'failed'
                WHERE replay_id = ?
            """, (now_end, replay_id))
            conn.commit()
        except:
            pass
        logger.error(f"Replay run {replay_id} failed: {e}")
        return {"error": str(e), "replay_id": replay_id}
    finally:
        conn.close()


def replay_all_events(consumer_name, mode="SAFE", from_timestamp=None, to_timestamp=None):
    """Replays all historical events chronologically."""
    sql = "SELECT * FROM event_store WHERE 1=1"
    sql_params = []
    if from_timestamp:
        sql += " AND created_at >= ?"
        sql_params.append(from_timestamp)
    if to_timestamp:
        sql += " AND created_at <= ?"
        sql_params.append(to_timestamp)
    sql += " ORDER BY entity_id ASC, entity_sequence ASC"

    params = {
        "from_time": from_timestamp,
        "to_time": to_timestamp,
        "sql_params": tuple(sql_params)
    }
    return execute_replay_query(sql, params, consumer_name, mode)


def replay_entity_events(consumer_name, entity_type, entity_id, mode="SAFE"):
    """Replays events scoped to a specific entity in sequence order."""
    sql = "SELECT * FROM event_store WHERE entity_type = ? AND entity_id = ? ORDER BY entity_sequence ASC"
    params = {
        "from_time": None,
        "to_time": None,
        "sql_params": (entity_type, entity_id)
    }
    return execute_replay_query(sql, params, consumer_name, mode)


def replay_engine_events(consumer_name, event_type, mode="SAFE"):
    """Replays events of a specific event type."""
    sql = "SELECT * FROM event_store WHERE event_type = ? ORDER BY entity_id ASC, entity_sequence ASC"
    params = {
        "from_time": None,
        "to_time": None,
        "sql_params": (event_type,)
    }
    return execute_replay_query(sql, params, consumer_name, mode)
