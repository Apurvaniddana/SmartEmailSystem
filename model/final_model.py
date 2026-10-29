import pandas as pd
import re
import os
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier


# -------------------------------------------------
# 1. Find project folder
# -------------------------------------------------

project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# -------------------------------------------------
# 2. Dataset path
# -------------------------------------------------

dataset_path = os.path.join(
    project_folder,
    "dataset",
    "enron_spam_data.csv"
)


# -------------------------------------------------
# 3. Load dataset
# -------------------------------------------------

print("Loading dataset...")

data = pd.read_csv(dataset_path)

print("Dataset loaded:", data.shape)


# -------------------------------------------------
# 4. Handle missing values
# -------------------------------------------------

data["Subject"] = data["Subject"].fillna("")
data["Message"] = data["Message"].fillna("")


# -------------------------------------------------
# 5. Combine Subject + Message
# -------------------------------------------------

data["email_text"] = (
    data["Subject"] + " " + data["Message"]
)


# -------------------------------------------------
# 6. Clean email text
# -------------------------------------------------

def clean_text(text):

    text = str(text).lower()

    # Remove URLs
    text = re.sub(
        r"http\S+|www\S+",
        " ",
        text
    )

    # Remove email addresses
    text = re.sub(
        r"\S+@\S+",
        " ",
        text
    )

    # Remove HTML
    text = re.sub(
        r"<.*?>",
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


# -------------------------------------------------
# 7. Input and output
# -------------------------------------------------

X = data["clean_text"]
y = data["Spam/Ham"]


# -------------------------------------------------
# 8. Create TF-IDF
# -------------------------------------------------

print("Creating TF-IDF features...")

vectorizer = TfidfVectorizer(
    max_features=10000,
    stop_words="english"
)

X_tfidf = vectorizer.fit_transform(X)


print("TF-IDF shape:", X_tfidf.shape)


# -------------------------------------------------
# 9. Create final Random Forest model
# -------------------------------------------------

print("Training final Random Forest model...")

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)


# -------------------------------------------------
# 10. Train using complete dataset
# -------------------------------------------------

model.fit(
    X_tfidf,
    y
)


print("Model training completed!")


# -------------------------------------------------
# 11. Create model folder
# -------------------------------------------------

saved_model_folder = os.path.join(
    project_folder,
    "saved_model"
)

os.makedirs(
    saved_model_folder,
    exist_ok=True
)


# -------------------------------------------------
# 12. Save Random Forest model
# -------------------------------------------------

model_path = os.path.join(
    saved_model_folder,
    "random_forest_model.pkl"
)

joblib.dump(
    model,
    model_path
)


# -------------------------------------------------
# 13. Save TF-IDF vectorizer
# -------------------------------------------------

vectorizer_path = os.path.join(
    saved_model_folder,
    "tfidf_vectorizer.pkl"
)

joblib.dump(
    vectorizer,
    vectorizer_path
)


print("\n===================================")
print("FINAL MODEL SAVED SUCCESSFULLY")
print("===================================")

print("\nModel:")
print(model_path)

print("\nVectorizer:")
print(vectorizer_path)