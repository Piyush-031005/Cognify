"""
config.py
Week 23 — Centralized Configuration Management.
"""

import os

# Secret key for signing tokens
COGNIFY_SECRET_KEY = os.environ.get("COGNIFY_SECRET_KEY", "cognify_default_secret_key_1234567890_abc")

# Database name
DATABASE_URL = os.environ.get("DATABASE_URL", "cognify.db")

# Flag to bypass auth checks during regression testing
COGNIFY_BYPASS_AUTH = os.environ.get("COGNIFY_BYPASS_AUTH", "true").lower() == "true"

# Current Version details
DATABASE_VERSION = "v3.0"
SCHEMA_VERSION = "v3.0"
RELEASE_TAG = "v3.0.0-rc1"
GIT_COMMIT = os.environ.get("GIT_COMMIT", "844d6e3") # Default fallback to main commit
