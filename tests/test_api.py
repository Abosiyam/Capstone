# ============================================================================
# tests/test_api.py – Contract tests for the FastAPI application
# ============================================================================

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app import app

# ---------- Load feature columns from metadata ----------
METADATA_PATH = Path('artifacts/deployment_metadata.json')
with open(METADATA_PATH, 'r') as f:
    metadata = json.load(f)

FEATURE_COLUMNS = metadata['feature_columns']
N_FEATURES = len(FEATURE_COLUMNS)


@pytest.fixture(scope="module")
def client():
    """TestClient with lifespan triggered."""
    with TestClient(app) as c:
        yield c


def build_valid_customer():
    customer = {}
    for col in FEATURE_COLUMNS:
        if col == 'top_country':
            customer[col] = 'United Kingdom'
        elif col in ('first_purchase_date', 'last_purchase_date'):
            customer[col] = '2010-08-01'
        else:
            customer[col] = 1.0
    return customer


# ============================================================================
# Head A – Retention Prediction Tests
# ============================================================================

def test_health(client):
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_info(client):
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "retention_model" in data
    assert "n_features" in data
    assert data["n_features"] == N_FEATURES
    assert "recommendation_engine" in data


def test_predict_valid(client):
    customer = build_valid_customer()
    response = client.post("/predict", json=customer)
    assert response.status_code == 200
    data = response.json()
    assert "probability" in data
    assert "decision" in data
    assert data["decision"] in ["Send coupon", "No coupon"]
    assert 0 <= data["probability"] <= 1


def test_predict_extra_field_forbidden(client):
    customer = build_valid_customer()
    customer["invalid_field"] = "should fail"
    response = client.post("/predict", json=customer)
    assert response.status_code == 422


# ============================================================================
# Head B – Recommendation Tests
# ============================================================================

def test_recommend_valid(client):
    response = client.post("/recommend", json={"basket": ["84997C"], "n": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["strategy"] in ["rules", "empty_basket", "no_match"]
    if data["strategy"] == "rules":
        assert len(data["recommendations"]) > 0
        first = data["recommendations"][0]
        assert "item" in first
        assert "lift" in first
        assert "because" in first


def test_recommend_empty_basket(client):
    response = client.post("/recommend", json={"basket": [], "n": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["strategy"] == "empty_basket"
    assert data["recommendations"] == []
    assert "message" in data


def test_recommend_no_match(client):
    response = client.post("/recommend", json={"basket": ["NONEXISTENT_XYZ"], "n": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["strategy"] == "no_match"
    assert data["recommendations"] == []


def test_recommend_extra_field_forbidden(client):
    response = client.post("/recommend", json={"basket": ["84997C"], "n": 5, "invalid": "fail"})
    assert response.status_code == 422