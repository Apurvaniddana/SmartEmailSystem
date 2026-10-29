import pandas as pd
import re
import os

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

print("Original dataset shape:")
print(data.shape)

print("\nOriginal Spam/Ham distribution:")
print(data["Spam/Ham"].value_counts())


# Remove unnecessary index column
data = data.drop(columns=["Unnamed: 0"])


# Handle missing values
data["Subject"] = data["Subject"].fillna("")
data["Message"] = data["Message"].fillna("")


# Combine Subject and Message
data["email_text"] = (
    data["Subject"] + " " + data["Message"]
)


# Clean email text
def clean_text(text):
    text = str(text)

    # Convert to lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", " ", text)

    # Remove email addresses
    text = re.sub(r"\S+@\S+", " ", text)

    # Remove HTML tags
    text = re.sub(r"<.*?>", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# Apply cleaning
data["clean_text"] = data["email_text"].apply(clean_text)


# Remove only rows where the cleaned email is completely empty
data = data[data["clean_text"].str.len() > 0]


print("\nAfter preprocessing:")
print(data.shape)

print("\nSpam/Ham distribution:")
print(data["Spam/Ham"].value_counts())


# Show an example
print("\nExample cleaned email:")
print(data["clean_text"].iloc[0][:500])