r"""
Example analysis: Eurostat at-risk-of-poverty-or-social-exclusion (AROPE) rate.

This script is self-contained: running it from scratch will
  1. download the data from Eurostat (ilc_peps01n) via fetch_eurostat(),
  2. parse it into a Dataset with from_sdmx_csv(),
  3. produce three figures and matching LaTeX snippets.

Outputs
-------
  pics/arope_map_<year>.pdf          + latex/texparts/arope_map_<year>.tex
  pics/stav_arope_vyvoj.pdf         + latex/texparts/stav_arope_vyvoj.tex
  pics/stav_arope_skupiny.pdf              + latex/texparts/stav_arope_skupiny.tex

Run from the python/ directory:
    python analyses/arope_example.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    add_pgf_tooltips,
    apply_geo_labels_pgf,
)
from statout.map_europe import choropleth
from statout.timeline import timeline, timeline_groups, EU27 as _EU27

# ── 0. Global style ───────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download & parse ───────────────────────────────────────────────────────
# ilc_peps01n dimensions: freq, unit, age, sex, geo
# Filter to total (all ages, both sexes) for a single value per country/year.
path = fetch_eurostat(
    "ilc_peps01n",
    "A.PC.TOTAL.T.",          # freq=A, unit=PC, age=TOTAL, sex=T, geo=all
)

ds = Dataset.from_sdmx_csv(
    path,
    name="AROPE",
    unit="%",
    source_url="Eurostat/ilc_peps01n",
)

print(f"Countries: {len(ds.countries)}  |  Years: {ds.years[0]}--{ds.years[-1]}")

# ── 2. Figure A -- Europe choropleth (latest year) ─────────────────────────────
map_name = f"stav_arope_mapa_{ds.latest_year}"
_values_arope = (
    ds.df[ds.df["time"] <= ds.latest_year]
    .sort_values("time").groupby("geo")["value"].last().to_dict()
)
_vmin_arope = min(_values_arope.values())
_vmax_arope = max(_values_arope.values())

STRINGS_MAP = {
    "title": f"Míra \\acs{{AROPE}} ({ds.latest_year})",
    "colorbar_label": r"\acs{AROPE} [\%]",
}

fig_a = choropleth(
    ds,
    year=ds.latest_year,
    title=STRINGS_MAP["title"],
    colorbar_label=STRINGS_MAP["colorbar_label"],
    cmap="RdYlGn_r",
    vmin=_vmin_arope,
    vmax=_vmax_arope,
    highlight_colorbar=["CZ"],
)
apply_geo_labels_pgf(fig_a.axes[0], halo=True, values=_values_arope, tooltip_fmt="{:.1f}")
savefig_pgf(fig_a, map_name, strings=STRINGS_MAP)
save_figure_tex_pgf(
    map_name,
    caption=(
        f"Míra \\acs{{AROPE}} v~evropských zemích, {ds.latest_year}."),
    label=f"fig:{map_name}",
    cite_key="eurostat_ilc_peps01n_PC_pop",
    strings=STRINGS_MAP,
)

# ── 3. Figure B -- Timeline for Central European countries ──────────────────
V4_AND_NEIGHBOURS = ["CZ", "SK", "PL", "HU", "AT", "DE", "SI", "HR"]
STRINGS_TL_B = {
    "title": r"Míra \acs{AROPE}",
    "ylabel": r"míra \acs{AROPE} [\%]",
}
fig_b = timeline(
    ds,
    countries=V4_AND_NEIGHBOURS,
    title=STRINGS_TL_B["title"],
    ylabel=STRINGS_TL_B["ylabel"],
    highlight=["CZ"],
    background_eu=True,
)
# ── PGF tooltips & geo labels ───────────────────────────────────────────
_ax_b = fig_b.axes[0]
_pivot_arope_b = (
    ds.df[ds.df["geo"].isin(V4_AND_NEIGHBOURS)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax_b, _pivot_arope_b, fmt="{:.1f}")
_bg_arope = sorted(set(_EU27) - set(V4_AND_NEIGHBOURS))
_pivot_arope_b_bg = (
    ds.df[ds.df["geo"].isin(_bg_arope)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax_b, _pivot_arope_b_bg, fmt="{:.1f}")
for _child in _ax_b.get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in V4_AND_NEIGHBOURS:
            _child.set_text(f"\\acs{{geo-{_txt}}}")
savefig_pgf(fig_b, "stav_arope_vyvoj", strings=STRINGS_TL_B)
save_figure_tex_pgf(
    "stav_arope_vyvoj",
    caption=f"Vývoj míry \\acs{{AROPE}}, střední Evropa, {ds.years[0]}--{ds.years[-1]}.",
    label="fig:stav_arope_vyvoj",
    cite_key="eurostat_ilc_peps01n_PC_pop",
    strings=STRINGS_TL_B,
)

# ── 4. Figure C -- Country-group averages ──────────────────────────────────────
GROUPS = {
    "V4":   ["CZ", "SK", "PL", "HU"],
    "S-EU": ["SE", "FI", "DK", "NO", "IS"],
    "J-EU": ["IT", "GR", "ES", "PT"],
}
STRINGS_TL_C = {
    "title": r"Míra \acs{AROPE} podle skupin zemí",
    "ylabel": r"míra \acs{AROPE} [\%]",
}
fig_c = timeline_groups(
    ds,
    GROUPS,
    title=STRINGS_TL_C["title"],
    ylabel=STRINGS_TL_C["ylabel"],
)
# ── PGF tooltips (groups) ─────────────────────────────────────────────────
import pandas as _pd
_pivot_arope_c = _pd.DataFrame({
    _lbl: ds.df[ds.df["geo"].isin(_geos)].groupby("time")["value"].mean()
    for _lbl, _geos in GROUPS.items()
})
add_pgf_tooltips(fig_c.axes[0], _pivot_arope_c, fmt="{:.1f}")
savefig_pgf(fig_c, "stav_arope_skupiny", strings=STRINGS_TL_C)
save_figure_tex_pgf(
    "stav_arope_skupiny",
    caption=(
        "Vývoj míry \\acs{AROPE} podle skupin zemí, "
        f"{ds.years[0]}--{ds.years[-1]}."),
    label="fig:stav_arope_skupiny",
    cite_key="eurostat_ilc_peps01n_PC_pop",
    strings=STRINGS_TL_C,
)

print(f"\nVšechny výstupy uloženy do {LATEX_PICS_DIR}")
