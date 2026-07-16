"""
Pulls issuer financial data directly from SEC EDGAR's XBRL company-facts API —
i.e. straight from the numbers each bank reports in its own 10-K/10-Q filings.
No API key needed, but SEC requires a descriptive User-Agent on every request.

Docs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
"""

import os
import time
import json
import requests
import pandas as pd

# Update this to your own name/email -- SEC blocks generic/missing User-Agents.
USER_AGENT = "Shilpa CC-Market-Dashboard shilpa.contact@example.com"

# CIK numbers (SEC's internal company identifiers) for the major card issuers.
# Zero-padding to 10 digits is required by the API.
ISSUERS = {
    "JPMorgan Chase": "0000019617",
    "Bank of America": "0000070858",
    "Citigroup": "0000831001",
    "Wells Fargo": "0000072971",
    "Capital One": "0000927628",
    "American Express": "0000004962",
    "Discover Financial": "0001393612",
}

# US-GAAP concepts we want. Different companies sometimes use slightly
# different tags for similar line items, so we try a few candidates per metric
# and keep whichever one the filer actually reported.
CONCEPT_CANDIDATES = {
    "total_assets": ["Assets"],
    "net_income": ["NetIncomeLoss"],
    "total_revenue": [
        "Revenues",
        "RevenuesNetOfInterestExpense",
        "InterestAndDividendIncomeOperating",
    ],
    "stockholders_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
HEADERS = {"User-Agent": USER_AGENT}


def fetch_company_facts(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def extract_concept(facts_json, concept_candidates):
    """Return a DataFrame of quarterly/annual values for the first matching concept tag."""
    us_gaap = facts_json.get("facts", {}).get("us-gaap", {})
    for concept in concept_candidates:
        if concept in us_gaap:
            units = us_gaap[concept].get("units", {})
            # Most monetary concepts are reported in USD
            values = units.get("USD", [])
            if values:
                df = pd.DataFrame(values)
                df["concept"] = concept
                return df
    return pd.DataFrame()


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_rows = []

    for issuer_name, cik in ISSUERS.items():
        print(f"Fetching SEC data for {issuer_name} (CIK {cik})...")
        try:
            facts = fetch_company_facts(cik)
        except Exception as e:
            print(f"  WARNING: failed to fetch {issuer_name}: {e}")
            continue

        for metric_label, candidates in CONCEPT_CANDIDATES.items():
            df = extract_concept(facts, candidates)
            if df.empty:
                print(f"  No data found for {metric_label}")
                continue
            df["issuer"] = issuer_name
            df["metric"] = metric_label
            all_rows.append(df)

        # SEC asks for max ~10 requests/second; be a polite, well-spaced client
        time.sleep(0.3)

    if not all_rows:
        print("No data fetched. Exiting.")
        return

    combined = pd.concat(all_rows, ignore_index=True)

    # Keep the useful columns: end date, value, form type (10-K/10-Q), fiscal period
    keep_cols = ["issuer", "metric", "end", "val", "form", "fy", "fp", "frame"]
    keep_cols = [c for c in keep_cols if c in combined.columns]
    combined = combined[keep_cols].rename(columns={"end": "period_end", "val": "value"})

    # Keep only actual 10-K / 10-Q filings, drop duplicate/amended noise
    combined = combined[combined["form"].isin(["10-K", "10-Q"])]
    combined = combined.drop_duplicates(subset=["issuer", "metric", "period_end", "form"])

    out_path = os.path.join(OUTPUT_DIR, "sec_issuer_financials.csv")
    combined.to_csv(out_path, index=False)
    print(f"\nSaved {len(combined)} rows to {out_path}")

    # Latest reported value per issuer/metric -- handy for a quick comparison table
    latest = (
        combined.sort_values("period_end")
        .groupby(["issuer", "metric"])
        .tail(1)
        .reset_index(drop=True)
    )
    latest_path = os.path.join(OUTPUT_DIR, "sec_latest.csv")
    latest.to_csv(latest_path, index=False)
    print(f"Saved latest snapshot to {latest_path}")


if __name__ == "__main__":
    main()
