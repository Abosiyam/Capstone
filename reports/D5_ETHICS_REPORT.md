# D5 – Optimization and Ethics Report

**Project:** Boréal Marché – Customer Intelligence Platform  
**Student:** Hossam Siyam  
**Course:** 420-977-VA – AI Development Project  
**Date:** September 2026

---

## 1. Performance Optimization

### 1.1 Model Performance

The final model is a **calibrated Logistic Regression** classifier. It was selected after comparing 9 models under identical folds and preprocessing.

| Metric | Value |
|--------|-------|
| PR-AUC | 0.7803 |
| ROC-AUC | 0.7191 |
| Brier Score | 0.2090 |
| Recall (threshold 0.5) | 0.7133 |
| Precision (threshold 0.5) | 0.7202 |

**Comparison against baselines:**

| Model | PR-AUC |
|-------|--------|
| Dummy (most frequent) | 0.5809 |
| Business Rule (recency < 30) | 0.6307 |
| **Our model** | **0.7803** |

Our model improves PR-AUC by **+0.15** over the business rule baseline.

### 1.2 Hyperparameter Tuning

We used **Optuna** with Bayesian search (TPE sampler) and median pruning. 30 trials were run per model. All trials were logged to MLflow.

Best parameters for Logistic Regression:
- `C = 0.0187`
- `solver = lbfgs`
- `max_iter = 190`

### 1.3 Calibration and Threshold Selection

We calibrated the model using **Platt scaling** (sigmoid) to make the probabilities more reliable.

The optimal decision threshold was selected by maximizing expected profit:

| Threshold | Expected Profit |
|-----------|-----------------|
| 0.5 (default) | $72,032 |
| **0.01 (optimal)** | **$100,232** |
| Improvement | **+$28,200 (+39%)** |

**Cost assumptions:**
- Coupon cost: $4
- Retained customer value: $180

### 1.4 Latency Optimization

| Endpoint | p50 Latency | p95 Latency |
|----------|-------------|-------------|
| `/status` | ~10 ms | ~30 ms |
| `/predict` | ~50 ms | ~150 ms |
| `/predict/batch` (10 items) | ~200 ms | ~500 ms |

The API loads the model **once at startup** using the FastAPI lifespan pattern, so there is no per-request model loading overhead.

---

## 2. Scalability

### 2.1 Current Capacity

| Aspect | Value |
|--------|-------|
| Model size | ~5 MB |
| Memory usage | ~200 MB |
| Concurrent requests | Tested up to 10/sec |
| Cold start | ~50 sec (free tier sleep) |

### 2.2 Breaking Points

| Load | Expected Behaviour |
|------|-------------------|
| < 100 req/sec | Works on current setup (1 CPU, 512 MB) |
| 100–1000 req/sec | Requires scaling up (more CPU/RAM) |
| > 1000 req/sec | Requires horizontal scaling + load balancer |

### 2.3 Cost per 1,000 Requests

| Platform | Estimated Cost per 1k Requests |
|----------|-------------------------------|
| Render (free tier) | $0 (within limits) |
| AWS App Runner | ~$0.02 |
| AWS SageMaker Endpoint | ~$0.10 |

---

## 3. Interpretability

### 3.1 Feature Importance

The top 5 features (by absolute coefficient magnitude in the Logistic Regression):

| Rank | Feature | Direction |
|------|---------|-----------|
| 1 | `days_since_last_purchase` | Negative (more days → less likely to return) |
| 2 | `order_count` | Positive (more orders → more likely) |
| 3 | `total_spend` | Positive |
| 4 | `unique_products_bought` | Positive |
| 5 | `avg_days_between_orders` | Negative |

### 3.2 Per-Prediction Explanation

The model provides a probability (0–1) for each customer. This is used to rank customers for the marketing team. The human reviewer can see:
- The probability
- The decision (Send coupon / No coupon)
- The optimal threshold (0.01)

### 3.3 Is This Fit to Show a Customer?

No – the raw model output is not shown to customers. It is used internally by the marketing team, with a human review step before any coupon is sent.

---

## 4. Fairness Audit

See `GOVERNANCE_LOI25.md` for the full audit. Summary:

| Subgroup | Recall Gap | Severity |
|----------|------------|----------|
| Spend Q1 (lowest) | -37.3% | 🔴 Critical |
| Spend Q2 | -21.0% | 🔴 Critical |
| Tenure 0–6 months | -12.7% | 🟡 Moderate |

**Candidate mitigations:**

1. **Lower the threshold** for flagged groups (immediate, no data collection needed).
2. **Collect more data** for new and low-spend customers (3–6 months).
3. **Add features** capturing low-spend and new-customer behaviour.
4. **Separate model** for new customers.

**Recommendation:** Start with mitigation #1 (lower threshold).

---

## 5. Law 25 Governance

See `GOVERNANCE_LOI25.md` for full details. Summary:

| Requirement | Status |
|-------------|--------|
| Automated-decision register | ✅ Provided |
| Plain-language customer notice (EN/FR) | ✅ Provided |
| Human review step | ✅ Marketing manager approves final list |
| Data minimisation audit | ✅ All 25 features justified |
| Fairness audit | ✅ Complete |
| Model card | ✅ `MODEL_CARD.md` |
| Data card | ✅ `DATA_CARD.md` |

---

## 6. Ethics Summary

| Aspect | Assessment |
|--------|------------|
| Human oversight | ✅ Present |
| Data minimisation | ✅ Applied |
| Fairness gaps identified | ✅ Yes |
| Gaps mitigated | ⏳ Partially (mitigations proposed) |
| Transparency | ✅ Documents provided |
| Customer rights | ✅ Documented (bilingual) |
| Compliance with Law 25 | ✅ Yes |

**Honest conclusion:** The model is fit for deployment **with human review**. Fairness gaps exist but are documented with clear mitigation paths. We do not hide the gaps – we report them and propose solutions.

---

## 7. Summary

| Requirement | Status |
|-------------|--------|
| Performance optimization | ✅ Documented |
| Scalability analysis | ✅ Documented |
| Interpretability | ✅ Documented |
| Fairness audit | ✅ Documented |
| Law 25 governance | ✅ Documented |
| Model and data cards | ✅ Provided |

---

**End of D5 Report**
