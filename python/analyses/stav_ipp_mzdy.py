r"""
Czech collective-agreement wage growth vs. actual wage growth – CZ and peers.

Data sources
------------
Czech Republic (negotiated):
    MPSV IPP (Informace o pracovních podmínkách) – annual Excel workbooks
    downloaded from ``https://www.kolektivnismlouvy.cz``.
    The ``odmenovani`` workbook sheet A15a "Mzdový vývoj" contains, for each
    trade union sector, the breakdown of collective agreements (KS) by wage
    adjustment method. The **Celkem** (total) row col 11 gives the average
    percentage increase (``prům.%``) among KS that used the
    "zvýšením v %" (percentage-increase) method.

    Fixed layout (verified 2019–2025):
      - sheet: ``A15a``
      - header rows: 6 (rows 0–5 are title/header; row 6 starts the table)
      - Celkem row: row index 11 (0-based) or the first row where col 0 == "Celkem"
      - value column: index 11 (``prům.%`` for "zvýšením v %" sub-column)

All 6 countries (actual):
    Eurostat Labour Cost Index – nominal, annual (``lc_lci_r2_a``).
    ``B-S`` = total business economy; ``D1_D4_MD5`` = total labour costs;
    ``I20`` = 2020 = 100 base year.
    Annual growth rate derived by dividing consecutive index values.

Output
------
  pics/python/stav_ipp_mzdy.pdf
  latex/texparts/python/stav_ipp_mzdy.tex  ← \\input{} this in main.tex

Run
---
    python analyses/stav_ipp_mzdy.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import cm2in, apply_style_pgf, savefig_pgf, save_figure_tex_pgf
from analyses._shared_data import extract_ipp_negotiated

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
GEO_6 = "+".join(COUNTRIES)
START_YEAR = 2007   # first year with available IPP odmenovani data
END_YEAR = 2025     # most recent complete survey year
LBL_ACTUAL = "skutečný nárůst (Eurostat LCI)"
LBL_NEGOTIATED = "sjednaný nárůst (IPP/KS)"

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Load IPP negotiated wage increases ─────────────────────────────────────
print(f"Loading IPP odmenovani for {START_YEAR}–{END_YEAR} …")
ipp_dict = extract_ipp_negotiated(START_YEAR, END_YEAR)
ipp_records = [{"time": yr, "value": val} for yr, val in sorted(ipp_dict.items())]
ipp_years_ok = sorted(ipp_dict.keys())
for yr, val in sorted(ipp_dict.items()):
    print(f"  IPP {yr}: {val:.1f} %")

if not ipp_records:
    print(
        "\nNote: No IPP data could be downloaded (network unavailable or files "
        "not yet published for these years).\n"
        "The figure will show Eurostat labour-cost data only.\n"
        "Download the odmenovani Excel files manually from "
        "https://www.kolektivnismlouvy.cz and re-run to include CZ CA data."
    )

# ── 2. Download Eurostat labour cost index (nominal, all countries) ───────────
# lc_lci_r2_a: Labour cost index – nominal, annual (replaced lc_lci_r2 in 2024)
# Dimensions: freq · unit · nace_r2 · lcstruct · geo
# Filter: A (annual) · I20 (2020=100) · B-S (business economy) · D1_D4_MD5 (total labour costs)
print("Downloading Eurostat labour cost index (total labour costs) …")
path_lci = fetch_eurostat(
    "lc_lci_r2_a",
    f"A.I20.B-S.D1_D4_MD5.{GEO_6}",
    start_period=START_YEAR - 1,  # one extra year to compute first difference
)

ds_lci = Dataset.from_sdmx_csv(
    path_lci,
    name="Index nákladů práce",
    unit="2020=100",
    source_url="Eurostat/lc_lci_r2_a",
)

print(f"LCI countries: {ds_lci.countries}  |  years: {ds_lci.years[0]}–{ds_lci.years[-1]}")

# ── 3. Compute year-on-year wage growth from LCI index ────────────────────────

def _lci_yoy_growth(ds: Dataset, geo: str) -> pd.Series:
    """Return annual % wage growth for *geo* derived from LCI index."""
    sub = ds.for_country(geo).set_index(ds.time_col)[ds.value_col].sort_index()
    return sub.pct_change() * 100


wage_growth: dict[str, pd.Series] = {}
for country in COUNTRIES:
    series = _lci_yoy_growth(ds_lci, country)
    series = series[series.index >= START_YEAR].dropna()
    if not series.empty:
        wage_growth[country] = series

# ── 4. Build figure ───────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=cm2in(15, 10))

prop_cycle = iter(plt.rcParams["axes.prop_cycle"])

# Plot Eurostat actual wage growth (dashed, lighter) for comparison countries
for geo in COUNTRIES:
    if geo not in wage_growth:
        continue
    series = wage_growth[geo]
    color = COUNTRY_COLORS.get(geo, next(prop_cycle)["color"])
    lw = 2.0 if geo == "CZ" else 1.2
    alpha = 1.0 if geo == "CZ" else 0.65
    ax.plot(
        series.index,
        series.values,
        label=f"{geo} ({LBL_ACTUAL})",
        color=color,
        linewidth=lw,
        linestyle="--",
        alpha=alpha,
    )

# Plot IPP negotiated increases for CZ (solid, prominent)
if ipp_records:
    df_ipp = pd.DataFrame(ipp_records).set_index("time")["value"]
    ax.plot(
        df_ipp.index,
        df_ipp.values,
        label=f"CZ ({LBL_NEGOTIATED})",
        color=COUNTRY_COLORS["CZ"],
        linewidth=2.5,
        linestyle="-",
        marker="o",
        markersize=4,
        zorder=5,
    )

# Reference line at 0 %
ax.axhline(0, color="gray", linewidth=0.7, linestyle=":", alpha=0.5)

# Axis formatting
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:.0f}\u00a0%"))
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=8))
ax.set_xlabel("rok", fontsize=FONT_SIZE)
ax.set_ylabel("meziroční nárůst [%]", fontsize=FONT_SIZE)
ax.set_title(
    "Sjednaný vs. skutečný mzdový nárůst, ČR",
    fontsize=FONT_SIZE,
)

# Legend: place outside plot area if many entries
ax.legend(
    frameon=False,
    fontsize=FONT_SIZE - 1,
    ncol=2,
    loc="upper left",
)

all_years = sorted(
    {y for s in wage_growth.values() for y in s.index}
    | {r["time"] for r in ipp_records}
)
if all_years:
    ax.set_xlim(START_YEAR, END_YEAR)

# ── 5. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "stav_ipp_mzdy")

# ── 6. Write LaTeX snippet ────────────────────────────────────────────────────
year_range = f"{START_YEAR}–{END_YEAR}"
save_figure_tex_pgf(
    "stav_ipp_mzdy",
    caption=f"Sjednaný a~skutečný mzdový nárůst v~KS, ČR, {year_range}.",
    label="fig:stav_ipp_mzdy",
    resizebox_width=r"0.95\linewidth",
    cite_keys=["mpsv_ipp", "eurostat_lci"],
    strings={},
)

print("Done.")
