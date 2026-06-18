r"""
Tax wedge choropleth map of Europe.

Data source: Eurostat, earn_nt_taxwedge
  Tax wedge at 67 % of average wage (AW), single person, no children.
  Unit: % of total labour costs.

Output
------
  pics/eu_danovy_klin.pdf
  latex/texparts/eu_danovy_klin.tex  ← \input{} this in main.tex

Run
---
    python analyses/eu_danovy_klin.py
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
    apply_geo_labels_pgf,
)
from statout.map_europe import choropleth

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
# Full dataset -- no geo filter so all European countries appear on the map.
# earn_nt_taxwedge: simple 2-dim dataset (freq, geo).
# Omit the path filter to download all countries at once.
path = fetch_eurostat("earn_nt_taxwedge", start_period=2015)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="Daňový klín",
    unit="%",
    source_url="https://ec.europa.eu/eurostat -- earn_nt_taxwedge",
)
print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}--{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
_values = (
    ds.df[ds.df["time"] <= ds.latest_year]
    .sort_values("time").groupby("geo")["value"].last().to_dict()
)
_vmin = min(_values.values())
_vmax = max(_values.values())

COUNTRIES = ["CZ", "DK", "AT", "DE", "PL", "SK"]
NUDGE_LABELS = [(c, c) for c in COUNTRIES]

STRINGS = {
    "title": f"Daňový klín (67\\,\\% průměrné mzdy, {ds.latest_year})",
    "colorbar_label": r"daňový klín [\% mzdových nákladů]",
}

fig = choropleth(
    ds,
    year=ds.latest_year,
    title=STRINGS["title"],
    colorbar_label=STRINGS["colorbar_label"],
    cmap="RdYlGn_r",
    vmin=_vmin,
    vmax=_vmax,
    label_countries=True,
    highlight_colorbar=COUNTRIES,
)

apply_geo_labels_pgf(fig.axes[0], halo=True, values=_values, tooltip_fmt="{:.1f}")

savefig_pgf(fig, "eu_danovy_klin", strings=STRINGS, nudge_labels=NUDGE_LABELS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_danovy_klin",
    caption=f"Daňový klín (\\SI{{67}}{{\\percent}} průměrné mzdy), \\acs{{geo-EU27}} mapa, {ds.latest_year}",
    label="fig:eu_danovy_klin",
    resizebox_width=r"\linewidth",
    cite_key="eurostat_earn_nt_taxwedge_PC_AW100",
    strings=STRINGS,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
