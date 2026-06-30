r"""
Tax wedge choropleth map of Europe.

Data source: Eurostat, earn_nt_taxwedge
  Tax wedge at average wage (100 % AW), single person, no children.
  Unit: % of total labour costs.

Output
------
  pics/tax_wedge_map.pdf
  latex/texparts/tax_wedge_map.tex  ← \input{} this in main.tex

Run
---
    python analyses/tax_wedge_map.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.map_europe import choropleth

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# Full dataset – no geo filter so all European countries appear on the map.
# earn_nt_taxwedge: simple 2-dim dataset (freq, geo).
# Omit the path filter to download all countries at once.
path = fetch_eurostat("earn_nt_taxwedge", start_period=2015)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="Daňový klín",
    unit="%",
    source_url="https://ec.europa.eu/eurostat – earn_nt_taxwedge",
)
print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}–{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
fig = choropleth(
    ds,
    year=ds.latest_year,
    title=f"Daňový klín na průměrnou mzdu, {ds.latest_year}",
    colorbar_label="Daňový klín (% mzdových nákladů)",
    cmap="RdYlGn_r",
    vmin=25,
    vmax=55,
    label_countries=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "tax_wedge_map", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "tax_wedge_map",
    caption=(
        f"Daňový klín na průměrnou mzdu (100\\,\\% AW, bezdětný zaměstnanec), "
        f"{ds.latest_year}."
    ),
    label="fig:tax_wedge_map",
    width=r"0.92\linewidth",
    cite_key="eurostat_earn_nt_taxwedge",
)

print("Done.")
