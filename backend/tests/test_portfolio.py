import pandas as pd
import numpy as np
import pytest
from src.attribution.portfolio import compute_portfolio_returns


def make_return_series(n: int = 60, mean: float = 0.01, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2019-01-31", periods=n, freq="ME")
    return pd.Series(rng.normal(mean, 0.04, n), index=dates)


class TestComputePortfolioReturns:
    def test_single_stock_100pct_returns_same_series(self) -> None:
        r = make_return_series(seed=1)
        result = compute_portfolio_returns({"A": (r, 1.0)})
        pd.testing.assert_series_equal(result, r, check_names=False)

    def test_equal_weight_two_stocks(self) -> None:
        r1 = make_return_series(seed=1)
        r2 = make_return_series(seed=2)
        result = compute_portfolio_returns({"A": (r1, 0.5), "B": (r2, 0.5)})
        expected = 0.5 * r1 + 0.5 * r2
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_weights_not_summing_to_one_raises(self) -> None:
        r1 = make_return_series(seed=1)
        r2 = make_return_series(seed=2)
        with pytest.raises(ValueError, match="weights"):
            compute_portfolio_returns({"A": (r1, 0.6), "B": (r2, 0.6)})

    def test_output_is_series(self) -> None:
        r = make_return_series(seed=3)
        result = compute_portfolio_returns({"A": (r, 1.0)})
        assert isinstance(result, pd.Series)

    def test_overlapping_date_range_used(self) -> None:
        r1 = make_return_series(n=60, seed=1)
        r2_dates = pd.date_range("2020-01-31", periods=40, freq="ME")
        r2 = pd.Series(np.random.default_rng(2).normal(0.01, 0.04, 40), index=r2_dates)
        result = compute_portfolio_returns({"A": (r1, 0.5), "B": (r2, 0.5)})
        assert len(result) == 40  # inner join
