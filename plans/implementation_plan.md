# Implementation Plan: Factor Attribution Engine

## What We're Building

A Python research tool that decomposes stock and portfolio historical returns into systematic
factor exposures (market beta, size, value, momentum, profitability, investment) plus an
unexplained residual (alpha). The core question it answers: "Did this asset go up because it's
genuinely good, or because it's riding a factor tilt?"

Deliverable: a clean CLI tool + Jupyter notebooks. No UI, no database, no trading system.
The intellectual weight is in the econometrics, not the tooling.

---

## Full Feature Set by Milestone

### Milestone 1 — Single-Stock Attribution (FF3)
- Fetch monthly factor returns from Kenneth French's Data Library (MKT, SMB, HML, RF)
- Fetch monthly adjusted close prices via yfinance
- Align dates correctly across two sources with different calendar conventions
- Compute excess returns: R_i - RF
- Run OLS regression via statsmodels
- Output: factor betas, alpha, t-statistics, p-values, R², adjusted R², N, date range
- Interpret output in plain English (e.g. "market beta 1.2, significant at 1%; alpha 0.1%/mo, NOT significant")
- CLI entry point: `python -m src.cli --ticker AAPL`

### Milestone 2 — Statistical Rigor + Rolling Betas
- Newey-West HAC standard errors (corrects for heteroskedasticity and autocorrelation)
- Toggle between vanilla OLS SE and Newey-West SE to show the difference
- Rolling-window regression (default 36-month window): betas at each window endpoint
- Plot: market beta drift over time as a time series
- Multi-ticker support: run attribution on a list of stocks in one call
- Portfolio weighted returns: compute portfolio-level returns from tickers + weights

### Milestone 3 — Portfolio Attribution + Visualization
- Portfolio-level factor attribution (weighted sum of individual returns → one regression)
- Factor loadings bar chart (per factor: alpha, MKT, SMB, HML, MOM)
- Rolling beta time series plot (all factors, configurable window)
- Actual vs. factor-predicted returns overlay chart
- Alpha confidence interval at portfolio level
- Summary narrative: "Your 'alpha' is statistically zero; 90% of variation is explained by a
  small-cap value tilt."

### Milestone 4 (stretch) — FF5 + Regression Diagnostics
- Carhart 4-factor model (FF3 + MOM)
- Fama-French 5-factor model (FF3 + RMW + CMA)
- Breusch-Pagan test for heteroskedasticity
- Durbin-Watson statistic for autocorrelation
- Residual plots
- Model comparison table: FF3 vs FF4 vs FF5 — adjusted R², AIC, BIC
- Warn when adding factors inflates R² without improving adjusted R²

---

## Stack

| Layer              | Tool                        | Rationale                                                              |
|--------------------|-----------------------------|------------------------------------------------------------------------|
| Language           | Python 3.11+                | Ecosystem fit; pandas/statsmodels are first-class                     |
| Data wrangling     | pandas 2.x                  | Core; date alignment logic lives here                                  |
| OLS regression     | statsmodels 0.14+           | t-stats, p-values, R², CIs, HAC — sklearn cannot do this              |
| Asset prices       | yfinance 0.2+               | Free, reliable enough for monthly research                             |
| Factor data        | pandas-datareader 0.10+     | Direct accessor to Kenneth French's library                            |
| Visualization      | matplotlib + plotly          | matplotlib for static exports; plotly for interactive notebook charts  |
| Testing            | pytest + pytest-cov         | 80% coverage gate enforced in CI                                       |
| Dependency mgmt    | uv                          | Fast, reproducible; replaces pip+venv                                  |
| Notebooks          | Jupyter                     | One notebook per milestone as the walkthrough deliverable              |
| Linting/format     | ruff                        | Fast; replaces flake8 + black + isort                                  |

---

## Project Structure

```
factor-attribution-engine/
├── plans/
│   └── implementation_plan.md      # This file
├── data/
│   ├── raw/                        # Downloaded CSVs from French's library (gitignored)
│   └── cache/                      # Aligned DataFrames cached as parquet (gitignored)
├── src/
│   ├── __init__.py
│   ├── cli.py                      # CLI entry point
│   ├── data/
│   │   ├── __init__.py
│   │   ├── french.py               # Fetch + parse Kenneth French factor data
│   │   ├── prices.py               # Fetch asset prices via yfinance
│   │   └── align.py                # Date alignment logic
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ols.py                  # OLS regression wrapper (statsmodels)
│   │   ├── rolling.py              # Rolling-window regression
│   │   └── diagnostics.py         # BP test, DW stat, Newey-West, residuals
│   ├── attribution/
│   │   ├── __init__.py
│   │   ├── single.py               # Single-asset attribution orchestrator
│   │   ├── portfolio.py            # Portfolio weighted attribution
│   │   └── compare.py             # Model comparison (FF3 vs FF4 vs FF5)
│   └── reporting/
│       ├── __init__.py
│       ├── tables.py               # Formatted coefficient tables + narrative
│       └── plots.py                # All visualization functions
├── notebooks/
│   ├── 01_single_stock.ipynb       # M1 walkthrough: AAPL FF3
│   ├── 02_rolling_betas.ipynb      # M2 walkthrough: rolling betas, Newey-West
│   ├── 03_portfolio.ipynb          # M3 walkthrough: portfolio attribution + viz
│   └── 04_diagnostics.ipynb        # M4 walkthrough: FF5, BP, DW, model comparison
├── tests/
│   ├── conftest.py                 # Shared fixtures (sample factor data, price series)
│   ├── test_french.py
│   ├── test_prices.py
│   ├── test_align.py
│   ├── test_ols.py
│   ├── test_rolling.py
│   ├── test_portfolio.py
│   ├── test_diagnostics.py
│   └── test_compare.py
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

---

## Milestone 1 — Detailed Steps

### Step 1.1: Project scaffolding
- `pyproject.toml` with all dependencies (uv)
- `src/` package with `__init__.py` files
- `pytest.ini` or `[tool.pytest.ini_options]` with `--cov=src --cov-fail-under=80`
- `.gitignore`: `data/raw/`, `data/cache/`, `.env`, `__pycache__/`, `.pytest_cache/`
- `ruff.toml` for linting config

### Step 1.2: French data fetcher (`src/data/french.py`)
- Download FF3 monthly dataset: `F-F_Research_Data_Factors` via `pandas_datareader.famafrench`
- Cache to `data/raw/ff3_monthly.parquet` on first run; read from cache on subsequent runs
- Parse: divide by 100 (French reports in percent), rename to `MKT`, `SMB`, `HML`, `RF`
- Return `pd.DataFrame` with `DatetimeIndex` at month-end frequency (`ME`)
- Validate: assert columns present, assert values between -0.5 and +0.5 (sanity check)

### Step 1.3: Price fetcher (`src/data/prices.py`)
- Fetch monthly adjusted close prices via `yfinance.download(ticker, interval='1mo')`
- Compute simple monthly returns: `(P_t - P_{t-1}) / P_{t-1}` (match French's convention)
- Return `pd.Series` with `DatetimeIndex`, name = ticker symbol

### Step 1.4: Date alignment (`src/data/align.py`) — the hard part
- Problem: French uses last trading day of month; Yahoo may use different day
- Strategy: normalize both indexes to month-end (`pd.DateOffset` + `to_period('M')`)
- Compute excess returns: `r_excess = r_asset - rf`
- Inner join on overlapping date range
- Drop any NaN rows
- Validate: assert zero NaN rows, assert at least 24 months of data, assert date range sane
- Return: `pd.DataFrame` with columns `[excess_return, MKT, SMB, HML]`

### Step 1.5: OLS wrapper (`src/models/ols.py`)
- Accept `y: pd.Series`, `X: pd.DataFrame` (factors, no constant)
- Add constant via `sm.add_constant(X)`
- Fit `sm.OLS(y, X_with_const).fit()`
- Return typed dataclass: `OLSResult(alpha, betas, tvalues, pvalues, r2, adj_r2, nobs, conf_int)`

### Step 1.6: Single-asset attribution (`src/attribution/single.py`)
- Orchestrate: fetch prices → fetch factors → align → run OLS
- Accept: `ticker: str`, `model: str = 'ff3'`, `start: str`, `end: str`
- Return `AttributionResult` with all OLSResult fields + metadata

### Step 1.7: Reporting table (`src/reporting/tables.py`)
- Print formatted table: `Coefficient | Estimate | Std Error | t-stat | p-value | Sig`
- Significance stars: *** p<0.01, ** p<0.05, * p<0.10
- Print summary block: R², adj R², N observations, date range
- Print narrative: one sentence per coefficient interpreting significance and direction

### Step 1.8: CLI (`src/cli.py`)
- `--ticker` (required)
- `--model` (ff3/ff4/ff5, default ff3)
- `--start` / `--end` (YYYY-MM format)
- `--window` (rolling window size, default 36)
- `--newey-west` flag (toggle HAC SEs)

### Step 1.9: Tests for M1
- `test_french.py`: correct columns, dtype float, values in [-0.5, 0.5], index is DatetimeIndex
- `test_prices.py`: returns are simple (not log), no NaN in output
- `test_align.py`: no NaN after alignment, inner join preserves correct date range, excess returns = r - rf
- `test_ols.py`: R² in [0,1], tvalues finite, known AAPL beta in plausible range (0.8–1.5)
- Use synthetic fixtures in `conftest.py` — don't hit the network in unit tests

---

## Milestone 2 — Detailed Steps

### Step 2.1: Newey-West HAC standard errors (`src/models/ols.py`)
- Add `cov_type` parameter to OLS wrapper: `'HC3'` (robust) or `'HAC'` (Newey-West)
- Default to `'HAC'` with `maxlags=int(nobs^(1/4))` (standard rule of thumb)
- Refit using `result.get_robustcov_results(cov_type='HAC', maxlags=lags)`
- Update `OLSResult` to carry `se_type: str` field

### Step 2.2: Rolling regression (`src/models/rolling.py`)
- Accept `aligned_df: pd.DataFrame`, `window: int = 36`, `factor_cols: list[str]`
- Slide window: for each endpoint from `window` to `len(df)`, slice and fit OLS
- Store per window: date, alpha, per-factor beta, t-stat, R²
- Return `pd.DataFrame` indexed by window end date

### Step 2.3: Multi-ticker support (`src/attribution/single.py`)
- Accept `tickers: list[str]` in addition to single `ticker: str`
- Return `dict[str, AttributionResult]`

### Step 2.4: Portfolio returns (`src/attribution/portfolio.py`)
- Accept `portfolio: dict[str, float]` (ticker → weight, weights must sum to 1.0)
- Fetch all tickers, align individually, then compute weighted sum of excess returns
- Feed weighted portfolio returns into OLS as the `y` series
- Return `AttributionResult` with `ticker = 'PORTFOLIO'`

### Step 2.5: Rolling beta plot (`src/reporting/plots.py`)
- `plot_rolling_betas(rolling_df, factor='MKT')` → matplotlib figure
- Show 95% confidence band if t-stats available
- Add horizontal line at 0 for reference

### Step 2.6: Tests for M2
- `test_rolling.py`: rolling df has correct length `(N - window + 1)`, all betas finite
- `test_portfolio.py`: weighted returns computed correctly (use known weights + returns), weights != 1.0 raises ValueError
- `test_ols.py`: HAC SEs differ from vanilla SEs on autocorrelated synthetic data (directional test)

---

## Milestone 3 — Detailed Steps

### Step 3.1: Portfolio-level attribution report (`src/reporting/tables.py`)
- `print_portfolio_report(result: AttributionResult)` → full narrative
- Include alpha confidence interval: `[alpha_lower, alpha_upper]` at 95%
- Print plain-English verdict: "Alpha is statistically zero. Primary exposures: MKT (β=1.1***), SMB (β=0.4**)"

### Step 3.2: Factor loadings bar chart (`src/reporting/plots.py`)
- `plot_factor_loadings(result: AttributionResult)` → bar chart
- Bars colored by significance: green = significant, grey = not significant
- Error bars from confidence intervals

### Step 3.3: Actual vs predicted returns chart (`src/reporting/plots.py`)
- `plot_actual_vs_predicted(result: AttributionResult, aligned_df: pd.DataFrame)`
- Overlay: actual excess returns (line), factor-predicted returns (dashed line)
- Bottom panel: residuals (alpha + epsilon)

### Step 3.4: Notebook 03 (`notebooks/03_portfolio.ipynb`)
- Example portfolio: 40% AAPL, 30% MSFT, 20% TSLA, 10% BRK-B
- Run attribution, show all three charts, write interpretation paragraph

### Step 3.5: Tests for M3
- `test_portfolio.py`: alpha CI contains 0 for diversified portfolio (statistical sanity check using synthetic data)
- Plotting functions return `matplotlib.figure.Figure` without error (smoke tests)

---

## Milestone 4 — Detailed Steps (stretch)

### Step 4.1: FF4 (Carhart) and FF5 data (`src/data/french.py`)
- Add `fetch_ff4_monthly()`: FF3 + MOM (`F-F_Momentum_Factor`)
- Add `fetch_ff5_monthly()`: `F-F_Research_Data_5_Factors_2x3`
- Unify under `fetch_factors(model: str)` dispatcher

### Step 4.2: Model comparison (`src/attribution/compare.py`)
- Run FF3, FF4, FF5 on same asset/portfolio
- Return comparison table: model | adj R² | AIC | BIC | alpha | alpha t-stat
- Warn if FF5 adj R² < FF4 adj R² (overfitting signal)

### Step 4.3: Regression diagnostics (`src/models/diagnostics.py`)
- Breusch-Pagan test: `statsmodels.stats.diagnostic.het_breuschpagan`
- Durbin-Watson: `statsmodels.stats.stattools.durbin_watson`
- Residual plot: histogram + Q-Q plot
- Print diagnostic summary: pass/fail per test with interpretation

### Step 4.4: Notebook 04 (`notebooks/04_diagnostics.ipynb`)
- Show vanilla OLS vs Newey-West SE comparison on same regression
- Show BP and DW results and what they imply for inference validity
- Show model comparison table: FF3 vs FF4 vs FF5

### Step 4.5: Tests for M4
- `test_diagnostics.py`: BP test returns (statistic, p-value) tuple, DW in [0,4]
- `test_compare.py`: comparison table has correct columns, adj R² ordering is valid

---

## Data Flow

```
Kenneth French Data Library
        │
        ▼
src/data/french.py  →  data/raw/ff3_monthly.parquet (cached)
        │
        ▼
src/data/align.py  ←──  src/data/prices.py  ←── yfinance
        │
        ▼ (aligned DataFrame: date × [excess_return, MKT, SMB, HML])
src/models/ols.py
        │
        ├── src/models/rolling.py  (rolling window)
        └── src/models/diagnostics.py  (BP, DW, residuals)
        │
        ▼
src/attribution/single.py  or  src/attribution/portfolio.py
        │
        ▼
src/reporting/tables.py  +  src/reporting/plots.py
        │
        ▼
CLI output  or  Jupyter notebook
```

---

## Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Date alignment bugs (French vs Yahoo calendar mismatch) | HIGH | Validate explicitly: assert no NaN, assert N > 24, use period-based join |
| yfinance API changes / rate limits | MEDIUM | Cache raw downloads; add retry logic; test with fixtures so tests don't hit network |
| French library dataset naming changes | MEDIUM | Pin pandas-datareader version; store raw CSV fallback in `data/raw/` |
| Overclaiming alpha (sign of a bug) | HIGH | Treat any significant alpha as a bug first; add sanity checks against known published results |
| OLS assumptions violated without correction | HIGH | Default to Newey-West; always report which SE type was used |
| Rolling window edge cases (window > N) | MEDIUM | Validate window < N - 1 before running; raise ValueError with helpful message |
| Monthly return convention mismatch (log vs simple) | MEDIUM | Use simple returns throughout; document explicitly; add assertion that returns are in (-1, +∞) |

---

## Rigor Checklist (what separates this from a toy)

- [ ] Report t-statistics alongside every point estimate — a beta without a t-stat is noise
- [ ] Default to Newey-West SE — vanilla OLS SE on financial returns overstates significance
- [ ] Report adjusted R², not R² — adding factors always increases R²; adj R² penalizes overfitting
- [ ] Alpha CI explicitly includes 0 for liquid assets — if it doesn't, check for a bug first
- [ ] Rolling betas show non-stationarity — prove the "constant beta" assumption is false
- [ ] Model comparison uses BIC in addition to adj R² — BIC penalizes complexity more harshly

---

## Testing Strategy

- **Unit tests**: synthetic fixtures in `conftest.py` — never hit the network
- **Integration smoke test**: one test that fetches real AAPL data (marked `@pytest.mark.network`, skipped in CI)
- **Coverage gate**: 80% minimum enforced via `pytest-cov`
- **TDD workflow**: write the test → see it fail → write minimal implementation → see it pass → refactor

---

## Timeline

### Week 1 (M1 complete)
| Day | Task |
|-----|------|
| Day 1 | Scaffolding: pyproject.toml, uv, ruff, pytest, directory structure, .gitignore |
| Day 2 | `french.py` + `test_french.py` (TDD) — fetch, cache, parse FF3 data |
| Day 3 | `prices.py` + `test_prices.py` (TDD) — yfinance fetch, simple returns |
| Day 4 | `align.py` + `test_align.py` (TDD) — date alignment (expect this to take all day) |
| Day 5 | `ols.py` + `test_ols.py` (TDD) — OLS wrapper with statsmodels |
| Day 6 | `single.py` + `tables.py` + `cli.py` — orchestration + output |
| Day 7 | Notebook 01: AAPL end-to-end walkthrough + interpretation paragraph |

**M1 gate**: `python -m src.cli --ticker AAPL` prints a fully interpretable regression table.

---

### Week 2 (M2 complete)
| Day | Task |
|-----|------|
| Day 8 | Newey-West HAC SEs in `ols.py` + update tests |
| Day 9 | `rolling.py` + `test_rolling.py` (TDD) |
| Day 10 | Rolling beta plot in `plots.py` |
| Day 11 | Multi-ticker support + portfolio weighted returns in `portfolio.py` |
| Day 12 | `test_portfolio.py` (TDD) |
| Day 13 | Notebook 02: rolling betas on AAPL showing beta drift over time |
| Day 14 | Buffer: catch up on anything that ran long; refactor align.py if brittle |

**M2 gate**: Plot shows AAPL market beta changing across 36-month windows.

---

### Week 3 (M3 complete)
| Day | Task |
|-----|------|
| Day 15 | Portfolio attribution orchestration + `test_portfolio.py` updates |
| Day 16 | Factor loadings bar chart in `plots.py` |
| Day 17 | Actual vs predicted returns overlay chart |
| Day 18 | Portfolio-level narrative report in `tables.py` |
| Day 19 | Notebook 03: example portfolio walkthrough |
| Day 20 | End-to-end CLI polish: `--model`, `--window`, `--newey-west` flags working |
| Day 21 | Buffer: cross-check results against published FF factor research |

**M3 gate**: Hand a portfolio dict to CLI and get charts + "your alpha is statistically zero" verdict.

---

### Week 4 (M4 stretch)
| Day | Task |
|-----|------|
| Day 22 | FF4 + FF5 data fetching in `french.py` |
| Day 23 | `diagnostics.py` + `test_diagnostics.py` (BP, DW, residuals) |
| Day 24 | `compare.py` + `test_compare.py` — model comparison table |
| Day 25 | Notebook 04: diagnostics + model comparison walkthrough |
| Day 26 | README: setup instructions, usage examples, interpretation guide |
| Day 27 | Final coverage check; fill gaps to hit 80% |
| Day 28 | Polish: consistent error messages, helpful CLI --help text, review all narratives |

**M4 gate**: Can demonstrate that vanilla OLS SEs overstate significance relative to Newey-West on real data.

---

## Total Estimate: 4 weeks (28 working days across evenings)

This is achievable in 2-3 weeks if you can do full days on weekends. The original estimate of
"a weekend for M1" assumes the date alignment takes longer than expected, which it will.
Budget M1 for 5-7 days total and you'll have more margin for M2-M4.

The stretch (M4) is genuinely open-ended — the econometrics rabbit hole goes as deep as you want.
Ship M3 as v1.0 and treat M4 as the never-ending improvement track.

---

**WAITING FOR CONFIRMATION**: Does this plan match your vision? Reply yes/proceed to begin
implementation with M1, or reply with modifications.
