# drugs/ddi_model.py
import joblib
import numpy as np
from rapidfuzz import process
import os
from django.conf import settings
# Load model & matrices

model_dir = os.path.join(settings.BASE_DIR, "drugs", "ddi_model_files")

clf = joblib.load(os.path.join(model_dir, "DDI_rf_model.pkl"))
u = np.load(os.path.join(model_dir, "u_matrix.npy"))
vt = np.load(os.path.join(model_dir, "vt_matrix.npy"))
drug_index = np.load(os.path.join(model_dir, "drug_index.npy"), allow_pickle=True).item()

severity_messages = {
    3: "Major interaction: These drugs can have serious side effects when taken together. Consult a healthcare provider immediately.",
    2: "Moderate interaction: These drugs may interact and cause noticeable effects. Use caution and seek medical advice if necessary.",
    1: "Minor interaction: The interaction is minimal, but you may still experience mild effects.",
    0: "No known interaction: There are no reported interactions between these drugs."
}


def find_closest_drug(drug_name, drug_list, threshold=80):
    match, score, _ = process.extractOne(drug_name.lower(), drug_list)
    if score >= threshold:
        return match
    return None


def preprocess_input(drug_a, drug_b):
    drug_a = find_closest_drug(drug_a, drug_index.keys())
    drug_b = find_closest_drug(drug_b, drug_index.keys())
    if drug_a is None or drug_b is None:
        return None
    idx1 = drug_index[drug_a]
    idx2 = drug_index[drug_b]
    features = np.concatenate([u[idx1], vt[idx2]])
    return features
