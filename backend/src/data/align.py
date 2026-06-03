import pandas as pd
from src.data.prices import compute_simple_returns

MIN_OBSERVATIONS = 24


def compute_excess_returns(prices: pd.Series, factors: pd.DataFrame) -> pd.DataFrame:
    returns = compute_simple_returns(prices)
    returns.index = returns.index.to_period("M").to_timestamp("M")
    factors_aligned = factors.copy()
    factors_aligned.index = factors_aligned.index.to_period("M").to_timestamp("M")
    combined = factors_aligned.join(returns.rename("asset_return"), how="inner")
    combined["excess_return"] = combined["asset_return"] - combined["RF"]
    return combined.drop(columns=["asset_return"])


def align_data(prices: pd.Series, factors: pd.DataFrame) -> pd.DataFrame:
    result = compute_excess_returns(prices, factors)
    result = result.dropna()
    if len(result) < MIN_OBSERVATIONS:
        raise ValueError(
            f"Only {len(result)} overlapping observations after alignment. "
            f"Need at least {MIN_OBSERVATIONS}. Expand the date range."
        )
    factor_cols = [c for c in factors.columns if c != "RF"]
    return result[["excess_return"] + factor_cols]
