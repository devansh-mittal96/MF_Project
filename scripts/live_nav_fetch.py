"""
Fetch live NAV history from mfapi.in for key large-cap schemes.

Day 1 deliverable: live_nav_fetch.py
"""

import json
import sys
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
MFAPI_SCHEMES = {
    125497: "hdfc_top_100_live.csv",
    119551: "SBI_Bluechip_live.csv",
    120503: "ICICI_Bluechip_live.csv",
    118632: "Nippon_Large_Cap_live.csv",
    119092: "Axis_Bluechip_live.csv",
    120841: "Kotak_Bluechip_live.csv",
}


def fetch_scheme_nav(scheme_code: int, timeout: int = 30) -> pd.DataFrame | None:
    """Download NAV history for one AMFI scheme code."""
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    response = requests.get(url, timeout=timeout)
    if response.status_code != 200:
        return None
    payload = response.json()
    if "data" not in payload:
        return None
    return pd.DataFrame(payload["data"])


def fetch_all_live_nav() -> dict[int, Path]:
    """Fetch and save NAV CSVs for all configured schemes."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    saved: dict[int, Path] = {}

    for scheme_code, filename in MFAPI_SCHEMES.items():
        df = fetch_scheme_nav(scheme_code)
        if df is None or df.empty:
            continue
        out_path = RAW_DIR / filename
        df.to_csv(out_path, index=False)
        saved[scheme_code] = out_path

    return saved


def main() -> None:
    saved = fetch_all_live_nav()
    if not saved:
        raise SystemExit("No NAV data fetched. Check network or mfapi.in availability.")
    for code, path in saved.items():
        print(f"Saved scheme {code} -> {path.name} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
