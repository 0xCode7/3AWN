from transformers import AutoTokenizer, AutoModelForSequenceClassification
from huggingface_hub import snapshot_download
import torch

HF_REPO = "0xCode/3AWN"
HF_CACHE_DIR = "./hf_models"


tokenizer = None
model = None


def load_model():
    global tokenizer, model

    if model is None:

        snapshot_download(
            repo_id=HF_REPO,
            local_dir=HF_CACHE_DIR,
        )

        tokenizer = AutoTokenizer.from_pretrained(HF_CACHE_DIR)
        model = AutoModelForSequenceClassification.from_pretrained(HF_CACHE_DIR)

        model.eval()


def predict_ddi(smiles1: str, smiles2: str) -> float:

    load_model()   # 🔥 lazy loading

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
