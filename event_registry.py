"""
event_registry.py
Week 17 – Cognitive Event Bus (CEB)
Defines all allowed domain events, their producers, allowed consumers, and schema versions.
"""

EVENT_TYPES = {
    "ResponseSubmitted": {
        "producer": "telemetry_engine",
        "allowed_consumers": ["memory_engine", "analytics_engine"],
        "schema_version": "v1.0"
    },
    "MemoryUpdated": {
        "producer": "memory_engine",
        "allowed_consumers": ["qqi_engine", "nbirt_engine", "ccli_engine", "teacher_twin", "student_twin", "parent_twin", "school_admin_twin", "research_analytics_twin"],
        "schema_version": "v1.0"
    },
    "QQIUpdated": {
        "producer": "qqi_engine",
        "allowed_consumers": ["nbirt_engine", "analytics_engine"],
        "schema_version": "v1.0"
    },
    "NBIRTUpdated": {
        "producer": "nbirt_engine",
        "allowed_consumers": ["context_engine", "teacher_twin", "student_twin", "analytics_engine"],
        "schema_version": "v1.0"
    },
    "CCLIUpdated": {
        "producer": "ccli_engine",
        "allowed_consumers": ["attention_engine", "cdo_engine", "student_twin", "parent_twin", "analytics_engine"],
        "schema_version": "v1.0"
    },
    "AttentionUpdated": {
        "producer": "attention_engine",
        "allowed_consumers": ["cdo_engine", "student_twin", "parent_twin", "school_admin_twin", "analytics_engine"],
        "schema_version": "v1.0"
    },
    "DecisionGenerated": {
        "producer": "cdo_engine",
        "allowed_consumers": ["teacher_twin", "student_twin", "parent_twin", "school_admin_twin", "research_analytics_twin", "analytics_engine"],
        "schema_version": "v1.0"
    },
    "QuestionRetired": {
        "producer": "qbl_engine",
        "allowed_consumers": ["context_engine", "analytics_engine"],
        "schema_version": "v1.0"
    },
    "QuestionPromoted": {
        "producer": "qbl_engine",
        "allowed_consumers": ["context_engine", "analytics_engine"],
        "schema_version": "v1.0"
    },
    "TeacherOverride": {
        "producer": "teacher_twin",
        "allowed_consumers": ["cdo_engine", "context_engine", "teacher_twin"],
        "schema_version": "v1.0"
    },
    "TelemetryBatchReceived": {
        "producer": "telemetry_engine",
        "allowed_consumers": ["feature_extractor", "analytics_engine"],
        "schema_version": "v1.0"
    },
    "TeacherRecommendationGenerated": {
        "producer": "teacher_twin",
        "allowed_consumers": ["dashboard", "student_twin", "analytics_engine"],
        "schema_version": "v1.0"
    },
    "TeacherOverrideApplied": {
        "producer": "teacher_twin",
        "allowed_consumers": ["cdo_engine", "context_engine", "student_twin", "school_admin_twin", "analytics_engine"],
        "schema_version": "v1.0"
    },
    "TeacherPolicyUpdated": {
        "producer": "teacher_twin",
        "allowed_consumers": ["cdo_engine", "context_engine", "analytics_engine"],
        "schema_version": "v1.0"
    }
}

def validate_event(event_type, producer, schema_version):
    """Checks if the event type exists and has matching schema/producer parameters."""
    if event_type not in EVENT_TYPES:
        return False, f"Unknown event type: {event_type}"
    config = EVENT_TYPES[event_type]
    if config["schema_version"] != schema_version:
        return False, f"Schema version mismatch: expected {config['schema_version']}, got {schema_version}"
    return True, "Valid"
