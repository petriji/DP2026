r"""
Gross hourly wage — fitted log-normal distributions, six countries.

Variant of ``eu_prijem_distribuce`` that uses per-worker gross hourly wages
(Structure of Earnings Survey, ``earn_ses_hourly``) instead of household
disposable income.  SES publishes only three distribution points per country
(D1, median, D9), which is exactly enough to fit a log-normal location and
scale parameter via least squares.

Output
------
  python/figures/eu_mzda_distribuce.pgf
  latex/texparts/python/eu_mzda_distribuce.tex
  latex/texparts/figures/eu_mzda_distribuce.tex (editable, written once)

Run
---
    python analyses/eu_mzda_distribuce.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import COUNTRY_COLORS, FONT_SIZE
from statout.timeline import EU27
from stattool.fetch import fetch_eurostat
from stattool.style import (
    apply_style_pgf,
    cm2in,
    savefig_pgf,
    save_figure_tex_pgf,
)

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "SK", "PL", "AT", "DE", "DK"]
INDIC = ["D1_E_PPS", "MED_E_PPS", "D9_E_PPS"]
PROBS = np.array([0.10, 0.50, 0.90])
ZSCORES = np.array([-1.281552, 0.000000, 1.281552])

# X-axis evaluation grid (PPS / hour)
X_MIN, X_MAX = 0.0, 50.0
# 100 points keep the PGF light while staying smooth for log-normal.
X_GRID = np.linspace(X_MIN, X_MAX, 100)
BIN_WIDTH = 1.0  # PPS/h

# Background EU27 countries (drawn as thin grey lines, no fill).
# Eurostat uses "EL" for Greece, not "GR".
BG_COUNTRIES = sorted((set(EU27) - set(COUNTRIES)) - {"GR"} | {"EL"})

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()


# ── Math helpers ──────────────────────────────────────────────────────────────

def fit_lognormal(values: np.ndarray) -> tuple[float, float]:
    """Fit log-normal (μ, σ) by OLS on log(Q_p) = μ + σ · Φ⁻¹(p)."""
    log_q = np.log(np.maximum(values, 1e-12))
    a = np.column_stack([np.ones_like(ZSCORES), ZSCORES])
    params, *_ = np.linalg.lstsq(a, log_q, rcond=None)
    return float(params[0]), float(max(params[1], 1e-6))


def lognormal_pdf(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    x_pos = np.maximum(x, 1e-12)
    return (
        np.exp(-0.5 * ((np.log(x_pos) - mu) / sigma) ** 2)
        / (x_pos * sigma * np.sqrt(2.0 * np.pi))
    )


# ── 1. Download (foreground + EU27 background in one fetch) ──────────────────
ALL_GEO = sorted(set(COUNTRIES) | set(BG_COUNTRIES))
geo_filter = "+".join(ALL_GEO)
indic_filter = "+".join(INDIC)
path = fetch_eurostat(
    "earn_ses_hourly",
    f"A.B-S_X_O.TOTAL.TOTAL.TOTAL.T.{indic_filter}.{geo_filter}",
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
raw = pd.read_csv(path, comment="#")
raw.columns = [c.strip() for c in raw.columns]
raw["OBS_VALUE"] = pd.to_numeric(raw["OBS_VALUE"], errors="coerce")
raw = raw.dropna(subset=["OBS_VALUE"])
raw["year"] = raw["TIME_PERIOD"].astype(str).str[:4].astype(int)

# Latest SES year with all three indicators present
counts = raw.groupby(["geo", "year"])["indic_se"].nunique().reset_index(name="n")
counts = counts[counts["n"] == len(INDIC)]
latest = counts.sort_values("year").groupby("geo")["year"].last().to_dict()
ref_year = max(latest.values()) if latest else int(raw["year"].max())
print(f"Reference year (per country): {latest}")
print(f"Reference year for caption: {ref_year}")

snap = raw[raw.apply(lambda r: r["year"] == latest.get(r["geo"], -1), axis=1)]

# ── 3. Fit log-normal per country ─────────────────────────────────────────────
fits: dict[str, tuple[float, float]] = {}
medians: dict[str, float] = {}
indic_values: dict[str, np.ndarray] = {}
for country in sorted(set(COUNTRIES) | set(BG_COUNTRIES)):
    sub = snap[snap["geo"] == country].set_index("indic_se")["OBS_VALUE"]
    if len(sub) < len(INDIC):
        if country in COUNTRIES:
            print(f"  {country}: missing indicators, skipping")
        continue
    vals = np.array([float(sub[i]) for i in INDIC])
    mu, sigma = fit_lognormal(vals)
    fits[country] = (mu, sigma)
    medians[country] = float(np.exp(mu))
    indic_values[country] = vals
    if country in COUNTRIES:
        print(
            f"  {country} ({latest[country]}): μ={mu:.3f}, σ={sigma:.3f}, "
            f"medián≈{medians[country]:.2f} PPS/h"
        )

# ── 4. Plot ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=cm2in(16, 10))

# Density [1/(PPS/h)] → % of employees per BIN_WIDTH-wide bin
y_scale = BIN_WIDTH * 100.0

# Background: other EU27 countries as thin grey lines (no fill, no markers)
for country in BG_COUNTRIES:
    if country not in fits:
        continue
    mu, sigma = fits[country]
    pdf = lognormal_pdf(X_GRID, mu, sigma) * y_scale
    ax.plot(
        X_GRID, pdf,
        color="#999999", linewidth=0.5, alpha=0.45, zorder=1,
    )


DP_LABELS = ["D1 (p=0,1)", "medián (p=0,5)", "D9 (p=0,9)"]


def _tooltip(ax, x, y, text):
    ax.text(
        x, y,
        r"\pdftooltip{\phantom{\rule{3pt}{3pt}}}{" + text + r"}",
        fontsize=FONT_SIZE,
        ha="center", va="center", clip_on=True, zorder=10,
    )


handles = []
for country in COUNTRIES:
    if country not in fits:
        continue
    mu, sigma = fits[country]
    pdf = lognormal_pdf(X_GRID, mu, sigma) * y_scale
    color = COUNTRY_COLORS.get(country, "#888888")
    ax.fill_between(X_GRID, pdf, alpha=0.10, color=color, zorder=2)
    line, = ax.plot(
        X_GRID, pdf,
        color=color, linewidth=1.6,
        label=f"\\acs{{geo-{country}}}",
        zorder=4,
    )
    handles.append(line)
    ax.axvline(
        medians[country],
        color=color, linewidth=0.8, linestyle="--", alpha=0.55, zorder=3,
    )
    peak_y = lognormal_pdf(np.array([medians[country]]), mu, sigma)[0] * y_scale
    _tooltip(
        ax, medians[country], peak_y,
        f"{country} {latest[country]}: median {medians[country]:.2f} PPS/h",
    )
    # Tooltips at the three SES data points (D1, median, D9)
    for label, q in zip(DP_LABELS, indic_values[country]):
        y_q = lognormal_pdf(np.array([q]), mu, sigma)[0] * y_scale
        _tooltip(
            ax, q, y_q,
            f"{country} {latest[country]} {label}: {q:.2f} PPS/h",
        )

ax.set_xlabel("hrubá hodinová mzda [PPS/h]", fontsize=FONT_SIZE)
ax.set_ylabel(
    "podíl zaměstnanců v\\,intervalu \\SI{1}{\\pps\\per\\hour} [\\%]",
    fontsize=FONT_SIZE,
)
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:.0f}"))
ax.yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ","))
)
ax.set_xlim(X_MIN, X_MAX)
ax.set_ylim(bottom=0)
ax.set_title(
    f"Modelové rozložení hrubé hodinové mzdy zaměstnanců ({ref_year})",
    fontsize=FONT_SIZE,
)

# Minor grid
ax.minorticks_on()
ax.grid(which="major", axis="both", linestyle=":", linewidth=0.5, alpha=0.6)
ax.grid(which="minor", axis="both", linestyle=":", linewidth=0.3, alpha=0.3)

ax.legend(
    handles=handles,
    ncol=len(handles),
    loc="lower center",
    bbox_to_anchor=(0.5, -0.22),
    frameon=False,
    fontsize=FONT_SIZE - 1,
)

# ── 5. Save ───────────────────────────────────────────────────────────────────
median_str = "; ".join(
    f"\\acs{{geo-{c}}}~\\SI{{{medians[c]:.2f}}}{{\\pps\\per\\hour}}".replace(".", "{,}")
    for c in COUNTRIES if c in medians
)

savefig_pgf(fig, "eu_mzda_distribuce")
save_figure_tex_pgf(
    "eu_mzda_distribuce",
    caption=(
        f"Modelové rozložení hrubé hodinové mzdy zaměstnanců v~\\acs{{PPS}}, "
        f"vybrané země EU, {ref_year}."
    ),
    cite_keys="eurostat_ses_hourly",
    label="fig:eu_mzda_distribuce",
    resizebox_width=r"0.95\linewidth",
    strings={
        "mediany": median_str,
    },
)

print("Done.")
