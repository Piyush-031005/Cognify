import joblib
import os
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
model = joblib.load(os.path.join(BASE_DIR, "weakness_model.pkl"))

def get_weakness(data):
    u = data.get("understanding", [])
    s = data.get("strategy", [])

    total = len(u) if len(u) > 0 else 1

    # values
    conceptual_acc = u.count(1) / total
    basic_acc = u.count(0) / total
    tricky_acc = u.count(2) / total
    application_acc = s.count("application") / total

    # 🔥 safety
    application_acc = float(application_acc)
    basic_acc = float(basic_acc)
    conceptual_acc = float(conceptual_acc)
    tricky_acc = float(tricky_acc)

    # 🔥 DEBUG (INSIDE FUNCTION)
    print("DEBUG INPUT:", {
        "application_acc": application_acc,
        "basic_acc": basic_acc,
        "conceptual_acc": conceptual_acc,
        "tricky_acc": tricky_acc
    })

    # dataframe with correct order
    df = pd.DataFrame([{
    "application_acc": application_acc,
    "basic_acc": basic_acc,
    "conceptual_acc": conceptual_acc,
    "tricky_acc": tricky_acc
}])

# 🔥 FORCE EXACT TRAINING ORDER
    df = df[model.feature_names_in_]

    # 🔥 extra safety (very important)
    df = df.astype(float)

    pred = model.predict(df)[0]
    return str(pred)