import pandas as pd
import random

# load processed data
df = pd.read_csv("processed_responses.csv")

def assign_strategy(row):
    
    # 🔥 10% randomness (anti-overfitting)
    if random.random() < 0.1:
        return random.choice(["trial", "conceptual", "pattern", "mixed"])

    # Trial-based: fast + wrong
    if row["time_taken"] < 7 and row["answer_correct"] == 0:
        return "trial"

    # Conceptual: slow + correct + confident
    elif row["time_taken"] > 10 and row["answer_correct"] == 1 and row["confidence"] >= 4:
        return "conceptual"

    # Pattern-based: high confidence but wrong
    elif row["confidence"] >= 4 and row["answer_correct"] == 0:
        return "pattern"

    else:
        return "mixed"

# apply labeling
df["strategy_type"] = df.apply(assign_strategy, axis=1)

# save updated dataset
df.to_csv("processed_responses_with_strategy.csv", index=False)

print("Strategy labels added with noise!")
print(df[["time_taken", "confidence", "answer_correct", "strategy_type"]].head())