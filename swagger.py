"""
swagger.py
Week 23 — Centralized OpenAPI/Swagger Spec Generator (Refinement 7).
"""

import json
import config

ENDPOINTS = [
    # Auth
    {"path": "/signup", "method": "post", "summary": "Register a new user role", "roles": ["any"], "params": ["name", "email", "role", "password"]},
    {"path": "/signin", "method": "post", "summary": "Authenticate and get HMAC JWT token", "roles": ["any"], "params": ["email", "password"]},
    
    # Core Engine / Telemetry
    {"path": "/submit", "method": "post", "summary": "Submit student quiz response & telemetry", "roles": ["student", "super_admin"]},
    
    # Parent Twin
    {"path": "/api/v1/parent/{parent_email}/children", "method": "get", "summary": "Get list of linked children", "roles": ["parent", "super_admin"]},
    {"path": "/api/v1/parent/{parent_email}/child/{student_email}/link", "method": "post", "summary": "Link parent and child", "roles": ["parent", "super_admin"]},
    {"path": "/api/v1/parent/{parent_email}/child/{student_email}/snapshot", "method": "get", "summary": "Get human digest of student cognitive state", "roles": ["parent", "super_admin"]},
    {"path": "/api/v1/parent/{parent_email}/child/{student_email}/weekly-report", "method": "get", "summary": "Get latest weekly report (auto-generates)", "roles": ["parent", "super_admin"]},
    {"path": "/api/v1/parent/{parent_email}/child/{student_email}/weekly-report/read", "method": "post", "summary": "Mark weekly report as read", "roles": ["parent", "super_admin"]},
    {"path": "/api/v1/parent/rebuild", "method": "post", "summary": "Safe rebuild parent projections with checksum", "roles": ["super_admin", "school_admin"]},
    
    # Teacher Twin
    {"path": "/api/v1/teacher/override", "method": "post", "summary": "Teacher manual override for student mastery", "roles": ["teacher", "super_admin"]},
    {"path": "/api/v1/teacher/rebuild", "method": "post", "summary": "Safe rebuild teacher projections", "roles": ["super_admin", "school_admin"]},
    {"path": "/api/v1/teacher/rooms/{room_id}/report", "method": "get", "summary": "Get classroom analytical reports", "roles": ["teacher", "super_admin"]},
    
    # School Admin Twin
    {"path": "/api/v1/admin/school/overview", "method": "get", "summary": "School-wide adoption metrics and stats", "roles": ["school_admin", "super_admin"]},
    {"path": "/api/v1/admin/school/classrooms", "method": "get", "summary": "All classroom summaries in the school", "roles": ["school_admin", "super_admin"]},
    {"path": "/api/v1/admin/school/classrooms/{room_code}", "method": "get", "summary": "Details of a single classroom", "roles": ["school_admin", "super_admin"]},
    {"path": "/api/v1/admin/school/teachers", "method": "get", "summary": "All teacher summaries in the school", "roles": ["school_admin", "super_admin"]},
    {"path": "/api/v1/admin/school/teachers/{teacher_email}", "method": "get", "summary": "Details of a single teacher", "roles": ["school_admin", "super_admin"]},
    {"path": "/api/v1/admin/school/curriculum", "method": "get", "summary": "School-wide concept coverage statistics", "roles": ["school_admin", "super_admin"]},
    {"path": "/api/v1/admin/school/risk", "method": "get", "summary": "School-wide student risk dashboard", "roles": ["school_admin", "super_admin"]},
    {"path": "/api/v1/admin/school/weekly-snapshot", "method": "get", "summary": "Generate or retrieve weekly overview snapshot", "roles": ["school_admin", "super_admin"]},
    {"path": "/api/v1/admin/school/rebuild", "method": "post", "summary": "Safe rebuild school projections with checksum", "roles": ["super_admin", "school_admin"]},

    # Research Twin
    {"path": "/api/v1/research/decay", "method": "get", "summary": "Concept decay speed rankings", "roles": ["research_viewer", "super_admin"]},
    {"path": "/api/v1/research/misconceptions", "method": "get", "summary": "Misconception occurrence statistics", "roles": ["research_viewer", "super_admin"]},
    {"path": "/api/v1/research/interventions", "method": "get", "summary": "Interventions success rates", "roles": ["research_viewer", "super_admin"]},
    {"path": "/api/v1/research/discrimination", "method": "get", "summary": "Question discrimination metrics", "roles": ["research_viewer", "super_admin"]},
    {"path": "/api/v1/research/classrooms/speed", "method": "get", "summary": "Classroom learning growth speed rankings", "roles": ["research_viewer", "super_admin"]},
    {"path": "/api/v1/research/correlation/load-decay", "method": "get", "summary": "CCLI load before decay correlation", "roles": ["research_viewer", "super_admin"]},
    {"path": "/api/v1/research/rebuild", "method": "post", "summary": "Safe rebuild research projections with checksum", "roles": ["super_admin", "school_admin"]},
    
    # Production Hardening / Admin
    {"path": "/health", "method": "get", "summary": "Liveness status check", "roles": ["any"]},
    {"path": "/readiness", "method": "get", "summary": "Readiness status check", "roles": ["any"]},
    {"path": "/metrics", "method": "get", "summary": "Prometheus/JSON application metrics", "roles": ["any"]},
    {"path": "/api/v1/admin/audit-logs", "method": "get", "summary": "Get system audit logs", "roles": ["super_admin"]},
    {"path": "/api/v1/admin/backup", "method": "post", "summary": "Trigger online database backup", "roles": ["super_admin"]},
    {"path": "/api/v1/admin/restore", "method": "post", "summary": "Trigger database restore from backup", "roles": ["super_admin"]}
]

def get_swagger_spec():
    """Generates a complete OpenAPI 3.0.0 schema dynamically."""
    paths = {}
    for ep in ENDPOINTS:
        path = ep["path"]
        method = ep["method"]
        
        if path not in paths:
            paths[path] = {}
            
        paths[path][method] = {
            "summary": ep["summary"],
            "description": f"Enforces RBAC Roles: {', '.join(ep['roles'])}",
            "responses": {
                "200": {"description": "Successful operation"},
                "401": {"description": "Unauthorized access"},
                "403": {"description": "Forbidden - Insufficient permissions"}
            }
        }
        
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Cognify Cognitive Platform API Docs",
            "version": config.RELEASE_TAG,
            "description": "Production hardened API specifications for Cognify stage v3.0."
        },
        "paths": paths
    }

def get_swagger_ui_html():
    """Returns a simple Swagger UI HTML page wrapper (Refinement 7)."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <title>Cognify API docs</title>
        <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@3/swagger-ui.css" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-bundle-dist.js"></script>
        <script>
            const ui = SwaggerUIBundle({
                url: '/swagger.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout"
            });
        </script>
    </body>
    </html>
    """
