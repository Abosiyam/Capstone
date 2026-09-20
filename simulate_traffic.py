# ============================================================================
# simulate_traffic.py – Simulate API traffic for dashboard testing
# ============================================================================

import json
import random
from pathlib import Path
from datetime import datetime

METRICS_PATH = Path('artifacts/metrics.json')

# Initialize metrics if not exists
if not METRICS_PATH.exists():
    metrics = {
        "requests": [],
        "total_requests": 0,
        "errors": 0,
        "predictions": {"Send coupon": 0, "No coupon": 0}
    }
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)

# Load existing metrics
with open(METRICS_PATH, 'r') as f:
    metrics = json.load(f)

# Simulate 20 requests
print("Simulating 20 requests...")
for i in range(20):
    # 10% chance of error
    if random.random() < 0.1:
        metrics["errors"] += 1
        latency = random.uniform(500, 1500)
    else:
        latency = random.uniform(50, 300)
    
    # Random decision
    decision = random.choice(["Send coupon", "No coupon"])
    metrics["predictions"][decision] += 1
    
    metrics["requests"].append({
        "timestamp": datetime.now().isoformat(),
        "latency_ms": round(latency, 2),
        "decision": decision
    })
    metrics["total_requests"] += 1

# Keep only last 100 requests
metrics["requests"] = metrics["requests"][-100:]

# Save
with open(METRICS_PATH, 'w') as f:
    json.dump(metrics, f, indent=2)

print(f"✅ Simulated! Total requests: {metrics['total_requests']}")
print(f"   Errors: {metrics['errors']}")
print(f"   Predictions: {metrics['predictions']}")