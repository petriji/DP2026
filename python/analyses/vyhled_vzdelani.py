r"""
Tertiary education attainment – timeline.

Share of population aged 25–64 with tertiary education (ISCED 5–8).

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
from stattool.style import apply_style, savefig, save_figure_tex
from statout.timeline import timeline

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2004
HIGHLIGHT = ["CZ"]

CITE_KEY = "eurostat_edat_lfse_03_ED58"

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

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
    name="Terciární vzdělání (25–64)",
    unit="%",
    source_url="Eurostat/edat_lfse_03",
)

print(f"Countries: {len(ds.countries)}  |  Years: {ds.years[0]}–{ds.years[-1]}")

# ── 3. Timeline figure ────────────────────────────────────────────────────────
fig = timeline(
    ds,
    countries=COUNTRIES,
    title="Podíl obyvatel s terciárním vzděláním (25–64 let)",
    ylabel="podíl s ISCED 5–8 [%]",
    highlight=HIGHLIGHT,
    annotate_last=True,
    background_eu=True,
    show_eu_avg=True,
)

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "vyhled_vzdelani_vyvoj", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "vyhled_vzdelani_vyvoj",
    caption=(
        f"Podíl obyvatel s~terciárním vzděláním (ISCED 5--8, věk 25--64 let), "
        f"vybrané země EU, {ds.years[0]}--{ds.years[-1]}."
    ),
    label="fig:vyhled_vzdelani_vyvoj",
    width=r"0.95\linewidth",
    cite_key=CITE_KEY,
)

print("Done.")
