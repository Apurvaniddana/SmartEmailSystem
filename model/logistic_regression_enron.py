import pandas as pd
import re
import os

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)


# Find project folder
project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Dataset path
dataset_path = os.path.join(
    project_folder,
    "dataset",
    "enron_spam_data.csv"
)

# Load dataset
data = pd.read_csv(dataset_path)

# Handle missing values
data["Subject"] = data["Subject"].fillna("")
data["Message"] = data["Message"].fillna("")

# Combine Subject + Message
data["email_text"] = (
    data["Subject"] + " " + data["Message"]
)


# Clean text
def clean_text(text):
    text = str(text).lower()

    text = re.sub(
        r"http\S+|www\S+",
        " ",
        text
    )

    text = re.sub(
        r"\S+@\S+",
        " ",
        text
    )

    text = re.sub(
        r"<.*?>",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


data["clean_text"] = data["email_text"].apply(clean_text)

# Remove empty emails
data = data[data["clean_text"].str.len() > 0]


# Input and output
X = data["clean_text"]
y = data["Spam/Ham"]


# Train/Test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# TF-IDF
vectorizer = TfidfVectorizer(
    max_features=10000,
    stop_words="english"
)

X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)


# Create Logistic Regression model
model = LogisticRegression(
    max_iter=1000
)


# Train model
print("Training Logistic Regression model...")

model.fit(
    X_train_tfidf,
    y_train
)


# Predict
y_pred = model.predict(X_test_tfidf)


# Metrics
accuracy = accuracy_score(
    y_test,
    y_pred
)

precision = precision_score(
    y_test,
    y_pred,
    pos_label="spam"
)

recall = recall_score(
    y_test,
    y_pred,
    pos_label="spam"
)

f1 = f1_score(
    y_test,
    y_pred,
    pos_label="spam"
)


# Display results
print("\n===================================")
print("LOGISTIC REGRESSION SPAM CLASSIFIER")
print("===================================")

print("\nAccuracy :", accuracy)
print("Precision:", precision)
print("Recall   :", recall)
print("F1-Score :", f1)


# Classification report
print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred
    )
)


# Confusion matrix
print("Confusion Matrix:")
print(
    confusion_matrix(
        y_test,
        y_pred
    )
)