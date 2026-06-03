import pandas as pd
import numpy as np
import pytest
from src.models.ols import run_ols, OLSResult


def make_known_regression(n: int = 120, seed: int = 0) -> tuple[pd.Series, pd.DataFrame]:
    """y = 0.003 + 1.2*MKT + 0.3*SMB - 0.2*HML + noise. True betas are known."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2014-01-31", periods=n, freq="ME")
    mkt = rng.normal(0.007, 0.04, n)
    smb = rng.normal(0.001, 0.02, n)
    hml = rng.normal(0.001, 0.02, n)
    y = 0.003 + 1.2 * mkt + 0.3 * smb - 0.2 * hml + rng.normal(0, 0.005, n)
    X = pd.DataFrame({"MKT": mkt, "SMB": smb, "HML": hml}, index=dates)
    return pd.Series(y, index=dates, name="excess_return"), X


class TestRunOLS:
    def test_returns_ols_result(self) -> None:
        y, X = make_known_regression()
        result = run_ols(y, X)
        assert isinstance(result, OLSResult)

    def test_alpha_near_true_value(self) -> None:
        y, X = make_known_regression()
        result = run_ols(y, X)
        assert abs(result.alpha - 0.003) < 0.002  # within 20bp

    def test_mkt_beta_near_true_value(self) -> None:
        y, X = make_known_regression()
        result = run_ols(y, X)
        assert abs(result.betas["MKT"] - 1.2) < 0.1

    def test_r2_in_valid_range(self) -> None:
        y, X = make_known_regression()
        result = run_ols(y, X)
        assert 0 < result.r2 <= 1.0

    def test_adj_r2_less_than_r2(self) -> None:
        y, X = make_known_regression()
        result = run_ols(y, X)
        assert result.adj_r2 <= result.r2

    def test_tvalues_are_finite(self) -> None:
        y, X = make_known_regression()
        result = run_ols(y, X)
        assert all(np.isfinite(t) for t in result.tvalues.values())

    def test_pvalues_in_zero_one(self) -> None:
        y, X = make_known_regression()
        result = run_ols(y, X)
        assert all(0 <= p <= 1 for p in result.pvalues.values())

    def test_alpha_ci_is_two_element_tuple(self) -> None:
        y, X = make_known_regression()
        result = run_ols(y, X)
        assert len(result.alpha_ci) == 2
        assert result.alpha_ci[0] < result.alpha_ci[1]

    def test_nobs_matches_input(self) -> None:
        y, X = make_known_regression(n=80)
        result = run_ols(y, X)
        assert result.nobs == 80

    def test_se_type_hac_by_default(self) -> None:
        y, X = make_known_regression()
        result = run_ols(y, X)
        assert result.se_type == "HAC"

    def test_vanilla_ols_se_type(self) -> None:
        y, X = make_known_regression()
        result = run_ols(y, X, newey_west=False)
        assert result.se_type == "OLS"

    def test_hac_se_differs_from_ols_se(self) -> None:
        """HAC standard errors should differ from vanilla OLS on autocorrelated residuals."""
        rng = np.random.default_rng(5)
        n = 120
        dates = pd.date_range("2014-01-31", periods=n, freq="ME")
        mkt = rng.normal(0.007, 0.04, n)
        # introduce autocorrelation in residuals
        noise = np.zeros(n)
        noise[0] = rng.normal(0, 0.01)
        for i in range(1, n):
            noise[i] = 0.5 * noise[i - 1] + rng.normal(0, 0.01)
        y = pd.Series(1.0 * mkt + noise, index=dates)
        X = pd.DataFrame({"MKT": mkt}, index=dates)
        hac = run_ols(y, X, newey_west=True)
        ols = run_ols(y, X, newey_west=False)
        assert hac.tvalues["MKT"] != ols.tvalues["MKT"]
