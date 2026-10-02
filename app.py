# ============================================================================
# app.py – FastAPI for Boréal Marché Retention + Recommendation
# ============================================================================

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List
import json
from pathlib import Path
from contextlib import asynccontextmanager

from src.recommendation_engine import RecommendationEngine

# ---------- Global objects ----------
ml_bundle = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model and rules ONCE at startup."""
    print("=" * 60)
    print("🚀 Starting Boréal Marché API")
    print("=" * 60)

    MODEL_PATH = Path('artifacts/final_model.joblib')
    METADATA_PATH = Path('artifacts/deployment_metadata.json')

    ml_bundle['model'] = joblib.load(MODEL_PATH)
    with open(METADATA_PATH, 'r') as f:
        metadata = json.load(f)

    ml_bundle['feature_columns'] = metadata['feature_columns']
    ml_bundle['optimal_threshold'] = metadata['optimal_threshold']

    print(f"✅ Model loaded: {len(ml_bundle['feature_columns'])} features, threshold={ml_bundle['optimal_threshold']}")

    ml_bundle['engine'] = RecommendationEngine()
    print("✅ Recommendation engine loaded")
    print("=" * 60)

    yield

    print("🛑 Shutting down...")


app = FastAPI(
    title="Boréal Marche Retention + Recommendation API",
    version="1.2.0",
    lifespan=lifespan
)


# ---------- Schemas ----------
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


class RecommendRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    basket: List[str]
    n: int = 5


# ---------- Endpoints ----------
@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {
        "message": "Boréal Marché Retention + Recommendation API",
        "docs": "/docs",
        "status": "/status",
        "predict": "/predict",
        "recommend": "/recommend",
        "version": "1.2.0"
    }


@app.api_route("/status", methods=["GET", "HEAD"])
async def status():
    return {"status": "healthy"}


@app.get("/info")
async def info():
    return {
        "retention_model": "Logistic_Regression_Calibrated",
        "n_features": len(ml_bundle['feature_columns']),
        "optimal_threshold": ml_bundle['optimal_threshold'],
        "recommendation_engine": ml_bundle['engine'].stats()
    }


@app.post("/predict")
async def predict(customer: CustomerFeatures):
    try:
        data = customer.model_dump()
        X = pd.DataFrame([data])

        missing = [c for c in ml_bundle['feature_columns'] if c not in X.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        X = X[ml_bundle['feature_columns']]
        prob = ml_bundle['model'].predict_proba(X)[0][1]
        decision = "Send coupon" if prob >= ml_bundle['optimal_threshold'] else "No coupon"

        return {
            "probability": round(float(prob), 4),
            "threshold": ml_bundle['optimal_threshold'],
            "decision": decision
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/predict/batch")
async def predict_batch(customers: List[CustomerFeatures]):
    try:
        results = []
        for customer in customers:
            data = customer.model_dump()
            X = pd.DataFrame([data])[ml_bundle['feature_columns']]
            prob = ml_bundle['model'].predict_proba(X)[0][1]
            decision = "Send coupon" if prob >= ml_bundle['optimal_threshold'] else "No coupon"
            results.append({"probability": round(float(prob), 4), "decision": decision})
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/recommend")
async def recommend(request: RecommendRequest):
    try:
        return ml_bundle['engine'].recommend(request.basket, n=request.n)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Run ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)