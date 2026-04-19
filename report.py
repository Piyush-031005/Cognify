from collections import Counter
from models.model5.engine import predict_future

def analyze_reflection(text):
    words = text.split()
    length = len(words)

    if length < 8:
        return "Weak"
    elif "because" in text.lower() or "means" in text.lower():
        return "Strong"
    else:
        return "Moderate"


def generate_report(data):
    u = data["understanding"]
    b = data["behavior"]
    reflection = data.get("reflection", "")

    def calc(arr):
        if len(arr) == 0:
            return {}
        c = Counter(arr)
        total = len(arr)
        return {k: round(v/total, 2) for k, v in c.items()}

    u_res = calc(u)
    b_res = calc(b)

    # mapping
    conceptual = u_res.get(1, 0)
    memorized = u_res.get(0, 0)
    fake = u_res.get(2, 0)

    hesitant = b_res.get("hesitant", 0)
    confident = b_res.get("confident", 0)

    
    s = data.get("strategy", [])
    s_res = calc(s) 

    future = predict_future({
        "conceptual": conceptual,
        "memorized": memorized,
        "fake": fake,
        "hesitant": hesitant,
        "confident": confident
    })

    reflection_score = analyze_reflection(reflection)

    return {
    "understanding_analysis": u_res,
    "behavior_analysis": b_res,
    "future_prediction": future,
    "reflection_analysis": reflection_score,   
    "strategy_analysis": s_res
}

