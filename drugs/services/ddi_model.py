from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os
from django.conf import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, "ddi_model")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
model.eval()


def predict_ddi(smiles1: str, smiles2: str) -> float:
    inputs = tokenizer(
        smiles1,
        smiles2,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    )

    with torch.no_grad():
        outputs = model(**inputs)
        prob = torch.softmax(outputs.logits, dim=1)[0, 1].item()

    return round(prob, 4)
