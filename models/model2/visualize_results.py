import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv("topic_understanding.csv")

plt.figure(figsize=(8,5))

plt.bar(data["topic"], data["understanding_score"])

plt.title("Topic Understanding Scores")
plt.xlabel("Topics")
plt.ylabel("Understanding Score")

plt.savefig("topic_understanding_graph.png")

plt.show()
