import pandas as pd
import random

# ---------------------------
# LOAD & FIX CSV 🔥
# ---------------------------
df = pd.read_csv(
    "questions_final.csv",
    on_bad_lines="skip",
    header=None
)

# FORCE COLUMNS
df.columns = ["subject","topic","type","question","A","B","C","D","answer"]

# REMOVE WRONG HEADER ROWS
df = df[df["subject"] != "subject"]

# CLEAN DATA
df["subject"] = df["subject"].astype(str).str.strip().str.lower()
df["topic"] = df["topic"].astype(str).str.strip().str.lower()
df["type"] = df["type"].astype(str).str.strip().str.lower()
df["answer"] = df["answer"].astype(str).str.strip().str.upper()

# DEBUG CHECK (optional)
print("✅ Dataset Loaded:", df.shape)


# ---------------------------
# RANDOM ANSWER GENERATOR
# ---------------------------
def simulate_answer(correct_answer, bias=0.6):
    options = ["A", "B", "C", "D"]

    if random.random() < bias:
        return correct_answer
    else:
        wrong = [op for op in options if op != correct_answer]
        return random.choice(wrong)


# ---------------------------
# SIMULATE ONE QUIZ
# ---------------------------
def run_simulation():

    results = {"basic": [], "conceptual": [], "application": [], "tricky": []}

    for q_type in results.keys():

        subset = df[df["type"] == q_type]

        if len(subset) == 0:
            continue

        # ensure enough questions
        questions = subset.sample(n=3, replace=True)

        for _, row in questions.iterrows():
            user_ans = simulate_answer(row["answer"], bias=random.uniform(0.3, 0.8))
            correct = user_ans == row["answer"]
            results[q_type].append(correct)

    # ---------------------------
    # ACCURACY CALCULATION
    # ---------------------------
    basic_acc = sum(results["basic"]) / len(results["basic"]) if results["basic"] else 0
    conceptual_acc = sum(results["conceptual"]) / len(results["conceptual"]) if results["conceptual"] else 0
    application_acc = sum(results["application"]) / len(results["application"]) if results["application"] else 0
    tricky_acc = sum(results["tricky"]) / len(results["tricky"]) if results["tricky"] else 0

    scores = {
        "basic": basic_acc,
        "conceptual": conceptual_acc,
        "application": application_acc,
        "tricky": tricky_acc
    }

    # detect weakest
    if all(v == 0 for v in scores.values()):
        weak_area = "unknown"
    else:
        weak_area = min(scores, key=scores.get)

    return {
        "basic_acc": basic_acc,
        "conceptual_acc": conceptual_acc,
        "application_acc": application_acc,
        "tricky_acc": tricky_acc,
        "weak_area": weak_area
    }


# ---------------------------
# MAIN LOOP (🔥 GENERATE DATA)
# ---------------------------
data = []

for i in range(1200):   # 🔥 change if needed
    row = run_simulation()
    data.append(row)

df_new = pd.DataFrame(data)

df_new.to_csv("weakness_dataset.csv", mode="a", header=False, index=False)

print("\n🔥 Auto dataset generated successfully!")