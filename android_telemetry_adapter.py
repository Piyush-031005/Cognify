"""
android_telemetry_adapter.py
Week 14 – Cross-Platform Cognitive Telemetry Engine (CTE)
Normalizes Android (mobile) user interaction events.
"""

def normalize_android_event(raw_event: dict) -> dict:
    """
    Normalizes a raw Android event to standard telemetry format.
    Expected raw event formats:
      - touch: { event_type: 'touch', x: float, y: float, pressure: float }
      - drag: { event_type: 'drag', path: [[x1, y1], [x2, y2]], duration_ms: int }
      - scroll: { event_type: 'scroll', distance_y: float }
      - orientation: { event_type: 'orientation', mode: 'portrait' | 'landscape' }
      - app_lifecycle: { event_type: 'app_lifecycle', state: 'background' | 'foreground' }
    """
    event_type = raw_event.get("event_type")
    payload = {}

    if event_type == "touch":
        payload = {
            "x": float(raw_event.get("x", 0.0)),
            "y": float(raw_event.get("y", 0.0)),
            "pressure": float(raw_event.get("pressure", 1.0))
        }
    elif event_type == "drag":
        payload = {
            "path": list(raw_event.get("path", [])),
            "duration_ms": int(raw_event.get("duration_ms", 0))
        }
    elif event_type == "scroll":
        payload = {
            "delta_y": float(raw_event.get("distance_y", 0.0))
        }
    elif event_type == "orientation":
        payload = {
            "mode": str(raw_event.get("mode", "portrait"))
        }
    elif event_type == "app_lifecycle":
        # Map app_lifecycle to focus_loss for higher-level normalizer
        event_type = "focus"
        payload = {
            "state": "lost" if raw_event.get("state") == "background" else "gained"
        }
    else:
        payload = raw_event.get("payload", {})

    return {
        "event_type": event_type,
        "payload": payload
    }
