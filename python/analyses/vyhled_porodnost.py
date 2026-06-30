r"""
Total Fertility Rate – timeline and EU choropleth.

Shows the long-run collapse and partial recovery of fertility in CZ relative
to selected European countries, plus a snapshot EU-wide choropleth.

Data source: Eurostat, demo_find
  indic_de = TOTFERRT  (total fertility rate, live births per woman)

Output
------
  pics/python/vyhled_porodnost_vyvoj.pdf
  latex/texparts/python/vyhled_porodnost_vyvoj.tex

  pics/python/vyhled_porodnost_mapa.pdf
  latex/texparts/python/vyhled_porodnost_mapa.tex

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
import pandas as pd
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    apply_geo_labels_pgf,
    add_pgf_tooltips,
)
from statout.timeline import timeline
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "SK", "PL", "FR", "SE"]
START_YEAR = 1960

HIGHLIGHT = ["CZ"]

# Replacement-level fertility
REPLACEMENT = 2.1

# ── Editable figure strings (also emitted as \def macros in wrapper .tex) ────
STRINGS_TIMELINE = {
    "title": r"\ac{TFR} -- úhrnná plodnost",
    "ylabel": "živě narozených na ženu",
    "annot_replacement": f"hladina prosté reprodukce (\\SI{{{REPLACEMENT}}}{{}})",
}
STRINGS_MAP = {
    "title_tpl": r"\ac{{TFR}} v~zemích \ac{{EU}} ({year})",
    "colorbar_label": "živě narozených na ženu",
}

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

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
    title=STRINGS_TIMELINE["title"],
    ylabel=STRINGS_TIMELINE["ylabel"],
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

# Tooltip on every data point (hover in Acrobat/Foxit shows country, year, value)
_pivot = (
    ds.df[ds.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(ax, _pivot, fmt="{:.2f}")

# Tooltip also on the grey EU-27 background lines (background_eu=True)
from statout.timeline import EU27 as _EU27
_bg = sorted(set(_EU27) - set(COUNTRIES))
_pivot_bg = (
    ds.df[ds.df["geo"].isin(_bg)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(ax, _pivot_bg, fmt="{:.2f}")

# Replace bare country codes with \acs{geo-XX} in annotations and legend
for child in ax.get_children():
    if hasattr(child, "get_text"):
        txt = child.get_text()
        if txt in COUNTRIES:
            child.set_text(f"\\acs{{geo-{txt}}}")
        elif txt == "EU27":
            child.set_text(r"\acs{geo-EU}")
legend = ax.get_legend()
if legend:
    for txt in legend.get_texts():
        code = txt.get_text()
        if code in COUNTRIES:
            txt.set_text(f"\\acs{{geo-{code}}}")
        elif code == "EU27":
            txt.set_text(r"\acs{geo-EU}")

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
    STRINGS_TIMELINE["annot_replacement"],
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
    f"\\acs{{geo-CZ}}\u00a0{cz_min_yr}: {cz_min_val:.2f}",
    xy=(cz_min_yr, cz_min_val),
    xytext=(10, -18),
    textcoords="offset points",
    fontsize=FONT_SIZE,
    arrowprops=dict(arrowstyle="-", color="#888888", lw=0.7),
)

# ── 4. Save figure A ──────────────────────────────────────────────────────────
savefig_pgf(fig, "vyhled_porodnost_vyvoj", out_dir=LATEX_PICS_DIR,
            strings=STRINGS_TIMELINE)

save_figure_tex_pgf(
    "vyhled_porodnost_vyvoj",
    caption=f"Úhrnná plodnost (TFR) ve vybraných zemích EU, {ds.years[0]}--{ds.years[-1]}.",
    label="fig:vyhled_porodnost_vyvoj",
    resizebox_width=r"0.95\linewidth",
    cite_keys="eurostat_demo_find",
    strings=STRINGS_TIMELINE,
)

print("Figure A done.")

# ── 5. Choropleth map ─────────────────────────────────────────────────────────
map_title = STRINGS_MAP["title_tpl"].format(year=ds.latest_year)
map_strings = {
    "title": map_title,
    "colorbar_label": STRINGS_MAP["colorbar_label"],
}
_values = (
    ds.df[ds.df["time"] <= ds.latest_year]
    .sort_values("time")
    .groupby("geo")["value"]
    .last()
    .to_dict()
)
fig_map = choropleth(
    ds,
    year=ds.latest_year,
    title=map_title,
    colorbar_label=STRINGS_MAP["colorbar_label"],
    cmap="RdYlGn",
    vmin=1.0,
    vmax=2.1,
    label_countries=True,
    highlight_colorbar=COUNTRIES,
)

# Replace bare ISO-2 codes with \acs{geo-XX}, add white halo, and hover tooltip.
apply_geo_labels_pgf(fig_map.axes[0], halo=True, values=_values, tooltip_fmt="{:.2f}")

# ── 6. Save figure B ──────────────────────────────────────────────────────────
savefig_pgf(fig_map, "vyhled_porodnost_mapa", out_dir=LATEX_PICS_DIR,
            strings=map_strings)

save_figure_tex_pgf(
    "vyhled_porodnost_mapa",
    caption=f"Úhrnná plodnost (TFR), evropské země, {ds.latest_year}.",
    label="fig:vyhled_porodnost_mapa",
    resizebox_width=r"0.85\linewidth",
    cite_keys="eurostat_demo_find",
    strings=map_strings,
)

print("Figure B done.")
