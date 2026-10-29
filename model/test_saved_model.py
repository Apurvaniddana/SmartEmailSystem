import os
import re
import joblib

# Find project folder
project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Model paths
model_path = os.path.join(
    project_folder,
    "saved_model",
    "random_forest_model.pkl"
)

vectorizer_path = os.path.join(
    project_folder,
    "saved_model",
    "tfidf_vectorizer.pkl"
)

# Load saved model and vectorizer
model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)

print("Model loaded successfully!")
print("Vectorizer loaded successfully!")


# Function to clean email
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


# Test email
email = """
Congratulations! You have won $1,000,000.
Click here to claim your prize immediately.
"""


# Clean email
cleaned_email = clean_text(email)


# Convert email to TF-IDF
email_tfidf = vectorizer.transform(
    [cleaned_email]
)


# Predict
prediction = model.predict(
    email_tfidf
)


print("\nEmail:")
print(email)

print("\nPrediction:")
print(prediction[0])