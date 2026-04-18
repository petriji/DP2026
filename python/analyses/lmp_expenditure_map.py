r"""
Labour Market Policy (LMP) expenditure choropleth map of Europe.

Data source: OECD LMPEXP (Labour Market Policy Expenditure)
  Programme LMP_20T70 = active measures (cat. 2–7); UNIT_MEASURE PT_B1GQ = % of GDP.
  (Eurostat lmp_expsumm was discontinued; OECD covers same EU countries.)

Output
------
  pics/python/lmp_expenditure_map.pdf
  latex/texparts/python/lmp_expenditure_map.tex

Run
---
    python analyses/lmp_expenditure_map.py
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
    title=f"Výdaje na aktivní politiku zaměstnanosti ({ds.latest_year})",
    colorbar_label="Výdaje na APZ (% HDP)",
    cmap="RdYlGn",
    vmin=0,
    vmax=2.0,
    label_countries=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "lmp_expenditure_map", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "lmp_expenditure_map",
    caption=f"Výdaje na APZ jako podíl HDP, EU mapa, {ds.latest_year}.",
    label="fig:lmp_expenditure_map",
    width=r"0.92\linewidth",
    cite_keys="oecd_lmpexp",
)

print("Done.")
