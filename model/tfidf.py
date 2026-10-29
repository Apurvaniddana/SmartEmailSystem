import pandas as pd
import re
import os

from sklearn.feature_extraction.text import TfidfVectorizer


# Find the project folder
project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Create dataset path
dataset_path = os.path.join(
    project_folder,
    "dataset",
    "spam.csv"
)

# Read dataset
data = pd.read_csv(dataset_path)


# Function to clean email text
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# Clean the email text
data["clean_text"] = data["text"].apply(clean_text)


# Create TF-IDF vectorizer
vectorizer = TfidfVectorizer()

# Convert text into numerical features
X = vectorizer.fit_transform(data["clean_text"])


# Display results
print("TF-IDF Matrix Shape:")
print(X.shape)

print("\nWords learned by TF-IDF:")
print(vectorizer.get_feature_names_out())

print("\nTF-IDF Matrix:")
print(X.toarray())