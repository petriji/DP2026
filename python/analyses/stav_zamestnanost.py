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

from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    add_pgf_tooltips,
)
from statout.timeline import timeline, EU27 as _EU27

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
GEO = "+".join(COUNTRIES)
START_YEAR = 2000
HIGHLIGHT = ["CZ"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

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
STRINGS = {
    "title": "Míra zaměstnanosti (20--64 let)",
    "ylabel": r"míra zaměstnanosti [\%]",
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

_ax = fig.axes[0]
_pivot = (
    ds.df[ds.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax, _pivot, fmt="{:.1f}")
_bg = sorted(set(_EU27) - set(COUNTRIES))
_pivot_bg = (
    ds.df[ds.df["geo"].isin(_bg)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax, _pivot_bg, fmt="{:.1f}")
for _child in _ax.get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in COUNTRIES:
            _child.set_text(f"\\acs{{geo-{_txt}}}")
        elif _txt == "EU27":
            _child.set_text(r"\acs{geo-EU}")
_legend = _ax.get_legend()
if _legend:
    for _t in _legend.get_texts():
        _code = _t.get_text()
        if _code in COUNTRIES:
            _t.set_text(f"\\acs{{geo-{_code}}}")
        elif _code == "EU27":
            _t.set_text(r"\acs{geo-EU}")

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "stav_zamestnanost", strings=STRINGS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "stav_zamestnanost",
    caption=(
        f"Míra zaměstnanosti (20--64 let), vybrané země EU, "
        f"{ds.years[0]}--{ds.years[-1]}."
    ),
    label="fig:stav_zamestnanost",
    resizebox_width=r"\linewidth",
    cite_key="eurostat_lfsi_emp_a",
    strings=STRINGS,
)

print("Done.")
