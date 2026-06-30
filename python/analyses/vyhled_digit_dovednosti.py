r"""
Digital skills – EU map (above-basic level, individuals 16–74).

Data source: Eurostat ``isoc_sk_dskl_i21``
  Dimensions: freq.ind_type.indic_is.unit.geo
  I_DSK2_AB = individuals with above-basic overall digital skills
  IND_TOTAL = all individuals (16–74)
  PC_IND = percentage of individuals

Output
------
  pics/python/vyhled_digit_dovednosti_mapa.pdf
  latex/texparts/python/vyhled_digit_dovednosti_mapa.tex

Run
---
    python analyses/vyhled_digit_dovednosti.py
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

CITE_KEY = "eurostat_isoc_sk_dskl_i21_AB"

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
# isoc_sk_dskl_i21: Individuals' level of digital skills (from 2021)
# Dimensions: freq.ind_type.indic_is.unit.geo
path = fetch_eurostat(
    "isoc_sk_dskl_i21",
    "A.IND_TOTAL.I_DSK2_AB.PC_IND.",
    start_period=2021,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="Digitální dovednosti (nad základní)",
    unit="% jednotlivců",
    source_url="Eurostat/isoc_sk_dskl_i21",
)

print(f"Countries: {len(ds.countries)}  |  Years: {ds.years}")
print(f"Display year (latest): {ds.latest_year}")

# ── 3. Choropleth map ────────────────────────────────────────────────────────
fig = choropleth(
    ds,
    year=ds.latest_year,
    title=f"Digitální dovednosti nad základní úrovní ({ds.latest_year})",
    colorbar_label="podíl jednotlivců [%]",
    cmap="RdYlGn",
    vmin=0,
    vmax=70,
    label_countries=True,
    fill_latest=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "vyhled_digit_dovednosti_mapa")

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "vyhled_digit_dovednosti_mapa",
    caption=(
        f"Podíl jednotlivců s~nadprůměrnými digitálními dovednostmi, "
        f"EU mapa, {ds.latest_year}."),
    label="fig:vyhled_digit_dovednosti_mapa",
    resizebox_width=r"0.92\linewidth",
    cite_key=CITE_KEY,
    strings={},
)

print("Done.")
