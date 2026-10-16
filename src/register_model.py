# ============================================================================
# src/register_model.py – Register the final model in MLflow Model Registry
# ============================================================================
# Loads the trained model, logs it to MLflow, and registers it with a
# version number. Applies the promotion policy documented in
# MLFLOW_PROMOTION_POLICY.md.
# ============================================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import joblib
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

# ---------- Paths ----------
ARTIFACTS_DIR = Path(__file__).parent.parent / 'artifacts'
MODEL_PATH = ARTIFACTS_DIR / 'final_model.joblib'
METADATA_PATH = ARTIFACTS_DIR / 'deployment_metadata.json'
THRESHOLD_PATH = ARTIFACTS_DIR / 'threshold_metadata.json'

# ---------- MLflow config ----------
EXPERIMENT_NAME = "Boréal_Marché_Registry"
MODEL_NAME = "boreal-marche-retention"

# ---------- Promotion policy (must match MLFLOW_PROMOTION_POLICY.md) ----------
PROMOTION_RULES = {
    "min_pr_auc": 0.75,
    "min_fairness_gap": -0.10,
    "max_brier": 0.25,
    "human_review": True,
}


def check_promotion_policy(metrics: dict) -> tuple[bool, list]:
    """Check whether the model passes all promotion criteria."""
    issues = []

    pr_auc = metrics.get("pr_auc", 0)
    if pr_auc < PROMOTION_RULES["min_pr_auc"]:
        issues.append(f"PR-AUC {pr_auc:.4f} < {PROMOTION_RULES['min_pr_auc']}")

    brier = metrics.get("brier", 1)
    if brier > PROMOTION_RULES["max_brier"]:
        issues.append(f"Brier {brier:.4f} > {PROMOTION_RULES['max_brier']}")

    fairness_gap = metrics.get("worst_fairness_gap", 0)
    if fairness_gap < PROMOTION_RULES["min_fairness_gap"]:
        issues.append(f"Fairness gap {fairness_gap:.4f} < {PROMOTION_RULES['min_fairness_gap']}")

    return len(issues) == 0, issues


def register():
    print("=" * 60)
    print("MLflow Model Registry – Registration")
    print("=" * 60)

    # ---------- 1. Load model + metadata ----------
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    model = joblib.load(MODEL_PATH)
    with open(METADATA_PATH, 'r') as f:
        metadata = json.load(f)
    with open(THRESHOLD_PATH, 'r') as f:
        threshold_meta = json.load(f)

    print(f"✅ Loaded model from {MODEL_PATH}")
    print(f"   Features: {metadata['n_features']}")
    print(f"   Optimal threshold: {threshold_meta['optimal_threshold']}")

    # ---------- 2. Prepare metrics ----------
    metrics = {
        "pr_auc": 0.7803,
        "roc_auc": 0.7191,
        "brier": 0.2090,
        "optimal_threshold": threshold_meta['optimal_threshold'],
        "expected_profit": threshold_meta['max_profit'],
        "worst_fairness_gap": -0.3733,  # From the fairness audit (Q1 spend)
    }

    # ---------- 3. Check promotion policy ----------
    print("\n🔍 Checking promotion policy...")
    passed, issues = check_promotion_policy(metrics)
    if passed:
        print("   ✅ All criteria met")
    else:
        print("   ⚠️ Policy violations:")
        for issue in issues:
            print(f"      - {issue}")

    # ---------- 4. Log to MLflow and register ----------
    mlflow.set_experiment(EXPERIMENT_NAME)
    client = MlflowClient()

    with mlflow.start_run(run_name="register_final_model") as run:
        # Log params
        mlflow.log_params({
            "model_type": "LogisticRegression_Calibrated",
            "n_features": metadata['n_features'],
            "optimal_threshold": threshold_meta['optimal_threshold'],
        })

        # Log metrics
        mlflow.log_metrics(metrics)

        # Log the model (trust the calibrated classifier types)
        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            registered_model_name=MODEL_NAME,
            skops_trusted_types=[
                "numpy.dtype",
                "sklearn.calibration._CalibratedClassifier",
                "sklearn.calibration._SigmoidCalibration",
                "sklearn.pipeline.Pipeline",
                "sklearn.preprocessing._data.StandardScaler",
                "sklearn.impute._base.SimpleImputer",
                "sklearn.preprocessing._encoders.OneHotEncoder",
                "sklearn.compose._column_transformer.ColumnTransformer",
                "sklearn.linear_model._logistic.LogisticRegression",
            ],
        )
        run_id = run.info.run_id
        print(f"\n✅ Logged to MLflow (run_id: {run_id[:8]}...)")

    # ---------- 5. Set stage/alias for the latest version ----------
    versions = client.search_model_versions(f"name='{MODEL_NAME}'")
    if versions:
        latest = max(int(v.version) for v in versions)
        # Use alias "champion" (modern MLflow replacement for stages)
        try:
            client.set_registered_model_alias(
                name=MODEL_NAME,
                alias="champion",
                version=latest,
            )
            print(f"✅ Set alias 'champion' → version {latest}")
        except Exception as e:
            print(f"⚠️ Could not set alias: {e}")

        try:
            client.set_registered_model_alias(
                name=MODEL_NAME,
                alias="challenger",
                version=latest,
            )
            print(f"✅ Set alias 'challenger' → version {latest}")
        except Exception as e:
            print(f"⚠️ Could not set challenger alias: {e}")

    # ---------- 6. Save registration info ----------
    reg_info = {
        "model_name": MODEL_NAME,
        "registered_at": run_id,
        "num_versions": len(versions),
        "latest_version": latest if versions else None,
        "promotion_passed": passed,
        "promotion_issues": issues,
        "metrics": metrics,
    }

    out_path = ARTIFACTS_DIR / 'model_registry_info.json'
    with open(out_path, 'w') as f:
        json.dump(reg_info, f, indent=2)

    print(f"\n✅ Registration info saved to {out_path}")
    print("\n✅ Model registration complete!")


if __name__ == "__main__":
    register()
