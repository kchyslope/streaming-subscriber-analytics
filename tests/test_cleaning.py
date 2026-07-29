import pandas as pd

from subscriber_analytics.cleaning import clean_subscribers
from subscriber_analytics.loading import RAW_COLUMN_MAP


def test_clean_subscribers_derives_columns(raw_df):
    renamed = raw_df.rename(columns=RAW_COLUMN_MAP)
    clean = clean_subscribers(renamed)

    assert "tenure_days" in clean.columns
    assert "days_since_last_payment" in clean.columns
    assert "is_lapsed" in clean.columns
    assert clean["tenure_days"].min() >= 0
    assert clean["is_lapsed"].dtype == bool


def test_clean_subscribers_drops_duplicates_and_invalid_rows(raw_df):
    renamed = raw_df.rename(columns=RAW_COLUMN_MAP)
    dup = pd.concat([renamed, renamed.iloc[[0]]], ignore_index=True)
    dup.loc[len(dup) - 1, "age"] = -5  # also invalid, should be dropped separately

    clean = clean_subscribers(dup)

    assert clean["user_id"].is_unique
    assert (clean["age"] > 0).all()
    assert (clean["age"] < 100).all()


def test_clean_subscribers_respects_custom_threshold(raw_df):
    renamed = raw_df.rename(columns=RAW_COLUMN_MAP)
    loose = clean_subscribers(renamed, lapsed_threshold_days=1000)

    assert loose["is_lapsed"].sum() == 0
