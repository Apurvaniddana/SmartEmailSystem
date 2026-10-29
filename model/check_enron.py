import pandas as pd
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

# Read the real dataset
data = pd.read_csv(dataset_path)

print("Dataset loaded successfully!")

print("\nDataset shape:")
print(data.shape)

print("\nColumns:")
print(data.columns.tolist())

print("\nFirst 5 emails:")
print(data.head())

print("\nSpam/Ham distribution:")
print(data["Spam/Ham"].value_counts())