r"""
Log-normal distribution fit to Czech wage and pension data.

Fits log-normal distributions to:
  * Wages:   ISPV 2024 H2 percentile distribution of gross monthly wages
  * Pensions: ČSSZ 2023 percentile distribution of old-age pensions

Methodology:
  Given empirical percentiles (p, x_p), the log-normal parameters are
  estimated by ordinary least squares on the probit (inverse-normal) scale:
    Φ⁻¹(p) = (ln x_p − μ) / σ
  The system is over-determined for ≥ 3 percentiles and solved via lstsq.

Data sources:
  Wages:   ISPV (MPSV) – Informační systém o průměrném výdělku, pololetí 2/2024
           Fallback percentiles used when data download is unavailable.
  Pensions: ČSSZ – výroční zpráva 2023, statistická příloha
            Fallback percentiles used when data download is unavailable.

Figures
-------
  ``wage_pension_distribution`` – overlapping density curves with annotations

Output
------
  pics/python/wage_pension_distribution.pdf
  latex/texparts/python/wage_pension_distribution.tex

Run
---
    python analyses/wage_pension_distribution.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from scipy import stats

from config import FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.style import apply_style, cm2in, savefig, save_figure_tex

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

apply_style()

# ── Fallback empirical percentiles ───────────────────────────────────────────
# ISPV 2024 H2 – hrubá měsíční mzda zaměstnanců (Kč/month)
FALLBACK_WAGE_PERCENTILES: dict[int, float] = {
    10: 20_700,
    25: 28_600,
    50: 40_709,
    75: 59_900,
    90: 89_900,
}

# ČSSZ 2023 – starobní důchody (Kč/month)
FALLBACK_PENSION_PERCENTILES: dict[int, float] = {
    25: 14_500,
    50: 19_800,
    75: 26_400,
}

MIN_WAGE:    float = 20_800   # Kč/month (2026, NV č. 405/2025 Sb.)
MEDIAN_WAGE: float = 40_709   # Kč/month (ISPV 2024 H2 median)
MEDIAN_PEN:  float = 19_800   # Kč/month (ČSSZ 2023 median)


# ── Log-normal parameter estimation via probit OLS ───────────────────────────

def fit_lognormal(percentiles: dict[int, float]) -> tuple[float, float]:
    """Estimate log-normal (μ, σ) from empirical percentiles via probit OLS.

    The log-normal CDF implies:
        Φ⁻¹(p/100) = (ln x_p − μ) / σ

    Re-arranged for OLS:
        ln x_p  =  μ  +  σ · Φ⁻¹(p/100)

    Parameters
    ----------
    percentiles:
        Mapping {integer percentile rank → observed value}.

    Returns
    -------
    (μ, σ) – parameters of the underlying normal distribution of ln(x).
    """
    ps   = np.array(sorted(percentiles.keys()), dtype=float) / 100.0
    vals = np.array([percentiles[int(p * 100)] for p in ps], dtype=float)

    z = stats.norm.ppf(ps)        # Φ⁻¹(p) – probit values
    ln_x = np.log(vals)

    # OLS: ln_x = μ + σ·z  →  design matrix [1, z]
    A = np.column_stack([np.ones_like(z), z])
    coeffs, *_ = np.linalg.lstsq(A, ln_x, rcond=None)
    mu, sigma = float(coeffs[0]), float(coeffs[1])
    return mu, sigma


def _lognormal_pdf(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Log-normal PDF."""
    return stats.lognorm.pdf(x, s=sigma, scale=np.exp(mu))


# ── Fit distributions ─────────────────────────────────────────────────────────

wage_pctls    = FALLBACK_WAGE_PERCENTILES
pension_pctls = FALLBACK_PENSION_PERCENTILES

mu_w, sig_w = fit_lognormal(wage_pctls)
mu_p, sig_p = fit_lognormal(pension_pctls)

log.info("Wage log-normal:    μ=%.4f  σ=%.4f", mu_w, sig_w)
log.info("Pension log-normal: μ=%.4f  σ=%.4f", mu_p, sig_p)

# ── Build density curves ──────────────────────────────────────────────────────

X_GRID = np.linspace(1, 150_001, 3_000)

pdf_wage    = _lognormal_pdf(X_GRID, mu_w, sig_w)
pdf_pension = _lognormal_pdf(X_GRID, mu_p, sig_p)

# Normalise to make areas visually comparable (both integrate to ~1 on truncated
# grid after scaling – purely presentational, not a probability statement)
pdf_wage    = pdf_wage    / pdf_wage.max()
pdf_pension = pdf_pension / pdf_pension.max()

# ── Figure ────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=cm2in(15, 9))

# Wage density
ax.plot(X_GRID / 1_000, pdf_wage,    color=PALETTE[0], linewidth=1.8,
        label="Mzdy zaměstnanců (2024)")
ax.fill_between(X_GRID / 1_000, pdf_wage,    alpha=0.25, color=PALETTE[0])

# Pension density
ax.plot(X_GRID / 1_000, pdf_pension, color=PALETTE[1], linewidth=1.8,
        label="Starobní důchody (2023)")
ax.fill_between(X_GRID / 1_000, pdf_pension, alpha=0.25, color=PALETTE[1])

# Vertical reference lines
ax.axvline(MIN_WAGE    / 1_000, color="grey",      linewidth=0.9, linestyle=":",
           label=f"Minimální mzda ({MIN_WAGE:,} Kč)".replace(",", "\u202f"))
ax.axvline(MEDIAN_WAGE / 1_000, color=PALETTE[0],  linewidth=0.9, linestyle="--",
           label=f"Medián mzdy ({MEDIAN_WAGE:,} Kč)".replace(",", "\u202f"))
ax.axvline(MEDIAN_PEN  / 1_000, color=PALETTE[1],  linewidth=0.9, linestyle="--",
           label=f"Medián důchodu ({MEDIAN_PEN:,} Kč)".replace(",", "\u202f"))

# Annotations
_ann_kw = dict(textcoords="offset points", fontsize=FONT_SIZE - 1,
               arrowprops=dict(arrowstyle="-", color="grey", lw=0.7))
_y_med_w = float(_lognormal_pdf(np.array([MEDIAN_WAGE]), mu_w, sig_w)[0]) \
            / pdf_wage.max()
_y_med_p = float(_lognormal_pdf(np.array([MEDIAN_PEN]),  mu_p, sig_p)[0]) \
            / pdf_pension.max()

ax.annotate("Medián mzdy",
            xy=(MEDIAN_WAGE / 1_000, _y_med_w),
            xytext=(15, 18), color=PALETTE[0], **_ann_kw)
ax.annotate("Medián důchodu",
            xy=(MEDIAN_PEN  / 1_000, _y_med_p),
            xytext=(-60, 25), color=PALETTE[1], **_ann_kw)

ax.set_xlabel("Měsíční příjem (tis. Kč)")
ax.set_ylabel("Relativní četnost (normalisovaná hustota)")
ax.set_xlim(0, 120)
ax.legend(loc="upper right", framealpha=0.9)
ax.yaxis.set_major_formatter(ticker.NullFormatter())

savefig(fig, "wage_pension_distribution", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "wage_pension_distribution",
    caption=(
        "Srovnání rozdělení hrubých mezd zaměstnanců (ISPV 2024 H2) a "
        "starobních důchodů (ČSSZ 2023) – log-normální fit přes empirické "
        "percentily. Svislé čáry vyznačují minimální mzdu, medián mzdy "
        "a medián důchodu."
    ),
    label="fig:wage_pension_distribution",
    width=r"0.95\linewidth",
    cite_key="ispv2024",
)

print("Done.")
