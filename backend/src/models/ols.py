from dataclasses import dataclass
import math
import pandas as pd
import statsmodels.api as sm


@dataclass
class OLSResult:
    alpha: float
    betas: dict[str, float]
    tvalues: dict[str, float]
    pvalues: dict[str, float]
    r2: float
    adj_r2: float
    nobs: int
    alpha_ci: tuple[float, float]
    se_type: str
    date_range: tuple[str, str]


def run_ols(y: pd.Series, X: pd.DataFrame, newey_west: bool = True) -> OLSResult:
    X_const = sm.add_constant(X, has_constant="add")
    factor_names = list(X.columns)

    if newey_west:
        maxlags = max(1, int(math.floor(len(y) ** 0.25)))
        fit = sm.OLS(y, X_const).fit(
            cov_type="HAC", cov_kwds={"maxlags": maxlags, "use_correction": True}
        )
        se_type = "HAC"
    else:
        fit = sm.OLS(y, X_const).fit()
        se_type = "OLS"

    betas = {name: float(fit.params[name]) for name in factor_names}
    tvalues = {name: float(fit.tvalues[name]) for name in factor_names}
    tvalues["alpha"] = float(fit.tvalues["const"])
    pvalues = {name: float(fit.pvalues[name]) for name in factor_names}
    pvalues["alpha"] = float(fit.pvalues["const"])

    ci = fit.conf_int()
    alpha_ci = (float(ci.loc["const", 0]), float(ci.loc["const", 1]))

    start_date = y.index[0].strftime("%Y-%m")
    end_date = y.index[-1].strftime("%Y-%m")

    return OLSResult(
        alpha=float(fit.params["const"]),
        betas=betas,
        tvalues=tvalues,
        pvalues=pvalues,
        r2=float(fit.rsquared),
        adj_r2=float(fit.rsquared_adj),
        nobs=int(fit.nobs),
        alpha_ci=alpha_ci,
        se_type=se_type,
        date_range=(start_date, end_date),
    )
