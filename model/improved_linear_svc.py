import pandas as pd
import re
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
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
print("Loading dataset...")
data = pd.read_csv(dataset_path)

print("Dataset:", data.shape)


# Handle missing values
data["Subject"] = data["Subject"].fillna("")
data["Message"] = data["Message"].fillna("")


# Combine subject and message
data["email_text"] = (
    data["Subject"] + " " + data["Message"]
)


# Clean text
def clean_text(text):

    text = str(text).lower()

    # Replace URLs with a common token
    text = re.sub(
        r"http\S+|www\S+",
        " URL ",
        text
    )

    # Replace email addresses
    text = re.sub(
        r"\S+@\S+",
        " EMAIL ",
        text
    )

    # Remove HTML
    text = re.sub(
        r"<.*?>",
        " ",
        text
    )

    # Keep letters, numbers and spaces
    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    # Remove extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


data["clean_text"] = data["email_text"].apply(
    clean_text
)


# Remove empty emails
data = data[
    data["clean_text"].str.len() > 0
]


# Input and output
X = data["clean_text"]
y = data["Spam/Ham"]


# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# TF-IDF with word n-grams
print("Creating improved TF-IDF...")

vectorizer = TfidfVectorizer(
    max_features=30000,
    ngram_range=(1, 2),
    min_df=2,
    sublinear_tf=True,
    stop_words="english"
)


X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)


print(
    "Training TF-IDF shape:",
    X_train_tfidf.shape
)

print(
    "Testing TF-IDF shape:",
    X_test_tfidf.shape
)


# LinearSVC
print("\nTraining improved LinearSVC...")

model = LinearSVC(
    C=2.0,
    class_weight="balanced"
)

model.fit(
    X_train_tfidf,
    y_train
)


# Prediction
y_pred = model.predict(
    X_test_tfidf
)


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


print("\n===================================")
print("IMPROVED LINEARSVC")
print("===================================")

print("Accuracy :", accuracy)
print("Precision:", precision)
print("Recall   :", recall)
print("F1-Score :", f1)


print("\nClassification Report:")

print(
    classification_report(
        y_test,
        y_pred
    )
)


print("Confusion Matrix:")

print(
    confusion_matrix(
        y_test,
        y_pred
    )
)


# Save improved model
saved_model_folder = os.path.join(
    project_folder,
    "saved_model"
)

os.makedirs(
    saved_model_folder,
    exist_ok=True
)


model_path = os.path.join(
    saved_model_folder,
    "improved_linear_svc.pkl"
)

vectorizer_path = os.path.join(
    saved_model_folder,
    "improved_tfidf_vectorizer.pkl"
)


joblib.dump(
    model,
    model_path
)

joblib.dump(
    vectorizer,
    vectorizer_path
)


print("\n===================================")
print("IMPROVED MODEL SAVED")
print("===================================")

print("Model:")
print(model_path)

print("\nVectorizer:")
print(vectorizer_path)