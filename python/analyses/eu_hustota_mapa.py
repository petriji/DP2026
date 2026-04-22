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
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    apply_geo_labels_pgf,
)
from statout.map_europe import choropleth
from analyses._shared_data import load_union_density

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Load data ──────────────────────────────────────────────────────────────
ds = load_union_density(start_period=2010)

print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}--{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
_values = (
    ds.df[ds.df["time"] <= ds.latest_year]
    .sort_values("time").groupby("geo")["value"].last().to_dict()
)
_vmax = max(_values.values())

STRINGS = {
    "title": f"Hustota odborů ({ds.latest_year})",
    "colorbar_label": r"hustota odborů [\% zaměstnanců]",
}

fig = choropleth(
    ds,
    year=ds.latest_year,
    title=STRINGS["title"],
    colorbar_label=STRINGS["colorbar_label"],
    cmap="RdYlGn",
    vmin=0,
    vmax=_vmax,
    label_countries=True,
    highlight_colorbar=["CZ"],
)

apply_geo_labels_pgf(fig.axes[0], halo=True, values=_values, tooltip_fmt="{:.1f}")

savefig_pgf(fig, "eu_hustota_mapa", strings=STRINGS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_hustota_mapa",
    caption=(
        f"Hustota odborů, EU mapa, {ds.latest_year}."),
    label="fig:eu_hustota_mapa",
    resizebox_width=r"\linewidth",
    cite_key="oecd_aias_ictwss_TUD_pct",
    strings=STRINGS,
)

print("Done.")
