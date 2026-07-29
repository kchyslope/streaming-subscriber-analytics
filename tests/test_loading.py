import pandas as pd
import pytest

from subscriber_analytics.loading import load_subscribers


def test_load_subscribers_renames_columns(tmp_path, raw_df):
    csv_path = tmp_path / "sample.csv"
    raw_df.to_csv(csv_path, index=False)

    df = load_subscribers(csv_path)

    assert "user_id" in df.columns
    assert "subscription_type" in df.columns
    assert "User ID" not in df.columns
    assert len(df) == len(raw_df)


def test_load_subscribers_raises_on_missing_columns(tmp_path):
    bad_path = tmp_path / "bad.csv"
    pd.DataFrame({"foo": [1, 2, 3]}).to_csv(bad_path, index=False)

    with pytest.raises(ValueError, match="missing expected columns"):
        load_subscribers(bad_path)
