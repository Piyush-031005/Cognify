import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
import joblib

# load data
df = pd.read_csv("model1_dataset.csv")

X = df.drop("label", axis=1)
y = df["label"]

# scaling important for NN
scaler = StandardScaler()
X = scaler.fit_transform(X)

# split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# model
model = MLPClassifier(
    hidden_layer_sizes=(64,32),
    max_iter=1000,
    learning_rate_init=0.001
)
model.fit(X_train, y_train)

# accuracy
print("Accuracy:", model.score(X_test, y_test))

# save
joblib.dump(model, "model1.pkl")
joblib.dump(scaler, "scaler.pkl")

print("Model trained & saved!")