r"""
Income GINI coefficient timeline -- CZ, AT, DE, DK, PL, SK.

Presents the long-run trend in income inequality (Gini of equivalised
disposable income) for six reference countries.  CZ has one of the lowest
Gini values in the EU --- but this is used as a protiargument: low Gini at a
low median income level means equality in relative poverty, not prosperity.

Data source: Eurostat, ``ilc_di12``
  Gini coefficient of equivalised disposable income.
  Dimensions: freq · unit · indunit · geo
  Filter: freq=A, unit=TOTAL, indunit=GINI_HND.

Output
------
  pics/python/eu_gini_prijem.pdf
  latex/texparts/python/eu_gini_prijem.tex  ← \input{} this in main.tex

Run
---
    python analyses/eu_gini_prijem.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style_pgf, savefig_pgf, save_figure_tex_pgf, add_pgf_tooltips
from statout.timeline import timeline, EU27 as _EU27

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2003
HIGHLIGHT = ["CZ"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
# ilc_di12: Gini coefficient of equivalised disposable income
# Dimensions: freq · unit · indunit · geo
# Download all countries (trailing dot) for EU background cloud.
path = fetch_eurostat(
    "ilc_di12",
    "A.TOTAL.GINI_HND.",
    start_period=START_YEAR,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="Giniho koeficient",
    unit="",
    source_url="Eurostat/ilc_di12",
)

print(f"Countries: {ds.countries}  |  Years: {ds.years[0]}--{ds.years[-1]}")

# ── 3. Timeline figure ────────────────────────────────────────────────────────
STRINGS = {
    "title": "Giniho koeficient příjmové nerovnosti",
    "ylabel": "Giniho koeficient [0--100]",
}
fig = timeline(
    ds,
    countries=COUNTRIES,
    title=STRINGS["title"],
    ylabel=STRINGS["ylabel"],
    highlight=HIGHLIGHT,
    annotate_last=True,
    background_eu=True,
    show_eu_avg=True,
)

ax = fig.axes[0]
ax.set_ylim(15, 45)

# ── PGF tooltips & geo labels ─────────────────────────────────────────────────
_pivot = (
    ds.df[ds.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(ax, _pivot, fmt="{:.2f}")
_bg = sorted(set(_EU27) - set(COUNTRIES))
_pivot_bg = (
    ds.df[ds.df["geo"].isin(_bg)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(ax, _pivot_bg, fmt="{:.2f}")
for _child in ax.get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in COUNTRIES:
            _child.set_text(f"\\acs{{geo-{_txt}}}")

# ── 4. Save figure ────────────────────────────────────────────────────────────
# Nudge knobs: end-of-line country labels. Override LaTeX-side via
# \renewcommand\NudgeEuGiniPrijemCZ{-3pt} in latex/texparts/figures/eu_gini_prijem.tex
NUDGE_LABELS = [(c, rf"\acs{{geo-{c}}}") for c in COUNTRIES]
savefig_pgf(fig, "eu_gini_prijem", strings=STRINGS, nudge_labels=NUDGE_LABELS)

# ── 5. Write LaTeX snippet ───────────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_gini_prijem",
    caption=(
        f"Giniho koeficient disponibilního příjmu, vybrané země \\acs{{EU}}, {START_YEAR}--{ds.years[-1]}."),
    label="fig:eu_gini_prijem",
    resizebox_width=r"\linewidth",
    cite_key="eurostat_ilc_di12_Gini",
    strings=STRINGS,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
