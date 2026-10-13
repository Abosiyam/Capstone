# Boréal Marché – Customer Intelligence Platform

> An end-to-end AI system: from raw transactions to a monitored, deployed, governed platform.

[![CI](https://github.com/Abosiyam/Capstone/actions/workflows/ci.yml/badge.svg)](https://github.com/Abosiyam/Capstone/actions/workflows/ci.yml)

---

## 🎬 Demo Video

📹 **[Watch the demo video](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)**

---

## 🌐 Live URLs

| Service | URL |
|---------|-----|
| **Frontend (Interactive)** | [https://boreal-marche-frontend.streamlit.app](https://boreal-marche-frontend.streamlit.app) |
| **API (Head A + B + C)** | [https://boreal-marche-api-latest-1.onrender.com](https://boreal-marche-api-latest-1.onrender.com) |
| **API Docs (Swagger)** | [https://boreal-marche-api-latest-1.onrender.com/docs](https://boreal-marche-api-latest-1.onrender.com/docs) |
| **Monitoring Dashboard** | [https://bibe6vpgewedpjfv7emsae.streamlit.app](https://bibe6vpgewedpjfv7emsae.streamlit.app) |

**Available endpoints:**
- `POST /predict` – Retention prediction (Head A)
- `POST /recommend` – Product recommendations (Head B)
- `POST /chat` – Bilingual assistant (Head C)
- `GET /status` – Health check
- `GET /info` – Model metadata
## 📊 Results at a Glance

| Metric | Value |
|--------|-------|
| **Best model** | Logistic Regression (Calibrated) |
| **PR-AUC (test)** | 0.7803 |
| **Expected profit** | $100,232 |
| **Improvement over baseline** | +$28,200 (+39%) |
| **Optimal threshold** | 0.01 |

---

## 🚀 Quickstart

### Local Setup (Docker)

```bash
git clone https://github.com/Abosiyam/Capstone.git
cd Capstone
docker build -t boreal-marche-api .
docker run -p 8000:8000 boreal-marche-api