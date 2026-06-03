import pandas as pd
import numpy as np
import pytest
from src.models.rolling import rolling_regression


def make_aligned_df(n: int = 120) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    dates = pd.date_range("2014-01-31", periods=n, freq="ME")
    mkt = rng.normal(0.007, 0.04, n)
    smb = rng.normal(0.001, 0.02, n)
    hml = rng.normal(0.001, 0.02, n)
    excess = 1.1 * mkt + 0.2 * smb + rng.normal(0, 0.01, n)
    return pd.DataFrame(
        {"excess_return": excess, "MKT": mkt, "SMB": smb, "HML": hml}, index=dates
    )


class TestRollingRegression:
    def test_output_length(self) -> None:
        df = make_aligned_df(n=120)
        result = rolling_regression(df, window=36)
        assert len(result) == 120 - 36 + 1

    def test_output_columns_include_betas(self) -> None:
        df = make_aligned_df()
        result = rolling_regression(df, window=36)
        for col in ["alpha", "MKT", "SMB", "HML"]:
            assert col in result.columns

    def test_index_is_datetime(self) -> None:
        df = make_aligned_df()
        result = rolling_regression(df, window=36)
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_all_betas_finite(self) -> None:
        df = make_aligned_df()
        result = rolling_regression(df, window=36)
        for col in ["alpha", "MKT", "SMB", "HML"]:
            assert result[col].notna().all()

    def test_window_too_large_raises(self) -> None:
        df = make_aligned_df(n=30)
        with pytest.raises(ValueError, match="window"):
            rolling_regression(df, window=36)

    def test_custom_window(self) -> None:
        df = make_aligned_df(n=60)
        result = rolling_regression(df, window=24)
        assert len(result) == 60 - 24 + 1
