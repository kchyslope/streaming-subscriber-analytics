"""EDA aggregations, hypothesis tests, and a churn-proxy classifier."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_FEATURES = ["age", "tenure_days", "monthly_revenue"]
CATEGORICAL_FEATURES = ["subscription_type", "device", "gender"]


def summarize(df: pd.DataFrame) -> dict:
    """High-level overview stats for the cleaned subscriber base."""
    return {
        "n_subscribers": len(df),
        "total_monthly_revenue": round(df["monthly_revenue"].sum(), 2),
        "avg_monthly_revenue": round(df["monthly_revenue"].mean(), 2),
        "avg_age": round(df["age"].mean(), 1),
        "lapsed_rate": round(df["is_lapsed"].mean(), 4),
        "reference_date": df.attrs.get("reference_date"),
        "earliest_join_date": df["join_date"].min(),
        "latest_join_date": df["join_date"].max(),
    }


def revenue_by(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Subscriber count, mean revenue, and total revenue grouped by `by`."""
    grouped = df.groupby(by, observed=True)["monthly_revenue"].agg(
        subscribers="count", avg_revenue="mean", total_revenue="sum"
    )
    return grouped.sort_values("total_revenue", ascending=False).round(2).reset_index()


def segment_counts(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Value counts and share of subscriber base for a categorical column."""
    counts = df[by].value_counts().rename("subscribers")
    share = (counts / counts.sum()).rename("share")
    return pd.concat([counts, share.round(4)], axis=1).reset_index(names=by)


def chi_square_association(df: pd.DataFrame, col_a: str, col_b: str) -> dict:
    """Chi-square test of independence between two categorical columns."""
    table = pd.crosstab(df[col_a], df[col_b])
    chi2, p_value, dof, _expected = stats.chi2_contingency(table)
    return {
        "test": "chi-square",
        "columns": (col_a, col_b),
        "chi2": round(chi2, 3),
        "p_value": round(p_value, 4),
        "dof": dof,
        "significant_at_0.05": bool(p_value < 0.05),
    }


def anova_revenue_by_plan(df: pd.DataFrame) -> dict:
    """One-way ANOVA: does mean monthly revenue differ across subscription plans?"""
    groups = [g["monthly_revenue"].values for _, g in df.groupby("subscription_type")]
    f_stat, p_value = stats.f_oneway(*groups)
    return {
        "test": "one-way ANOVA",
        "target": "monthly_revenue",
        "grouped_by": "subscription_type",
        "f_stat": round(f_stat, 3),
        "p_value": round(p_value, 6),
        "significant_at_0.05": bool(p_value < 0.05),
    }


def ttest_age_by_lapsed_status(df: pd.DataFrame) -> dict:
    """Independent t-test: does mean age differ between lapsed and active users?"""
    lapsed_ages = df.loc[df["is_lapsed"], "age"]
    active_ages = df.loc[~df["is_lapsed"], "age"]
    t_stat, p_value = stats.ttest_ind(lapsed_ages, active_ages, equal_var=False)
    return {
        "test": "Welch's t-test",
        "target": "age",
        "grouped_by": "is_lapsed",
        "lapsed_mean_age": round(lapsed_ages.mean(), 1),
        "active_mean_age": round(active_ages.mean(), 1),
        "t_stat": round(t_stat, 3),
        "p_value": round(p_value, 4),
        "significant_at_0.05": bool(p_value < 0.05),
    }


@dataclass
class ChurnModelResult:
    pipeline: Pipeline
    accuracy: float
    roc_auc: float | None
    confusion_matrix: np.ndarray
    feature_names: list[str]
    coefficients: pd.DataFrame
    n_train: int
    n_test: int


def fit_churn_proxy_model(df: pd.DataFrame, random_state: int = 42) -> ChurnModelResult:
    """Logistic regression predicting `is_lapsed` from demographic/usage features.

    This predicts the recency-based lapsed proxy defined in cleaning.py, not
    verified churn — framed here as a demonstration of the modeling workflow,
    not a production churn model.
    """
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df["is_lapsed"].astype(int)

    stratify = y if y.nunique() > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_state, stratify=stratify
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    pipeline = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", LogisticRegression(max_iter=1000, random_state=random_state)),
        ]
    )
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    roc_auc = None
    if y_test.nunique() > 1:
        y_proba = pipeline.predict_proba(X_test)[:, 1]
        roc_auc = roc_auc_score(y_test, y_proba)

    cm = confusion_matrix(y_test, y_pred)

    feature_names = list(
        pipeline.named_steps["preprocess"].get_feature_names_out()
    )
    coefficients = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": pipeline.named_steps["model"].coef_[0],
        }
    ).sort_values("coefficient", key=np.abs, ascending=False)

    return ChurnModelResult(
        pipeline=pipeline,
        accuracy=round(accuracy, 4),
        roc_auc=round(roc_auc, 4) if roc_auc is not None else None,
        confusion_matrix=cm,
        feature_names=feature_names,
        coefficients=coefficients.reset_index(drop=True),
        n_train=len(X_train),
        n_test=len(X_test),
    )
