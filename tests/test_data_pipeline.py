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
