import pandas as pd
import yfinance as yf


def fetch_monthly_prices(ticker: str, start: str, end: str) -> pd.Series:
    raw = yf.download(ticker, start=start, end=end, interval="1mo",
                      auto_adjust=True, progress=False)
    if raw.empty:
        raise ValueError(f"No price data found for ticker '{ticker}'. Check the symbol.")
    close = raw["Close"].squeeze()
    close.index = close.index.to_period("M").to_timestamp("M")
    close.name = ticker
    return close


def compute_simple_returns(prices: pd.Series) -> pd.Series:
    returns = prices.pct_change().dropna()
    assert (returns > -1).all(), "Returns contain values <= -100%, check price data."
    return returns
