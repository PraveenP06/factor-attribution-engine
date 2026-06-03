import pandas as pd
import numpy as np
import pytest
from src.data.align import align_data, compute_excess_returns


def make_factor_df(n: int = 60, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2019-01-31", periods=n, freq="ME")
    return pd.DataFrame(
        {"MKT": rng.normal(0.007, 0.04, n), "SMB": rng.normal(0, 0.02, n),
         "HML": rng.normal(0, 0.02, n), "RF": np.full(n, 0.0004)},
        index=dates,
    )


def make_price_series(n: int = 62, seed: int = 1) -> pd.Series:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2018-12-31", periods=n, freq="ME")
    prices = 100 * np.cumprod(1 + rng.normal(0.01, 0.05, n))
    return pd.Series(prices, index=dates, name="TEST")


class TestComputeExcessReturns:
    def test_subtracts_rf_from_returns(self) -> None:
        factors = make_factor_df()
        prices = make_price_series()
        result = compute_excess_returns(prices, factors)
        assert "excess_return" in result.columns

    def test_excess_return_is_return_minus_rf(self) -> None:
        factors = make_factor_df(n=5)
        factors["RF"] = 0.001
        dates = pd.date_range("2018-12-31", periods=6, freq="ME")
        prices = pd.Series([100.0, 105.0, 102.0, 108.0, 104.0, 110.0], index=dates, name="X")
        result = compute_excess_returns(prices, factors)
        # simple return for first period: (105-100)/100 = 0.05; excess = 0.05 - 0.001 = 0.049
        assert abs(result["excess_return"].iloc[0] - 0.049) < 1e-9

    def test_returns_are_simple_not_log(self) -> None:
        factors = make_factor_df(n=3)
        factors["RF"] = 0.0
        dates = pd.date_range("2018-12-31", periods=4, freq="ME")
        prices = pd.Series([100.0, 200.0, 100.0, 150.0], index=dates, name="X")
        result = compute_excess_returns(prices, factors)
        assert abs(result["excess_return"].iloc[0] - 1.0) < 1e-9  # +100% simple


class TestAlignData:
    def test_no_nan_after_alignment(self) -> None:
        factors = make_factor_df()
        prices = make_price_series()
        result = align_data(prices, factors)
        assert result.isnull().sum().sum() == 0

    def test_minimum_observations_required(self) -> None:
        factors = make_factor_df(n=60)
        short_prices = make_price_series(n=5)
        with pytest.raises(ValueError, match="at least 24"):
            align_data(short_prices, factors)

    def test_inner_join_respects_overlap(self) -> None:
        factors = make_factor_df(n=60)
        prices = make_price_series(n=62)
        result = align_data(prices, factors)
        assert len(result) <= 60

    def test_output_columns(self) -> None:
        factors = make_factor_df()
        prices = make_price_series()
        result = align_data(prices, factors)
        assert set(result.columns) >= {"excess_return", "MKT", "SMB", "HML"}

    def test_excess_returns_in_valid_range(self) -> None:
        factors = make_factor_df()
        prices = make_price_series()
        result = align_data(prices, factors)
        # monthly returns should be between -1 and +5 for any sane stock
        assert (result["excess_return"] > -1).all()
        assert (result["excess_return"] < 5).all()
