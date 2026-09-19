# ============================================================================
# tests/test_api.py – Contract tests for the FastAPI application
# ============================================================================

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

# ---------- Load feature columns from metadata ----------
METADATA_PATH = Path('artifacts/deployment_metadata.json')
with open(METADATA_PATH, 'r') as f:
    metadata = json.load(f)

FEATURE_COLUMNS = metadata['feature_columns']
N_FEATURES = len(FEATURE_COLUMNS)

# ---------- Build a valid customer sample dynamically ----------
def build_valid_customer():
    """Build a customer with all required features."""
    customer = {}
    for col in FEATURE_COLUMNS:
        if col == 'top_country':
            customer[col] = 'United Kingdom'
        elif col in ('first_purchase_date', 'last_purchase_date'):
            customer[col] = '2010-08-01'
        else:
            customer[col] = 1.0
    return customer

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
    assert data["n_features"] == N_FEATURES

# ---------- Test /predict with valid input ----------
def test_predict_valid():
    customer = build_valid_customer()
    response = client.post("/predict", json=customer)
    if response.status_code != 200:
        print("Error response:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert "probability" in data
    assert "decision" in data
    assert data["decision"] in ["Send coupon", "No coupon"]
    assert 0 <= data["probability"] <= 1

# ---------- Test /predict with extra field (should fail) ----------
def test_predict_extra_field_forbidden():
    customer = build_valid_customer()
    customer["invalid_field"] = "should fail"
    response = client.post("/predict", json=customer)
    assert response.status_code == 422  # Unprocessable Entity