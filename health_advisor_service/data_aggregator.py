import pymongo
import mysql.connector
import pandas as pd
from collections import defaultdict
import os
from dotenv import load_dotenv
from bson import ObjectId  # Import ObjectId to handle MongoDB ObjectIds

# Load environment variables
load_dotenv()

# MongoDB Connection
mongo_client = pymongo.MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client["SokPheap"]  # Database name is "SokPheap"
patients_col = mongo_db["patients"]
symptoms_col = mongo_db["symptoms"]

# MySQL Connection
mysql_conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=int(os.getenv("DB_PORT"))
)
mysql_cursor = mysql_conn.cursor(dictionary=True)

# Fetch patients and assign `ObjectId` as `userId`
patients = list(patients_col.find({}, {"_id": 1, "firstName": 1, "lastName": 1, "age": 1, "gender": 1, "contact": 1, "address": 1, "isActive": 1, "createdAt": 1, "updatedAt": 1}))
patients_df = pd.DataFrame(patients)

# Convert ObjectId to string so it can be used as userId
patients_df["userId"] = patients_df["_id"].apply(str)
patients_df.drop(columns=["_id"], inplace=True)  # Drop the _id field after using it

# Fetch symptoms and aggregate
symptoms = list(symptoms_col.find({}, {"_id": 0}))
symptom_agg = defaultdict(lambda: {
    "avg_symptom_severity": 0,
    "chronic_symptom_count": 0,
    "acute_symptom_count": 0,
    "recurring_symptom_count": 0,
    "symptom_count": 0
})

for s in symptoms:
    user_id = str(s["userId"])  # Ensure the userId is in string format (same as in patients_df)
    symptom_agg[user_id]["avg_symptom_severity"] += s["severity"]
    symptom_agg[user_id]["symptom_count"] += 1
    duration = s.get("duration", "acute")
    symptom_agg[user_id][f"{duration}_symptom_count"] += 1

# Finalize averages
for user_id in symptom_agg:
    if symptom_agg[user_id]["symptom_count"] > 0:
        symptom_agg[user_id]["avg_symptom_severity"] /= symptom_agg[user_id]["symptom_count"]

symptom_df = pd.DataFrame.from_dict(symptom_agg, orient='index').reset_index().rename(columns={"index": "userId"})

# Fetch vitals from MySQL
mysql_cursor.execute(""" 
    SELECT 
        user_id,
        AVG(systolic_bp) AS avg_systolic_bp,
        AVG(diastolic_bp) AS avg_diastolic_bp,
        AVG(heart_rate) AS avg_heart_rate,
        AVG(blood_glucose) AS avg_blood_glucose,
        AVG(temperature) AS avg_temperature
    FROM vital_signs
    GROUP BY user_id
""")
vitals = mysql_cursor.fetchall()
vitals_df = pd.DataFrame(vitals).rename(columns={"user_id": "userId"})

# Print column names to ensure the merge keys match
print("Patients DataFrame Columns:")
print(patients_df.columns)

print("\nSymptom DataFrame Columns:")
print(symptom_df.columns)

print("\nVitals DataFrame Columns:")
print(vitals_df.columns)

# Merge all data into a single DataFrame
df = patients_df.merge(symptom_df, on="userId", how="left").merge(vitals_df, on="userId", how="left")

# One-hot encode gender
df["gender_male"] = (df["gender"] == "male").astype(int)
df["gender_female"] = (df["gender"] == "female").astype(int)

# Output to CSV
df.to_csv("aggregated_health_data.csv", index=False)
print("✅ Aggregated data saved to aggregated_health_data.csv")

# Optional: print preview of the DataFrame
print(df.head())
