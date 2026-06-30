r"""
Net disposable household income — fitted log-normal distributions, six countries.

For CZ, SK, PL, AT, DE and DK fits a log-normal distribution to the nine
decile cut-off thresholds (D1..D9, indicator TC) of equivalised disposable
household income (Eurostat ``ilc_di01``) in PPS per equivalent adult per
year, and plots the density curves on a shared x-axis.

Fitting
-------
For X ~ LN(μ, σ) the p-th quantile satisfies ``log(Q_p) = μ + σ · Φ⁻¹(p)``.
Given the nine decile cut-offs (p = 0.1 .. 0.9) μ and σ are estimated by
ordinary least squares on the linear model in the log-quantile / probit
scale.

Output
------
  python/figures/eu_prijem_distribuce.pgf
  latex/texparts/python/eu_prijem_distribuce.tex
  latex/texparts/figures/eu_prijem_distribuce.tex (editable, written once)

Run
---
    python analyses/eu_prijem_distribuce.py
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
DECILES = [f"D{i}" for i in range(1, 10)]
PROBS = np.array([i / 10 for i in range(1, 10)])
# Φ⁻¹(p) for p = 0.1 .. 0.9
ZSCORES = np.array([
    -1.281552, -0.841621, -0.524401, -0.253347, 0.000000,
     0.253347,  0.524401,  0.841621,  1.281552,
])
START_YEAR = 2015

# X-axis evaluation grid (PPS / equivalent adult / year)
X_MIN, X_MAX = 0.0, 80_000.0
# 100 points is plenty for a smooth log-normal — keeps PGF compile light.
X_GRID = np.linspace(X_MIN, X_MAX, 100)
# Bin width used to convert density → % share per bin on the y-axis
BIN_WIDTH = 1_000.0  # PPS

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
quant_filter = "+".join(DECILES)
path = fetch_eurostat(
    "ilc_di01",
    f"A.{quant_filter}.TC.PPS.{geo_filter}",
    start_period=START_YEAR,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
raw = pd.read_csv(path, comment="#")
raw.columns = [c.strip() for c in raw.columns]
raw["OBS_VALUE"] = pd.to_numeric(raw["OBS_VALUE"], errors="coerce")
raw = raw.dropna(subset=["OBS_VALUE"])
raw["year"] = raw["TIME_PERIOD"].astype(str).str[:4].astype(int)

# Latest year per country with the full set of D1..D9
counts = raw.groupby(["geo", "year"])["quantile"].nunique().reset_index(name="n")
counts = counts[counts["n"] == len(DECILES)]
latest = counts.sort_values("year").groupby("geo")["year"].last().to_dict()
ref_year = max(latest.values()) if latest else int(raw["year"].max())
print(f"Reference year (per country): {latest}")
print(f"Reference year for caption: {ref_year}")

snap = raw[raw.apply(lambda r: r["year"] == latest.get(r["geo"], -1), axis=1)]

# ── 3. Fit log-normal per country ─────────────────────────────────────────────
fits: dict[str, tuple[float, float]] = {}
medians: dict[str, float] = {}
decile_values: dict[str, np.ndarray] = {}
for country in sorted(set(COUNTRIES) | set(BG_COUNTRIES)):
    sub = snap[snap["geo"] == country].set_index("quantile")["OBS_VALUE"]
    if len(sub) < len(DECILES):
        if country in COUNTRIES:
            print(f"  {country}: missing deciles, skipping")
        continue
    vals = np.array([float(sub[d]) for d in DECILES])
    mu, sigma = fit_lognormal(vals)
    fits[country] = (mu, sigma)
    medians[country] = float(np.exp(mu))
    decile_values[country] = vals
    if country in COUNTRIES:
        print(
            f"  {country} ({latest[country]}): μ={mu:.3f}, σ={sigma:.3f}, "
            f"medián≈{medians[country]:,.0f} PPS"
        )

# ── 4. Plot ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=cm2in(16, 10))

x_thousands = X_GRID / 1_000.0  # display x in thousand PPS
# Convert density [1/PPS] to % of population per BIN_WIDTH-wide bin
y_scale = BIN_WIDTH * 100.0

# Background: other EU27 countries as thin grey lines (no fill, no markers)
for country in BG_COUNTRIES:
    if country not in fits:
        continue
    mu, sigma = fits[country]
    pdf = lognormal_pdf(X_GRID, mu, sigma) * y_scale
    ax.plot(
        x_thousands, pdf,
        color="#999999", linewidth=0.5, alpha=0.45, zorder=1,
    )


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
    ax.fill_between(x_thousands, pdf, alpha=0.10, color=color, zorder=2)
    line, = ax.plot(
        x_thousands, pdf,
        color=color, linewidth=1.6,
        label=f"\\acs{{geo-{country}}}",
        zorder=4,
    )
    handles.append(line)
    # Median reference line
    ax.axvline(
        medians[country] / 1_000.0,
        color=color, linewidth=0.8, linestyle="--", alpha=0.55, zorder=3,
    )
    # Tooltip at the median peak
    peak_y = lognormal_pdf(np.array([medians[country]]), mu, sigma)[0] * y_scale
    _tooltip(
        ax, medians[country] / 1_000.0, peak_y,
        f"{country} {latest[country]}: median {medians[country]:,.0f} PPS",
    )
    # Tooltips at each decile cut-off (D1..D9) — invisible markers carrying data
    for d, p, q in zip(DECILES, PROBS, decile_values[country]):
        y_q = lognormal_pdf(np.array([q]), mu, sigma)[0] * y_scale
        _tooltip(
            ax, q / 1_000.0, y_q,
            f"{country} {latest[country]} {d} (p={p:.1f}): {q:,.0f} PPS",
        )

STRINGS = {
    "title": rf"Modelové rozložení čistého disponibilního příjmu domácností ({ref_year})",
    "xlabel": r"ekvivalizovaný čistý disponibilní příjem [tis.\,\acs{PPS}/rok]",
    "ylabel": r"podíl domácností v\,intervalu \SI{1000}{\pps} [\%]",
}
ax.set_xlabel(
    STRINGS["xlabel"],
    fontsize=FONT_SIZE,
)
ax.set_ylabel(
    STRINGS["ylabel"],
    fontsize=FONT_SIZE,
)
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:.0f}"))
ax.yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ","))
)
ax.set_xlim(X_MIN / 1_000.0, X_MAX / 1_000.0)
ax.set_ylim(bottom=0)
ax.set_title(
    STRINGS["title"],
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
    f"\\acs{{geo-{c}}}~\\SI{{{medians[c]:,.0f}}}{{\\pps}}".replace(",", "\\,")
    for c in COUNTRIES if c in medians
)

savefig_pgf(fig, "eu_prijem_distribuce", strings=STRINGS)
save_figure_tex_pgf(
    "eu_prijem_distribuce",
    caption=(
        f"Modelové rozložení ekvivalizovaného čistého disponibilního "
        f"příjmu domácností, vybrané země EU, {ref_year}."
    ),
    cite_keys="eurostat_ilc_di01",
    label="fig:eu_prijem_distribuce",
    resizebox_width=r"\linewidth",
    strings={**STRINGS, "mediany": median_str},
)

print("Done.")
