# ============================================================================
# dashboard.py – Streamlit Monitoring Dashboard
# ============================================================================

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Boréal Marché Monitoring", layout="wide")

METRICS_PATH = Path('artifacts/metrics.json')

st.title("📊 Boréal Marché – Monitoring Dashboard")
st.markdown("Live monitoring of the retention prediction API")

# Load metrics
if not METRICS_PATH.exists():
    st.warning("No metrics yet. Run `python simulate_traffic.py` first.")
    st.stop()

with open(METRICS_PATH, 'r') as f:
    metrics = json.load(f)

# ---------- Top KPIs ----------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Requests", metrics["total_requests"])

with col2:
    st.metric("Errors", metrics["errors"])

with col3:
    if metrics["requests"]:
        avg_latency = sum(r["latency_ms"] for r in metrics["requests"]) / len(metrics["requests"])
        st.metric("Avg Latency (ms)", f"{avg_latency:.0f}")
    else:
        st.metric("Avg Latency (ms)", "N/A")

with col4:
    total_pred = sum(metrics["predictions"].values())
    coupon_rate = (metrics["predictions"]["Send coupon"] / total_pred * 100) if total_pred > 0 else 0
    st.metric("Coupon Rate", f"{coupon_rate:.1f}%")

st.markdown("---")

# ---------- Charts ----------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Prediction Distribution")
    pred_df = pd.DataFrame({
        "Decision": list(metrics["predictions"].keys()),
        "Count": list(metrics["predictions"].values())
    })
    st.bar_chart(pred_df.set_index("Decision"))

with col_right:
    st.subheader("Latency Over Time")
    if metrics["requests"]:
        lat_df = pd.DataFrame(metrics["requests"])
        lat_df["timestamp"] = pd.to_datetime(lat_df["timestamp"])
        st.line_chart(lat_df.set_index("timestamp")["latency_ms"])
    else:
        st.info("No requests yet")

st.markdown("---")

# ---------- Recent Requests ----------
st.subheader("Recent Requests")
if metrics["requests"]:
    recent = pd.DataFrame(metrics["requests"][-10:])
    st.dataframe(recent, use_container_width=True)
else:
    st.info("No recent requests")

# ---------- Alerts ----------
st.markdown("---")
st.subheader("🚦 Alerts")

alerts = []
if metrics["errors"] > 5:
    alerts.append(("🔴 High Error Rate", f"{metrics['errors']} errors detected"))
if metrics["requests"]:
    avg_lat = sum(r["latency_ms"] for r in metrics["requests"]) / len(metrics["requests"])
    if avg_lat > 500:
        alerts.append(("🟡 High Latency", f"Avg latency is {avg_lat:.0f}ms"))

if alerts:
    for level, msg in alerts:
        st.error(f"{level}: {msg}")
else:
    st.success("✅ All systems healthy")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")