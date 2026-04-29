r"""
CB coverage × GDP per capita scatter -- OECD/EU countries.

Illustrates the correlation between collective bargaining coverage (% of
salaried workers covered) and GDP per capita in PPS (EU27=100), 
supporting the argument that higher CB coverage is associated with higher
living standards.

Data sources:
  CB coverage (%):             OECD CBC (ERB measure, % salaried employees)
  GDP per capita (PPS EU27=100): Eurostat ``nama_10_pc``

Output
------
  pics/python/eu_pokryti_prijem.pdf
  latex/texparts/python/eu_pokryti_prijem.tex

Run
---
    python analyses/eu_pokryti_prijem.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_oecd, fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    add_pgf_tooltips_scatter,
)
from statout.scatter import scatter_xy
from statout.timeline import EU27

# ── Parameters ─────────────────────────────────────────────────────────────────

HIGHLIGHT_COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2010

# ── 0. Style ──────────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download CB coverage ───────────────────────────────────────────────────
# CBC dataset: ERB = % salaried employees covered by collective agreements
path_cbc = fetch_oecd("CBC", start_period=START_YEAR)

ds_cbc = Dataset.from_oecd_csv(
    path_cbc,
    name="Pokrytí KV",
    unit="% salaried",
    source_url="OECD AIAS ICTWSS / CBC",
    filters={"MEASURE": "ERB"},
)

# ── 2. Download GDP per capita in PPS ─────────────────────────────────────────
# Eurostat nama_10_pc: GDP per capita in PPS (EU27_2020=100)
# No geo filter → all available countries for broadest scatter
path_gdp = fetch_eurostat(
    "nama_10_pc",
    "A.PC_EU27_2020_HAB_MPPS_CP.B1GQ.",
    start_period=START_YEAR,
)

ds_gdp = Dataset.from_sdmx_csv(
    path_gdp,
    name="HDP na obyvatele (EU27=100)",
    unit="EU27=100",
    source_url="Eurostat/nama_10_pc",
)

STRINGS = {
    "title": r"Korelace: pokrytí \acs{KV} a~\acs{HDP} na obyvatele",
    "xlabel": r"pokrytí \acs{KV} [\%]",
    "ylabel": r"\acs{HDP} na obyvatele [\acs{PPS}, \acs{geo-EU}27 = 100]",
}
# ── 3. Scatter plot ───────────────────────────────────────────────────────────────
fig = scatter_xy(
    ds_cbc,
    ds_gdp,
    title=STRINGS["title"],
    xlabel=STRINGS["xlabel"],
    ylabel=STRINGS["ylabel"],
    trendline=True,
    label_points=True,
    highlight=HIGHLIGHT_COUNTRIES,
    x_min=0,
    countries=sorted(EU27),
    year_tolerance=3,
)

# Hover tooltips on every data point (PGF/Acrobat).
ax = fig.axes[0]
add_pgf_tooltips_scatter(
    ax,
    fig._scatter_merged,  # type: ignore[attr-defined]
    fmt_x="{:.1f}",
    fmt_y="{:.1f}",
    label_x="pokrytí KV [%]",
    label_y="HDP/ob. [PPS]",
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "eu_pokryti_prijem", strings=STRINGS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
common_years = sorted(set(ds_cbc.years) & set(ds_gdp.years))
display_year = common_years[-1] if common_years else "?"

save_figure_tex_pgf(
    "eu_pokryti_prijem",
    caption=f"Pokrytí \\acs{{KS}} a~\\acs{{HDP}} na obyvatele v~paritě kupní síly (\\acs{{geo-EU27}} = 100), pro státy OECD/\\acs{{geo-EU}}, {display_year}. Přerušovaná čára -- regrese \\acs{{MNČ}}",
    label="fig:eu_pokryti_prijem",
    cite_key="oecd_aias_ictwss_CBC_ERB_pct,eurostat_nama_10_pc_PPS_EU27eq100",
    strings=STRINGS,
)

print("Done.")
