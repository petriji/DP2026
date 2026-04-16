r"""
Total Fertility Rate – timeline and EU choropleth.

Shows the long-run collapse and partial recovery of fertility in CZ relative
to selected European countries, plus a snapshot EU-wide choropleth.

Data source: Eurostat, demo_find
  indic_de = TOTFERRT  (total fertility rate, live births per woman)

Output
------
  pics/python/natality_tfr_timeline.pdf
  latex/texparts/python/natality_tfr_timeline.tex

  pics/python/natality_tfr_map.pdf
  latex/texparts/python/natality_tfr_map.tex

Run
---
    python analyses/natality_timeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR, FONT_SIZE
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.timeline import timeline
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "SK", "PL", "FR", "SE"]
START_YEAR = 1960

HIGHLIGHT = ["CZ"]

# Replacement-level fertility
REPLACEMENT = 2.1

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# demo_find dimensions: freq · indic_de · geo
# TOTFERRT = total fertility rate (live births per woman)
path = fetch_eurostat(
    "demo_find",
    "A.TOTFERRT.",
    start_period=START_YEAR,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="Úhrnná plodnost",
    unit="živě narozených na ženu",
    source_url="Eurostat/demo_find",
)

print(f"Loaded: {len(ds.countries)} countries, {ds.years[0]}–{ds.years[-1]}")
print(f"Latest year: {ds.latest_year}")

# Print CZ key data points for verification
cz = ds.df[ds.df["geo"] == "CZ"].set_index("time")["value"]
for yr in [1974, 1999, 2021, 2024]:
    if yr in cz.index:
        print(f"  CZ {yr}: {cz[yr]:.3f}")

# ── 3. Timeline figure ────────────────────────────────────────────────────────
fig = timeline(
    ds,
    countries=COUNTRIES,
    title="Úhrnná plodnost",
    ylabel="živě narozených na ženu",
    highlight=HIGHLIGHT,
    annotate_last=True,
    background_eu=True,
    show_eu_avg=True,
    label_offsets={
        "FR": (0, 4),
        "SE": (0, -6),
        "DE": (0, -6),
        "SK": (0, 4),
    },
)

ax = fig.axes[0]
ax.set_xlim(START_YEAR, ds.years[-1])

# Replacement-level reference line
ax.axhline(
    REPLACEMENT,
    color="gray",
    linewidth=0.9,
    linestyle="--",
    alpha=0.65,
    zorder=1,
)
ax.annotate(
    f"hladina prosté reprodukce ({REPLACEMENT})",
    xy=(ds.years[-1], REPLACEMENT),
    xytext=(-120, 5),
    textcoords="offset points",
    fontsize=FONT_SIZE,
    color="gray",
    alpha=0.9,
)

# Annotate CZ minimum (1999 post-communist trough)
cz_min_yr = int(cz.idxmin())
cz_min_val = cz.min()
ax.annotate(
    f"CZ\u00a0{cz_min_yr}: {cz_min_val:.2f}",
    xy=(cz_min_yr, cz_min_val),
    xytext=(10, -18),
    textcoords="offset points",
    fontsize=FONT_SIZE,
    arrowprops=dict(arrowstyle="-", color="#888888", lw=0.7),
)

# ── 4. Save figure A ──────────────────────────────────────────────────────────
savefig(fig, "natality_tfr_timeline", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "natality_tfr_timeline",
    caption=f"Úhrnná plodnost (TFR) ve vybraných zemích EU, {ds.years[0]}--{ds.years[-1]}.",
    label="fig:natality_tfr_timeline",
    width=r"0.95\linewidth",
    cite_keys="eurostat_demo_find",
)

print("Figure A done.")

# ── 5. Choropleth map ─────────────────────────────────────────────────────────
fig_map = choropleth(
    ds,
    year=ds.latest_year,
    title=f"Úhrnná plodnost v EU ({ds.latest_year})",
    colorbar_label="živě narozených na ženu",
    cmap="RdYlGn",
    vmin=1.0,
    vmax=2.1,
    label_countries=True,
)

# ── 6. Save figure B ──────────────────────────────────────────────────────────
savefig(fig_map, "natality_tfr_map", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "natality_tfr_map",
    caption=f"Úhrnná plodnost (TFR), EU mapa, {ds.latest_year}.",
    label="fig:natality_tfr_map",
    width=r"0.85\linewidth",
    cite_keys="eurostat_demo_find",
)

print("Figure B done.")
