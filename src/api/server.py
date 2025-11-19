from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import joblib
import os
from fastapi import HTTPException
from typing import Optional

app = FastAPI()

# Model will be loaded lazily to avoid import-time errors in CI (missing deps)
model_path = os.getenv(
    "MODEL_PATH",
    "src/models/artifacts/models/linear_regression_model.pkl"
)
model: Optional[object] = None


def load_model():
    global model
    if model is not None:
        return model
    try:
        print(f"🔧 Loading model from: {model_path}")
        model = joblib.load(model_path)
        print("✅ Model loaded successfully")
    except ImportError as ie:
        # missing optional dependency like 'dill'
        print(f"⚠️ Model load ImportError: {ie}")
        model = None
    except Exception as e:
        print(f"⚠️ Model load failed: {e}")
        model = None
    return model

# CORS (optional but fine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static dir: serve templates folder as /static
app.mount("/static", StaticFiles(directory="src/api/templates"), name="static")


class MeterFeatures(BaseModel):
    voltage: float
    temperature: float
    power_factor: float
    load_kw: float
    frequency_hz: float
    hour: int
    day_of_week: int
    is_weekend: int
    voltage_flag: int
    pf_issue: int
    high_temp: int
    load_intensity: float


@app.post("/predict")
def predict(features: MeterFeatures):
    import pandas as pd
    import numpy as np

    # Build a single-row DataFrame matching your training features
    df = pd.DataFrame([{
        "voltage": features.voltage,
        "temperature": features.temperature,
        "power_factor": features.power_factor,
        "load_kw": features.load_kw,
        "frequency_hz": features.frequency_hz,
        "hour": features.hour,
        "day_of_week": features.day_of_week,
        "is_weekend": features.is_weekend,
        "voltage_flag": features.voltage_flag,
        "pf_issue": features.pf_issue,
        "high_temp": features.high_temp,
        "load_intensity": features.load_intensity,
    }])

    # Ensure model is available
    mdl = model or load_model()
    if mdl is None:
        raise HTTPException(status_code=503, detail="Model not available. Check server logs for load errors.")

    # Get prediction
    predicted_units = float(mdl.predict(df)[0])

    return {"prediction": round(predicted_units, 2), "units": "kWh"}


@app.get("/", response_class=HTMLResponse)
def home():
    # Serve the HTML file
    with open("src/api/templates/index.html", "r", encoding="utf-8") as f:
        return f.read()
