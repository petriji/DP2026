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
    with AT / DE / SK / PL NUTS2 coloured by same indicator for comparison.
    Values are explicitly normalised: commuters_THOUS / employed_THOUS * 100.

Output
------
  pics/python/problemy_dojezdeni_vyvoj.pdf
  pics/python/problemy_dojezdeni_mapa.pdf
  pics/python/problemy_dojezdeni_nuts2.pdf
  latex/texparts/python/problemy_dojezdeni_vyvoj.tex
  latex/texparts/python/problemy_dojezdeni_mapa.tex
  latex/texparts/python/problemy_dojezdeni_nuts2.tex

Run
---
    cd python && python analyses/cross_border_commuting.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patheffects as mpe
import pandas as pd
import geopandas as gpd

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.fetch import fetch, fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    cm2in,
    savefig_pgf,
    save_figure_tex_pgf,
    add_pgf_tooltips,
    apply_geo_labels_pgf,
)
from statout.timeline import timeline, EU27
from statout.map_cz import choropleth_cz
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
GEO_6 = "+".join(COUNTRIES)
HIGHLIGHT = ["CZ"]
START_YEAR = 2005

_GISCO_NUTS_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_20M_2021_3035.geojson"
)

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

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
wrkplace_candidates = [c for c in df.columns if any(k in c for k in ["WRKPLC", "WRKPLACE", "WSTATUS", "C_WORK", "CWORK"])]
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

unit_val     = _first_val(df, unit_candidates,    ["PC_ACT", "PC_EMP", "PC", "THS_PER", "THOUS", "THS"])
wrkplace_val = _first_val(df, wrkplace_candidates, ["FOR", "ABROAD", "ABRD", "TOTAL"])
sex_val      = _first_val(df, sex_candidates,      ["T", "TOTAL"])
age_val      = _first_val(df, age_candidates,      ["Y20-64", "Y_GE15", "TOTAL", "Y15-74"])

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

# ── 3c. Top destination country per CZ NUTS2 region ─────────────────────────
# Finds which foreign country has the highest commuter count per CZ region
# at the latest available year, excluding aggregate rows (FOR/TOTAL).
_top_dest: dict[str, str] = {}
_cwork_col = next((c for c in df.columns if c in ("C_WORK", "CWORK")), None)
if _cwork_col is not None and geo_col and val_col and time_col:
    _AGG_VALS = {"FOR", "TOTAL", "ABROAD", "ABRD", "EU27_2020"}
    _td_mask = (
        df[geo_col].astype(str).str.match(r"^CZ[A-Z0-9]{2}$")
        & ~df[_cwork_col].astype(str).str.upper().isin(_AGG_VALS)
    )
    if sex_val and sex_candidates:
        _td_mask &= df[sex_candidates[0]].astype(str).str.upper() == sex_val.upper()
    if age_val and age_candidates:
        _td_mask &= df[age_candidates[0]].astype(str).str.upper() == age_val.upper()
    if unit_val and unit_candidates:
        _td_mask &= df[unit_candidates[0]].astype(str).str.upper() == unit_val.upper()
    _td = df[_td_mask].copy()
    _td[val_col] = pd.to_numeric(_td[val_col], errors="coerce")
    _td = _td.dropna(subset=[val_col])
    _td["_time_int"] = _td[time_col].astype(str).str[:4].astype(int)
    _td_latest_yr = _td.groupby(geo_col)["_time_int"].transform("max")
    _td = _td[_td["_time_int"] == _td_latest_yr]
    _idx = _td.groupby(geo_col)[val_col].idxmax()
    _top_dest = _td.loc[_idx, [geo_col, _cwork_col]].set_index(geo_col)[_cwork_col].to_dict()
    print(f"  Top destinations per CZ NUTS2: {_top_dest}")
else:
    print("  C_WORK column not found — top-destination labels unavailable.")

ds = Dataset(filt, name="Přeshraniční dojíždění", unit="% zaměstnaných",
             source_url="Eurostat/lfst_r_lfe2ecomm")

# ── 3b. Download employed-persons denominator (lfst_r_lfe2emprtn) ────────────
# Used to normalise absolute commuter counts (THOUS) to % of regional workforce.
print("Downloading lfst_r_lfe2emprtn (denominator: employed persons) …")
_emp_data: "pd.DataFrame | None" = None
try:
    _emp_path = fetch_eurostat("lfst_r_lfe2emprtn", "A.THS_PER.T.TOTAL.", start_period=2015)
    _emp_raw = pd.read_csv(_emp_path, comment="#")
    _emp_raw.columns = [c.strip().upper() for c in _emp_raw.columns]
    _emp_geo  = next((c for c in _emp_raw.columns if c in ("GEO", "REF_AREA")), None)
    _emp_val  = next((c for c in _emp_raw.columns if c in ("OBS_VALUE", "VALUE")), None)
    _emp_time = next((c for c in _emp_raw.columns if c in ("TIME_PERIOD", "TIME")), None)
    _emp_unit_col = next((c for c in _emp_raw.columns if "UNIT" in c), None)
    _emp_sex_col  = next((c for c in _emp_raw.columns if "SEX"  in c), None)
    _emp_age_col  = next((c for c in _emp_raw.columns if "AGE"  in c), None)
    _emp_unit_val = _first_val(_emp_raw, [_emp_unit_col] if _emp_unit_col else [],
                               ["THS_PER", "THOUS", "THS"])
    _emp_sex_val  = _first_val(_emp_raw, [_emp_sex_col]  if _emp_sex_col  else [],
                               ["T", "TOTAL"])
    _emp_age_val  = _first_val(_emp_raw, [_emp_age_col]  if _emp_age_col  else [],
                               ["TOTAL", "Y_GE15", "Y15-74"])
    _emp_mask = pd.Series([True] * len(_emp_raw), index=_emp_raw.index)
    if _emp_unit_val and _emp_unit_col:
        _emp_mask &= _emp_raw[_emp_unit_col].astype(str).str.upper() == _emp_unit_val.upper()
    if _emp_sex_val and _emp_sex_col:
        _emp_mask &= _emp_raw[_emp_sex_col].astype(str).str.upper() == _emp_sex_val.upper()
    if _emp_age_val and _emp_age_col:
        _emp_mask &= _emp_raw[_emp_age_col].astype(str).str.upper() == _emp_age_val.upper()
    _emp_filt = _emp_raw[_emp_mask].copy()
    _emp_filt[_emp_val] = pd.to_numeric(_emp_filt[_emp_val], errors="coerce")
    _emp_filt = _emp_filt.rename(
        columns={_emp_geo: "geo", _emp_time: "time", _emp_val: "emp_value"}
    )
    _emp_filt["time"] = _emp_filt["time"].astype(str).str[:4].astype(int)
    _emp_data = _emp_filt[["geo", "time", "emp_value"]].dropna()
    print(f"  lfst_r_lfe2emprtn rows: {len(_emp_data)}  "
          f"unit={_emp_unit_val}, sex={_emp_sex_val}, age={_emp_age_val}")
except Exception as _exc:
    print(f"  WARNING: denominator download failed ({_exc}); "
          "will use raw values if already in % form")
    _emp_data = None

# ── Figure A — Timeline (national-level rows only, 2-char geo codes) ─────────
print("\nFigure A: timeline …")
nat = filt[filt["geo"].str.len() == 2].copy()
ds_nat = Dataset(nat, name="Přeshraniční dojíždění", unit="% zaměstnaných",
                 source_url="Eurostat/lfst_r_lfe2ecomm")

if not ds_nat.df.empty and len(ds_nat.countries) >= 2:
    fig_a = timeline(
        ds_nat,
        countries=COUNTRIES,
        title="Přeshraniční pracovní dojíždění",
        ylabel=r"podíl pracujících v~zahraničí [\%]",
        highlight=HIGHLIGHT,
        annotate_last=True,
        show_eu_avg=False,
        background_eu=True,
    )
    # Tooltips: foreground countries + grey EU-27 background lines.
    _ax_a = fig_a.axes[0]
    _pivot_a_fg = nat[nat["geo"].isin(COUNTRIES)].pivot_table(
        index="time", columns="geo", values="value", aggfunc="mean"
    )
    add_pgf_tooltips(_ax_a, _pivot_a_fg, fmt="{:.2f}")
    _bg_a = sorted(set(EU27) - set(COUNTRIES))
    _pivot_a_bg = nat[nat["geo"].isin(_bg_a)].pivot_table(
        index="time", columns="geo", values="value", aggfunc="mean"
    )
    add_pgf_tooltips(_ax_a, _pivot_a_bg, fmt="{:.2f}")
    savefig_pgf(fig_a, "problemy_dojezdeni_vyvoj")
    yr_min = nat["time"].min()
    yr_max = nat["time"].max()
    save_figure_tex_pgf(
        "problemy_dojezdeni_vyvoj",
        caption=f"Přeshraniční pracovní dojíždění, vybrané země \\acs{{geo-EU}}, {yr_min}--{yr_max}",
        label="fig:problemy_dojezdeni_vyvoj",
        cite_keys="eurostat_lfst_r_lfe2ecomm",
    )

# ── Figure B — EU map ─────────────────────────────────────────────────────────
print("\nFigure B: EU map …")
try:
    nat2 = filt[filt["geo"].str.len() == 2].copy()
    latest_nat = int(nat2["time"].max())
    snap_nat = nat2[nat2["time"] == latest_nat].copy()

    ds_map = Dataset(snap_nat, name="Přeshraniční dojíždění", unit="% zaměstnaných",
                     source_url="Eurostat/lfst_r_lfe2ecomm")
    fig_b = choropleth(
        ds_map, year=latest_nat,
        title=(
            f"Přeshraniční pracovní dojíždění v~\\acs{{geo-EU}} ({latest_nat})\n"
            r"\% zaměstnaných pracujících v~zahraničí"
        ),
        colorbar_label=r"\% zaměstnaných pracujících v zahraničí",
        cmap="RdYlGn_r",

        label_countries=True,
    )
    # PGF hover tooltips on country codes (values shown on hover).
    _snap_map = snap_nat.set_index("geo")["value"].to_dict()
    apply_geo_labels_pgf(fig_b.axes[0], values=_snap_map, tooltip_fmt="{:.2f} %")

    savefig_pgf(fig_b, "problemy_dojezdeni_mapa")
    save_figure_tex_pgf(
        "problemy_dojezdeni_mapa",
        caption=f"Přeshraniční pracovní dojíždění, \\acs{{geo-EU}}27, {latest_nat}.",
        label="fig:problemy_dojezdeni_mapa",
        cite_keys="eurostat_lfst_r_lfe2ecomm",
    )
    print(f"  Figure B done ({latest_nat}).")
except Exception as exc:
    print(f"  Figure B skipped: {exc}")

# ── Figure C — CZ NUTS2 choropleth ───────────────────────────────────────────
print("\nFigure C: CZ NUTS2 choropleth …")
try:
    nuts2_data = filt[filt["geo"].str.len() == 4].copy()
    latest_nuts2 = nuts2_data["time"].max()
    snap_nuts2 = nuts2_data[nuts2_data["time"] == latest_nuts2].copy()

    # Normalise to % of regional workforce when commuter counts are absolute
    # (unit THS_PER / THOUS).  If unit is already PC_ACT/PC_EMP use as-is.
    _is_absolute = unit_val is not None and any(
        k in unit_val.upper() for k in ["THS", "THOUS"]
    )
    if _is_absolute and _emp_data is not None:
        # Prefer exact year; fall back to latest available per region.
        _emp_snap = _emp_data[
            (_emp_data["geo"].str.len() == 4) & (_emp_data["time"] == latest_nuts2)
        ][["geo", "emp_value"]].drop_duplicates(subset="geo")
        if _emp_snap.empty:
            _emp_snap = (
                _emp_data[_emp_data["geo"].str.len() == 4]
                .sort_values("time")
                .groupby("geo")
                .last()
                .reset_index()[["geo", "emp_value"]]
            )
        snap_nuts2 = snap_nuts2.merge(_emp_snap, on="geo", how="left")
        snap_nuts2["value"] = snap_nuts2["value"] / snap_nuts2["emp_value"] * 100
        _normed = snap_nuts2["value"].notna().sum()
        print(f"  Normalised {_normed}/{len(snap_nuts2)} regions to % of employed.")
    elif _is_absolute:
        print("  WARNING: absolute unit detected but denominator unavailable — "
              "values not normalised; map may have non-comparable scale.")

    data_series = snap_nuts2.drop_duplicates(subset="geo").set_index("geo")["value"].dropna()

    # Flag whether German NUTS2 data is present (often missing in lfst_r_lfe2ecomm).
    _de_regions = [g for g in data_series.index if g.startswith("DE")]
    _de_missing = len(_de_regions) == 0
    if _de_missing:
        print("  NOTE: German NUTS2 data not available in lfst_r_lfe2ecomm — "
              "DE regions render as 'data nedostupná'.")

    fig_c = choropleth_cz(
        data_series,
        nuts_level_cz=2,
        title=(
            f"ČR NUTS2: přeshraniční dojíždění ({latest_nuts2})\n"
            r"\% regionální pracovní síly pracující v~zahraničí"
        ),
        colorbar_label=r"\% regionální pracovní síly pracující v zahraničí",
        cmap="RdYlGn_r",
        label_cz=False,
    )
    # Annotate each CZ NUTS2 region with its top destination country code
    if _top_dest:
        try:
            _nuts_path_c = fetch(_GISCO_NUTS_URL, suffix=".geojson")
            _cz2_gdf = gpd.read_file(_nuts_path_c)
            _cz2_gdf = _cz2_gdf[
                (_cz2_gdf["LEVL_CODE"] == 2) & (_cz2_gdf["CNTR_CODE"] == "CZ")
            ]
            _ax_c = fig_c.axes[0]
            for _, _row in _cz2_gdf.iterrows():
                _rid = _row["NUTS_ID"]
                if _rid not in _top_dest:
                    continue
                _cx, _cy = _row.geometry.centroid.x, _row.geometry.centroid.y
                _dest = _top_dest[_rid]
                # \pdftooltip so hover shows NUTS_ID + destination country long name.
                from stattool.style import GEO_LONG_NAMES as _GL
                _tip = f"{_rid} \u2192 {_GL.get(_dest, _dest)}"
                _ax_c.text(
                    _cx, _cy,
                    rf"\pdftooltip{{{_dest}}}{{{_tip}}}",
                    ha="center", va="center",
                    fontsize=FONT_SIZE, fontweight="bold", color="white",
                    path_effects=[mpe.withStroke(linewidth=2.5, foreground="black")],
                )
        except Exception as _exc:
            print(f"  Top-destination labels skipped: {_exc}")
    savefig_pgf(fig_c, "problemy_dojezdeni_nuts2")
    _de_note = (
        " Německé regiony nejsou v~datech dostupné."
        if _de_missing else ""
    )
    save_figure_tex_pgf(
        "problemy_dojezdeni_nuts2",
        caption=(
            f"Přeshraniční dojíždění, regiony NUTS2, ČR a~sousední země, {latest_nuts2}. "
            r"Hodnoty: podíl regionální pracovní síly pracující v~zahraničí (\%)."
            f"{_de_note}"
        ),
        label="fig:problemy_dojezdeni_nuts2",
        cite_keys="eurostat_lfst_r_lfe2ecomm",
    )
    print(f"  Figure C done ({latest_nuts2}).")
except Exception as exc:
    print(f"  Figure C skipped: {exc}")

print("\nDone.")
