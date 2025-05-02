FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install scikit-learn==1.3.0


# Copy ALL files including the model
COPY . .

# Explicitly copy model to root directory
COPY model.joblib /app/model.joblib

EXPOSE 5003
CMD ["uvicorn", "health_advisor:app", "--host", "0.0.0.0", "--port", "5003"]