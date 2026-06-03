import json
import pandas as pd
import numpy as np
import pytest
from src.models.ols import OLSResult
from src.reporting.plots import factor_loadings_chart, rolling_beta_chart, actual_vs_predicted_chart


def make_ols_result() -> OLSResult:
    return OLSResult(
        alpha=0.001,
        betas={"MKT": 1.2, "SMB": -0.1, "HML": -0.3},
        tvalues={"alpha": 0.9, "MKT": 14.0, "SMB": -2.1, "HML": -3.4},
        pvalues={"alpha": 0.37, "MKT": 0.001, "SMB": 0.04, "HML": 0.001},
        r2=0.71,
        adj_r2=0.70,
        nobs=108,
        alpha_ci=(-0.003, 0.005),
        se_type="HAC",
        date_range=("2015-01", "2023-12"),
    )


def make_rolling_df(n: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(1)
    dates = pd.date_range("2019-01-31", periods=n, freq="ME")
    return pd.DataFrame(
        {"alpha": rng.normal(0, 0.002, n), "MKT": rng.normal(1.1, 0.1, n),
         "SMB": rng.normal(-0.1, 0.05, n), "HML": rng.normal(-0.2, 0.05, n)},
        index=dates,
    )


def make_aligned_df(n: int = 108) -> pd.DataFrame:
    rng = np.random.default_rng(2)
    dates = pd.date_range("2015-01-31", periods=n, freq="ME")
    mkt = rng.normal(0.007, 0.04, n)
    smb = rng.normal(0.001, 0.02, n)
    hml = rng.normal(0.001, 0.02, n)
    excess = 0.001 + 1.2 * mkt - 0.1 * smb - 0.3 * hml + rng.normal(0, 0.005, n)
    return pd.DataFrame(
        {"excess_return": excess, "MKT": mkt, "SMB": smb, "HML": hml}, index=dates
    )


class TestFactorLoadingsChart:
    def test_returns_valid_json_string(self) -> None:
        result = make_ols_result()
        chart_json = factor_loadings_chart(result)
        parsed = json.loads(chart_json)
        assert "data" in parsed

    def test_has_bar_trace(self) -> None:
        result = make_ols_result()
        parsed = json.loads(factor_loadings_chart(result))
        assert any(t.get("type") == "bar" for t in parsed["data"])

    def test_chart_has_all_factors(self) -> None:
        result = make_ols_result()
        parsed = json.loads(factor_loadings_chart(result))
        bar = next(t for t in parsed["data"] if t.get("type") == "bar")
        assert "MKT" in bar["x"]


class TestRollingBetaChart:
    def test_returns_valid_json_string(self) -> None:
        rolling_df = make_rolling_df()
        chart_json = rolling_beta_chart(rolling_df)
        json.loads(chart_json)

    def test_empty_df_returns_empty_json(self) -> None:
        parsed = json.loads(rolling_beta_chart(pd.DataFrame()))
        assert parsed == {}

    def test_has_scatter_traces(self) -> None:
        rolling_df = make_rolling_df()
        parsed = json.loads(rolling_beta_chart(rolling_df))
        assert any(t.get("type") == "scatter" for t in parsed["data"])


class TestActualVsPredictedChart:
    def test_returns_valid_json_string(self) -> None:
        result = make_ols_result()
        aligned = make_aligned_df()
        chart_json = actual_vs_predicted_chart(aligned, result)
        json.loads(chart_json)

    def test_has_multiple_traces(self) -> None:
        result = make_ols_result()
        aligned = make_aligned_df()
        parsed = json.loads(actual_vs_predicted_chart(aligned, result))
        assert len(parsed["data"]) >= 2
