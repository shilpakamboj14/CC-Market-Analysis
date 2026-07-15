"""
Pulls macroeconomic and consumer-credit indicators from FRED (Federal Reserve
Economic Data) — all public, free data, no vendor licensing required.

Requires a free FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html
Set it as an environment variable before running:
    export FRED_API_KEY="your_key_here"
"""

import os
import sys
import pandas as pd
from fredapi import Fred

# ---- Series we care about for the credit card market report ----
# Each maps to a FRED series ID. Comment describes what it feeds in the app.
SERIES = {
    "real_gdp": "GDPC1",                # Real GDP, $B -> Market Overview
    "unemployment_rate": "UNRATE",       # Unemployment rate, % -> Market Overview
    "cpi": "CPIAUCSL",                   # Consumer Price Index -> Market Overview
    "real_median_household_income": "MEHOINUSA672N",  # $ -> Customer Profiles
    "revolving_consumer_credit": "REVOLSL",   # $B, mostly credit card debt -> Market Value
    "credit_card_delinquency_rate": "DRCCLACBS",  # % -> Market Risk
    "credit_card_interest_rate": "TERMCBCCALLNS",  # Avg APR, % -> Market Overview
    "personal_savings_rate": "PSAVERT",  # % -> Macro context
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def main():
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        print("ERROR: Set the FRED_API_KEY environment variable first.")
        print('  export FRED_API_KEY="your_key_here"')
        print("Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html")
        sys.exit(1)

    fred = Fred(api_key=api_key)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_frames = []
    for label, series_id in SERIES.items():
        print(f"Fetching {label} ({series_id})...")
        try:
            s = fred.get_series(series_id)
            df = s.reset_index()
            df.columns = ["date", "value"]
            df["series"] = label
            df["series_id"] = series_id
            all_frames.append(df)
        except Exception as e:
            print(f"  WARNING: failed to fetch {series_id}: {e}")

    if not all_frames:
        print("No data fetched. Exiting.")
        sys.exit(1)

    combined = pd.concat(all_frames, ignore_index=True)
    out_path = os.path.join(OUTPUT_DIR, "fred_indicators.csv")
    combined.to_csv(out_path, index=False)
    print(f"\nSaved {len(combined)} rows to {out_path}")

    # Also save a "latest value per series" summary — handy for headline stats
    latest = (
        combined.sort_values("date")
        .groupby(["series", "series_id"])
        .tail(1)
        .reset_index(drop=True)
    )
    latest_path = os.path.join(OUTPUT_DIR, "fred_latest.csv")
    latest.to_csv(latest_path, index=False)
    print(f"Saved latest snapshot to {latest_path}")


if __name__ == "__main__":
    main()
