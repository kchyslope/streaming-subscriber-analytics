"""Validate raw subscriber data and derive analysis-ready columns."""

from __future__ import annotations

import warnings

import pandas as pd

DEFAULT_LAPSED_THRESHOLD_DAYS = 45


def clean_subscribers(
    df: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
    lapsed_threshold_days: int = DEFAULT_LAPSED_THRESHOLD_DAYS,
) -> pd.DataFrame:
    """Parse dates, derive tenure/recency columns, and flag likely-lapsed users.

    `is_lapsed` is a recency-based proxy, not a true churn label: a user is
    flagged if their last payment is more than `lapsed_threshold_days` before
    the reference date (defaults to the most recent last_payment_date in the
    data, i.e. "as of the day this dataset was pulled").
    """
    df = df.copy()

    # dayfirst=True (no explicit format) correctly parses both the real
    # dataset's DD-MM-YY dates and this project's ISO sample dates. Do NOT
    # add format="mixed" here -- combined with dayfirst=True it silently
    # mis-parses unambiguous ISO dates (verified: shifts some dates by
    # months without raising an error).
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Parsing dates in.*dayfirst")
        df["join_date"] = pd.to_datetime(df["join_date"], dayfirst=True, errors="coerce")
        df["last_payment_date"] = pd.to_datetime(
            df["last_payment_date"], dayfirst=True, errors="coerce"
        )

    before = len(df)
    df = df.dropna(subset=["join_date", "last_payment_date", "monthly_revenue", "age"])
    df = df.drop_duplicates(subset="user_id")
    dropped = before - len(df)

    df = df[(df["age"] > 0) & (df["age"] < 100)]
    df = df[df["monthly_revenue"] > 0]

    if reference_date is None:
        reference_date = df["last_payment_date"].max()

    df["tenure_days"] = (df["last_payment_date"] - df["join_date"]).dt.days
    df = df[df["tenure_days"] >= 0]

    df["days_since_last_payment"] = (reference_date - df["last_payment_date"]).dt.days
    df["is_lapsed"] = df["days_since_last_payment"] > lapsed_threshold_days

    df.attrs["reference_date"] = reference_date
    df.attrs["rows_dropped_in_cleaning"] = dropped
    df.attrs["lapsed_threshold_days"] = lapsed_threshold_days

    return df.reset_index(drop=True)
