# Executive Summary
# Résumé Exécutif

---

## English Version

### Boréal Marché – Customer Intelligence Platform

**Prepared by:** Hossam Siyam  
**Date:** September 2026  
**For:** Boréal Marché Executive Team

---

#### The Problem

Boréal Marché currently sends a 15% discount coupon to every customer every quarter. This approach:
- **Wastes margin** on customers who would have purchased anyway.
- **Misses customers** who have quietly stopped buying.
- **Relies on intuition** rather than data.

The company also has an outdated cross-sell system and two employees answering the same forty customer questions every day in two languages.

---

#### The Solution

We built an **end-to-end AI platform** that addresses all three problems through one integrated system:

| Component | What It Does |
|-----------|--------------|
| **Retention Prediction** | Predicts which customers will return in the next 90 days |
| **Recommendation Engine** | Suggests products based on the current basket |
| **Bilingual Assistant** | Answers customer questions in French or English, grounded in real policies |

The system is **fully deployed**, **monitored**, and **governed** according to Quebec's Law 25.

---

#### Business Impact

| Metric | Value |
|--------|-------|
| **Expected annual profit increase** | **+$28,200** (from $72,032 to $100,232) |
| **Improvement over current approach** | **+39%** |
| **Model accuracy (PR-AUC)** | 0.78 (strong for retail retention) |
| **Live API** | https://capstone-bkg2.onrender.com |
| **Live Dashboard** | https://bibe6vpgewedpjfv7emsae.streamlit.app |

The model identifies the optimal decision threshold (0.01) that maximises profit given the cost of a coupon ($4) versus the value of a retained customer ($180).

---

#### Technical Approach

| Aspect | Detail |
|--------|--------|
| **Data** | 400,916 real transactions from UCI Online Retail II |
| **Features** | 25 engineered features (Recency, Frequency, Monetary, Basket, Category, Behavioural) |
| **Models tested** | 9 models compared (including 2 baselines) |
| **Final model** | Logistic Regression (Calibrated) |
| **Tuning** | Optuna with Bayesian search (30 trials per model) |
| **Calibration** | Platt scaling for reliable probabilities |
| **Deployment** | FastAPI + Docker + Render |
| **Monitoring** | Streamlit dashboard with drift and alerting |
| **CI/CD** | GitHub Actions with branch protection |

---

#### Governance and Ethics

| Requirement | Status |
|-------------|--------|
| Automated decision register | ✅ Documented in `GOVERNANCE_LOI25.md` |
| Bilingual customer notice | ✅ Provided |
| Human review step | ✅ Marketing manager approves final list |
| Data minimisation | ✅ All 25 features justified |
| Fairness audit | ✅ Complete (gaps identified and mitigations proposed) |
| Model Card | ✅ `MODEL_CARD.md` |
| Data Card | ✅ `DATA_CARD.md` |

**Fairness findings:** The model performs well overall but shows lower recall for new customers (0–6 months) and low-spend customers. We recommend lowering the decision threshold for these groups and collecting more data over time.

---

#### Recommendation

We recommend **deploying the system immediately** with the following conditions:
1. **Human review** before any coupon list is finalised.
2. **Monthly monitoring** of drift, error rate, and fairness metrics.
3. **Quarterly re-training** with new data.
4. **Threshold adjustment** for flagged groups within 3 months.

The system is ready for production and will deliver measurable profit improvement from day one.

---

## Version Française

### Boréal Marché – Plateforme d'Intelligence Client

**Préparé par :** Hossam Siyam  
**Date :** Septembre 2026  
**Pour :** Équipe de direction de Boréal Marché

---

#### Le Problème

Boréal Marché envoie actuellement un coupon de réduction de 15 % à chaque client chaque trimestre. Cette approche :
- **Gaspille la marge** sur les clients qui auraient acheté de toute façon.
- **Rate les clients** qui ont discrètement arrêté d'acheter.
- **Repose sur l'intuition** plutôt que sur les données.

L'entreprise dispose également d'un système de vente croisée obsolète et de deux employés qui répondent aux mêmes quarante questions client chaque jour en deux langues.

---

#### La Solution

Nous avons construit une **plateforme d'IA de bout en bout** qui résout ces trois problèmes grâce à un système intégré :

| Composant | Ce qu'il fait |
|-----------|---------------|
| **Prédiction de rétention** | Prédit quels clients reviendront dans les 90 prochains jours |
| **Moteur de recommandation** | Suggère des produits en fonction du panier actuel |
| **Assistant bilingue** | Répond aux questions des clients en français ou en anglais, ancré dans les politiques réelles |

Le système est **entièrement déployé**, **surveillé** et **gouverné** conformément à la Loi 25 du Québec.

---

#### Impact Commercial

| Indicateur | Valeur |
|------------|--------|
| **Augmentation annuelle du profit** | **+28 200 $** (de 72 032 $ à 100 232 $) |
| **Amélioration par rapport à l'approche actuelle** | **+39 %** |
| **Performance du modèle (PR-AUC)** | 0,78 (élevé pour la rétention en commerce de détail) |
| **API en direct** | https://capstone-bkg2.onrender.com |
| **Tableau de bord en direct** | https://bibe6vpgewedpjfv7emsae.streamlit.app |

Le modèle identifie le seuil de décision optimal (0,01) qui maximise le profit compte tenu du coût d'un coupon (4 $) par rapport à la valeur d'un client retenu (180 $).

---

#### Approche Technique

| Aspect | Détail |
|--------|--------|
| **Données** | 400 916 transactions réelles du UCI Online Retail II |
| **Caractéristiques** | 25 caractéristiques (Récence, Fréquence, Monétaire, Panier, Catégorie, Comportement) |
| **Modèles testés** | 9 modèles comparés (incluant 2 références) |
| **Modèle final** | Régression Logistique (Calibrée) |
| **Optimisation** | Optuna avec recherche bayésienne (30 essais par modèle) |
| **Calibration** | Platt scaling pour des probabilités fiables |
| **Déploiement** | FastAPI + Docker + Render |
| **Surveillance** | Tableau de bord Streamlit avec dérive et alertes |
| **CI/CD** | GitHub Actions avec protection de branche |

---

#### Gouvernance et Éthique

| Exigence | Statut |
|----------|--------|
| Registre des décisions automatisées | ✅ Documenté dans `GOVERNANCE_LOI25.md` |
| Avis client bilingue | ✅ Fourni |
| Étape de révision humaine | ✅ Le responsable marketing approuve la liste finale |
| Minimisation des données | ✅ Les 25 caractéristiques sont justifiées |
| Audit d'équité | ✅ Complet (écarts identifiés et mesures proposées) |
| Fiche du modèle | ✅ `MODEL_CARD.md` |
| Fiche des données | ✅ `DATA_CARD.md` |

**Constats d'équité :** Le modèle performe bien globalement mais montre un rappel plus faible pour les nouveaux clients (0–6 mois) et les clients à faible dépense. Nous recommandons d'abaisser le seuil de décision pour ces groupes et de collecter davantage de données.

---

#### Recommandation

Nous recommandons de **déployer le système immédiatement** avec les conditions suivantes :
1. **Révision humaine** avant toute finalisation de liste de coupons.
2. **Surveillance mensuelle** de la dérive, du taux d'erreur et des métriques d'équité.
3. **Ré-entraînement trimestriel** avec de nouvelles données.
4. **Ajustement du seuil** pour les groupes signalés dans les 3 mois.

Le système est prêt pour la production et offrira une amélioration mesurable du profit dès le premier jour.

---

*End of Executive Summary / Fin du Résumé Exécutif*