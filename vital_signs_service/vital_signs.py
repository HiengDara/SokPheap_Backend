from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error, pooling
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional

# 🚀 Initialize App
app = FastAPI()

# 🔌 Load Config
load_dotenv()

# ========================
# 🛠️ Database Setup
# ========================

# MySQL Connection Pool
db_pool = pooling.MySQLConnectionPool(
    pool_name="vital_pool",
    pool_size=5,
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "vitals"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    port=int(os.getenv("DB_PORT", 3306))
)

def get_db():
    """Get MySQL connection from pool"""
    try:
        conn = db_pool.get_connection()
        yield conn
    finally:
        if conn.is_connected():
            conn.close()

# ========================
# 📦 Data Models
# ========================

class VitalSigns(BaseModel):
    user_id: str
    systolic_bp: int
    diastolic_bp: int
    heart_rate: int
    blood_glucose: Optional[float] = None
    temperature: Optional[float] = None

# ========================
# 🔒 User Verification
# ========================

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5000")

async def verify_user(user_id: str):
    """Verify user exists in MongoDB"""
    try:
        response = requests.get(
            f"{USER_SERVICE_URL}/users/{user_id}",
            timeout=2  # Fail fast
        )
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"⚠️ User verification error: {e}")
        return False

# ========================
# 🚪 API Endpoints
# ========================

@app.post("/vitals")
async def create_vitals(vital: VitalSigns, conn = Depends(get_db)):
    # 1. Validate user
    if not await verify_user(vital.user_id):
        raise HTTPException(
            status_code=404,
            detail="User not found in MongoDB"
        )

    # 2. Insert into PostgreSQL
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            INSERT INTO vital_signs 
            (user_id, systolic_bp, diastolic_bp, heart_rate, 
             blood_glucose, temperature)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            vital.user_id,
            vital.systolic_bp,
            vital.diastolic_bp,
            vital.heart_rate,
            vital.blood_glucose,
            vital.temperature
        ))
        conn.commit()

        # Return created record
        cursor.execute("SELECT * FROM vital_signs WHERE id = LAST_INSERT_ID()")
        return {
            "message": "Vitals recorded",
            "data": cursor.fetchone()
        }
    except Error as e:
        conn.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()

@app.get("/vitals/{user_id}")
async def get_vitals(user_id: str, conn = Depends(get_db)):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM vital_signs 
            WHERE user_id = %s 
            ORDER BY recorded_at DESC
        """, (user_id,))
        
        results = cursor.fetchall()
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No vitals found for this user"
            )
            
        return {"data": results}
    except Error as e:
        raise HTTPException(
            status_code=500,
            detail="Database query failed"
        )
    finally:
        cursor.close()

@app.put("/vitals/{record_id}")
async def update_vitals(
    record_id: int, 
    vital: VitalSigns, 
    conn = Depends(get_db)
):
    cursor = conn.cursor(dictionary=True)
    try:
        # Verify the record exists
        cursor.execute("""
            UPDATE vital_signs SET
                systolic_bp = %s,
                diastolic_bp = %s,
                heart_rate = %s,
                blood_glucose = %s,
                temperature = %s
            WHERE id = %s
        """, (
            vital.systolic_bp,
            vital.diastolic_bp,
            vital.heart_rate,
            vital.blood_glucose,
            vital.temperature,
            record_id
        ))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Vital record not found"
            )

        # Return updated record
        cursor.execute("SELECT * FROM vital_signs WHERE id = %s", (record_id,))
        return {
            "message": "Vitals updated",
            "data": cursor.fetchone()
        }
    except Error as e:
        conn.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Update failed: {e}"
        )
    finally:
        cursor.close()

# ========================
# 🏁 Startup
# ========================

@app.on_event("startup")
async def startup():
    print("✅ Connected to MySQL pool")
    print(f"🔗 User Service: {USER_SERVICE_URL}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)