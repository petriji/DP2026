r"""
Cross-border labour mobility – CZ and EU comparators.

Three figures illustrating how Czech workers commute across national borders,
expressed as % of the employed workforce (PC_EMP) — normalised to remove
country- and region-size effects.

Data source: Eurostat, ``lfst_r_lfe2ecomm``
  Employed persons commuting to work by country of work and NUTS 2 region.
  Dimensions: freq · unit · wstatus · wrkplace · age · sex · geo
  Key filter values (verified from CSV on first download):
    unit     = PC_ACT   (% of employed; may also appear as PC_EMP — checked at runtime)
    wrkplace = FOR       (working in a foreign country; may be ABROAD / ABRD)
    age      = TOTAL or Y_GE15
    sex      = T

Figures
-------
A  ``cross_border_commuting_timeline``
    Line chart: % of employed working abroad, CZ / AT / DE / DK / PL / SK, all available years.

B  ``cross_border_commuting_map``
    EU choropleth: % of employed working abroad by country, latest year.

C  ``cross_border_commuting_nuts2``
    CZ NUTS2 choropleth: % of employed working abroad by region of residence,
    with AT / DE / SK / PL NUTS2 as grey geographic context.

Output
------
  pics/python/cross_border_commuting_timeline.pdf
  pics/python/cross_border_commuting_map.pdf
  pics/python/cross_border_commuting_nuts2.pdf
  latex/texparts/python/cross_border_commuting_timeline.tex
  latex/texparts/python/cross_border_commuting_map.tex
  latex/texparts/python/cross_border_commuting_nuts2.tex

Run
---
    cd python && python analyses/cross_border_commuting.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.cm as mcm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import geopandas as gpd
from shapely.geometry import box as _shapely_box

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.fetch import fetch, fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, cm2in, savefig, save_figure_tex
from statout.timeline import timeline

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
GEO_6 = "+".join(COUNTRIES)
HIGHLIGHT = ["CZ"]
START_YEAR = 2005

_GISCO_NUTS_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_20M_2021_3035.geojson"
)
# EPSG:3035 bounding box around CZ and immediate neighbours
_CZ_XLIM = (4_150_000, 5_150_000)
_CZ_YLIM = (2_600_000, 3_350_000)
# Wider box for EU overview map
_EU_XLIM = (2_500_000, 7_100_000)
_EU_YLIM = (1_400_000, 5_500_000)

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# Download all geo (NUTS2 + national aggregates), all sex/age combos.
# We post-filter after inspecting the column names.
print("Downloading lfst_r_lfe2ecomm …")
path = fetch_eurostat(
    "lfst_r_lfe2ecomm",
    start_period=START_YEAR,
)

# ── 2. Inspect columns and build filters ─────────────────────────────────────
raw = pd.read_csv(path, nrows=5, comment="#")
print("Columns:", list(raw.columns))

# Re-read full CSV (skip lines starting with #)
df = pd.read_csv(path, comment="#")
df.columns = [c.strip().upper() for c in df.columns]

# Identify the dimension for unit (% employed)
unit_candidates = [c for c in df.columns if "UNIT" in c]
wrkplace_candidates = [c for c in df.columns if any(k in c for k in ["WRKPLC", "WRKPLACE", "WSTATUS"])]
sex_candidates = [c for c in df.columns if "SEX" in c]
age_candidates = [c for c in df.columns if "AGE" in c]
geo_col = next((c for c in df.columns if c in ("GEO", "REF_AREA")), None)
val_col = next((c for c in df.columns if c in ("OBS_VALUE", "VALUE")), None)
time_col = next((c for c in df.columns if c in ("TIME_PERIOD", "TIME")), None)

print(f"  unit cols: {unit_candidates}")
print(f"  wrkplace cols: {wrkplace_candidates}")
print(f"  sex cols: {sex_candidates}")
print(f"  age cols: {age_candidates}")
print(f"  geo={geo_col}, val={val_col}, time={time_col}")

# ── 3. Filter to: total sex, working abroad, % of employed ───────────────────

def _first_val(df: pd.DataFrame, col_list: list[str], keywords: list[str]) -> str | None:
    """Return first value in col_list[0] that matches one of the keywords."""
    if not col_list:
        return None
    vals = df[col_list[0]].dropna().unique()
    for kw in keywords:
        matches = [v for v in vals if kw.upper() in str(v).upper()]
        if matches:
            return str(matches[0])
    return None

unit_val     = _first_val(df, unit_candidates,    ["PC_ACT", "PC_EMP", "PC"])
wrkplace_val = _first_val(df, wrkplace_candidates, ["FOR", "ABROAD", "ABRD"])
sex_val      = _first_val(df, sex_candidates,      ["T", "TOTAL"])
age_val      = _first_val(df, age_candidates,      ["TOTAL", "Y_GE15", "Y15-74"])

print(f"  Selected: unit={unit_val}, wrkplace={wrkplace_val}, sex={sex_val}, age={age_val}")

mask = pd.Series([True] * len(df), index=df.index)
if unit_val and unit_candidates:
    mask &= df[unit_candidates[0]].astype(str).str.upper() == unit_val.upper()
if wrkplace_val and wrkplace_candidates:
    mask &= df[wrkplace_candidates[0]].astype(str).str.upper() == wrkplace_val.upper()
if sex_val and sex_candidates:
    mask &= df[sex_candidates[0]].astype(str).str.upper() == sex_val.upper()
if age_val and age_candidates:
    mask &= df[age_candidates[0]].astype(str).str.upper() == age_val.upper()

filt = df[mask].copy()
if val_col:
    filt[val_col] = pd.to_numeric(filt[val_col], errors="coerce")
filt = filt.dropna(subset=[val_col] if val_col else [])
print(f"  Filtered rows: {len(filt)}  |  geo values (sample): {filt[geo_col].unique()[:10]}")

# Standardise column names for Dataset
filt = filt.rename(columns={geo_col: "geo", time_col: "time", val_col: "value"})
filt["time"] = filt["time"].astype(str).str[:4].astype(int)
filt = filt[["geo", "time", "value"]].dropna()

ds = Dataset(filt, name="Přeshraniční dojíždění", unit="% zaměstnaných",
             source_url="Eurostat/lfst_r_lfe2ecomm")

# ── Figure A — Timeline (national-level rows only, 2-char geo codes) ─────────
print("\nFigure A: timeline …")
nat = filt[filt["geo"].str.len() == 2].copy()
ds_nat = Dataset(nat, name="Přeshraniční dojíždění", unit="% zaměstnaných",
                 source_url="Eurostat/lfst_r_lfe2ecomm")

if not ds_nat.df.empty and len(ds_nat.countries) >= 2:
    fig_a = timeline(
        ds_nat,
        countries=COUNTRIES,
        title="Přeshraniční pracovní dojíždění do zahraničí",
        ylabel="% zaměstnaných pracujících v\u00a0zahraničí",
        highlight=HIGHLIGHT,
        annotate_last=True,
        show_eu_avg=False,
        background_eu=True,
    )
    savefig(fig_a, "cross_border_commuting_timeline", out_dir=LATEX_PICS_DIR)
    yr_min = nat["time"].min()
    yr_max = nat["time"].max()
    save_figure_tex(
        "cross_border_commuting_timeline",
        caption=f"Přeshraniční pracovní dojíždění, vývoj {yr_min}--{yr_max}.",
        label="fig:cross_border_commuting_timeline",
        width=r"0.95\linewidth",
        cite_keys="eurostat_lfst_r_lfe2ecomm",
    )

# ── Figure B — EU map ─────────────────────────────────────────────────────────
print("\nFigure B: EU map …")
try:
    nuts_path = fetch(_GISCO_NUTS_URL, suffix=".geojson")
    nuts_all = gpd.read_file(nuts_path)
    nuts0 = nuts_all[nuts_all["LEVL_CODE"] == 0].copy()

    nat2 = filt[filt["geo"].str.len() == 2].copy()
    latest_nat = nat2["time"].max()
    snap_nat = nat2[nat2["time"] == latest_nat].copy()

    merged_eu = nuts0.merge(snap_nat[["geo", "value"]], left_on="NUTS_ID",
                            right_on="geo", how="left")

    fig_b, ax_b = plt.subplots(figsize=cm2in(15, 11))
    vmin_b, vmax_b = 0, snap_nat["value"].quantile(0.95)
    cmap_b = plt.colormaps["YlOrRd"]
    norm_b = mcolors.Normalize(vmin=vmin_b, vmax=vmax_b)

    for _, row in merged_eu.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue
        val = row["value"]
        color = cmap_b(norm_b(val)) if pd.notna(val) else "#CCCCCC"
        gpd.GeoSeries([row.geometry]).plot(
            ax=ax_b, color=color, edgecolor="white", linewidth=0.4,
        )

    sm_b = mcm.ScalarMappable(cmap=cmap_b, norm=norm_b)
    sm_b.set_array([])
    cbar_b = fig_b.colorbar(sm_b, ax=ax_b, fraction=0.03, pad=0.02)
    cbar_b.set_label("% zaměstnaných pracujících v zahraničí", fontsize=FONT_SIZE)
    cbar_b.ax.tick_params(labelsize=FONT_SIZE - 1)
    ax_b.set_xlim(_EU_XLIM)
    ax_b.set_ylim(_EU_YLIM)
    ax_b.axis("off")
    ax_b.set_title(
        f"Přeshraniční pracovní dojíždění v\u00a0EU ({latest_nat})\n"
        "% zaměstnaných pracujících v\u00a0zahraničí",
        fontsize=FONT_SIZE,
    )
    fig_b.tight_layout()

    savefig(fig_b, "cross_border_commuting_map", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "cross_border_commuting_map",
        caption=f"Přeshraniční pracovní dojíždění, EU27, {latest_nat}.",
        label="fig:cross_border_commuting_map",
        width=r"0.85\linewidth",
        cite_keys="eurostat_lfst_r_lfe2ecomm",
    )
    print(f"  Figure B done ({latest_nat}).")
except Exception as exc:
    print(f"  Figure B skipped: {exc}")

# ── Figure C — CZ NUTS2 choropleth ───────────────────────────────────────────
print("\nFigure C: CZ NUTS2 choropleth …")
try:
    nuts_path = fetch(_GISCO_NUTS_URL, suffix=".geojson")
    nuts_all = gpd.read_file(nuts_path)
    nuts2_all = nuts_all[nuts_all["LEVL_CODE"] == 2].copy()
    nuts2_all["CNTR_CODE"] = nuts2_all["NUTS_ID"].str[:2]

    nuts2_data = filt[filt["geo"].str.len() == 4].copy()
    latest_nuts2 = nuts2_data["time"].max()
    snap_nuts2 = nuts2_data[nuts2_data["time"] == latest_nuts2].copy()

    merged_cz = nuts2_all.merge(
        snap_nuts2[["geo", "value"]], left_on="NUTS_ID", right_on="geo", how="left",
    )

    fig_c, ax_c = plt.subplots(figsize=cm2in(15, 11))

    # Grey neighbours
    nbrs = merged_cz[merged_cz["CNTR_CODE"].isin(["AT", "DE", "PL", "SK"])]
    nbrs.plot(ax=ax_c, color="#DDDDDD", edgecolor="white", linewidth=0.4)

    # CZ regions
    cz_nuts2 = merged_cz[merged_cz["CNTR_CODE"] == "CZ"].copy()
    bbox_cz = _shapely_box(_CZ_XLIM[0], _CZ_YLIM[0], _CZ_XLIM[1], _CZ_YLIM[1])
    cz_nuts2["geometry"] = cz_nuts2["geometry"].intersection(bbox_cz)

    cz_vals = cz_nuts2["value"].dropna()
    vmin_c = cz_vals.min() if not cz_vals.empty else 0
    vmax_c = cz_vals.max() if not cz_vals.empty else 5
    cmap_c = plt.colormaps["YlOrRd"]
    norm_c = mcolors.Normalize(vmin=vmin_c, vmax=vmax_c)

    for _, row in cz_nuts2.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue
        val = row["value"]
        color = cmap_c(norm_c(val)) if pd.notna(val) else "#CCCCCC"
        gpd.GeoSeries([row.geometry]).plot(
            ax=ax_c, color=color, edgecolor="white", linewidth=0.5,
        )
        centroid = row.geometry.centroid
        if pd.notna(val):
            ax_c.text(
                centroid.x, centroid.y,
                f"{row['NUTS_ID']}\n{val:.1f}\u00a0%",
                ha="center", va="center",
                fontsize=FONT_SIZE - 2, color="black",
            )

    sm_c = mcm.ScalarMappable(cmap=cmap_c, norm=norm_c)
    sm_c.set_array([])
    cbar_c = fig_c.colorbar(sm_c, ax=ax_c, fraction=0.03, pad=0.02)
    cbar_c.set_label("% zaměstnaných pracujících v zahraničí", fontsize=FONT_SIZE)
    cbar_c.ax.tick_params(labelsize=FONT_SIZE - 1)
    ax_c.set_xlim(_CZ_XLIM)
    ax_c.set_ylim(_CZ_YLIM)
    ax_c.axis("off")
    ax_c.set_title(
        f"ČR NUTS2: přeshraniční dojíždění ({latest_nuts2})\n"
        "% zaměstnaných pracujících v\u00a0zahraničí",
        fontsize=FONT_SIZE,
    )
    fig_c.tight_layout()

    savefig(fig_c, "cross_border_commuting_nuts2", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "cross_border_commuting_nuts2",
        caption=f"Přeshraniční dojíždění, regiony NUTS2, ČR, {latest_nuts2}.",
        label="fig:cross_border_commuting_nuts2",
        width=r"0.85\linewidth",
        cite_keys="eurostat_lfst_r_lfe2ecomm",
    )
    print(f"  Figure C done ({latest_nuts2}).")
except Exception as exc:
    print(f"  Figure C skipped: {exc}")

print("\nDone.")
