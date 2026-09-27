# D4 – Deployment Demonstration and Dashboard

**Project:** Boréal Marché – Customer Intelligence Platform  
**Student:** Hossam Siyam  
**Course:** 420-977-VA – AI Development Project  
**Date:** September 2026

---

## 1. Live URLs

| Service | URL | Status |
|---------|-----|--------|
| **API (production)** | https://capstone-bkg2.onrender.com | ✅ Live |
| **API Documentation (Swagger)** | https://capstone-bkg2.onrender.com/docs | ✅ Live |
| **Monitoring Dashboard** | https://bibe6vpgewedpjfv7emsae.streamlit.app | ✅ Live |
| **Source Repository** | https://github.com/Abosiyam/Capstone | ✅ Public |

**Note:** The API is hosted on Render's free tier, which spins down after 15 minutes of inactivity. The first request after inactivity may take up to 50 seconds to wake the service. This behaviour is documented in the README and the monitoring dashboard.

---

## 2. API Endpoints

| Endpoint | Method | Purpose | Example Response |
|----------|--------|---------|------------------|
| `/` | GET, HEAD | API information | `{"message":"Boréal Marché Retention API",...}` |
| `/status` | GET, HEAD | Health check | `{"status":"healthy"}` |
| `/info` | GET | Model metadata | `{"model":"Logistic_Regression_Calibrated","n_features":25,...}` |
| `/predict` | POST | Predict one customer | `{"probability":0.78,"decision":"Send coupon"}` |
| `/predict/batch` | POST | Predict multiple customers | `{"results":[...]}` |
| `/docs` | GET | Interactive Swagger UI | HTML page |

All request and response schemas use **Pydantic v2** with `extra='forbid'` (rejects unknown fields).

---

## 3. Docker Containerisation

### 3.1 Dockerfile Design Choices

| Choice | Reason |
|--------|--------|
| **Multi-stage build** | Smaller final image – build tools are not included in the runtime image |
| **`python:3.13-slim` base** | Minimal image (~150 MB) compared to the full Python image (~900 MB) |
| **Non-root user (`appuser`)** | Security best practice – the container does not run as root |
| **HEALTHCHECK** | Docker automatically monitors the API health |
| **Pinned dependencies** | `requirements.txt` ensures reproducible builds |
| **`.dockerignore`** | Excludes `data/`, `notebooks/`, `venv/` – keeps the image small |

### 3.2 Image Size

| Metric | Value |
|--------|-------|
| **Image name** | `boreal-marche-api:latest` |
| **Image ID** | `6cef0e440ad3` |
| **Content size** | **609 MB** ✅ (under 700 MB "Excellent" target) |
| **Build time** | ~3–5 minutes |

### 3.3 Build and Run Commands

```bash
# Build
docker build -t boreal-marche-api .

# Run
docker run -p 8000:8000 boreal-marche-api