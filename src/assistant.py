# ============================================================================
# src/assistant.py – Bilingual Assistant with 3 Providers + Guardrails (v2)
# ============================================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import re
import json
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from src.assistant_tools import (
    policy_search, recommend_items, product_lookup, retention_score,
    PolicySearchOutput, RecommendOutput, ProductLookupOutput, RetentionOutput
)

# ---------- Supported providers ----------
Provider = Literal["rule", "openai", "ollama"]

# ---------- Guardrail config ----------
SIMILARITY_FLOOR = 0.3


# ---------- Response schema ----------
class AssistantResponse(BaseModel):
    answer: str
    provider: str
    grounded: bool
    citations: List[str] = []
    tool_used: Optional[str] = None
    refused: bool = False
    handoff: bool = False
    reason: Optional[str] = None


# ============================================================================
# Scope detection – refuse out-of-scope questions
# ============================================================================

OUT_OF_SCOPE_PATTERNS = [
    r"\bweather\b", r"\bmétéo\b", r"\btemps fait\b",
    r"\bstock market\b", r"\bbourse\b",
    r"\bpolitic", r"\bprime minister\b", r"\bpremier ministre\b",
    r"\bmedical\b", r"\bmédical\b",
    r"\bnews\b", r"\bnouvelles\b",
    r"\bwhat time\b", r"\bquelle heure\b",
    r"\bjoke\b", r"\bblague\b",
    r"\bpresident\b", r"\bprésident\b",
]

PERSONAL_DATA_PATTERNS = [
    r"\banother customer\b",
    r"\bother customer['s]?\b",
    r"\bcustomer \d+['s]? (email|address|phone)\b",
    r"\bun autre client\b",
]


def is_out_of_scope(question: str) -> bool:
    q = question.lower()
    for pat in OUT_OF_SCOPE_PATTERNS:
        if re.search(pat, q):
            return True
    return False


def is_personal_data_request(question: str) -> bool:
    q = question.lower()
    for pat in PERSONAL_DATA_PATTERNS:
        if re.search(pat, q):
            return True
    return False


# ============================================================================
# Tool routing – decide which tool (if any) should fire
# ============================================================================

def route_tool(question: str) -> Optional[str]:
    """Decide which tool to call based on the question."""
    q = question.lower()

    # Product lookup (do this BEFORE policy_search)
    if any(k in q for k in ["product", "produit", "stockcode", "price range",
                            "description of", "times ordered", "how many times",
                            "tell me about product", "fiche produit",
                            "quel est le produit", "info about product"]):
        # Distinguish from recommendations
        if "recommend" not in q and "suggest" not in q and "recommand" not in q:
            return "product_lookup"

    # Retention prediction
    if any(k in q for k in ["retention", "churn", "will i buy", "will this customer",
                            "rétention", "achètera", "reviendra"]):
        return "retention_score"

        # Recommendation
    if any(k in q for k in ["recommend", "suggest", "what else", "what goes with",
                            "goes well with", "add to my basket",
                            "recommand", "suggérer", "quoi acheter",
                            "qu'avec", "avec le produit", "avec 8"]):
        return "recommend_items"

    # Policy search (default for policy-like questions)
    if any(k in q for k in ["return", "delivery", "shipping", "allergen", "loyalty",
                            "privacy", "policy", "refund", "coupon", "provinces",
                            "data", "points", "discount",
                            "retour", "livraison", "allergène", "fidélité",
                            "confidentialité", "politique", "remboursement",
                            "données", "points de fidélité", "réduction"]):
        return "policy_search"

    return None


# ============================================================================
# Provider 1 – Rule baseline (no LLM)
# ============================================================================

def rule_provider(question: str, language: str = "en") -> AssistantResponse:
    """Answer using only rules and tools. No LLM."""

    # ---------- Guardrail: out of scope ----------
    if is_out_of_scope(question):
        msg = (
            "I'm sorry, that question is outside my scope. I can help with "
            "orders, returns, delivery, allergens, loyalty, and product questions."
        ) if language == "en" else (
            "Désolé, cette question est hors de mon champ. Je peux vous aider "
            "avec les commandes, retours, livraisons, allergènes, fidélité et produits."
        )
        return AssistantResponse(
            answer=msg, provider="rule", grounded=False, refused=True, reason="out_of_scope"
        )

    # ---------- Guardrail: personal data ----------
    if is_personal_data_request(question):
        msg = (
            "I cannot share another customer's personal information. "
            "Please contact our privacy officer at privacy@borealmarche.ca."
        ) if language == "en" else (
            "Je ne peux pas partager les informations personnelles d'un autre client. "
            "Contactez notre responsable de la confidentialité à privacy@borealmarche.ca."
        )
        return AssistantResponse(
            answer=msg, provider="rule", grounded=False, refused=True, reason="privacy"
        )

    # ---------- Route to a tool ----------
    tool = route_tool(question)

    if tool == "policy_search":
        result = policy_search(question, top_k=3)
        if not result.found:
            msg = (
                "I couldn't find a policy that answers this question. "
                "Let me connect you with a human agent."
            ) if language == "en" else (
                "Je n'ai pas trouvé de politique qui répond à cette question. "
                "Je vais vous mettre en contact avec un agent humain."
            )
            return AssistantResponse(
                answer=msg, provider="rule", grounded=False, handoff=True,
                tool_used="policy_search", reason="no_relevant_chunk"
            )
        top = result.results[0]
        answer = (
            f"According to {top.source}:\n\n{top.text}\n\n"
            f"(Source: {top.source}, similarity: {top.score:.2f})"
        )
        return AssistantResponse(
            answer=answer,
            provider="rule",
            grounded=True,
            citations=[top.source],
            tool_used="policy_search"
        )

    if tool == "recommend_items":
        basket = _extract_basket(question) or ["84997C"]
        result = recommend_items(basket, n=3)
        if result.error:
            return AssistantResponse(
                answer=f"Sorry, recommendation service is unavailable: {result.error}",
                provider="rule", grounded=False, tool_used="recommend_items"
            )
        if not result.recommendations:
            msg = "I couldn't find recommendations for that basket."
            return AssistantResponse(
                answer=msg, provider="rule", grounded=False, tool_used="recommend_items"
            )
        lines = [f"Given your basket ({', '.join(basket)}), you might like:"]
        for rec in result.recommendations:
            lines.append(
                f"  • {rec.item} (because you added {', '.join(rec.because)}; lift={rec.lift:.1f})"
            )
        return AssistantResponse(
            answer="\n".join(lines), provider="rule", grounded=True,
            tool_used="recommend_items"
        )

    if tool == "product_lookup":
        code = _extract_stock_code(question) or "84997C"
        result = product_lookup(code)
        if not result.found:
            return AssistantResponse(
                answer=result.message or f"Product {code} not found.",
                provider="rule", grounded=False, tool_used="product_lookup"
            )
        p = result.product
        answer = (
            f"Product {p.stock_code}: {p.description}\n"
            f"Average price: ${p.avg_price}\n"
            f"Price range: ${p.min_price}–${p.max_price}\n"
            f"Times ordered: {p.times_ordered}"
        )
        return AssistantResponse(
            answer=answer, provider="rule", grounded=True, tool_used="product_lookup"
        )

    if tool == "retention_score":
        msg = (
            "To compute a retention score, I need the customer's full 25-feature profile. "
            "Please use the /predict endpoint directly."
        ) if language == "en" else (
            "Pour calculer un score de rétention, j'ai besoin du profil complet du client. "
            "Veuillez utiliser directement l'endpoint /predict."
        )
        return AssistantResponse(
            answer=msg, provider="rule", grounded=False, tool_used="retention_score"
        )

    # ---------- Default: try policy search ----------
    result = policy_search(question, top_k=1)
    if result.found:
        top = result.results[0]
        return AssistantResponse(
            answer=f"According to {top.source}:\n\n{top.text}",
            provider="rule",
            grounded=True,
            citations=[top.source],
            tool_used="policy_search"
        )

    msg = (
        "I'm not sure how to answer that. Could you rephrase, or ask about "
        "returns, delivery, allergens, loyalty, or product recommendations?"
    ) if language == "en" else (
        "Je ne suis pas sûr de pouvoir répondre. Pouvez-vous reformuler, ou "
        "poser une question sur les retours, livraisons, allergènes, fidélité ou produits ?"
    )
    return AssistantResponse(answer=msg, provider="rule", grounded=False, reason="no_route")


# ============================================================================
# Provider 2 – OpenAI (optional)
# ============================================================================

def openai_provider(question: str, language: str = "en") -> AssistantResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        r = rule_provider(question, language)
        r.reason = "no_openai_key"
        return r

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        ctx = policy_search(question, top_k=3)
        if not ctx.found:
            msg = (
                "I couldn't find a policy that answers this question. "
                "Let me connect you with a human agent."
            ) if language == "en" else (
                "Je n'ai pas trouvé de politique qui répond à cette question. "
                "Je vais vous mettre en contact avec un agent humain."
            )
            return AssistantResponse(
                answer=msg, provider="openai", grounded=False, handoff=True,
                reason="no_relevant_chunk"
            )

        context_text = "\n\n".join(
            f"[{c.source}]\n{c.text}" for c in ctx.results
        )

        system = (
            "You are a bilingual customer service assistant for Boréal Marché, "
            "a Quebec online grocery. Answer ONLY using the provided context. "
            "Always cite the source document. If the answer is not in the context, "
            "say you don't know and offer a human handoff. Answer in the same "
            "language as the question."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}"}
            ],
            temperature=0.2,
            max_tokens=400
        )

        answer = response.choices[0].message.content.strip()
        return AssistantResponse(
            answer=answer,
            provider="openai",
            grounded=True,
            citations=[c.source for c in ctx.results],
            tool_used="policy_search"
        )

    except Exception as e:
        r = rule_provider(question, language)
        r.reason = f"openai_error: {e}"
        return r


# ============================================================================
# Provider 3 – Ollama (local, optional)
# ============================================================================

def ollama_provider(question: str, language: str = "en") -> AssistantResponse:
    try:
        import httpx

        ctx = policy_search(question, top_k=3)
        if not ctx.found:
            msg = (
                "I couldn't find a policy that answers this question. "
                "Let me connect you with a human agent."
            ) if language == "en" else (
                "Je n'ai pas trouvé de politique qui répond à cette question. "
                "Je vais vous mettre en contact avec un agent humain."
            )
            return AssistantResponse(
                answer=msg, provider="ollama", grounded=False, handoff=True
            )

        context_text = "\n\n".join(f"[{c.source}]\n{c.text}" for c in ctx.results)

        prompt = (
            "You are a bilingual customer service assistant for Boréal Marché. "
            "Answer ONLY using the context below. Cite the source. "
            "Answer in the same language as the question.\n\n"
            f"Context:\n{context_text}\n\nQuestion: {question}\nAnswer:"
        )

        r = httpx.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=60.0
        )
        r.raise_for_status()
        answer = r.json().get("response", "").strip()

        return AssistantResponse(
            answer=answer,
            provider="ollama",
            grounded=True,
            citations=[c.source for c in ctx.results],
            tool_used="policy_search"
        )

    except Exception as e:
        r = rule_provider(question, language)
        r.reason = f"ollama_error: {e}"
        return r


# ============================================================================
# Public API – main entry point
# ============================================================================

def ask(question: str, provider: Provider = "rule", language: str = "en") -> AssistantResponse:
    if provider == "rule":
        return rule_provider(question, language)
    elif provider == "openai":
        return openai_provider(question, language)
    elif provider == "ollama":
        return ollama_provider(question, language)
    else:
        return AssistantResponse(
            answer=f"Unknown provider: {provider}",
            provider=provider,
            grounded=False,
            refused=True,
            reason="invalid_provider"
        )


# ============================================================================
# Helpers
# ============================================================================

def _extract_basket(question: str) -> Optional[List[str]]:
    codes = re.findall(r'\b[A-Z0-9]{5,8}\b', question)
    return codes if codes else None


def _extract_stock_code(question: str) -> Optional[str]:
    codes = re.findall(r'\b[A-Z0-9]{5,8}\b', question)
    return codes[0] if codes else None