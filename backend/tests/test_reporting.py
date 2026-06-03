import pytest
from src.models.ols import OLSResult
from src.reporting.tables import significance_stars, build_verdict


def make_result(alpha: float = 0.001, alpha_tstat: float = 0.8, r2: float = 0.70) -> OLSResult:
    return OLSResult(
        alpha=alpha,
        betas={"MKT": 1.2, "SMB": -0.1, "HML": -0.3},
        tvalues={"alpha": alpha_tstat, "MKT": 14.0, "SMB": -2.1, "HML": -3.4},
        pvalues={"alpha": 0.42, "MKT": 0.001, "SMB": 0.04, "HML": 0.001},
        r2=r2,
        adj_r2=r2 - 0.01,
        nobs=108,
        alpha_ci=(-0.003, 0.005),
        se_type="HAC",
        date_range=("2015-01", "2023-12"),
    )


class TestSignificanceStars:
    def test_triple_star_below_one_pct(self) -> None:
        assert significance_stars(0.005) == "***"

    def test_double_star_below_five_pct(self) -> None:
        assert significance_stars(0.03) == "**"

    def test_single_star_below_ten_pct(self) -> None:
        assert significance_stars(0.08) == "*"

    def test_no_star_above_ten_pct(self) -> None:
        assert significance_stars(0.15) == ""


class TestBuildVerdict:
    def test_mentions_alpha_not_significant(self) -> None:
        result = make_result(alpha_tstat=0.8)
        verdict = build_verdict(result)
        assert "not significant" in verdict.lower() or "indistinguishable" in verdict.lower()

    def test_mentions_adj_r2(self) -> None:
        result = make_result(r2=0.70)  # adj_r2 = 0.69 (r2 - 0.01 per make_result)
        verdict = build_verdict(result)
        assert "69%" in verdict or "0.69" in verdict

    def test_mentions_primary_factor(self) -> None:
        result = make_result()
        verdict = build_verdict(result)
        assert "MKT" in verdict or "market" in verdict.lower()
