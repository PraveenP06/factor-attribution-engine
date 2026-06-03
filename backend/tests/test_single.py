import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from src.attribution.single import run_single_attribution, AttributionResult


def make_factors(n: int = 80) -> pd.DataFrame:
    rng = np.random.default_rng(1)
    dates = pd.date_range("2018-01-31", periods=n, freq="ME")
    return pd.DataFrame(
        {"MKT": rng.normal(0.007, 0.04, n), "SMB": rng.normal(0, 0.02, n),
         "HML": rng.normal(0, 0.02, n), "RF": np.full(n, 0.0004)},
        index=dates,
    )


def make_prices(n: int = 82) -> pd.Series:
    rng = np.random.default_rng(2)
    dates = pd.date_range("2017-11-30", periods=n, freq="ME")
    prices = 100 * np.cumprod(1 + rng.normal(0.01, 0.05, n))
    return pd.Series(prices, index=dates, name="FAKE")


class TestRunSingleAttribution:
    def test_returns_attribution_result(self) -> None:
        with patch("src.attribution.single.fetch_factors") as mock_ff, \
             patch("src.attribution.single.fetch_monthly_prices") as mock_prices:
            mock_ff.return_value = make_factors()
            mock_prices.return_value = make_prices()
            result = run_single_attribution("FAKE", model="ff3")
        assert isinstance(result, AttributionResult)

    def test_ticker_stored_on_result(self) -> None:
        with patch("src.attribution.single.fetch_factors") as mock_ff, \
             patch("src.attribution.single.fetch_monthly_prices") as mock_prices:
            mock_ff.return_value = make_factors()
            mock_prices.return_value = make_prices()
            result = run_single_attribution("AAPL")
        assert result.ticker == "AAPL"

    def test_ols_result_has_betas(self) -> None:
        with patch("src.attribution.single.fetch_factors") as mock_ff, \
             patch("src.attribution.single.fetch_monthly_prices") as mock_prices:
            mock_ff.return_value = make_factors()
            mock_prices.return_value = make_prices()
            result = run_single_attribution("FAKE")
        assert "MKT" in result.ols.betas
        assert result.ols.r2 > 0

    def test_rolling_df_populated_when_enough_data(self) -> None:
        with patch("src.attribution.single.fetch_factors") as mock_ff, \
             patch("src.attribution.single.fetch_monthly_prices") as mock_prices:
            mock_ff.return_value = make_factors(n=80)
            mock_prices.return_value = make_prices(n=82)
            result = run_single_attribution("FAKE", rolling_window=36)
        assert not result.rolling_df.empty

    def test_rolling_df_empty_when_too_few_obs(self) -> None:
        with patch("src.attribution.single.fetch_factors") as mock_ff, \
             patch("src.attribution.single.fetch_monthly_prices") as mock_prices:
            mock_ff.return_value = make_factors(n=30)
            mock_prices.return_value = make_prices(n=32)
            result = run_single_attribution("FAKE", rolling_window=36)
        assert result.rolling_df.empty
