from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Union
import json

from src.attribution.single import run_single_attribution
from src.attribution.portfolio import compute_portfolio_returns
from src.data.french import fetch_factors
from src.data.prices import fetch_monthly_prices
from src.data.align import align_data
from src.models.ols import run_ols
from src.models.rolling import rolling_regression
from src.reporting.tables import significance_stars, build_verdict
from src.reporting.plots import factor_loadings_chart, rolling_beta_chart, actual_vs_predicted_chart

router = APIRouter()


class WeightedTicker(BaseModel):
    ticker: str
    weight: float


class AnalyzeRequest(BaseModel):
    mode: str
    tickers: list[Union[str, WeightedTicker]]
    model: str = "ff3"
    start: str = "2015-01"
    end: str = "2024-12"
    newey_west: bool = True

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        if v not in ("ff3", "ff4", "ff5"):
            raise ValueError("model must be 'ff3', 'ff4', or 'ff5'")
        return v

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        if v not in ("single", "portfolio"):
            raise ValueError("mode must be 'single' or 'portfolio'")
        return v


def _to_api_date(period: str) -> str:
    return period + "-01"


@router.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    start_date = _to_api_date(request.start)
    end_date = _to_api_date(request.end)

    try:
        if request.mode == "single":
            ticker = request.tickers[0]
            if not isinstance(ticker, str):
                ticker = ticker.ticker
            result = run_single_attribution(
                ticker=ticker.upper(),
                model=request.model,
                start=start_date,
                end=end_date,
                newey_west=request.newey_west,
            )
            ols = result.ols
            aligned = result.aligned_df
            rolling_df = result.rolling_df
            display_ticker = ticker.upper()

        else:
            weighted = [
                t if isinstance(t, WeightedTicker) else WeightedTicker(ticker=t, weight=1.0)
                for t in request.tickers
            ]
            factors = fetch_factors(request.model)
            holdings = {}
            for wt in weighted:
                prices = fetch_monthly_prices(wt.ticker.upper(), start=start_date, end=end_date)
                aligned_single = align_data(prices, factors)
                holdings[wt.ticker.upper()] = (aligned_single["excess_return"], wt.weight)

            portfolio_returns = compute_portfolio_returns(holdings)
            factors_trimmed = factors.reindex(portfolio_returns.index)
            factor_cols = [c for c in factors.columns if c != "RF"]
            aligned = factors_trimmed[factor_cols].copy()
            aligned.insert(0, "excess_return", portfolio_returns)
            aligned = aligned.dropna()

            ols = run_ols(aligned["excess_return"], aligned[factor_cols], newey_west=request.newey_west)
            rolling_window = 36
            rolling_df = rolling_regression(aligned, window=rolling_window) if len(aligned) > rolling_window else None
            display_ticker = "PORTFOLIO"

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(exc)}") from exc

    factor_cols_list = list(ols.betas.keys())
    coefficients = [
        {
            "name": "Alpha",
            "beta": round(ols.alpha, 6),
            "tstat": round(ols.tvalues["alpha"], 3),
            "pvalue": round(ols.pvalues["alpha"], 4),
            "sig": significance_stars(ols.pvalues["alpha"]),
        }
    ] + [
        {
            "name": f,
            "beta": round(ols.betas[f], 4),
            "tstat": round(ols.tvalues[f], 3),
            "pvalue": round(ols.pvalues[f], 4),
            "sig": significance_stars(ols.pvalues[f]),
        }
        for f in factor_cols_list
    ]

    rolling_betas_payload: dict = {}
    if rolling_df is not None and not rolling_df.empty:
        rolling_betas_payload = {
            "dates": [d.strftime("%Y-%m") for d in rolling_df.index],
            **{col: [round(v, 4) for v in rolling_df[col].tolist()] for col in rolling_df.columns},
        }

    return {
        "ticker": display_ticker,
        "model": request.model,
        "date_range": {"start": ols.date_range[0], "end": ols.date_range[1]},
        "n_obs": ols.nobs,
        "r2": round(ols.r2, 4),
        "adj_r2": round(ols.adj_r2, 4),
        "se_type": ols.se_type,
        "coefficients": coefficients,
        "alpha_ci": [round(ols.alpha_ci[0], 6), round(ols.alpha_ci[1], 6)],
        "verdict": build_verdict(ols),
        "rolling_betas": rolling_betas_payload,
        "factor_loadings_chart": json.loads(factor_loadings_chart(ols)),
        "rolling_beta_chart": json.loads(rolling_beta_chart(rolling_df if rolling_df is not None and not rolling_df.empty else __import__("pandas").DataFrame())),
        "actual_vs_predicted_chart": json.loads(actual_vs_predicted_chart(aligned, ols)),
    }
