# ============================================================================
# src/drift_monitor.py – Data Drift Detection (PSI + KS)
# ============================================================================
# Compares current traffic against the training reference distribution.
# Reports PSI and KS per feature, with traffic-light thresholds.
# ============================================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.stats import ks_2samp

# ---------- Paths ----------
REFERENCE_PATH = Path(__file__).parent.parent / 'data' / 'splits' / 'X_train.parquet'
DRIFT_REPORT_PATH = Path(__file__).parent.parent / 'artifacts' / 'drift_report.json'
CURRENT_DATA_PATH = Path(__file__).parent.parent / 'artifacts' / 'current_traffic.parquet'

# ---------- Thresholds ----------
PSI_SAFE = 0.1
PSI_WARNING = 0.2

KS_SAFE = 0.05
KS_WARNING = 0.10


def compute_psi(reference: np.ndarray, current: np.ndarray, n_bins: int = 10) -> float:
    """Compute Population Stability Index (PSI)."""
    reference = reference[~np.isnan(reference)]
    current = current[~np.isnan(current)]

    if len(reference) == 0 or len(current) == 0:
        return 0.0

    breakpoints = np.quantile(reference, np.linspace(0, 1, n_bins + 1))
    breakpoints = np.unique(breakpoints)
    if len(breakpoints) < 2:
        return 0.0

    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf

    ref_counts, _ = np.histogram(reference, bins=breakpoints)
    cur_counts, _ = np.histogram(current, bins=breakpoints)

    ref_pct = ref_counts / len(reference)
    cur_pct = cur_counts / len(current)

    ref_pct = np.where(ref_pct == 0, 1e-6, ref_pct)
    cur_pct = np.where(cur_pct == 0, 1e-6, cur_pct)

    psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
    return float(psi)


def compute_ks(reference: np.ndarray, current: np.ndarray) -> float:
    """Compute Kolmogorov-Smirnov statistic."""
    reference = reference[~np.isnan(reference)]
    current = current[~np.isnan(current)]

    if len(reference) == 0 or len(current) == 0:
        return 0.0

    stat, _ = ks_2samp(reference, current)
    return float(stat)


def status_from_value(value: float, safe: float, warning: float) -> str:
    """Return traffic-light status based on thresholds."""
    if value < safe:
        return "green"
    elif value < warning:
        return "yellow"
    else:
        return "red"


def compute_drift():
    """Main function: compute drift for all numeric features."""
    print("=" * 60)
    print("Drift Monitoring – PSI + KS")
    print("=" * 60)

    # ---------- Load reference ----------
    if not REFERENCE_PATH.exists():
        raise FileNotFoundError(f"Reference data not found: {REFERENCE_PATH}")

    reference = pd.read_parquet(REFERENCE_PATH)
    print(f"✅ Loaded reference: {reference.shape}")

    # ---------- Load current (or generate simulated shifted data) ----------
    if CURRENT_DATA_PATH.exists():
        current = pd.read_parquet(CURRENT_DATA_PATH)
        print(f"✅ Loaded current traffic: {current.shape}")
    else:
        print("⚠️ No current traffic file found. Simulating a shifted cohort...")
        current = simulate_shifted_traffic(reference)
        CURRENT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        current.to_parquet(CURRENT_DATA_PATH, index=False)
        print(f"✅ Simulated and saved current traffic: {current.shape}")

    # ---------- Compute drift per numeric feature ----------
    numeric_cols = reference.select_dtypes(include=['int64', 'float64']).columns.tolist()

    results = []
    for col in numeric_cols:
        if col not in current.columns:
            continue
        ref_vals = reference[col].values
        cur_vals = current[col].values

        psi = compute_psi(ref_vals, cur_vals)
        ks = compute_ks(ref_vals, cur_vals)

        psi_status = status_from_value(psi, PSI_SAFE, PSI_WARNING)
        ks_status = status_from_value(ks, KS_SAFE, KS_WARNING)

        overall = "red" if "red" in (psi_status, ks_status) else \
                  "yellow" if "yellow" in (psi_status, ks_status) else "green"

        results.append({
            'feature': col,
            'psi': round(psi, 4),
            'ks': round(ks, 4),
            'psi_status': psi_status,
            'ks_status': ks_status,
            'status': overall
        })

    # ---------- Summary ----------
    n_green = sum(1 for r in results if r['status'] == 'green')
    n_yellow = sum(1 for r in results if r['status'] == 'yellow')
    n_red = sum(1 for r in results if r['status'] == 'red')

    overall_status = "red" if n_red > 0 else "yellow" if n_yellow > 0 else "green"

    report = {
        'timestamp': datetime.now().isoformat(),
        'reference_size': len(reference),
        'current_size': len(current),
        'n_features_checked': len(results),
        'summary': {
            'green': n_green,
            'yellow': n_yellow,
            'red': n_red,
            'overall_status': overall_status
        },
        'features': results,
        'thresholds': {
            'psi_safe': PSI_SAFE,
            'psi_warning': PSI_WARNING,
            'ks_safe': KS_SAFE,
            'ks_warning': KS_WARNING
        }
    }

    DRIFT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DRIFT_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)

    # ---------- Print summary ----------
    print("\n📊 Drift Summary:")
    print(f"   Features checked: {len(results)}")
    print(f"   🟢 Green:  {n_green}")
    print(f"   🟡 Yellow: {n_yellow}")
    print(f"   🔴 Red:    {n_red}")
    print(f"   Overall: {overall_status.upper()}")

    # ---------- Top drifting features ----------
    sorted_results = sorted(results, key=lambda x: x['psi'], reverse=True)
    print("\n📋 Top 5 drifting features (by PSI):")
    for r in sorted_results[:5]:
        icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}[r['status']]
        print(f"   {icon} {r['feature']}: PSI={r['psi']:.4f}, KS={r['ks']:.4f}")

    print(f"\n✅ Report saved to {DRIFT_REPORT_PATH}")
    return report


def simulate_shifted_traffic(reference: pd.DataFrame, shift_factor: float = 1.4) -> pd.DataFrame:
    """Simulate a shifted cohort for testing."""
    np.random.seed(42)
    current = reference.sample(n=min(1000, len(reference)), replace=True).copy()

    numeric_cols = current.select_dtypes(include=['int64', 'float64']).columns
    for col in numeric_cols:
        # Convert to float first to allow decimal shifts
        current[col] = current[col].astype('float64')

        mask = np.random.rand(len(current)) < 0.4
        noise = np.random.normal(1.0, 0.1, size=len(current))
        current.loc[mask, col] = current.loc[mask, col] * shift_factor * noise[mask]

    return current.reset_index(drop=True)


if __name__ == "__main__":
    compute_drift()