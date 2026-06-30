r"""
Tax wedge choropleth map of Europe.

Data source: Eurostat, earn_nt_taxwedge
  Tax wedge at 67 % of average wage (AW), single person, no children.
  Unit: % of total labour costs.

Output
------
  pics/eu_danovy_klin.pdf
  latex/texparts/eu_danovy_klin.tex  ← \input{} this in main.tex

Run
---
    python analyses/eu_danovy_klin.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style_pgf, savefig_pgf, save_figure_tex_pgf
from statout.map_europe import choropleth

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

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
    title=f"Daňový klín (67 % průměrné mzdy, {ds.latest_year})",
    colorbar_label="daňový klín [% mzdových nákladů]",
    cmap="RdYlGn_r",
    label_countries=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "eu_danovy_klin")

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_danovy_klin",
    caption=(
        f"Daňový klín (67\\,\\% průměrné mzdy, \\% celkových nákladů práce), "
        f"EU mapa, {ds.latest_year}."
    ),
    label="fig:eu_danovy_klin",
    resizebox_width=r"0.92\linewidth",
    cite_key="eurostat_earn_nt_taxwedge_PC_AW100",
    strings={},
)

print("Done.")
