"""Build a static HTML snapshot of the subscriber analytics dashboard for
GitHub Pages. Run manually: `python scripts/build_static_site.py`.

This is a read-only snapshot of the full sample dataset (no filters) — for
live interactive filtering, see the Streamlit app linked in the page banner.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from subscriber_analytics.analysis import (
    anova_revenue_by_plan,
    chi_square_association,
    fit_churn_proxy_model,
    summarize,
    ttest_age_by_lapsed_status,
)
from subscriber_analytics.data_pipeline import load_and_clean_data
from subscriber_analytics.viz import (
    age_distribution_histogram,
    churn_model_coefficients_chart,
    lapsed_rate_by_plan_chart,
    signups_over_time_chart,
)

# Update this once the Streamlit app is deployed to Streamlit Community Cloud.
STREAMLIT_URL_PLACEHOLDER = "https://share.streamlit.io/"

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = _REPO_ROOT / "docs" / "index.html"

_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Streaming Subscriber Analytics</title>
<style>
body { font-family: -apple-system, sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1rem; }
.banner { background: #eef6ff; border: 1px solid #b6d8ff; padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1.5rem; }
.kpis { display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 2rem; }
.kpi { background: #f7f7f7; border-radius: 8px; padding: 1rem 1.5rem; }
.kpi .value { font-size: 1.5rem; font-weight: 600; }
.test-result { border: 1px solid #ddd; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; }
</style>
</head>
<body>
<h1>Streaming Subscriber Analytics</h1>
<div class="banner">
  This is a static snapshot of the full sample dataset (no filters).
  For live filtering and exploration, see the
  <a href="{{ streamlit_url }}">interactive app</a>.
</div>

<h2>Overview</h2>
<div class="kpis">
  <div class="kpi"><div class="value">{{ stats.n_subscribers }}</div>Subscribers</div>
  <div class="kpi"><div class="value">${{ "%.2f"|format(stats.total_monthly_revenue) }}</div>Total monthly revenue</div>
  <div class="kpi"><div class="value">${{ "%.2f"|format(stats.avg_monthly_revenue) }}</div>Avg monthly revenue</div>
  <div class="kpi"><div class="value">{{ stats.avg_age }}</div>Avg age</div>
  <div class="kpi"><div class="value">{{ "%.1f"|format(stats.lapsed_rate * 100) }}%</div>Lapsed rate</div>
</div>

{{ signups_chart }}
{{ age_chart }}
{{ lapsed_rate_chart }}

<h2>Statistical Tests</h2>
<div class="test-result">
  <strong>Plan vs. Device (Chi-Square)</strong><br>
  chi2 = {{ chi2.chi2 }}, p = {{ chi2.p_value }} —
  {{ "Significant" if chi2["significant_at_0.05"] else "Not significant" }} at 0.05
</div>
<div class="test-result">
  <strong>Revenue by Plan (One-Way ANOVA)</strong><br>
  F = {{ anova.f_stat }}, p = {{ anova.p_value }} —
  {{ "Significant" if anova["significant_at_0.05"] else "Not significant" }} at 0.05
</div>
<div class="test-result">
  <strong>Age: Lapsed vs. Active (Welch's t-test)</strong><br>
  t = {{ ttest.t_stat }}, p = {{ ttest.p_value }} —
  {{ "Significant" if ttest["significant_at_0.05"] else "Not significant" }} at 0.05
</div>

<h2>Churn-Risk Model</h2>
<p><em>`is_lapsed` is a recency-based proxy, not verified churn — this demonstrates the
modeling workflow, not a production churn model.</em></p>
<div class="kpis">
  <div class="kpi"><div class="value">{{ "%.2f"|format(model.accuracy * 100) }}%</div>Accuracy</div>
  <div class="kpi"><div class="value">{{ model.roc_auc if model.roc_auc else "N/A" }}</div>ROC-AUC</div>
</div>
{{ coefficients_chart }}

</body>
</html>
"""
)


def main(output_path: str | Path | None = None) -> Path:
    output_path = Path(output_path) if output_path is not None else DEFAULT_OUTPUT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_and_clean_data()
    stats = summarize(df)
    model_result = fit_churn_proxy_model(df)

    html = _TEMPLATE.render(
        streamlit_url=STREAMLIT_URL_PLACEHOLDER,
        stats=stats,
        signups_chart=signups_over_time_chart(df).to_html(full_html=False, include_plotlyjs="cdn"),
        age_chart=age_distribution_histogram(df).to_html(full_html=False, include_plotlyjs=False),
        lapsed_rate_chart=lapsed_rate_by_plan_chart(df).to_html(full_html=False, include_plotlyjs=False),
        chi2=chi_square_association(df, "subscription_type", "device"),
        anova=anova_revenue_by_plan(df),
        ttest=ttest_age_by_lapsed_status(df),
        model=model_result,
        coefficients_chart=churn_model_coefficients_chart(model_result.coefficients).to_html(
            full_html=False, include_plotlyjs=False
        ),
    )

    output_path.write_text(html)
    return output_path


if __name__ == "__main__":
    written_to = main()
    print(f"Wrote static site to {written_to}")
