# MODEL_CARD.md

## Model Overview

| Property | Value |
|----------|-------|
| **Model Name** | Boréal Marché Retention Model |
| **Version** | 1.0.0 |
| **Model Type** | Logistic Regression (Calibrated) |
| **Task** | Binary classification – predict customer return in next 90 days |
| **Owner** | Boréal Marché Data Science Team |
| **Contact** | atakys@vaniercollege.qc.ca |
| **Training Date** | September 2026 |
| **Framework** | scikit-learn 1.9.0 |
| **Artifact** | `artifacts/final_model.joblib` |

---

## Intended Use

### Primary Use
- **Identify customers likely to return** in the next 90 days.
- **Prioritise coupon distribution** to maximize retention and profit.
- **Support marketing decisions** with a data-driven ranking.

### Out-of-Scope Uses
- ❌ Do not use to **deny service** to any customer.
- ❌ Do not use to **determine credit or pricing**.
- ❌ Do not use as the **sole basis** for any decision – a human must review the final list.
- ❌ Do not deploy without **regular monitoring** for drift.

---

## Training Data

| Property | Value |
|----------|-------|
| **Source** | UCI Online Retail II |
| **Licence** | CC BY 4.0 |
| **Rows (cleaned)** | 400,916 |
| **Unique Customers** | 3,321 |
| **Date Range** | December 2009 – December 2010 |
| **Observation Window** | Data before 2010-09-01 |
| **Label Window** | 90 days after 2010-09-01 |
| **Train/Test Split** | 70% / 30% (stratified) |

See `DATA_CARD.md` for full data provenance and cleaning details.

---

## Features

**25 features** across the following categories:

| Category | Example Features |
|----------|------------------|
| Frequency | `order_count`, `total_orders` |
| Monetary | `total_spend`, `avg_spend_per_order`, `max_order_value` |
| Recency | `days_since_last_purchase`, `customer_lifetime_days` |
| Basket | `avg_basket_size`, `unique_products_bought`, `product_diversity` |
| Category Mix | `pct_food`, `pct_drink`, `pct_gift`, `pct_household`, `pct_office`, `pct_other` |
| Behavioural | `order_frequency_days`, `avg_days_between_orders` |
| Geographic | `top_country` |

**Data Minimisation:** All 25 features are directly tied to a business need. See the Data Minimisation Audit in `GOVERNANCE_LOI25.md`.

---

## Performance Metrics

### Test Set Performance (Threshold = 0.01)

| Metric | Value |
|--------|-------|
| **PR-AUC** | 0.7803 |
| **ROC-AUC** | 0.7191 |
| **Brier Score** | 0.2090 |
| **Recall** | 1.0000 |
| **Precision** | 0.5807 |
| **Selection Rate** | 1.0000 |

### Test Set Performance (Threshold = 0.5, Comparison)

| Metric | Value |
|--------|-------|
| **Recall** | 0.7133 |
| **Precision** | 0.7202 |
| **Selection Rate** | 0.5750 |

### Business Impact

| Threshold | Expected Profit |
|-----------|-----------------|
| 0.5 (default) | $72,032 |
| **0.01 (optimal)** | **$100,232** |
| **Improvement** | **+$28,200 (+39%)** |

**Cost assumptions:** Coupon cost = $4, Retained customer value = $180.

---

## Limitations

### Known Weaknesses

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Low recall for new customers (0–6 months)** | -12.7% below overall | Lower threshold for this group; collect more data |
| **Low recall for low-spend customers (Q1, Q2)** | -37.3% and -20.9% | Lower threshold; add features capturing low-spend behaviour |
| **Trained on UK data** | May not generalise to Quebec customers | Monitor drift; consider re-training with local data |
| **Threshold = 0.01 contacts everyone** | High marketing cost if applied blindly | Human review step filters the final list |
| **Probabilities may be slightly miscalibrated** | Minor impact on profit calculation | Monitor Brier score over time |

### Fairness Gaps

See `GOVERNANCE_LOI25.md` for the full fairness audit. Flagged groups:
- Spend Q1 (lowest): recall gap -37.3%
- Spend Q2: recall gap -21.0%
- Tenure 0–6 months: recall gap -12.7%

---

## Ethical Considerations

| Aspect | Status |
|--------|--------|
| Human review required? | ✅ Yes – before any coupon is sent |
| Data minimisation applied? | ✅ Yes – 25 features, all justified |
| Fairness audit performed? | ✅ Yes – see `GOVERNANCE_LOI25.md` |
| Customer rights documented? | ✅ Yes – bilingual notice in `GOVERNANCE_LOI25.md` |
| Law 25 compliant? | ✅ Yes – automated-decision register provided |

---

## Monitoring Plan

| Metric | Threshold | Action |
|--------|-----------|--------|
| Input drift (PSI) | > 0.2 | Investigate; consider retraining |
| Prediction drift | > 0.1 shift in mean | Investigate |
| Error rate | > 5% | Alert |
| Latency p95 | > 500 ms | Investigate |
| Brier score | Increase > 0.05 | Retrain |

---

## Deployment

| Environment | URL |
|-------------|-----|
| **API (Render)** | https://capstone-bkg2.onrender.com |
| **Dashboard (Streamlit)** | https://bibe6vpgewedpjfv7emsae.streamlit.app |
| **Repository** | https://github.com/Abosiyam/Capstone |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | September 2026 | Initial deployment – Logistic Regression (Calibrated) |

---

## Contact

For questions about this model, contact:
- **Data Science Team:** atakys@vaniercollege.qc.ca
- **Privacy Officer:** privacy@borealmarche.ca