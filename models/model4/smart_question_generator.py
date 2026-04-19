import pandas as pd
import random

# load dataset
df = pd.read_csv("questions_final.csv")

def generate_question(topic, strategy, behavior):

    # 🔥 mapping logic
    if strategy == "trial":
        q_type = "basic"

    elif strategy == "pattern":
        q_type = "conceptual"

    elif strategy == "mixed":
        q_type = "application"

    elif strategy == "conceptual":
        if behavior in ["confused", "overthinking"]:
            q_type = "application"
        else:
            q_type = "deep"
    else:
        q_type = "basic"

    # filter
    filtered = df[(df["topic"] == topic) & (df["question_type"] == q_type)]

    if len(filtered) == 0:
        return "No question available"

    return random.choice(filtered["question"].values)


# -------- TEST --------

topic = input("Enter topic (stack/queue): ")
strategy = input("Enter strategy (trial/pattern/mixed/conceptual): ")
behavior = input("Enter behavior (confident/confused/overthinking): ")

q = generate_question(topic, strategy, behavior)

print("\n🧠 AI Generated Question:")
print(q)