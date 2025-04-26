from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from joblib import load
import numpy as np
import httpx

# Load environment variables
load_dotenv()

# Load trained health risk model with error handling
try:
    model = load("health_model.pkl")
    print("✅ Model loaded successfully")
except Exception as e:
    raise RuntimeError(f"Failed to load model: {str(e)}")

app = FastAPI()

# Service URLs with Docker compatibility
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5000")
VITAL_SERVICE_URL = os.getenv("VITAL_SERVICE_URL", "http://vital-service:5001")
SYMPTOM_SERVICE_URL = os.getenv("SYMPTOM_SERVICE_URL", "http://symptom-service:5002")

# Timeout settings (seconds)
REQUEST_TIMEOUT = 5

class RiskInput(BaseModel):
    userId: str

class RecommendationRequest(BaseModel):
    userId: str
    focusArea: Optional[str] = None

async def fetch_with_timeout(client: httpx.AsyncClient, url: str) -> Optional[Dict[str, Any]]:
    try:
        print(f"🔍 Fetching from {url}")
        response = await client.get(url, timeout=REQUEST_TIMEOUT)
        print(f"📥 Response from {url}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Data received: {data}")
            return data
        return None
    except httpx.RequestError as e:
        print(f"❌ Error fetching {url}: {str(e)}")
        return None

async def get_user(client: httpx.AsyncClient, user_id: str) -> Optional[Dict[str, Any]]:
    url = f"{USER_SERVICE_URL}/users/{user_id}"
    return await fetch_with_timeout(client, url)

async def get_latest_vitals(client: httpx.AsyncClient, user_id: str) -> Optional[Dict[str, Any]]:
    url = f"{VITAL_SERVICE_URL}/vitals/{user_id}"
    return await fetch_with_timeout(client, url)

async def get_latest_symptoms(client: httpx.AsyncClient, user_id: str) -> Optional[Dict[str, Any]]:
    url = f"{SYMPTOM_SERVICE_URL}/symptoms/{user_id}"
    return await fetch_with_timeout(client, url)

@app.post("/predict-risk")
async def predict_risk(data: RiskInput):
    user_id = data.userId
    print(f"\n🔧 Using services:\n- User: {USER_SERVICE_URL}\n- Vital: {VITAL_SERVICE_URL}\n- Symptom: {SYMPTOM_SERVICE_URL}")

    async with httpx.AsyncClient() as client:
        user, vitals, symptoms = await asyncio.gather(
            get_user(client, user_id),
            get_latest_vitals(client, user_id),
            get_latest_symptoms(client, user_id)
        )

    print(f"User: {user}, Vitals: {vitals}, Symptoms: {symptoms}")

    if not user:
        raise HTTPException(status_code=404, detail="User not found or missing age")
    if not vitals or not vitals.get('data'):
        raise HTTPException(status_code=404, detail="Vitals not found")
    if not symptoms:
        raise HTTPException(status_code=404, detail="Symptoms not found")

    try:
        # Get the most recent vitals data based on 'recorded_at' field
        latest_vital = sorted(vitals['data'], key=lambda x: x['recorded_at'], reverse=True)[0]

        age = int(user['patient']['age'])
        avg_systolic_bp = float(latest_vital.get('systolic_bp', 120))
        avg_diastolic_bp = float(latest_vital.get('diastolic_bp', 80))
        avg_heart_rate = float(latest_vital.get('heart_rate', 70))
        avg_blood_glucose = float(latest_vital.get('blood_glucose', 90))
        avg_temperature = float(latest_vital.get('temperature', 37.0))

        symptom_values = [float(v) for v in symptoms.values() if isinstance(v, (int, float))]
        avg_symptom_severity = sum(symptom_values) / len(symptom_values) if symptom_values else 0

        # Prepare input in required order
        features = np.array([[age, avg_systolic_bp, avg_diastolic_bp, avg_heart_rate,
                              avg_blood_glucose, avg_temperature, avg_symptom_severity]])

        risk_level = model.predict(features)[0]
        risk_score = min(100, (
            0.15 * age +
            0.2 * max(0, avg_systolic_bp - 120) +
            0.1 * max(0, avg_diastolic_bp - 80) +
            0.1 * max(0, avg_heart_rate - 70) +
            0.15 * max(0, avg_blood_glucose - 100) +
            0.1 * abs(avg_temperature - 37) * 10 +
            0.2 * avg_symptom_severity * 10
        ))

        return {
            "user_id": user_id,
            "risk_level": risk_level,
            "risk_score": round(risk_score, 1),
            "features_used": {
                "age": age,
                "avg_systolic_bp": avg_systolic_bp,
                "avg_diastolic_bp": avg_diastolic_bp,
                "avg_heart_rate": avg_heart_rate,
                "avg_blood_glucose": avg_blood_glucose,
                "avg_temperature": avg_temperature,
                "avg_symptom_severity": round(avg_symptom_severity, 2)
            },
            "data_sources": {
                "user_service": USER_SERVICE_URL,
                "vital_service": VITAL_SERVICE_URL,
                "symptom_service": SYMPTOM_SERVICE_URL
            }
        }

    except Exception as e:
        print(f"❌ Error in prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str, focus_area: Optional[str] = None):
    try:
        risk_result = await predict_risk(RiskInput(userId=user_id))
        risk_level = risk_result["risk_level"]
        risk_score = risk_result["risk_score"]

        recommendations = [
            "💧 Drink at least 2L of water daily",
            "🛌 Maintain 7-9 hours of quality sleep",
            "🚭 Avoid tobacco and limit alcohol"
        ]

        if risk_level == "High":
            recommendations += [
                "🚨 Schedule a doctor consultation ASAP",
                "📅 Weekly health monitoring recommended",
                "🍎 Reduce sodium intake to <1500mg/day"
            ]
        elif risk_level == "Medium":
            recommendations += [
                "🍎 Adopt Mediterranean diet principles",
                "🏋️‍♂️ 150 mins moderate exercise weekly",
                "🧂 Limit salt intake to 1 tsp/day"
            ]
        else:
            recommendations += [
                "🥗 Maintain balanced nutrition",
                "🚶‍♂️ 30 minute daily walks",
                "🧘‍♀️ Practice stress management"
            ]

        if focus_area:
            focus = focus_area.lower()
            if focus == "diet":
                recommendations += [
                    "🥦 Increase vegetable intake to 5 servings/day",
                    "🍞 Choose whole grains over refined carbs"
                ]
                if risk_level in ["Medium", "High"]:
                    recommendations.append("🧈 Reduce saturated fats to <10% of calories")
            elif focus == "exercise":
                recommendations += [
                    "🏃‍♂️ Include both cardio and strength training",
                    "🧘‍♀️ Add flexibility exercises 2x/week"
                ]
                if risk_level == "High":
                    recommendations.append("❤️ Start with supervised cardiac rehab if needed")
            elif focus == "stress":
                recommendations.append("🧠 Practice mindfulness 10 mins daily")
                if risk_level in ["Medium", "High"]:
                    recommendations.append("📝 Keep a stress journal to identify triggers")

        return {
            "success": True,
            "user_id": user_id,
            "risk_level": risk_level,
            "risk_score": f"{risk_score}%",
            "recommendations": recommendations
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup():
    print("✅ Health Advisor Service Ready")
    print(f"🔗 User Service: {USER_SERVICE_URL}")
    print(f"💓 Vital Service: {VITAL_SERVICE_URL}")
    print(f"🤒 Symptom Service: {SYMPTOM_SERVICE_URL}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)
