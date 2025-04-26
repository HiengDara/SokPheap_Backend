import pandas as pd

df = pd.read_csv("aggregated_health_data.csv")
print(df.columns.tolist())
