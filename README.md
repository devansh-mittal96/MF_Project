# Capstone Project 1 — Mutual Fund Analytics

**Company:** Bluestock Fintech Pvt. Ltd.  
**Prepared by:** Devansh Mittal  
**Project Manager:** Yash Kale  
**Educational use only — not financial advice.**

End-to-end ETL pipeline, SQLite analytics database, 15+ EDA charts, performance metrics, advanced risk analytics, PDF report, and presentation for Indian large-cap mutual funds.

---

## Project Structure

```
MF_Project/
├── data/
│   ├── raw/              # 10 CSV datasets + live NAV downloads
│   ├── processed/        # Cleaned CSV outputs (*_clean.csv)
│   └── db/               # bluestock_mf.db (regenerate via pipeline)
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── EDA_Analysis.ipynb          # Day 3
│   ├── Performance_Analytics.ipynb # Day 4
│   └── Advanced_Analytics.ipynb    # Day 6
├── scripts/
│   ├── paths.py
│   ├── generate_industry_data.py
│   ├── live_nav_fetch.py
│   ├── data_ingestion.py
│   ├── etl_pipeline.py
│   ├── compute_metrics.py
│   ├── export_eda_charts.py
│   ├── advanced_analytics.py
│   ├── recommender.py
│   └── create_presentation.py
├── sql/
│   ├── schema.sql
│   └── queries.sql
├── dashboard/            # Place bluestock_mf_dashboard.pbix here
├── reports/
│   ├── charts/           # 15+ PNG charts
│   ├── Final_Report.pdf
│   ├── Bluestock_MF_Presentation.pptx
│   ├── fund_scorecard.csv
│   └── var_cvar_report.csv
├── run_pipeline.py       # Master one-command runner
├── generate_report.py
├── data_dictionary.md
└── requirements.txt
```

---

## Setup

```bash
pip install -r requirements.txt
```

Place the 10 provided CSV datasets in `data/raw/` (or let `generate_industry_data.py` populate industry reference files automatically).

---

## Run Everything (One Command)

From project root:

```bash
python run_pipeline.py
```

This executes:

| Stage | Script | Output |
|-------|--------|--------|
| 1 | `generate_industry_data.py` | Industry AUM, SIP, folio, holdings CSVs |
| 2 | `live_nav_fetch.py` | Live NAV from mfapi.in (6 schemes) |
| 3 | `data_ingestion.py` | Validated raw data + quality summary |
| 4 | `etl_pipeline.py` | Clean CSVs + SQLite DB |
| 5 | `compute_metrics.py` | Scorecard, alpha/beta, performance charts |
| 6 | `export_eda_charts.py` | 15 EDA PNG charts |
| 7 | `advanced_analytics.py` | VaR/CVaR, cohort, HHI, rolling Sharpe |
| 8 | `generate_report.py` | Final_Report.pdf (15-20 pages) |
| 9 | `create_presentation.py` | Bluestock_MF_Presentation.pptx (12 slides) |

---

## Day-by-Day Deliverables

| Day | Deliverable | Location |
|-----|-------------|----------|
| 1 | Data ingestion | `data_ingestion.py`, `live_nav_fetch.py` |
| 2 | Clean data + DB | `data/processed/`, `data/db/bluestock_mf.db`, `sql/` |
| 3 | EDA (15+ charts) | `notebooks/EDA_Analysis.ipynb`, `reports/charts/eda_*.png` |
| 4 | Performance | `Performance_Analytics.ipynb`, `fund_scorecard.csv` |
| 5 | Dashboard | `dashboard/bluestock_mf_dashboard.pbix` (Power BI) |
| 6 | Advanced analytics | `Advanced_Analytics.ipynb`, `var_cvar_report.csv`, `recommender.py` |
| 7 | Final report + PPT | `reports/Final_Report.pdf`, `Bluestock_MF_Presentation.pptx` |

---

## Fund Recommender

```bash
python scripts/recommender.py
```

Input: risk appetite (`Low` / `Moderate` / `High`). Output: top 3 funds by Sharpe ratio.

---

## Dashboard (Power BI)

1. Open Power BI Desktop.
2. **Get Data** → SQLite or import `data/processed/*.csv`.
3. Build 4 pages: Industry Overview, Fund Performance, Investor Analytics, SIP & Market Trends.
4. Save as `dashboard/bluestock_mf_dashboard.pbix`.

---

## Team

| Role | Name |
|------|------|
| Lead / Report Author | Devansh Mittal |
| Project Manager | Yash Kale |
| Team | madhukatta0731, krishnavamsibommireddy07, mujaseem78 |

---

## Dataset Descriptions

See `data_dictionary.md` for full column definitions.

| File | Description |
|------|-------------|
| `01_fund_master.csv` | Scheme metadata (AMFI code, AMC, category, risk) |
| `02_nav_history.csv` | Daily NAV time series |
| `03_aum_by_fund_house.csv` | AUM by AMC and year |
| `04_monthly_sip_inflows.csv` | Monthly SIP industry data |
| `05_category_inflows.csv` | Category-wise net inflows |
| `06_industry_folio_count.csv` | Industry folio milestones |
| `07_scheme_performance.csv` | Return and risk metrics per scheme |
| `08_investor_transactions.csv` | Investor transactions with demographics |
| `09_portfolio_holdings.csv` | Top equity holdings by fund |
| `10_benchmark_indices.csv` | NIFTY 50 / NIFTY 100 prices |
