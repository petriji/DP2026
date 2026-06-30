r"""
Labour Market Policy (LMP) expenditure as % of GDP – CZ, AT, DE, DK, PL, SK.

Key message for the thesis: DK spends ~2 % of GDP on active labour-market
policy; CZ spends ~0.3 %.  The "flexicurity" triangle only works with
adequate income-support and re-skilling investment.

Data source: Eurostat, ``lmp_expsumm``
  LMP summary expenditure by type of action.
  Dimensions: freq · exptype · unit · geo
  Filter used: freq=A, exptype=LMP_TOT (total LMP), unit=PC_GDP.

Output
------
  pics/lmp_expenditure.pdf
  latex/texparts/lmp_expenditure.tex  ← \input{} this in main.tex

Run
---
    python analyses/lmp_expenditure.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.timeline import timeline

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
GEO = "+".join(COUNTRIES)
START_YEAR = 2004
HIGHLIGHT = ["CZ", "DK"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# lmp_expsumm: LMP expenditure summary (annual)
# exptype=LMP_TOT selects total LMP spending; unit=PC_GDP gives % of GDP.
path = fetch_eurostat(
    "lmp_expsumm",
    f"A.LMP_TOT.PC_GDP.{GEO}",
    start_period=START_YEAR,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="Výdaje na APZ",
    unit="% HDP",
    source_url="Eurostat/lmp_expsumm",
)

print(f"Countries: {ds.countries}  |  Years: {ds.years[0]}–{ds.years[-1]}")

# ── 3. Timeline figure ────────────────────────────────────────────────────────
fig = timeline(
    ds,
    countries=COUNTRIES,
    title="Výdaje na aktivní politiku zaměstnanosti (% HDP)",
    ylabel="Výdaje na aktivní politiku zaměstnanosti (% HDP)",
    highlight=HIGHLIGHT,
    annotate_last=True,
    show_eu_avg=False,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "lmp_expenditure", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "lmp_expenditure",
    caption=(
        f"Výdaje na aktivní politiku zaměstnanosti jako podíl HDP, "
        f"{START_YEAR}--{ds.years[-1]}."
    ),
    label="fig:lmp_expenditure",
    width=r"0.95\linewidth",
    cite_key="eurostat_lmp_expsumm",
)

print("Done.")
