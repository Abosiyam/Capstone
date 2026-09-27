# D6 – Presentation Slides

**Boréal Marché – Customer Intelligence Platform**  
Hossam Siyam – 420-977-VA – September 2026

---

## Slide 1 – Title

**Boréal Marché – Customer Intelligence Platform**

An end-to-end AI system: from raw transactions to a monitored, deployed, governed platform.

- **Student:** Hossam Siyam
- **Course:** 420-977-VA – AI Development Project
- **Live API:** https://capstone-bkg2.onrender.com
- **Live Dashboard:** https://bibe6vpgewedpjfv7emsae.streamlit.app

---

## Slide 2 – The Problem

**Boréal Marché: A mid‑size Quebec online grocery**

| Problem | Current Approach | Consequence |
|---------|------------------|-------------|
| **Retention** | 15% coupon to every customer every quarter | Wastes margin, misses churning customers |
| **Cross‑sell** | Hard‑coded recommendations, 8 months stale | Missed attachment opportunities |
| **Customer support** | Two employees answer 40 questions/day in 2 languages | Repetitive work, slow response |

---

## Slide 3 – The Solution

**One platform, three model heads**

| Head | Technique | Business Question |
|------|-----------|-------------------|
| **A – Prédiction** | Supervised classification | Will this customer buy again in 90 days? |
| **B – Recommandation** | Association rule mining | Given the basket, what should we suggest? |
| **C – Assistant** | RAG + tool calling | Answer customers in French or English |

---

## Slide 4 – Architecture

**Offline (scheduled) and Online (per request)**
