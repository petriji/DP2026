r"""
Cross-border labour mobility -- CZ and EU comparators.

Three figures illustrating how Czech workers commute across national borders,
expressed as % of the employed workforce (PC_EMP) --- normalised to remove
country- and region-size effects.

Data source: Eurostat, ``lfst_r_lfe2ecomm``
  Employed persons commuting to work by country of work and NUTS 2 region.
  Dimensions: freq · age · c_work · sex · unit · geo
  Filter values (only THS_PER is published in this dataset):
    unit    = THS_PER  (thousand persons; absolute counts)
    c_work  = FOR      (working in a foreign country)
    age     = Y20-64
    sex     = T
  All three figures express the indicator as
  ``cross-border commuters / total employed in the same region * 100``.
  The denominator is built from the same dataset by summing
  ``c_work ∈ {FOR, INR, OUTR}`` (total employed by region of residence).

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

unit_val     = _first_val(df, unit_candidates,    ["THS_PER", "THOUS", "THS"])
wrkplace_val = _first_val(df, wrkplace_candidates, ["FOR", "ABROAD", "ABRD"])
sex_val      = _first_val(df, sex_candidates,      ["T", "TOTAL"])
age_val      = _first_val(df, age_candidates,      ["Y20-64", "Y_GE15", "Y15-64"])

print(f"  Selected: unit={unit_val}, wrkplace={wrkplace_val}, sex={sex_val}, age={age_val}")

# Coerce values
df[val_col] = pd.to_numeric(df[val_col], errors="coerce")

# Common dim filter (unit/sex/age) --- used for both numerator and denominator.
common_mask = pd.Series([True] * len(df), index=df.index)
if unit_val and unit_candidates:
    common_mask &= df[unit_candidates[0]].astype(str).str.upper() == unit_val.upper()
if sex_val and sex_candidates:
    common_mask &= df[sex_candidates[0]].astype(str).str.upper() == sex_val.upper()
if age_val and age_candidates:
    common_mask &= df[age_candidates[0]].astype(str).str.upper() == age_val.upper()

# Numerator: cross-border commuters (c_work=FOR), thousand persons.
num_mask = common_mask.copy()
if wrkplace_val and wrkplace_candidates:
    num_mask &= df[wrkplace_candidates[0]].astype(str).str.upper() == wrkplace_val.upper()
num = df[num_mask].copy()
num = num.rename(columns={geo_col: "geo", time_col: "time", val_col: "commuters_ths"})
num["time"] = num["time"].astype(str).str[:4].astype(int)
num = num[["geo", "time", "commuters_ths"]].dropna()

# Denominator: total employed = sum over c_work ∈ {FOR, INR, OUTR}.
# (NRP excluded --- 'no response on place of work'.)
den_mask = common_mask.copy()
if wrkplace_candidates:
    den_mask &= df[wrkplace_candidates[0]].astype(str).str.upper().isin(["FOR", "INR", "OUTR"])
den = df[den_mask].copy()
den = den.rename(columns={geo_col: "geo", time_col: "time", val_col: "emp_ths"})
den["time"] = den["time"].astype(str).str[:4].astype(int)
den = den.groupby(["geo", "time"], as_index=False)["emp_ths"].sum()

# Combine → percent of regional employed working abroad.
filt = num.merge(den, on=["geo", "time"], how="left")
filt["value"] = filt["commuters_ths"] / filt["emp_ths"] * 100
filt = filt[["geo", "time", "value"]].dropna()
print(f"  Filtered (normalised) rows: {len(filt)}  "
      f"|  geo sample: {list(filt['geo'].unique()[:10])}")

# Note: lfst_r_lfe2ecomm has no per-destination-country breakdown
# (c_work ∈ {FOR, INR, OUTR, NRP} only), so per-region top-destination
# annotations are not available from this dataset.

ds = Dataset(filt, name="Přeshraniční dojíždění", unit="% zaměstnaných",
             source_url="Eurostat/lfst_r_lfe2ecomm")

# ── Figure A --- Timeline (national-level rows only, 2-char geo codes) ─────────
print("\nFigure A: timeline …")
nat = filt[filt["geo"].str.len() == 2].copy()
ds_nat = Dataset(nat, name="Přeshraniční dojíždění", unit="% zaměstnaných",
                 source_url="Eurostat/lfst_r_lfe2ecomm")

if not ds_nat.df.empty and len(ds_nat.countries) >= 2:
    STRINGS_VYVOJ = {
        "title": "Přeshraniční pracovní dojíždění",
        "ylabel": r"podíl pracujících v~zahraničí [\%]",
    }
    fig_a = timeline(
        ds_nat,
        countries=COUNTRIES,
        title=STRINGS_VYVOJ["title"],
        ylabel=STRINGS_VYVOJ["ylabel"],
        highlight=HIGHLIGHT,
        annotate_last=True,
        show_eu_avg=False,
        background_eu=True,
    )
    fig_a.axes[0].set_ylim(0, 8)
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
    NUDGE_LABELS = [(c, rf"\acs{{geo-{c}}}") for c in COUNTRIES]
    savefig_pgf(fig_a, "problemy_dojezdeni_vyvoj", strings=STRINGS_VYVOJ, nudge_labels=NUDGE_LABELS)
    yr_min = nat["time"].min()
    yr_max = nat["time"].max()
    save_figure_tex_pgf(
        "problemy_dojezdeni_vyvoj",
        caption=f"Přeshraniční pracovní dojíždění, vybrané země \\acs{{geo-EU}}, {yr_min}--{yr_max}",
        label="fig:problemy_dojezdeni_vyvoj",
        cite_keys="eurostat_lfst_r_lfe2ecomm",
        strings=STRINGS_VYVOJ,
        nudge_labels=NUDGE_LABELS,
    )

# ── Figure B --- EU map ─────────────────────────────────────────────────────────
print("\nFigure B: EU map …")
try:
    nat2 = filt[filt["geo"].str.len() == 2].copy()
    latest_nat = int(nat2["time"].max())
    snap_nat = nat2[nat2["time"] == latest_nat].copy()

    ds_map = Dataset(snap_nat, name="Přeshraniční dojíždění", unit="% zaměstnaných",
                     source_url="Eurostat/lfst_r_lfe2ecomm")
    _values_map = snap_nat.set_index("geo")["value"].to_dict()
    _vmax = max(_values_map.values())
    STRINGS_MAP = {
        "title": f"Přeshraniční pracovní dojíždění v~\\acs{{geo-EU}} ({latest_nat})",
        "colorbar_label": r"\% zaměstnaných pracujících v~zahraničí",
    }
    fig_b = choropleth(
        ds_map, year=latest_nat,
        title=STRINGS_MAP["title"],
        colorbar_label=STRINGS_MAP["colorbar_label"],
        cmap="RdYlGn_r",
        vmin=0, vmax=_vmax,
        highlight_colorbar=["CZ"],
        label_countries=True,
    )
    # PGF hover tooltips on country codes (values shown on hover).
    apply_geo_labels_pgf(fig_b.axes[0], halo=True, values=_values_map, tooltip_fmt="{:.2f} %")

    savefig_pgf(fig_b, "problemy_dojezdeni_mapa", strings=STRINGS_MAP)
    save_figure_tex_pgf(
        "problemy_dojezdeni_mapa",
        caption=f"Přeshraniční pracovní dojíždění, \\acs{{geo-EU}}27, {latest_nat}.",
        label="fig:problemy_dojezdeni_mapa",
        cite_keys="eurostat_lfst_r_lfe2ecomm",
        strings=STRINGS_MAP,
    )
    print(f"  Figure B done ({latest_nat}).")
except Exception as exc:
    print(f"  Figure B skipped: {exc}")

# ── Figure C --- CZ NUTS2 choropleth ───────────────────────────────────────────
print("\nFigure C: CZ NUTS2 choropleth …")
try:
    nuts2_data = filt[filt["geo"].str.len() == 4].copy()
    # Use latest non-NaN value per region — improves DE / CZ02 coverage where
    # the very latest year is sparse.  Each region thus reports its most recent
    # available estimate.
    nuts2_data = nuts2_data.sort_values("time")
    snap_nuts2 = nuts2_data.groupby("geo", as_index=False).tail(1)
    latest_nuts2 = int(nuts2_data["time"].max())

    data_series = snap_nuts2.drop_duplicates(subset="geo").set_index("geo")["value"].dropna()
    year_series = snap_nuts2.drop_duplicates(subset="geo").set_index("geo")["time"]

    # Region long names from the GISCO NUTS layer (used for PGF tooltips).
    _nuts_path = fetch(_GISCO_NUTS_URL, suffix=".geojson")
    _nuts_gdf = gpd.read_file(_nuts_path)
    _names_map = dict(zip(_nuts_gdf["NUTS_ID"], _nuts_gdf["NAME_LATN"]))
    label_names = {
        nid: f"{_names_map.get(nid, nid)} ({int(year_series.get(nid, latest_nuts2))})"
        for nid in data_series.index
    }

    STRINGS_NUTS2 = {
        "title": (
            f"\\acs{{geo-CZ}} a~okolí NUTS2: přeshraniční dojíždění ({latest_nuts2}, \acs{{geo-DE}} nejnovější dostupný rok)\n"
            r"\% regionální pracovní síly pracující v~zahraničí"
        ),
        "colorbar_label": r"\% regionální pracovní síly pracující v zahraničí",
    }
    fig_c = choropleth_cz(
        data_series,
        nuts_level_cz=2,
        title=STRINGS_NUTS2["title"],
        colorbar_label=STRINGS_NUTS2["colorbar_label"],
        cmap="RdYlGn_r",
        vmin=float(data_series.min()),
        vmax=float(data_series.max()),
        label_cz=True,
        label_nbr=True,
        label_fmt="{:.1f}",
        label_names=label_names,
        label_tooltip_fmt=r"{:.2f}\,\%",
    )
    savefig_pgf(fig_c, "problemy_dojezdeni_nuts2", strings=STRINGS_NUTS2)
    save_figure_tex_pgf(
        "problemy_dojezdeni_nuts2",
        caption=(
            f"Přeshraniční dojíždění, regiony NUTS2, ČR a~sousední země; nejnovější dostupný rok per region "
            f"($\\le${latest_nuts2}). "
            r"Hodnoty: podíl regionální pracovní síly pracující v~zahraničí (\%)."
        ),
        label="fig:problemy_dojezdeni_nuts2",
        cite_keys="eurostat_lfst_r_lfe2ecomm",
        strings=STRINGS_NUTS2,
    )
    print(f"  Figure C done (latest <= {latest_nuts2}).")
except Exception as exc:
    print(f"  Figure C skipped: {exc}")

print("\nDone.")
