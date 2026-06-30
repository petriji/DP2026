r"""
Employer organisation density – map + timeline.

Data source: OECD / AIAS ICTWSS v2 (variable ``ED``)
  ED = share of employees working in firms that are members
  of an employer organisation (%).

Output
------
  pics/python/stav_zamestnavatele_hustota_mapa.pdf
  pics/python/stav_zamestnavatele_hustota_vyvoj.pdf
  latex/texparts/python/stav_zamestnavatele_hustota_mapa.tex
  latex/texparts/python/stav_zamestnavatele_hustota_vyvoj.tex

Run
---
    python analyses/stav_zamestnavatele_hustota.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.style import apply_style, savefig, save_figure_tex
from statout.map_europe import choropleth
from statout.timeline import timeline
from analyses._shared_data import load_employer_density

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2000
HIGHLIGHT = ["CZ"]

CITE_KEY = "oecd_aias_ictwss_ED_pct"

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Load data ──────────────────────────────────────────────────────────────
ds = load_employer_density(start_period=START_YEAR)

print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}–{ds.years[-1]}")
print(f"Display year (latest): {ds.latest_year}")

# ── 2. Choropleth map ────────────────────────────────────────────────────────
fig_map = choropleth(
    ds,
    year=ds.latest_year,
    title=f"Hustota zaměstnavatelských organizací ({ds.latest_year})",
    colorbar_label="hustota [% zaměstnanců]",
    cmap="RdYlGn",
    vmin=0,
    vmax=100,
    label_countries=True,
)

savefig(fig_map, "stav_zamestnavatele_hustota_mapa", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "stav_zamestnavatele_hustota_mapa",
    caption=(
        f"Hustota zaměstnavatelských organizací, EU mapa, "
        f"{ds.latest_year}."
    ),
    label="fig:stav_zamestnavatele_hustota_mapa",
    width=r"0.92\linewidth",
    cite_key=CITE_KEY,
)

# ── 3. Timeline figure ───────────────────────────────────────────────────────
fig_tl = timeline(
    ds,
    countries=COUNTRIES,
    title="Hustota zaměstnavatelských organizací",
    ylabel="hustota zaměstnavatelských org. [%]",
    highlight=HIGHLIGHT,
    annotate_last=True,
    markers=True,
    show_eu_avg=False,
    background_eu=True,
)
fig_tl.axes[0].set_xlim(START_YEAR, 2025)
fig_tl.axes[0].set_ylim(0, 105)

savefig(fig_tl, "stav_zamestnavatele_hustota_vyvoj", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "stav_zamestnavatele_hustota_vyvoj",
    caption=(
        f"Vývoj hustoty zaměstnavatelských organizací, vybrané země EU, "
        f"{START_YEAR}--{ds.years[-1]}."
    ),
    label="fig:stav_zamestnavatele_hustota_vyvoj",
    width=r"0.95\linewidth",
    cite_key=CITE_KEY,
)

print("Done.")
