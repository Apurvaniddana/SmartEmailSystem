import pandas as pd
import re
import os

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer


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
data = pd.read_csv(dataset_path)

# Handle missing values
data["Subject"] = data["Subject"].fillna("")
data["Message"] = data["Message"].fillna("")


# Combine Subject + Message
data["email_text"] = (
    data["Subject"] + " " + data["Message"]
)


# Clean email text
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


data["clean_text"] = data["email_text"].apply(clean_text)


# Remove completely empty emails
data = data[data["clean_text"].str.len() > 0]


# Input and output
X = data["clean_text"]
y = data["Spam/Ham"]


# Split into training and testing data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print("Total emails:", len(data))
print("Training emails:", len(X_train))
print("Testing emails:", len(X_test))


# Create TF-IDF vectorizer
vectorizer = TfidfVectorizer(
    max_features=10000,
    stop_words="english"
)


# Learn vocabulary from training data
X_train_tfidf = vectorizer.fit_transform(X_train)

# Transform testing data using the same vocabulary
X_test_tfidf = vectorizer.transform(X_test)


print("\nTF-IDF Training Shape:")
print(X_train_tfidf.shape)

print("\nTF-IDF Testing Shape:")
print(X_test_tfidf.shape)

print("\nNumber of TF-IDF features:")
print(len(vectorizer.get_feature_names_out()))