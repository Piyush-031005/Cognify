from models.model1.engine import predict_understanding
from models.model2.engine import predict_strategy
from models.model3.engine import predict_behavior


def clamp(val, low=0, high=1):
    return max(low, min(high, val))


def normalize(value, max_val):
    return clamp(value / max_val)


def build_cognitive_flag(understanding, behavior, strategy, hesitation_score, confidence_error):
    if hesitation_score > 0.72 and confidence_error > 0.4:
        return "Hesitation spike with fake confidence"

    elif hesitation_score > 0.55 and behavior == "overthinking":
        return "Decision turbulence detected"

    elif understanding == 1 and hesitation_score < 0.30 and confidence_error < 0.15:
        return "Measured conceptual response"

    elif understanding == 1 and strategy in ["trial-based", "trial"]:
        return "Recovered through elimination"

    elif understanding == 2 and confidence_error > 0.50:
        return "Surface familiarity without certainty"

    elif strategy in ["trial", "trial_based", "trial-based"]:
        return "Reaching through iteration"

    elif behavior == "overthinking":
        return "Cognitive drag detected"

    else:
        return "Unstable answer formation"


def process_question(data):

    response_time = float(data.get("response_time", 0))
    attempts = int(data.get("attempts", 1))
    confidence = float(data.get("confidence", 0.5))
    is_application = int(data.get("is_application", 0))
    correct = int(data.get("correct", 0))

    idle_time = float(data.get("idle_time", 0))
    rewrite_count = int(data.get("rewrite_count", 0))
    backspace_count = int(data.get("backspace_count", 0))
    skipped = int(bool(data.get("skipped", 0)))
    hover_count = int(data.get("hover_count", 0))
    same_option_clicks = int(data.get("same_option_clicks", 0))
    reflection_length = int(data.get("reflection_length", 0))

    question_id = data.get("question_id", "unknown")
    question_text = data.get("question_text", "")

    norm_idle = normalize(idle_time, 12)
    norm_backspace = normalize(backspace_count, 10)
    norm_rewrite = normalize(rewrite_count, 4)
    norm_attempts = normalize(attempts, 3)
    norm_response = normalize(response_time, 18)
    norm_hover = normalize(hover_count, 8)
    norm_same_click = normalize(same_option_clicks, 4)
    norm_reflection = 1 - normalize(reflection_length, 40)

    hesitation_score = round(
    (0.22 * norm_idle) +
    (0.10 * norm_backspace) +
    (0.10 * norm_rewrite) +
    (0.12 * norm_attempts) +
    (0.12 * norm_response) +
    (0.18 * norm_hover) +
    (0.10 * norm_same_click) +
    (0.06 * norm_reflection),
    3
)

    confidence_error = round(confidence * (1 - correct), 3)

    engagement_score = round(
    1 - clamp(
        (
            idle_time +
            rewrite_count +
            skipped * 4 +
            hover_count * 0.6 +
            same_option_clicks * 0.8
        ) / max(response_time + 1, 1)
    ),
    3
)
    understanding_pred = predict_understanding({
        "response_time": response_time,
        "attempts": attempts,
        "confidence": confidence,
        "is_application": is_application,
        "correct": correct
    })

    behavior_pred = predict_behavior({
        "time_taken": response_time,
        "idle_time": idle_time,
        "rewrite_count": rewrite_count,
        "backspace_count": backspace_count,
        "skipped": skipped
    })

    strategy_pred = predict_strategy({
        "confidence": confidence,
        "time_taken": response_time,
        "correct": correct
    })

    # ---------------- HUMAN TELEMETRY OVERRIDE V2 ----------------
    if hesitation_score > 0.42 or hover_count >= 6 or same_option_clicks >= 3:
        behavior_pred = "overthinking"

    if confidence_error > 0.50:
        understanding_pred = 2

    if reflection_length > 0 and reflection_length < 15:
        understanding_pred = 2

    if attempts > 1 or same_option_clicks > 1:
        strategy_pred = "trial-based"

    if correct == 1 and hesitation_score < 0.18 and confidence > 0.78:
        understanding_pred = 1
        strategy_pred = "concept-based"

    cognitive_flag = build_cognitive_flag(
        understanding_pred,
        behavior_pred,
        strategy_pred,
        hesitation_score,
        confidence_error
    )

    return {
        "question_id": question_id,
        "question_text": question_text,
        "response_time": response_time,
        "idle_time": idle_time,
        "rewrite_count": rewrite_count,
        "backspace_count": backspace_count,
        "attempts": attempts,
        "confidence": confidence,
        "correct": correct,
        "is_application": is_application,
        "skipped": skipped,
        "hesitation_score": hesitation_score,
        "confidence_error": confidence_error,
        "engagement_score": engagement_score,
        "understanding_pred": understanding_pred,
        "behavior_pred": behavior_pred,
        "strategy_pred": strategy_pred,
        "cognitive_flag": cognitive_flag,
        "hover_count": hover_count,
        "same_option_clicks": same_option_clicks,
        "reflection_length": reflection_length
    }