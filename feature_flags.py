"""
feature_flags.py
Week 23 — Centralized Feature Flag Management (Decision 8).
"""

import os

FLAGS = {
    "ENABLE_PARENT_TWIN": True,
    "ENABLE_RESEARCH_TWIN": True,
    "ENABLE_ADMIN_TWIN": True,
    "ENABLE_RAT": True,
    "ENABLE_BACKUPS": True,
    "ENABLE_SWAGGER": True
}

def is_enabled(flag_name):
    """
    Returns if a feature flag is enabled.
    Checks environment variable COGNIFY_FF_<flag_name> first.
    """
    env_name = f"COGNIFY_FF_{flag_name}"
    if env_name in os.environ:
        return os.environ[env_name].lower() in ("true", "1")
    return FLAGS.get(flag_name, True)
