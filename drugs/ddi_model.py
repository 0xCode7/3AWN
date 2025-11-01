import joblib
import pandas as pd
from pathlib import Path
from django.conf import settings

# ==========================================================
# ✅ Model configuration
# ==========================================================
LOCAL_MODEL_PATH = Path(settings.BASE_DIR) / "drugs" / "ai_model" / "ddi_model.pkl"

ddi_model = None


# ==========================================================
# ✅ Load the model
# ==========================================================
def load_ddi_model():
    """Load the DDI prediction model from the local project folder."""
    global ddi_model

    try:
        if not LOCAL_MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found at: {LOCAL_MODEL_PATH}")

        print(f"✅ Loading model from: {LOCAL_MODEL_PATH}")
        ddi_model = joblib.load(LOCAL_MODEL_PATH)
        print("✅ Model loaded successfully!")

    except Exception as e:
        print("❌ Error loading model:", repr(e))
        ddi_model = None


# ==========================================================
# 🔮 Prediction function
# ==========================================================
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from django.conf import settings
from hashlib import sha256

LOCAL_MODEL_PATH = Path(settings.BASE_DIR) / "drugs" / "ai_model" / "ddi_model.pkl"

ddi_model = None


def load_ddi_model():
    global ddi_model
    try:
        ddi_model = joblib.load(LOCAL_MODEL_PATH)
        print(f"✅ Model loaded from: {LOCAL_MODEL_PATH}")
    except Exception as e:
        print("❌ Error loading model:", repr(e))
        ddi_model = None


def hash_to_vector(drug_name: str, size: int = 512) -> np.ndarray:
    """Convert drug name into a fixed-size numeric vector (deterministic)."""
    # Create a long hash and convert each byte into a number
    h = sha256(drug_name.encode("utf-8")).digest()
    vec = np.array(list(h) * (size // len(h) + 1))[:size]
    return vec / 255.0  # normalize 0-1


def predict_ddi_api(drug_a: str, drug_b: str) -> dict:
    if ddi_model is None:
        return {"error": "Model not loaded. Please call load_ddi_model() first."}

    try:
        # Hash drugs → 512 numeric features
        vec_a = hash_to_vector(drug_a)
        vec_b = hash_to_vector(drug_b)

        X = np.concatenate([vec_a[:256], vec_b[:256]])  # total 512 features
        X = pd.DataFrame([X])

        # Predict safely
        proba = ddi_model.predict_proba(X)[0][1]
        label = "yes" if proba >= 0.5 else "no"
        severity = "High" if proba > 0.8 else "Moderate" if proba > 0.5 else "Low"

        return {
            "label": label,
            "probability": float(proba),
            "severity_category": severity,
        }

    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}


# ==========================================================
# ⚡ Auto-load model on startup
# ==========================================================
load_ddi_model()
