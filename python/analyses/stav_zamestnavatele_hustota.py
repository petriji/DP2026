r"""
Employer organisation density -- map + timeline.

Data source: OECD / AIAS ICTWSS v2 (variable ``ED``)
  ED = share of employees working in firms that are members
  of an employer organisation (%).

Output
------
  pics/python/stav_zamestnavatele_hustota_mapa.pdf
  pics/python/stav_zamestnavatele_hustota_vyvoj.pdf
  latex/texparts/python/stav_zamestnavatele_hustota_mapa.tex
  latex/texparts/python/stav_zamestnavatele_hustota_vyvoj.tex

Run
---
    python analyses/stav_zamestnavatele_hustota.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.data_quality import warn_non_target_year
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    add_pgf_tooltips,
    apply_geo_labels_pgf,
)
from statout.map_europe import choropleth
from statout.timeline import timeline, EU27 as _EU27
from analyses._shared_data import load_employer_density

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2000
HIGHLIGHT = ["CZ"]

CITE_KEY = "oecd_aias_ictwss_ED_pct"

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Load data ──────────────────────────────────────────────────────────────
ds = load_employer_density(start_period=START_YEAR)

print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}--{ds.years[-1]}")
print(f"Display year (latest): {ds.latest_year}")
warn_non_target_year(source="OECD AIAS ICTWSS ED", year=ds.latest_year, context="Employer-organisation density map")

# ── 2. Choropleth map ────────────────────────────────────────────────────────
_values_map = (
    ds.df[ds.df["time"] <= ds.latest_year]
    .sort_values("time").groupby("geo")["value"].last().to_dict()
)
_vmin_map = min(_values_map.values())
_vmax_map = max(_values_map.values())

STRINGS_MAP = {
    "title": f"Hustota zaměstnavatelských organizací ({ds.latest_year})",
    "colorbar_label": r"hustota [\% zaměstnanců]",
}

fig_map = choropleth(
    ds,
    year=ds.latest_year,
    title=STRINGS_MAP["title"],
    colorbar_label=STRINGS_MAP["colorbar_label"],
    cmap="RdYlGn",
    vmin=_vmin_map,
    vmax=_vmax_map,
    label_countries=True,
    highlight_colorbar=HIGHLIGHT,
)

apply_geo_labels_pgf(fig_map.axes[0], halo=True, values=_values_map, tooltip_fmt="{:.1f}")

savefig_pgf(fig_map, "stav_zamestnavatele_hustota_mapa", strings=STRINGS_MAP)

save_figure_tex_pgf(
    "stav_zamestnavatele_hustota_mapa",
    caption=(
        f"Hustota zaměstnavatelských organizací, EU mapa, "
        f"{ds.latest_year}."),
    label="fig:stav_zamestnavatele_hustota_mapa",
    resizebox_width=r"\linewidth",
    cite_key=CITE_KEY,
    strings=STRINGS_MAP,
)

# ── 3. Timeline figure ───────────────────────────────────────────────────────
STRINGS_TL = {
    "title": "Zaměstnavatelská organizovanost",
    "ylabel": r"hustota zaměstnavatelských org. [\%]",
}

fig_tl = timeline(
    ds,
    countries=COUNTRIES,
    title=STRINGS_TL["title"],
    ylabel=STRINGS_TL["ylabel"],
    highlight=HIGHLIGHT,
    annotate_last=True,
    markers=True,
    show_eu_avg=False,
    background_eu=True,
)
fig_tl.axes[0].set_xlim(START_YEAR, 2025)
fig_tl.axes[0].set_ylim(0, 105)

# ── PGF tooltips & geo labels ───────────────────────────────────────────
_pivot_ed = (
    ds.df[ds.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(fig_tl.axes[0], _pivot_ed, fmt="{:.1f}")
_bg_ed = sorted(set(_EU27) - set(COUNTRIES))
_pivot_ed_bg = (
    ds.df[ds.df["geo"].isin(_bg_ed)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(fig_tl.axes[0], _pivot_ed_bg, fmt="{:.1f}")
for _child in fig_tl.axes[0].get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in COUNTRIES:
            _child.set_text(f"\\acs{{geo-{_txt}}}")

NUDGE_LABELS = [(c, rf"\acs{{geo-{c}}}") for c in COUNTRIES]
savefig_pgf(fig_tl, "stav_zamestnavatele_hustota_vyvoj", strings=STRINGS_TL, nudge_labels=NUDGE_LABELS)

save_figure_tex_pgf(
    "stav_zamestnavatele_hustota_vyvoj",
    caption=(
        f"Vývoj hustoty zaměstnavatelských organizací, vybrané země EU, "
        f"{START_YEAR}--{ds.years[-1]}."),
    label="fig:stav_zamestnavatele_hustota_vyvoj",
    resizebox_width=r"\linewidth",
    cite_key=CITE_KEY,
    strings=STRINGS_TL,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
