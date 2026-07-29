import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from generate_sample_data import generate  # noqa: E402

from subscriber_analytics.cleaning import clean_subscribers
from subscriber_analytics.loading import RAW_COLUMN_MAP


@pytest.fixture
def raw_df():
    return generate(n=300, seed=1)


@pytest.fixture
def clean_df(raw_df):
    renamed = raw_df.rename(columns=RAW_COLUMN_MAP)
    return clean_subscribers(renamed)
