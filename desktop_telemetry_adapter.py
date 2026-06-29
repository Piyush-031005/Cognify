"""
desktop_telemetry_adapter.py
Week 14 – Cross-Platform Cognitive Telemetry Engine (CTE)
Normalizes desktop user interaction events.
"""

def normalize_desktop_event(raw_event: dict) -> dict:
    """
    Normalizes a raw desktop event to standard telemetry format.
    Expected raw event formats:
      - mouse_movement: { event_type: 'mouse_movement', coordinates: [x, y], speed: float }
      - key_cadence: { event_type: 'key_cadence', delay_ms: int }
      - scroll: { event_type: 'scroll', delta_y: float }
      - hover: { event_type: 'hover', element_id: str, duration_ms: int }
      - focus: { event_type: 'focus', state: 'lost' | 'gained' }
    """
    event_type = raw_event.get("event_type")
    payload = {}

    if event_type == "mouse_movement":
        payload = {
            "x": float(raw_event.get("coordinates", [0, 0])[0]),
            "y": float(raw_event.get("coordinates", [0, 0])[1]),
            "speed": float(raw_event.get("speed", 0.0))
        }
    elif event_type == "key_cadence":
        payload = {
            "delay_ms": int(raw_event.get("delay_ms", 0))
        }
    elif event_type == "scroll":
        payload = {
            "delta_y": float(raw_event.get("delta_y", 0.0))
        }
    elif event_type == "hover":
        payload = {
            "element_id": str(raw_event.get("element_id", "")),
            "duration_ms": int(raw_event.get("duration_ms", 0))
        }
    elif event_type == "focus":
        payload = {
            "state": str(raw_event.get("state", "gained"))
        }
    else:
        payload = raw_event.get("payload", {})

    return {
        "event_type": event_type,
        "payload": payload
    }
