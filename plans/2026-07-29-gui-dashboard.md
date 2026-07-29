# Subscriber Analytics GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Streamlit dashboard for interactive exploration of the subscriber analytics pipeline, plus a static HTML snapshot published via GitHub Pages, without modifying the existing `src/subscriber_analytics` modules.

**Architecture:** A new shared `data_pipeline.py` module wraps "generate sample data if missing -> load -> clean" so both `app.py` (Streamlit) and `scripts/build_static_site.py` reuse identical data-loading logic. `app.py` renders a sidebar with filters plus four tabs (Overview, Segments, Statistical Tests, Churn-Risk Model), all reading from `src/subscriber_analytics`'s existing `analysis.py`/`viz.py` functions. `build_static_site.py` runs the same analysis unfiltered and renders a single static `docs/index.html` with embedded Plotly HTML fragments.

**Tech Stack:** Python, Streamlit, Plotly (already a dependency via `viz.py`), pandas, scikit-learn (already a dependency via `analysis.py`), Jinja2 for the static HTML template, pytest.

## Global Constraints

- Do not modify `src/subscriber_analytics/loading.py`, `cleaning.py`, `analysis.py`, or `viz.py` — use them as-is.
- Sample data source: `data/raw/netflix_userbase_sample.csv`; generate via `scripts/generate_sample_data.py`'s `generate()` if missing (this path is gitignored, so it will always be missing on a fresh clone).
- No CSV upload feature — sample data only.
- Follow the existing repo pattern for importing the non-package `scripts/` module: `sys.path.insert(0, str(<scripts dir>))` then `from generate_sample_data import generate` (see `tests/conftest.py:1-8` for the precedent).
- New dependencies: `streamlit>=1.30`, `jinja2>=3.1` — add to both `pyproject.toml` and `requirements.txt`.
- `docs/` is the GitHub Pages publish root (`main` branch, `/docs`, confirmed live at https://kchyslope.github.io/streaming-subscriber-analytics/) — only `build_static_site.py`'s generated `index.html` (and its assets, if any) belong there. Do not put planning docs, specs, or other non-published files under `docs/`.
- Spec: `specs/2026-07-29-gui-dashboard-design.md`.

---

### Task 1: Shared data-loading pipeline

**Files:**
- Create: `src/subscriber_analytics/data_pipeline.py`
- Test: `tests/test_data_pipeline.py`

**Interfaces:**
- Consumes: `subscriber_analytics.loading.load_subscribers(path) -> pd.DataFrame`, `subscriber_analytics.cleaning.clean_subscribers(df) -> pd.DataFrame`, `generate_sample_data.generate(n, seed) -> pd.DataFrame` (imported via the `sys.path` pattern above).
- Produces: `load_and_clean_data(csv_path: str | Path | None = None) -> pd.DataFrame` — used by both `app.py` (Task 3) and `scripts/build_static_site.py` (Task 7). Also exports `DEFAULT_SAMPLE_PATH: Path` (repo-root-relative `data/raw/netflix_userbase_sample.csv`).

- [ ] **Step 1: Write the failing test**

Create `tests/test_data_pipeline.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from subscriber_analytics.data_pipeline import load_and_clean_data


def test_load_and_clean_data_generates_sample_when_missing(tmp_path):
    csv_path = tmp_path / "sample.csv"
    assert not csv_path.exists()

    df = load_and_clean_data(csv_path)

    assert csv_path.exists()
    assert len(df) > 0
    assert "is_lapsed" in df.columns
    assert "tenure_days" in df.columns


def test_load_and_clean_data_reuses_existing_file(tmp_path):
    csv_path = tmp_path / "sample.csv"
    first = load_and_clean_data(csv_path)
    mtime_after_first = csv_path.stat().st_mtime

    second = load_and_clean_data(csv_path)

    assert csv_path.stat().st_mtime == mtime_after_first
    assert len(first) == len(second)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_data_pipeline.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'subscriber_analytics.data_pipeline'`

- [ ] **Step 3: Write the implementation**

Create `src/subscriber_analytics/data_pipeline.py`:

```python
"""Shared 'generate sample data if missing -> load -> clean' pipeline used
by both the Streamlit app and the static site builder."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from subscriber_analytics.cleaning import clean_subscribers
from subscriber_analytics.loading import load_subscribers

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
DEFAULT_SAMPLE_PATH = _REPO_ROOT / "data" / "raw" / "netflix_userbase_sample.csv"

sys.path.insert(0, str(_SCRIPTS_DIR))
from generate_sample_data import generate  # noqa: E402


def load_and_clean_data(csv_path: str | Path | None = None) -> pd.DataFrame:
    """Load the sample subscriber CSV, generating it first if missing.

    Returns the cleaned DataFrame produced by `clean_subscribers()`.
    """
    path = Path(csv_path) if csv_path is not None else DEFAULT_SAMPLE_PATH

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        generate().to_csv(path, index=False)

    raw_df = load_subscribers(path)
    return clean_subscribers(raw_df)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_data_pipeline.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/subscriber_analytics/data_pipeline.py tests/test_data_pipeline.py
git commit -m "feat: add shared load-and-clean data pipeline for GUI entry points"
```

---

### Task 2: Add Streamlit and Jinja2 dependencies

**Files:**
- Modify: `pyproject.toml`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: nothing.
- Produces: `streamlit` and `jinja2` importable in the project's virtualenv, required by Task 3 and Task 7.

- [ ] **Step 1: Modify `pyproject.toml`**

In the `dependencies` list, add two lines after `"kaleido>=0.2.1",`:

```toml
    "kaleido>=0.2.1",
    "streamlit>=1.30",
    "jinja2>=3.1",
]
```

- [ ] **Step 2: Modify `requirements.txt`**

Add two lines:

```
streamlit>=1.30
jinja2>=3.1
```

- [ ] **Step 3: Install and verify**

Run: `pip install -e .` (from repo root, with the project venv active)
Expected: `streamlit` and `jinja2` install successfully; `python -c "import streamlit, jinja2"` exits with no error.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml requirements.txt
git commit -m "chore: add streamlit and jinja2 dependencies for the GUI"
```

---

### Task 3: Streamlit app shell, sidebar filters, and Overview tab

**Files:**
- Create: `app.py` (repo root)

**Interfaces:**
- Consumes: `subscriber_analytics.data_pipeline.load_and_clean_data() -> pd.DataFrame` (Task 1), `subscriber_analytics.analysis.summarize(df) -> dict`, `subscriber_analytics.viz.signups_over_time_chart(df)`, `subscriber_analytics.viz.age_distribution_histogram(df)`.
- Produces: a module-level `filter_dataframe(df, plans, countries, devices) -> pd.DataFrame` function (pure, no Streamlit calls) that Task 4-6 tabs will read the already-filtered result from (the filtering itself happens once, before the tabs are rendered — later tasks append `st.tabs` code to this same file and use the `filtered_df` variable already in scope, they do not call `filter_dataframe` again).

- [ ] **Step 1: Write the app shell with data loading, sidebar, and Overview tab**

Create `app.py`:

```python
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
```

- [ ] **Step 2: Manual verification**

Run: `streamlit run app.py`
Expected: browser opens; sidebar shows plan/country/device multiselects and a subscriber count caption; the "Overview" tab shows 5 metric tiles and two charts. Deselecting all plans shows the "No subscribers match..." message instead of an error.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add Streamlit app shell with sidebar filters and Overview tab"
```

---

### Task 4: Segments tab

**Files:**
- Modify: `app.py` (append to the `with tab_segments:` block)

**Interfaces:**
- Consumes: `filtered_df` (from Task 3, already in scope), `subscriber_analytics.analysis.revenue_by(df, by) -> pd.DataFrame`, `segment_counts(df, by) -> pd.DataFrame`, `subscriber_analytics.viz.revenue_by_plan_chart(revenue_df, by)`, `segment_share_pie(segment_df, by)`, `lapsed_rate_by_plan_chart(df)`.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Add the Segments tab body**

In `app.py`, add these imports to the existing `from subscriber_analytics.analysis import ...` and `from subscriber_analytics.viz import ...` lines:

```python
from subscriber_analytics.analysis import revenue_by, segment_counts, summarize
from subscriber_analytics.viz import (
    age_distribution_histogram,
    lapsed_rate_by_plan_chart,
    revenue_by_plan_chart,
    segment_share_pie,
    signups_over_time_chart,
)
```

Then add, after the `with tab_overview:` block:

```python
with tab_segments:
    if filtered_df.empty:
        st.info("No subscribers match the current filter selection.")
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
```

- [ ] **Step 2: Manual verification**

Run: `streamlit run app.py`
Expected: "Segments" tab shows a group-by dropdown; switching between subscription_type/country/device/gender updates the bar chart, table, and pie chart; the lapsed-rate-by-plan chart always renders (it's fixed to subscription_type).

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add Segments tab to Streamlit app"
```

---

### Task 5: Statistical Tests tab

**Files:**
- Modify: `app.py` (append to the `with tab_tests:` block)

**Interfaces:**
- Consumes: `filtered_df`, `subscriber_analytics.analysis.chi_square_association(df, col_a, col_b) -> dict`, `anova_revenue_by_plan(df) -> dict`, `ttest_age_by_lapsed_status(df) -> dict`.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Add the Statistical Tests tab body**

Add to the `from subscriber_analytics.analysis import ...` line:

```python
from subscriber_analytics.analysis import (
    anova_revenue_by_plan,
    chi_square_association,
    revenue_by,
    segment_counts,
    summarize,
    ttest_age_by_lapsed_status,
)
```

Then add, after the `with tab_segments:` block:

```python
def _render_test_result(title: str, result: dict, stat_key: str, stat_label: str) -> None:
    st.subheader(title)
    col1, col2, col3 = st.columns(3)
    col1.metric(stat_label, result[stat_key])
    col2.metric("p-value", result["p_value"])
    verdict = "Significant (p < 0.05)" if result["significant_at_0.05"] else "Not significant"
    col3.metric("Result", verdict)


with tab_tests:
    if len(filtered_df["subscription_type"].unique()) < 2:
        st.info("Select at least two subscription plans to run the ANOVA and chi-square tests.")
    elif filtered_df["is_lapsed"].nunique() < 2:
        st.info("Current filter selection has only one lapsed/active group; the t-test needs both.")
    else:
        chi2_result = chi_square_association(filtered_df, "subscription_type", "device")
        _render_test_result(
            "Plan vs. Device (Chi-Square Test of Independence)", chi2_result, "chi2", "Chi-square"
        )

        anova_result = anova_revenue_by_plan(filtered_df)
        _render_test_result(
            "Revenue by Plan (One-Way ANOVA)", anova_result, "f_stat", "F-statistic"
        )

        ttest_result = ttest_age_by_lapsed_status(filtered_df)
        _render_test_result(
            "Age: Lapsed vs. Active (Welch's t-test)", ttest_result, "t_stat", "t-statistic"
        )
```

- [ ] **Step 2: Manual verification**

Run: `streamlit run app.py`
Expected: "Statistical Tests" tab shows three subsections each with stat/p-value/verdict. Filtering down to a single subscription plan replaces the content with the "Select at least two..." info message instead of crashing.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add Statistical Tests tab to Streamlit app"
```

---

### Task 6: Churn-Risk Model tab

**Files:**
- Modify: `app.py` (append to the `with tab_model:` block)

**Interfaces:**
- Consumes: `filtered_df`, `subscriber_analytics.analysis.fit_churn_proxy_model(df) -> ChurnModelResult`, `subscriber_analytics.viz.churn_model_coefficients_chart(coefficients_df, top_n=15)`.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Add the Churn-Risk Model tab body**

Add to the `from subscriber_analytics.analysis import ...` line:

```python
from subscriber_analytics.analysis import (
    anova_revenue_by_plan,
    chi_square_association,
    fit_churn_proxy_model,
    revenue_by,
    segment_counts,
    summarize,
    ttest_age_by_lapsed_status,
)
```

Add to the `from subscriber_analytics.viz import ...` line:

```python
from subscriber_analytics.viz import (
    age_distribution_histogram,
    churn_model_coefficients_chart,
    lapsed_rate_by_plan_chart,
    revenue_by_plan_chart,
    segment_share_pie,
    signups_over_time_chart,
)
```

Then add, after the `with tab_tests:` block:

```python
with tab_model:
    if filtered_df["is_lapsed"].nunique() < 2 or len(filtered_df) < 20:
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
        col2.metric("ROC-AUC", f"{model_result.roc_auc:.3f}" if model_result.roc_auc else "N/A")
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
```

- [ ] **Step 2: Manual verification**

Run: `streamlit run app.py`
Expected: "Churn-Risk Model" tab shows the proxy-disclaimer caption, 4 metrics, a confusion matrix table, and the coefficients chart. Filtering to a tiny/one-class subset shows the info message instead of an exception.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add Churn-Risk Model tab to Streamlit app"
```

---

### Task 7: Static site builder for GitHub Pages

**Files:**
- Create: `scripts/build_static_site.py`
- Test: `tests/test_build_static_site.py`

**Interfaces:**
- Consumes: `subscriber_analytics.data_pipeline.load_and_clean_data() -> pd.DataFrame` (Task 1), all of `analysis.py`'s functions, all of `viz.py`'s functions.
- Produces: `main(output_path: str | Path | None = None) -> Path` — writes the static HTML file and returns its path. Default `output_path` is `docs/index.html` (repo-root-relative).

- [ ] **Step 1: Write the failing test**

Create `tests/test_build_static_site.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_static_site import main  # noqa: E402


def test_main_writes_nonempty_html(tmp_path):
    output_path = tmp_path / "index.html"

    result_path = main(output_path)

    assert result_path == output_path
    assert output_path.exists()
    html = output_path.read_text()
    assert len(html) > 0
    assert "Subscribers" in html
    assert "plotly" in html.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_build_static_site.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build_static_site'`

- [ ] **Step 3: Write the implementation**

Create `scripts/build_static_site.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_build_static_site.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Run the script for real and spot-check the output**

Run: `python scripts/build_static_site.py`
Expected: prints `Wrote static site to .../docs/index.html`; opening `docs/index.html` in a browser shows the banner, KPIs, three charts, three test results, and the churn model section, all rendered correctly.

- [ ] **Step 6: Commit**

```bash
git add scripts/build_static_site.py tests/test_build_static_site.py docs/index.html
git commit -m "feat: add static site builder for GitHub Pages snapshot"
```

---

### Task 8: Full test suite verification and README update

**Files:**
- Modify: `README.md` (if it exists; create it if not, with at least the sections below)

**Interfaces:**
- Consumes: nothing new.
- Produces: nothing consumed by later tasks (final task).

- [ ] **Step 1: Read the existing README.md**

`README.md` already exists with these sections in order: title/intro,
"Project structure", "Setup", "Getting data", "Running the analysis", "The
'lapsed' label, and why it's a proxy", "Tests", "Building a GUI on top".
Read it with the Read tool before editing.

- [ ] **Step 2: Insert a "Running the dashboard" section**

Insert this new section immediately after the existing "Running the
analysis" section and before "The 'lapsed' label, and why it's a proxy"
section (i.e., the dashboard is another way to run the analysis, presented
right after the notebook walkthrough):

```markdown
## Running the dashboard

**Interactive (Streamlit):**

```bash
pip install -e .
streamlit run app.py
```

Opens a local dashboard with sidebar filters (plan/country/device) and four
tabs: Overview, Segments, Statistical Tests, and Churn-Risk Model. Sample
data is generated automatically on first run if `data/raw/` is empty.

**Static snapshot (GitHub Pages):**

A read-only snapshot of the full dataset is published at
https://kchyslope.github.io/streaming-subscriber-analytics/. To regenerate
it after code changes:

```bash
python scripts/build_static_site.py
git add docs/index.html
git commit -m "docs: refresh static dashboard snapshot"
```
```

- [ ] **Step 3: Update the "Building a GUI on top" section**

That section currently describes, in the future tense, how a GUI *could*
be built on top of the analysis modules. Replace its final paragraph:

```
3. Pass the result into the matching `viz.*` function and embed the returned Plotly
   `Figure` (e.g. via `QWebEngineView` for PyQt/PySide, or natively if building with
   Streamlit/Dash).
```

with:

```
3. Pass the result into the matching `viz.*` function and embed the returned Plotly
   `Figure` (e.g. via `QWebEngineView` for PyQt/PySide, or natively if building with
   Streamlit/Dash).

This is exactly what `app.py` does — see "Running the dashboard" above for the
working example.
```

- [ ] **Step 4: Run the full test suite**

Run: `pytest -v`
Expected: all tests pass, including the pre-existing `test_analysis.py`, `test_cleaning.py`, `test_loading.py`, `test_viz.py`, plus the new `test_data_pipeline.py` and `test_build_static_site.py`.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: document how to run the Streamlit app and rebuild the static site"
```

---

## Post-plan manual steps (not automated)

1. Push all commits: `git push`.
2. Deploy `app.py` to Streamlit Community Cloud (https://streamlit.io/cloud) using your GitHub account, pointing at this repo/branch/`app.py`. Copy the resulting `*.streamlit.app` URL.
3. Update `STREAMLIT_URL_PLACEHOLDER` in `scripts/build_static_site.py` with that URL.
4. Re-run `python scripts/build_static_site.py`, commit `docs/index.html`, and push.
