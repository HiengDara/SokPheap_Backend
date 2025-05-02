import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Load your dataset
df = pd.read_csv("aggregated_health_data.csv")

# ======== STEP 1: Clean & Prepare Data ========
default_values = {
    'age': 30,
    'avg_systolic_bp': 120,
    'avg_diastolic_bp': 80,
    'avg_heart_rate': 75,
    'avg_blood_glucose': 100,
    'avg_temperature': 37.0,
    'avg_symptom_severity': 0
}

for col, val in default_values.items():
    if col not in df.columns:
        print(f"⚠️ Missing column: {col}. Creating with default value {val}")
        df[col] = val
    else:
        df[col] = df[col].fillna(val)

# ======== STEP 2: Generate Risk Score ========
df['risk_score'] = (
    0.2 * df['age'] +
    0.25 * (df['avg_systolic_bp'] - 120).clip(lower=0) +
    0.25 * (df['avg_diastolic_bp'] - 80).clip(lower=0) +
    0.1 * (df['avg_heart_rate'] - 100).clip(lower=0) +
    0.1 * (df['avg_blood_glucose'] - 140).clip(lower=0) +
    0.1 * (df['avg_temperature'] - 37).clip(lower=0) +
    0.2 * df['avg_symptom_severity'] * 10
).clip(upper=100)

# ======== STEP 3: Create Risk Level Labels ========
df['risk_level'] = pd.cut(df['risk_score'],
                          bins=[-1, 50, 70, 100],
                          labels=["Low", "Medium", "High"])

# ======== STEP 4: Select Features and Target ========
X = df[['age', 'avg_systolic_bp', 'avg_diastolic_bp', 'avg_heart_rate',
        'avg_blood_glucose', 'avg_temperature', 'avg_symptom_severity']]
y = df['risk_level']

# ======== STEP 5: Split the Data ========
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ======== STEP 6: Train the Model ========
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# ======== STEP 7: Evaluate the Model ========
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"✅ Model Accuracy: {accuracy * 100:.2f}%")
print("📊 Classification Report:\n", classification_report(y_test, y_pred))

# ======== STEP 8: Save the Model ========
joblib.dump(model, "model.joblib")
print("💾 Model saved as model.joblib")
