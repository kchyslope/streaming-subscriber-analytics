"""Streamlit dashboard for the streaming subscriber analytics project."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from subscriber_analytics.analysis import (
    anova_revenue_by_plan,
    chi_square_association,
    fit_churn_proxy_model,
    revenue_by,
    segment_counts,
    summarize,
    ttest_age_by_lapsed_status,
)
from subscriber_analytics.data_pipeline import load_and_clean_data
from subscriber_analytics.viz import (
    age_distribution_histogram,
    churn_model_coefficients_chart,
    lapsed_rate_by_plan_chart,
    revenue_by_plan_chart,
    segment_share_pie,
    signups_over_time_chart,
)

st.set_page_config(page_title="Streaming Subscriber Analytics", layout="wide")

NO_SUBSCRIBERS_MESSAGE = "No subscribers match the current filter selection."


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


def _render_test_result(title: str, result: dict, stat_key: str, stat_label: str) -> None:
    st.subheader(title)
    col1, col2, col3 = st.columns(3)
    col1.metric(stat_label, result[stat_key])
    col2.metric("p-value", result["p_value"])
    verdict = "Significant (p < 0.05)" if result["significant_at_0.05"] else "Not significant"
    col3.metric("Result", verdict)


tab_overview, tab_segments, tab_tests, tab_model = st.tabs(
    ["Overview", "Segments", "Statistical Tests", "Churn-Risk Model"]
)

with tab_overview:
    if filtered_df.empty:
        st.info(NO_SUBSCRIBERS_MESSAGE)
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

with tab_segments:
    if filtered_df.empty:
        st.info(NO_SUBSCRIBERS_MESSAGE)
    else:
        group_by = st.selectbox(
            "Group by", ["subscription_type", "country", "device", "gender"]
        )

        revenue_df = revenue_by(filtered_df, group_by)
        st.plotly_chart(revenue_by_plan_chart(revenue_df, group_by), use_container_width=True)
        st.dataframe(revenue_df, use_container_width=True)

        segment_df = segment_counts(filtered_df, group_by)
        st.plotly_chart(segment_share_pie(segment_df, group_by), use_container_width=True)

        st.plotly_chart(lapsed_rate_by_plan_chart(filtered_df), use_container_width=True)


with tab_tests:
    if filtered_df.empty:
        st.info(NO_SUBSCRIBERS_MESSAGE)
    else:
        if filtered_df["subscription_type"].nunique() < 2 or filtered_df["device"].nunique() < 2:
            st.info("Select at least two subscription plans and two devices to run the chi-square test.")
        else:
            chi2_result = chi_square_association(filtered_df, "subscription_type", "device")
            _render_test_result(
                "Plan vs. Device (Chi-Square Test of Independence)", chi2_result, "chi2", "Chi-square"
            )

        if filtered_df["subscription_type"].nunique() < 2:
            st.info("Select at least two subscription plans to run the ANOVA.")
        else:
            anova_result = anova_revenue_by_plan(filtered_df)
            _render_test_result(
                "Revenue by Plan (One-Way ANOVA)", anova_result, "f_stat", "F-statistic"
            )

        if filtered_df["is_lapsed"].nunique() < 2:
            st.info("Current filter selection has only one lapsed/active group; the t-test needs both.")
        else:
            ttest_result = ttest_age_by_lapsed_status(filtered_df)
            _render_test_result(
                "Age: Lapsed vs. Active (Welch's t-test)", ttest_result, "t_stat", "t-statistic"
            )

with tab_model:
    if (
        filtered_df["is_lapsed"].nunique() < 2
        or filtered_df["is_lapsed"].value_counts().min() < 2
        or len(filtered_df) < 20
    ):
        st.info(
            "Not enough data in the current filter selection to train the churn-risk model "
            "(need both lapsed and active subscribers, and a reasonable sample size)."
        )
    else:
        st.caption(
            "`is_lapsed` is a recency-based proxy (no recent payment), not verified churn — "
            "this demonstrates the modeling workflow, not a production churn model."
        )
        model_result = fit_churn_proxy_model(filtered_df)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Accuracy", f"{model_result.accuracy:.2%}")
        col2.metric(
            "ROC-AUC",
            f"{model_result.roc_auc:.3f}" if model_result.roc_auc is not None else "N/A",
        )
        col3.metric("Train rows", model_result.n_train)
        col4.metric("Test rows", model_result.n_test)

        st.write("Confusion matrix (rows = actual, columns = predicted):")
        st.dataframe(
            pd.DataFrame(
                model_result.confusion_matrix,
                index=["Actual: Active", "Actual: Lapsed"],
                columns=["Predicted: Active", "Predicted: Lapsed"],
            )
        )

        st.plotly_chart(
            churn_model_coefficients_chart(model_result.coefficients), use_container_width=True
        )
