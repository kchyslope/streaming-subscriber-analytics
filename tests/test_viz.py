import plotly.graph_objects as go

from subscriber_analytics.analysis import fit_churn_proxy_model, revenue_by, segment_counts
from subscriber_analytics.viz import (
    age_distribution_histogram,
    churn_model_coefficients_chart,
    lapsed_rate_by_plan_chart,
    revenue_by_plan_chart,
    segment_share_pie,
    signups_over_time_chart,
)


def test_revenue_by_plan_chart_returns_figure(clean_df):
    revenue_df = revenue_by(clean_df, "subscription_type")
    fig = revenue_by_plan_chart(revenue_df, "subscription_type")
    assert isinstance(fig, go.Figure)


def test_segment_share_pie_returns_figure(clean_df):
    segments = segment_counts(clean_df, "device")
    fig = segment_share_pie(segments, "device")
    assert isinstance(fig, go.Figure)


def test_age_distribution_histogram_returns_figure(clean_df):
    assert isinstance(age_distribution_histogram(clean_df), go.Figure)


def test_lapsed_rate_by_plan_chart_returns_figure(clean_df):
    assert isinstance(lapsed_rate_by_plan_chart(clean_df), go.Figure)


def test_signups_over_time_chart_returns_figure(clean_df):
    assert isinstance(signups_over_time_chart(clean_df), go.Figure)


def test_churn_model_coefficients_chart_returns_figure(clean_df):
    result = fit_churn_proxy_model(clean_df)
    assert isinstance(churn_model_coefficients_chart(result.coefficients), go.Figure)
