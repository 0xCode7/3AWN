import os
import joblib
import pandas as pd
import tempfile
import requests
from django.conf import settings
from pathlib import Path

# ==========================================================
# ✅ Model configuration
# ==========================================================
LOCAL_MODEL_PATH = Path(settings.BASE_DIR) / "drugs" / "ai_model" / "best_ddi_model.pkl"

# 🧠 Replace this with your Hugging Face file URL (raw link)
REMOTE_MODEL_URL = "https://huggingface.co/0xCode/3AWN/resolve/main/best_ddi_model.pkl"

ddi_model = None


# ==========================================================
# ✅ Load the model (local → fallback to HuggingFace)
# ==========================================================
def load_ddi_model():
    global ddi_model

    try:
        if LOCAL_MODEL_PATH.exists():
            print(f"✅ Loading local model from: {LOCAL_MODEL_PATH}")
            ddi_model = joblib.load(LOCAL_MODEL_PATH)
        else:
            print("⚠️ Local model not found. Downloading from Hugging Face...")

            response = requests.get(REMOTE_MODEL_URL, stream=True)
            response.raise_for_status()

            # Save temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            print(f"✅ Downloaded remote model → {tmp_path}")
            ddi_model = joblib.load(tmp_path)

        print("✅ Model loaded successfully!")

    except Exception as e:
        print("❌ Error loading model:", repr(e))
        ddi_model = None


# ==========================================================
# 🔮 Prediction function
# ==========================================================
def predict_ddi_api(drug_a, drug_b):
    if ddi_model is None:
        return {"error": "Model not loaded."}

    try:
        X = pd.DataFrame([{"drug1_name": drug_a, "drug2_name": drug_b}])
        proba = ddi_model.predict_proba(X)[0][1]

        label = "yes" if proba >= 0.5 else "no"
        severity = "High" if proba > 0.8 else "Moderate" if proba > 0.5 else "Low"

        return {
            "label": label,
            "probability": float(proba),
            "message": f"Interaction probability: {proba:.2f}",
            "severity_category": severity,
        }

    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}


# ==========================================================
# ⚡ Load on server startup
# ==========================================================
# load_ddi_model()
