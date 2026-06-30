r"""
AROPE rate (top) and D3 income threshold vs EU27 median (bottom).

Two stacked panels sharing the x-axis (year).

Top panel
---------
At-risk-of-poverty-or-social-exclusion rate (AROPE) --- Eurostat ``ilc_peps01n``
filtered to ``A.PC.TOTAL.T.`` (annual, % of population, all ages, both sexes).

Bottom panel
------------
Upper threshold of the third decile (D3) of equivalised disposable income in
PPS, expressed as % of the EU27 median (D5, PPS).  Source: Eurostat
``ilc_di01`` (PPS basis ``PPS_EU27_2020_HAB`` for cross-country comparability).

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
import pandas as pd

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
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
path_di01 = fetch_eurostat(
    "ilc_di01",
    "A.D3+D5.TC.PPS+EUR.",
)
raw = pd.read_csv(path_di01, comment="#")
raw.columns = [c.strip() for c in raw.columns]
raw["OBS_VALUE"] = pd.to_numeric(raw["OBS_VALUE"], errors="coerce")
raw = raw.dropna(subset=["OBS_VALUE"])
raw["time"] = raw["TIME_PERIOD"].astype(str).str[:4].astype(int)

# EU27 median --- prefer PPS, fall back to EUR when PPS missing (≤2 % error)
eu_pps = (
    raw[(raw["geo"] == "EU27_2020")
        & (raw["quantile"] == "D5")
        & (raw["indic_il"] == "TC")
        & (raw["currency"] == "PPS")]
    .groupby("time")["OBS_VALUE"].mean()
)
eu_eur = (
    raw[(raw["geo"] == "EU27_2020")
        & (raw["quantile"] == "D5")
        & (raw["indic_il"] == "TC")
        & (raw["currency"] == "EUR")]
    .groupby("time")["OBS_VALUE"].mean()
)
eu_median = eu_pps.combine_first(eu_eur).rename("eu_median")

# Country D3 in PPS
d3 = raw[(raw["quantile"] == "D3")
         & (raw["indic_il"] == "TC")
         & (raw["currency"] == "PPS")
         & (raw["geo"] != "EU27_2020")][["geo", "time", "OBS_VALUE"]].copy()
d3 = d3.merge(eu_median, on="time", how="inner")
d3["value"] = d3["OBS_VALUE"] / d3["eu_median"] * 100.0
d3_norm = d3[["geo", "time", "value"]].dropna()

# Restrict both panels to the AROPE start year (2015) onward for alignment
d3_norm = d3_norm[d3_norm["time"] >= 2015]

ds_d3 = Dataset(
    d3_norm,
    name="D3 vs EU",
    unit="EU=100",
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
    "ylabel_top": r"míra \acs{AROPE} [\%]",
    "ylabel_bot": r"D3 (\acs{PPS}, \acs{geo-EU}\,=\,100)",
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
    ax=ax_bot,
)
# EU=100 reference line
ax_bot.axhline(100.0, color="#888888", linewidth=0.8, linestyle="--",
               alpha=0.7, zorder=2)

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

fig.subplots_adjust(hspace=0.08)

# ── 5. Save ───────────────────────────────────────────────────────────────────
savefig_pgf(fig, "stav_arope_dual", strings=STRINGS)

save_figure_tex_pgf(
    "stav_arope_dual",
    caption=(
        f"Vývoj míry \\acs{{AROPE}} a~hranice třetího decilu čistého "
        f"ekvivalizovaného příjmu v~\\acs{{PPS}} vůči mediánu \\acs{{EU}}27, "
        f"vybrané země EU, {first_year}--{last_year}."
    ),
    label="fig:stav_arope_dual",
    cite_keys=[
        "eurostat_ilc_peps01n_PC_pop",
        "eurostat_ilc_di01_D3_PPS",
    ],
    strings=STRINGS,
)

print(f"\nDone. Output in {LATEX_PICS_DIR} / texparts.")
