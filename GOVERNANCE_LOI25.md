# GOVERNANCE_LOI25.md

## Automated Decision Register

| Decision Point | What is Decided | Personal Information Used | Principal Factors | Human Review? | How Customer Exercises Rights |
|----------------|-----------------|---------------------------|-------------------|---------------|-------------------------------|
| Retention coupon targeting | Whether a customer receives a 15% discount coupon | Purchase history, recency, frequency, monetary value, product categories | Days since last purchase, order count, total spend, product diversity | Yes – a marketing manager reviews the list before sending | Contact privacy@borealmarche.ca to request human review or opt out |
| Product recommendation | Which products to suggest in the "You might also like" strip | Current basket contents, past purchases | Association rules (lift, confidence) | No – recommendations are non-binding suggestions | Customers can clear their browsing history or disable recommendations in account settings |
| Assistant response | Answer to a customer question | Question text, retrieved policy documents | Retrieval similarity, tool outputs | No – but every response cites sources and refuses to invent answers | Customers can request a human agent at any time |

---

## Plain-Language Customer Notice (French and English)

### English

**How we use your data to personalise your experience**

At Boréal Marché, we use your purchase history to:
- Predict whether you might like a discount coupon.
- Recommend products you might enjoy.
- Answer your questions with our virtual assistant.

**Your rights:**
- You can ask us to explain any decision made about you.
- You can request a human review of any automated decision.
- You can opt out of personalised recommendations at any time.

To exercise these rights, contact us at privacy@borealmarche.ca.

### French

**Comment nous utilisons vos données pour personnaliser votre expérience**

Chez Boréal Marché, nous utilisons votre historique d'achat pour :
- Prédire si vous pourriez bénéficier d'un coupon de réduction.
- Recommander des produits susceptibles de vous intéresser.
- Répondre à vos questions avec notre assistant virtuel.

**Vos droits :**
- Vous pouvez nous demander d'expliquer toute décision vous concernant.
- Vous pouvez demander une révision humaine de toute décision automatisée.
- Vous pouvez refuser les recommandations personnalisées à tout moment.

Pour exercer ces droits, contactez-nous à privacy@borealmarche.ca.

---

## Design Consequence

Because a decision based exclusively on automated processing triggers disclosure and human-review obligations under Law 25, we inserted a **human approval step** in the retention coupon workflow. The model generates a ranked list of customers, but a marketing manager reviews and approves the final list before any coupon is sent. This ensures that no customer is denied an offer solely by an algorithm.

---

## Data Minimisation Audit

| Feature | Necessary? | Justification |
|---------|------------|---------------|
| order_count | Yes | Measures frequency – a core retention signal |
| total_spend | Yes | Measures monetary value – a core retention signal |
| days_since_last_purchase | Yes | Measures recency – the strongest predictor |
| customer_lifetime_days | Yes | Context for recency |
| avg_basket_size | Yes | Basket composition |
| unique_products_bought | Yes | Product diversity |
| pct_food, pct_drink, etc. | Yes | Category preferences |
| top_country | Yes | Geographic context (borderline, kept for fairness monitoring) |
| first_purchase_date, last_purchase_date | Yes | Used to compute recency and lifetime |
| **All other features** | Removed | We removed any feature that was not directly linked to a business need. |

---

## Fairness Audit

We computed recall, precision, and selection rate by subgroup at threshold = 0.5 (the standard comparison point).

### Overall Metrics

| Metric | Value |
|--------|-------|
| Overall Recall | 0.7133 |
| Overall Precision | 0.7202 |
| Overall Selection Rate | 0.5750 |

### By Region (top countries)

| Subgroup | N | Recall | Precision | Selection Rate | Recall Gap |
|----------|---|--------|-----------|----------------|------------|
| United Kingdom | 920 | 0.7135 | 0.7202 | 0.5750 | +0.0002 |
| Germany | 21 | 0.9231 | 0.6667 | 0.8571 | +0.2098 |

### By Tenure Band

| Subgroup | N | Recall | Precision | Selection Rate | Recall Gap |
|----------|---|--------|-----------|----------------|------------|
| 0–6 months | 785 | 0.5860 | 0.6438 | 0.4650 | **-0.1273** ⚠️ |
| 6–12 months | 212 | 1.0000 | 0.8396 | 1.0000 | +0.2867 |

### By Spend Quartile

| Subgroup | N | Recall | Precision | Selection Rate | Recall Gap |
|----------|---|--------|-----------|----------------|------------|
| Q1 (lowest) | 250 | 0.3400 | 0.5667 | 0.2400 | **-0.3733** ⚠️⚠️ |
| Q2 | 249 | 0.5036 | 0.6635 | 0.4177 | **-0.2096** ⚠️ |
| Q3 | 249 | (see notebook) | – | – | – |
| Q4 (highest) | 249 | 0.9747 | 0.8075 | 0.9598 | +0.2614 |

### Flagged Groups (recall gap < -5 percentage points)

| Group | Recall Gap | Severity |
|-------|------------|----------|
| Q1 (lowest spend) | **-37.3%** | 🔴 Critical |
| Q2 | **-21.0%** | 🔴 Critical |
| 0–6 months tenure | **-12.7%** | 🟡 Moderate |

### Candidate Mitigations

**1. Lower the decision threshold for flagged groups**
- **Action:** Use a lower threshold (e.g., 0.3 instead of 0.5) for new and low-spend customers.
- **Trade-off:** Increases false positives → more coupons sent to customers who would not return → lower profit per customer.
- **Benefit:** Reduces the recall gap by up to 20 percentage points for Q1.

**2. Collect more data and re-train**
- **Action:** Acquire more transaction data specifically for new customers (0–6 months) and low-spend customers.
- **Trade-off:** Takes time (3–6 months) and cannot be done immediately.
- **Benefit:** The model will learn better patterns for these groups.

**3. Add features that capture low-spend and new-customer behaviour**
- **Action:** Engineer features such as "first purchase category", "days since account creation", or "order via mobile vs desktop".
- **Trade-off:** Requires additional data collection and feature engineering.
- **Benefit:** Improves the model's ability to distinguish between returners and non-returners in these groups.

**4. Separate model for new customers**
- **Action:** Train a dedicated model only on customers with < 6 months tenure.
- **Trade-off:** Splits the data, reducing sample size for the main model.
- **Benefit:** Better fit for the specific behaviour of new customers.

### Recommendation

We recommend starting with **Mitigation #1** (lower threshold for flagged groups), because it can be implemented immediately with no additional data collection. We would monitor profit impact over 3 months and, if the gap persists, move to **Mitigation #3** (feature engineering).

---

## Model and Data Cards

- See `MODEL_CARD.md` for model details, limitations, and out-of-scope uses.
- See `DATA_CARD.md` for data provenance, licence, and cleaning steps.