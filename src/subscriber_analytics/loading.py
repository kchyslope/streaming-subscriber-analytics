"""Load raw subscriber data into a standardized DataFrame."""

from pathlib import Path

import pandas as pd

# Maps the raw Kaggle "Netflix Userbase Dataset" column names to snake_case.
RAW_COLUMN_MAP = {
    "User ID": "user_id",
    "Subscription Type": "subscription_type",
    "Monthly Revenue": "monthly_revenue",
    "Join Date": "join_date",
    "Last Payment Date": "last_payment_date",
    "Country": "country",
    "Age": "age",
    "Gender": "gender",
    "Device": "device",
    "Plan Duration": "plan_duration",
}

REQUIRED_COLUMNS = set(RAW_COLUMN_MAP.values())


def load_subscribers(path: str | Path) -> pd.DataFrame:
    """Read the subscriber CSV and normalize column names to snake_case.

    Accepts either the raw Kaggle column names or already-normalized ones,
    so a cleaned export can be re-loaded without modification.
    """
    df = pd.read_csv(path)
    df = df.rename(columns=RAW_COLUMN_MAP)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Input file is missing expected columns: {sorted(missing)}. "
            f"Found columns: {list(df.columns)}"
        )

    return df[list(RAW_COLUMN_MAP.values())]
