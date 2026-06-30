r"""
Tertiary education attainment -- timeline.

Share of population aged 25--64 with tertiary education (ISCED 5--8).

Data source: Eurostat ``edat_lfse_03``
  Dimensions: freq.sex.age.unit.isced11.geo
  Filter: A.T.Y25-64.PC.ED5-8.<geo>

Output
------
  pics/python/vyhled_vzdelani_vyvoj.pdf
  latex/texparts/python/vyhled_vzdelani_vyvoj.tex

Run
---
    python analyses/vyhled_vzdelani.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style_pgf, savefig_pgf, save_figure_tex_pgf, add_pgf_tooltips
from statout.timeline import timeline, EU27 as _EU27

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2004
HIGHLIGHT = ["CZ"]

CITE_KEY = "eurostat_edat_lfse_03_ED58"

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
# edat_lfse_03: Population by educational attainment level
# Dimensions: freq.sex.age.unit.isced11.geo
path = fetch_eurostat(
    "edat_lfse_03",
    "A.T.Y25-64.PC.ED5-8.",
    start_period=START_YEAR,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="Terciární vzdělání (25--64)",
    unit="%",
    source_url="Eurostat/edat_lfse_03",
)

print(f"Countries: {len(ds.countries)}  |  Years: {ds.years[0]}--{ds.years[-1]}")

# ── 3. Timeline figure ────────────────────────────────────────────────────────
STRINGS = {
    "title": "Podíl obyvatel s terciárním vzděláním (25--64 let)",
    "ylabel": r"podíl s ISCED 5--8 [\%]",
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

# ── PGF tooltips & geo labels ───────────────────────────────────────────
_pivot_edu = (
    ds.df[ds.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(fig.axes[0], _pivot_edu, fmt="{:.1f}")
_bg_edu = sorted(set(_EU27) - set(COUNTRIES))
_pivot_edu_bg = (
    ds.df[ds.df["geo"].isin(_bg_edu)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(fig.axes[0], _pivot_edu_bg, fmt="{:.1f}")
for _child in fig.axes[0].get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in COUNTRIES:
            _child.set_text(f"\\acs{{geo-{_txt}}}")

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "vyhled_vzdelani_vyvoj", strings=STRINGS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "vyhled_vzdelani_vyvoj",
    caption=(
        f"Podíl obyvatel s~terciárním vzděláním (ISCED 5--8, věk 25--64 let), "
        f"vybrané země \\acs{{EU}}, {ds.years[0]}--{ds.years[-1]}."
    ),
    label="fig:vyhled_vzdelani_vyvoj",
    resizebox_width=r"\linewidth",
    cite_key=CITE_KEY,
    strings=STRINGS,
)

print("Done.")
