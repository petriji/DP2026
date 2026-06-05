r"""
Union density × Gini coefficient scatter -- EU27 countries.

Shows the inverse correlation between trade union density and income
inequality (Gini on disposable income), underpinning the thesis argument
that strong collective bargaining reduces wage dispersion.

Data sources:
  Trade union density (%):   OECD AIAS ICTWSS (TUD dataset)
  Gini coefficient:          Eurostat ``ilc_di12``
    Latest common year with data for both sources is used.

Output
------
  pics/korelace_hustota_gini.pdf
  latex/texparts/korelace_hustota_gini.tex  ← \input{} this in main.tex

Run
---
    python analyses/korelace_hustota_gini.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import COUNTRY_COLORS, LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import (
    add_pgf_tooltips_scatter,
    apply_style_pgf,
    load_angle_nudges_from_figure_tex,
    save_figure_tex_pgf,
    savefig_pgf,
)
from statout.scatter import scatter_xy
from statout.timeline import EU27
from analyses._shared_data import load_union_density

# ── Parameters ────────────────────────────────────────────────────────────────

# EU27 member states (ISO-2, as returned by from_oecd_csv and Eurostat)
EU27_ISO2 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}
START_YEAR = 2010
HIGHLIGHT_COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
LABEL_ANGLE_NUDGES = {geo: 21.8 for geo in HIGHLIGHT_COUNTRIES}

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Load union density ─────────────────────────────────────────────────────
ds_tud = load_union_density(start_period=START_YEAR)
# Keep all countries (not just EU27) for a fuller grey cloud and better trendline

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
STRINGS = {
    "title": r"Korelace: hustota odborů a Giniho koeficient (\acs{geo-EU}27)",
    "xlabel": r"hustota odborů [\%]",
    "ylabel": "Giniho koeficient [0–100]",
}
fig = scatter_xy(
    ds_tud,
    ds_gini,
    title=STRINGS["title"],
    xlabel=STRINGS["xlabel"],
    ylabel=STRINGS["ylabel"],
    trendline=True,
    label_points=True,
    highlight=HIGHLIGHT_COUNTRIES,
    x_min=0,
    countries=sorted(EU27),
    year_tolerance=3,
    label_angle_nudges=load_angle_nudges_from_figure_tex("korelace_hustota_gini", LABEL_ANGLE_NUDGES),
)

for _child in fig.axes[0].get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in HIGHLIGHT_COUNTRIES:
            _child.set_text(f"\\acs{{geo-{_txt}}}")

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "korelace_hustota_gini", strings=STRINGS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
# Determine the year actually plotted
common_years = sorted(set(ds_tud.years) & set(ds_gini.years))
display_year = common_years[-1] if common_years else "?"

save_figure_tex_pgf(
    "korelace_hustota_gini",
    caption=f"Hustota odborů a~příjmová nerovnost, \\acs{{EU}}, {display_year}.",
    label="fig:korelace_hustota_gini",
    resizebox_width=r"\linewidth",
    cite_keys=["oecd_aias_ictwss_TUD_pct", "eurostat_ilc_di12_Gini"],
    strings=STRINGS,
    angle_labels=LABEL_ANGLE_NUDGES,
)

print("Done.")
