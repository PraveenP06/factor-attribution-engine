import pandas as pd
import numpy as np
import pytest
from src.data.french import parse_ff3, parse_ff4, parse_ff5, FACTOR_COLS_FF3, FACTOR_COLS_FF4, FACTOR_COLS_FF5


def make_raw_ff3_parsed(n: int = 60) -> pd.DataFrame:
    """Simulate parsed raw CSV: first col is YYYYMM int, rest are percent values."""
    rng = np.random.default_rng(1)
    dates = [int((pd.Timestamp("2019-01-31") + pd.DateOffset(months=i)).strftime("%Y%m")) for i in range(n)]
    return pd.DataFrame({
        0: dates,
        1: rng.normal(0.7, 4, n),
        2: rng.normal(0.1, 2, n),
        3: rng.normal(0.1, 2, n),
        4: np.full(n, 0.04),
    })


def make_raw_mom_parsed(n: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(2)
    dates = [int((pd.Timestamp("2019-01-31") + pd.DateOffset(months=i)).strftime("%Y%m")) for i in range(n)]
    return pd.DataFrame({0: dates, 1: rng.normal(0.3, 3, n)})


def make_raw_ff5_parsed(n: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(3)
    dates = [int((pd.Timestamp("2019-01-31") + pd.DateOffset(months=i)).strftime("%Y%m")) for i in range(n)]
    return pd.DataFrame({
        0: dates,
        1: rng.normal(0.7, 4, n),
        2: rng.normal(0.1, 2, n),
        3: rng.normal(0.1, 2, n),
        4: rng.normal(0.2, 1.5, n),
        5: rng.normal(0.1, 1.5, n),
        6: np.full(n, 0.04),
    })


class TestParseFF3:
    def test_output_columns(self) -> None:
        result = parse_ff3(make_raw_ff3_parsed())
        assert list(result.columns) == FACTOR_COLS_FF3

    def test_values_divided_by_100(self) -> None:
        result = parse_ff3(make_raw_ff3_parsed())
        assert result["MKT"].mean() < 0.05

    def test_values_in_valid_range(self) -> None:
        result = parse_ff3(make_raw_ff3_parsed())
        for col in ["MKT", "SMB", "HML"]:
            assert (result[col] > -0.5).all(), f"{col} has values below -0.5"
            assert (result[col] < 0.5).all(), f"{col} has values above 0.5"

    def test_index_is_datetime(self) -> None:
        result = parse_ff3(make_raw_ff3_parsed())
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_rf_in_valid_range(self) -> None:
        result = parse_ff3(make_raw_ff3_parsed())
        assert (result["RF"] >= 0).all()
        assert (result["RF"] < 0.01).all()


class TestParseFF4:
    def test_output_columns(self) -> None:
        result = parse_ff4(make_raw_ff3_parsed(), make_raw_mom_parsed())
        assert list(result.columns) == FACTOR_COLS_FF4

    def test_mom_divided_by_100(self) -> None:
        result = parse_ff4(make_raw_ff3_parsed(), make_raw_mom_parsed())
        assert result["MOM"].mean() < 0.05


class TestParseFF5:
    def test_output_columns(self) -> None:
        result = parse_ff5(make_raw_ff5_parsed())
        assert list(result.columns) == FACTOR_COLS_FF5

    def test_rmw_cma_divided_by_100(self) -> None:
        result = parse_ff5(make_raw_ff5_parsed())
        assert result["RMW"].mean() < 0.05
        assert result["CMA"].mean() < 0.05
