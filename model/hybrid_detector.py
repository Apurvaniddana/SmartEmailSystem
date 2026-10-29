import os
import re
import joblib


# ============================================
# 1. Find project folder
# ============================================

project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# ============================================
# 2. Load ML model
# ============================================

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

model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)


print("ML model loaded successfully!")
print("TF-IDF vectorizer loaded successfully!")


# ============================================
# 3. Text cleaning
# ============================================

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


# ============================================
# 4. Spam indicators
# ============================================

spam_patterns = [

    r"\bwon\b",
    r"\bwinner\b",
    r"\bprize\b",
    r"\breward\b",
    r"\bfree gift\b",
    r"\bclaim\b",
    r"\bclaim your\b",
    r"\bclick here\b",
    r"\bclick the link\b",
    r"\bverify your account\b",
    r"\baccount.*suspended\b",
    r"\burgent\b",
    r"\blimited time\b",
    r"\bspecial offer\b",
    r"\bexclusive offer\b",
    r"\bearn money\b",
    r"\bmake money\b",
    r"\bbonus\b",
    r"\bcongratulations\b",
    r"\bselected.*reward\b",
    r"\b\d+%\s*discount\b",
    r"\bmillion dollars\b"
]


# ============================================
# 5. Calculate rule-based score
# ============================================

def calculate_spam_score(text):

    text = text.lower()

    score = 0
    matched_patterns = []

    for pattern in spam_patterns:

        if re.search(pattern, text):

            score += 1

            matched_patterns.append(pattern)

    # URL indicator
    if re.search(
        r"https?://|www\.",
        text
    ):
        score += 1
        matched_patterns.append("URL")

    # Excessive exclamation marks
    if text.count("!") >= 3:

        score += 1
        matched_patterns.append("excessive_exclamation")

    # Money amount
    if re.search(
        r"\$\s?\d+|€\s?\d+|₹\s?\d+",
        text
    ):

        score += 1
        matched_patterns.append("money_amount")

    return score, matched_patterns


# ============================================
# 6. Hybrid prediction
# ============================================

def predict_email(email):

    cleaned = clean_text(email)

    # ML prediction
    tfidf = vectorizer.transform(
        [cleaned]
    )

    ml_prediction = model.predict(
        tfidf
    )[0]

    # ML confidence score
    decision_score = model.decision_function(
        tfidf
    )[0]

    # Rule-based score
    rule_score, indicators = calculate_spam_score(
        email
    )

    # Final decision
    #
    # Strong rule evidence can override
    # the ML prediction for obvious spam.

    if rule_score >= 2:

        final_prediction = "spam"

    elif ml_prediction == "spam":

        final_prediction = "spam"

    else:

        final_prediction = "ham"

    return (
        final_prediction,
        ml_prediction,
        decision_score,
        rule_score,
        indicators
    )


# ============================================
# 7. Test emails
# ============================================

test_emails = [

    """
    Congratulations! You have won $1,000,000.
    Click here to claim your prize immediately.
    """,

    """
    Hi John,
    Can we meet tomorrow at 10 AM to discuss our project?
    Please bring the project report.
    """,

    """
    URGENT! Your bank account has been selected for a
    special reward. Click the link now to verify your account.
    """,

    """
    Dear Professor,
    I am submitting my assignment for review.
    Thank you.
    """
]


# ============================================
# 8. Test
# ============================================

print("\n===================================")
print("HYBRID SPAM DETECTOR")
print("===================================")


for i, email in enumerate(
    test_emails,
    1
):

    (
        final_prediction,
        ml_prediction,
        decision_score,
        rule_score,
        indicators
    ) = predict_email(email)

    print(
        f"\nEmail {i}"
    )

    print(
        "-----------------------------"
    )

    print(
        email.strip()
    )

    print(
        "\nML Prediction:",
        ml_prediction
    )

    print(
        "ML Decision Score:",
        round(
            decision_score,
            4
        )
    )

    print(
        "Rule Score:",
        rule_score
    )

    print(
        "Spam Indicators:",
        indicators
    )

    print(
        "FINAL PREDICTION:",
        final_prediction.upper()
    )