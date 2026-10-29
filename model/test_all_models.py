import os
import re
import joblib

# Find project folder
project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Model folder
saved_model_folder = os.path.join(
    project_folder,
    "saved_model"
)

# Load Random Forest
rf_model = joblib.load(
    os.path.join(
        saved_model_folder,
        "random_forest_model.pkl"
    )
)

# Load TF-IDF
vectorizer = joblib.load(
    os.path.join(
        saved_model_folder,
        "tfidf_vectorizer.pkl"
    )
)


# Clean email
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


# Test emails
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


print("===================================")
print("NEW EMAIL TEST")
print("===================================")


# Test each email
for i, email in enumerate(test_emails, start=1):

    cleaned_email = clean_text(email)

    email_tfidf = vectorizer.transform(
        [cleaned_email]
    )

    prediction = rf_model.predict(
        email_tfidf
    )

    print("\nEmail", i)
    print("-----------------------------")
    print(email.strip())
    print("\nPrediction:", prediction[0])