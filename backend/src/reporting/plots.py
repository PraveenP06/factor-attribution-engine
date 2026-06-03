import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.models.ols import OLSResult
from src.reporting.tables import significance_stars

_DARK_BG = "#0f1117"
_PANEL_BG = "#1a1d2e"
_GRID = "#2a2d3e"
_TEXT = "#e2e8f0"
_ACCENT = "#6366f1"
_GREEN = "#22c55e"
_YELLOW = "#eab308"
_ORANGE = "#f97316"
_GREY = "#64748b"

_SIG_COLORS = {"***": _GREEN, "**": _YELLOW, "*": _ORANGE, "": _GREY}


def _base_layout(**kwargs) -> dict:
    return dict(
        paper_bgcolor=_DARK_BG,
        plot_bgcolor=_PANEL_BG,
        font=dict(color=_TEXT, family="JetBrains Mono, monospace"),
        margin=dict(l=40, r=20, t=40, b=40),
        **kwargs,
    )


def factor_loadings_chart(result: OLSResult) -> str:
    factors = list(result.betas.keys())
    betas = [result.betas[f] for f in factors]
    sigs = [significance_stars(result.pvalues[f]) for f in factors]
    colors = [_SIG_COLORS[s] for s in sigs]

    ci_low = [result.alpha_ci[0]] + [0.0] * (len(factors) - 1)
    ci_high = [result.alpha_ci[1]] + [0.0] * (len(factors) - 1)

    # For non-alpha factors, approximate CI from t-stat (±1.96 * se)
    for i, f in enumerate(factors):
        if f != "alpha":
            se = abs(betas[i] / result.tvalues[f]) if result.tvalues[f] != 0 else 0
            ci_low[i] = betas[i] - 1.96 * se
            ci_high[i] = betas[i] + 1.96 * se

    display_names = [f if f != "alpha" else "Alpha (α)" for f in factors]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=display_names,
            y=betas,
            marker_color=colors,
            error_y=dict(
                type="data",
                symmetric=False,
                array=[h - b for h, b in zip(ci_high, betas)],
                arrayminus=[b - l for b, l in zip(betas, ci_low)],
                color=_TEXT,
                thickness=1.5,
            ),
            hovertemplate="<b>%{x}</b><br>β = %{y:.3f}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_color=_GRID, line_width=1)
    fig.update_layout(
        **_base_layout(title="Factor Loadings"),
        xaxis=dict(showgrid=False, color=_TEXT),
        yaxis=dict(gridcolor=_GRID, color=_TEXT, title="Beta (β)"),
        showlegend=False,
    )
    return fig.to_json()


def rolling_beta_chart(rolling_df: pd.DataFrame, factors: list[str] | None = None) -> str:
    if rolling_df.empty:
        return json.dumps({})

    factor_cols = factors or [c for c in rolling_df.columns if c != "alpha"]
    colors = [_ACCENT, _GREEN, _YELLOW, _ORANGE, "#a78bfa", "#38bdf8"]

    fig = go.Figure()
    for i, col in enumerate(factor_cols):
        if col not in rolling_df.columns:
            continue
        color = colors[i % len(colors)]
        fig.add_trace(
            go.Scatter(
                x=rolling_df.index,
                y=rolling_df[col],
                mode="lines",
                name=col,
                line=dict(color=color, width=1.5),
                hovertemplate=f"<b>{col}</b><br>%{{x|%Y-%m}}<br>β = %{{y:.3f}}<extra></extra>",
            )
        )
    fig.add_hline(y=0, line_color=_GRID, line_width=1, line_dash="dot")
    fig.update_layout(
        **_base_layout(title="Rolling Factor Betas (36-month window)"),
        xaxis=dict(gridcolor=_GRID, color=_TEXT),
        yaxis=dict(gridcolor=_GRID, color=_TEXT, title="Beta (β)"),
        legend=dict(bgcolor=_PANEL_BG, bordercolor=_GRID),
    )
    return fig.to_json()


def actual_vs_predicted_chart(aligned_df: pd.DataFrame, result: OLSResult) -> str:
    y = aligned_df["excess_return"]
    factor_cols = [c for c in aligned_df.columns if c != "excess_return"]
    X = aligned_df[factor_cols]

    predicted = result.alpha + sum(result.betas[f] * X[f] for f in factor_cols)
    residual = y - predicted

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.05,
    )
    fig.add_trace(
        go.Scatter(x=y.index, y=y.values, name="Actual", mode="lines",
                   line=dict(color=_TEXT, width=1.5)),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=predicted.index, y=predicted.values, name="Factor-Predicted",
                   mode="lines", line=dict(color=_ACCENT, width=1.5, dash="dash")),
        row=1, col=1,
    )
    fig.add_trace(
        go.Bar(x=residual.index, y=residual.values, name="Residual (α + ε)",
               marker_color=_GREY),
        row=2, col=1,
    )
    fig.add_hline(y=0, line_color=_GRID, line_width=1, row=2, col=1)
    fig.update_layout(
        **_base_layout(title="Actual vs Factor-Predicted Excess Returns"),
        legend=dict(bgcolor=_PANEL_BG, bordercolor=_GRID),
    )
    fig.update_yaxes(gridcolor=_GRID, color=_TEXT)
    fig.update_xaxes(gridcolor=_GRID, color=_TEXT)
    return fig.to_json()
