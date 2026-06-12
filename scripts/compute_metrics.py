"""
Compute performance metrics, VaR/CVaR, fund scorecard, and export charts.

Day 4 + Day 6 deliverable: compute_metrics.py (replaces advanced_analytics.py)
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "db" / "bluestock_mf.db"
REPORTS_DIR = ROOT / "reports"
CHARTS_DIR = REPORTS_DIR / "charts"


def ensure_dirs() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

RF_ANNUAL = 0.065
TRADING_DAYS = 252


def load_nav() -> pd.DataFrame:
    """Load NAV fact table from SQLite."""
    engine = create_engine(f"sqlite:///{DB_PATH}")
    df = pd.read_sql("SELECT * FROM fact_nav", engine)
    df["date"] = pd.to_datetime(df["date"])
    code_col = "amfi_code" if "amfi_code" in df.columns else "scheme_code"
    return df, code_col


def period_cagr(nav_series: pd.Series, years: int) -> float:
    """CAGR over the last N calendar years using trading-day count."""
    nav_series = nav_series.dropna()
    if len(nav_series) < 2:
        return np.nan
    end = nav_series.index[-1]
    start_target = end - pd.DateOffset(years=years)
    subset = nav_series[nav_series.index >= start_target]
    if len(subset) < 2:
        subset = nav_series
    n_days = len(subset) - 1
    if n_days <= 0:
        return np.nan
    return (subset.iloc[-1] / subset.iloc[0]) ** (TRADING_DAYS / n_days) - 1


def compute_metrics() -> pd.DataFrame:
    """Calculate CAGR, Sharpe, Sortino, Alpha, Beta, drawdown per fund."""
    nav_df, code_col = load_nav()
    pivot = nav_df.pivot(index="date", columns=code_col, values="nav").ffill()
    daily = pivot.pct_change().dropna()
    rf_daily = RF_ANNUAL / TRADING_DAYS

    bench_col = pivot.columns[0]
    bench_ret = daily[bench_col]
    rows = []

    for code in pivot.columns:
        nav_s = pivot[code].dropna()
        ret = daily[code].dropna()
        aligned, aligned_bench = ret.align(bench_ret, join="inner")

        n_days = len(nav_s) - 1
        cagr_all = (nav_s.iloc[-1] / nav_s.iloc[0]) ** (TRADING_DAYS / n_days) - 1 if n_days else 0
        excess = aligned - rf_daily
        sharpe = (excess.mean() / aligned.std()) * np.sqrt(TRADING_DAYS) if aligned.std() else 0
        downside = aligned[aligned < 0].std()
        sortino = (excess.mean() / downside) * np.sqrt(TRADING_DAYS) if downside else 0
        slope, intercept, _, _, _ = stats.linregress(aligned_bench, aligned)
        mdd = (nav_s / nav_s.cummax() - 1).min()
        te = (aligned - aligned_bench).std() * np.sqrt(TRADING_DAYS)

        rows.append({
            "amfi_code": code,
            "CAGR_1Y": period_cagr(nav_s, 1),
            "CAGR_3Y": period_cagr(nav_s, 3),
            "CAGR_5Y": period_cagr(nav_s, 5),
            "CAGR_Overall": cagr_all,
            "Sharpe": sharpe,
            "Sortino": sortino,
            "Alpha": intercept * TRADING_DAYS,
            "Beta": slope,
            "Max_Drawdown": mdd,
            "Tracking_Error": te,
            "Expense_Ratio": 0.015,
        })

    return pd.DataFrame(rows), pivot


def build_scorecard(metrics: pd.DataFrame) -> pd.DataFrame:
    """Composite 0-100 score per capstone rubric weights."""
    df = metrics.copy()
    df["Rank_Return"] = df["CAGR_3Y"].rank(pct=True)
    df["Rank_Sharpe"] = df["Sharpe"].rank(pct=True)
    df["Rank_Alpha"] = df["Alpha"].rank(pct=True)
    df["Rank_ER"] = df["Expense_Ratio"].rank(pct=True, ascending=False)
    df["Rank_DD"] = df["Max_Drawdown"].rank(pct=True)
    df["Score"] = (
        30 * df["Rank_Return"]
        + 25 * df["Rank_Sharpe"]
        + 20 * df["Rank_Alpha"]
        + 15 * df["Rank_ER"]
        + 10 * df["Rank_DD"]
    )
    return df.sort_values("Score", ascending=False)


def compute_var_cvar(daily_returns: pd.DataFrame) -> pd.DataFrame:
    """Historical VaR (95%) and CVaR for each fund."""
    rows = []
    for col in daily_returns.columns:
        r = daily_returns[col].dropna() * 100
        var_95 = np.percentile(r, 5)
        cvar = r[r <= var_95].mean() if (r <= var_95).any() else var_95
        rows.append({"amfi_code": col, "VaR_95": var_95, "CVaR": cvar})
    return pd.DataFrame(rows)


FUND_NAMES = {
    125497: "HDFC Top 100",
    119551: "SBI Bluechip",
    120503: "ICICI Bluechip",
    118632: "Nippon Large Cap",
    119092: "Axis Bluechip",
    120841: "Kotak Bluechip",
}


def export_charts(metrics: pd.DataFrame, pivot: pd.DataFrame, daily: pd.DataFrame) -> None:
    """Save PNG charts for report and dashboard."""
    ensure_dirs()
    sns.set_theme(style="whitegrid")
    labels = [FUND_NAMES.get(c, str(c)) for c in metrics["amfi_code"]]

    fig, ax = plt.subplots(figsize=(11, 5))
    for col in pivot.columns:
        norm = pivot[col] / pivot[col].dropna().iloc[0] * 100
        ax.plot(norm.index, norm.values, label=FUND_NAMES.get(col, col), linewidth=1.1)
    ax.set_title("Normalized NAV Performance (Base = 100)", fontweight="bold")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "01_nav_trend.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(labels, metrics["Sharpe"].values, color="#1f4e79")
    ax.set_title("Sharpe Ratio by Fund", fontweight="bold")
    plt.xticks(rotation=25, ha="right", fontsize=8)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "02_sharpe_ranking.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = sns.color_palette("deep", len(metrics))
    ax.barh(labels, metrics["CAGR_Overall"].values * 100, color=colors)
    ax.set_xlabel("CAGR (%)")
    ax.set_title("Compound Annual Growth Rate by Fund", fontweight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "cagr_comparison.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(metrics["Beta"], metrics["Sharpe"], s=120, c=colors, edgecolors="black")
    for name, b, s in zip(labels, metrics["Beta"], metrics["Sharpe"]):
        ax.annotate(name.split()[0], (b, s), fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.axhline(0, color="gray", linestyle="--", linewidth=0.8)
    ax.axvline(1, color="gray", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Beta")
    ax.set_ylabel("Sharpe Ratio")
    ax.set_title("Risk-Return Profile: Sharpe vs Beta", fontweight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "sharpe_beta.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, metrics["Max_Drawdown"].values * 100, color="#c0392b", alpha=0.85)
    ax.set_ylabel("Max Drawdown (%)")
    ax.set_title("Maximum Drawdown by Fund", fontweight="bold")
    plt.xticks(rotation=25, ha="right", fontsize=8)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "drawdown.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    for col in pivot.columns[:3]:
        ax.plot(pivot.index, pivot[col] / pivot[col].dropna().iloc[0] * 100, label=FUND_NAMES.get(col, col))
    ax.set_title("Benchmark Comparison — Top 3 Funds (Normalized)", fontweight="bold")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "benchmark_comparison.png", dpi=200)
    plt.close(fig)

    rolling_vol = daily.rolling(60).std() * np.sqrt(TRADING_DAYS) * 100
    fig, ax = plt.subplots(figsize=(10, 4))
    for col in list(pivot.columns[:3]):
        if col in rolling_vol.columns:
            ax.plot(rolling_vol.index, rolling_vol[col], label=FUND_NAMES.get(col, col), alpha=0.85)
    ax.set_title("60-Day Rolling Annualized Volatility (%)", fontweight="bold")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "volatility.png", dpi=200)
    plt.close(fig)

    rolling_sharpe = (
        daily.rolling(90).mean() / daily.rolling(90).std() * np.sqrt(TRADING_DAYS)
    ).dropna(how="all")
    fig, ax = plt.subplots(figsize=(10, 4))
    for col in list(pivot.columns[:5]):
        if col in rolling_sharpe.columns:
            ax.plot(rolling_sharpe.index, rolling_sharpe[col], label=FUND_NAMES.get(col, col), alpha=0.85)
    ax.set_title("Rolling 90-Day Sharpe Ratio", fontweight="bold")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "rolling_sharpe_chart.png", dpi=200)
    plt.close(fig)


def run_metrics() -> None:
    """Run full metrics pipeline and write CSV outputs."""
    ensure_dirs()
    metrics, pivot = compute_metrics()
    daily = pivot.pct_change().dropna()
    scorecard = build_scorecard(metrics)
    var_df = compute_var_cvar(daily)

    scorecard.to_csv(REPORTS_DIR / "fund_scorecard.csv", index=False)
    scorecard.to_csv(PROCESSED_DIR / "fund_scorecard.csv", index=False)
    var_df.to_csv(REPORTS_DIR / "var_cvar_report.csv", index=False)
    var_df.to_csv(PROCESSED_DIR / "var_cvar_report.csv", index=False)
    metrics[["amfi_code", "Alpha", "Beta", "Sharpe", "Sortino"]].to_csv(
        REPORTS_DIR / "alpha_beta.csv", index=False
    )
    export_charts(scorecard, pivot, daily)
    print(f"Scorecard -> {REPORTS_DIR / 'fund_scorecard.csv'}")
    print(f"VaR report -> {REPORTS_DIR / 'var_cvar_report.csv'}")


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}. Run etl_pipeline.py first.")
    run_metrics()


if __name__ == "__main__":
    main()
