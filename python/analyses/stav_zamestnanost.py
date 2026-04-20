r"""
Employment rate (ages 20--64) timeline -- CZ, AT, DE, DK, PL, SK.

Shows the trend in total employment rates across the six reference countries
from the first available year to the latest available year. CZ's high employment rate relative
to its wage level is a key protiargument that the thesis addresses.

Data source: Eurostat, ``lfsi_emp_a``
  Employment rate by sex and age (annual), age group Y20-64.
  Dimensions: freq · indic_em · sex · age · unit · geo
  Filter: freq=A, indic_em=EMP_LFS, sex=T (total), age=Y20-64, unit=PC_POP (%).

Output
------
  pics/python/stav_zamestnanost.pdf
  latex/texparts/python/stav_zamestnanost.tex  ← \input{} this in main.tex

Run
---
    python analyses/stav_zamestnanost.py
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
START_YEAR = 2000
HIGHLIGHT = ["CZ"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# lfsi_emp_a: employment rate by sex and age
# Dimensions: freq · unit · sex · age · geo
path = fetch_eurostat(
    "lfsi_emp_a",
    "A.EMP_LFS.T.Y20-64.PC_POP.",
    start_period=START_YEAR,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="Míra zaměstnanosti",
    unit="%",
    source_url="Eurostat/lfsi_emp_a",
)

print(f"Countries: {ds.countries}  |  Years: {ds.years[0]}--{ds.years[-1]}")

# ── 3. Timeline figure ────────────────────────────────────────────────────────
fig = timeline(
    ds,
    countries=COUNTRIES,
    title="Míra zaměstnanosti (20--64 let)",
    ylabel="míra zaměstnanosti [%]",
    highlight=HIGHLIGHT,
    annotate_last=True,
    background_eu=True,
    show_eu_avg=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "stav_zamestnanost", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "stav_zamestnanost",
    caption=(
        f"Míra zaměstnanosti (20--64 let), vybrané země EU, "
        f"{ds.years[0]}--{ds.years[-1]}."
    ),
    label="fig:stav_zamestnanost",
    width=r"\linewidth",
    cite_key="eurostat_lfsi_emp_a",
)

print("Done.")
