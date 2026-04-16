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
START_YEAR = 1993   # post-transition baseline for all six countries
HIGHLIGHT = ["CZ"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# Fetch full TUD dataset (no country filter — the old per-country filter
# expression is no longer accepted by stats.oecd.org; filter in Python below).
path = fetch_oecd("TUD", start_period=START_YEAR)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_oecd_csv(
    path,
    name="Hustota odborů",
    unit="%",
    source_url="OECD AIAS ICTWSS / TUD",
    filters={"INDICATOR": "TUD"},
)

# Drop OECD aggregate; keep all countries for the EU grey cloud
ds.df = ds.df[ds.df["geo"] != "OECD"].copy()

print(f"Countries: {len(ds.countries)}  |  Years: {ds.years[0]}–{ds.years[-1]}")

# ── 3. Timeline figure (full history, grey cloud) ─────────────────────────────
fig = timeline(
    ds,
    countries=COUNTRIES,
    title="Hustota odborových organizací – vývoj",
    ylabel="Hustota odborů (% zaměstnaných)",
    highlight=HIGHLIGHT,
    annotate_last=True,
    show_eu_avg=False,
    background_eu=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "union_density_trend", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "union_density_trend",
    caption=(
        f"Vývoj hustoty odborových organizací, {START_YEAR}--{ds.years[-1]}. "
        f"Šedé linie = ostatní evropské země."
    ),
    label="fig:union_density_trend",
    width=r"0.95\linewidth",
    cite_key="oecd_aias_ictwss_TUD_pct",
)

# ── 6. Second variant: 2004–latest (cropped x-axis) ──────────────────────────
YEAR_2004 = 2004

fig2 = timeline(
    ds,
    countries=COUNTRIES,
    title=f"Hustota odborových organizací ({YEAR_2004}–{ds.years[-1]})",
    ylabel="hustota odborů [% zaměstnanců]",
    highlight=HIGHLIGHT,
    annotate_last=True,
    label_offsets={"PL": (4, -10)},
    show_eu_avg=False,
    background_eu=True,
)
fig2.axes[0].set_xlim(2004, ds.years[-1])
fig2.axes[0].set_ylim(0, 80)

savefig(fig2, "union_density_trend_2004", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "union_density_trend_2004",
    caption=(
        f"Vývoj hustoty odborových organizací (podíl odborově organizovaných "
        f"zaměstnanců, \\%), 2004--{ds.years[-1]}. "
        f"Šedé linie = ostatní evropské země."
    ),
    label="fig:union_density_trend_2004",
    width=r"0.95\linewidth",
    cite_key="oecd_aias_ictwss_TUD_pct",
)

print("Done.")
