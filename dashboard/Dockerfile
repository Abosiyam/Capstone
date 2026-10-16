# ============================================================================
# dashboard/Dockerfile – Monitoring Dashboard (Streamlit)
# ============================================================================

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir streamlit requests pandas

# Copy the dashboard code and the artifacts it reads
COPY dashboard.py .
COPY artifacts/ ./artifacts/

# Expose Streamlit port
EXPOSE 8502

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8502/_stcore/health || exit 1

# Run Streamlit on port 8502
CMD ["streamlit", "run", "dashboard.py", "--server.port=8502", "--server.address=0.0.0.0"]