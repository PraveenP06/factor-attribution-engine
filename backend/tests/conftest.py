import pandas as pd
import numpy as np
import pytest


@pytest.fixture
def factor_data() -> pd.DataFrame:
    """Synthetic FF3 factor data — 60 months. Values are decimals (not percent)."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2019-01-31", periods=60, freq="ME")
    return pd.DataFrame(
        {
            "MKT": rng.normal(0.007, 0.04, 60),
            "SMB": rng.normal(0.001, 0.02, 60),
            "HML": rng.normal(0.001, 0.02, 60),
            "RF": np.full(60, 0.0004),
        },
        index=dates,
    )


@pytest.fixture
def factor_data_ff4(factor_data: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(99)
    data = factor_data.copy()
    data["MOM"] = rng.normal(0.003, 0.03, len(data))
    return data


@pytest.fixture
def factor_data_ff5(factor_data_ff4: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(77)
    data = factor_data_ff4.copy()
    data["RMW"] = rng.normal(0.002, 0.015, len(data))
    data["CMA"] = rng.normal(0.001, 0.015, len(data))
    return data


@pytest.fixture
def price_series() -> pd.Series:
    """Synthetic monthly price series for 62 months (yields 61 return observations)."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2018-12-31", periods=62, freq="ME")
    prices = 100 * np.cumprod(1 + rng.normal(0.01, 0.05, 62))
    return pd.Series(prices, index=dates, name="FAKE")


@pytest.fixture
def aligned_df(factor_data: pd.DataFrame) -> pd.DataFrame:
    """Aligned DataFrame: excess_return + 3 factor columns, 60 rows."""
    rng = np.random.default_rng(42)
    df = factor_data.copy()
    # excess return = 1.2*MKT + 0.3*SMB - 0.2*HML + small noise
    df["excess_return"] = (
        1.2 * df["MKT"] + 0.3 * df["SMB"] - 0.2 * df["HML"]
        + rng.normal(0, 0.01, len(df))
    )
    return df[["excess_return", "MKT", "SMB", "HML"]]
