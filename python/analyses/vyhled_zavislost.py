r"""
Old-age dependency ratio -- choropleth map of Europe.

Shows the share of people aged 65+ relative to the working-age population
(20--64) across EU member states.  Underlines the demographic pressure on
pension systems and the relevance of active labour-market policy.

Data source: Eurostat, ``demo_pjanind``
  Old-age dependency ratio I (65+ / 20--64), age group OLDDEP1.
  Annual population indicator.

Output
------
  pics/python/vyhled_zavislost_mapa.pdf
  latex/texparts/python/vyhled_zavislost_mapa.tex  ← \input{} this in main.tex

Run
---
    python analyses/vyhled_zavislost_mapa.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style_pgf, savefig_pgf, save_figure_tex_pgf
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────

START_YEAR = 2010

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
# demo_pjanind: population structure indicators
# Dimensions: freq · indic_de · geo
# indic_de=OLDDEP1 → old-age dependency ratio I (65+ / 20--64)
path = fetch_eurostat(
    "demo_pjanind",
    "A.OLDDEP1.",
    start_period=START_YEAR,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="Koeficient stárnutí",
    unit="%",
    source_url="Eurostat/demo_pjanind",
)

print(f"Loaded: {len(ds.countries)} countries, {ds.years[0]}--{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
fig = choropleth(
    ds,
    year=ds.latest_year,
    title=f"Koeficient ekonomického zatížení seniory ({ds.latest_year})",
    colorbar_label="osoby 65+ / osoby 20--64 [%]",
    cmap="RdYlGn_r",
    vmin=20,
    vmax=60,
    label_countries=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "vyhled_zavislost_mapa")

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "vyhled_zavislost_mapa",
    caption=(
        f"Koeficient ekonomického zatížení seniory, evropské země, {ds.latest_year}."),
    label="fig:vyhled_zavislost_mapa",
    resizebox_width=r"0.92\linewidth",
    cite_key="eurostat_demo_pjanind",
    strings={},
)

print("Done.")
