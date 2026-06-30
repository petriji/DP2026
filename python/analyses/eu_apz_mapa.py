r"""
Labour Market Policy (LMP) expenditure choropleth map of Europe.

Data source: OECD LMPEXP (Labour Market Policy Expenditure)
  Programme LMP_20T70 = active measures (cat. 2–7); UNIT_MEASURE PT_B1GQ = % of GDP.
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
from stattool.style import apply_style, savefig, save_figure_tex
from statout.map_europe import choropleth
from analyses._shared_data import load_lmp_active

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Load data ──────────────────────────────────────────────────────────────
ds = load_lmp_active()

print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}–{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
fig = choropleth(
    ds,
    year=ds.latest_year,
    title=f"Výdaje na APZ ({ds.latest_year})",
    colorbar_label="výdaje na APZ [% HDP]",
    cmap="RdYlGn",
    vmin=0,
    vmax=2.0,
    label_countries=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "eu_apz_mapa", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "eu_apz_mapa",
    caption=f"Výdaje na APZ (% HDP), EU mapa, {ds.latest_year}.",
    label="fig:eu_apz_mapa",
    width=r"0.92\linewidth",
    cite_keys="oecd_lmpexp",
)

print("Done.")
