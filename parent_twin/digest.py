"""
parent_twin/digest.py
Decision 2 — Privacy-by-Design: All parent-facing language passes through this module.
These are PURE functions. No DB access. No side effects.
"""


def translate_memory_health(memory_strength: float) -> str:
    """Translate raw memory_strength [0,1] → human-readable parent digest."""
    if memory_strength >= 0.70:
        return "Learning well"
    elif memory_strength >= 0.40:
        return "Needs more practice"
    else:
        return "Struggling — support recommended"


def translate_attention(focus_state: str) -> str:
    """Translate raw focus_state → human-readable parent digest."""
    mapping = {
        "optimal": "Focused",
        "recovering": "Focused",
        "decay": "Slightly distracted",
        "distracted": "Slightly distracted",
        "fatigued": "Tired — needs a break",
        "overloaded": "Tired — needs a break",
    }
    return mapping.get(focus_state, "Focused")


def translate_cognitive_health(score: float) -> str:
    """Translate cognitive_health_score [0,1] → overall parent digest."""
    if score >= 0.75:
        return "Doing great"
    elif score >= 0.50:
        return "Progressing steadily"
    else:
        return "Needs attention"


def translate_memory_trend(recent_scores: list) -> str:
    """
    Determine memory trend direction from a list of recent health scores (oldest→newest).
    Returns 'improving', 'stable', or 'declining'.
    """
    if not recent_scores or len(recent_scores) < 2:
        return "stable"
    delta = recent_scores[-1] - recent_scores[0]
    if delta > 0.05:
        return "improving"
    elif delta < -0.05:
        return "declining"
    return "stable"


def translate_ccli(rolling_ccli: float) -> str:
    """Translate CCLI load score → parent-readable phrase."""
    if rolling_ccli <= 0.40:
        return "Working comfortably"
    elif rolling_ccli <= 0.70:
        return "Moderate study load"
    else:
        return "Overloaded — recommend a break"


def build_study_habit_summary(streak: int, active_days: int, total_sessions: int) -> dict:
    """
    Construct a parent-facing study habit summary from projection fields.
    """
    consistency = "Excellent" if streak >= 7 else ("Good" if streak >= 3 else "Needs improvement")
    return {
        "current_streak_days": streak,
        "active_days_this_week": active_days,
        "total_sessions": total_sessions,
        "consistency_label": consistency,
        "habit_summary": (
            f"Your child has studied {active_days} day(s) this week "
            f"with a {streak}-day streak. Consistency is rated: {consistency}."
        )
    }


def build_recommendations(overall_digest: str, memory_trend: str, attention_digest: str) -> list:
    """
    Produce 2–3 plain-English parent recommendations.
    Based solely on digest labels — no raw metrics.
    """
    recs = []
    if overall_digest == "Needs attention":
        recs.append("Schedule a quiet 30-minute study session with your child each evening.")
    if memory_trend == "declining":
        recs.append("Encourage your child to review topics from the past week — memory needs refreshing.")
    if attention_digest in ("Tired — needs a break", "Slightly distracted"):
        recs.append("Make sure your child gets 8+ hours of sleep and takes regular breaks while studying.")
    if not recs:
        recs.append("Keep up the great work! Consistent practice is key to long-term learning.")
    return recs
