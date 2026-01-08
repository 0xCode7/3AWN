import numpy as np
import pandas as pd
import joblib
from hashlib import sha256
from pathlib import Path
from django.conf import settings

LOCAL_MODEL_PATH = Path(settings.BASE_DIR) / "drugs" / "ai_model" / "ddi_model.pkl"
ddi_model = None

def load_ddi_model():
    global ddi_model
    try:
        if not LOCAL_MODEL_PATH.exists():
            print(f"❌ Model file not found at: {LOCAL_MODEL_PATH}")
            return

        ddi_model = joblib.load(LOCAL_MODEL_PATH)
        print(f"✅ Model loaded: {LOCAL_MODEL_PATH}")

    except Exception as e:
        print(f"❌ Failed to load model: {e}")

def hash_to_vector(drug_name: str, size: int = 2048):
    h = sha256(drug_name.encode()).digest()
    vec = np.array(list(h) * (size // len(h) + 1))[:size]
    return vec / 255.0

def predict_ddi_api(drug_a, drug_b):
    global ddi_model

    if ddi_model is None:
        return {"error": "Model not loaded on server."}

    try:
        vec_a = hash_to_vector(drug_a)
        vec_b = hash_to_vector(drug_b)
        X = np.concatenate([vec_a, vec_b]).reshape(1, -1)
        X = pd.DataFrame(X)

        proba = ddi_model.predict_proba(X)[0][1]
        label = "yes" if proba >= 0.5 else "no"
        severity = "High" if proba > 0.8 else "Moderate" if proba > 0.5 else "Low"

        return {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "label": label,
            "probability": float(proba),
            "severity_category": severity
        }
    except Exception as e:
        return {"error": str(e)}
