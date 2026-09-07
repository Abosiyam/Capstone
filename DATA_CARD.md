# DATA_CARD.md

## 📊 Dataset Information

| Property | Value |
|----------|-------|
| **Name** | Online Retail II |
| **Source** | UCI Machine Learning Repository |
| **URL** | https://archive.ics.uci.edu/dataset/502/online+retail+ii |
| **Licence** | CC BY 4.0 |
| **Description** | Real transaction data from a UK-based online retailer |
| **Date range** | December 2009 – December 2011 |
| **Rows (raw)** | 525,461 |
| **Rows (after cleaning)** | 400,916 |
| **Columns** | InvoiceNo, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country |

---

## 🧹 Cleaning Summary

| Step | Action |
|------|--------|
| 1 | Removed cancelled invoices (InvoiceNo starting with 'C') |
| 2 | Removed non-positive Quantity or Price |
| 3 | Removed rows without Customer ID |
| 4 | Removed duplicate rows |
| 5 | Converted InvoiceDate to datetime |
| 6 | Standardised country names |
| 7 | Renamed 'Invoice' to 'InvoiceNo' |
| 8 | Converted StockCode to string |

---

## 🎯 Intended Use

| Head | Task |
|------|------|
| **A – Prédiction** | Customer retention prediction (will they buy in next 90 days?) |
| **B – Recommandation** | Association rule mining for product recommendations |
| **C – Assistant** | Grounded retrieval‑augmented generation for customer support |

---

## ⚠️ Limitations

- Data is from a UK retailer – may not generalise to Quebec/Canada
- Descriptions are in English only
- No explicit product categories
- Customer IDs are anonymised

---

## 🔐 Data Integrity

- **SHA‑256 (raw Excel):** `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`
- Checksum stored in `data/raw/online_retail_ii.sha256`

---

## 📂 File Locations

| File | Path |
|------|------|
| Raw Excel | `data/raw/online_retail_II.xlsx` |
| Cleaned Parquet | `data/silver/online_retail_ii_clean.parquet` |
| Checksum | `data/raw/online_retail_ii.sha256` |
