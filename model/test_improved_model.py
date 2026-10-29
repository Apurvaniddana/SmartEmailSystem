import os
import re
import joblib


# Find project folder
project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# Load improved model
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


print("Improved model loaded successfully!")
print("Improved vectorizer loaded successfully!")


# Cleaning function
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


# New test emails
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


# Test each email
for i, email in enumerate(test_emails, 1):

    cleaned_email = clean_text(email)

    email_tfidf = vectorizer.transform(
        [cleaned_email]
    )

    prediction = model.predict(
        email_tfidf
    )

    print("\nEmail", i)
    print("-----------------------------")
    print(email.strip())
    print("\nPrediction:", prediction[0])