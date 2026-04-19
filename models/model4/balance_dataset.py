import pandas as pd

# load dataset
df = pd.read_csv("weakness_dataset.csv")

# ❌ remove garbage labels
df = df[df["weak_area"].isin(["basic","conceptual","application","tricky"])]

# check count
print("Before balance:\n", df["weak_area"].value_counts())

# ✅ balance dataset
min_count = df["weak_area"].value_counts().min()

df_balanced = df.groupby("weak_area").sample(min_count)

# save new file
df_balanced.to_csv("balanced_dataset.csv", index=False)

print("\nAfter balance:\n", df_balanced["weak_area"].value_counts())
print("\n✅ Balanced dataset saved as balanced_dataset.csv")