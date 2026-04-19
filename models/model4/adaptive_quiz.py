import pandas as pd
import joblib

# ---------------------------
# LOAD CSV (SAFE)
# ---------------------------
df = pd.read_csv("questions_final.csv", on_bad_lines="skip", header=None)

# fix broken rows
df = df.iloc[:, :9]

df.columns = ["subject","topic","type","question","A","B","C","D","answer"]

# remove header rows if repeated
df = df[df["subject"] != "subject"]

# clean
df["subject"] = df["subject"].astype(str).str.strip().str.lower()
df["topic"] = df["topic"].astype(str).str.strip().str.lower()
df["type"] = df["type"].astype(str).str.strip().str.lower()
df["answer"] = df["answer"].astype(str).str.strip().str.upper()

print("✅ Dataset loaded:", df.shape)

# ---------------------------
# ASK QUESTION
# ---------------------------
def ask_question(row):

    options = {
        "A": row.get("A"),
        "B": row.get("B"),
        "C": row.get("C"),
        "D": row.get("D")
    }

    # count valid options
    valid_options = [k for k,v in options.items() if pd.notna(v) and str(v).strip() != ""]

    # skip if less than 2 options (avoid bad dataset)
    if len(valid_options) < 2:
        return None

    print("\n" + "="*50)
    print("🧠 QUESTION:")
    print(row["question"])
    print("\nOPTIONS:")

    for key in valid_options:
        print(f"{key}: {options[key]}")

    print("="*50)

    while True:
        ans = input(f"👉 Your answer {valid_options}: ").strip().upper()

        if ans in valid_options:
            return ans == row["answer"]
        else:
            print("❌ Invalid input")

# ---------------------------
# MAIN QUIZ
# ---------------------------
def run_quiz(subject, topic):

    topic_df = df[
        (df["subject"] == subject) &
        (df["topic"] == topic)
    ]

    print("\n📊 Questions Found:", len(topic_df))

    if len(topic_df) == 0:
        print("❌ No questions found")
        return

    results = {"basic": [], "conceptual": [], "application": [], "tricky": []}

    for q_type in results.keys():

        subset = topic_df[topic_df["type"] == q_type]

        if len(subset) == 0:
            continue

        questions = subset.sample(min(2, len(subset)))

        for _, row in questions.iterrows():
            print("\n🧠 New Question")
            correct = ask_question(row)

            if correct is None:
                continue

            results[q_type].append(correct)

    # ---------------------------
    # ACCURACY
    # ---------------------------
    def calc_acc(lst):
        return sum(lst)/len(lst) if lst else 0

    basic_acc = calc_acc(results["basic"])
    conceptual_acc = calc_acc(results["conceptual"])
    application_acc = calc_acc(results["application"])
    tricky_acc = calc_acc(results["tricky"])

    # ---------------------------
    # PERFORMANCE SUMMARY
    # ---------------------------
    print("\n📊 Performance Summary:")

    print("✔ Strong in basics" if basic_acc > 0.7 else "❗ Weak in basics")
    print("✔ Good conceptual understanding" if conceptual_acc > 0.7 else "❗ Concept clarity needs work")
    print("✔ Good problem solving" if application_acc > 0.7 else "❗ Needs more practice in applying concepts")
    print("✔ Handles tricky problems well" if tricky_acc > 0.7 else "❗ Struggles with tricky problems")

    # ---------------------------
    # SAVE DATA
    # ---------------------------
    scores = {
        "basic": basic_acc,
        "conceptual": conceptual_acc,
        "application": application_acc,
        "tricky": tricky_acc
    }

    weak_area = min(scores, key=scores.get)

    data = {
        "basic_acc": basic_acc,
        "conceptual_acc": conceptual_acc,
        "application_acc": application_acc,
        "tricky_acc": tricky_acc,
        "weak_area": weak_area
    }

    pd.DataFrame([data]).to_csv("weakness_dataset.csv", mode="a", header=False, index=False)

    print("\n✅ Data saved!")

    # ---------------------------
    # ML PREDICTION
    # ---------------------------
    try:
        model = joblib.load("weakness_model.pkl")

        input_df = pd.DataFrame([data]).drop("weak_area", axis=1)

        prediction = model.predict(input_df)[0]

        print("\n🧠 Insight:")

        if prediction == "basic":
            print("👉 Your fundamentals need improvement.")
        elif prediction == "conceptual":
            print("👉 Conceptual clarity is weak.")
        elif prediction == "application":
            print("👉 You understand but struggle to apply.")
        elif prediction == "tricky":
            print("👉 Tricky problems are challenging.")
        else:
            print("👉 Mixed performance.")

    except:
        print("\n⚠️ Model not found")

# ---------------------------
# USER FLOW
# ---------------------------
subjects = list(df["subject"].unique())

print("\n📚 Subjects:")
for i, s in enumerate(subjects):
    print(f"{i+1}. {s.upper()}")

while True:
    try:
        choice = int(input("Select subject: "))
        if 1 <= choice <= len(subjects):
            subject = subjects[choice - 1]
            break
        else:
            print("❌ Invalid choice")
    except:
        print("❌ Enter a number")

topics = list(df[df["subject"] == subject]["topic"].unique())

print(f"\n📖 Topics in {subject.upper()}:")
for i, t in enumerate(topics):
    print(f"{i+1}. {t.title()}")

while True:
    try:
        choice = int(input("Select topic: "))
        if 1 <= choice <= len(topics):
            topic = topics[choice - 1]
            break
        else:
            print("❌ Invalid choice")
    except:
        print("❌ Enter a number")

# RUN
run_quiz(subject, topic)