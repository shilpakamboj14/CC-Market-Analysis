"""
Gets bank financial numbers directly from SEC's public filings (10-K and 10-Q).
"""

import os
import time
import requests
import pandas as pd

# SEC asks for a name/email with every request
USER_AGENT = "Shilpa CC-Market-Dashboard shilpakamboj14@gmail.com"

# Each bank's ID number on SEC's website
BANKS = {
    "JPMorgan Chase": "0000019617",
    "Bank of America": "0000070858",
    "Citigroup": "0000831001",
    "Wells Fargo": "0000072971",
    "Capital One": "0000927628",
    "American Express": "0000004962",
    "Discover Financial": "0001393612",
}

# The numbers we want, and the possible names SEC filings use for each one
METRICS = {
    "total_assets": ["Assets"],
    "net_income": ["NetIncomeLoss"],
    "total_revenue": ["Revenues", "RevenuesNetOfInterestExpense", "InterestAndDividendIncomeOperating"],
    "stockholders_equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
}

DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data")


def get_bank_data(cik):
    url = "https://data.sec.gov/api/xbrl/companyfacts/CIK" + cik + ".json"
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    return response.json()


def main():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    all_rows = []

    for bank_name, cik in BANKS.items():
        bank_data = get_bank_data(cik)
        numbers = bank_data["facts"]["us-gaap"]

        for metric_name, possible_tags in METRICS.items():
            # try each possible tag name until we find one this bank actually uses
            for tag in possible_tags:
                if tag in numbers:
                    values = numbers[tag]["units"]["USD"]
                    table = pd.DataFrame(values)
                    table["issuer"] = bank_name
                    table["metric"] = metric_name
                    all_rows.append(table)
                    break  # found it, stop trying other tag names

        time.sleep(0.3)  # small pause so we don't overload SEC's server

    full_table = pd.concat(all_rows, ignore_index=True)
    full_table = full_table[["issuer", "metric", "end", "val", "form"]]
    full_table.columns = ["issuer", "metric", "period_end", "value", "form"]

    # keep only real yearly/quarterly reports, not corrected re-filings
    full_table = full_table[full_table["form"].isin(["10-K", "10-Q"])]
    full_table = full_table.drop_duplicates(subset=["issuer", "metric", "period_end"])

    full_table.to_csv(os.path.join(DATA_FOLDER, "sec_issuer_financials.csv"), index=False)

    latest = full_table.sort_values("period_end").groupby(["issuer", "metric"]).tail(1)
    latest.to_csv(os.path.join(DATA_FOLDER, "sec_latest.csv"), index=False)

    print("Done! Data saved to the data folder.")


if __name__ == "__main__":
    main()
