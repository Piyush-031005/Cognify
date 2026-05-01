import math


def clamp(x, low=0, high=1):
    return max(low, min(high, x))


def predict_future(data):
    """
    Enterprise Predictive Cognitive Projection Engine
    Inputs:
    conceptual, memorized, fake, hesitant, confident
    """

    conceptual = float(data.get("conceptual", 0))
    memorized = float(data.get("memorized", 0))
    fake = float(data.get("fake", 0))
    hesitant = float(data.get("hesitant", 0))
    confident = float(data.get("confident", 0))

    # -----------------------------
    # CORE LEARNING STABILITY SCORE
    # -----------------------------
    stability = (
        conceptual * 0.42 +
        confident * 0.22 -
        fake * 0.20 -
        hesitant * 0.16
    )

    # -----------------------------
    # RETENTION RISK SCORE
    # -----------------------------
    retention_risk = (
        fake * 0.38 +
        memorized * 0.22 +
        hesitant * 0.20 +
        (1 - confident) * 0.20
    )

    # -----------------------------
    # ADAPTIVE GROWTH SCORE
    # -----------------------------
    growth = (
        conceptual * 0.45 +
        confident * 0.25 +
        (1 - fake) * 0.15 +
        (1 - hesitant) * 0.15
    )

    stability = clamp(stability)
    retention_risk = clamp(retention_risk)
    growth = clamp(growth)

    # -----------------------------
    # FINAL DECISION LOGIC
    # -----------------------------
    if retention_risk > 0.58 and conceptual < 0.35:
        return "Decline"

    if growth > 0.62 and conceptual >= fake:
        return "Improve"

    if stability >= 0.40 and retention_risk < 0.60:
        return "Stable"

    if fake > 0.45 and hesitant > 0.28:
        return "Decline"

    return "Stable"