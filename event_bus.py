"""
event_bus.py
Week 17 – Cognitive Event Bus (CEB)
Core event broker implementing publication, dynamic subscriptions, idempotency guards, and dead-letter routing.
"""

import uuid
import json
import logging
from datetime import datetime
from database import get_conn
import event_registry
import event_dispatcher

logger = logging.getLogger(__name__)

def publish(
    event_type, entity_type, entity_id, producer, producer_version,
    schema_version, metadata_json, payload_json, event_id=None
):
    """
    Publishes an immutable domain event.
    Calculates monotonically increasing entity-scoped sequence number.
    Saves to event_store append-only ledger and dispatches to active subscribers.
    """
    # 1. Validate against registry
    is_valid, msg = event_registry.validate_event(event_type, producer, schema_version)
    if not is_valid:
        raise ValueError(f"Event registry validation failed: {msg}")

    conn = get_conn()
    cur = conn.cursor()
    try:
        now = datetime.now().isoformat()
        if not event_id:
            event_id = str(uuid.uuid4())

        # 2. Get monotonic sequence number per entity (Decision 4)
        cur.execute("""
            SELECT MAX(entity_sequence) as max_seq 
            FROM event_store 
            WHERE entity_type = ? AND entity_id = ?
        """, (entity_type, entity_id))
        row = cur.fetchone()
        entity_sequence = (row["max_seq"] or 0) + 1

        # 3. Store event (Append-Only ledger)
        cur.execute("""
            INSERT INTO event_store (
                event_id, event_type, entity_type, entity_id, entity_sequence,
                producer, producer_version, schema_version, metadata_json, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, event_type, entity_type, entity_id, entity_sequence,
            producer, producer_version, schema_version,
            json.dumps(metadata_json) if isinstance(metadata_json, dict) else metadata_json,
            json.dumps(payload_json) if isinstance(payload_json, dict) else payload_json,
            now
        ))
        conn.commit()

        # Retrieve parsed event record for dispatching
        event_record = {
            "event_id": event_id,
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_sequence": entity_sequence,
            "producer": producer,
            "producer_version": producer_version,
            "schema_version": schema_version,
            "metadata_json": metadata_json,
            "payload_json": payload_json,
            "created_at": now
        }

        # 4. Dispatch to active subscribers
        subs = event_dispatcher.get_active_subscriptions(event_type, schema_version)
        for sub in subs:
            dispatch(event_id, sub["consumer_name"], sub["handler"], event_record)

        return event_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to publish event {event_type}: {e}")
        raise e
    finally:
        conn.close()


def subscribe(consumer_name, event_type, schema_version, handler, enabled=1):
    """Creates or updates a versioned subscription in event_subscriptions."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO event_subscriptions (consumer_name, event_type, schema_version, handler, enabled)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(consumer_name, event_type, schema_version) DO UPDATE SET
                handler = excluded.handler,
                enabled = excluded.enabled
        """, (consumer_name, event_type, schema_version, handler, enabled))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to subscribe consumer {consumer_name}: {e}")
        raise e
    finally:
        conn.close()


def dispatch(event_id, consumer_name, handler_str, event_data, is_replay=False, replay_mode="SAFE"):
    """
    Routes an event to a subscriber with At-Least-Once Delivery and Processed Idempotency checks.
    Includes Dead Letter Queue routing on repeat failures.
    """
    # 1. Idempotency Check (bypassed only in Safe/Live replay modes if specifically designated)
    if not is_replay:
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) as cnt FROM processed_events
                WHERE event_id = ? AND consumer_name = ?
            """, (event_id, consumer_name))
            row = cur.fetchone()
            if row and row["cnt"] > 0:
                logger.info(f"Event {event_id} already processed by {consumer_name}. Skipping.")
                return
        finally:
            conn.close()

    # 2. Execute Handler with Retry & Dead Letter fallback (Decision 6)
    max_retries = 3
    retry_count = 0
    success = False
    last_error = ""

    while retry_count < max_retries:
        try:
            success = event_dispatcher.dispatch_to_subscriber(
                consumer_name, event_data["event_type"], event_data["schema_version"],
                handler_str, event_data, is_replay=is_replay, replay_mode=replay_mode
            )
            if success:
                break
        except Exception as ex:
            retry_count += 1
            last_error = str(ex)
            logger.warning(f"Handler retry {retry_count}/{max_retries} failed for {consumer_name}: {ex}")

    now = datetime.now().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    try:
        if success:
            # Mark processed (unless in SAFE replay mode where we avoid state updates)
            if not is_replay or replay_mode == "LIVE":
                cur.execute("""
                    INSERT OR IGNORE INTO processed_events (event_id, consumer_name, processed_at)
                    VALUES (?, ?, ?)
                """, (event_id, consumer_name, now))
                conn.commit()
        else:
            # Route to Dead Letter Queue (DLQ)
            cur.execute("""
                INSERT OR REPLACE INTO dead_letter_events (
                    event_id, consumer_name, error_message, retry_count, failed_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event_id, consumer_name, last_error or "Handler resolution failed",
                retry_count, now, json.dumps(event_data["payload_json"])
            ))
            conn.commit()
            logger.error(f"Event {event_id} moved to DLQ for consumer {consumer_name}.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update processed status or DLQ: {e}")
    finally:
        conn.close()
