"""
ETL pipeline: clean datasets, gap-fill NAV, load SQLite star schema.

Day 2 deliverable: etl_pipeline.py (replaces root eda_analysis.py)
"""

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "db" / "bluestock_mf.db"

RAW_DATASETS = [
    "01_fund_master.csv",
    "02_nav_history.csv",
    "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv",
    "05_category_inflows.csv",
    "06_industry_folio_count.csv",
    "07_scheme_performance.csv",
    "08_investor_transactions.csv",
    "09_portfolio_holdings.csv",
    "10_benchmark_indices.csv",
]


def ensure_dirs() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

CODE_ALIASES = ("amfi_code", "scheme_code")
TX_TYPE_MAP = {
    "SIP": "SIP",
    "LUMPSUM": "Lumpsum",
    "LUMP SUM": "Lumpsum",
    "REDEMPTION": "Redemption",
}


def _code_column(df: pd.DataFrame) -> str:
    for col in CODE_ALIASES:
        if col in df.columns:
            return col
    raise ValueError(f"No scheme code column in {df.columns.tolist()}")


def clean_nav_history() -> pd.DataFrame | None:
    """Parse dates, dedupe, forward-fill holidays/weekends, validate NAV > 0."""
    raw_path = RAW_DIR / "02_nav_history.csv"
    if not raw_path.exists():
        return None

    df = pd.read_csv(raw_path)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    code_col = _code_column(df)
    if code_col == "scheme_code" and "amfi_code" not in df.columns:
        df["amfi_code"] = df["scheme_code"]

    df = df.dropna(subset=["date", code_col])
    df = df[df["nav"] > 0]
    df = df.drop_duplicates(subset=[code_col, "date"])
    df = df.sort_values([code_col, "date"])

    min_date, max_date = df["date"].min(), df["date"].max()
    all_dates = pd.date_range(min_date, max_date, freq="D")
    funds = df[code_col].unique()
    index = pd.MultiIndex.from_product([funds, all_dates], names=[code_col, "date"])
    full = index.to_frame(index=False)
    merged = full.merge(df, on=[code_col, "date"], how="left")
    merged["nav"] = merged.groupby(code_col)["nav"].ffill()
    merged = merged.dropna(subset=["nav"])
    merged["daily_return"] = merged.groupby(code_col)["nav"].pct_change()

    out = PROCESSED_DIR / "02_nav_history_clean.csv"
    merged.to_csv(out, index=False)
    return merged


def clean_transactions() -> pd.DataFrame | None:
    """Standardise transaction types, amounts, dates, and KYC values."""
    raw_path = RAW_DIR / "08_investor_transactions.csv"
    if not raw_path.exists():
        return None

    df = pd.read_csv(raw_path)
    if "amount_inr" not in df.columns and "amount" in df.columns:
        df = df.rename(columns={"amount": "amount_inr"})

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["transaction_type"] = (
        df["transaction_type"].astype(str).str.strip().str.upper().map(TX_TYPE_MAP).fillna(
            df["transaction_type"].astype(str).str.strip().str.title()
        )
    )
    df = df[df["amount_inr"] > 0]
    df["kyc_status"] = df["kyc_status"].astype(str).str.strip().str.title()
    df = df.reset_index(drop=True)
    df.insert(0, "transaction_id", range(1, len(df) + 1))

    out = PROCESSED_DIR / "08_investor_transactions_clean.csv"
    df.to_csv(out, index=False)
    return df


def clean_scheme_performance() -> pd.DataFrame | None:
    """Validate numeric returns and clip expense ratio to 0.1%–2.5%."""
    raw_path = RAW_DIR / "07_scheme_performance.csv"
    if not raw_path.exists():
        return None

    df = pd.read_csv(raw_path)
    if "status" in df.columns and len(df.columns) <= 2:
        return None

    numeric_cols = [c for c in df.columns if "return" in c.lower() or c in ("sharpe_ratio", "alpha", "beta")]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    er_col = next((c for c in df.columns if "expense" in c.lower()), None)
    if er_col:
        df[er_col] = pd.to_numeric(df[er_col], errors="coerce").clip(0.1, 2.5)

    out = PROCESSED_DIR / "07_scheme_performance_clean.csv"
    df.to_csv(out, index=False)
    return df


def passthrough_clean(name: str) -> None:
    """Copy raw file to processed when no transform is required."""
    raw_path = RAW_DIR / name
    if not raw_path.exists():
        return
    df = pd.read_csv(raw_path)
    if "status" in df.columns and len(df.columns) <= 2:
        return
    clean_name = name.replace(".csv", "_clean.csv")
    df.to_csv(PROCESSED_DIR / clean_name, index=False)


def load_sqlite(nav_df: pd.DataFrame | None, tx_df: pd.DataFrame | None, perf_df: pd.DataFrame | None) -> None:
    """Load cleaned tables into SQLite using SQLAlchemy."""
    ensure_dirs()
    schema_path = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
    engine = create_engine(f"sqlite:///{DB_PATH}")

    if schema_path.exists():
        with engine.begin() as conn:
            for stmt in schema_path.read_text(encoding="utf-8").split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))

    fund_path = PROCESSED_DIR / "01_fund_master_clean.csv"
    if not fund_path.exists():
        fund_path = RAW_DIR / "01_fund_master.csv"
    if fund_path.exists():
        funds = pd.read_csv(fund_path)
        if "scheme_code" in funds.columns and "amfi_code" not in funds.columns:
            funds["amfi_code"] = funds["scheme_code"]
        funds.to_sql("dim_fund", engine, if_exists="replace", index=False)

    if nav_df is not None:
        dates = pd.DataFrame({"date": nav_df["date"].unique()})
        dates["year"] = dates["date"].dt.year
        dates["month"] = dates["date"].dt.month
        dates["quarter"] = dates["date"].dt.quarter
        dates["day"] = dates["date"].dt.day
        dates["is_weekday"] = dates["date"].dt.dayofweek < 5
        dates["date"] = dates["date"].dt.strftime("%Y-%m-%d")
        dates.to_sql("dim_date", engine, if_exists="replace", index=False)

        nav_load = nav_df.copy()
        nav_load["date"] = nav_load["date"].dt.strftime("%Y-%m-%d")
        nav_load.to_sql("fact_nav", engine, if_exists="replace", index=False)

    if tx_df is not None:
        tx_load = tx_df.copy()
        tx_load["transaction_date"] = tx_load["transaction_date"].dt.strftime("%Y-%m-%d")
        tx_load.to_sql("fact_transactions", engine, if_exists="replace", index=False)

    if perf_df is not None:
        perf_df.to_sql("fact_performance", engine, if_exists="replace", index=False)

    for table, fname in (
        ("fact_aum", "03_aum_by_fund_house_clean.csv"),
        ("fact_sip_industry", "04_monthly_sip_inflows_clean.csv"),
    ):
        p = PROCESSED_DIR / fname
        if p.exists():
            pd.read_csv(p).to_sql(table, engine, if_exists="replace", index=False)


def verify_row_counts(nav_df: pd.DataFrame | None) -> None:
    """Compare CSV row counts with SQLite after load."""
    if nav_df is None:
        return
    engine = create_engine(f"sqlite:///{DB_PATH}")
    db_count = pd.read_sql("SELECT COUNT(*) AS n FROM fact_nav", engine).iloc[0]["n"]
    print(f"fact_nav rows — CSV: {len(nav_df)}, DB: {db_count}, match: {len(nav_df) == db_count}")


def run_etl() -> None:
    """Execute full clean + load pipeline."""
    ensure_dirs()
    for name in RAW_DATASETS:
        if name not in ("02_nav_history.csv", "07_scheme_performance.csv", "08_investor_transactions.csv"):
            passthrough_clean(name)

    nav_df = clean_nav_history()
    tx_df = clean_transactions()
    perf_df = clean_scheme_performance()
    load_sqlite(nav_df, tx_df, perf_df)
    verify_row_counts(nav_df)
    print(f"ETL complete -> {DB_PATH}")


def main() -> None:
    run_etl()


if __name__ == "__main__":
    main()
