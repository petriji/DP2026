r"""
Labour Market Policy (LMP) expenditure choropleth map of Europe.

Data source: OECD LMPEXP (Labour Market Policy Expenditure)
  Programme LMP_20T70 = active measures (cat. 2--7); UNIT_MEASURE PT_B1GQ = % of GDP.
  (Eurostat lmp_expsumm was discontinued; OECD covers same EU countries.)

Output
------
  pics/python/eu_apz_mapa.pdf
  latex/texparts/python/eu_apz_mapa.tex

Run
---
    python analyses/eu_apz_mapa.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    apply_geo_labels_pgf,
)
from statout.map_europe import choropleth
from analyses._shared_data import load_lmp_active

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Load data ──────────────────────────────────────────────────────────────
ds = load_lmp_active()

print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}--{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")

# Latest value per country (for tooltips and vmax)
_values = (
    ds.df[ds.df["time"] <= ds.latest_year]
    .sort_values("time").groupby("geo")["value"].last().to_dict()
)
_vmin = min(_values.values())
_vmax = max(_values.values())

STRINGS = {
    "title": f"Výdaje na \\acs{{APZ}} ({ds.latest_year})",
    "colorbar_label": r"výdaje na \acs{APZ} [\% \acs{HDP}]",
}

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
fig = choropleth(
    ds,
    year=ds.latest_year,
    title=STRINGS["title"],
    colorbar_label=STRINGS["colorbar_label"],
    cmap="RdYlGn",
    vmin=_vmin,
    vmax=_vmax,
    label_countries=True,
    highlight_colorbar=["CZ"],
)

apply_geo_labels_pgf(fig.axes[0], halo=True, values=_values, tooltip_fmt="{:.2f}")

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "eu_apz_mapa", strings=STRINGS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_apz_mapa",
    caption=f"Výdaje na \\acs{{APZ}} (\\% \\acs{{HDP}}), mapa Evropy, {ds.latest_year}",
    label="fig:eu_apz_mapa",
    resizebox_width=r"\linewidth",
    cite_keys="oecd_lmpexp",
    strings=STRINGS,
)

print("Done.")
