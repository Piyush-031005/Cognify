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


# Configurable Fusion Layer parameters/rules (Layer 5)
FUSION_RULES = {
    "weights": {
        "understanding_conceptual": 0.7,
        "strategy_conceptual": 0.3,
        "understanding_recall": 0.8,
        "strategy_trial": 0.2,
        "understanding_surface": 0.6,
        "strategy_concept_transfer": 0.4,
        "behavior_hesitation": 0.6,
        "strategy_trial_velocity": 0.4,
        "behavior_confident": 0.7,
        "telemetry_confidence_error": 0.3,
        "behavior_overthinking": 0.7,
        "telemetry_engagement": 0.3,
        "strategy_persistence": 0.7,
        "strategy_trial_persistence": 0.3
    },
    "thresholds": {
        "mixed_pattern_hesitation": 0.28,
        "mixed_pattern_surface": 0.45,
        "reflection_length_max": 30.0
    }
}


def fuse_evidence(question_sessions, reflection=""):
    total = len(question_sessions)
    if total == 0:
        return {
            "learning_velocity": 0.5,
            "conceptual_depth": 0.5,
            "confidence_stability": 0.5,
            "attention_stability": 0.5,
            "persistence": 0.5,
            "memory_dependence": 0.5,
            "transfer_ability": 0.5,
            "curiosity": 0.5,
            "dominant_pattern": "Concept-based",
            "understanding_fusion": 0.5,
            "strategy_fusion": 0.5,
            "behavior_fusion": 0.5,
            "confidence_score": 0.85
        }

    # Extract predictions from the 3 evaluation heads
    understanding_labels = [q.get("understanding_pred", 1) for q in question_sessions]
    strategy_labels = [str(q.get("strategy_pred", "concept-based")).lower() for q in question_sessions]
    behavior_labels = [str(q.get("behavior_pred", "confident")).lower() for q in question_sessions]

    # Calculate proportions
    conceptual_ratio = sum(1 for x in understanding_labels if x == 1) / total
    recall_ratio = sum(1 for x in understanding_labels if x == 0) / total
    surface_ratio = sum(1 for x in understanding_labels if x == 2) / total

    trial_ratio = sum(1 for x in strategy_labels if "trial" in x) / total
    concept_ratio = sum(1 for x in strategy_labels if "concept" in x) / total

    overthinking_ratio = sum(1 for x in behavior_labels if "overthinking" in x) / total
    confident_ratio = sum(1 for x in behavior_labels if "confident" in x or "stable" in x) / total
    hesitant_ratio = sum(1 for x in behavior_labels if "hesitation" in x or "confused" in x) / total

    avg_hesitation = safe_avg([q.get("hesitation_score") if q.get("hesitation_score") is not None else 0.5 for q in question_sessions])
    avg_conf_error = safe_avg([q.get("confidence_error") if q.get("confidence_error") is not None else 0.5 for q in question_sessions])
    avg_engagement = safe_avg([q.get("engagement_score") if q.get("engagement_score") is not None else 0.5 for q in question_sessions])

    # Fused Assessment Metrics using configurable FUSION_RULES weights
    w = FUSION_RULES["weights"]
    fused_conceptual_depth = round(conceptual_ratio * w["understanding_conceptual"] + concept_ratio * w["strategy_conceptual"], 3)
    fused_memory_dependence = round(recall_ratio * w["understanding_recall"] + trial_ratio * w["strategy_trial"], 3)
    fused_transfer_ability = round((1.0 - surface_ratio) * w["understanding_surface"] + concept_ratio * w["strategy_concept_transfer"], 3)
    
    # Velocity, confidence, and attention stability
    fused_learning_velocity = round((1.0 - avg_hesitation) * w["behavior_hesitation"] + (1.0 - trial_ratio) * w["strategy_trial_velocity"], 3)
    fused_confidence_stability = round(confident_ratio * w["behavior_confident"] + (1.0 - avg_conf_error) * w["telemetry_confidence_error"], 3)
    fused_attention_stability = round((1.0 - overthinking_ratio) * w["behavior_overthinking"] + avg_engagement * w["telemetry_engagement"], 3)

    persistence = round(concept_ratio * w["strategy_persistence"] + (1.0 - trial_ratio) * w["strategy_trial_persistence"], 3)
    
    words = reflection.strip().split()
    curiosity = round(min(1.0, len(words) / FUSION_RULES["thresholds"]["reflection_length_max"]), 3)

    # Determine dominant pattern
    t = FUSION_RULES["thresholds"]
    if trial_ratio > concept_ratio:
        dominant_pattern = "Trial-based"
    elif surface_ratio > t["mixed_pattern_surface"] and avg_hesitation > t["mixed_pattern_hesitation"]:
        dominant_pattern = "Mixed"
    else:
        dominant_pattern = "Concept-based"

    # Propagate head prediction confidence scores to calculate dynamic session confidence
    avg_understanding_conf = safe_avg([q.get("understanding_conf", 0.79) for q in question_sessions])
    avg_strategy_conf = safe_avg([q.get("strategy_conf", 0.92) for q in question_sessions])
    avg_behavior_conf = safe_avg([q.get("behavior_conf", 0.97) for q in question_sessions])
    
    session_confidence = round(
        avg_understanding_conf * 0.45 +
        avg_strategy_conf * 0.35 +
        avg_behavior_conf * 0.20,
        3
    )

    return {
        "learning_velocity": fused_learning_velocity,
        "conceptual_depth": fused_conceptual_depth,
        "confidence_stability": fused_confidence_stability,
        "attention_stability": fused_attention_stability,
        "persistence": persistence,
        "memory_dependence": fused_memory_dependence,
        "transfer_ability": fused_transfer_ability,
        "curiosity": curiosity,
        "dominant_pattern": dominant_pattern,
        "understanding_fusion": round(conceptual_ratio, 3),
        "strategy_fusion": round(concept_ratio, 3),
        "behavior_fusion": round(confident_ratio, 3),
        "confidence_score": session_confidence
    }


def generate_recommendations(fused_vector):
    recommendations = []
    
    # overall confidence score to display to teachers (calibrated propagation)
    rec_confidence = f"{fused_vector.get('confidence_score', 0.85)*100:.0f}%"

    # Recommendation 1: Concept mapping vs Memory dependence
    if fused_vector["conceptual_depth"] < 0.6 and fused_vector["memory_dependence"] > 0.4:
        recommendations.append({
            "id": 101,
            "concept": "Roots & Quadratic Functions",
            "priority": "HIGH",
            "reason": "Weak conceptual grounding paired with high rote memory dependence",
            "evidence": f"Memory reliance is {fused_vector['memory_dependence']*100:.1f}%, conceptual depth is {fused_vector['conceptual_depth']*100:.1f}%",
            "confidence": rec_confidence,
            "suggestedAction": "Run interactive comparative concept-mapping drills to separate algebraic formulas from graphical behaviors.",
            "expectedGain": "+20% transfer precision in application-based tasks",
            "estimatedTime": "15 minutes",
            "validationExercise": "Parabola vertex translation challenge (map algebraic forms to graphs)"
        })
        
    # Recommendation 2: Attention & Overthinking vs Confidence stability
    if fused_vector["attention_stability"] < 0.6 and fused_vector["confidence_stability"] < 0.6:
        recommendations.append({
            "id": 102,
            "concept": "Discriminant Calculation Speed",
            "priority": "HIGH",
            "reason": "Significant decision latency and overthinking with unstable option commit confidence",
            "evidence": f"Overthinking ratio detected, confidence stability index is low at {fused_vector['confidence_stability']:.2f}",
            "confidence": rec_confidence,
            "suggestedAction": "Conduct rapid 5-second assertion drills on simple discriminant signs (D > 0, D = 0, D < 0) to bypass analytical paralysis.",
            "expectedGain": "-35% reduction in option hover scan counts and search time",
            "estimatedTime": "10 minutes",
            "validationExercise": "Real-time sign flashcard round (10 cards, timed completion)"
        })

    # Recommendation 3: Transfer ability failure
    if fused_vector["transfer_ability"] < 0.6:
        recommendations.append({
            "id": 103,
            "concept": "Quadratic Applications",
            "priority": "MEDIUM",
            "reason": "Knowledge strain when transitioning from recall questions to multi-step application scenarios",
            "evidence": f"Transfer ability index is low ({fused_vector['transfer_ability']:.2f}) despite stable recall features",
            "confidence": rec_confidence,
            "suggestedAction": "Provide structured visual walk-throughs of real-world projectile paths followed by a collaborative mini-quiz.",
            "expectedGain": "+25% increase in first-attempt correctness on multi-step problems",
            "estimatedTime": "20 minutes",
            "validationExercise": "Staging launch height optimization scenario calculation"
        })

    # Default fallback if metrics are completely healthy
    if not recommendations:
        recommendations.append({
            "id": 104,
            "concept": "Advanced Polynomials",
            "priority": "LOW",
            "reason": "Strong balanced performance across all three prediction heads",
            "evidence": f"Conceptual depth is {fused_vector['conceptual_depth']*100:.1f}%, transfer ability is {fused_vector['transfer_ability']*100:.1f}%",
            "confidence": "95%",
            "suggestedAction": "Deploy non-linear extensions like cubic equations and graphical transformations to push limits.",
            "expectedGain": "Elevate learning velocity to peak capacity",
            "estimatedTime": "25 minutes",
            "validationExercise": "Visual inflection point mapping challenge"
        })
        
    return recommendations


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
        f"We observed the strongest hesitation on '{high_hes_q['question_text']}' where decision latency noticeably increased.",
        f"Our analysis indicates engagement dipped most on '{low_eng_q['question_text']}', suggesting weaker cognitive anchoring.",
        f"We noticed that reflection writing showed {reflection_score.lower()} conceptual articulation after the quiz.",
        f"We tracked active option scanning throughout the session (avg {avg_hover}), indicating visible internal checking.",
        f"We measured self-doubt reclick behavior at {avg_same_click} on average across questions."
    ]

    # Invoke the Evidence Fusion Layer (Layer 5)
    fused_assessment = fuse_evidence(question_sessions, reflection)

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
        "perQuestion": question_sessions,
        "fused_assessment": fused_assessment
    }