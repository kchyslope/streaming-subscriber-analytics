"""Streamlit dashboard for the streaming subscriber analytics project."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from subscriber_analytics.analysis import summarize
from subscriber_analytics.data_pipeline import load_and_clean_data
from subscriber_analytics.viz import age_distribution_histogram, signups_over_time_chart

st.set_page_config(page_title="Streaming Subscriber Analytics", layout="wide")


@st.cache_data
def get_data() -> pd.DataFrame:
    return load_and_clean_data()


def filter_dataframe(
    df: pd.DataFrame, plans: list[str], countries: list[str], devices: list[str]
) -> pd.DataFrame:
    return df[
        df["subscription_type"].isin(plans)
        & df["country"].isin(countries)
        & df["device"].isin(devices)
    ]


df = get_data()

st.sidebar.title("Streaming Subscriber Analytics")
st.sidebar.write(
    "Explore subscriber demographics, revenue, statistical tests, and a "
    "churn-risk proxy model built on a Netflix-userbase-shaped dataset."
)

all_plans = sorted(df["subscription_type"].unique())
all_countries = sorted(df["country"].unique())
all_devices = sorted(df["device"].unique())

selected_plans = st.sidebar.multiselect("Subscription plan", all_plans, default=all_plans)
selected_countries = st.sidebar.multiselect("Country", all_countries, default=all_countries)
selected_devices = st.sidebar.multiselect("Device", all_devices, default=all_devices)

filtered_df = filter_dataframe(df, selected_plans, selected_countries, selected_devices)
st.sidebar.caption(f"{len(filtered_df)} of {len(df)} subscribers selected")

tab_overview, tab_segments, tab_tests, tab_model = st.tabs(
    ["Overview", "Segments", "Statistical Tests", "Churn-Risk Model"]
)

with tab_overview:
    if filtered_df.empty:
        st.info("No subscribers match the current filter selection.")
    else:
        stats = summarize(filtered_df)
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Subscribers", f"{stats['n_subscribers']:,}")
        col2.metric("Total monthly revenue", f"${stats['total_monthly_revenue']:,.2f}")
        col3.metric("Avg monthly revenue", f"${stats['avg_monthly_revenue']:.2f}")
        col4.metric("Avg age", f"{stats['avg_age']:.1f}")
        col5.metric("Lapsed rate", f"{stats['lapsed_rate']:.1%}")

        st.plotly_chart(signups_over_time_chart(filtered_df), use_container_width=True)
        st.plotly_chart(age_distribution_histogram(filtered_df), use_container_width=True)
