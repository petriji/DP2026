r"""
Trade union density trend -- CZ, AT, DE, DK, PL, SK.

Data source: OECD AIAS ICTWSS (via OECD Stats API, dataset ``TUD``)
  Trade union density = share of wage and salary earners who are
  members of a trade union.

Output
------
  pics/stav_hustota_vyvoj.pdf
  latex/texparts/stav_hustota_vyvoj.tex  ← \input{} this in main.tex

Run
---
    python analyses/stav_hustota_vyvoj.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.style import apply_style, savefig, save_figure_tex
from statout.timeline import timeline
from analyses._shared_data import load_union_density

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 1993   # post-transition baseline for all six countries
HIGHLIGHT = ["CZ"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Load data ──────────────────────────────────────────────────────────────
ds = load_union_density(start_period=START_YEAR)

print(f"Countries: {len(ds.countries)}  |  Years: {ds.years[0]}--{ds.years[-1]}")

# ── 3. Timeline figure (full history, grey cloud) ─────────────────────────────
fig = timeline(
    ds,
    countries=COUNTRIES,
    title="Hustota odborových organizací",
    ylabel="hustota odborů [% zaměstnanců]",
    highlight=HIGHLIGHT,
    annotate_last=True,
    show_eu_avg=False,
    background_eu=True,
)
fig.axes[0].set_xlim(START_YEAR, 2025)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "stav_hustota_vyvoj", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "stav_hustota_vyvoj",
    caption=(
        f"Vývoj hustoty odborových organizací, vybrané země EU, "
        f"{START_YEAR}--{ds.years[-1]}."
    ),
    label="fig:stav_hustota_vyvoj",
    width=r"\linewidth",
    cite_key="oecd_aias_ictwss_TUD_pct",
)

# ── 6. Second variant: 2004--latest (cropped x-axis) ──────────────────────────
YEAR_2004 = 2004

fig2 = timeline(
    ds,
    countries=COUNTRIES,
    title=f"Hustota odborových organizací ({YEAR_2004}--{ds.years[-1]})",
    ylabel="hustota odborů [% zaměstnanců]",
    highlight=HIGHLIGHT,
    annotate_last=True,
    label_offsets={"PL": (4, -10)},
    show_eu_avg=False,
    background_eu=True,
)
fig2.axes[0].set_xlim(2004, 2025)
fig2.axes[0].set_ylim(0, 80)

savefig(fig2, "stav_hustota_vyvoj_2004", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "stav_hustota_vyvoj_2004",
    caption=(
        f"Vývoj hustoty odborových organizací, vybrané země EU, "
        f"2004--{ds.years[-1]}."
    ),
    label="fig:stav_hustota_vyvoj_2004",
    width=r"\linewidth",
    cite_key="oecd_aias_ictwss_TUD_pct",
)

print("Done.")
