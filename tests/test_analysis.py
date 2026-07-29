from subscriber_analytics.analysis import (
    anova_revenue_by_plan,
    chi_square_association,
    fit_churn_proxy_model,
    revenue_by,
    segment_counts,
    summarize,
    ttest_age_by_lapsed_status,
)


def test_summarize_returns_expected_keys(clean_df):
    summary = summarize(clean_df)
    assert summary["n_subscribers"] == len(clean_df)
    assert summary["total_monthly_revenue"] > 0
    assert 0 <= summary["lapsed_rate"] <= 1


def test_revenue_by_sums_to_total(clean_df):
    result = revenue_by(clean_df, "subscription_type")
    assert result["subscribers"].sum() == len(clean_df)
    assert abs(result["total_revenue"].sum() - clean_df["monthly_revenue"].sum()) < 0.5


def test_segment_counts_shares_sum_to_one(clean_df):
    result = segment_counts(clean_df, "device")
    assert abs(result["share"].sum() - 1.0) < 1e-6


def test_chi_square_association_returns_p_value(clean_df):
    result = chi_square_association(clean_df, "subscription_type", "device")
    assert 0 <= result["p_value"] <= 1


def test_anova_revenue_by_plan_is_significant(clean_df):
    # Revenue ranges don't overlap across plans by construction, so this
    # should always come out significant on generated data.
    result = anova_revenue_by_plan(clean_df)
    assert result["significant_at_0.05"] is True


def test_ttest_age_by_lapsed_status_returns_valid_result(clean_df):
    result = ttest_age_by_lapsed_status(clean_df)
    assert 0 <= result["p_value"] <= 1


def test_fit_churn_proxy_model_runs_end_to_end(clean_df):
    result = fit_churn_proxy_model(clean_df)
    assert 0 <= result.accuracy <= 1
    assert result.n_train + result.n_test == len(clean_df)
    assert not result.coefficients.empty
