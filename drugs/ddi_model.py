# drugs/ddi_model.py
import os
from django.conf import settings
from drugs.ddi_model_files.ddi_pipeline import predict_interaction as pipeline_predict

# Path to best model (already trained)
MODEL_PATH = os.path.join(settings.BASE_DIR, "drugs", "ddi_model_files", "best_ddi_model.pkl")


def categorize_severity(probability: float) -> str:
    """
    Categorize DDI severity based on probability.
    Adjust thresholds as needed.
    """
    if probability >= 0.75:
        return "Major"
    elif probability >= 0.4:
        return "Moderate"
    elif probability > 0:
        return "Minor"
    else:
        return "None"


def generate_message(severity: str, drug_a: str, drug_b: str) -> str:
    """
    Generate a user-friendly message based on severity.
    """
    if severity == "Major":
        return f"Major interaction detected between {drug_a} and {drug_b}. Consult your healthcare provider immediately."
    elif severity == "Moderate":
        return f"Moderate interaction detected between {drug_a} and {drug_b}. Use caution."
    elif severity == "Minor":
        return f"Minor interaction detected between {drug_a} and {drug_b}. Likely minimal risk."
    else:
        return f"No known interaction between {drug_a} and {drug_b}."


def predict_ddi(drug_a: str, drug_b: str):
    """
    Run DDI prediction using the trained pipeline.
    Returns: label, probability, severity_category, message
    """
    label, proba = pipeline_predict(drug_a, drug_b, model_path=MODEL_PATH)
    severity_category = categorize_severity(proba) if label == "yes" else "None"
    message = generate_message(severity_category, drug_a, drug_b)

    return {
        "label": label,
        "probability": proba,
        "severity_category": severity_category,
        "message": message
    }
