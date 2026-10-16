# ============================================================================
# src/evaluate_recommendation.py – Offline evaluation of Head B
# ============================================================================
# Evaluates the recommendation engine using a temporal holdout.
# Computes Hit-rate@5 and coverage against a global-popularity baseline.
# ============================================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pandas as pd
import numpy as np
from datetime import datetime
from collections import Counter
from mlxtend.frequent_patterns import fpgrowth, association_rules
from mlxtend.preprocessing import TransactionEncoder

# ---------- Paths ----------
DATA_PATH = Path(__file__).parent.parent / 'data' / 'silver' / 'online_retail_ii_clean.parquet'
OUTPUT_PATH = Path(__file__).parent.parent / 'artifacts' / 'recommendation_evaluation.json'

# ---------- Config ----------
MIN_SUPPORT = 0.02
MIN_CONFIDENCE = 0.3
MIN_LIFT = 1.5
TOP_N = 5
TRAIN_RATIO = 0.8


def load_data():
    df = pd.read_parquet(DATA_PATH)
    print(f"✅ Loaded {len(df):,} rows")
    return df


def build_baskets_with_dates(df):
    """Return a list of (date, [items]) for each invoice."""
    df = df.sort_values('InvoiceDate')
    baskets = df.groupby('InvoiceNo').agg({
        'StockCode': lambda x: list(set(x)),
        'InvoiceDate': 'first'
    }).reset_index()
    baskets = baskets.sort_values('InvoiceDate')
    basket_list = [(row['InvoiceDate'], row['StockCode']) for _, row in baskets.iterrows()]
    print(f"✅ Built {len(basket_list):,} baskets (with dates)")
    return basket_list


def temporal_split(basket_list, train_ratio=0.8):
    split_idx = int(len(basket_list) * train_ratio)
    train = basket_list[:split_idx]
    test = basket_list[split_idx:]
    print(f"✅ Train: {len(train):,} | Test: {len(test):,}")
    return train, test


def mine_rules(baskets, min_support=0.02, min_confidence=0.3, min_lift=1.5):
    """Mine association rules from a list of baskets."""
    print(f"   Mining rules on {len(baskets)} baskets...")
    te = TransactionEncoder()
    te_array = te.fit([b[1] for b in baskets]).transform([b[1] for b in baskets])
    dense_df = pd.DataFrame(te_array, columns=te.columns_)

    frequent = fpgrowth(dense_df, min_support=min_support, use_colnames=True)
    if len(frequent) == 0:
        return []
    rules = association_rules(frequent, metric="confidence", min_threshold=min_confidence)
    rules = rules[rules['lift'] >= min_lift].copy()
    rules = rules.sort_values('lift', ascending=False)

    rules_list = []
    for _, row in rules.iterrows():
        rules_list.append({
            'antecedents': list(row['antecedents']),
            'consequents': list(row['consequents']),
            'support': float(row['support']),
            'confidence': float(row['confidence']),
            'lift': float(row['lift']),
        })
    print(f"   ✅ Mined {len(rules_list)} rules")
    return rules_list


def build_index(rules):
    index = {}
    for rule in rules:
        for item in rule['antecedents']:
            index.setdefault(item, []).append(rule)
    return index


def recommend(basket, index, top_n=5):
    basket_set = set(basket)
    candidates = {}
    for item in basket_set:
        for rule in index.get(item, []):
            if not set(rule['antecedents']).issubset(basket_set):
                continue
            for c in rule['consequents']:
                if c in basket_set:
                    continue
                if c not in candidates or rule['lift'] > candidates[c]['lift']:
                    candidates[c] = rule
    ranked = sorted(candidates.values(), key=lambda x: x['lift'], reverse=True)
    return [r['consequents'][0] for r in ranked[:top_n]]


def popularity_baseline(train_baskets, top_n=5):
    counter = Counter()
    for _, items in train_baskets:
        counter.update(items)
    return [item for item, _ in counter.most_common(top_n)]


def hit_rate_at_5(test_baskets, index, top_n=5):
    hits = 0
    total = 0
    recommended_items = set()
    for _, items in test_baskets:
        if len(items) < 2:
            continue
        target = items[-1]
        basket = items[:-1]
        recs = recommend(basket, index, top_n=top_n)
        recommended_items.update(recs)
        if target in recs:
            hits += 1
        total += 1
    return hits / total if total > 0 else 0.0, total, recommended_items


def popularity_hit_rate(test_baskets, popular_items, top_n=5):
    hits = 0
    total = 0
    for _, items in test_baskets:
        if len(items) < 2:
            continue
        target = items[-1]
        if target in popular_items:
            hits += 1
        total += 1
    return hits / total if total > 0 else 0.0


def main():
    print("=" * 60)
    print("Head B – Offline Evaluation (Hit-rate@5)")
    print("=" * 60)

    df = load_data()
    baskets = build_baskets_with_dates(df)
    train, test = temporal_split(baskets, TRAIN_RATIO)

    rules = mine_rules(train, MIN_SUPPORT, MIN_CONFIDENCE, MIN_LIFT)
    index = build_index(rules)

    popular_items = popularity_baseline(train, top_n=TOP_N)
    print(f"\n📊 Top {TOP_N} popular items: {popular_items}")

    # Our engine
    our_hit_rate, n_eval, recommended_items = hit_rate_at_5(test, index, TOP_N)
    all_items = set()
    for _, items in train:
        all_items.update(items)
    coverage = len(recommended_items) / len(all_items) if all_items else 0

    # Popularity baseline
    pop_hit_rate = popularity_hit_rate(test, popular_items, TOP_N)

    print("\n" + "=" * 60)
    print("📊 Results")
    print("=" * 60)
    print(f"Evaluated baskets:        {n_eval}")
    print(f"Our Hit-rate@5:           {our_hit_rate:.4f}")
    print(f"Popularity Hit-rate@5:    {pop_hit_rate:.4f}")
    print(f"Improvement over popularity: {our_hit_rate - pop_hit_rate:+.4f}")
    print(f"Coverage:                 {coverage:.4f}")

    results = {
        "evaluated_baskets": n_eval,
        "our_hit_rate@5": round(our_hit_rate, 4),
        "popularity_hit_rate@5": round(pop_hit_rate, 4),
        "improvement": round(our_hit_rate - pop_hit_rate, 4),
        "coverage": round(coverage, 4),
        "top_n": TOP_N,
        "min_support": MIN_SUPPORT,
        "min_confidence": MIN_CONFIDENCE,
        "min_lift": MIN_LIFT,
        "timestamp": datetime.now().isoformat(),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()