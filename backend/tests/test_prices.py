import pandas as pd
import numpy as np
import pytest
from src.data.prices import compute_simple_returns


class TestComputeSimpleReturns:
    def test_returns_series(self) -> None:
        dates = pd.date_range("2019-01-31", periods=13, freq="ME")
        prices = pd.Series(100 * np.cumprod(1 + np.full(13, 0.01)), index=dates)
        result = compute_simple_returns(prices)
        assert isinstance(result, pd.Series)

    def test_length_is_n_minus_one(self) -> None:
        dates = pd.date_range("2019-01-31", periods=13, freq="ME")
        prices = pd.Series(100 * np.cumprod(1 + np.full(13, 0.01)), index=dates)
        result = compute_simple_returns(prices)
        assert len(result) == 12

    def test_known_return_value(self) -> None:
        dates = pd.date_range("2019-01-31", periods=3, freq="ME")
        prices = pd.Series([100.0, 110.0, 99.0], index=dates)
        result = compute_simple_returns(prices)
        assert abs(result.iloc[0] - 0.10) < 1e-9
        assert abs(result.iloc[1] - ((99.0 - 110.0) / 110.0)) < 1e-9

    def test_no_nan_in_result(self) -> None:
        dates = pd.date_range("2019-01-31", periods=13, freq="ME")
        prices = pd.Series(100 * np.cumprod(1 + np.full(13, 0.005)), index=dates)
        result = compute_simple_returns(prices)
        assert result.notna().all()

    def test_assertion_on_invalid_returns(self) -> None:
        dates = pd.date_range("2019-01-31", periods=3, freq="ME")
        prices = pd.Series([100.0, 50.0, -10.0], index=dates)
        with pytest.raises(AssertionError):
            compute_simple_returns(prices)
