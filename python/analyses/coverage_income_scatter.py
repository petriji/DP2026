r"""
CB coverage × GDP per capita scatter – OECD/EU countries.

Illustrates the correlation between collective bargaining coverage (% of
salaried workers covered) and GDP per capita in PPS (EU27=100), 
supporting the argument that higher CB coverage is associated with higher
living standards.

Data sources:
  CB coverage (%):             OECD CBC (ERB measure, % salaried employees)
  GDP per capita (PPS EU27=100): Eurostat ``nama_10_pc``

Output
------
  pics/python/coverage_income_scatter.pdf
  latex/texparts/python/coverage_income_scatter.tex

Run
---
    python analyses/coverage_income_scatter.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_oecd, fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.scatter import scatter_xy
from statout.timeline import EU27

# ── Parameters ────────────────────────────────────────────────────────────────

HIGHLIGHT_COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2010

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

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

# ── 3. Scatter plot ───────────────────────────────────────────────────────────
fig = scatter_xy(
    ds_cbc,
    ds_gdp,
    title="Korelace: pokrytí KV a HDP na obyvatele",
    xlabel="pokrytí kolektivního vyjednávání [%]",
    ylabel="HDP na obyvatele (EU27 = 100)",
    trendline=True,
    label_points=True,
    highlight=HIGHLIGHT_COUNTRIES,
    x_min=0,
    countries=sorted(EU27),
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "coverage_income_scatter", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
common_years = sorted(set(ds_cbc.years) & set(ds_gdp.years))
display_year = common_years[-1] if common_years else "?"

save_figure_tex(
    "coverage_income_scatter",
    caption=(
        f"Vztah mezi pokrytím kolektivního vyjednávání (\\% zaměstnanců, osa x) "
        f"a HDP na obyvatele v paritě kupní síly (EU27\u00a0=\u00a0100, osa y) "
        f"pro státy OECD/EU, {display_year}. "
        f"Přerušovaná čára – regrese OLS."
    ),

    label="fig:coverage_income_scatter",
    width=r"0.85\linewidth",
    cite_key="oecd_aias_ictwss_CBC_ERB_pct,eurostat_nama_10_pc_PPS_EU27eq100",
)

print("Done.")
