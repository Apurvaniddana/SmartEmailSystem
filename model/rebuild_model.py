import os
import pickle

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATASET = os.path.join(
    BASE_DIR,
    "dataset",
    "spam.csv"
)

SAVE_DIR = os.path.join(
    BASE_DIR,
    "saved_model"
)

MODEL_FILE = os.path.join(
    SAVE_DIR,
    "improved_linear_svc.pkl"
)

VECTORIZER_FILE = os.path.join(
    SAVE_DIR,
    "improved_tfidf_vectorizer.pkl"
)


# ============================================================
# LOAD DATASET
# ============================================================

print("Loading dataset...")

data = pd.read_csv(DATASET)

print("Dataset shape:", data.shape)

print("Columns:", data.columns.tolist())


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

if "text" not in data.columns or "label" not in data.columns:

    print("\nERROR: Dataset must contain:")
    print("text")
    print("label")

    raise SystemExit


# Remove missing values

data["text"] = data["text"].fillna("")
data["label"] = data["label"].fillna("")


# Remove empty emails

data = data[
    data["text"].str.strip() != ""
]


print(
    "\nSpam/Ham distribution:"
)

print(
    data["label"].value_counts()
)


# ============================================================
# INPUT AND OUTPUT
# ============================================================

X = data["text"].astype(str)

y = data["label"].astype(str)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.20,

    random_state=42,

    stratify=y
)


print(
    "\nTraining samples:",
    len(X_train)
)

print(
    "Testing samples:",
    len(X_test)
)


# ============================================================
# TF-IDF
# ============================================================

print(
    "\nCreating TF-IDF features..."
)

vectorizer = TfidfVectorizer(

    max_features=30000,

    ngram_range=(1, 2),

    sublinear_tf=True,

    min_df=1,

    max_df=0.95
)


X_train_tfidf = vectorizer.fit_transform(
    X_train
)

X_test_tfidf = vectorizer.transform(
    X_test
)


print(
    "Training TF-IDF shape:",
    X_train_tfidf.shape
)

print(
    "Testing TF-IDF shape:",
    X_test_tfidf.shape
)


# ============================================================
# TRAIN LINEAR SVC
# ============================================================

print(
    "\nTraining LinearSVC..."
)

model = LinearSVC(
    C=1.0
)


model.fit(
    X_train_tfidf,
    y_train
)


print(
    "Training completed!"
)


# ============================================================
# EVALUATION
# ============================================================

predictions = model.predict(
    X_test_tfidf
)


accuracy = accuracy_score(
    y_test,
    predictions
)


print(
    "\n==================================="
)

print(
    "MODEL PERFORMANCE"
)

print(
    "==================================="
)


print(
    "\nAccuracy:",
    accuracy
)


print(
    "\nClassification Report:"
)

print(
    classification_report(
        y_test,
        predictions
    )
)


print(
    "Confusion Matrix:"
)

print(
    confusion_matrix(
        y_test,
        predictions
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

os.makedirs(
    SAVE_DIR,
    exist_ok=True
)


print(
    "\nSaving model..."
)


with open(
    MODEL_FILE,
    "wb"
) as file:

    pickle.dump(
        model,
        file,
        protocol=pickle.HIGHEST_PROTOCOL
    )


print(
    "Model saved:"
)

print(
    MODEL_FILE
)


print(
    "\nSaving vectorizer..."
)


with open(
    VECTORIZER_FILE,
    "wb"
) as file:

    pickle.dump(
        vectorizer,
        file,
        protocol=pickle.HIGHEST_PROTOCOL
    )


print(
    "Vectorizer saved:"
)

print(
    VECTORIZER_FILE
)


print(
    "\n==================================="
)

print(
    "MODEL REBUILT SUCCESSFULLY"
)

print(
    "==================================="
)