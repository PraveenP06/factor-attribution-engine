export type ModelType = "ff3" | "ff4" | "ff5";
export type SeType = "HAC" | "OLS";

export type SingleTicker = string;
export type WeightedTicker = { ticker: string; weight: number };

export type AnalyzeRequest = {
  mode: "single" | "portfolio";
  tickers: SingleTicker[] | WeightedTicker[];
  model: ModelType;
  start: string;
  end: string;
  newey_west: boolean;
};

export type Coefficient = {
  name: string;
  beta: number;
  tstat: number;
  pvalue: number;
  sig: "" | "*" | "**" | "***";
};

export type RollingBetas = {
  dates: string[];
  MKT?: number[];
  SMB?: number[];
  HML?: number[];
  MOM?: number[];
  RMW?: number[];
  CMA?: number[];
};

export type AnalyzeResponse = {
  ticker: string;
  model: ModelType;
  date_range: { start: string; end: string };
  n_obs: number;
  r2: number;
  adj_r2: number;
  se_type: SeType;
  coefficients: Coefficient[];
  alpha_ci: [number, number];
  verdict: string;
  rolling_betas: RollingBetas;
  factor_loadings_chart: object;
  rolling_beta_chart: object;
  actual_vs_predicted_chart: object;
};

export type ApiError = {
  detail: string;
};
