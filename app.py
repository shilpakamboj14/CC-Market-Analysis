"""
US Credit Card Market Dashboard - SIMPLE VERSION
This does the same job as the original file, but written in plain,
beginner-friendly steps. Every section just does ONE thing at a time:
1. Load a CSV file
2. Show it as a chart or table

No fancy helper functions, no caching, no dynamically-built caption text.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# This is just the folder where our CSV files live.
DATA_DIR = "data"

st.set_page_config(page_title="US Credit Card Market Dashboard", layout="wide")

st.title("US Credit Card Market Dashboard")
st.caption("Built using public data from FRED, SEC EDGAR, and issuer rate pages.")

# We split the page into 4 tabs. Think of tabs like folders you click between.
tab_macro, tab_issuers, tab_products, tab_about = st.tabs(
    ["Macro Overview", "Issuer Financials", "Product Comparison", "Methodology"]
)

# -----------------------------------------------------------
# TAB 1: Macro & Market Overview
# -----------------------------------------------------------
with tab_macro:
    st.subheader("Macroeconomic & Consumer Credit Indicators")
    st.caption("Source: FRED (Federal Reserve Economic Data)")

    fred_df = pd.read_csv(f"{DATA_DIR}/fred_indicators.csv", parse_dates=["date"])

    # A simple dictionary: internal column name -> nice title to display
    series_labels = {
        "real_gdp": "Real GDP ($B)",
        "unemployment_rate": "Unemployment Rate (%)",
        "revolving_consumer_credit": "Revolving Consumer Credit ($B)",
        "credit_card_delinquency_rate": "Credit Card Delinquency Rate (%)",
        "credit_card_utilization_rate": "Median Credit Card Utilization Rate (%)",
        "real_median_household_income": "Real Median Household Income ($)",
    }

    # Draw one line chart per series, one after another (simpler than
    # alternating columns - easier to follow when you're starting out).
    for series_key, label in series_labels.items():
        subset = fred_df[fred_df["series"] == series_key].sort_values("date")
        if subset.empty:
            continue
        fig = px.line(subset, x="date", y="value", title=label)
        st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Credit card utilization rate is the median share of a customer's "
        "available credit that is actually being used. Higher utilization "
        "can be a sign of financial stress."
    )

# -----------------------------------------------------------
# TAB 2: Issuer Financials
# -----------------------------------------------------------
with tab_issuers:
    st.subheader("Issuer Financial Comparison")
    st.caption("Source: SEC EDGAR filings (10-K / 10-Q)")

    sec_df = pd.read_csv(f"{DATA_DIR}/sec_issuer_financials.csv")

    metric_labels = {
        "total_assets": "Total Assets ($)",
        "net_income": "Net Income ($)",
        "total_revenue": "Total Revenue ($)",
        "stockholders_equity": "Stockholders' Equity ($)",
    }

    # A dropdown so the user can pick which metric to see.
    metric_choice = st.selectbox("Metric", list(metric_labels.keys()), format_func=lambda k: metric_labels[k])

    subset = sec_df[sec_df["metric"] == metric_choice].copy()
    subset["period_end"] = pd.to_datetime(subset["period_end"])
    subset = subset.sort_values("period_end")

    fig = px.line(subset, x="period_end", y="value", color="issuer", title=metric_labels[metric_choice])
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
# TAB 3: Product Comparison
# -----------------------------------------------------------
with tab_products:
    st.subheader("Card Product Comparison")
    st.caption("Manually compiled from each issuer's public rewards/rates page.")

    product_df = pd.read_csv(f"{DATA_DIR}/card_product_comparison.csv")

    all_categories = sorted(product_df["category"].unique().tolist())
    all_issuers = sorted(product_df["issuer"].unique().tolist())

    selected_categories = st.multiselect("Card category", options=all_categories, default=all_categories)
    selected_issuers = st.multiselect("Bank / issuer", options=all_issuers, default=all_issuers)

    filtered_df = product_df[
        product_df["category"].isin(selected_categories)
        & product_df["issuer"].isin(selected_issuers)
    ]

    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# -----------------------------------------------------------
# TAB 4: Methodology
# -----------------------------------------------------------
with tab_about:
    st.subheader("Methodology & Sources")
    st.markdown(
        """
This dashboard is built entirely on public data — no vendor or licensed sources.

**Data sources:**
- FRED — GDP, unemployment, consumer credit, delinquency rates.
- SEC EDGAR — issuer financials from 10-K/10-Q filings.
- Issuer websites — card rewards, APR, and fee data, compiled manually.

**Limitations:**
- Product comparison data is a manual snapshot, not a live feed.
- Some financial terms (like "Revenue") are labeled differently across
  companies' own filings.
        """
    )
