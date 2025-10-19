import joblib
from django.conf import settings
from pathlib import Path

# ==========================================================
# ✅ إعدادات الموديل المحلي
# ==========================================================
LOCAL_MODEL_PATH = Path(settings.BASE_DIR) / "drugs" / "ai_model" / "best_ddi_model.pkl"
ddi_model = None


# ==========================================================
# ✅ تحميل الموديل مرة واحدة فقط وقت تشغيل السيرفر
# ==========================================================
def load_ddi_model():
    global ddi_model

    try:
        if not LOCAL_MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {LOCAL_MODEL_PATH}")

        print(f"✅ Loading local model from: {LOCAL_MODEL_PATH}")
        ddi_model = joblib.load(LOCAL_MODEL_PATH)
        print("✅ Model loaded successfully!")

    except Exception as e:
        print("❌ Error loading model:", repr(e))
        ddi_model = None


# حمّل الموديل عند تشغيل السيرفر
load_ddi_model()


# ==========================================================
# 🔮 دالة التنبؤ
# ==========================================================
def predict_ddi_api(drug_a, drug_b):
    import pandas as pd
    import numpy as np

    if ddi_model is None:
        return {"error": "Model not loaded."}

    # 🧠 نحافظ على القيم كنصوص بدل ما نحولها لأرقام hash
    X = pd.DataFrame(
        [[drug_a, drug_b]],
        columns=["drug1_name", "drug2_name"]
    )

    try:
        # بعض الموديلات تعمل مع النصوص مباشرة (مثل pipeline فيها encoder)
        if hasattr(ddi_model, "predict_proba"):
            proba = float(ddi_model.predict_proba(X)[0][1])
        else:
            proba = float(ddi_model.predict(X)[0])
    except Exception as e:
        return {"error": f"Prediction failed: {e}"}

    label = "yes" if proba > 0.5 else "no"

    if proba > 0.8:
        severity = "High"
    elif proba > 0.5:
        severity = "Moderate"
    else:
        severity = "Low"

    return {
        "label": label,
        "probability": round(proba, 3),
        "message": f"Interaction probability: {proba:.2f}",
        "severity_category": severity,
    }
