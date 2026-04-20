r"""
GDP per capita in PPS (EU27=100) timeseries -- AT, DE, SK, PL, DK, CZ.

Data source: Eurostat, nama_10_pc
  unit = PC_EU27_2020_HAB_MPPS_CP (% of EU27 average in million PPS per capita)
  na_item = B1GQ (GDP)

Output
------
  pics/stav_hdp_vyvoj.pdf
  latex/texparts/stav_hdp_vyvoj.tex  ← \input{} this in main.tex

Run
---
    python analyses/stav_hdp_vyvoj.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR, FONT_SIZE
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style_pgf, savefig_pgf, save_figure_tex_pgf, add_pgf_tooltips
from statout.timeline import timeline, EU27 as _EU27

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "SK", "PL", "AT", "DE", "DK"]
GEO_FILTER = "+".join(COUNTRIES)
START_YEAR = 2004  # EU enlargement year for CZ/SK/PL

HIGHLIGHT = ["CZ"]  # emphasised line

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

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
    source_url="https://ec.europa.eu/eurostat -- nama_10_pc",
)
# Remove LU and IE: outliers with ~270 and ~175 EU27=100 that distort the y-axis
ds.df = ds.df[~ds.df["geo"].isin({"LU", "IE"})].copy()
print(f"Loaded: {len(ds.countries)} countries, {ds.years[0]}--{ds.years[-1]}")

# ── 3. Timeline figure ────────────────────────────────────────────────────────
fig = timeline(
    ds,
    countries=COUNTRIES,
    title="HDP na obyvatele",
    ylabel="HDP na obyvatele [PPS, EU27 = 100]",
    highlight=HIGHLIGHT,
    annotate_last=True,
    show_eu_avg=False,    background_eu=True,)

# Add EU27 = 100 reference line
ax = fig.axes[0]
ax.set_xlim(START_YEAR, max(ds.years[-1], 2025))
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

# ── PGF tooltips & geo labels ───────────────────────────────────────────
_pivot = (
    ds.df[ds.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(ax, _pivot, fmt="{:.1f}")
_bg = sorted(set(_EU27) - set(COUNTRIES))
_pivot_bg = (
    ds.df[ds.df["geo"].isin(_bg)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(ax, _pivot_bg, fmt="{:.1f}")
for _child in ax.get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in COUNTRIES:
            _child.set_text(f"\\acs{{geo-{_txt}}}")

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "stav_hdp_vyvoj")

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "stav_hdp_vyvoj",
    caption=(
        f"HDP na obyvatele v~PPS (EU27\\,=\\,100), vybrané země EU, "
        f"{ds.years[0]}--{ds.years[-1]}."
    ),
    label="fig:stav_hdp_vyvoj",
    resizebox_width=r"\linewidth",
    cite_key="eurostat_nama_10_pc_PPS_EU27eq100",
    strings={},
)

print("Done.")
