# Factor Attribution Engine — CLAUDE.md

## What This Project Is

A Python Fama-French/Carhart factor attribution engine with a Next.js live dashboard.
It decomposes stock and portfolio returns into systematic factor exposures (MKT, SMB, HML,
MOM, RMW, CMA) plus unexplained alpha. The frontend is a Bloomberg-lite quant dashboard
deployed as a portfolio showcase.

**Monorepo layout:**
```
factor-attribution-engine/
├── backend/          Python: FastAPI + attribution engine
├── frontend/         Next.js 16 (App Router, TypeScript, Tailwind)
├── plans/            Implementation plans
├── graphify-out/     Graphify code graph (DO NOT edit manually)
└── CLAUDE.md         This file
```

---

## Navigating the Codebase — Use Graphify

**ALWAYS use graphify before manually reading files.** The code graph at
`graphify-out/graph.json` maps every file, function, and import relationship across the
whole monorepo. It is dramatically faster than grepping or reading files one by one.

Run all graphify commands from the **project root**
(`/Users/praveen/Desktop/factor-attribution-engine/`).

### Find what a file or function does

```bash
graphify explain "french"         # explains french.py and all its functions
graphify explain "run_ols"        # explains the OLS wrapper + its callers
graphify explain "analyze"        # explains the FastAPI route handler
graphify explain "InputPanel"     # explains the React input component
graphify explain "align_data"     # explains the date alignment function
```

### Trace how two things connect

```bash
graphify path "french.py" "analyze.py"        # french → fetch_factors → analyze()
graphify path "OLSResult" "RegressionTable"   # backend dataclass → frontend table
graphify path "align_data" "run_ols"          # data pipeline chain
```

### Rules for using graphify

- Use `graphify explain` BEFORE opening any file you haven't seen in this session
- Use `graphify path` to trace a call chain or data flow before editing anything in it
- Only read the actual file after graphify has confirmed what's in it and why you need it
- Never scan a directory with `find` or `ls` to figure out what files do — ask graphify

---

## Running the Project

### Backend

```bash
cd backend
uv venv .venv --python 3.11          # first time only
uv pip install -e ".[dev]"            # first time only
.venv/bin/uvicorn api.main:app --port 8000 --reload
```

API is live at `http://127.0.0.1:8000`. Docs at `http://127.0.0.1:8000/docs`.

### Frontend

```bash
cd frontend
npm install                            # first time only
cp .env.example .env.local             # first time only
npm run dev
```

App is live at `http://localhost:3000`.

### Run both together

```bash
# Terminal 1
cd backend && .venv/bin/uvicorn api.main:app --port 8000 --reload

# Terminal 2
cd frontend && npm run dev
```

---

## Backend Architecture

```
backend/
├── api/
│   ├── main.py              FastAPI app + CORS middleware
│   └── routes/
│       └── analyze.py       POST /api/analyze  GET /api/health
├── src/
│   ├── data/
│   │   ├── french.py        Download + parse Kenneth French factor data
│   │   ├── prices.py        yfinance monthly prices + simple returns
│   │   └── align.py         Date alignment (month-end normalization)
│   ├── models/
│   │   ├── ols.py           statsmodels OLS wrapper (returns OLSResult dataclass)
│   │   └── rolling.py       Rolling-window regression
│   ├── attribution/
│   │   ├── single.py        Single-ticker attribution orchestrator
│   │   └── portfolio.py     Weighted portfolio returns
│   └── reporting/
│       ├── tables.py        significance_stars(), build_verdict()
│       └── plots.py         Plotly JSON for 3 charts
├── tests/                   pytest, 65 tests, 82% coverage
├── data/
│   ├── raw/                 Cached parquet from French's library (gitignored)
│   └── cache/               (gitignored)
├── pyproject.toml
└── Dockerfile
```

### Data flow

```
Kenneth French Data Library (HTTP)
    └─→ french.py (_load_raw → parquet cache)
            └─→ fetch_factors(model)
                    └─→ align.py (align_data)
                            ↑
                    prices.py (fetch_monthly_prices → yfinance)

align_data → OLSResult (ols.py)
          → rolling_df (rolling.py)
          → AttributionResult (single.py / portfolio.py)
                  └─→ plots.py (3 Plotly JSON charts)
                  └─→ tables.py (build_verdict)
                          └─→ api/routes/analyze.py (JSON response)
```

### Key types

```python
# backend/src/models/ols.py
@dataclass
class OLSResult:
    alpha: float
    betas: dict[str, float]        # {"MKT": 1.21, "SMB": -0.12, ...}
    tvalues: dict[str, float]      # includes "alpha" key
    pvalues: dict[str, float]      # includes "alpha" key
    r2: float
    adj_r2: float
    nobs: int
    alpha_ci: tuple[float, float]  # 95% CI for alpha
    se_type: str                   # "HAC" or "OLS"
    date_range: tuple[str, str]    # ("2015-01", "2024-12")
```

---

## Frontend Architecture

```
frontend/
├── app/
│   ├── layout.tsx                   Root layout (Geist Mono, dark bg)
│   ├── page.tsx                     Portfolio landing page (/)
│   └── factor-attribution/
│       └── page.tsx                 Quant dashboard (/factor-attribution)
├── components/
│   └── factor-app/
│       ├── InputPanel.tsx           Ticker + model + date range + SE toggle
│       ├── ResultsPanel.tsx         Composes table + verdict + 3 charts
│       ├── RegressionTable.tsx      Coefficient table with t-stats + sig stars
│       ├── AlphaVerdict.tsx         Plain-English verdict + CI card
│       └── PlotlyChart.tsx          react-plotly.js wrapper (SSR-disabled)
└── lib/
    ├── types.ts                     Shared request/response types
    └── api.ts                       analyze() + healthCheck() fetch wrappers
```

### API contract

```typescript
// POST /api/analyze
type AnalyzeRequest = {
  mode: "single" | "portfolio";
  tickers: string[] | WeightedTicker[];
  model: "ff3" | "ff4" | "ff5";
  start: string;       // "YYYY-MM"
  end: string;         // "YYYY-MM"
  newey_west: boolean;
};

type AnalyzeResponse = {
  ticker: string;
  model: string;
  n_obs: number;
  r2: number;
  adj_r2: number;
  se_type: "HAC" | "OLS";
  coefficients: Coefficient[];   // Alpha first, then factors
  alpha_ci: [number, number];
  verdict: string;               // plain-English interpretation
  rolling_betas: RollingBetas;
  factor_loadings_chart: object; // Plotly figure JSON
  rolling_beta_chart: object;
  actual_vs_predicted_chart: object;
};
```

Charts are Plotly figure objects serialized to JSON by the Python backend and rendered via
`react-plotly.js` in the frontend. No chart logic lives in TypeScript.

### Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | Backend URL (default: `http://localhost:8000`) |

---

## Testing

### Backend

```bash
cd backend

# Run all tests (no network)
.venv/bin/python -m pytest tests/ -q

# Run with coverage report
.venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing

# Run only network-free tests explicitly
.venv/bin/python -m pytest tests/ -m "not network"

# Run a single test file
.venv/bin/python -m pytest tests/test_ols.py -v
```

Coverage gate is 80% (`pyproject.toml`: `--cov-fail-under=80`).

Network tests (hitting yfinance + French library) are marked `@pytest.mark.network` and
skipped by default in CI. Use synthetic fixtures in `tests/conftest.py` for all unit tests.

### Frontend

```bash
cd frontend
npx tsc --noEmit      # type check
npm run build          # full build check
```

---

## Critical Gotchas

### 1. pandas-datareader is broken — use direct HTTP
`pandas-datareader` fails to import with pandas 2.x due to a `deprecate_kwarg` signature
change. The project uses direct HTTP download from Kenneth French's Data Library via
`requests` + `zipfile`. Never add `pandas-datareader` back.

See: `backend/src/data/french.py:_download_zip()` and `_parse_french_csv()`

### 2. statsmodels: use `fit(cov_type='HAC')`, not `get_robustcov_results()`
`result.get_robustcov_results(cov_type='HAC')` drops named index from `params` — you get
a bare numpy array and string key lookups fail with `IndexError`. Always use:
```python
fit = sm.OLS(y, X_const).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
```
See: `backend/src/models/ols.py:run_ols()`

### 3. Date alignment: pandas 2.x won't set datetime into int64 column
You cannot do `df.iloc[:, 0] = pd.to_datetime(...)` on a DataFrame with an int64 column
in pandas 2.x (`LossySetitemError`). Build the DatetimeIndex separately and assign to
`df.index`:
```python
dates = pd.to_datetime(raw.iloc[:, 0].astype(int).astype(str), format="%Y%m")
df = raw.iloc[:, 1:].copy()
df.index = dates
```
See: `backend/src/data/french.py:_to_date_index()`

### 4. pyarrow required for parquet caching
Add `pyarrow>=15.0` to dependencies. Without it, `pd.DataFrame.to_parquet()` raises
`"Unable to find a usable engine"`. It's in `pyproject.toml`.

### 5. Rolling regression uses Newey-West HAC by default
Default `newey_west=True` in both `run_ols()` and `rolling_regression()`. Vanilla OLS
standard errors overstate significance for financial time series with autocorrelated
residuals. Never default to `newey_west=False` without a reason.

### 6. French data: month-end normalization
French uses last-trading-day-of-month dates; yfinance uses a different convention.
Both are normalized to month-end via `to_period("M").to_timestamp("M")` before joining.
See: `backend/src/data/align.py:compute_excess_returns()`

### 7. PlotlyChart is SSR-disabled
`react-plotly.js` cannot run server-side. It's wrapped with `dynamic(..., { ssr: false })`.
Never import `react-plotly.js` directly in a server component.
See: `frontend/components/factor-app/PlotlyChart.tsx`

---

## Making Changes

### Editing the OLS model
Run `graphify explain "run_ols"` first to see all callers before touching the function
signature or `OLSResult` fields. Changes to `OLSResult` cascade to `single.py`,
`portfolio.py`, `analyze.py`, and the `AnalyzeResponse` type in `frontend/lib/types.ts`.

### Adding a new factor model
1. Add a `fetch_ffX()` function in `backend/src/data/french.py`
2. Add the model key to `fetch_factors()` dispatcher
3. Add `"ffX"` to the `validate_model` validator in `backend/api/routes/analyze.py`
4. Add `"ffX"` to `ModelType` in `frontend/lib/types.ts`
5. Add the option to `MODELS` array in `frontend/components/factor-app/InputPanel.tsx`

Use `graphify path "french.py" "InputPanel"` to verify the chain before editing.

### Adding a new API field
1. Add to the `return` dict in `backend/api/routes/analyze.py`
2. Add to `AnalyzeResponse` in `frontend/lib/types.ts`
3. Consume in the appropriate component under `frontend/components/factor-app/`

Use `graphify path "analyze" "ResultsPanel"` to see the full data flow.

### Adding a new chart
1. Add a new chart function to `backend/src/reporting/plots.py` returning `fig.to_json()`
2. Add the chart to the `return` dict in `backend/api/routes/analyze.py`
3. Add the field to `AnalyzeResponse` in `frontend/lib/types.ts`
4. Add a `<PlotlyChart figure={result.new_chart} />` in `ResultsPanel.tsx`

---

## Deployment

### Backend → Railway
1. Push to GitHub
2. New Railway project → connect GitHub → root directory: `backend/`
3. Environment variables: `PYTHONPATH=.`, `PORT=8000`
4. Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Verify: `curl https://<railway-url>/api/health` → `{"status":"ok"}`

### Frontend → Vercel
1. New Vercel project → connect GitHub → root directory: `frontend/`
2. Environment variables: `NEXT_PUBLIC_API_URL=https://<railway-url>`
3. Framework preset: Next.js (auto-detected)
4. Verify: `/factor-attribution` loads and can run a live AAPL analysis

### CORS
`backend/api/main.py` currently allows all origins (`allow_origins=["*"]`). Before
deploying, lock this to the Vercel domain:
```python
allow_origins=["https://your-app.vercel.app"]
```

---

## Verification Checklist

```
[ ] cd backend && .venv/bin/python -m pytest tests/ -q          # 65 pass, 82%+ coverage
[ ] .venv/bin/uvicorn api.main:app --port 8000                  # server starts
[ ] curl http://127.0.0.1:8000/api/health                       # {"status":"ok"}
[ ] POST /api/analyze AAPL FF3 → n_obs>0, MKT t-stat>5         # live data works
[ ] cd frontend && npx tsc --noEmit                             # zero type errors
[ ] npm run build                                               # clean production build
[ ] localhost:3000 renders portfolio landing page               # UI works
[ ] localhost:3000/factor-attribution submits AAPL → results   # end-to-end works
```
