r"""
Example analysis: Eurostat at-risk-of-poverty-or-social-exclusion (AROPE) rate.

This script is self-contained: running it from scratch will
  1. download the data from Eurostat (ilc_peps01n) via fetch_eurostat(),
  2. parse it into a Dataset with from_sdmx_csv(),
  3. produce three figures and matching LaTeX snippets.

Outputs
-------
  pics/arope_map_<year>.pdf          + latex/texparts/arope_map_<year>.tex
  pics/arope_timeline_CE.pdf         + latex/texparts/arope_timeline_CE.tex
  pics/arope_groups.pdf              + latex/texparts/arope_groups.tex

Run from the python/ directory:
    python analyses/arope_example.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.map_europe import choropleth
from statout.timeline import timeline, timeline_groups

# ── 0. Global style ───────────────────────────────────────────────────────────
apply_style()

# ── 1. Download & parse ───────────────────────────────────────────────────────
# ilc_peps01n dimensions: freq, unit, age, sex, geo
# Filter to total (all ages, both sexes) for a single value per country/year.
path = fetch_eurostat(
    "ilc_peps01n",
    "A.PC.TOTAL.T.",          # freq=A, unit=PC, age=TOTAL, sex=T, geo=all
)

ds = Dataset.from_sdmx_csv(
    path,
    name="AROPE",
    unit="%",
    source_url="Eurostat/ilc_peps01n",
)

print(f"Countries: {len(ds.countries)}  |  Years: {ds.years[0]}–{ds.years[-1]}")

# ── 2. Figure A – Europe choropleth (latest year) ─────────────────────────────
map_name = f"arope_map_{ds.latest_year}"
fig_a = choropleth(
    ds,
    year=ds.latest_year,
    title=f"AROPE – ohrožení chudobou nebo sociálním vyloučením ({ds.latest_year})",
    colorbar_label="AROPE [%]",
    cmap="RdYlGn_r",
    vmin=0,
    vmax=40,
)
savefig(fig_a, map_name, out_dir=LATEX_PICS_DIR)
save_figure_tex(
    map_name,
    caption=(
        f"Podíl obyvatel ohrožených chudobou nebo sociálním vyloučením (AROPE), "
        f"{ds.latest_year}\\,\\%."
    ),
    label=f"fig:{map_name}",
    cite_key="eurostat_ilc_peps01n_PC_pop",
)

# ── 3. Figure B – Timeline for Central European countries ─────────────────────
V4_AND_NEIGHBOURS = ["CZ", "SK", "PL", "HU", "AT", "DE", "SI", "HR"]
fig_b = timeline(
    ds,
    countries=V4_AND_NEIGHBOURS,
    title="AROPE – vývoj ve střední Evropě",
    ylabel="AROPE [%]",
    highlight=["CZ"],
    background_eu=True,
)
savefig(fig_b, "arope_timeline_CE", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "arope_timeline_CE",
    caption=(
        "Vývoj míry ohrožení chudobou nebo sociálním vyloučením (AROPE) "
        f"ve vybraných zemích střední Evropy, {ds.years[0]}--{ds.years[-1]}."
    ),
    label="fig:arope_timeline_CE",
    cite_key="eurostat_ilc_peps01n_PC_pop",
)

# ── 4. Figure C – Country-group averages ──────────────────────────────────────
GROUPS = {
    "V4":   ["CZ", "SK", "PL", "HU"],
    "S-EU": ["SE", "FI", "DK", "NO", "IS"],
    "J-EU": ["IT", "GR", "ES", "PT"],
}
fig_c = timeline_groups(
    ds,
    GROUPS,
    title="AROPE – průměr podle skupin zemí",
    ylabel="AROPE [%]",
)
savefig(fig_c, "arope_groups", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "arope_groups",
    caption=(
        "Vývoj průměrné míry AROPE podle skupin zemí, "
        f"{ds.years[0]}--{ds.years[-1]}."
    ),
    label="fig:arope_groups",
    cite_key="eurostat_ilc_peps01n_PC_pop",
)

print(f"\nVšechny výstupy uloženy do {LATEX_PICS_DIR}")
