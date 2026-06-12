"""
Day 6 deliverable: VaR/CVaR, rolling Sharpe, cohort analysis, SIP continuity,
sector HHI concentration, and fund recommender integration.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import CHARTS_DIR, DB_PATH, PROCESSED_DIR, REPORTS_DIR, ensure_dirs
from recommender import recommend_funds

FUND_NAMES = {
    125497: "HDFC Top 100",
    119551: "SBI Bluechip",
    120503: "ICICI Bluechip",
    118632: "Nippon Large Cap",
    119092: "Axis Bluechip",
    120841: "Kotak Bluechip",
}

TRADING_DAYS = 252
INSIGHTS_PATH = REPORTS_DIR / "advanced_insights.md"


def load_nav_pivot() -> tuple[pd.DataFrame, pd.DataFrame]:
    engine = create_engine(f"sqlite:///{DB_PATH}")
    nav = pd.read_sql("SELECT * FROM fact_nav", engine)
    nav["date"] = pd.to_datetime(nav["date"])
    code_col = "amfi_code" if "amfi_code" in nav.columns else "scheme_code"
    pivot = nav.pivot_table(index="date", columns=code_col, values="nav", aggfunc="last").ffill()
    daily = pivot.pct_change().dropna()
    return pivot, daily


def compute_var_cvar(daily: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in daily.columns:
        r = daily[col].dropna() * 100
        var_95 = np.percentile(r, 5)
        cvar = r[r <= var_95].mean() if (r <= var_95).any() else var_95
        rows.append({
            "amfi_code": col,
            "scheme_name": FUND_NAMES.get(col, str(col)),
            "VaR_95_pct": round(var_95, 4),
            "CVaR_pct": round(cvar, 4),
        })
    return pd.DataFrame(rows).sort_values("VaR_95_pct")


def plot_rolling_sharpe(daily: pd.DataFrame, codes: list | None = None) -> Path:
    codes = codes or list(daily.columns[:5])
    rolling = (daily.rolling(90).mean() / daily.rolling(90).std() * np.sqrt(TRADING_DAYS)).dropna(how="all")
    fig, ax = plt.subplots(figsize=(11, 4))
    for code in codes:
        if code in rolling.columns:
            ax.plot(rolling.index, rolling[code], label=FUND_NAMES.get(code, code), linewidth=1.2)
    ax.set_title("Rolling 90-Day Sharpe Ratio — Key Funds", fontweight="bold")
    ax.set_ylabel("Sharpe Ratio")
    ax.legend(fontsize=8)
    fig.tight_layout()
    out = CHARTS_DIR / "rolling_sharpe_chart.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out


def cohort_analysis(tx: pd.DataFrame) -> pd.DataFrame:
    tx = tx.copy()
    tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
    tx["cohort_year"] = tx.groupby("investor_id")["transaction_date"].transform("min").dt.year
    sip = tx[tx["transaction_type"] == "SIP"]
    cohort = sip.groupby("cohort_year").agg(
        avg_sip_amount=("amount_inr", "mean"),
        total_invested=("amount_inr", "sum"),
        investor_count=("investor_id", "nunique"),
    ).reset_index()
    top_fund = (
        sip.groupby(["cohort_year", "amfi_code"])["amount_inr"].sum()
        .reset_index()
        .sort_values(["cohort_year", "amount_inr"], ascending=[True, False])
        .drop_duplicates("cohort_year")
    )
    cohort = cohort.merge(top_fund[["cohort_year", "amfi_code"]], on="cohort_year", how="left")
    cohort["top_fund"] = cohort["amfi_code"].map(FUND_NAMES)
    return cohort


def sip_continuity(tx: pd.DataFrame) -> pd.DataFrame:
    tx = tx.copy()
    tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
    sip = tx[tx["transaction_type"] == "SIP"].sort_values(["investor_id", "transaction_date"])
    gaps = sip.groupby("investor_id")["transaction_date"].diff().dt.days
    sip = sip.assign(gap_days=gaps)
    eligible = sip.groupby("investor_id").size()
    eligible_ids = eligible[eligible >= 6].index
    subset = sip[sip["investor_id"].isin(eligible_ids)]
    avg_gap = subset.groupby("investor_id")["gap_days"].mean()
    result = avg_gap.reset_index()
    result.columns = ["investor_id", "avg_gap_days"]
    result["at_risk"] = result["avg_gap_days"] > 35
    return result


def sector_hhi(holdings: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for code, grp in holdings.groupby("amfi_code"):
        sector_w = grp.groupby("sector")["weight_pct"].sum()
        total = sector_w.sum()
        if total <= 0:
            continue
        weights = (sector_w / total).values
        hhi = (weights ** 2).sum()
        rows.append({
            "amfi_code": code,
            "scheme_name": FUND_NAMES.get(code, code),
            "HHI": round(hhi, 4),
            "concentration": "High" if hhi > 0.18 else "Moderate" if hhi > 0.12 else "Diversified",
        })
    return pd.DataFrame(rows).sort_values("HHI", ascending=False)


def write_insights(var_df: pd.DataFrame, cohort: pd.DataFrame, continuity: pd.DataFrame, hhi: pd.DataFrame) -> None:
    at_risk_pct = continuity["at_risk"].mean() * 100 if len(continuity) else 0
    worst_var = var_df.iloc[0]
    best_hhi = hhi.iloc[-1] if len(hhi) else None
    top_cohort = cohort.sort_values("total_invested", ascending=False).iloc[0] if len(cohort) else None

    lines = [
        "# Advanced Analytics — Key Insights",
        "",
        f"1. **Highest VaR (95%)**: {worst_var['scheme_name']} at {worst_var['VaR_95_pct']:.2f}% daily — "
        "highest tail-risk among anchor large-cap funds.",
        "",
        f"2. **Investor cohorts**: {top_cohort['cohort_year'] if top_cohort is not None else 'N/A'} cohort "
        f"shows highest total SIP investment (Rs {top_cohort['total_invested']/1e7:.1f} Cr equivalent) "
        f"with preference for {top_cohort['top_fund'] if top_cohort is not None else 'N/A'}.",
        "",
        f"3. **SIP continuity**: {at_risk_pct:.1f}% of investors with 6+ SIPs have average inter-SIP gap "
        "> 35 days and are flagged as at-risk for discontinuation.",
        "",
        f"4. **Portfolio concentration**: {best_hhi['scheme_name'] if best_hhi is not None else 'N/A'} "
        f"has the most diversified sector allocation (HHI = {best_hhi['HHI'] if best_hhi is not None else 0:.3f}).",
        "",
        "5. **Fund recommender**: High-risk appetite investors are best served by top Sharpe-ranked "
        "large-cap direct plans per the composite scorecard (see recommender.py output).",
    ]
    INSIGHTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Insights -> {INSIGHTS_PATH}")


def run_advanced() -> None:
    ensure_dirs()
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}. Run etl_pipeline.py first.")

    pivot, daily = load_nav_pivot()
    var_df = compute_var_cvar(daily)
    var_df.to_csv(REPORTS_DIR / "var_cvar_report.csv", index=False)
    var_df.to_csv(PROCESSED_DIR / "var_cvar_report.csv", index=False)

    plot_rolling_sharpe(daily)

    tx = pd.read_csv(PROCESSED_DIR / "08_investor_transactions_clean.csv")
    cohort = cohort_analysis(tx)
    cohort.to_csv(REPORTS_DIR / "investor_cohort_analysis.csv", index=False)

    continuity = sip_continuity(tx)
    continuity.to_csv(REPORTS_DIR / "sip_continuity_analysis.csv", index=False)

    holdings = pd.read_csv(PROCESSED_DIR / "09_portfolio_holdings_clean.csv")
    hhi = sector_hhi(holdings)
    hhi.to_csv(REPORTS_DIR / "sector_hhi.csv", index=False)

    write_insights(var_df, cohort, continuity, hhi)

    print("\nFund Recommender (High risk appetite):")
    print(recommend_funds("High", top_n=3).to_string(index=False))


def main() -> None:
    run_advanced()


if __name__ == "__main__":
    main()
