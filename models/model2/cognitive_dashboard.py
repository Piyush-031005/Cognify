import pandas as pd
import matplotlib.pyplot as plt

# load responses
data = pd.read_csv("responses.csv")

# topic wise average score
topic_scores = data.groupby("topic")["understanding_score"].mean()

# convert to dataframe
topic_scores = topic_scores.reset_index()

print("\nTopic Understanding Scores\n")
print(topic_scores)

# plot graph
plt.figure(figsize=(8,5))

plt.bar(topic_scores["topic"], topic_scores["answer_correct"])

plt.title("Student Cognitive Understanding by Topic")
plt.xlabel("Topics")
plt.ylabel("Average Understanding Score")

plt.savefig("cognitive_dashboard.png")

plt.show()
