# ============================================================================
# app.py – FastAPI for Boréal Marché (Head A + B + C) with Logging
# ============================================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional
import json
from contextlib import asynccontextmanager

from src.recommendation_engine import RecommendationEngine
from src.prediction_logger import log_request, Timer

# ---------- Global objects ----------
ml_bundle = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("🚀 Starting Boréal Marché API (Head A + B + C)")
    print("=" * 60)

    MODEL_PATH = Path('artifacts/final_model.joblib')
    METADATA_PATH = Path('artifacts/deployment_metadata.json')

    ml_bundle['model'] = joblib.load(MODEL_PATH)
    with open(METADATA_PATH, 'r') as f:
        metadata = json.load(f)

    ml_bundle['feature_columns'] = metadata['feature_columns']
    ml_bundle['optimal_threshold'] = metadata['optimal_threshold']

    print(f"✅ Model loaded: {len(ml_bundle['feature_columns'])} features, "
          f"threshold={ml_bundle['optimal_threshold']}")

    ml_bundle['engine'] = RecommendationEngine()
    print("✅ Recommendation engine loaded")
    print("=" * 60)

    yield

    print("🛑 Shutting down...")


app = FastAPI(
    title="Boréal Marche Retention + Recommendation + Assistant API",
    version="1.4.1",
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


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(..., description="Question in French or English")
    provider: Literal["rule", "openai", "ollama"] = "rule"
    language: Literal["en", "fr"] = "en"


# ---------- Endpoints ----------
@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {
        "message": "Boréal Marché API (Head A + B + C)",
        "docs": "/docs",
        "status": "/status",
        "predict": "/predict",
        "recommend": "/recommend",
        "chat": "/chat",
        "version": "1.4.1"
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
        "recommendation_engine": ml_bundle['engine'].stats(),
        "assistant_providers": ["rule", "openai", "ollama"]
    }


@app.post("/predict")
async def predict(customer: CustomerFeatures):
    input_data = customer.model_dump()
    timer = Timer()
    timer.__enter__()
    status_code = 200
    error_msg = None
    result = None

    try:
        X = pd.DataFrame([input_data])
        missing = [c for c in ml_bundle['feature_columns'] if c not in X.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        X = X[ml_bundle['feature_columns']]
        prob = ml_bundle['model'].predict_proba(X)[0][1]
        decision = "Send coupon" if prob >= ml_bundle['optimal_threshold'] else "No coupon"

        result = {
            "probability": round(float(prob), 4),
            "threshold": ml_bundle['optimal_threshold'],
            "decision": decision
        }
    except Exception as e:
        status_code = 400
        error_msg = str(e)
    finally:
        timer.__exit__(None, None, None)
        log_request("/predict", input_data, result, timer.latency_ms, status_code, error_msg)

    if error_msg:
        raise HTTPException(status_code=400, detail=error_msg)
    return result


@app.post("/predict/batch")
async def predict_batch(customers: List[CustomerFeatures]):
    inputs = [c.model_dump() for c in customers]
    timer = Timer()
    timer.__enter__()
    status_code = 200
    error_msg = None
    results = None

    try:
        results = []
        for data in inputs:
            X = pd.DataFrame([data])[ml_bundle['feature_columns']]
            prob = ml_bundle['model'].predict_proba(X)[0][1]
            decision = "Send coupon" if prob >= ml_bundle['optimal_threshold'] else "No coupon"
            results.append({"probability": round(float(prob), 4), "decision": decision})
    except Exception as e:
        status_code = 400
        error_msg = str(e)
    finally:
        timer.__exit__(None, None, None)
        log_request("/predict/batch", {"count": len(inputs)},
                    {"count": len(results)} if results else None,
                    timer.latency_ms, status_code, error_msg)

    if error_msg:
        raise HTTPException(status_code=400, detail=error_msg)
    return {"results": results}


@app.post("/recommend")
async def recommend(request: RecommendRequest):
    input_data = request.model_dump()
    timer = Timer()
    timer.__enter__()
    status_code = 200
    error_msg = None
    result = None

    try:
        result = ml_bundle['engine'].recommend(request.basket, n=request.n)
    except Exception as e:
        status_code = 400
        error_msg = str(e)
    finally:
        timer.__exit__(None, None, None)
        log_request("/recommend", input_data, result, timer.latency_ms, status_code, error_msg)

    if error_msg:
        raise HTTPException(status_code=400, detail=error_msg)
    return result


@app.post("/chat")
async def chat(request: ChatRequest):
    input_data = request.model_dump()
    timer = Timer()
    timer.__enter__()
    status_code = 200
    error_msg = None
    response = None

    try:
        from src.assistant import ask as assistant_ask
        response = assistant_ask(
            question=request.question,
            provider=request.provider,
            language=request.language
        )
    except Exception as e:
        status_code = 400
        error_msg = str(e)
    finally:
        timer.__exit__(None, None, None)
        log_request("/chat", input_data,
                    response.model_dump() if response else None,
                    timer.latency_ms, status_code, error_msg)

    if error_msg:
        raise HTTPException(status_code=400, detail=error_msg)
    return response


# ---------- Run ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)