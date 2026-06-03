import pandas as pd


def compute_portfolio_returns(
    holdings: dict[str, tuple[pd.Series, float]]
) -> pd.Series:
    total_weight = sum(w for _, w in holdings.values())
    if abs(total_weight - 1.0) > 1e-6:
        raise ValueError(
            f"Portfolio weights must sum to 1.0, got {total_weight:.4f}. "
            "Adjust weights before computing portfolio returns."
        )

    aligned = pd.DataFrame({ticker: series for ticker, (series, _) in holdings.items()})
    aligned = aligned.dropna()

    portfolio = sum(
        aligned[ticker] * weight for ticker, (_, weight) in holdings.items()
    )
    return portfolio.rename("portfolio")
