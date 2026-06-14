r"""
Top 1 % wealth share map — World Inequality Database (WID).

Downloads per-country bulk CSV files from wid.world and extracts the
household net wealth share of the top 1 % of adults (equal-split).

WID variable: ``shwealj992`` (share · hweal · equal-split · adults 992)
Percentile:   ``p99p100`` (top 1 %)
Values:        fractions in [0, 1] → multiplied by 100 to give percent.

Data source: World Inequality Database (WID) bulk CSV: https://wid.world/bulk_download/
Filter: variable == shwealj992, percentile == p99p100 (top 1 % share of net household wealth)

Output
------
  python/figures/eu_bohatstvi_top1_wid.pgf
  latex/texparts/figures/eu_bohatstvi_top1_wid.tex
  latex/texparts/python/eu_bohatstvi_top1_wid.tex

Run
---
    cd python && bash run.sh analyses/eu_bohatstvi_top1_wid.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR
from stattool.data_quality import warn_non_target_year, warn_years
from stattool.fetch import fetch
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    apply_geo_labels_pgf,
)
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────

# European countries to collect — EU-27 + Iceland, Norway, Switzerland, UK
# (for a complete-looking map). WID uses ISO 3166-1 alpha-2 codes.
COUNTRIES = [
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR",
    "GR", "HR", "HU", "IE", "IS", "IT", "LT", "LU", "LV", "MT", "NL",
    "NO", "PL", "PT", "RO", "SE", "SI", "SK", "CH", "GB",
]

WID_BASE_URL = "https://wid.world/bulk_download/WID_data_{cc}.csv"
WID_VARIABLE = "shwealj992"
WID_PERCENTILE = "p99p100"

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()


# ── 1. Download & parse WID per-country data ──────────────────────────────────

def _load_country(cc: str) -> pd.DataFrame | None:
    """Download WID CSV for *cc* and return filtered rows (top 1 % wealth share)."""
    url = WID_BASE_URL.format(cc=cc)
    try:
        path = fetch(url, suffix=".csv")
    except Exception as exc:
        print(f"  [{cc}] download failed: {exc}")
        return None
    try:
        df = pd.read_csv(
            path,
            sep=";",
            usecols=["country", "variable", "percentile", "year", "value"],
            dtype={"country": str, "variable": str, "percentile": str,
                   "year": int, "value": float},
        )
    except Exception as exc:
        print(f"  [{cc}] parse failed: {exc}")
        return None
    mask = (df["variable"] == WID_VARIABLE) & (df["percentile"] == WID_PERCENTILE)
    sub = df[mask].copy()
    if sub.empty:
        print(f"  [{cc}] no {WID_VARIABLE}/{WID_PERCENTILE} data")
        return None
    return sub


rows = []
print("Downloading WID per-country data …")
for cc in COUNTRIES:
    sub = _load_country(cc)
    if sub is not None:
        rows.append(sub)
        latest = sub.sort_values("year").iloc[-1]
        print(f"  [{cc}] latest year {int(latest['year'])}: "
              f"{latest['value'] * 100:.1f} %")

if not rows:
    raise RuntimeError("No WID data downloaded — check network access.")

raw = pd.concat(rows, ignore_index=True)

# ── 2. Build tidy Dataset (latest year per country, values in %) ──────────────
latest_rows = (
    raw.sort_values("year")
       .groupby("country", as_index=False)
       .last()
)
latest_rows = latest_rows.rename(columns={"country": "geo", "year": "time"})
latest_rows["value"] = latest_rows["value"] * 100.0  # fraction → percent

display_year = int(latest_rows["time"].max())
print(f"\nDisplay year (global max): {display_year}")
print(f"Countries with data: {sorted(latest_rows['geo'].tolist())}")
warn_non_target_year(source="WID shwealj992", year=display_year, context="Top 1% wealth-share WID map reference year")
warn_years("WID shwealj992", latest_rows["time"].tolist(), context="Top 1% wealth-share WID map country fill years")

ds = Dataset(
    latest_rows[["geo", "time", "value"]],
    name="Podíl top 1 % na čistém jmění (WID)",
    unit="%",
    source_url="https://wid.world/bulk_download/",
)

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
_values = latest_rows.set_index("geo")["value"].to_dict()
_vmin = min(_values.values())
_vmax = max(_values.values())

STRINGS = {
    "title": f"Podíl top 1\\,\\% domácností na čistém jmění (WID, do {display_year})",
    "colorbar_label": r"podíl top 1\,\% na čistém jmění [\%]",
}

fig = choropleth(
    ds,
    year=display_year,
    title=STRINGS["title"],
    colorbar_label=STRINGS["colorbar_label"],
    cmap="RdYlGn_r",
    vmin=_vmin,
    vmax=_vmax,
    label_countries=True,
    fill_latest=True,
    highlight_colorbar=["CZ"],
)

apply_geo_labels_pgf(fig.axes[0], halo=True, values=_values, tooltip_fmt="{:.1f}")

# ── 4. Save ───────────────────────────────────────────────────────────────────
savefig_pgf(fig, "eu_bohatstvi_top1_wid", strings=STRINGS)

# ── 5. LaTeX snippet ──────────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_bohatstvi_top1_wid",
    caption=f"Podíl top 1\\,\\% domácností na čistém jmění, \\acs{{geo-EU27}} mapa, do~{display_year}",
    label="fig:eu_bohatstvi_top1_wid",
    resizebox_width=r"\linewidth",
    cite_key="wid_world_shweal",
    strings=STRINGS,
)

print("\nDone: eu_bohatstvi_top1_wid")
