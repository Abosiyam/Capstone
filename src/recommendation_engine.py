# ============================================================================
# src/recommendation_engine.py – Fast Rule Serving for Head B
# ============================================================================
# Loads rules from artifacts/rules.json, indexes them by antecedent item,
# and provides millisecond-fast recommendations for a given basket.
# ============================================================================

import json
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

RULES_PATH = Path(__file__).parent.parent / 'artifacts' / 'rules.json'


class RecommendationEngine:
    """In-memory rule serving engine indexed by antecedent item."""

    def __init__(self, rules_path: Path = RULES_PATH):
        self.rules_path = rules_path
        self.rules: List[Dict] = []
        self.index: Dict[str, List[Dict]] = defaultdict(list)
        self.metadata: Dict = {}
        self._load()

    def _load(self):
        """Load rules from JSON and build the antecedent index."""
        if not self.rules_path.exists():
            raise FileNotFoundError(f"Rules file not found: {self.rules_path}")

        with open(self.rules_path, 'r') as f:
            payload = json.load(f)

        self.metadata = payload.get('metadata', {})
        self.rules = payload.get('rules', [])

        # Build index: for each rule, index it under each antecedent item.
        for rule in self.rules:
            for item in rule['antecedents']:
                self.index[item].append(rule)

        print(f"✅ Loaded {len(self.rules)} rules")
        print(f"   Mining date: {self.metadata.get('mining_date', 'unknown')}")
        print(f"   Indexed antecedents: {len(self.index)}")

    def recommend(self, basket: List[str], n: int = 5) -> Dict:
        """
        Given a basket, return the top N recommendations.

        Strategy:
            1. Find all rules whose antecedents are a subset of the basket.
            2. Deduplicate by consequent, keeping the highest lift.
            3. Exclude items already in the basket.
            4. Return the top N sorted by lift.
        """
        # ---------- Handle empty basket ----------
        if not basket:
            return {
                'strategy': 'empty_basket',
                'recommendations': [],
                'message': 'Basket is empty. Please add items first.'
            }

        basket_set = set(basket)

        # ---------- Collect firing rules ----------
        candidates: Dict[str, Dict] = {}  # consequent -> best rule

        for item in basket_set:
            for rule in self.index.get(item, []):
                # All antecedents must be in the basket
                if not set(rule['antecedents']).issubset(basket_set):
                    continue

                for consequent in rule['consequents']:
                    # Skip items already in the basket
                    if consequent in basket_set:
                        continue

                    # Keep the highest lift for each consequent
                    if consequent not in candidates or rule['lift'] > candidates[consequent]['lift']:
                        candidates[consequent] = {
                            'item': consequent,
                            'lift': rule['lift'],
                            'confidence': rule['confidence'],
                            'support': rule['support'],
                            'because': sorted(rule['antecedents'])
                        }

        # ---------- Sort by lift ----------
        ranked = sorted(candidates.values(), key=lambda x: x['lift'], reverse=True)
        top = ranked[:n]

        # ---------- Handle no-match basket ----------
        if not top:
            return {
                'strategy': 'no_match',
                'recommendations': [],
                'message': 'No rules matched this basket. Returning empty list.'
            }

        return {
            'strategy': 'rules',
            'recommendations': top,
            'n_returned': len(top)
        }

    def explain(self, item: str, basket: List[str]) -> Optional[Dict]:
        """Return the highest-lift rule that recommended `item` for `basket`."""
        basket_set = set(basket)
        best = None
        for rule in self.index.get(item, []):
            if item in rule['consequents'] and set(rule['antecedents']).issubset(basket_set):
                if best is None or rule['lift'] > best['lift']:
                    best = rule
        return best

    def stats(self) -> Dict:
        """Return engine statistics."""
        return {
            'rule_count': len(self.rules),
            'indexed_antecedents': len(self.index),
            'mining_date': self.metadata.get('mining_date'),
            'min_support': self.metadata.get('min_support'),
            'min_confidence': self.metadata.get('min_confidence'),
            'min_lift': self.metadata.get('min_lift')
        }


# ---------- Self-test ----------
if __name__ == "__main__":
    print("=" * 60)
    print("Head B – Recommendation Engine Self-Test")
    print("=" * 60)

    engine = RecommendationEngine()
    print("\n📊 Engine stats:")
    for k, v in engine.stats().items():
        print(f"   {k}: {v}")

    # Show a sample rule
    print("\n📋 Sample rule:")
    if engine.rules:
        print(json.dumps(engine.rules[0], indent=2))

    # Test with the first rule's antecedents
    if engine.rules:
        test_basket = engine.rules[0]['antecedents']
        print(f"\n🧺 Test basket: {test_basket}")
        result = engine.recommend(test_basket, n=5)
        print(json.dumps(result, indent=2))

    # Test empty basket
    print("\n🧺 Empty basket test:")
    print(json.dumps(engine.recommend([], n=5), indent=2))

    print("\n✅ Self-test complete!")