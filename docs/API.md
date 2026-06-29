# Cognify v3.0 API Documentation

This guide documents the REST API endpoints exposed by the Cognify platform.

---

## 1. Authentication & Security
Cognify secures its endpoints using Role-Based Access Control (RBAC). Authentic requests must supply a signed token in the header:
`Authorization: Bearer <HMAC_token>`

---

## 2. API Endpoints

### Authentication
#### `POST /signup`
Registers a new user role.
- **Payload**:
  ```json
  {
    "name": "John Doe",
    "email": "john@school.edu",
    "role": "teacher",
    "password": "securepassword"
  }
  ```
- **Response**: `200 OK` with User object and `"token"`.

#### `POST /signin`
Authenticates credentials and returns a secure token.
- **Payload**:
  ```json
  {
    "email": "john@school.edu",
    "password": "securepassword"
  }
  ```
- **Response**: `200 OK` with User object and `"token"`.

---

### Student Telemetry
#### `POST /submit`
Submit student quiz response and associated telemetry.
- **Access Roles**: `student`, `super_admin`
- **Payload**:
  ```json
  {
    "student_email": "student1@school.edu",
    "question_id": 105,
    "correct": 1,
    "response_time": 4.5,
    "confidence": 0.8,
    "idle_time": 0.8,
    "attempts": 1
  }
  ```

---

### Parent Twin
#### `GET /api/v1/parent/<parent_email>/children`
Lists all students linked to this parent.
- **Access Roles**: `parent`, `super_admin`

#### `POST /api/v1/parent/<parent_email>/child/<student_email>/link`
Link a child student to a parent.
- **Access Roles**: `parent`, `super_admin`

#### `GET /api/v1/parent/<parent_email>/child/<student_email>/snapshot`
Get live parent-translated child cognitive snapshot.
- **Access Roles**: `parent`, `super_admin`

---

### Teacher Twin
#### `POST /api/v1/teacher/override`
Applies a teacher manual override (force mastery/demote) for a student concept.
- **Access Roles**: `teacher`, `super_admin`
- **Payload**:
  ```json
  {
    "student_email": "student1@school.edu",
    "concept_id": "fractions",
    "override_type": "force_mastery",
    "reason": "Demonstrated understanding in class"
  }
  ```

---

### Observability
#### `GET /health`
Liveness status check.
- **Response**: `{"status": "healthy"}`

#### `GET /readiness`
Database readiness and migration state check.
- **Response**: `{"status": "ready"}`

#### `GET /metrics`
Observability statistics (DB size, event store count, DLQ size, latencies).
- **Response**: JSON payload with system statistics.
