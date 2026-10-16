# ============================================================================
# src/sagemaker_train.py – SageMaker-Compatible Training Script
# ============================================================================
# This script follows the SageMaker script-mode contract:
#   - Reads training data from SM_CHANNEL_TRAIN (or a local path)
#   - Writes the model to SM_MODEL_DIR (or a local path)
#   - Accepts hyperparameters via argparse
#
# It runs both locally and on AWS SageMaker without modification.
# ============================================================================

import os
import sys
import argparse
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss


# ============================================================================
# Utility: SageMaker environment or local fallback
# ============================================================================

def get_train_dir() -> Path:
    """Return the training data directory (SageMaker or local)."""
    if "SM_CHANNEL_TRAIN" in os.environ:
        return Path(os.environ["SM_CHANNEL_TRAIN"])
    return Path("../data/splits")  # local fallback


def get_model_dir() -> Path:
    """Return the model output directory (SageMaker or local)."""
    if "SM_MODEL_DIR" in os.environ:
        return Path(os.environ["SM_MODEL_DIR"])
    return Path("../artifacts/sagemaker_output")  # local fallback


# ============================================================================
# Training
# ============================================================================

def train(args):
    print("=" * 60)
    print("SageMaker-Compatible Training")
    print("=" * 60)

    train_dir = get_train_dir()
    model_dir = get_model_dir()
    model_dir.mkdir(parents=True, exist_ok=True)

    print(f"📂 Training dir: {train_dir}")
    print(f"📂 Model dir:    {model_dir}")

    # ---------- Load data ----------
    X_train = pd.read_parquet(train_dir / "X_train.parquet")
    y_train = pd.read_parquet(train_dir / "y_train.parquet")["target"]
    X_test = pd.read_parquet(train_dir / "X_test.parquet")
    y_test = pd.read_parquet(train_dir / "y_test.parquet")["target"]

    print(f"✅ Loaded train: {X_train.shape}, test: {X_test.shape}")

    # ---------- Preprocessing ----------
    numeric_cols = X_train.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = X_train.select_dtypes(include=['object', 'category']).columns.tolist()

    numeric_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])

    categorical_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore')),
    ])

    preprocessor = ColumnTransformer([
        ('num', numeric_transformer, numeric_cols),
        ('cat', categorical_transformer, categorical_cols),
    ])

    # ---------- Model ----------
    base_model = LogisticRegression(
        C=args.C,
        solver=args.solver,
        max_iter=args.max_iter,
        random_state=42,
    )

    # Calibrate with Platt scaling
    model = CalibratedClassifierCV(base_model, method='sigmoid', cv=5)

    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', model),
    ])

    # ---------- Train ----------
    print("\n🏋️ Training...")
    pipeline.fit(X_train, y_train)

    # ---------- Evaluate ----------
    proba = pipeline.predict_proba(X_test)[:, 1]
    pr_auc = average_precision_score(y_test, proba)
    roc_auc = roc_auc_score(y_test, proba)
    brier = brier_score_loss(y_test, proba)

    print("\n📊 Test metrics:")
    print(f"   PR-AUC:  {pr_auc:.4f}")
    print(f"   ROC-AUC: {roc_auc:.4f}")
    print(f"   Brier:   {brier:.4f}")

    # ---------- Save model ----------
    model_path = model_dir / "model.joblib"
    joblib.dump(pipeline, model_path)

    metadata = {
        "model_type": "LogisticRegression_Calibrated",
        "hyperparameters": {
            "C": args.C,
            "solver": args.solver,
            "max_iter": args.max_iter,
        },
        "metrics": {
            "pr_auc": round(pr_auc, 4),
            "roc_auc": round(roc_auc, 4),
            "brier": round(brier, 4),
        },
        "n_features": len(numeric_cols) + len(categorical_cols),
        "n_train_samples": len(X_train),
        "n_test_samples": len(X_test),
    }

    with open(model_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ Model saved to {model_path}")
    print(f"✅ Metadata saved to {model_dir / 'metadata.json'}")

    return pr_auc


# ============================================================================
# Entry point
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser()

    # SageMaker passes hyperparameters as --key value
    parser.add_argument("--C", type=float, default=0.0187)
    parser.add_argument("--solver", type=str, default="lbfgs")
    parser.add_argument("--max_iter", type=int, default=190)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(args)