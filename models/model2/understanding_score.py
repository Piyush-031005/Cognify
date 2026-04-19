import pandas as pd

data = pd.read_csv("processed_responses.csv")

def calculate_score(row):

    score = 50   # base score

    if row["answer_correct"] == 1:
        score += 10
    else:
        score -= 10

    if row["answer_correct"] == 1 and row["confidence"] >= 4:
        score += 5

    if row["answer_correct"] == 0 and row["confidence"] >= 4:
        score -= 15

    if row["answer_correct"] == 1 and row["confidence"] <= 2:
        score -= 5

    return score


data["understanding_score"] = data.apply(calculate_score, axis=1)

data.to_csv("final_results.csv", index=False)

print(data[["answer_correct","confidence","understanding_score"]])
