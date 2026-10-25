# ============================================================================
# frontend/app.py – Boréal Marché Interactive Frontend
# ============================================================================
# 5 sections: Prediction, Basket & Recommendations, Assistant, Monitoring, About
# Language toggle: English / French
# ============================================================================

import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# ---------- Config ----------
API_BASE = "https://boreal-marche-api-latest-1.onrender.com"
DASHBOARD_URL = "https://bibe6vpgewedpjfv7emsae.streamlit.app"

st.set_page_config(
    page_title="Boréal Marché",
    page_icon="🛒",
    layout="wide"
)

# ---------- Language dictionary ----------
T = {
    "en": {
        "title": "Boréal Marché – Customer Intelligence Platform",
        "subtitle": "An end-to-end AI system for retention, recommendations, and support",
        "section": "Section",
        "prediction": "🎯 Retention Prediction",
        "basket": "🧺 Basket & Recommendations",
        "assistant": "💬 Assistant",
        "monitoring": "📊 Monitoring",
        "about": "ℹ️ About",
        "customer_features": "Customer Features",
        "predict": "Predict",
        "probability": "Probability",
        "threshold": "Threshold",
        "decision": "Decision",
        "send_coupon": "✅ Send coupon",
        "no_coupon": "❌ No coupon",
        "basket_input": "Enter StockCodes (one per line)",
        "get_recommendations": "Get Recommendations",
        "recommendations": "Recommendations",
        "ask_question": "Ask a question (EN or FR)",
        "send": "Send",
        "answer": "Answer",
        "provider": "Provider",
        "language": "Language",
        "model_info": "Model Information",
        "privacy": "Privacy Notice",
        "architecture": "Architecture",
        "loading": "Loading...",
        "error": "Error",
    },
    "fr": {
        "title": "Boréal Marché – Plateforme d'Intelligence Client",
        "subtitle": "Un système d'IA de bout en bout pour la rétention, les recommandations et le support",
        "section": "Section",
        "prediction": "🎯 Prédiction de rétention",
        "basket": "🧺 Panier et recommandations",
        "assistant": "💬 Assistant",
        "monitoring": "📊 Surveillance",
        "about": "ℹ️ À propos",
        "customer_features": "Caractéristiques du client",
        "predict": "Prédire",
        "probability": "Probabilité",
        "threshold": "Seuil",
        "decision": "Décision",
        "send_coupon": "✅ Envoyer un coupon",
        "no_coupon": "❌ Pas de coupon",
        "basket_input": "Entrez les codes produits (un par ligne)",
        "get_recommendations": "Obtenir des recommandations",
        "recommendations": "Recommandations",
        "ask_question": "Posez une question (FR ou EN)",
        "send": "Envoyer",
        "answer": "Réponse",
        "provider": "Fournisseur",
        "language": "Langue",
        "model_info": "Informations sur le modèle",
        "privacy": "Avis de confidentialité",
        "architecture": "Architecture",
        "loading": "Chargement...",
        "error": "Erreur",
    }
}

# ---------- Session state ----------
if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "basket" not in st.session_state:
    st.session_state.basket = []

t = T[st.session_state.lang]


# ============================================================================
# Sidebar
# ============================================================================
with st.sidebar:
    st.markdown("### 🌐 Language / Langue")
    lang_choice = st.radio(
        "Choose language",
        ["English", "Français"],
        index=0 if st.session_state.lang == "en" else 1,
        label_visibility="collapsed"
    )
    st.session_state.lang = "en" if lang_choice == "English" else "fr"
    t = T[st.session_state.lang]

    st.markdown("---")
    st.markdown(f"### {t['section']}")
    section = st.radio(
        "Navigation",
        [t['prediction'], t['basket'], t['assistant'], t['monitoring'], t['about']],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption(f"API: {API_BASE[:40]}...")


# ============================================================================
# Header
# ============================================================================
st.title(t['title'])
st.markdown(f"*{t['subtitle']}*")
st.markdown("---")


# ============================================================================
# Helper functions
# ============================================================================
def call_api(endpoint, method="GET", data=None, timeout=60):
    """Call the API and return the JSON response or an error dict."""
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=timeout)
        else:
            r = requests.post(url, json=data, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Section 1 – Prediction
# ============================================================================
if section == t['prediction']:
    st.header(t['prediction'])

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(t['customer_features'])
        order_count = st.slider("order_count", 1, 50, 5)
        total_spend = st.slider("total_spend", 10, 5000, 150)
        days_since = st.slider("days_since_last_purchase", 1, 365, 30)
        unique_products = st.slider("unique_products_bought", 1, 200, 15)
        avg_basket = st.slider("avg_basket_size", 1.0, 50.0, 5.0)

    with col2:
        st.subheader("⚙️ What-if Controls")
        st.caption("Change the sliders on the left to see the probability update live.")

        # Build payload
        payload = {
            "order_count": float(order_count),
            "total_orders": float(order_count),
            "total_items": float(order_count * avg_basket),
            "avg_items_per_order": float(avg_basket),
            "std_items_per_order": 0.5,
            "total_spend": float(total_spend),
            "avg_spend_per_order": float(total_spend) / max(order_count, 1),
            "max_order_value": float(total_spend) / max(order_count, 1) * 1.5,
            "min_order_value": float(total_spend) / max(order_count, 1) * 0.5,
            "first_purchase_date": "2010-08-01",
            "last_purchase_date": "2010-08-15",
            "days_since_last_purchase": float(days_since),
            "customer_lifetime_days": 180.0,
            "order_frequency_days": 45.0,
            "avg_days_between_orders": 45.0,
            "avg_basket_size": float(avg_basket),
            "unique_products_bought": float(unique_products),
            "product_diversity": float(unique_products) / max(float(order_count * avg_basket), 1),
            "pct_drink": 0.1,
            "pct_food": 0.5,
            "pct_gift": 0.2,
            "pct_household": 0.1,
            "pct_office": 0.05,
            "pct_other": 0.05,
            "top_country": "United Kingdom"
        }

        if st.button(t['predict'], type="primary"):
            with st.spinner(t['loading']):
                result = call_api("/predict", "POST", payload)
            if "error" in result:
                st.error(f"{t['error']}: {result['error']}")
            else:
                prob = result.get('probability', 0)
                decision = result.get('decision', '')
                threshold = result.get('threshold', 0.5)

                st.metric(t['probability'], f"{prob:.2%}")
                st.metric(t['threshold'], f"{threshold}")
                if decision == "Send coupon":
                    st.success(t['send_coupon'])
                else:
                    st.warning(t['no_coupon'])


# ============================================================================
# Section 2 – Basket & Recommendations
# ============================================================================
elif section == t['basket']:
    st.header(t['basket'])

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🛒 Your Basket")
        
        # Load product catalog to map names to codes
        import json
        from pathlib import Path
        catalog_path = Path(__file__).parent.parent / 'artifacts' / 'product_catalog.json'
        catalog = {}
        if catalog_path.exists():
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
                
        # Create options for dropdown (Name (Code))
        product_options = {f"{v['description']} ({k})": k for k, v in catalog.items()}
        
        # Default selection (84997C = BLUE 3 PIECE MINI DOTS CUTLERY SET)
        default_label = [label for label, code in product_options.items() if code == "84997C"]
        
        selected_products = st.multiselect(
            "Select products to add to your basket:",
            options=list(product_options.keys()),
            default=default_label if default_label else []
        )
        
        n_recs = st.slider("Number of recommendations", 1, 10, 5)

        if st.button(t['get_recommendations'], type="primary"):
            # Convert selected product names back to StockCodes
            basket = [product_options[p] for p in selected_products]
    with col2:
        st.subheader("💡 " + t['recommendations'])
        if "recs" in st.session_state:
            result = st.session_state.recs
            strategy = result.get('strategy')
            st.info(f"Strategy: **{strategy}**")

            recs = result.get('recommendations', [])
            if not recs:
                st.warning(result.get('message', 'No recommendations available.'))
            for rec in recs:
                with st.container():
                    st.markdown(f"### 📦 `{rec['item']}`")
                    st.markdown(f"**Lift:** {rec['lift']:.2f} | **Confidence:** {rec['confidence']:.2%}")
                    st.caption(f"Because you added: {', '.join(rec['because'])}")
                    st.markdown("---")


# ============================================================================
# Section 3 – Assistant
# ============================================================================
elif section == t['assistant']:
    st.header(t['assistant'])

    provider = st.selectbox(t['provider'], ["rule", "openai", "ollama"])
    lang_choice = st.selectbox("Assistant language", ["en", "fr"], index=0 if st.session_state.lang == "en" else 1)

    st.markdown("### " + t['ask_question'])

    user_input = st.text_input("", key="chat_input", placeholder="e.g., What is your return policy?")

    col1, col2 = st.columns([1, 5])
    with col1:
        send = st.button(t['send'], type="primary")
    with col2:
        if st.button("Clear history"):
            st.session_state.chat_history = []
            st.rerun()

    if send and user_input:
        with st.spinner(t['loading']):
            result = call_api("/chat", "POST", {
                "question": user_input,
                "provider": provider,
                "language": lang_choice
            }, timeout=90)

        if "error" in result:
            st.error(f"{t['error']}: {result['error']}")
        else:
            st.session_state.chat_history.append({
                "question": user_input,
                "answer": result.get('answer', ''),
                "citations": result.get('citations', []),
                "grounded": result.get('grounded', False),
                "refused": result.get('refused', False),
                "provider": result.get('provider', '')
            })

    # Display chat history
    if st.session_state.chat_history:
        st.markdown("### " + t['answer'])
        for i, msg in enumerate(reversed(st.session_state.chat_history)):
            with st.container():
                st.markdown(f"**🧑 You:** {msg['question']}")
                st.markdown(f"**🤖 Assistant:** {msg['answer']}")
                if msg['citations']:
                    st.caption(f"📚 Sources: {', '.join(msg['citations'])}")
                if msg['refused']:
                    st.warning("⚠️ Refused (out of scope or privacy)")
                elif msg['grounded']:
                    st.success(f"✅ Grounded | Provider: {msg['provider']}")
                st.markdown("---")


# ============================================================================
# Section 4 – Monitoring
# ============================================================================
elif section == t['monitoring']:
    st.header(t['monitoring'])

    st.markdown("### Live Dashboard")
    st.markdown(f"The monitoring dashboard is available at: **[{DASHBOARD_URL}]({DASHBOARD_URL})**")

    st.markdown("""
    The dashboard shows:
    - **Total requests** and **error count**
    - **Average latency** in milliseconds
    - **Coupon rate** (% of customers receiving a coupon)
    - **Prediction distribution**
    - **Latency over time**
    - **Alerts** (traffic-light status)
    """)

    st.info("💡 Tip: The dashboard may take ~30 seconds to wake up if it has been idle.")


# ============================================================================
# Section 5 – About
# ============================================================================
elif section == t['about']:
    st.header(t['about'])

    st.markdown(f"## {t['model_info']}")
    if st.button("Load Model Info"):
        with st.spinner(t['loading']):
            info = call_api("/info", "GET")
        if "error" in info:
            st.error(f"{t['error']}: {info['error']}")
        else:
            st.json(info)

    st.markdown(f"## {t['architecture']}")
    st.markdown("""
""")

st.markdown(f"## {t['privacy']}")
st.markdown("""
**How we use your data:**
- To predict whether you might like a discount coupon.
- To recommend products you might enjoy.
- To answer your questions.

**Your rights (Law 25):**
- Ask us to explain any decision about you.
- Request a human review of any automated decision.
- Opt out of personalised recommendations.

Contact: privacy@borealmarche.ca
""")

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


# ============================================================================
# Footer
# ============================================================================
st.markdown("---")
st.caption(f"Boréal Marché | Capstone Project | {datetime.now().year}")