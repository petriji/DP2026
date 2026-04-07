r"""
Income GINI coefficient timeline – CZ, AT, DE, DK, PL, SK.

Presents the long-run trend in income inequality (Gini of equivalised
disposable income) for six reference countries.  CZ has one of the lowest
Gini values in the EU — but this is used as a protiargument: low Gini at a
low median income level means equality in relative poverty, not prosperity.

Data source: Eurostat, ``ilc_di12``
  Gini coefficient of equivalised disposable income.
  Dimensions: freq · unit · indunit · geo
  Filter: freq=A, unit=TOTAL, indunit=GINI_HND.

Output
------
  pics/python/gini_income_timeline.pdf
  latex/texparts/python/gini_income_timeline.tex  ← \input{} this in main.tex

Run
---
    python analyses/gini_income_timeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.timeline import timeline

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
GEO = "+".join(COUNTRIES)
START_YEAR = 2003
HIGHLIGHT = ["CZ"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# ilc_di12: Gini coefficient of equivalised disposable income
# Dimensions: freq · unit · indunit · geo
path = fetch_eurostat(
    "ilc_di12",
    f"A.TOTAL.GINI_HND.{GEO}",
    start_period=START_YEAR,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="Giniho koeficient",
    unit="",
    source_url="Eurostat/ilc_di12",
)

print(f"Countries: {ds.countries}  |  Years: {ds.years[0]}–{ds.years[-1]}")

# ── 3. Timeline figure ────────────────────────────────────────────────────────
fig = timeline(
    ds,
    countries=COUNTRIES,
    title="Giniho koeficient příjmové nerovnosti",
    ylabel="Giniho koeficient (disponibilní příjem)",
    highlight=HIGHLIGHT,
    annotate_last=True,
    show_eu_avg=True,
)

ax = fig.axes[0]
ax.set_ylim(20, 40)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "gini_income_timeline", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "gini_income_timeline",
    caption=(
        f"Vývoj Giniho koeficientu disponibilního příjmu domácností, "
        f"{START_YEAR}--{ds.years[-1]}."
    ),
    label="fig:gini_income_timeline",
    width=r"0.95\linewidth",
    cite_key="eurostat_ilc_di12",
)

print("Done.")
