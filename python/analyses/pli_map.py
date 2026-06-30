r"""
Price Level Index choropleth – purchasing power variability across Europe.

Shows the GDP Price Level Index (PLI_EU27_2020.GDP, EU27=100) for each
European country.  A PLI below 100 means the country is cheaper than the EU27
average (wages/income in EUR buy *more* goods), above 100 means it is more
expensive.  The map illustrates the east–west purchasing power gap that
motivates PPS-adjusted comparisons throughout this thesis.

Data source: Eurostat ``prc_ppp_ind``
  Dimensions: freq · na_item · ppp_cat · geo
  Filter: A.PLI_EU27_2020.GDP.  (all geo)

Output
------
  pics/python/pli_map.pdf
  latex/texparts/python/pli_map.tex  ← \input{} this in main.tex

Run
---
    python analyses/pli_map.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────

START_YEAR = 2015

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# prc_ppp_ind: Price Level Indices (Eurostat)
# PLI_EU27_2020.GDP = GDP price level index, EU27_2020 = 100
# Trailing dot → all geo
path = fetch_eurostat(
    "prc_ppp_ind",
    "A.PLI_EU27_2020.GDP.",
    start_period=START_YEAR,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
raw = pd.read_csv(path)
raw = raw[["geo", "TIME_PERIOD", "OBS_VALUE"]].dropna(subset=["OBS_VALUE"])
raw.columns = ["geo", "time", "value"]
raw["time"] = raw["time"].astype(int)

ds = Dataset(
    raw,
    name="Index cenové hladiny (PLI)",
    unit="EU27=100",
    source_url="Eurostat/prc_ppp_ind",
)

print(f"Loaded: {len(ds.countries)} countries, {ds.years[0]}–{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
fig = choropleth(
    ds,
    year=ds.latest_year,
    title=f"Index cenové hladiny HDP ({ds.latest_year})",
    colorbar_label="PLI (EU27 = 100)",
    cmap="RdYlGn_r",   # red = expensive, green = cheap
    vmin=40,
    vmax=160,
    diverging=False,
    label_countries=True,
)

# ── 4. Save figure ─────────────────────────────────────────────────────────────
savefig(fig, "pli_map", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ─────────────────────────────────────────────────────
save_figure_tex(
    "pli_map",
    caption=(
        f"Index cenové hladiny HDP, EU mapa, {ds.latest_year}."
    ),
    label="fig:pli_map",
    width=r"0.92\linewidth",
    cite_key="eurostat_prc_ppp_ind_PLI_GDP",
)

print("Done.")
