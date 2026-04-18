r"""
Top 10 % wealth share map – Europe choropleth.

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
from stattool.style import apply_style, savefig, save_figure_tex
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────

START_YEAR = 2008

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

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

print(f"Loaded: {len(ds.countries)} countries, {ds.years[0]}–{ds.years[-1]}")
print(f"Display year (latest): {ds.latest_year}")

# ── 2. Choropleth map ─────────────────────────────────────────────────────────
# fill_latest=True (default) fills countries with their most recent survey data
fig = choropleth(
    ds,
    year=ds.latest_year,
    title=f"Podíl top 10\\,% domácností na čistém jmění (do {ds.latest_year})",
    colorbar_label="top 10 % podíl na čistém jmění [%]",
    cmap="RdYlGn_r",
    vmin=30,
    vmax=80,
    label_countries=True,
    fill_latest=True,
)

# ── 3. Save ───────────────────────────────────────────────────────────────────
savefig(fig, "eu_bohatstvi_mapa", out_dir=LATEX_PICS_DIR)

# ── 4. LaTeX snippet ──────────────────────────────────────────────────────────
save_figure_tex(
    "eu_bohatstvi_mapa",
    caption=(
        f"Majetkové nerovnosti: top 10\,\%, EU, do {ds.latest_year}). "
        "Šedá = data nedostupná."
    ),
    label="fig:eu_bohatstvi_mapa",
    width=r"0.95\linewidth",
    cite_key="oecd_hfcs_wealth_top10_PC",
)

print("Done.")
