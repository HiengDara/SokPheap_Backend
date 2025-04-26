import pandas as pd

# Load the CSV file
df = pd.read_csv("aggregated_health_data.csv")

# View the first few rows of the dataset
print(df.head())

# Example: Perform basic analysis or preprocessing
print("Summary Statistics:")
print(df.describe())

# Example: Check for missing values
print("Missing Values:")
print(df.isnull().sum())

# Example: Any other analysis or manipulation can be added here
