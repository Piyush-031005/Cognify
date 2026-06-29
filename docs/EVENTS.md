# Cognify v3.0 Event Catalog

This document catalogues the domain events supported by the Cognitive Event Bus (CEB) and their consumers.

---

## 1. Registry Configuration (`event_registry.py`)

Every event published to the CEB is registered with:
- **Producer**: The source engine generating the event.
- **Allowed Consumers**: List of engine/twin names permitted to subscribe.
- **Schema Version**: For backward compatibility.

---

## 2. Event Types & Schemas

### `ResponseSubmitted`
Published when a student submits a quiz answer.
- **Producer**: `quiz_service`
- **Allowed Consumers**: `memory_engine`
- **Payload Schema**:
  ```json
  {
    "student_email": "student1@school.edu",
    "question_id": 101,
    "correct": 1,
    "response_time": 4.5,
    "confidence": 0.8
  }
  ```

### `MemoryUpdated`
Published when the Memory Engine completes decay half-life re-evaluations.
- **Producer**: `memory_engine`
- **Allowed Consumers**: `qqi_engine`, `nbirt_engine`, `ccli_engine`, `teacher_twin`, `student_twin`, `parent_twin`, `school_admin_twin`, `research_analytics_twin`
- **Payload Schema**:
  ```json
  {
    "concept_id": "algebra",
    "memory_strength": 0.85,
    "memory_state": "Stable"
  }
  ```

### `DecisionGenerated`
Published when the Decision Engine (CDO) updates recommendation decisions.
- **Producer**: `cdo_engine`
- **Allowed Consumers**: `teacher_twin`, `student_twin`, `parent_twin`, `school_admin_twin`, `research_analytics_twin`
- **Payload Schema**:
  ```json
  {
    "recommendation": "Review fraction ratios",
    "priority_score": 0.85,
    "confidence": 0.92
  }
  ```
