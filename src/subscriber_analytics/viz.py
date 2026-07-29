"""Plotly figure builders. Each function returns a go.Figure ready to
`.show()` in a notebook or embed in a GUI (e.g. via a QWebEngineView or a
Dash/Streamlit component)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

TEMPLATE = "plotly_white"


def revenue_by_plan_chart(revenue_df: pd.DataFrame, by: str) -> go.Figure:
    fig = px.bar(
        revenue_df,
        x=by,
        y="total_revenue",
        text="subscribers",
        title=f"Total Monthly Revenue by {by.replace('_', ' ').title()}",
        template=TEMPLATE,
    )
    fig.update_traces(texttemplate="%{text} subs", textposition="outside")
    return fig


def segment_share_pie(segment_df: pd.DataFrame, by: str) -> go.Figure:
    fig = px.pie(
        segment_df,
        names=by,
        values="subscribers",
        title=f"Subscriber Share by {by.replace('_', ' ').title()}",
        template=TEMPLATE,
        hole=0.35,
    )
    return fig


def age_distribution_histogram(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        df,
        x="age",
        color="is_lapsed",
        barmode="overlay",
        nbins=30,
        title="Age Distribution: Active vs. Lapsed Subscribers",
        template=TEMPLATE,
        labels={"is_lapsed": "Lapsed"},
    )
    fig.update_traces(opacity=0.7)
    return fig


def lapsed_rate_by_plan_chart(df: pd.DataFrame) -> go.Figure:
    rate = df.groupby("subscription_type")["is_lapsed"].mean().reset_index()
    rate["is_lapsed"] = (rate["is_lapsed"] * 100).round(1)
    fig = px.bar(
        rate,
        x="subscription_type",
        y="is_lapsed",
        title="Lapsed Rate (%) by Subscription Plan",
        labels={"is_lapsed": "Lapsed rate (%)"},
        template=TEMPLATE,
    )
    return fig


def signups_over_time_chart(df: pd.DataFrame) -> go.Figure:
    by_month = (
        df.set_index("join_date")
        .resample("MS")
        .size()
        .rename("signups")
        .reset_index()
    )
    fig = px.line(
        by_month,
        x="join_date",
        y="signups",
        markers=True,
        title="Signups by Join Month",
        template=TEMPLATE,
    )
    return fig


def churn_model_coefficients_chart(coefficients_df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    top = coefficients_df.head(top_n).sort_values("coefficient")
    colors = ["crimson" if c > 0 else "steelblue" for c in top["coefficient"]]
    fig = go.Figure(
        go.Bar(
            x=top["coefficient"],
            y=top["feature"],
            orientation="h",
            marker_color=colors,
        )
    )
    fig.update_layout(
        title="Churn-Proxy Model: Top Feature Coefficients (positive = higher lapse risk)",
        template=TEMPLATE,
        xaxis_title="Coefficient",
    )
    return fig
