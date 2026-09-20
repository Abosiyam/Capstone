# ============================================================================
# app.py – FastAPI for Boréal Marché Retention Model
# ============================================================================

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List
import json
from pathlib import Path

# ---------- 1. Load model and metadata ----------
MODEL_PATH = Path('artifacts/final_model.joblib')
METADATA_PATH = Path('artifacts/deployment_metadata.json')

model = joblib.load(MODEL_PATH)

with open(METADATA_PATH, 'r') as f:
    metadata = json.load(f)

feature_columns = metadata['feature_columns']
optimal_threshold = metadata['optimal_threshold']

print(f"✅ Model loaded: {len(feature_columns)} features, threshold={optimal_threshold}")

# ---------- 2. Request schema (matches the 25 model features) ----------
class CustomerFeatures(BaseModel):
    model_config = ConfigDict(extra='forbid')

    order_count: float
    total_orders: float
    total_items: float
    avg_items_per_order: float
    std_items_per_order: float
    total_spend: float
    avg_spend_per_order: float
    max_order_value: float
    min_order_value: float
    first_purchase_date: str
    last_purchase_date: str
    days_since_last_purchase: float
    customer_lifetime_days: float
    order_frequency_days: float
    avg_days_between_orders: float
    avg_basket_size: float
    unique_products_bought: float
    product_diversity: float
    pct_drink: float
    pct_food: float
    pct_gift: float
    pct_household: float
    pct_office: float
    pct_other: float
    top_country: str

# ---------- 3. FastAPI app ----------
app = FastAPI(title="Boréal Marche Retention API", version="1.0.0")

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {
        "message": "Boréal Marché Retention API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }

@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "healthy"}

@app.get("/info")
async def info():
    return {
        "model": "Logistic_Regression_Calibrated",
        "version": metadata.get("model_version", "1.0.0"),
        "n_features": len(feature_columns),
        "optimal_threshold": optimal_threshold
    }

@app.post("/predict")
async def predict(customer: CustomerFeatures):
    try:
        data = customer.model_dump()
        X = pd.DataFrame([data])

        # Check for missing columns
        missing = [col for col in feature_columns if col not in X.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        X = X[feature_columns]
        prob = model.predict_proba(X)[0][1]
        decision = "Send coupon" if prob >= optimal_threshold else "No coupon"

        return {
            "probability": round(float(prob), 4),
            "threshold": optimal_threshold,
            "decision": decision
        }
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/predict/batch")
async def predict_batch(customers: List[CustomerFeatures]):
    try:
        results = []
        for customer in customers:
            data = customer.model_dump()
            X = pd.DataFrame([data])
            X = X[feature_columns]
            prob = model.predict_proba(X)[0][1]
            decision = "Send coupon" if prob >= optimal_threshold else "No coupon"
            results.append({"probability": round(float(prob), 4), "decision": decision})
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ---------- 4. Run ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)