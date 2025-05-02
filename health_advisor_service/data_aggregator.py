import pymongo
import pandas as pd
from collections import defaultdict
import os
from dotenv import load_dotenv
from bson import ObjectId

# Load environment variables
load_dotenv()

# MongoDB Connection
mongo_client = pymongo.MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client["SokPheap"]
patients_col = mongo_db["patients"]
symptoms_col = mongo_db["symptoms"]
vitals_col = mongo_db["vitalsigns"]

# Fetch patients
patients = list(patients_col.find({}, {
    "_id": 1, "firstName": 1, "lastName": 1, "age": 1,
    "gender": 1, "contact": 1, "address": 1, "isActive": 1,
    "createdAt": 1, "updatedAt": 1
}))
patients_df = pd.DataFrame(patients)
patients_df["userId"] = patients_df["_id"].apply(str)
patients_df.drop(columns=["_id"], inplace=True)

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
    user_id = str(s["userId"])
    symptom_agg[user_id]["avg_symptom_severity"] += s["severity"]
    symptom_agg[user_id]["symptom_count"] += 1
    duration = s.get("duration", "acute")
    symptom_agg[user_id][f"{duration}_symptom_count"] += 1

for user_id in symptom_agg:
    if symptom_agg[user_id]["symptom_count"] > 0:
        symptom_agg[user_id]["avg_symptom_severity"] /= symptom_agg[user_id]["symptom_count"]

symptom_df = pd.DataFrame.from_dict(symptom_agg, orient='index').reset_index().rename(columns={"index": "userId"})

# Fetch vitals and fix column naming issue
vitals = list(vitals_col.find({}, {"_id": 0}))
vitals_df_raw = pd.DataFrame(vitals)

# Check and rename user_id to userId for consistency
if "user_id" in vitals_df_raw.columns:
    vitals_df_raw["userId"] = vitals_df_raw["user_id"].apply(str)
else:
    raise KeyError("Missing 'user_id' field in vitals collection")

# Aggregate vitals
vitals_df = vitals_df_raw.groupby("userId").agg({
    "systolic_bp": "mean",
    "diastolic_bp": "mean",
    "heart_rate": "mean",
    "blood_glucose": "mean",
    "temperature": "mean"
}).reset_index()

# Rename columns
vitals_df = vitals_df.rename(columns={
    "systolic_bp": "avg_systolic_bp",
    "diastolic_bp": "avg_diastolic_bp",
    "heart_rate": "avg_heart_rate",
    "blood_glucose": "avg_blood_glucose",
    "temperature": "avg_temperature"
})

# Debugging info
print("Patients DataFrame Columns:")
print(patients_df.columns)

print("\nSymptom DataFrame Columns:")
print(symptom_df.columns)

print("\nVitals DataFrame Columns:")
print(vitals_df.columns)

# Merge all data
df = patients_df.merge(symptom_df, on="userId", how="left").merge(vitals_df, on="userId", how="left")

# One-hot encode gender
df["gender_male"] = (df["gender"] == "male").astype(int)
df["gender_female"] = (df["gender"] == "female").astype(int)

# Save to CSV
df.to_csv("aggregated_health_data.csv", index=False)
print("✅ Aggregated data saved to aggregated_health_data.csv")

# Preview
print(df.head())
