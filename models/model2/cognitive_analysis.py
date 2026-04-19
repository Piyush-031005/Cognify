import pandas as pd

data = pd.read_csv("final_results.csv")

# average understanding per topic
topic_scores = data.groupby("topic")["understanding_score"].mean()

print("\nTopic Understanding Scores:\n")
print(topic_scores)

# save results
topic_scores.to_csv("topic_understanding.csv")
