r"""
GDP per capita in PPS (EU27=100) timeseries – AT, DE, SK, PL, DK, CZ.

Data source: Eurostat, nama_10_pc
  unit = PC_EU27_2020_HAB_MPPS_CP (% of EU27 average in million PPS per capita)
  na_item = B1GQ (GDP)

Output
------
  pics/gdp_ppp_timeline.pdf
  latex/texparts/gdp_ppp_timeline.tex  ← \input{} this in main.tex

Run
---
    python analyses/gdp_ppp_timeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR, FONT_SIZE
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.timeline import timeline

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "SK", "PL", "AT", "DE", "DK"]
GEO_FILTER = "+".join(COUNTRIES)
START_YEAR = 2004  # EU enlargement year for CZ/SK/PL

HIGHLIGHT = ["CZ"]  # emphasised line

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# Filter expression: freq . unit . na_item . geo
# Fetch all countries (trailing dot) for the EU grey cloud
path = fetch_eurostat(
    "nama_10_pc",
    "A.PC_EU27_2020_HAB_MPPS_CP.B1GQ.",
    start_period=START_YEAR,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="GDP per capita",
    unit="EU27=100",
    source_url="https://ec.europa.eu/eurostat – nama_10_pc",
)
# Remove LU and IE: outliers with ~270 and ~175 EU27=100 that distort the y-axis
ds.df = ds.df[~ds.df["geo"].isin({"LU", "IE"})].copy()
print(f"Loaded: {len(ds.countries)} countries, {ds.years[0]}–{ds.years[-1]}")

# ── 3. Timeline figure ────────────────────────────────────────────────────────
fig = timeline(
    ds,
    countries=COUNTRIES,
    title="HDP na obyvatele",
    ylabel="HDP/obyvatele (EU27 = 100)",
    highlight=HIGHLIGHT,
    annotate_last=True,
    show_eu_avg=False,    background_eu=True,)

# Add EU27 = 100 reference line
ax = fig.axes[0]
ax.set_xlim(START_YEAR, ds.years[-1])
ax.axhline(100, color="gray", linewidth=0.8, linestyle="--", alpha=0.6, zorder=1)
ax.annotate(
    "EU27 = 100",
    xy=(ds.years[-1], 100),
    xytext=(-30, 4),
    textcoords="offset points",
    fontsize=FONT_SIZE,
    color="gray",
    alpha=0.8,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "gdp_ppp_timeline", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "gdp_ppp_timeline",
    caption=(
        "HDP na obyvatele v~paritě kupní síly (PPS), index EU27\\,=\\,100 "
        "(kód \\texttt{PC\_EU27\_2020\_HAB\_MPPS\_CP}), "
        f"{ds.years[0]}--{ds.years[-1]}."
    ),
    label="fig:gdp_ppp_timeline",
    width=r"0.95\linewidth",
    cite_key="eurostat_nama_10_pc_PPS_EU27eq100",
)

print("Done.")
