r"""
Trade union density choropleth map of Europe.

Data source: OECD AIAS ICTWSS (dataset ``TUD``)
  Trade union density = share of wage and salary earners who are
  members of a trade union (%).

Output
------
  pics/python/eu_hustota_mapa.pdf
  latex/texparts/python/eu_hustota_mapa.tex

Run
---
    python analyses/eu_hustota_mapa.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.style import apply_style, savefig, save_figure_tex
from statout.map_europe import choropleth
from analyses._shared_data import load_union_density

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Load data ──────────────────────────────────────────────────────────────
ds = load_union_density(start_period=2010)

print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}–{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
fig = choropleth(
    ds,
    year=ds.latest_year,
    title=f"Hustota odborů ({ds.latest_year})",
    colorbar_label="hustota odborů [% zaměstnanců]",
    cmap="RdYlGn",
    vmin=0,
    vmax=80,
    label_countries=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "eu_hustota_mapa", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "eu_hustota_mapa",
    caption=(
        f"Hustota odborů, EU mapa, {ds.latest_year}."
    ),
    label="fig:eu_hustota_mapa",
    width=r"0.92\linewidth",
    cite_key="oecd_aias_ictwss_TUD_pct",
)

print("Done.")
