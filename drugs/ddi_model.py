# drugs/ddi_model.py
import os
from django.conf import settings
from drugs.ddi_model_files.ddi_pipeline import predict_interaction as pipeline_predict

# Path to best model (already trained)
MODEL_PATH = os.path.join(settings.BASE_DIR, "drugs", "ddi_model_files", "best_ddi_model.pkl")

severity_messages = {
    "yes": "⚠️ Interaction detected: These drugs may interact. Consult your healthcare provider.",
    "no": "✅ No known interaction between these drugs."
}

def predict_ddi(drug_a: str, drug_b: str):
    """
    Run DDI prediction using the trained pipeline.
    Returns: (label, probability, message)
    """
    label, proba = pipeline_predict(drug_a, drug_b, model_path=MODEL_PATH)
    message = severity_messages.get(label, "Unknown interaction.")
    return {
        "label": label,
        "probability": proba,
        "message": message
    }
