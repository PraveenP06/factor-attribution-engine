import pandas as pd
from dataclasses import dataclass
from src.data.french import fetch_factors
from src.data.prices import fetch_monthly_prices
from src.data.align import align_data
from src.models.ols import run_ols, OLSResult
from src.models.rolling import rolling_regression


@dataclass
class AttributionResult:
    ols: OLSResult
    aligned_df: pd.DataFrame
    rolling_df: pd.DataFrame
    ticker: str
    model: str


def run_single_attribution(
    ticker: str,
    model: str = "ff3",
    start: str = "2015-01-01",
    end: str = "2024-12-31",
    newey_west: bool = True,
    rolling_window: int = 36,
) -> AttributionResult:
    factors = fetch_factors(model)
    factors = factors[
        (factors.index >= pd.Timestamp(start)) & (factors.index <= pd.Timestamp(end))
    ]
    prices = fetch_monthly_prices(ticker, start=start, end=end)
    aligned = align_data(prices, factors)

    factor_cols = [c for c in aligned.columns if c != "excess_return"]
    y = aligned["excess_return"]
    X = aligned[factor_cols]
    ols_result = run_ols(y, X, newey_west=newey_west)

    if len(aligned) > rolling_window:
        rolling_df = rolling_regression(aligned, window=rolling_window, newey_west=newey_west)
    else:
        rolling_df = pd.DataFrame()

    return AttributionResult(
        ols=ols_result,
        aligned_df=aligned,
        rolling_df=rolling_df,
        ticker=ticker,
        model=model,
    )
