"""
Simple fund recommender by risk appetite and Sharpe ratio.

Day 6 deliverable: recommender.py
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"


RISK_MAP = {
    "Low": ["Low", "Low to Moderate"],
    "Moderate": ["Moderate", "Moderately High"],
    "High": ["High", "Very High"],
}


def recommend_funds(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    """
    Return top funds matching risk appetite ranked by Sharpe ratio.

    Parameters
    ----------
    risk_appetite : str
        One of Low, Moderate, High.
    top_n : int
        Number of recommendations to return.
    """
    master_path = PROCESSED_DIR / "01_fund_master_clean.csv"
    if not master_path.exists():
        master_path = RAW_DIR / "01_fund_master.csv"

    score_path = REPORTS_DIR / "fund_scorecard.csv"
    if not score_path.exists():
        score_path = PROCESSED_DIR / "fund_scorecard.csv"

    master = pd.read_csv(master_path)
    if score_path.exists():
        scores = pd.read_csv(score_path)
        code_master = "amfi_code" if "amfi_code" in master.columns else "scheme_code"
        code_score = "amfi_code" if "amfi_code" in scores.columns else "Scheme_Code"
        master = master.merge(scores, left_on=code_master, right_on=code_score, how="left")

    risk_col = next((c for c in ("risk_grade", "risk_category") if c in master.columns), None)
    sharpe_col = "Sharpe" if "Sharpe" in master.columns else "sharpe_ratio"
    name_col = "scheme_name" if "scheme_name" in master.columns else "amfi_code"

    allowed = RISK_MAP.get(risk_appetite, RISK_MAP["High"])
    filtered = master[master[risk_col].isin(allowed)] if risk_col else master
    if sharpe_col not in filtered.columns:
        filtered = filtered.head(top_n)
    else:
        filtered = filtered.sort_values(sharpe_col, ascending=False).head(top_n)

    cols = [c for c in [name_col, "category", "sub_category", sharpe_col, "Score"] if c in filtered.columns]
    return filtered[cols]


def main() -> None:
    for appetite in ("Low", "Moderate", "High"):
        print(f"\nTop funds for {appetite} risk:")
        result = recommend_funds(appetite)
        print(result.to_string(index=False))


if __name__ == "__main__":
    main()
