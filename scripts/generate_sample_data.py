"""Generate a synthetic CSV matching the Netflix Userbase Dataset schema.

This is a stand-in for testing the pipeline before you download the real
dataset. It is NOT real subscriber data -- see README.md for the actual
Kaggle source. Column names and value ranges mirror the real dataset closely
enough that swapping this file for the real CSV requires no code changes.
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_SUBSCRIBERS = 2500
END_DATE = pd.Timestamp("2024-06-01")  # fixed "as of" date for reproducibility

PLANS = ["Basic", "Standard", "Premium"]
PLAN_WEIGHTS = [0.35, 0.40, 0.25]
PLAN_REVENUE = {"Basic": (8.99, 11.99), "Standard": (13.99, 15.99), "Premium": (17.99, 19.99)}

COUNTRIES = ["United States", "Canada", "United Kingdom", "Germany", "France",
             "Brazil", "Mexico", "Australia", "India", "Spain"]
COUNTRY_WEIGHTS = [0.30, 0.10, 0.10, 0.08, 0.08, 0.09, 0.08, 0.06, 0.06, 0.05]

DEVICES = ["Smartphone", "Tablet", "Smart TV", "Laptop"]
DEVICE_WEIGHTS = [0.35, 0.15, 0.30, 0.20]

PLAN_DURATIONS = ["1 Month", "3 Months", "12 Months"]
PLAN_DURATION_WEIGHTS = [0.6, 0.25, 0.15]

GENDERS = ["Male", "Female"]


def generate(n: int = N_SUBSCRIBERS, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    subscription_type = rng.choice(PLANS, size=n, p=PLAN_WEIGHTS)
    monthly_revenue = np.array(
        [round(rng.uniform(*PLAN_REVENUE[p]), 2) for p in subscription_type]
    )

    country = rng.choice(COUNTRIES, size=n, p=COUNTRY_WEIGHTS)
    device = rng.choice(DEVICES, size=n, p=DEVICE_WEIGHTS)
    plan_duration = rng.choice(PLAN_DURATIONS, size=n, p=PLAN_DURATION_WEIGHTS)
    gender = rng.choice(GENDERS, size=n)
    age = rng.normal(38, 12, size=n).clip(18, 75).round().astype(int)

    # Join dates spread over the ~2 years before END_DATE.
    join_offsets_days = rng.integers(30, 730, size=n)
    join_date = END_DATE - pd.to_timedelta(join_offsets_days, unit="D")

    # ~18% of users are "lapsed": last payment well before END_DATE.
    is_lapsed = rng.random(n) < 0.18
    recent_gap = rng.integers(0, 30, size=n)
    lapsed_gap = rng.integers(60, 200, size=n)
    days_since_payment = np.where(is_lapsed, lapsed_gap, recent_gap)
    # Never pay before joining.
    max_gap_from_join = (END_DATE - join_date).days
    days_since_payment = np.minimum(days_since_payment, max_gap_from_join)
    last_payment_date = END_DATE - pd.to_timedelta(days_since_payment, unit="D")

    df = pd.DataFrame(
        {
            "User ID": np.arange(1, n + 1),
            "Subscription Type": subscription_type,
            "Monthly Revenue": monthly_revenue,
            "Join Date": join_date.strftime("%Y-%m-%d"),
            "Last Payment Date": last_payment_date.strftime("%Y-%m-%d"),
            "Country": country,
            "Age": age,
            "Gender": gender,
            "Device": device,
            "Plan Duration": plan_duration,
        }
    )
    return df


if __name__ == "__main__":
    out_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "netflix_userbase_sample.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    generate().to_csv(out_path, index=False)
    print(f"Wrote {N_SUBSCRIBERS} sample rows to {out_path}")
