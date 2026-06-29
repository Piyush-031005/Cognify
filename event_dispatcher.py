"""
event_dispatcher.py
Week 17 – Cognitive Event Bus (CEB)
Handles routing of events to registered subscribers based on event_subscriptions database records.
"""

import importlib
import logging
from database import get_conn

logger = logging.getLogger(__name__)

# In-memory callbacks registry to simplify test mocks and direct handler bindings
_in_memory_subscribers = {}

def register_in_memory_handler(consumer_name, event_type, schema_version, func):
    """Registers an in-memory python function callback for testing and direct routing."""
    key = (consumer_name, event_type, schema_version)
    _in_memory_subscribers[key] = func

def clear_in_memory_handlers():
    _in_memory_subscribers.clear()

def resolve_handler_function(handler_str):
    """Resolves an import path string (e.g., 'memory_engine.on_response') to a python function."""
    try:
        parts = handler_str.split('.')
        module_path = '.'.join(parts[:-1])
        func_name = parts[-1]
        mod = importlib.import_module(module_path)
        return getattr(mod, func_name)
    except Exception as e:
        logger.error(f"Failed to resolve handler path '{handler_str}': {e}")
        return None

def get_active_subscriptions(event_type, schema_version):
    """Retrieves enabled subscriptions from database for event_type + schema_version."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT consumer_name, handler, enabled
            FROM event_subscriptions
            WHERE event_type = ? AND schema_version = ? AND enabled = 1
        """, (event_type, schema_version))
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Failed to fetch subscriptions: {e}")
        return []
    finally:
        conn.close()

def dispatch_to_subscriber(consumer_name, event_type, schema_version, handler_str, event_data, is_replay=False, replay_mode="SAFE"):
    """
    Invokes the resolved subscriber function with event payload, passing is_replay and replay_mode.
    """
    # 1. Check in-memory registry first
    key = (consumer_name, event_type, schema_version)
    if key in _in_memory_subscribers:
        func = _in_memory_subscribers[key]
        func(event_data, is_replay=is_replay, replay_mode=replay_mode)
        return True

    # 2. Resolve database handler path
    if not handler_str:
        return False
    func = resolve_handler_function(handler_str)
    if func:
        # Call resolved python function
        func(event_data, is_replay=is_replay, replay_mode=replay_mode)
        return True
    
    return False
