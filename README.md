# US Credit Card Market Dashboard

A public-data-only market research dashboard for the US credit card industry —
macro trends, issuer financials, and product comparisons, refreshed on demand.

**Data sources (all public, no vendor/paid data):**
- [FRED](https://fred.stlouisfed.org/) (Federal Reserve Economic Data) — GDP, unemployment, consumer credit, delinquency rates
- [SEC EDGAR](https://www.sec.gov/edgar) — issuer financials from 10-K/10-Q filings (JPM, BAC, C, WFC, COF, AXP, DFS)
- [CFPB Consumer Credit Card Market Report](https://www.consumerfinance.gov/) — consumer behavior data (manually refreshed, periodic release)
- Issuer public websites — rewards/APR/fee comparison (manually compiled, refreshed quarterly)

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt --break-system-packages
   ```

2. Get a free FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html
   Then set it as an environment variable:
   ```
   export FRED_API_KEY="your_key_here"
   ```
   (SEC EDGAR needs no key, just a descriptive User-Agent header, already set in the script.)

3. Pull the data:
   ```
   python scripts/fetch_fred_data.py
   python scripts/fetch_sec_data.py
   ```

4. Run the dashboard:
   ```
   streamlit run app.py
   ```

## Deploying for a public link

Push this repo to GitHub, then deploy free at https://share.streamlit.io
(Streamlit Community Cloud) — connect your repo, add `FRED_API_KEY` as a secret
in the app settings, and you'll get a public `*.streamlit.app` link.

## Project structure

```
cc-market-dashboard/
├── app.py                      # Streamlit dashboard
├── requirements.txt
├── scripts/
│   ├── fetch_fred_data.py      # Pulls macro + consumer credit series from FRED
│   └── fetch_sec_data.py       # Pulls issuer financials from SEC EDGAR
├── data/                       # Cached CSVs (created after running fetch scripts)
└── .streamlit/
    └── secrets.toml.example    # Template for API key storage
```
