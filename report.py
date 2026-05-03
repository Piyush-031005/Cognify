from collections import Counter
from models.model5.engine import predict_future
from database import get_student_attempt_responses


def analyze_reflection(text):
    words = text.strip().split()
    length = len(words)
    lower = text.lower()

    conceptual_words = [
        "because", "means", "concept", "formula",
        "velocity", "displacement", "acceleration",
        "understand", "relation", "depends"
    ]

    concept_hits = sum(1 for w in conceptual_words if w in lower)

    if length < 4:
        return "Very Weak"
    elif length < 8:
        return "Weak"
    elif concept_hits >= 2:
        return "Strong"
    else:
        return "Moderate"
    
def safe_avg(arr):
    return round(sum(arr) / len(arr), 2) if arr else 0


def generate_report(student_email, attempt_id, reflection=""):
    question_sessions = get_student_attempt_responses(student_email, attempt_id)
    if len(question_sessions) == 0:
        return {}

    total = len(question_sessions)
    avg_hover = safe_avg([q.get("hover_count", 0) for q in question_sessions])
    avg_same_click = safe_avg([q.get("same_option_clicks", 0) for q in question_sessions])
    avg_reflection_len = safe_avg([q.get("reflection_length", 0) for q in question_sessions])

    understanding_labels = [q["understanding_pred"] for q in question_sessions]
    uc = Counter(understanding_labels)

    conceptual = round((uc.get(1, 0) / total), 2)
    memorized = round((uc.get(0, 0) / total), 2)
    fake = round((uc.get(2, 0) / total), 2)

    avg_hesitation = safe_avg([q["hesitation_score"] for q in question_sessions])
    avg_conf_error = safe_avg([q["confidence_error"] for q in question_sessions])
    avg_engagement = safe_avg([q["engagement_score"] for q in question_sessions])

    if conceptual > 0 and avg_hesitation < 0.22:
        conceptual = min(1, conceptual + 0.08)

    if fake > 0 and avg_reflection_len > 10:
        fake = max(0, fake - 0.06)

    confidence_meter = round(
    max(0, 1 - avg_conf_error - avg_same_click * 0.04 + avg_reflection_len * 0.005),
    2
    )
    confidence_meter = min(confidence_meter, 1)

    overthinking_meter = round(
        avg_hesitation * 0.55 +
        (1 - avg_engagement) * 0.22 +
        avg_hover * 0.015,
        2
    )
    overthinking_meter = min(overthinking_meter, 1)

    strategy_labels = [str(q["strategy_pred"]) for q in question_sessions]
    sc = Counter(strategy_labels)

    future = predict_future({
        "conceptual": conceptual,
        "memorized": memorized,
        "fake": fake,
        "hesitant": avg_hesitation,
        "confident": confidence_meter
    })

    if conceptual > 0.55 and confidence_meter > 0.55:
        future = "Growth likely with strong conceptual adaptation"

    elif fake > 0.55 and confidence_meter < 0.4:
        future = "Risk of academic decline unless conceptual correction happens"

    elif overthinking_meter > 0.45:  
        future = "Potential slowed performance due to internal decision friction"

    trial_ratio = sc.get("trial-based", 0) + sc.get("trial", 0)
    concept_ratio = sc.get("concept-based", 0)

    if trial_ratio > concept_ratio:
        dominant_pattern = "Trial-based"
    elif fake > 0.45 and avg_hesitation > 0.28:
        dominant_pattern = "Mixed"
    else:
        dominant_pattern = "Concept-based"

    reflection_score = analyze_reflection(reflection)

    high_hes_q = max(question_sessions, key=lambda x: x["hesitation_score"])
    low_eng_q = min(question_sessions, key=lambda x: x["engagement_score"])

    insights = [
    f"Strongest hesitation surfaced on '{high_hes_q['question_text']}' where decision latency noticeably increased.",
    f"Engagement dipped most on '{low_eng_q['question_text']}', suggesting weaker cognitive anchoring.",
    f"Reflection writing showed {reflection_score.lower()} conceptual articulation after the quiz.",
    f"Option scanning stayed active throughout the session (avg {avg_hover}), indicating visible internal checking.",
    f"Self-doubt reclick behavior remained {avg_same_click} on average across questions."
]

    return {
    "conceptual": conceptual,
    "memorized": memorized,
    "fake": fake,
    "hesitation": avg_hesitation,
    "confidence": confidence_meter,
    "overthinking": overthinking_meter,
    "strategy_distribution": dict(sc),
    "dominant_pattern": dominant_pattern,
    "future_prediction": future,
    "reflection_analysis": reflection_score,
    "insights": insights,
    "question_timeline": question_sessions,
    "perQuestion": question_sessions
}