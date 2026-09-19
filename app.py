# ============================================================================
# app.py – FastAPI for Boréal Marché Retention Model
# ============================================================================

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
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

# ---------- 2. Request schema ----------
class CustomerFeatures(BaseModel):
    model_config = ConfigDict(extra='forbid')

    order_count: float = Field(..., description="Number of orders")
    total_orders: float = Field(..., description="Total orders (alias)")
    total_items: float = Field(..., description="Total items purchased")
    avg_items_per_order: float = Field(..., description="Average items per order")
    std_items_per_order: float = Field(..., description="Std dev of items per order")
    total_spend: float = Field(..., description="Total spend in £")
    avg_spend_per_order: float = Field(..., description="Average spend per order")
    max_order_value: float = Field(..., description="Maximum order value")
    min_order_value: float = Field(..., description="Minimum order value")
    days_since_last_purchase: float = Field(..., description="Days since last purchase")
    customer_lifetime_days: float = Field(..., description="Customer lifetime in days")
    days_between_first_last: float = Field(..., description="Days between first and last purchase")
    order_frequency_days: float = Field(..., description="Average days between orders")
    avg_days_between_orders: float = Field(..., description="Average days between orders (alias)")
    avg_basket_size: float = Field(..., description="Average basket size")
    unique_products_bought: float = Field(..., description="Unique products bought")
    product_diversity: float = Field(..., description="Product diversity (unique/total)")
    pct_drink: float = Field(..., description="Percentage of drink purchases")
    pct_food: float = Field(..., description="Percentage of food purchases")
    pct_gift: float = Field(..., description="Percentage of gift purchases")
    pct_household: float = Field(..., description="Percentage of household purchases")
    pct_office: float = Field(..., description="Percentage of office purchases")
    pct_other: float = Field(..., description="Percentage of other purchases")
    category_entropy: float = Field(..., description="Category diversity (entropy)")
    first_purchase_season_encoded: float = Field(..., description="Season of first purchase (0-3)")
    top_country: str = Field(..., description="Most frequent country")

# ---------- 3. FastAPI app ----------
app = FastAPI(title="Boréal Marche Retention API", version="1.0.0")

@app.get("/health")
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
        X = X[feature_columns]
        prob = model.predict_proba(X)[0][1]
        decision = "Send coupon" if prob >= optimal_threshold else "No coupon"
        return {
            "probability": round(float(prob), 4),
            "threshold": optimal_threshold,
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