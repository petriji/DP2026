r"""
Labour Market Policy (LMP) expenditure choropleth map of Europe.

Data source: OECD LMPEXP (Labour Market Policy Expenditure)
  Programme _T = total LMP; UNIT_MEASURE PT_B1GQ = % of GDP.
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
from stattool.fetch import fetch_oecd
from stattool.dataset import Dataset, _OECD_ISO3_TO_ISO2
from stattool.style import apply_style, savefig, save_figure_tex
from statout.map_europe import choropleth

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
path = fetch_oecd("LMPEXP")

# ── 2. Parse ──────────────────────────────────────────────────────────────────
raw = pd.read_csv(path)
raw = raw[
    (raw["MEASURE"] == "EXP") &
    (raw["UNIT_MEASURE"] == "PT_B1GQ") &
    (raw["PROGRAMME"] == "_T")
].copy()
raw = raw.rename(columns={"REF_AREA": "geo", "TIME_PERIOD": "time", "OBS_VALUE": "value"})
raw["geo"] = raw["geo"].map(lambda x: _OECD_ISO3_TO_ISO2.get(str(x).upper(), str(x)))
raw = raw[["geo", "time", "value"]].dropna(subset=["value"])

# Drop OECD aggregate
raw = raw[raw["geo"] != "OECD"].copy()

ds = Dataset(raw, name="Výdaje na APZ", unit="% HDP", source_url="OECD/LMPEXP")

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
    vmax=3.5,
    label_countries=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "lmp_expenditure_map", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "lmp_expenditure_map",
    caption=(
        f"Výdaje na aktivní politiku zaměstnanosti jako podíl HDP (EU, "
        f"{ds.latest_year}; OECD LMPEXP, program \\_T = celkem)."
    ),
    label="fig:lmp_expenditure_map",
    width=r"0.92\linewidth",
    cite_key="oecd_lmpexp",
)

print("Done.")
