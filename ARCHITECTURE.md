# ARCHITECTURE.md

## System Architecture

The Boréal Marché platform is built on a modern MLOps architecture that separates the expensive offline training process from the fast online serving process.

### 1. Offline Pipeline (Data to Model)
- **Data Ingestion:** Raw data is downloaded, cleaned, and versioned using DVC.
- **Feature Engineering:** Temporal splitting prevents data leakage. 25 features are generated.
- **Model Training:** 9 models are evaluated. Logistic Regression is selected and calibrated.
- **Tracking:** All runs are logged to MLflow.
- **Artifacts:** The final `model.joblib`, `rules.json`, and `tfidf_index.pkl` are saved.

### 2. Online Pipeline (API & Serving)
- **API:** FastAPI handles requests (`/predict`, `/recommend`, `/chat`).
- **Head A (Retention):** Loads the calibrated model into memory at startup.
- **Head B (Recommendation):** Uses an in-memory lookup index for millisecond-fast rule serving.
- **Head C (Assistant):** Uses a TF-IDF retriever to search the corpus and calls the API tools.

### 3. Monitoring & MLOps
- **Logging:** Every request is saved to a SQLite database (`predictions.db`).
- **Dashboard:** Streamlit reads the logs and computes Data Drift (PSI/KS).
- **CI/CD:** GitHub Actions runs tests on every push. Render auto-deploys the API.