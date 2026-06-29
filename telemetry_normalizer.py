"""
telemetry_normalizer.py
Week 14 – Cross-Platform Cognitive Telemetry Engine (CTE)
Telemetry Normalizer converting client-specific events into unified schemas.
"""

import uuid
from datetime import datetime
from desktop_telemetry_adapter import normalize_desktop_event
from android_telemetry_adapter import normalize_android_event

def normalize_telemetry_payload(raw_payload: dict) -> dict:
    """
    Validates and normalizes raw telemetry payload from client request.
    Expected raw_payload format:
      {
         "event_id": str (optional, generated if missing),
         "student_email": str,
         "device_type": "desktop" | "android" | "ios",
         "event_type": str,
         ... raw device details ...
         "timestamp": str (optional, generated if missing)
      }
    """
    event_id = raw_payload.get("event_id") or str(uuid.uuid4())
    student_email = raw_payload.get("student_email")
    device_type = raw_payload.get("device_type", "desktop").lower()
    timestamp = raw_payload.get("timestamp") or datetime.now().isoformat()

    if not student_email:
        raise ValueError("Missing student_email in telemetry event.")

    # Delegate to device adapters
    if device_type == "desktop":
        normalized = normalize_desktop_event(raw_payload)
    elif device_type in ["android", "ios"]:
        normalized = normalize_android_event(raw_payload)
    else:
        # Fallback raw mapping
        normalized = {
            "event_type": raw_payload.get("event_type", "unknown"),
            "payload": raw_payload.get("payload", {})
        }

    import json
    return {
        "event_id": event_id,
        "student_email": student_email,
        "device_type": device_type,
        "event_type": normalized["event_type"],
        "payload_json": json.dumps(normalized["payload"]),
        "timestamp": timestamp
    }
