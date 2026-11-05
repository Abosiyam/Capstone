---
marp: true
theme: default
paginate: true
---

# Boréal Marché
### Customer Intelligence Platform
**Hossam Siyam**
420-977-VA Capstone Project

---

## Slide 1: The Problem
**Boréal Marché is wasting money and time.**

1. **Retention:** They give a 15% coupon to *everyone*, even loyal customers.
2. **Recommendations:** The "You might also like" section is old and hard-coded.
3. **Support:** Two employees answer the same 40 questions every day.

---

## Slide 2: The Solution (3 AI Brains)
**One system with three parts:**

- **Head A (Prediction):** Will this customer buy again in 90 days?
- **Head B (Recommendation):** What should we suggest in their cart?
- **Head C (Assistant):** A chatbot that answers questions in English and French.

---

## Slide 3: The Data & Leakage Fix
**We used real data, but it was messy.**

- Started with **525,000** transactions, cleaned it to **400,000**.
- **Major Fix:** We prevented "Data Leakage." At first, the AI cheated by looking at future data. We split the data by time so the AI only learns from the past to predict the future.

---

## Slide 4: Head A - The Prediction Model
**How we predicted who will return:**

- Tested **9 different AI models**.
- The winner: **Logistic Regression** (Accurate and easy to explain).
- **Accuracy Score:** 0.78 (Very good for real-world retail).

---

## Slide 5: Head A - The Money Decision
**How we saved the company money:**

- Default threshold (0.5) made $72,000.
- We changed the threshold to **0.01**.
- **New Profit:** **$100,232**.
- **We saved Boréal Marché an extra $28,200** just by changing the math!

---

## Slide 6: Head B - The Recommendation Engine
**How we suggest products:**

- We analyzed shopping baskets to find patterns (e.g., "If you buy charcoal, you buy matches").
- Created **55 strong rules**.
- **Result:** Our engine is **6.3 times better** than just showing the most popular items.

---

## Slide 7: Head C - The AI Assistant
**A smart chatbot for customer support:**

- Uses our real company policies to answer questions in **English and French**.
- **Engineering Trade-off:** The project suggested heavy tools (PyTorch), but our cloud server has a 512MB limit. I used a lightweight search tool (TF-IDF) instead to prevent server crashes.
- **Result:** Scored **100%** on our 40-question test.

---

## Slide 8: Deployment (Render vs. AWS)
**The system is on the internet right now:**

- **Live API:** Hosted on **Render**. (The project asked for AWS, but I used Render to avoid credit card billing. However, I wrote the training code to be 100% compatible with AWS SageMaker).
- **Live Frontend:** Hosted on **Streamlit Cloud**.
- **Code:** Fully automated testing on GitHub (CI/CD).

---

## Slide 9: Monitoring Dashboard
**We watch the system 24/7:**

- Tracks how many requests come in, speed, and errors.
- **Data Drift:** Alerts us if customer behavior changes over time.
- **Safe Retraining:** A weekly automated job retrains the model, but it opens a Pull Request for human review instead of deploying automatically.

---

## Slide 10: Ethics & Law 25
**We built this responsibly:**

- **Fairness Audit:** We checked if the AI is unfair to certain groups (e.g., new customers) and proposed fixes.
- **Human Review:** A human must review the list before sending coupons.
- **Privacy:** We follow Quebec's Law 25.

---

## Slide 11: Conclusion
**What we delivered:**

- A fully working AI system.
- Live on the internet.
- Monitored and safe.
- Saves the company $28,200.

---

## Slide 12: Thank You
**Thank you for listening.**

