r"""
ICT-workforce share of women -- EU choropleth map.

Shows the share of female individuals (aged 16--74) who are employed in
ICT-related occupations. Used in the GPG-analysis section to illustrate that CZ women are under-
represented in ICT employment, which contributes to the structural GPG
through occupational segregation into lower-paying sectors.

Data source: Eurostat ``isoc_sks_itsps``
  Dimensions: freq · unit · sex · age · geo
  Filter: freq=A, unit=PC_IND, sex=F, age=Y16_74

Output
------
  python/figures/eu_ict_gender.pgf
  latex/texparts/figures/eu_ict_gender.tex   (hand-editable, git-tracked)
  latex/texparts/python/eu_ict_gender.tex    (one-line wrapper)

Run
---
    python analyses/eu_ict_gender.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from stattool.data_quality import warn_non_target_year, warn_years
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    apply_geo_labels_pgf,
)
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────

CITE_KEY = "eurostat_isoc_sks_itsps"
COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
# isoc_sks_itsps: ICT employment participation
# Dimensions: freq · unit · sex · age · geo
# Filter to: annual, % of individuals, females, 16–74 years, all geos.
path = fetch_eurostat(
    "isoc_sks_itsps",
    start_period=2015,
)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="Účast žen v ICT",
    unit="% žen",
    source_url="Eurostat/isoc_sks_itsps",
    filters={"unit": "PC", "sex": "F"},
)

print(f"Countries: {len(ds.countries)}  |  Years: {ds.years}")
print(f"Display year (latest): {ds.latest_year}")
warn_non_target_year(source="Eurostat isoc_sks_itsps", year=ds.latest_year, context="Women in ICT map reference year")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
_years_used = ds.df.sort_values("time").groupby("geo")["time"].last().to_dict()
warn_years("Eurostat isoc_sks_itsps", _years_used.values(), context="Women in ICT map country fill years")
_values = (
    ds.df[ds.df["time"] <= ds.latest_year]
    .sort_values("time").groupby("geo")["value"].last().to_dict()
)
_vmax = max(_values.values())

NUDGE_LABELS = [(c, c) for c in COUNTRIES]

STRINGS = {
    "title": f"Podíl žen na zaměstnanosti v ICT ({ds.latest_year})",
    "colorbar_label": r"podíl žen (16--74 let) [\%]",
}

fig = choropleth(
    ds,
    year=ds.latest_year,
    title=STRINGS["title"],
    colorbar_label=STRINGS["colorbar_label"],
    cmap="RdYlGn",
    vmin=0,
    vmax=_vmax,
    label_countries=True,
    fill_latest=True,
    highlight_colorbar=COUNTRIES,
)

apply_geo_labels_pgf(fig.axes[0], halo=True, values=_values, tooltip_fmt="{:.1f}")

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "eu_ict_gender", strings=STRINGS, nudge_labels=NUDGE_LABELS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_ict_gender",
    caption=(
        r"Podíl žen (16--74 let) mezi zaměstnanci v~\acs{ICT}, "
        f"mapa Evropy, {ds.latest_year}."
    ),
    label="fig:eu_ict_gender",
    resizebox_width=r"\linewidth",
    cite_key=CITE_KEY,
    strings=STRINGS,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
