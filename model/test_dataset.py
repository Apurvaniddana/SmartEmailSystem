import pandas as pd
import os

# Get the project folder
project_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Create the correct path to spam.csv
dataset_path = os.path.join(project_folder, "dataset", "spam.csv")

# Read the dataset
data = pd.read_csv(dataset_path)

# Display the dataset
print("Dataset:")
print(data)

# Display number of rows and columns
print("\nDataset Shape:")
print(data.shape)

# Count spam and ham emails
print("\nClass Distribution:")
print(data["label"].value_counts())