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
