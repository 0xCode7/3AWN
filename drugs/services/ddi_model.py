from transformers import AutoTokenizer, AutoModelForSequenceClassification
from huggingface_hub import snapshot_download
import torch
import os

HF_REPO = "0xCode/3AWN"
HF_CACHE_DIR = "/tmp/hf_models"

tokenizer = None
model = None


def load_model():
    global tokenizer, model

    if model is None:

        if not os.path.exists(HF_CACHE_DIR):
            snapshot_download(
                repo_id=HF_REPO,
                local_dir=HF_CACHE_DIR,
                local_dir_use_symlinks=False
            )

        tokenizer = AutoTokenizer.from_pretrained(
            HF_CACHE_DIR,
            local_files_only=True
        )

        model = AutoModelForSequenceClassification.from_pretrained(
            HF_CACHE_DIR,
            local_files_only=True
        )

        model.to("cpu")
        model.eval()


def predict_ddi(smiles1: str, smiles2: str) -> float:

    load_model()

    inputs = tokenizer(
        smiles1,
        smiles2,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256
    )

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)
        prob = probs[0, 1].item()

    return round(prob, 4)
