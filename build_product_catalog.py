# ============================================================================
# build_product_catalog.py – Build a product catalog for Head C's product_lookup
# ============================================================================

import json
import pandas as pd
from pathlib import Path

DATA_PATH = Path('data/silver/online_retail_ii_clean.parquet')
OUTPUT_PATH = Path('artifacts/product_catalog.json')


def main():
    print("Loading clean data...")
    df = pd.read_parquet(DATA_PATH)

    print("Aggregating by StockCode...")
    agg = df.groupby('StockCode').agg({
        'Description': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown',
        'Price': ['mean', 'min', 'max'],
        'Quantity': 'sum',
        'InvoiceNo': 'nunique'
    })

    agg.columns = ['description', 'avg_price', 'min_price', 'max_price',
                   'total_quantity', 'times_ordered']

    catalog = {}
    for stock_code, row in agg.iterrows():
        catalog[str(stock_code)] = {
            'stock_code': str(stock_code),
            'description': str(row['description']),
            'avg_price': round(float(row['avg_price']), 2),
            'min_price': round(float(row['min_price']), 2),
            'max_price': round(float(row['max_price']), 2),
            'total_quantity': int(row['total_quantity']),
            'times_ordered': int(row['times_ordered'])
        }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2)

    print(f"✅ Saved {len(catalog)} products to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()