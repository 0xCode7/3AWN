import numpy as np
import pandas as pd
import joblib
from hashlib import sha256
from pathlib import Path
from django.conf import settings

# ==========================================================
# ✅ Model file path
# ==========================================================
LOCAL_MODEL_PATH = Path(settings.BASE_DIR) / "drugs" / "ai_model" / "ddi_model.pkl"
ddi_model = None


# ==========================================================
# ✅ Load DDI Model
# ==========================================================
def load_ddi_model():
    global ddi_model
    try:
        if not LOCAL_MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {LOCAL_MODEL_PATH}")

        ddi_model = joblib.load(LOCAL_MODEL_PATH)
        print(f"✅ DDI model loaded from: {LOCAL_MODEL_PATH}")

    except Exception as e:
        print(f"❌ Failed to load DDI model: {e}")
        ddi_model = None


# ==========================================================
# 🔢 Convert drug name → numeric vector (2048 dims)
# ==========================================================
def hash_to_vector(drug_name: str, size: int = 2048) -> np.ndarray:
    h = sha256(drug_name.encode("utf-8")).digest()
    vec = np.array(list(h) * (size // len(h) + 1))[:size]
    return vec / 255.0  # Normalize 0-1


# ==========================================================
# 🔮 Predict Drug–Drug Interaction
# ==========================================================
def predict_ddi_api(drug_a: str, drug_b: str) -> dict:
    if ddi_model is None:
        return {"error": "Model not loaded. Restart server or call load_ddi_model()."}

    try:
        # Create 2048 features per drug → 4096 total
        vec_a = hash_to_vector(drug_a, size=2048)
        vec_b = hash_to_vector(drug_b, size=2048)

        X = np.concatenate([vec_a, vec_b]).reshape(1, -1)
        X = pd.DataFrame(X)

        proba = ddi_model.predict_proba(X)[0][1]
        label = "yes" if proba >= 0.5 else "no"
        severity = (
            "High" if proba > 0.8 else
            "Moderate" if proba > 0.5 else
            "Low"
        )

        return {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "label": label,
            "probability": float(proba),
            "severity_category": severity
        }

    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}


# ==========================================================
# ⚡ Load model automatically at startup
# ==========================================================
load_ddi_model()
