import pandas as pd

# load original questions
q1 = pd.read_csv("questions.csv")

# load generated questions
q2 = pd.read_csv("generated_questions.csv")

# merge both datasets
merged = pd.concat([q1, q2], ignore_index=True)

# reset ids
merged["id"] = range(1, len(merged) + 1)

# save final question bank
merged.to_csv("final_question_bank.csv", index=False)

print("Total questions in bank:", len(merged))
