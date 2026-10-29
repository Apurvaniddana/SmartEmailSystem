import pandas as pd
import os
import re
import joblib

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# Find project folder
project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# Validation dataset
dataset_path = os.path.join(
    project_folder,
    "dataset",
    "validation_emails.csv"
)


# Saved improved model
model_path = os.path.join(
    project_folder,
    "saved_model",
    "improved_linear_svc.pkl"
)

vectorizer_path = os.path.join(
    project_folder,
    "saved_model",
    "improved_tfidf_vectorizer.pkl"
)


# Load files
data = pd.read_csv(dataset_path)

model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)


print("Validation dataset loaded!")
print("Total validation emails:", len(data))


# Combine subject + message
data["Subject"] = data["Subject"].fillna("")
data["Message"] = data["Message"].fillna("")

data["email_text"] = (
    data["Subject"] + " " + data["Message"]
)


# Clean text
def clean_text(text):

    text = str(text).lower()

    text = re.sub(
        r"http\S+|www\S+",
        " URL ",
        text
    )

    text = re.sub(
        r"\S+@\S+",
        " EMAIL ",
        text
    )

    text = re.sub(
        r"<.*?>",
        " ",
        text
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# Clean emails
data["clean_text"] = data["email_text"].apply(
    clean_text
)


# Transform using saved vectorizer
X_validation = vectorizer.transform(
    data["clean_text"]
)


# Predict
predictions = model.predict(
    X_validation
)


# Actual labels
actual = data["Spam/Ham"]


# Accuracy
accuracy = accuracy_score(
    actual,
    predictions
)


print("\n===================================")
print("VALIDATION RESULTS")
print("===================================")

print("\nAccuracy:", accuracy)


print("\nClassification Report:")

print(
    classification_report(
        actual,
        predictions
    )
)


print("Confusion Matrix:")

print(
    confusion_matrix(
        actual,
        predictions
    )
)


# Show every prediction
print("\n===================================")
print("INDIVIDUAL PREDICTIONS")
print("===================================")

for i in range(len(data)):

    print(
        f"{i + 1}. Actual: {actual.iloc[i]:4} | "
        f"Predicted: {predictions[i]:4} | "
        f"Subject: {data['Subject'].iloc[i]}"
    )