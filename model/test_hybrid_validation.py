import pandas as pd
import os
import re
import joblib

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# =========================================================
# 1. PROJECT FOLDER
# =========================================================

project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# =========================================================
# 2. FILE PATHS
# =========================================================

dataset_path = os.path.join(
    project_folder,
    "dataset",
    "validation_emails.csv"
)

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


# =========================================================
# 3. LOAD DATASET
# =========================================================

print("Loading validation dataset...")

data = pd.read_csv(dataset_path)

print("Validation dataset loaded!")
print("Total emails:", len(data))


# =========================================================
# 4. LOAD MODEL AND VECTORIZER
# =========================================================

print("\nLoading ML model...")

model = joblib.load(model_path)

vectorizer = joblib.load(vectorizer_path)

print("ML model loaded successfully!")
print("TF-IDF vectorizer loaded successfully!")


# =========================================================
# 5. HANDLE MISSING VALUES
# =========================================================

data["Subject"] = data["Subject"].fillna("")
data["Message"] = data["Message"].fillna("")


# =========================================================
# 6. COMBINE SUBJECT + MESSAGE
# =========================================================

data["email_text"] = (
    data["Subject"] + " " + data["Message"]
)


# =========================================================
# 7. TEXT CLEANING FUNCTION
# =========================================================

def clean_text(text):

    text = str(text).lower()

    # Replace URLs
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


# =========================================================
# 8. STRONG SPAM INDICATORS
# =========================================================

strong_spam_patterns = {

    r"\bwon\b": 2,

    r"\bwinner\b": 2,

    r"\bprize\b": 2,

    r"\bfree gift\b": 2,

    r"\bclaim your\b": 2,

    r"\bclick here\b": 2,

    r"\bclick the link\b": 2,

    r"\bverify your account\b": 2,

    r"\baccount.*suspended\b": 2,

    r"\bearn money\b": 2,

    r"\bmake money\b": 2,

    r"\bmillion dollars\b": 2
}


# =========================================================
# 9. MEDIUM SPAM INDICATORS
# =========================================================

medium_spam_patterns = {

    r"\breward\b": 1,

    r"\bclaim\b": 1,

    r"\burgent\b": 1,

    r"\blimited time\b": 1,

    r"\bspecial offer\b": 1,

    r"\bexclusive offer\b": 1,

    r"\bbonus\b": 1,

    r"\bcongratulations\b": 1,

    r"\bselected.*reward\b": 1
}


# =========================================================
# 10. SPAM SCORE FUNCTION
# =========================================================

def calculate_spam_score(text):

    text = str(text).lower()

    score = 0

    # ---------------------------------------------
    # Strong indicators
    # ---------------------------------------------

    for pattern, weight in strong_spam_patterns.items():

        if re.search(pattern, text):

            score += weight


    # ---------------------------------------------
    # Medium indicators
    # ---------------------------------------------

    for pattern, weight in medium_spam_patterns.items():

        if re.search(pattern, text):

            score += weight


    # ---------------------------------------------
    # URL indicator
    # ---------------------------------------------

    if re.search(
        r"https?://|www\.",
        text
    ):

        score += 1


    # ---------------------------------------------
    # Excessive exclamation marks
    # ---------------------------------------------

    if text.count("!") >= 3:

        score += 1


    # ---------------------------------------------
    # Money indicator
    # ---------------------------------------------

    if re.search(
        r"\$\s?\d+|€\s?\d+|₹\s?\d+",
        text
    ):

        score += 1


    return score


# =========================================================
# 11. HYBRID PREDICTION FUNCTION
# =========================================================

def predict_email(email):

    # Clean email
    cleaned_email = clean_text(email)


    # ---------------------------------------------
    # ML prediction
    # ---------------------------------------------

    email_tfidf = vectorizer.transform(
        [cleaned_email]
    )

    ml_prediction = model.predict(
        email_tfidf
    )[0]


    # ---------------------------------------------
    # ML decision score
    # ---------------------------------------------

    ml_score = model.decision_function(
        email_tfidf
    )[0]


    # ---------------------------------------------
    # Rule-based score
    # ---------------------------------------------

    rule_score = calculate_spam_score(
        email
    )


    # ---------------------------------------------
    # Final decision
    # ---------------------------------------------

    if rule_score >= 2:

        final_prediction = "spam"

    elif ml_prediction == "spam":

        final_prediction = "spam"

    else:

        final_prediction = "ham"


    return (
        final_prediction,
        ml_prediction,
        ml_score,
        rule_score
    )


# =========================================================
# 12. RUN HYBRID DETECTION
# =========================================================

predictions = []

ml_predictions = []

rule_scores = []


print("\n===================================")
print("HYBRID SPAM DETECTION")
print("===================================")


for index, row in data.iterrows():

    email = row["email_text"]


    (
        final_prediction,
        ml_prediction,
        ml_score,
        rule_score
    ) = predict_email(email)


    predictions.append(
        final_prediction
    )

    ml_predictions.append(
        ml_prediction
    )

    rule_scores.append(
        rule_score
    )


# =========================================================
# 13. ACTUAL LABELS
# =========================================================

actual = data["Spam/Ham"]


# =========================================================
# 14. ACCURACY
# =========================================================

accuracy = accuracy_score(
    actual,
    predictions
)


# =========================================================
# 15. RESULTS
# =========================================================

print("\n===================================")
print("HYBRID VALIDATION RESULTS")
print("===================================")

print(
    "\nAccuracy:",
    accuracy
)


# =========================================================
# 16. CLASSIFICATION REPORT
# =========================================================

print("\nClassification Report:")

print(
    classification_report(
        actual,
        predictions,
        zero_division=0
    )
)


# =========================================================
# 17. CONFUSION MATRIX
# =========================================================

print("Confusion Matrix:")

print(
    confusion_matrix(
        actual,
        predictions
    )
)


# =========================================================
# 18. INDIVIDUAL PREDICTIONS
# =========================================================

print("\n===================================")
print("INDIVIDUAL PREDICTIONS")
print("===================================")


for i in range(len(data)):

    print(
        f"{i + 1}. "
        f"Actual: {actual.iloc[i]:4} | "
        f"ML: {ml_predictions[i]:4} | "
        f"Rule Score: {rule_scores[i]:2} | "
        f"Final: {predictions[i]:4} | "
        f"Subject: {data['Subject'].iloc[i]}"
    )