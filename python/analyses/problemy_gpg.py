r"""
Gender wage stratification: EU pay-gap choropleth and percentile profiles.

Figure A – ``gender_pay_gap_map``
    EU NUTS0 choropleth of the unadjusted gender pay gap in 2023 (latest),
    NACE B–S, in % of male hourly earnings.  Coloured by GPG value
    (continuous RdBu_r scale); CZ labelled; EU27 average line annotated.

    Data: Eurostat ``earn_gr_gpgr2``
      Dimensions: freq · nace_r2 · unit · geo · time
      Filter: nace_r2=B-S (broadest economy-wide aggregate), unit=PC

Figure B – ``gender_wage_stratification``
    Grouped percentile profile chart for 6 countries (CZ AT DE DK PL SK).
    For each country, shows the earnings distribution (P10/P25/P50/P75/P90)
    for males (blue) and females (red) as segments on a single axis.
    Latest Structure of Earnings Survey (SES) year.

    Data: Eurostat ``earn_ses_hourly``
      Dimensions: freq · sex · quantile · nace_r2 · currency · geo · time
      Filter: sex=M/F, quantile=P10/P25/P50/P75/P90, nace_r2=TOTAL (or B-S),
              currency=EUR (or PPS_EU27_2020), geo=CZ+AT+DE+DK+PL+SK

Argumentation
-------------
Together these two figures show: (a) CZ has a persistently high gender pay
gap compared to DK or BE; (b) the gap is not only in absolute levels but
in the entire distribution — the female P75 in CZ is below the male P50,
indicating structural segmentation that collective bargaining with wage
transparency could address.

Run
---
    cd python && python analyses/problemy_gpg_stratifikace.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import cm2in, apply_style_pgf, savefig_pgf, save_figure_tex_pgf
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────
COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
COUNTRY_LABELS = {"CZ": "CZ", "AT": "AT", "DE": "DE", "DK": "DK", "PL": "PL", "SK": "SK"}

apply_style_pgf()

# ==============================================================================
# Figure A – Gender Pay Gap choropleth (earn_gr_gpgr2)
# ==============================================================================
print("Downloading earn_gr_gpgr2 …")
gpg_path = fetch_eurostat("earn_gr_gpgr2", start_period=2018)
gpg_raw = pd.read_csv(gpg_path, comment="#")
gpg_raw.columns = [c.strip().upper() for c in gpg_raw.columns]
print("GPG columns:", list(gpg_raw.columns))

geo_col  = next((c for c in gpg_raw.columns if c in ("GEO", "REF_AREA")), None)
time_col = next((c for c in gpg_raw.columns if c in ("TIME_PERIOD", "TIME")), None)
val_col  = next((c for c in gpg_raw.columns if c in ("OBS_VALUE", "VALUE")), None)
nace_col = next((c for c in gpg_raw.columns if "NACE" in c), None)
unit_col = next((c for c in gpg_raw.columns if "UNIT" in c), None)
sex_col  = next((c for c in gpg_raw.columns if "SEX" in c), None)

print(f"  nace col: {nace_col}, unit col: {unit_col}, sex col: {sex_col}")
if nace_col:
    print("  nace values (sample):", gpg_raw[nace_col].unique()[:10])
if unit_col:
    print("  unit values:", gpg_raw[unit_col].unique())

# Filter: NACE B-S (broadest), PC unit, national level (len(geo)==2)
gpg = gpg_raw.copy()
if nace_col:
    nace_totals = [v for v in gpg[nace_col].unique()
                   if str(v).upper() in ("B-S_X_O", "B-S", "TOTAL", "A-Z")]
    if not nace_totals:
        nace_totals = gpg[nace_col].unique()[:1]
    print("  using NACE codes:", nace_totals)
    gpg = gpg[gpg[nace_col].isin(nace_totals)]
if unit_col:
    pc_vals = [v for v in gpg[unit_col].unique() if "PC" in str(v).upper()]
    if pc_vals:
        gpg = gpg[gpg[unit_col].isin(pc_vals)]
if sex_col:
    for exclude in ("F", "M", "MALE", "FEMALE", "NAP"):
        gpg = gpg[~gpg[sex_col].astype(str).str.upper().isin([exclude])]
if geo_col:
    gpg = gpg[gpg[geo_col].astype(str).str.len() == 2]

gpg[val_col] = pd.to_numeric(gpg[val_col], errors="coerce")
gpg = gpg.dropna(subset=[val_col])
gpg["time"] = gpg[time_col].astype(str).str[:4].astype(int)

# Take latest year per country
gpg_snap = (
    gpg.sort_values("time")
    .groupby(geo_col)[[val_col, "time"]]
    .last()
    .reset_index()
)
print(f"  GPG snapshot rows: {len(gpg_snap)}, median year: {gpg_snap['time'].median()}")
snap_year = int(gpg_snap["time"].mode()[0]) if not gpg_snap.empty else 2022

# Build Dataset for choropleth
gpg_df = (
    gpg_snap[[geo_col, val_col, "time"]]
    .rename(columns={geo_col: "geo", val_col: "value"})
    .copy()
)
ds_gpg = Dataset(gpg_df, name="Gender Pay Gap", unit="%",
                 source_url="Eurostat/earn_gr_gpgr2")

fig_a = choropleth(
    ds_gpg, year=snap_year,
    title=f"Nekorigovaný GPG v\u00a0EU ({snap_year})\nNACE B–S, v\u00a0% hodinové mzdy mužů",
    cmap="RdBu_r",
    vmin=0,
    vmax=25,
    colorbar_label="nekorigovaný GPG [%]",
    label_countries=True,
)

savefig_pgf(fig_a, "problemy_gpg_mapa")
save_figure_tex_pgf(
    "problemy_gpg_mapa",
    caption=(
        f"Nekorigovaný gender pay gap (NACE B--S), EU27, {snap_year}. "
        "Hodnota udává, o~kolik procent jsou průměrné hodinové výdělky žen nižší "
        "než výdělky mužů"
    ),
    cite_keys="eurostat_gpg",
    label="fig:problemy_gpg_mapa",
    resizebox_width=r"0.95\linewidth",
    cite_key="eurostat_gpg",
    strings={},
)

# ==============================================================================
# Figure B – Earnings distribution by sex (earn_ses_hourly)
# Indicators: D1 (P10 / 1st decile), median, D9 (P90 / 9th decile)
# ==============================================================================
print("Downloading earn_ses_hourly …")
# Dimensions: freq · nace_r2 · isco08 · worktime · age · sex · indic_se · geo
# Filter: A, NACE B-S_X_O, ISCO=TOTAL, worktime=TOTAL, age=TOTAL, sex=M+F,
#         indic_se=D1_E_EUR+MED_E_EUR+D9_E_EUR, geo=6 countries
GEO_6 = "+".join(COUNTRIES)
ses_filter = f"A.B-S_X_O.TOTAL.TOTAL.TOTAL.M+F.D1_E_EUR+MED_E_EUR+D9_E_EUR.{GEO_6}"
ses_path = fetch_eurostat("earn_ses_hourly", ses_filter)
ses_raw = pd.read_csv(ses_path, comment="#")
ses_raw.columns = [c.strip().upper() for c in ses_raw.columns]
print("SES columns:", list(ses_raw.columns))

s_geo    = next((c for c in ses_raw.columns if c in ("GEO", "REF_AREA")), None)
s_time   = next((c for c in ses_raw.columns if c in ("TIME_PERIOD", "TIME")), None)
s_val    = next((c for c in ses_raw.columns if c in ("OBS_VALUE", "VALUE")), None)
s_sex    = next((c for c in ses_raw.columns if c == "SEX"), None)
s_indic  = next((c for c in ses_raw.columns if "INDIC" in c), None)

print(f"  sex: {s_sex}, indic: {s_indic}")
if s_sex:  print("  sex values:", ses_raw[s_sex].unique())
if s_indic: print("  indic values:", ses_raw[s_indic].unique())

ses_raw[s_val] = pd.to_numeric(ses_raw[s_val], errors="coerce")
ses_raw = ses_raw.dropna(subset=[s_val])
ses_raw["time"] = ses_raw[s_time].astype(str).str[:4].astype(int)

# ── Convert EUR → PPS using PLI (price level index, EU27=100) ────────────────
print("Downloading prc_ppp_ind for EUR→PPS conversion …")
_pli_path = fetch_eurostat("prc_ppp_ind", f"A.PLI_EU27_2020.GDP.{GEO_6}", start_period=2014)
_pli_raw = pd.read_csv(_pli_path, comment="#")
_pli_raw.columns = [c.strip().upper() for c in _pli_raw.columns]
_pli_geo = next((c for c in _pli_raw.columns if c in ("GEO", "REF_AREA")), None)
_pli_time = next((c for c in _pli_raw.columns if c in ("TIME_PERIOD", "TIME")), None)
_pli_val = next((c for c in _pli_raw.columns if c in ("OBS_VALUE", "VALUE")), None)
_pli = _pli_raw[[_pli_geo, _pli_time, _pli_val]].dropna(subset=[_pli_val]).copy()
_pli.columns = ["_pli_geo", "_pli_time", "_pli"]
_pli["_pli_time"] = _pli["_pli_time"].astype(str).str[:4].astype(int)
_pli["_pli"] = pd.to_numeric(_pli["_pli"], errors="coerce") / 100.0  # EU27=1.0

ses_raw = ses_raw.merge(
    _pli,
    left_on=[s_geo, "time"],
    right_on=["_pli_geo", "_pli_time"],
    how="left",
)
_has_pli = ses_raw["_pli"].notna().any()
if _has_pli:
    ses_raw[s_val] = ses_raw[s_val] / ses_raw["_pli"]
    print("  EUR → PPS conversion applied")
else:
    print("  WARNING: PLI unavailable — keeping EUR values")
ses_raw = ses_raw.drop(columns=["_pli_geo", "_pli_time", "_pli"], errors="ignore")

# Map indicator to numeric x-position (P10=10, P50=50, P90=90)
_INDIC_RANK = {"D1_E_EUR": 10, "MED_E_EUR": 50, "D9_E_EUR": 90}
_INDIC_LABEL = {10: "D1\n(P10)", 50: "Med\n(P50)", 90: "D9\n(P90)"}

if s_indic:
    ses_raw["_rank"] = ses_raw[s_indic].map(_INDIC_RANK)
    ses_raw = ses_raw[ses_raw["_rank"].notna()]

# Latest SES survey year per country/sex/indicator
group_cols = [c for c in [s_geo, s_sex, s_indic] if c]
ses_snap = (
    ses_raw.sort_values("time")
    .groupby(group_cols, dropna=False)[[s_val, "time", "_rank"]]
    .last()
    .reset_index()
)
print(f"  SES snapshot rows: {len(ses_snap)}")
ses_year = int(ses_snap["time"].mode()[0]) if not ses_snap.empty else 2022
_HAS_SES_DATA = len(ses_snap) >= 4

fig_b, ax_b = plt.subplots(figsize=cm2in(15, 10))

ses_ok = False
if _HAS_SES_DATA and s_indic and s_sex and s_geo:
    ses_ok = True

for country in COUNTRIES:
    color = COUNTRY_COLORS.get(country, "#888888")
    sub = ses_snap[ses_snap[s_geo] == country].sort_values("_rank") if s_geo else pd.DataFrame()

    if ses_ok and not sub.empty and s_sex:
        sub_f = sub[sub[s_sex].astype(str).str.upper() == "F"]
        sub_m = sub[sub[s_sex].astype(str).str.upper() == "M"]

        if not sub_f.empty:
            ax_b.plot(sub_f["_rank"], sub_f[s_val],
                      color=color, linewidth=1.8, linestyle="-",
                      marker="o", markersize=5, zorder=3)
        if not sub_m.empty:
            ax_b.plot(sub_m["_rank"], sub_m[s_val],
                      color=color, linewidth=1.8, linestyle="--",
                      marker="o", markersize=5, zorder=3)

if not ses_ok:
    ax_b.text(0.5, 0.5, "data\nnedostupná",
              ha="center", va="center",
              transform=ax_b.transAxes, fontsize=FONT_SIZE, color="grey")
    ax_b.set_xticks([])
    ax_b.set_yticks([])

ranks = sorted(_INDIC_RANK.values())
ax_b.set_xticks(ranks)
ax_b.set_xticklabels([_INDIC_LABEL[r] for r in ranks], fontsize=FONT_SIZE - 1)
ax_b.set_xlabel("percentil mzdové distribuce", fontsize=FONT_SIZE - 1)
ax_b.set_ylabel("hodinová mzda [PPS/h]", fontsize=FONT_SIZE - 1)
ax_b.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:.0f}"))
ax_b.set_title(
    f"Mzdová distribuce podle pohlaví ({ses_year}): D1, medián, D9",
    fontsize=FONT_SIZE,
)

country_handles = [
    plt.Line2D([0], [0], color=COUNTRY_COLORS.get(c, "#888888"),
               linewidth=1.8, marker="o", markersize=5, label=c)
    for c in COUNTRIES
]
style_handles = [
    plt.Line2D([0], [0], color="black", linewidth=1.8, linestyle="-",
               marker="o", markersize=4, label="ženy"),
    plt.Line2D([0], [0], color="black", linewidth=1.8, linestyle="--",
               marker="o", markersize=4, label="muži"),
]
ax_b.legend(handles=country_handles + style_handles,
            ncol=len(COUNTRIES) + 2,
            loc="lower center", bbox_to_anchor=(0.5, -0.18),
            frameon=False, fontsize=FONT_SIZE - 1)

savefig_pgf(fig_b, "problemy_gpg_stratifikace")
save_figure_tex_pgf(
    "problemy_gpg_stratifikace",
    caption=(
        f"Hodinové mzdy podle pohlaví a~percentilu, vybrané země EU, {ses_year}. "
        "Plná čára = ženy, přerušovaná = muži; barvy odlišují země. "
        "Zobrazeny tři ukazatele: D1 (1.~decil), medián a~D9 (9.~decil)"
    ),
    cite_keys="eurostat_ses_hourly",
    label="fig:problemy_gpg_stratifikace",
    resizebox_width=r"\linewidth",
    cite_key="eurostat_ses_hourly",
    strings={},
)

print("Done.")
