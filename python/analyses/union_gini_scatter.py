r"""
Union density × Gini coefficient scatter – EU27 countries.

Shows the inverse correlation between trade union density and income
inequality (Gini on disposable income), underpinning the thesis argument
that strong collective bargaining reduces wage dispersion.

Data sources:
  Trade union density (%):   OECD AIAS ICTWSS (TUD dataset)
  Gini coefficient:          Eurostat ``ilc_di12``
    Latest common year with data for both sources is used.

Output
------
  pics/union_gini_scatter.pdf
  latex/texparts/union_gini_scatter.tex  ← \input{} this in main.tex

Run
---
    python analyses/union_gini_scatter.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import COUNTRY_COLORS, LATEX_PICS_DIR
from stattool.fetch import fetch_oecd, fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.scatter import scatter_xy

# ── Parameters ────────────────────────────────────────────────────────────────

# EU27 member states (ISO 3166-1 alpha-3 for OECD filter)
EU27_OECD = (
    "AUT+BEL+BGR+HRV+CYP+CZE+DNK+EST+FIN+FRA+DEU+GRC"
    "+HUN+IRL+ITA+LVA+LTU+LUX+MLT+NLD+POL+PRT+ROU+SVK"
    "+SVN+ESP+SWE"
)
START_YEAR = 2010
HIGHLIGHT_COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download union density ─────────────────────────────────────────────────
# TUD dataset – all EU27 members
path_tud = fetch_oecd(
    "TUD",
    f"{EU27_OECD}.../all",
    start_period=START_YEAR,
)

ds_tud = Dataset.from_oecd_csv(
    path_tud,
    name="Hustota odborů",
    unit="%",
    source_url="OECD AIAS ICTWSS / TUD",
    filters={"INDICATOR": "TUD"},
)

# ── 2. Download Gini coefficient ──────────────────────────────────────────────
# ilc_di12: Gini coefficient of equivalised disposable income
# Dimensions: freq · unit · indunit · geo
# filter: freq=A, unit=TOTAL, indunit=GINI_HND (Gini, disposable income)
path_gini = fetch_eurostat(
    "ilc_di12",
    "A.TOTAL.GINI_HND.",    # no geo filter → all EU countries
    start_period=START_YEAR,
)

ds_gini = Dataset.from_sdmx_csv(
    path_gini,
    name="Giniho koeficient",
    unit="",
    source_url="Eurostat/ilc_di12",
)

# ── 3. Scatter plot ───────────────────────────────────────────────────────────
# scatter_xy uses the latest common year by default
fig = scatter_xy(
    ds_tud,
    ds_gini,
    title="Hustota odborů vs. Giniho koeficient (EU27)",
    xlabel="Hustota odborů (%)",
    ylabel="Giniho koeficient (disponibilní příjem)",
    trendline=True,
    label_points=True,
    highlight=HIGHLIGHT_COUNTRIES,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "union_gini_scatter", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
# Determine the year actually plotted
common_years = sorted(set(ds_tud.years) & set(ds_gini.years))
display_year = common_years[-1] if common_years else "?"

save_figure_tex(
    "union_gini_scatter",
    caption=(
        f"Hustota odborových organizací (osa x) a Giniho koeficient disponibilního "
        f"příjmu (osa y) pro členské státy EU27, {display_year}. "
        f"Přerušovaná čára – regrese OLS."
    ),
    label="fig:union_gini_scatter",
    width=r"0.85\linewidth",
    cite_key="oecd_aias_ictwss",
)

print("Done.")
