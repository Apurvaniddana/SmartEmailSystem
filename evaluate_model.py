import os
import pickle

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "saved_model",
    "improved_linear_svc.pkl"
)

VECTORIZER_FILE = os.path.join(
    BASE_DIR,
    "saved_model",
    "improved_tfidf_vectorizer.pkl"
)


# ============================================================
# CHECK MODEL FILES
# ============================================================

print("===================================")
print("MODEL EVALUATION")
print("===================================")

print()
print("Checking model files...")

if not os.path.exists(MODEL_FILE):

    print("ERROR: Model file not found:")
    print(MODEL_FILE)
    exit()

print("Model file found.")


if not os.path.exists(VECTORIZER_FILE):

    print("ERROR: Vectorizer file not found:")
    print(VECTORIZER_FILE)
    exit()

print("Vectorizer file found.")


# ============================================================
# LOAD MODEL
# ============================================================

print()
print("Loading ML model...")

with open(MODEL_FILE, "rb") as f:

    model = pickle.load(f)

print("Model loaded.")


# ============================================================
# LOAD VECTORIZER
# ============================================================

print("Loading TF-IDF vectorizer...")

with open(VECTORIZER_FILE, "rb") as f:

    vectorizer = pickle.load(f)

print("Vectorizer loaded.")


# ============================================================
# TEST DATA
# ============================================================

test_emails = [

    (
        "Congratulations! You have won a free prize. "
        "Click here to claim your money now!",
        "SPAM"
    ),

    (
        "URGENT! Your account has been suspended. "
        "Verify your password immediately.",
        "SPAM"
    ),

    (
        "You have won $10000. Claim your prize now!",
        "SPAM"
    ),

    (
        "Reminder: Call for Paper at NIT Rourkela.",
        "HAM"
    ),

    (
        "Your LinkedIn profile is getting hits.",
        "HAM"
    ),

    (
        "Welcome to Emertxe Internship 2026 "
        "Kickoff Meeting Today.",
        "HAM"
    ),

    (
        "New openings based on your profile!",
        "HAM"
    ),

    (
        "Introducing Napkin Slides.",
        "HAM"
    ),

    (
        "Fast-track your career and win exciting prizes!",
        "SPAM"
    ),

    (
        "YouTube live session about an internship.",
        "HAM"
    )

]


# ============================================================
# SEPARATE TEXT AND LABELS
# ============================================================

texts = []

actual_labels = []


for text, label in test_emails:

    texts.append(text)

    actual_labels.append(label)


# ============================================================
# TF-IDF
# ============================================================

print()
print("Converting test emails using TF-IDF...")

features = vectorizer.transform(
    texts
)


# ============================================================
# PREDICTION
# ============================================================

print("Running model predictions...")

predicted_labels = model.predict(
    features
)


# ============================================================
# INDIVIDUAL RESULTS
# ============================================================

print()
print("===================================")
print("TEST RESULTS")
print("===================================")


correct_count = 0
incorrect_count = 0


for i in range(len(test_emails)):

    text = test_emails[i][0]

    actual = actual_labels[i]

    predicted = str(
        predicted_labels[i]
    ).upper()


    print()
    print(
        f"Test Email {i + 1}"
    )

    print(
        f"Text       : {text}"
    )

    print(
        f"Actual     : {actual}"
    )

    print(
        f"Predicted  : {predicted}"
    )


    if actual == predicted:

        print(
            "Result     : CORRECT"
        )

        correct_count += 1

    else:

        print(
            "Result     : INCORRECT"
        )

        incorrect_count += 1


# ============================================================
# CONVERT LABELS TO BINARY
#
# HAM  = 0
# SPAM = 1
# ============================================================

actual_binary = []

predicted_binary = []


for label in actual_labels:

    if label == "SPAM":

        actual_binary.append(1)

    else:

        actual_binary.append(0)


for label in predicted_labels:

    if str(label).upper() == "SPAM":

        predicted_binary.append(1)

    else:

        predicted_binary.append(0)


# ============================================================
# ACCURACY
# ============================================================

accuracy = accuracy_score(
    actual_binary,
    predicted_binary
)


# ============================================================
# PRECISION
# ============================================================

precision = precision_score(
    actual_binary,
    predicted_binary,
    zero_division=0
)


# ============================================================
# RECALL
# ============================================================

recall = recall_score(
    actual_binary,
    predicted_binary,
    zero_division=0
)


# ============================================================
# F1 SCORE
# ============================================================

f1 = f1_score(
    actual_binary,
    predicted_binary,
    zero_division=0
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    actual_binary,
    predicted_binary,
    labels=[0, 1]
)


# ============================================================
# MODEL EVALUATION RESULTS
# ============================================================

print()
print("===================================")
print("MODEL EVALUATION RESULTS")
print("===================================")

print(
    f"Correct Predictions   : {correct_count}"
)

print(
    f"Incorrect Predictions : {incorrect_count}"
)

print(
    f"Accuracy              : {accuracy * 100:.2f}%"
)

print(
    f"Precision             : {precision * 100:.2f}%"
)

print(
    f"Recall                : {recall * 100:.2f}%"
)

print(
    f"F1-Score              : {f1 * 100:.2f}%"
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print()
print("===================================")
print("CONFUSION MATRIX")
print("===================================")

print()
print("                    Predicted")
print("                    HAM    SPAM")

print(
    f"Actual HAM          {cm[0][0]:3d}    {cm[0][1]:3d}"
)

print(
    f"Actual SPAM         {cm[1][0]:3d}    {cm[1][1]:3d}"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print()
print("===================================")
print("CLASSIFICATION REPORT")
print("===================================")


print(
    classification_report(
        actual_binary,
        predicted_binary,
        target_names=[
            "HAM",
            "SPAM"
        ],
        zero_division=0
    )
)


# ============================================================
# INTERPRETATION
# ============================================================

print("===================================")
print("INTERPRETATION")
print("===================================")

print()
print(
    "HAM = Legitimate email"
)

print(
    "SPAM = Unwanted / suspicious email"
)

print()
print(
    "False Positive = Legitimate email classified as SPAM"
)

print(
    "False Negative = Spam email classified as HAM"
)

print()
print(
    "Evaluation completed successfully."
)

print("===================================")