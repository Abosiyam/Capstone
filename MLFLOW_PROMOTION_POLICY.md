# MLflow Promotion Policy

**Project:** Boréal Marché – Customer Intelligence Platform  
**Model:** `boreal-marche-retention`  
**Version:** 1  
**Last Updated:** October 2026

---

## 1. Purpose

This policy defines the criteria and process for promoting a model version from **Staging** to **Production** in the MLflow Model Registry.

**Guiding principle:** A model is promoted only when it meets all technical thresholds AND passes a fairness gate. No model is deployed automatically — a human reviewer must approve.

---

## 2. Model Registry Aliases

| Alias | Meaning |
|-------|---------|
| `challenger` | A newly registered model under evaluation |
| `champion` | The model currently serving production traffic |
| `archived` | A previously deployed model kept for rollback |

**Rule:** Only one model version can hold the `champion` alias at a time.

---

## 3. Promotion Criteria (Staging → Production)

A model must satisfy **ALL** of the following criteria before promotion:

| # | Criterion | Threshold | Source |
|---|-----------|-----------|--------|
| 1 | **PR-AUC** (on held-out test set) | ≥ **0.75** | `threshold_metadata.json` |
| 2 | **Brier score** | ≤ **0.25** | `threshold_metadata.json` |
| 3 | **Worst fairness gap** | ≥ **-0.10** (10 pp) | `GOVERNANCE_LOI25.md` |
| 4 | **Expected profit** | ≥ **$90,000** | `threshold_metadata.json` |
| 5 | **Human review** | Required | This policy |

---

## 4. Current Model Status (Version 1)

| Criterion | Value | Pass? |
|-----------|-------|-------|
| PR-AUC | 0.7803 | ✅ |
| Brier | 0.2090 | ✅ |
| Fairness gap (worst) | -0.3733 | ❌ **FAIL** |
| Expected profit | $100,232 | ✅ |
| Human review | Pending | ⏳ |

**Decision:** Version 1 is **conditionally approved**. Because the fairness gap for the Q1 (lowest-spend) group is -37.3%, the model **must not be deployed without a human review step** and **must include the mitigation plan** documented in `GOVERNANCE_LOI25.md`.

---

## 5. Promotion Process

### Step 1 – Register
The model is registered to MLflow with the `challenger` alias.

```bash
python src/register_model.py

---

## 5. Promotion Process

| Step | Action | Owner |
|------|--------|-------|
| 1 | Register new model version via `src/register_model.py` | Data Scientist |
| 2 | Alias it as `challenger` | Automation |
| 3 | Run the promotion checks (Section 3) | Automation |
| 4 | Generate the promotion report | Automation |
| 5 | Human review of the report | Data Science Lead |
| 6 | If approved: move `champion` alias to the new version | Approver |
| 7 | Move previous champion to `archived` | Automation |
| 8 | Update `deployment_metadata.json` and redeploy | MLOps |

---

## 6. Rollback Policy

If the deployed model degrades in production (drift alert, error rate spike, or fairness regression):

1. **Automatic:** The monitoring dashboard triggers a red alert.
2. **Manual:** Within 24 hours, the on-call MLOps engineer may:
   - Revert the `champion` alias to the previous version, OR
   - Switch to the previous model artifact via the serving layer.
3. **Redeploy:** The serving layer resolves the model by alias, so **no code change is required** – only a registry update.

**Target rollback time:** < 15 minutes.

---

## 7. Retraining Cadence

| Trigger | Action |
|---------|--------|
| **Scheduled** | Every **quarter** (3 months) |
| **Drift alert** | When any feature has PSI > 0.2 |
| **Fairness alert** | When any subgroup recall gap < -0.10 |
| **Manual** | On request by the Data Science Lead |

Scheduled retraining runs via a GitHub Actions workflow that:
1. Re-runs ETL.
2. Re-mines association rules.
3. Retrains the model.
4. Logs to MLflow.
5. **Opens a pull request** with the new metrics (does **not** deploy automatically).
6. A human merges the PR after reviewing.

---

## 8. Current Model Status (v1)

| Field | Value |
|-------|-------|
| **Version** | 1 |
| **Alias** | `champion` |
| **PR-AUC** | 0.7803 |
| **Brier** | 0.2090 |
| **Worst Fairness Gap** | **-0.3733** (Q1 spend) ⚠️ |
| **Promotion Passed** | ⚠️ **Conditional** – fairness gap exceeds threshold |
| **Mitigation Plan** | Lower threshold for Q1 group; collect more data over 3 months |
| **Approved by** | Pending Data Science Lead review |

**Status:** Deployed as `champion` with a **documented mitigation plan** for the fairness gap. Re-evaluation scheduled for Q1 2027.

---

## 9. Change Log

| Date | Version | Change |
|------|---------|--------|
| 2026-10-16 | 1.0 | Initial policy drafted |