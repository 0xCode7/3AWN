from __future__ import annotations
import os
import argparse
import joblib
import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)


# -----------------------------
# Configuration
# -----------------------------
DEFAULT_CSV_PATH = "DDI_data.csv"
BEST_MODEL_PATH = "best_ddi_model.pkl"
RANDOM_STATE = 42
NEGATIVE_SAMPLING_RATIO = 1.0  # number of negatives per positive if needed


# -----------------------------
# Utilities
# -----------------------------

def read_head(csv_path: str, n: int = 10) -> pd.DataFrame:
    """Read the first n rows of a CSV (with headers)."""
    return pd.read_csv(csv_path, nrows=n)


def load_full(csv_path: str) -> pd.DataFrame:
    """Load the full dataset."""
    return pd.read_csv(csv_path)


def _augment_with_negative_samples(
    df: pd.DataFrame,
    feature_cols: Tuple[str, str],
    ratio: float = NEGATIVE_SAMPLING_RATIO,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Generate synthetic negative samples (no interaction) by sampling random drug pairs
    not present in the dataset. Returns an augmented DataFrame with additional rows
    where 'interaction_type' is empty (so target will be 0 by inference).

    Assumption: interactions are undirected; a pair (A,B) is equivalent to (B,A).
    """
    if ratio <= 0:
        return df

    df = df.copy()
    col_a, col_b = feature_cols

    # Build set of existing (unordered) pairs
    def _key(a, b):
        return tuple(sorted((str(a), str(b))))

    pos_pairs = set(_key(a, b) for a, b in zip(df[col_a], df[col_b]) if pd.notna(a) and pd.notna(b))

    # Unique drugs from both columns
    drugs = pd.Index(pd.concat([df[col_a].astype(str), df[col_b].astype(str)], ignore_index=True).dropna().unique())
    if len(drugs) < 2:
        return df

    n_pos = len(pos_pairs)
    n_neg_target = int(n_pos * ratio)
    if n_neg_target == 0:
        return df

    rng = np.random.default_rng(random_state)
    neg_pairs = set()
    # Sample until we collect the desired number of unique negative pairs
    while len(neg_pairs) < n_neg_target:
        a = drugs[rng.integers(0, len(drugs))]
        b = drugs[rng.integers(0, len(drugs))]
        if a == b:
            continue
        k = _key(a, b)
        if k in pos_pairs or k in neg_pairs:
            continue
        neg_pairs.add(k)

    # Build negatives DataFrame; ensure 'interaction_type' present as empty to infer 0
    df_neg = pd.DataFrame(list(neg_pairs), columns=[col_a, col_b])
    # Insert empty interaction_type for negatives so inference maps to 0
    if 'interaction_type' in df.columns:
        df_neg['interaction_type'] = ""

    # Align columns
    for c in df.columns:
        if c not in df_neg.columns:
            df_neg[c] = pd.NA

    df_aug = pd.concat([df, df_neg[df.columns]], ignore_index=True)
    return df_aug


def prepare_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare target column (binary interaction) and return features, target.

    Priority order for target detection:
    - 'interaction' column (0/1 or yes/no)
    - 'label' column (0/1 or yes/no)
    - Fallback: from 'interaction_type' (non-null => 1)

    Returns:
        X_df: DataFrame with feature columns
        y: Series with binary labels (0/1)
    """
    df = df.copy()

    # Standardize potential target columns
    target_col = None
    for col in ["interaction", "label"]:
        if col in df.columns:
            target_col = col
            break

    if target_col is not None:
        # Normalize to 0/1 integer
        y_raw = df[target_col]
        if y_raw.dtype == object:
            y = y_raw.astype(str).str.lower().map({"yes": 1, "1": 1, "true": 1, "no": 0, "0": 0, "false": 0})
            # Any other non-empty gets 1
            y = y.fillna((y_raw.astype(str).str.len() > 0).astype(int))
        else:
            y = (y_raw.astype(float) > 0).astype(int)
    else:
        # Fallback: infer from interaction_type (any value -> 1)
        if "interaction_type" not in df.columns:
            raise ValueError(
                "No explicit binary target found. Provide 'interaction' or 'label' column, or 'interaction_type' to infer."
            )
        y = (df["interaction_type"].astype(str).str.len() > 0).astype(int)

    # Feature columns: prefer human-readable names; fallback to IDs
    feature_cols = []
    if "drug1_name" in df.columns and "drug2_name" in df.columns:
        feature_cols = ["drug1_name", "drug2_name"]
    elif "drug1" in df.columns and "drug2" in df.columns:
        feature_cols = ["drug1", "drug2"]
    elif "drug_a" in df.columns and "drug_b" in df.columns:
        feature_cols = ["drug_a", "drug_b"]
    elif "drug1_id" in df.columns and "drug2_id" in df.columns:
        feature_cols = ["drug1_id", "drug2_id"]
    else:
        # Try to guess by pattern
        name_like = [c for c in df.columns if "drug" in c.lower()]
        if len(name_like) >= 2:
            feature_cols = name_like[:2]
        else:
            raise ValueError("Could not find drug pair feature columns. Expected e.g. 'drug1_name','drug2_name'.")

    X_df = df[feature_cols].copy()

    # Basic cleaning: drop rows where any of the features or target is missing
    mask = X_df.notna().all(axis=1) & y.notna()
    X_df = X_df[mask]
    y = y[mask].astype(int)

    # If all labels are one class, try to synthesize negatives from random non-listed pairs
    if y.nunique() < 2:
        # Only attempt if we can infer negatives via empty interaction_type
        if "interaction_type" in df.columns:
            # Rebuild from the pre-cleaned original df columns used for features
            df_for_neg = df.copy()
            # Augment with negatives
            df_aug = _augment_with_negative_samples(df_for_neg, (feature_cols[0], feature_cols[1]))
            # Re-derive target
            y_aug = (df_aug["interaction_type"].astype(str).str.len() > 0).astype(int)
            X_aug = df_aug[feature_cols].copy()
            mask2 = X_aug.notna().all(axis=1) & y_aug.notna()
            X_aug = X_aug[mask2]
            y_aug = y_aug[mask2].astype(int)
            if y_aug.nunique() < 2:
                raise ValueError(
                    "Target has only one class even after negative sampling. Provide explicit negatives or adjust dataset."
                )
            return X_aug, y_aug
        else:
            raise ValueError(
                "Target has only one class after cleaning. Provide negative examples or adjust dataset."
            )

    return X_df, y


def build_preprocessor(feature_cols: Tuple[str, str]) -> ColumnTransformer:
    """Build a ColumnTransformer to one-hot encode both drug columns."""
    categorical_features = list(feature_cols)
    transformer = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=True), categorical_features),
        ],
        remainder="drop",
        sparse_threshold=1.0,
    )
    return transformer


def build_models(preprocessor: ColumnTransformer) -> Dict[str, Pipeline]:
    """Create model pipelines for Logistic Regression and Random Forest."""
    models: Dict[str, Pipeline] = {}

    log_reg = LogisticRegression(
        solver="saga",
        max_iter=200,
        random_state=RANDOM_STATE,
        class_weight="balanced",
    )
    models["logistic_regression"] = Pipeline([
        ("pre", preprocessor),
        ("clf", log_reg),
    ])

    rf = RandomForestClassifier(
        n_estimators=300,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced_subsample",
    )
    models["random_forest"] = Pipeline([
        ("pre", preprocessor),
        ("clf", rf),
    ])

    return models


def evaluate_model(name: str, model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Evaluate a trained model and print metrics."""
    y_pred = model.predict(X_test)
    if hasattr(model.named_steps.get("clf", None), "predict_proba"):
        y_proba = model.predict_proba(X_test)[:, 1]
    else:
        # Some classifiers might not support predict_proba
        y_proba = None

    avg = "binary"
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0, average=avg),
        "recall": recall_score(y_test, y_pred, zero_division=0, average=avg),
        "f1": f1_score(y_test, y_pred, zero_division=0, average=avg),
    }

    print("\n=== Evaluation:", name, "===")
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1-score:  {metrics['f1']:.4f}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred, zero_division=0))
    print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

    return metrics


def train_and_select_best(csv_path: str, test_size: float = 0.2, random_state: int = RANDOM_STATE) -> Tuple[str, Pipeline]:
    """Full training pipeline: load, preprocess, split, train, evaluate; return best model name and pipeline."""
    print(f"Loading dataset from: {csv_path}")
    head_df = read_head(csv_path, n=10)
    print("\nFirst rows (head):\n", head_df)

    df = load_full(csv_path)

    # Prepare features and target
    X_df, y = prepare_target(df)

    # Identify feature column names used
    feature_cols = tuple(X_df.columns.tolist())  # type: ignore

    # Build preprocessing and model pipelines
    pre = build_preprocessor(feature_cols)
    models = build_models(pre)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_df, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Train and evaluate
    results = {}
    best_name = None
    best_f1 = -1.0

    for name, model in models.items():
        print(f"\nTraining model: {name} ...")
        model.fit(X_train, y_train)
        metrics = evaluate_model(name, model, X_test, y_test)
        results[name] = (model, metrics)
        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            best_name = name

    assert best_name is not None
    best_model = results[best_name][0]
    print(f"\nBest model by F1-score: {best_name} (F1={best_f1:.4f})")

    # Save best pipeline (includes preprocessing)
    joblib.dump(best_model, BEST_MODEL_PATH)
    print(f"Saved best model pipeline to: {BEST_MODEL_PATH}")

    return best_name, best_model


# -----------------------------
# Inference helper
# -----------------------------

def load_best_model(model_path: str = BEST_MODEL_PATH) -> Pipeline:
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file '{model_path}' not found. Train the pipeline first to generate it."
        )
    model: Pipeline = joblib.load(model_path)
    return model


def predict_interaction(drug1: str, drug2: str, model_path: str = BEST_MODEL_PATH) -> Tuple[str, float]:
    """Predict whether there is an interaction for two drug names.

    Returns:
        label_str: "yes" or "no"
        prob: predicted probability for class '1' (interaction)
    """
    model = load_best_model(model_path)

    # Wrap into DataFrame with the same column names used during training
    # We can infer column names from the ColumnTransformer
    pre: ColumnTransformer = model.named_steps["pre"]
    # Extract original feature names list from the transformer remainder
    # We stored two columns in order; retrieve from transformers
    cat_features = pre.transformers_[0][2]
    if isinstance(cat_features, (list, tuple)) and len(cat_features) >= 2:
        col1, col2 = cat_features[0], cat_features[1]
    else:
        # Fallback to generic names
        col1, col2 = "drug1_name", "drug2_name"

    X_input = pd.DataFrame([{col1: drug1, col2: drug2}])

    # Predict
    if hasattr(model.named_steps.get("clf", None), "predict_proba"):
        proba = model.predict_proba(X_input)[0, 1]
    else:
        # Use decision function if available; map to probability via sigmoid-like transform
        clf = model.named_steps.get("clf", None)
        if hasattr(clf, "decision_function"):
            score = clf.decision_function(X_input)
            proba = 1.0 / (1.0 + np.exp(-score))[0]
        else:
            # As last resort, cast prediction to {0,1}
            pred = model.predict(X_input)[0]
            proba = float(pred)

    label = int(proba >= 0.5)
    return ("yes" if label == 1 else "no", float(proba))


# -----------------------------
# CLI
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="DDI pipeline: train models and predict interactions.")
    parser.add_argument("--csv", type=str, default=DEFAULT_CSV_PATH, help="Path to DDI_data.csv")
    parser.add_argument("--test_size", type=float, default=0.2, help="Test size fraction")
    parser.add_argument("--predict", nargs=2, metavar=("DRUG1", "DRUG2"), help="Predict interaction for two drugs")
    args = parser.parse_args()

    if args.predict:
        # Inference mode
        d1, d2 = args.predict
        label, proba = predict_interaction(d1, d2)
        print(f"Prediction for ({d1}, {d2}): {label} (prob={proba:.4f})")
    else:
        # Training mode
        train_and_select_best(csv_path=args.csv, test_size=args.test_size)


if __name__ == "__main__":
    main()
