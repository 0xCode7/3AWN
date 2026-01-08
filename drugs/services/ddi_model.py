from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os

HF_REPO = "0xCode/3AWN"   # Hugging Face

tokenizer = AutoTokenizer.from_pretrained(HF_REPO)
model = AutoModelForSequenceClassification.from_pretrained(HF_REPO)
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
