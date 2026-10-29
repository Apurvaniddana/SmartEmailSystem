import pandas as pd
import re
import os

# Find the main project folder
project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Build the correct dataset path
dataset_path = os.path.join(
    project_folder,
    "dataset",
    "spam.csv"
)

# Read the dataset
data = pd.read_csv(dataset_path)


# Function to clean email text
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# Apply cleaning
data["clean_text"] = data["text"].apply(clean_text)


# Display original and cleaned text
print("Original and Cleaned Emails:\n")

for i in range(len(data)):
    print("Original:", data["text"].iloc[i])
    print("Cleaned :", data["clean_text"].iloc[i])
    print("-" * 60)