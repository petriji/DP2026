r"""
Income per capita in PPS – choropleth map of Europe.

Shows GDP per capita in purchasing power standards (EU27=100) across EU
member states.  Illustrates the large gap in real living standards between
western and central-eastern Europe despite nominal GDP convergence.

Data source: Eurostat, ``nama_10_pc``
  GDP per capita in PPS (EU27_2020=100).
  Dimensions: freq · unit · na_item · geo
  Filter: freq=A, unit=PC_EU27_2020_HAB_MPPS_CP, na_item=B1GQ.

Output
------
  pics/python/eu_prijem_pps.pdf
  latex/texparts/python/eu_prijem_pps.tex  ← \input{} this in main.tex

Run
---
    python analyses/eu_prijem_pps.py
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

START_YEAR = 2015

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
# nama_10_pc: GDP and main components per capita (PPS)
# unit=PC_EU27_2020_HAB_MPPS_CP → % of EU27 average (chain-linked volume)
# No geo filter → all countries for the map
path = fetch_eurostat(
    "nama_10_pc",
    "A.PC_EU27_2020_HAB_MPPS_CP.B1GQ.",
    start_period=START_YEAR,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="HDP na obyvatele v PPS",
    unit="EU27=100",
    source_url="Eurostat/nama_10_pc",
)

print(f"Loaded: {len(ds.countries)} countries, {ds.years[0]}–{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
fig = choropleth(
    ds,
    year=ds.latest_year,
    title=f"HDP na obyvatele v PPS ({ds.latest_year})",
    colorbar_label="HDP na obyvatele [PPS, EU27 = 100]",
    cmap="RdYlGn",
    vmin=40,
    vmax=160,
    label_countries=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "eu_prijem_pps")

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_prijem_pps",
    caption=(
        f"HDP na obyvatele v~PPS (EU27\\,=\\,100), EU mapa, {ds.latest_year}."
    ),
    label="fig:eu_prijem_pps",
    resizebox_width=r"0.92\linewidth",
    cite_key="eurostat_nama_10_pc_PPS_EU27eq100",
    strings={},
)

print("Done.")
