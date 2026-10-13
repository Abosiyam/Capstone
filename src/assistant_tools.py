# ============================================================================
# src/assistant_tools.py – 4 Typed Tools (TF-IDF version, low memory)
# ============================================================================

import os
import json
import pickle
from pathlib import Path
from typing import List, Optional

import httpx
from pydantic import BaseModel, Field

# ---------- Paths ----------
ARTIFACTS_DIR = Path(__file__).parent.parent / 'artifacts'
TFIDF_INDEX_PATH = ARTIFACTS_DIR / 'tfidf_index.pkl'
PRODUCT_CATALOG_PATH = ARTIFACTS_DIR / 'product_catalog.json'

# ---------- Config ----------
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

# ---------- Lazy-loaded globals ----------
_tfidf_data = None


def _load_index():
    """Lazy-load the TF-IDF vectorizer and matrix."""
    global _tfidf_data
    if _tfidf_data is None:
        with open(TFIDF_INDEX_PATH, 'rb') as f:
            _tfidf_data = pickle.load(f)


# ============================================================================
# Tool 1 – Policy Search
# ============================================================================

class PolicySearchInput(BaseModel):
    query: str
    top_k: int = Field(3, ge=1, le=10)


class PolicyChunk(BaseModel):
    text: str
    source: str
    score: float


class PolicySearchOutput(BaseModel):
    query: str
    results: List[PolicyChunk]
    found: bool
    message: Optional[str] = None


def policy_search(query: str, top_k: int = 3) -> PolicySearchOutput:
    """Search policy documents using TF-IDF cosine similarity."""
    _load_index()

    vectorizer = _tfidf_data['vectorizer']
    matrix = _tfidf_data['matrix']
    chunks = _tfidf_data['chunks']

    from sklearn.metrics.pairwise import cosine_similarity

    q_vec = vectorizer.transform([query])
    scores = cosine_similarity(q_vec, matrix).flatten()

    top_indices = scores.argsort()[::-1][:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] < 0.05:
            continue
        chunk = chunks[idx]
        results.append(PolicyChunk(
            text=chunk['text'],
            source=chunk['source'],
            score=float(scores[idx])
        ))

    found = len(results) > 0
    message = None if found else "No relevant policy document found."

    return PolicySearchOutput(query=query, results=results, found=found, message=message)


# ============================================================================
# Tool 2 – Retention Score
# ============================================================================

class RetentionInput(BaseModel):
    customer_features: dict


class RetentionOutput(BaseModel):
    probability: Optional[float] = None
    threshold: Optional[float] = None
    decision: Optional[str] = None
    error: Optional[str] = None


def retention_score(customer_features: dict) -> RetentionOutput:
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(f"{API_BASE_URL}/predict", json=customer_features)
            if r.status_code == 200:
                data = r.json()
                return RetentionOutput(**{k: data.get(k) for k in ('probability', 'threshold', 'decision')})
            return RetentionOutput(error=f"API returned {r.status_code}")
    except Exception as e:
        return RetentionOutput(error=str(e))


# ============================================================================
# Tool 3 – Recommend Items
# ============================================================================

class RecommendInput(BaseModel):
    basket: List[str]
    n: int = Field(5, ge=1, le=20)


class RecommendationItem(BaseModel):
    item: str
    lift: float
    confidence: float
    because: List[str]


class RecommendOutput(BaseModel):
    strategy: Optional[str] = None
    recommendations: List[RecommendationItem] = []
    message: Optional[str] = None
    error: Optional[str] = None


def recommend_items(basket: List[str], n: int = 5) -> RecommendOutput:
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(f"{API_BASE_URL}/recommend", json={"basket": basket, "n": n})
            if r.status_code == 200:
                data = r.json()
                recs = [RecommendationItem(**rec) for rec in data.get('recommendations', [])]
                return RecommendOutput(strategy=data.get('strategy'), recommendations=recs, message=data.get('message'))
            return RecommendOutput(error=f"API returned {r.status_code}")
    except Exception as e:
        return RecommendOutput(error=str(e))


# ============================================================================
# Tool 4 – Product Lookup
# ============================================================================

class ProductLookupInput(BaseModel):
    stock_code: str


class ProductInfo(BaseModel):
    stock_code: str
    description: Optional[str] = None
    avg_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    total_quantity: Optional[int] = None
    times_ordered: Optional[int] = None


class ProductLookupOutput(BaseModel):
    found: bool
    product: Optional[ProductInfo] = None
    message: Optional[str] = None


def product_lookup(stock_code: str) -> ProductLookupOutput:
    if not PRODUCT_CATALOG_PATH.exists():
        return ProductLookupOutput(found=False, message="Product catalog not available.")

    with open(PRODUCT_CATALOG_PATH, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    product = catalog.get(stock_code)
    if product is None:
        return ProductLookupOutput(found=False, message=f"Product '{stock_code}' not found.")

    return ProductLookupOutput(found=True, product=ProductInfo(**product))