# ============================================================================
# tests/test_api.py – Contract tests for the FastAPI application
# ============================================================================

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

# ---------- Test /health ----------
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

# ---------- Test /info ----------
def test_info():
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "model" in data
    assert "n_features" in data
    assert "optimal_threshold" in data
    assert data["n_features"] == 25

# ---------- Test /predict with valid input ----------
def test_predict_valid():
    customer = {
        "order_count": 5, "total_orders": 5, "total_items": 25,
        "avg_items_per_order": 5.0, "std_items_per_order": 0.5,
        "total_spend": 150.0, "avg_spend_per_order": 30.0,
        "max_order_value": 50.0, "min_order_value": 20.0,
        "days_since_last_purchase": 10, "customer_lifetime_days": 180,
        "days_between_first_last": 180, "order_frequency_days": 45.0,
        "avg_days_between_orders": 45.0, "avg_basket_size": 5.0,
        "unique_products_bought": 15, "product_diversity": 0.6,
        "pct_drink": 0.1, "pct_food": 0.5, "pct_gift": 0.2,
        "pct_household": 0.1, "pct_office": 0.05, "pct_other": 0.05,
        "category_entropy": 1.8, "first_purchase_season_encoded": 1,
        "top_country": "United Kingdom"
    }
    response = client.post("/predict", json=customer)
    assert response.status_code == 200
    data = response.json()
    assert "probability" in data
    assert "decision" in data
    assert data["decision"] in ["Send coupon", "No coupon"]
    assert 0 <= data["probability"] <= 1

# ---------- Test /predict with extra field (should fail) ----------
def test_predict_extra_field_forbidden():
    customer = {
        "order_count": 5,
        "invalid_field": "should fail"
    }
    response = client.post("/predict", json=customer)
    assert response.status_code == 422  # Unprocessable Entity