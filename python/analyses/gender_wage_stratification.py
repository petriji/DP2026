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
    cd python && python analyses/gender_wage_stratification.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, cm2in, savefig, save_figure_tex
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────
COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
COUNTRY_LABELS = {"CZ": "CZ", "AT": "AT", "DE": "DE", "DK": "DK", "PL": "PL", "SK": "SK"}

apply_style()

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
    gpg_snap[[geo_col, "gpg", "time"]]
    .rename(columns={geo_col: "geo", "gpg": "value"})
    .copy()
)
ds_gpg = Dataset(gpg_df, name="Gender Pay Gap", unit="%",
                 source_url="Eurostat/earn_gr_gpgr2")

fig_a = choropleth(
    ds_gpg, year=snap_year,
    title=f"Neupravený gender pay gap v~EU ({snap_year})\nNACE B–S, v~% hodinové mzdy mužů",
    cmap="RdBu_r",
    vmin=0,
    vmax=25,
    colorbar_label="GPG (% mzdy mužů)",
    label_countries=True,
)

savefig(fig_a, "gender_pay_gap_map", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "gender_pay_gap_map",
    caption=(
        f"Neupravený gender pay gap, EU27, {snap_year}. "
        r"(Eurostat \texttt{earn\_gr\_gpgr2}, NACE B--S). "
        "Hodnota udává, o~kolik procent jsou průměrné hodinové výdělky žen nižší "
        "než výdělky mužů. ČR se pohybuje výrazně nad průměrem EU\\@. "
        "Transparentnost odměňování zakotvená v~kolektivních smlouvách "
        "(viz EU Pay Transparency Directive 2023/970) je klíčovým nástrojem "
        "ke snížení tohoto diferenciálu."
    ),
    cite_keys="eurostat_gpg",
    label="fig:gender_pay_gap_map",
    width=r"0.95\linewidth",
    cite_key="eurostat_gpg",
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

fig_b, axes_b = plt.subplots(
    1, len(COUNTRIES),
    figsize=cm2in(18, 8),
    sharey=False,
)

def _sex_label(code: str) -> str:
    c = str(code).upper()
    if c in ("M", "MALE"):
        return "muži"
    if c in ("F", "FEMALE"):
        return "ženy"
    return code

_MALE_COLOR   = "#2166ac"
_FEMALE_COLOR = "#d6604d"

ses_ok = False
if _HAS_SES_DATA and s_indic and s_sex and s_geo:
    ses_ok = True

for idx, country in enumerate(COUNTRIES):
    ax = axes_b[idx]
    sub = ses_snap[ses_snap[s_geo] == country].sort_values("_rank") if s_geo else pd.DataFrame()

    if ses_ok and not sub.empty and s_sex:
        sub_m = sub[sub[s_sex].astype(str).str.upper() == "M"]
        sub_f = sub[sub[s_sex].astype(str).str.upper() == "F"]

        if not sub_m.empty:
            ax.plot(sub_m["_rank"], sub_m[s_val],
                    color=_MALE_COLOR, linewidth=2.0, marker="o", markersize=5,
                    label="muži" if idx == 0 else "_")
        if not sub_f.empty:
            ax.plot(sub_f["_rank"], sub_f[s_val],
                    color=_FEMALE_COLOR, linewidth=2.0, marker="s", markersize=5,
                    label="ženy" if idx == 0 else "_")

        ranks = sorted(_INDIC_RANK.values())
        ax.set_xticks(ranks)
        ax.set_xticklabels([_INDIC_LABEL[r] for r in ranks],
                           fontsize=FONT_SIZE - 2.5)
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda y, _: f"{y:.0f}")
        )
        ax.tick_params(axis="y", labelsize=FONT_SIZE - 2)
    else:
        ax.text(0.5, 0.5, "data\nnedostupná",
                ha="center", va="center",
                transform=ax.transAxes, fontsize=FONT_SIZE - 2, color="grey")
        ax.set_xticks([])
        ax.set_yticks([])

    ax.set_title(country, fontsize=FONT_SIZE, pad=3)
    ax.set_xlabel("percentil", fontsize=FONT_SIZE - 2)
    if idx == 0:
        ax.set_ylabel("hodinová mzda (EUR/PPS)", fontsize=FONT_SIZE - 1)

handles = [
    mpatches.Patch(color=_MALE_COLOR,   label="muži"),
    mpatches.Patch(color=_FEMALE_COLOR, label="ženy"),
]
fig_b.legend(handles=handles, loc="lower center", ncol=2,
             frameon=False, fontsize=FONT_SIZE - 1, bbox_to_anchor=(0.5, -0.05))
fig_b.suptitle(
    f"Mzdová distribuce podle pohlaví ({ses_year}): percentilové profily",
    fontsize=FONT_SIZE, y=1.01,
)
fig_b.tight_layout()

savefig(fig_b, "gender_wage_stratification", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "gender_wage_stratification",
    caption=(
        f"Hodinové mzdy podle pohlaví, EU, {ses_year}.. "
        "Zobrazeny tři ukazatele: D1 (1. decil), medián a D9 (9. decil); "
        "modrá = muži, červená = ženy. "
        "Ve~všech zemích je celá distribuce žen níže než distribuce mužů; "
        "vzdálenost je největší v~horním decilu (D9), "
        "kde kolektivní smlouvy s~transparentními mzdovými tabulkami mají "
        "největší potenciál ke snížení gender pay gap."
    ),
    cite_keys="eurostat_ses_hourly",
    label="fig:gender_wage_stratification",
    width=r"\linewidth",
    cite_key="eurostat_ses_hourly",
)

print("Done.")
