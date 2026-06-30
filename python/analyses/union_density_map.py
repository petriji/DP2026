r"""
Trade union density choropleth map of Europe.

Data source: OECD AIAS ICTWSS (dataset ``TUD``)
  Trade union density = share of wage and salary earners who are
  members of a trade union (%).

Output
------
  pics/python/union_density_map.pdf
  latex/texparts/python/union_density_map.tex

Run
---
    python analyses/union_density_map.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_oecd
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.map_europe import choropleth

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# Fetch full TUD dataset (no country filter — filter in Python below).
path = fetch_oecd("TUD", start_period=2010)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_oecd_csv(
    path,
    name="Hustota odborů",
    unit="%",
    source_url="OECD AIAS ICTWSS / TUD",
)

# Drop the OECD aggregate row
ds.df = ds.df[ds.df["geo"] != "OECD"].copy()

print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}–{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
fig = choropleth(
    ds,
    year=ds.latest_year,
    title=f"Hustota odborových organizací ({ds.latest_year})",
    colorbar_label="hustota odborů [% zaměstnaných]",
    cmap="RdYlGn",
    vmin=0,
    vmax=80,
    label_countries=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "union_density_map", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "union_density_map",
    caption=(
        f"Hustota odborových organizací, EU mapa, {ds.latest_year}."
    ),
    label="fig:union_density_map",
    width=r"0.92\linewidth",
    cite_key="oecd_aias_ictwss_TUD_pct",
)

print("Done.")
