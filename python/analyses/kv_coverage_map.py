r"""
Collective bargaining coverage choropleth map of Europe.

Data source: OECD AIAS ICTWSS (dataset ``CBC``)
  Measure ERB: share of salaried employees covered by collective bargaining
  agreements (%).
  Note: not all EU27 countries are OECD members; Bulgaria, Croatia, Cyprus,
  Malta and Romania are absent from this dataset.

Output
------
  pics/python/kv_coverage_map.pdf
  latex/texparts/python/kv_coverage_map.tex

Run
---
    python analyses/kv_coverage_map.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_oecd
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.map_europe import choropleth

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# CBC: Collective Bargaining Coverage, single measure ERB (% of salaried).
# Download full dataset — no geo filter needed; from_oecd_csv handles column
# detection for both old (LOCATION/Value) and new (REF_AREA/OBS_VALUE) formats.
path = fetch_oecd("CBC", start_period=2010)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_oecd_csv(
    path,
    name="Pokrytí kolektivním vyjednáváním",
    unit="%",
    source_url="OECD AIAS ICTWSS / CBC",
)

# Drop the OECD aggregate row (not an individual country)
ds.df = ds.df[ds.df["geo"] != "OECD"].copy()

print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}–{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
fig = choropleth(
    ds,
    year=ds.latest_year,
    title=f"Pokrytí kolektivním vyjednáváním ({ds.latest_year})",
    colorbar_label="pokrytí KV [% zaměstnanců]",
    cmap="RdYlGn",
    vmin=0,
    vmax=100,
    label_countries=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "kv_coverage_map", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "kv_coverage_map",
    caption=(
        f"Pokrytí kolektivním vyjednáváním~-- podíl zaměstnanců, "
        f"na~které se vztahuje kolektivní smlouva, {ds.latest_year}. "
        r"Data nejsou dostupná pro nečlenské státy OECD (BG, HR, CY, MT, RO)."
    ),
    label="fig:kv_coverage_map",
    width=r"0.92\linewidth",
    cite_key="oecd_aias_ictwss_CBC_ERB_pct",
)

print("Done.")
