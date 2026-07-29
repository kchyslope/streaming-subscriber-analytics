# Streaming Subscriber Analytics

Analyzes a streaming service's subscriber base (Netflix Userbase schema) to answer:
who are the subscribers, what drives revenue, and which segments look most likely to lapse.

Built as a portfolio piece demonstrating EDA, hypothesis testing, a light predictive
model, and clean pipeline architecture. The analysis logic (`src/subscriber_analytics/`)
is intentionally GUI-agnostic — every function takes/returns plain DataFrames, dicts, or
Plotly `Figure` objects, so a GUI (Tkinter, PyQt/PySide, Streamlit, etc.) can call it
directly without modification.

## Project structure

```
data/raw/                          # place the subscriber CSV here (gitignored)
src/subscriber_analytics/
  loading.py                       # read_csv + column normalization
  cleaning.py                      # validation, derived columns (tenure, lapsed flag)
  analysis.py                      # EDA aggregations, hypothesis tests, churn-proxy model
  viz.py                           # Plotly figure builders
  data_pipeline.py                 # shared load-and-clean pipeline (used by app.py and the static site builder)
scripts/generate_sample_data.py    # synthetic CSV matching the real schema, for testing
scripts/build_static_site.py       # renders docs/index.html, a static GitHub Pages snapshot
app.py                             # Streamlit dashboard (repo root)
docs/index.html                    # published static snapshot (GitHub Pages)
tests/                             # pytest suite, one file per src module
notebooks/01_subscriber_analysis.ipynb   # narrative walkthrough of the full analysis
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Getting data

This project targets the **Netflix Userbase Dataset** on Kaggle:
https://www.kaggle.com/datasets/arnavsmayan/netflix-userbase-dataset

Download it and place the CSV at `data/raw/netflix_userbase.csv` (or point `DATA_PATH`
at wherever you saved it — the loader only requires these columns, in any order):

`User ID, Subscription Type, Monthly Revenue, Join Date, Last Payment Date, Country, Age, Gender, Device, Plan Duration`

**No Kaggle account yet?** Generate a synthetic stand-in with the same schema:

```bash
python scripts/generate_sample_data.py
```

This writes `data/raw/netflix_userbase_sample.csv` (2,500 rows, fixed random seed).
It's clearly synthetic data for exercising the pipeline — swap in the real CSV before
drawing any actual conclusions.

## Running the analysis

Open `notebooks/01_subscriber_analysis.ipynb` in VS Code (native Jupyter support, no
extra setup) or JupyterLab, set `DATA_PATH` in the first code cell to your CSV, and run
top to bottom. It walks through:

1. Overview stats (subscriber count, revenue, lapsed rate)
2. Revenue by plan, country, and device
3. Signups over time
4. Age distribution and lapsed rate by plan, with hypothesis tests
   (chi-square for plan/device association, ANOVA for revenue-by-plan, Welch's t-test
   for age-by-lapsed-status)
5. A logistic regression predicting the lapsed-proxy label, with feature coefficients

## Running the dashboard

**Interactive (Streamlit):**

```bash
pip install -e .
streamlit run app.py
```

Opens a local dashboard with sidebar filters (plan/country/device) and four
tabs: Overview, Segments, Statistical Tests, and Churn-Risk Model. Sample
data is generated automatically on first run if `data/raw/` is empty.

**Note:** the Streamlit app and the static site builder (below) always load the
synthetic sample CSV at `data/raw/netflix_userbase_sample.csv` via
`data_pipeline.load_and_clean_data()` — this path is hardcoded and does **not**
honor a real dataset placed elsewhere (e.g. `data/raw/netflix_userbase.csv`) or
the `DATA_PATH` variable. They're demo/showcase surfaces built on the bundled
sample data. To analyze the real Kaggle dataset, use the notebook (see "Running
the analysis" above), which does honor `DATA_PATH`.

**Static snapshot (GitHub Pages):**

A read-only snapshot of the full dataset is published at
https://kchyslope.github.io/streaming-subscriber-analytics/. To regenerate
it after code changes:

```bash
python scripts/build_static_site.py
git add docs/index.html
git commit -m "docs: refresh static dashboard snapshot"
```

## The "lapsed" label, and why it's a proxy

This dataset has no real churn flag. `is_lapsed` in `cleaning.py` is a **recency proxy**:
a user is flagged if their last payment is more than 45 days before the most recent
payment date in the dataset. Every finding downstream of this flag (the t-test, the
lapsed-rate charts, the logistic regression) should be read as a demonstration of the
analytical workflow, not a verified churn signal — say so explicitly if you present this.

## Tests

```bash
pytest
```

21 tests covering loading validation, cleaning/derivation logic, each analysis function,
that every viz function returns a valid `Figure`, the shared data pipeline's
load/generate/reuse behavior, and the static site builder.

## Building a GUI on top

Everything in `src/subscriber_analytics/` is a plain function — no I/O side effects
except `loading.load_subscribers`. A GUI layer would typically:

1. Call `loading.load_subscribers()` + `cleaning.clean_subscribers()` once, on load or on
   file-picker selection.
2. Call the relevant `analysis.*` function per view/tab.
3. Pass the result into the matching `viz.*` function and embed the returned Plotly
   `Figure` (e.g. via `QWebEngineView` for PyQt/PySide, or natively if building with
   Streamlit/Dash).

This is exactly what `app.py` does — see "Running the dashboard" above for the
working example.
