r"""
AROPE rate (top) and share of population below EU27 D3 threshold (bottom).

Two stacked panels sharing the x-axis (year).

Top panel
---------
At-risk-of-poverty-or-social-exclusion rate (AROPE) --- Eurostat ``ilc_peps01n``
filtered to ``A.PC.TOTAL.T.`` (annual, % of population, all ages, both sexes).

Bottom panel
------------
Estimated share (%) of each country's population whose equivalised disposable
income is at most the EU27 D3 threshold (upper bound of the third decile) in
PPS.  The share is obtained by fitting a log-normal distribution to the nine
country-specific decile thresholds D1..D9 (Eurostat ``ilc_di01``, currency
``PPS``) and evaluating its CDF at the EU27 D3 threshold.  This turns a purely
relative cut-off into an absolute cross-country benchmark.

Output
------
  python/figures/stav_arope_dual.pgf
  latex/texparts/python/stav_arope_dual.tex
  latex/texparts/figures/stav_arope_dual.tex

Run
---
    python analyses/stav_arope_dual.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import LATEX_PICS_DIR, FIGURE_TEXT_SIZE, FIGURE_LABEL_SIZE, FIGURE_COMPACT_LABEL_SIZE
from stattool.fetch import fetch_eurostat
from stattool.data_quality import warn_fallback
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    add_pgf_tooltips,
    cm2in,
)
from statout.timeline import timeline, EU27 as _EU27

# ── Parameters ────────────────────────────────────────────────────────────────
COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
HIGHLIGHT = ["CZ"]
START_YEAR = 2017

# Per-label y-nudge knobs exposed to LaTeX (one macro per country, applies
# to both panels because the labels share the same \acs{geo-XX} text).
NUDGE_LABELS = [(geo, rf"\acs{{geo-{geo}}}") for geo in COUNTRIES]

apply_style_pgf()

# ── 1. Fetch & parse AROPE (ilc_peps01n) ──────────────────────────────────────
path_arope = fetch_eurostat(
    "ilc_peps01n",
    "A.PC.TOTAL.T.",
)
ds_arope = Dataset.from_sdmx_csv(
    path_arope,
    name="AROPE",
    unit="%",
    source_url="Eurostat/ilc_peps01n",
)

# ── 2. Fetch & build D3-vs-EU-median Dataset (ilc_di01) ───────────────────────
# ilc_di01 dim order: freq · quantile · indic_il · currency · geo
# Need D3 per country in PPS, plus D5 for EU27_2020 as the baseline.
# The EU27_2020 D5 PPS series is published only from 2018. For 2015--2017 we
# back-fill it with the D5 EUR value for EU27_2020: at EU27 level PPP ≡ 1 by
# construction, and the observed overlap (2018--2024) shows diff ≤ 2 %.
# Fetch all deciles D1..D9 per country in PPS (plus EUR fallback for the
# EU27 aggregate, whose PPS series starts only in 2018).
path_di01 = fetch_eurostat(
    "ilc_di01",
    "A.D1+D2+D3+D4+D5+D6+D7+D8+D9.TC.PPS+EUR.",
)
raw = pd.read_csv(path_di01, comment="#")
raw.columns = [c.strip() for c in raw.columns]
raw["OBS_VALUE"] = pd.to_numeric(raw["OBS_VALUE"], errors="coerce")
raw = raw.dropna(subset=["OBS_VALUE"])
raw["time"] = raw["TIME_PERIOD"].astype(str).str[:4].astype(int)

# EU27 D3 threshold in PPS (reference bar shared across countries).
# PPS series starts 2018; for 2015--2017 use EUR value (EU27 PPP ≡ 1).
eu_d3_pps = (
    raw[(raw["geo"] == "EU27_2020")
        & (raw["quantile"] == "D3")
        & (raw["indic_il"] == "TC")
        & (raw["currency"] == "PPS")]
    .groupby("time")["OBS_VALUE"].mean()
)
eu_d3_eur = (
    raw[(raw["geo"] == "EU27_2020")
        & (raw["quantile"] == "D3")
        & (raw["indic_il"] == "TC")
        & (raw["currency"] == "EUR")]
    .groupby("time")["OBS_VALUE"].mean()
)
eu_d3 = eu_d3_pps.combine_first(eu_d3_eur).rename("eu_d3")
fallback_years = sorted(set(eu_d3_eur.index) - set(eu_d3_pps.index))
if fallback_years:
    warn_fallback(
        f"EU27 D3 PPS series missing in years {fallback_years}; EUR used as fallback",
        source="Eurostat/ilc_di01",
    )

# Country deciles D1..D9 in PPS (long → wide per country-year)
_DEC_ORDER = [f"D{k}" for k in range(1, 10)]
dec = (
    raw[(raw["indic_il"] == "TC")
        & (raw["currency"] == "PPS")
        & (raw["geo"] != "EU27_2020")
        & (raw["quantile"].isin(_DEC_ORDER))]
    [["geo", "time", "quantile", "OBS_VALUE"]]
    .pivot_table(
        index=["geo", "time"], columns="quantile", values="OBS_VALUE",
        aggfunc="mean",
    )
    .reindex(columns=_DEC_ORDER)
    .dropna()
    .reset_index()
)

# Share of population with income ≤ EU27 D3 threshold, estimated by fitting
# a log-normal distribution to each country-year's nine decile thresholds.
# Deciles give CDF points (D_k, k/10) for k=1..9.  Regressing log(D_k) on
# Φ⁻¹(k/10) yields (μ, σ) = (intercept, slope); the sought share is then
# Φ((log(threshold) − μ) / σ).  Empirically the fit is near-perfect in the
# middle of the distribution where D3--D5 live (R² > 0.999 for EU countries).
from scipy.stats import norm  # local import — only place scipy is used

_QLEVELS = np.array([k / 10.0 for k in range(1, 10)])
_Z = norm.ppf(_QLEVELS)

def _lognorm_cdf(row: pd.Series, threshold: float) -> float:
    y = np.log(row[_DEC_ORDER].to_numpy(dtype=float))
    sigma, mu = np.polyfit(_Z, y, 1)
    return float(norm.cdf((np.log(threshold) - mu) / sigma))

dec = dec.merge(eu_d3.rename("eu_d3"), on="time", how="inner")
dec["value"] = dec.apply(
    lambda r: 100.0 * _lognorm_cdf(r, r["eu_d3"]), axis=1,
)
d3_share = dec[["geo", "time", "value"]].copy()
d3_share = d3_share[d3_share["time"] >= 2015]

ds_d3 = Dataset(
    d3_share,
    name="Share ≤ EU27 D3",
    unit="%",
    source_url="Eurostat/ilc_di01",
)

print(f"AROPE years: {ds_arope.years[0]}--{ds_arope.years[-1]}  |  "
      f"D3 years: {ds_d3.years[0]}--{ds_d3.years[-1]}")

# Year range = intersection (for caption)
yrs_common = sorted(set(ds_arope.years) & set(ds_d3.years))
first_year, last_year = yrs_common[0], yrs_common[-1]

# ── 3. Plot --- two stacked panels ──────────────────────────────────────────────
fig, (ax_top, ax_bot) = plt.subplots(
    nrows=2, ncols=1, sharex=True, figsize=cm2in(15, 14),
)

STRINGS = {
    "title": r"Míra \acs{AROPE}, porovnání metodik dle národního a~\acs{EU} rozdělení příjmů v~\acs{PPS}",
    "ylabel_top": r"míra \acs{AROPE} [\si{\percent}]",
    "ylabel_bot": r"podíl os. s~příjmem $\leq$ \acs{var-D3}\acs{geo-EU} [\si{\percent}]",
}
# --- Top panel: AROPE -------------------------------------------------------
timeline(
    ds_arope,
    countries=COUNTRIES,
    title="",
    ylabel=STRINGS["ylabel_top"],
    xlabel="",
    highlight=HIGHLIGHT,
    background_eu=True,
    show_eu_avg=False,
    ax=ax_top,
)

# --- Bottom panel: D3 indexed to EU=100 -------------------------------------
timeline(
    ds_d3,
    countries=COUNTRIES,
    title="",
    ylabel=STRINGS["ylabel_bot"],
    xlabel="rok",
    highlight=HIGHLIGHT,
    background_eu=True,
    show_eu_avg=False,
    ax=ax_bot,
)
# Axis limits — common x-range, panel-specific y-range
LAST_YEAR = max(2025, last_year)
ax_top.set_xlim(START_YEAR, LAST_YEAR)
ax_bot.set_xlim(START_YEAR, LAST_YEAR)
ax_top.set_ylim(0, 35)
ax_bot.set_ylim(0, 100)

# Hide x-axis label/ticks on the top panel (sharex shows them on bottom)
ax_top.set_xlabel("")
for lbl in ax_top.get_xticklabels():
    lbl.set_visible(False)
ax_top.tick_params(axis="x", which="both", labelbottom=False)


# ── 4. PGF tooltips & geo-acro labels for both panels ────────────────────────
def _decorate(ax, ds, fmt):
    pivot_fg = (
        ds.df[ds.df["geo"].isin(COUNTRIES)]
        .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
    )
    add_pgf_tooltips(ax, pivot_fg, fmt=fmt)
    bg = sorted(set(_EU27) - set(COUNTRIES))
    pivot_bg = (
        ds.df[ds.df["geo"].isin(bg)]
        .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
    )
    if not pivot_bg.empty:
        add_pgf_tooltips(ax, pivot_bg, fmt=fmt)
    for child in ax.get_children():
        if hasattr(child, "get_text"):
            txt = child.get_text().strip()
            if txt in COUNTRIES:
                child.set_text(f"\\acs{{geo-{txt}}}")


_decorate(ax_top, ds_arope, "{:.1f}")
_decorate(ax_bot, ds_d3, "{:.1f}")

fig.suptitle(STRINGS["title"], fontsize=FIGURE_TEXT_SIZE, y=0.995)
fig.subplots_adjust(hspace=0.08, top=0.94)

# ── 5. Save ───────────────────────────────────────────────────────────────────
savefig_pgf(fig, "stav_arope_dual", strings=STRINGS, nudge_labels=NUDGE_LABELS)

save_figure_tex_pgf(
    "stav_arope_dual",
    caption=f"Vývoj míry \\acs{{AROPE}} a~odhadovaný podíl osob s~čistým ekvivalizovaným příjmem nejvýše na úrovni třetího decilu \\acs{{var-D3}} \\acs{{geo-EU27}} v~\\acs{{PPS}} (log-normální interpolace z~decilů), vybrané země EU, 2015--{last_year}",
    label="fig:stav_arope_dual",
    cite_keys=[
        "eurostat_ilc_peps01n_PC_pop",
        "eurostat_ilc_di01_D3_PPS",
    ],
    strings=STRINGS,
    nudge_labels=NUDGE_LABELS,
)

print(f"\nDone. Output in {LATEX_PICS_DIR} / texparts.")
