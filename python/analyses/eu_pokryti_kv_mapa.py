r"""
Collective bargaining coverage choropleth map of Europe.

Data source: ICTWSS AdjCov (adjusted coverage) for most EU-27 countries;
  OECD CBC ERB for DE, SK, SI (low AdjCov data density).
  Note: Bulgaria, Croatia, Cyprus, Malta, Romania absent from both sources.

Output
------
  pics/python/eu_pokryti_kv_mapa.pdf
  latex/texparts/python/eu_pokryti_kv_mapa.tex

Run
---
    python analyses/eu_pokryti_kv_mapa.py
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
    apply_geo_labels_pgf,
)
from statout.map_europe import choropleth
from analyses._shared_data import load_cb_coverage

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Load ───────────────────────────────────────────────────────────────────
# AdjCov (ICTWSS) for most EU-27; CBC ERB (OECD) for DE, SK, SI where AdjCov
# data density is too low for a reliable series.
ds = load_cb_coverage(start_period=2010)

print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}--{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")
warn_non_target_year(source="ICTWSS AdjCov + OECD CBC ERB", year=ds.latest_year, context="Collective bargaining coverage map")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
_values = (
    ds.df[ds.df["time"] <= ds.latest_year]
    .sort_values("time").groupby("geo")["value"].last().to_dict()
)
_vmax = max(_values.values())

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
NUDGE_LABELS = [(c, c) for c in COUNTRIES]

STRINGS = {
    "title": f"Pokrytí kolektivními smlouvami ({ds.latest_year})",
    "colorbar_label": r"pokrytí \acs{KS} [\% zaměstnanců]",
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
    highlight_colorbar=COUNTRIES,
)

apply_geo_labels_pgf(fig.axes[0], halo=True, values=_values, tooltip_fmt="{:.0f}")

# ── 4. Save figure ───────────────────────────────────────────────────────────────
savefig_pgf(fig, "eu_pokryti_kv_mapa", strings=STRINGS, nudge_labels=NUDGE_LABELS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_pokryti_kv_mapa",
    caption=f"Pokrytí \\acpins{{KS}}, mapa Evropy, {ds.latest_year}",
    label="fig:eu_pokryti_kv_mapa",
    resizebox_width=r"\linewidth",
    cite_key="oecd_aias_ictwss_CBC_ERB_pct",
    strings=STRINGS,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
