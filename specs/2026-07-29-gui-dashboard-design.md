# Subscriber Analytics GUI: Design Spec

Date: 2026-07-29

## Goal

Give the project a GUI that showcases the existing EDA / hypothesis-testing /
churn-proxy-modeling work in `src/subscriber_analytics`, via:

1. An interactive Streamlit app (`app.py`) for live exploration.
2. A static HTML snapshot (`docs/index.html`) published via GitHub Pages
   (already configured: `main` branch, `/docs` folder,
   https://kchyslope.github.io/streaming-subscriber-analytics/) as a
   read-only preview that links out to the live Streamlit app.

Neither the Streamlit app nor the static build script modifies
`src/subscriber_analytics/*` — those modules were already written with GUI
embedding in mind (see `viz.py` docstring) and are used as-is.

Note: this spec lives under `specs/` at the repo root, not `docs/`, because
`docs/` is the GitHub Pages publish root — anything placed there is served
publicly by the static site.

## Data source

Both entry points load `data/raw/netflix_userbase_sample.csv`. If it doesn't
exist, generate it first via `scripts/generate_sample_data.py`. No file
upload — sample data only, for a zero-friction demo.

Pipeline: `load_subscribers()` -> `clean_subscribers()` -> the resulting
DataFrame feeds all analysis/viz calls.

## Streamlit app (`app.py`)

### Caching

`@st.cache_data` around a `load_and_clean_data()` function that runs the
generate-if-missing -> load -> clean pipeline once per session.

### Sidebar

- Title and one-line description of the project.
- Multiselect filters: subscription plan, country, device. Each defaults to
  "all selected". Filtering re-slices the cleaned DataFrame; all tabs read
  from the filtered frame.
- Caption showing live count: "N of TOTAL subscribers selected".

### Tabs

**Overview**
- KPI row (`st.metric` x5) from `summarize()`: subscriber count, total
  monthly revenue, avg monthly revenue, avg age, lapsed rate.
- `signups_over_time_chart()`
- `age_distribution_histogram()`

**Segments**
- `st.selectbox` to choose grouping column: subscription_type, country,
  device, gender.
- `revenue_by(df, by)` table + `revenue_by_plan_chart(revenue_df, by)`
- `segment_counts(df, by)` table + `segment_share_pie(segment_df, by)`
- `lapsed_rate_by_plan_chart(df)` (fixed to subscription_type, as written)

**Statistical Tests**
- Three result cards (`st.metric`/`st.write` combo), one per test:
  - `chi_square_association(df, "subscription_type", "device")`
  - `anova_revenue_by_plan(df)`
  - `ttest_age_by_lapsed_status(df)`
- Each card shows the stat, p-value, and a plain-English
  significant/not-significant readout at alpha=0.05.

**Churn-Risk Model**
- Runs `fit_churn_proxy_model(df)` on the filtered data.
- Shows accuracy, ROC-AUC (if defined), a confusion matrix (`st.dataframe`
  or a small heatmap), and `churn_model_coefficients_chart()`.
- Caption clarifying `is_lapsed` is a recency-based proxy, not verified
  churn (matches the existing docstring in `analysis.py`).

### Error handling

If a filter selection leaves too few rows or too few groups for a given
test/model to run (e.g., a single subscription plan selected -> ANOVA needs
2+ groups; a filtered set with only one `is_lapsed` class -> t-test/model
undefined), catch the resulting exception (or pre-check group counts) and
show `st.info("Not enough data in the current filter selection to run this
test.")` in that tab instead of crashing the whole app.

## Static site (`scripts/build_static_site.py`)

- Runs the same load -> clean pipeline (unfiltered, full sample dataset).
- Computes `summarize()`, all `viz.py` charts, all three statistical tests,
  and `fit_churn_proxy_model()`.
- Renders `docs/index.html` via an f-string/Jinja2 template containing:
  - KPI summary block
  - All 5 charts, each exported with
    `fig.to_html(full_html=False, include_plotlyjs="cdn")`
  - The 3 hypothesis-test results (same plain-English format as the
    Streamlit tab)
  - Churn model accuracy/ROC-AUC/coefficient chart
  - A banner near the top: "This is a static snapshot. For live filtering,
    see the [interactive app](STREAMLIT_URL_PLACEHOLDER)."
- No filters — this is a fixed snapshot of the full dataset.
- `STREAMLIT_URL_PLACEHOLDER` is a constant at the top of the script,
  updated by hand once the Streamlit app is deployed.
- Entry point: `python scripts/build_static_site.py`, run manually (not
  wired to a GitHub Action in this iteration).

## Dependencies

Add to `pyproject.toml` and `requirements.txt`:
- `streamlit>=1.30`
- `jinja2>=3.1` (used directly by the static-site build script)

## Testing

Extend the existing pytest suite with a lightweight smoke test module
(`tests/test_app_smoke.py` or similar):
- Import `app.py`'s `load_and_clean_data()` (refactored out so it's
  importable without running the full Streamlit script) and assert it
  returns a non-empty, cleaned DataFrame.
- Run `build_static_site.main()` against a temp output path and assert the
  resulting HTML file exists, is non-empty, and contains a few expected
  markers (e.g. the KPI section, chart divs).

Full Streamlit UI interaction (widget state, tab switching) is not
unit-tested — out of scope for this iteration.

## Deployment notes (manual, post-implementation)

1. Push `app.py` and updated deps to GitHub (already public repo).
2. Sign in to https://streamlit.io/cloud with the GitHub account, pick this
   repo/branch/`app.py`, deploy. Copy the resulting `*.streamlit.app` URL.
3. Update `STREAMLIT_URL_PLACEHOLDER` in `build_static_site.py`, rebuild
   `docs/index.html`, commit and push.

These steps require the user's own Streamlit Cloud account and are not
performed by the implementation plan.
