# ============================================================================
# src/recommendation.py – Association Rule Mining for Head B
# ============================================================================
# Extracts association rules from clean transaction data using FP-Growth.
# Saves rules to artifacts/rules.json with a metadata header.
# ============================================================================

import pandas as pd
import numpy as np
import json
import time
from pathlib import Path
from datetime import datetime
from mlxtend.frequent_patterns import apriori, fpgrowth, association_rules
from mlxtend.preprocessing import TransactionEncoder
from scipy.sparse import csr_matrix

# ---------- 1. Paths ----------
DATA_PATH = Path('../data/silver/online_retail_ii_clean.parquet')
RULES_PATH = Path('../artifacts/rules.json')
METRICS_PATH = Path('../artifacts/recommendation_metrics.json')


def load_data():
    """Load the cleaned transaction data."""
    df = pd.read_parquet(DATA_PATH)
    print(f"✅ Loaded {len(df):,} rows")
    return df


def build_baskets(df):
    """Build a list of unique baskets (one per invoice)."""
    print("\n🧺 Building baskets...")
    baskets = df.groupby('InvoiceNo')['StockCode'].apply(
        lambda x: list(set(x))
    ).tolist()
    print(f"✅ Built {len(baskets):,} baskets")
    return baskets


def build_sparse_matrix(baskets):
    """Build a sparse transaction matrix and report memory usage."""
    print("\n📊 Building sparse matrix...")
    te = TransactionEncoder()
    te_array = te.fit(baskets).transform(baskets)
    dense_df = pd.DataFrame(te_array, columns=te.columns_)
    sparse_matrix = csr_matrix(te_array)

    dense_size = dense_df.values.nbytes / (1024 ** 2)
    sparse_size = (sparse_matrix.data.nbytes + sparse_matrix.indices.nbytes + sparse_matrix.indptr.nbytes) / (1024 ** 2)

    print(f"   Dense size:  {dense_size:.2f} MB")
    print(f"   Sparse size: {sparse_size:.2f} MB")
    print(f"   Compression ratio: {dense_size / sparse_size:.1f}x")
    return dense_df, sparse_matrix


def mine_rules_apriori(dense_df, min_support=0.02, min_confidence=0.3):
    """Mine rules with Apriori (timed, for comparison)."""
    print("\n⏱️  Mining with Apriori...")
    start = time.time()
    frequent = apriori(dense_df, min_support=min_support, use_colnames=True)
    rules = association_rules(frequent, metric="confidence", min_threshold=min_confidence)
    elapsed = time.time() - start
    print(f"✅ Apriori: {len(rules)} rules in {elapsed:.2f}s")
    return rules, elapsed


def mine_rules_fpgrowth(dense_df, min_support=0.02, min_confidence=0.3):
    """Mine rules with FP-Growth (production choice, faster)."""
    print("\n⏱️  Mining with FP-Growth...")
    start = time.time()
    frequent = fpgrowth(dense_df, min_support=min_support, use_colnames=True)
    rules = association_rules(frequent, metric="confidence", min_threshold=min_confidence)
    elapsed = time.time() - start
    print(f"✅ FP-Growth: {len(rules)} rules in {elapsed:.2f}s")
    return rules, elapsed


def filter_by_lift(rules, min_lift=1.5):
    """Filter rules by lift and sort by lift descending."""
    print(f"\n🔍 Filtering by lift >= {min_lift}...")
    before = len(rules)
    rules = rules[rules['lift'] >= min_lift].copy()
    rules = rules.sort_values('lift', ascending=False)
    print(f"✅ Kept {len(rules)} rules (removed {before - len(rules)})")
    return rules


def save_rules(rules, mining_date, apriori_time, fpgrowth_time, support, confidence, lift):
    """Save rules to JSON with a metadata header."""
    RULES_PATH.parent.mkdir(parents=True, exist_ok=True)

    rules_list = []
    for _, row in rules.iterrows():
        rules_list.append({
            'antecedents': list(row['antecedents']),
            'consequents': list(row['consequents']),
            'support': round(float(row['support']), 6),
            'confidence': round(float(row['confidence']), 6),
            'lift': round(float(row['lift']), 6)
        })

    payload = {
        'metadata': {
            'mining_date': mining_date,
            'source_data': str(DATA_PATH),
            'min_support': support,
            'min_confidence': confidence,
            'min_lift': lift,
            'rule_count': len(rules_list),
            'apriori_time_seconds': round(apriori_time, 2),
            'fpgrowth_time_seconds': round(fpgrowth_time, 2)
        },
        'rules': rules_list
    }

    with open(RULES_PATH, 'w') as f:
        json.dump(payload, f, indent=2)

    print(f"\n✅ Saved {len(rules_list)} rules to {RULES_PATH}")


def main():
    print("=" * 60)
    print("Head B – Association Rule Mining")
    print("=" * 60)

    df = load_data()
    baskets = build_baskets(df)
    dense_df, sparse_matrix = build_sparse_matrix(baskets)

    min_support = 0.02
    min_confidence = 0.3
    min_lift = 1.5

    rules_apriori, apriori_time = mine_rules_apriori(dense_df, min_support, min_confidence)
    rules_fpgrowth, fpgrowth_time = mine_rules_fpgrowth(dense_df, min_support, min_confidence)

    rules = filter_by_lift(rules_fpgrowth, min_lift)

    mining_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_rules(rules, mining_date, apriori_time, fpgrowth_time,
               min_support, min_confidence, min_lift)

    # Save metrics
    metrics = {
        'total_baskets': len(baskets),
        'total_products': dense_df.shape[1],
        'apriori_time_seconds': round(apriori_time, 2),
        'fpgrowth_time_seconds': round(fpgrowth_time, 2),
        'rule_count_before_lift': len(rules_fpgrowth),
        'rule_count_after_lift': len(rules),
        'min_support': min_support,
        'min_confidence': min_confidence,
        'min_lift': min_lift
    }
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"\n✅ Metrics saved to {METRICS_PATH}")
    print("\n✅ Head B – Rule mining complete!")


if __name__ == "__main__":
    main()