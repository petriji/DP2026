r"""
Trade union density trend – CZ, AT, DE, DK, PL, SK.

Data source: OECD AIAS ICTWSS (via OECD Stats API, dataset ``TUD``)
  Trade union density = share of wage and salary earners who are
  members of a trade union.

Output
------
  pics/union_density_trend.pdf
  latex/texparts/union_density_trend.tex  ← \input{} this in main.tex

Run
---
    python analyses/union_density_trend.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_oecd
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.timeline import timeline

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
# OECD uses ISO 3166-1 alpha-3 codes
OECD_FILTER = "CZE+AUT+DEU+DNK+POL+SVK.../all"
START_YEAR = 1993   # post-transition baseline for all six countries
HIGHLIGHT = ["CZ"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# TUD dataset columns (OECD Stats CSV format):
#   LOCATION, INDICATOR (TUD), SUBJECT, MEASURE, FREQUENCY, TIME, Value
path = fetch_oecd("TUD", OECD_FILTER, start_period=START_YEAR)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_oecd_csv(
    path,
    name="Hustota odborů",
    unit="%",
    source_url="OECD AIAS ICTWSS / TUD",
    filters={"INDICATOR": "TUD"},
)

# Keep only the six target countries
ds.df = ds.df[ds.df["geo"].isin(COUNTRIES)].copy()

print(f"Countries: {ds.countries}  |  Years: {ds.years[0]}–{ds.years[-1]}")

# ── 3. Timeline figure ────────────────────────────────────────────────────────
fig = timeline(
    ds,
    countries=COUNTRIES,
    title="Hustota odborových organizací – vývoj",
    ylabel="Hustota odborů (% zaměstnaných)",
    highlight=HIGHLIGHT,
    annotate_last=True,
    show_eu_avg=False,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "union_density_trend", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "union_density_trend",
    caption=(
        f"Vývoj hustoty odborových organizací (podíl odborově organizovaných "
        f"zaměstnanců), {START_YEAR}--{ds.years[-1]}."
    ),
    label="fig:union_density_trend",
    width=r"0.95\linewidth",
    cite_key="oecd_aias_ictwss",
)

print("Done.")
