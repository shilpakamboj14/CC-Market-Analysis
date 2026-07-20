"""
US Credit Card Market Dashboard
Built entirely on public data: FRED, SEC EDGAR, and issuer-published rate/fee pages.
"""

import os
import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

st.set_page_config(
    page_title="US Credit Card Market Dashboard",
    page_icon="\U0001F4B3",
    layout="wide",
)

# ---------- Helpers ----------

@st.cache_data(ttl=3600)
def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, parse_dates=["date"] if "date" in pd.read_csv(path, nrows=0).columns else None)


def missing_data_notice(filename, fetch_script):
    st.warning(
        f"**Data not found:** `{filename}`\n\n"
        f"Run `python scripts/{fetch_script}` first to populate this section."
    )


# ---------- Header ----------

st.title("\U0001F4B3 US Credit Card Market Dashboard")
st.caption(
    "A market research view of the US credit card industry, built entirely on "
    "public sources: Federal Reserve (FRED), SEC EDGAR filings, and issuers' "
    "own published rate/fee/rewards pages. No vendor or licensed data used."
)

# ---------- Headline KPI cards (main page, before the tabs) ----------

latest_df = load_csv("fred_latest.csv")

if latest_df is None:
    st.info(
        "Run `python scripts/fetch_fred_data.py` to populate the headline "
        "market snapshot above the tabs."
    )
else:
    # Turn the latest-value table into a simple lookup: series name -> value
    latest_lookup = dict(zip(latest_df["series"], latest_df["value"]))
    latest_dates = dict(zip(latest_df["series"], latest_df["date"]))

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        val = latest_lookup.get("unemployment_rate")
        st.metric("Unemployment Rate", f"{val:.1f}%" if val is not None else "N/A")

    with kpi_col2:
        val = latest_lookup.get("credit_card_utilization_rate")
        st.metric("Median Credit Card Utilization", f"{val:.1f}%" if val is not None else "N/A")

    with kpi_col3:
        val = latest_lookup.get("credit_card_delinquency_rate")
        st.metric("Credit Card Delinquency Rate", f"{val:.2f}%" if val is not None else "N/A")

    with kpi_col4:
        val = latest_lookup.get("revolving_consumer_credit")
        st.metric("Revolving Consumer Credit", f"${val:,.0f}B" if val is not None else "N/A")

    as_of = latest_dates.get("credit_card_utilization_rate", "")
    if as_of:
        st.caption(f"Snapshot as of most recent FRED release for each series (utilization data through {as_of}). See the Macro tab for trends over time.")

    st.divider()

tab_macro, tab_issuers, tab_products, tab_about = st.tabs(
    ["\U0001F4C8 Macro & Market Overview", "\U0001F3E6 Issuer Financials", "\U0001F4B3 Product Comparison", "\u2139\uFE0F Methodology"]
)

# ---------- Tab 1: Macro & Market Overview ----------
with tab_macro:
    st.subheader("Macroeconomic & Consumer Credit Indicators")
    st.caption("Source: FRED (Federal Reserve Economic Data)")

    fred_df = load_csv("fred_indicators.csv")

    if fred_df is None:
        missing_data_notice("fred_indicators.csv", "fetch_fred_data.py")
    else:
        series_labels = {
            "real_gdp": "Real GDP ($B)",
            "unemployment_rate": "Unemployment Rate (%)",
            "revolving_consumer_credit": "Revolving Consumer Credit ($B) — mostly credit card debt",
            "credit_card_delinquency_rate": "Credit Card Delinquency Rate (%)",
            "credit_card_utilization_rate": "Median Credit Card Utilization Rate (%)",
            "real_median_household_income": "Real Median Household Income ($)",
        }

        col1, col2 = st.columns(2)
        cols_cycle = [col1, col2]
        for i, (series_key, label) in enumerate(series_labels.items()):
            subset = fred_df[fred_df["series"] == series_key].sort_values("date")
            if subset.empty:
                continue
            with cols_cycle[i % 2]:
                fig = px.line(subset, x="date", y="value", title=label)
                fig.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "**Credit card utilization rate** is the median share of an account's "
            "available credit line that's actually being used, among active accounts "
            "at large banks. Higher utilization is generally a warning sign for "
            "consumer financial stress. Source: Federal Reserve Bank of Philadelphia."
        )

        latest_df = load_csv("fred_latest.csv")
        if latest_df is not None:
            with st.expander("Latest values (raw)"):
                st.dataframe(latest_df, use_container_width=True)

# ---------- Tab 2: Issuer Financials ----------
with tab_issuers:
    st.subheader("Issuer Financial Comparison")
    st.caption("Source: SEC EDGAR — figures as reported in each issuer's own 10-K/10-Q filings")

    sec_df = load_csv("sec_issuer_financials.csv")

    if sec_df is None:
        missing_data_notice("sec_issuer_financials.csv", "fetch_sec_data.py")
    else:
        metric_labels = {
            "total_assets": "Total Assets ($)",
            "net_income": "Net Income ($)",
            "total_revenue": "Total Revenue ($)",
            "stockholders_equity": "Stockholders' Equity ($)",
        }
        metric_choice = st.selectbox("Metric", list(metric_labels.keys()), format_func=lambda k: metric_labels[k])

        subset = sec_df[sec_df["metric"] == metric_choice].copy()
        subset["period_end"] = pd.to_datetime(subset["period_end"])
        subset = subset.sort_values("period_end")

        fig = px.line(
            subset, x="period_end", y="value", color="issuer",
            title=metric_labels[metric_choice],
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Latest reported values (raw)"):
            latest = load_csv("sec_latest.csv")
            if latest is not None:
                st.dataframe(latest, use_container_width=True)

# ---------- Tab 3: Product Comparison ----------
with tab_products:
    st.subheader("Card Product Comparison")
    st.caption(
        "Compiled manually from each issuer's own public rewards/rates page. "
        "Refresh quarterly — issuer offers change frequently."
    )

    product_df = load_csv("card_product_comparison.csv")
    if product_df is None:
        st.info(
            "This section isn't populated yet. Unlike the macro and issuer-financial "
            "tabs, there's no public API for card rewards/APR data — it needs to be "
            "manually compiled from each issuer's own website "
            "(Chase, Amex, Citi, Bank of America, Capital One, Wells Fargo, Discover) "
            "into `data/card_product_comparison.csv`. A template is provided in the repo."
        )
    elif "category" not in product_df.columns:
        # Older flat-list format (no category column) - just show as-is
        st.dataframe(product_df, use_container_width=True)
    else:
        all_categories = sorted(product_df["category"].unique().tolist())
        all_issuers = sorted(product_df["issuer"].unique().tolist())

        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            selected_categories = st.multiselect(
                "Card category",
                options=all_categories,
                default=all_categories,  # nothing excluded until the user narrows it
            )
        with filter_col2:
               st.markdown(
                   "<p style='color:#003366; font-weight:bold; margin-bottom:0;'>Bank / issuer</p>",
                   unsafe_allow_html=True,
        )

    selected_issuers = st.multiselect(
        label="",
        options=all_issuers,
        default=all_issuers,
        label_visibility="collapsed",
    )

    # If someone clears a filter entirely, treat that as "show everything"
active_categories = selected_categories if selected_categories else all_categories
active_issuers = selected_issuers if selected_issuers else all_issuers

        filtered_df = product_df[
            product_df["category"].isin(active_categories)
            & product_df["issuer"].isin(active_issuers)
        ]

        st.caption(f"Showing {len(filtered_df)} of {len(product_df)} cards")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# ---------- Tab 4: Methodology ----------
with tab_about:
    st.subheader("Methodology & Sources")
    st.markdown(
        """
This dashboard is built **entirely on public data** — no vendor, licensed, or
proprietary sources are used.

**Data sources:**
- **FRED (Federal Reserve Economic Data)** — GDP, unemployment, consumer credit
  outstanding, credit card delinquency rates, average APR. Free public API.
- **SEC EDGAR** — issuer financials (assets, net income, revenue, equity) pulled
  directly from each company's own 10-K/10-Q filings via SEC's public XBRL API.
- **CFPB Consumer Credit Card Market Report** — periodic (biennial) report on
  consumer credit card behavior and demographics. Manually reviewed on release.
- **Issuer websites** — card rewards, APR, and fee data compiled manually from
  each issuer's own published, public rate pages.

**Refresh cadence:**
- Macro & issuer financials: re-run the fetch scripts anytime for current data
  (FRED updates daily/monthly depending on series; SEC filings update quarterly).
- Consumer survey and product comparison data: reviewed and updated manually,
  since these aren't available via API and don't change as frequently.

**Limitations:**
- Card product data reflects a point-in-time manual compilation, not a live feed.
- Some issuer financial concepts (e.g. "Revenue") are tagged differently across
  companies in their own XBRL filings; this dashboard picks the closest available
  concept and notes it, rather than forcing an artificial apples-to-apples number.
        """
    )
