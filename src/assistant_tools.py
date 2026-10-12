# ============================================================================
# src/assistant_tools.py – 4 Typed Tools for Head C
# ============================================================================
# Each tool returns a validated Pydantic model.
# - policy_search: retrieves chunks from the FAISS index
# - retention_score: calls the /predict endpoint (Head A)
# - recommend_items: calls the /recommend endpoint (Head B)
# - product_lookup: looks up product metadata from a catalog
# ============================================================================

import os
import json
from pathlib import Path
from typing import List, Optional

import numpy as np
import httpx
import faiss
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

# ---------- Paths ----------
ARTIFACTS_DIR = Path(__file__).parent.parent / 'artifacts'
INDEX_PATH = ARTIFACTS_DIR / 'faiss_index' / 'index.faiss'
CHUNKS_PATH = ARTIFACTS_DIR / 'faiss_index' / 'chunks.json'
PRODUCT_CATALOG_PATH = ARTIFACTS_DIR / 'product_catalog.json'

# ---------- Config ----------
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

# ---------- Lazy-loaded globals ----------
_embedding_model = None
_faiss_index = None
_chunks = None


def _load_index():
    """Lazy-load the FAISS index and chunks."""
    global _embedding_model, _faiss_index, _chunks
    if _faiss_index is None:
        _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        _faiss_index = faiss.read_index(str(INDEX_PATH))
        with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:
            _chunks = json.load(f)['chunks']


# ============================================================================
# Tool 1 – Policy Search
# ============================================================================

class PolicySearchInput(BaseModel):
    query: str = Field(..., description="Search query in French or English")
    top_k: int = Field(3, ge=1, le=10, description="Number of chunks to return")


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
    """Search policy documents for relevant chunks."""
    _load_index()

    q_emb = _embedding_model.encode([query], convert_to_numpy=True).astype('float32')
    faiss.normalize_L2(q_emb)

    scores, indices = _faiss_index.search(q_emb, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_chunks):
            continue
        chunk = _chunks[idx]
        results.append(PolicyChunk(
            text=chunk['text'],
            source=chunk['source'],
            score=float(score)
        ))

    found = len(results) > 0 and results[0].score > 0.3
    message = None
    if not found:
        message = "No relevant policy document found above the similarity threshold."

    return PolicySearchOutput(
        query=query,
        results=results,
        found=found,
        message=message
    )


# ============================================================================
# Tool 2 – Retention Score (calls Head A)
# ============================================================================

class RetentionInput(BaseModel):
    customer_features: dict = Field(..., description="25-feature dict for the customer")


class RetentionOutput(BaseModel):
    probability: Optional[float] = None
    threshold: Optional[float] = None
    decision: Optional[str] = None
    error: Optional[str] = None


def retention_score(customer_features: dict) -> RetentionOutput:
    """Call the /predict endpoint to get a retention probability."""
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(f"{API_BASE_URL}/predict", json=customer_features)
            if r.status_code == 200:
                data = r.json()
                return RetentionOutput(
                    probability=data.get('probability'),
                    threshold=data.get('threshold'),
                    decision=data.get('decision')
                )
            else:
                return RetentionOutput(error=f"API returned {r.status_code}: {r.text}")
    except Exception as e:
        return RetentionOutput(error=str(e))


# ============================================================================
# Tool 3 – Recommend Items (calls Head B)
# ============================================================================

class RecommendInput(BaseModel):
    basket: List[str] = Field(..., description="List of StockCodes in the basket")
    n: int = Field(5, ge=1, le=20, description="Number of recommendations")


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
    """Call the /recommend endpoint to get product recommendations."""
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(f"{API_BASE_URL}/recommend", json={"basket": basket, "n": n})
            if r.status_code == 200:
                data = r.json()
                recs = [
                    RecommendationItem(
                        item=rec['item'],
                        lift=rec['lift'],
                        confidence=rec['confidence'],
                        because=rec['because']
                    )
                    for rec in data.get('recommendations', [])
                ]
                return RecommendOutput(
                    strategy=data.get('strategy'),
                    recommendations=recs,
                    message=data.get('message')
                )
            else:
                return RecommendOutput(error=f"API returned {r.status_code}: {r.text}")
    except Exception as e:
        return RecommendOutput(error=str(e))


# ============================================================================
# Tool 4 – Product Lookup
# ============================================================================

class ProductLookupInput(BaseModel):
    stock_code: str = Field(..., description="The product StockCode")


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
    """Look up product metadata from the catalog."""
    if not PRODUCT_CATALOG_PATH.exists():
        return ProductLookupOutput(
            found=False,
            message="Product catalog not available. Run build_product_catalog.py first."
        )

    with open(PRODUCT_CATALOG_PATH, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    product = catalog.get(stock_code)
    if product is None:
        return ProductLookupOutput(
            found=False,
            message=f"Product '{stock_code}' not found in catalog."
        )

    return ProductLookupOutput(
        found=True,
        product=ProductInfo(**product)
    )


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Head C – Tools Self-Test")
    print("=" * 60)

    # Test policy_search
    print("\n🔍 Test 1: policy_search")
    r1 = policy_search("Can I return an opened item?", top_k=2)
    print(f"   Found: {r1.found}")
    if r1.results:
        print(f"   Top result: {r1.results[0].text[:100]}...")
        print(f"   Source: {r1.results[0].source}, score={r1.results[0].score:.3f}")

    # Test recommend_items (requires API running)
    print("\n🔍 Test 2: recommend_items")
    r2 = recommend_items(["84997C"], n=3)
    if r2.error:
        print(f"   Error: {r2.error}")
    else:
        print(f"   Strategy: {r2.strategy}, count: {len(r2.recommendations)}")

    # Test product_lookup
    print("\n🔍 Test 3: product_lookup")
    r3 = product_lookup("84997C")
    print(f"   Found: {r3.found}, message: {r3.message}")

    print("\n✅ Self-test complete!")