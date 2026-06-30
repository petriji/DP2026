r"""
Top 10 % wealth share map -- Europe choropleth.

Shows the concentration of household net wealth (top 10 % share) across
European countries using OECD HFCS survey data (latest available per country).

Data source: OECD Wealth Distribution database (WEALTH dataset, SH_TOP10)

Output
------
  pics/python/eu_bohatstvi_mapa.pdf
  latex/texparts/python/eu_bohatstvi_mapa.tex

Run
---
    python analyses/gini_wealth_map.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_oecd
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    apply_geo_labels_pgf,
)
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────

START_YEAR = 2008

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
# WEALTH dataset: SH_TOP10 = top 10 % net wealth share (% of total)
path = fetch_oecd("WEALTH", start_period=START_YEAR)

ds = Dataset.from_oecd_csv(
    path,
    name="Podíl top 10 % na čistém jmění",
    unit="%",
    source_url="OECD Wealth Distribution / WEALTH",
    filters={"MEASURE": "SH_TOP10"},
)

print(f"Loaded: {len(ds.countries)} countries, {ds.years[0]}--{ds.years[-1]}")
print(f"Display year (latest): {ds.latest_year}")

# ── 2. Choropleth map ─────────────────────────────────────────────────────────
# fill_latest=True (default) fills countries with their most recent survey data
_values = (
    ds.df[ds.df["time"] <= ds.latest_year]
    .sort_values("time").groupby("geo")["value"].last().to_dict()
)
_vmin = min(_values.values())
_vmax = max(_values.values())

STRINGS = {
    "title": f"Podíl top 10\\,\\% domácností na čistém jmění (do {ds.latest_year})",
    "colorbar_label": r"podíl top 10\,\% na čistém jmění [\%]",
}

fig = choropleth(
    ds,
    year=ds.latest_year,
    title=STRINGS["title"],
    colorbar_label=STRINGS["colorbar_label"],
    cmap="RdYlGn_r",
    vmin=_vmin,
    vmax=_vmax,
    label_countries=True,
    fill_latest=True,
    highlight_colorbar=["CZ"],
)

apply_geo_labels_pgf(fig.axes[0], halo=True, values=_values, tooltip_fmt="{:.1f}")

# ── 3. Save ───────────────────────────────────────────────────────────────────
savefig_pgf(fig, "eu_bohatstvi_mapa", strings=STRINGS)

# ── 4. LaTeX snippet ──────────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_bohatstvi_mapa",
    caption=(
        f"Podíl top 10\\,\\% domácností na čistém jmění, EU mapa, do {ds.latest_year}."),
    label="fig:eu_bohatstvi_mapa",
    resizebox_width=r"0.95\linewidth",
    cite_key="oecd_hfcs_wealth_top10_PC",
    strings=STRINGS,
)

print("Done.")
