from src.models.ols import OLSResult


def significance_stars(pvalue: float) -> str:
    if pvalue < 0.01:
        return "***"
    if pvalue < 0.05:
        return "**"
    if pvalue < 0.10:
        return "*"
    return ""


def build_verdict(result: OLSResult) -> str:
    alpha_sig = result.pvalues["alpha"] < 0.05
    r2_pct = round(result.adj_r2 * 100)
    n_factors = len(result.betas)

    if alpha_sig:
        alpha_line = (
            f"Alpha is statistically significant ({result.alpha * 100:.2f}%/month, "
            f"t={result.tvalues['alpha']:.2f}, p={result.pvalues['alpha']:.3f}). "
            "Verify carefully — significant alpha in liquid assets usually indicates a data issue."
        )
    else:
        alpha_line = (
            f"Alpha is statistically indistinguishable from zero "
            f"(t={result.tvalues['alpha']:.2f}, p={result.pvalues['alpha']:.2f})."
        )

    # Primary factor: largest absolute t-stat among betas
    primary = max(result.tvalues, key=lambda k: abs(result.tvalues[k]) if k != "alpha" else 0)
    primary_beta = result.betas[primary]
    primary_t = result.tvalues[primary]

    model_line = (
        f"{r2_pct}% of monthly return variation is explained by {n_factors} systematic factors "
        f"(adj. R²={result.adj_r2:.2f}). "
        f"Primary driver: {primary} β={primary_beta:.2f} (t={primary_t:.1f})."
    )

    return f"{alpha_line} {model_line}"
