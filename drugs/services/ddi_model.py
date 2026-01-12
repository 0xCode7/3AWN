from transformers import AutoTokenizer, AutoModelForSequenceClassification
from huggingface_hub import snapshot_download
import torch
import os

HF_REPO = "0xCode/3AWN"
HF_CACHE_DIR = "/app/hf_models/3awn_ddi"

# auto-update
snapshot_download(
    repo_id=HF_REPO,
    local_dir=HF_CACHE_DIR,
    local_dir_use_symlinks=False,
    resume_download=True,
)

tokenizer = AutoTokenizer.from_pretrained(HF_CACHE_DIR)
model = AutoModelForSequenceClassification.from_pretrained(HF_CACHE_DIR)
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
