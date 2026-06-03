import pandas as pd
from src.models.ols import run_ols


def rolling_regression(
    aligned_df: pd.DataFrame, window: int = 36, newey_west: bool = True
) -> pd.DataFrame:
    n = len(aligned_df)
    if window >= n:
        raise ValueError(
            f"window={window} must be less than the number of observations ({n})."
        )

    factor_cols = [c for c in aligned_df.columns if c != "excess_return"]
    records = []

    for end in range(window, n + 1):
        slice_df = aligned_df.iloc[end - window : end]
        y = slice_df["excess_return"]
        X = slice_df[factor_cols]
        result = run_ols(y, X, newey_west=newey_west)
        row = {"alpha": result.alpha, **result.betas}
        records.append(row)

    index = aligned_df.index[window - 1 :]
    return pd.DataFrame(records, index=index)
