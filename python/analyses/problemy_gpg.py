r"""
Gender wage stratification: EU pay-gap choropleth and percentile profiles.

Figure A -- ``gender_pay_gap_map``
    EU NUTS0 choropleth of the unadjusted gender pay gap in 2023 (latest),
    NACE B--S, in % of male hourly earnings.  Coloured by GPG value
    (continuous RdBu_r scale); CZ labelled; EU27 average line annotated.

    Data: Eurostat ``earn_gr_gpgr2``
      Dimensions: freq · nace_r2 · unit · geo · time
      Filter: nace_r2=B-S (broadest economy-wide aggregate), unit=PC

Figure B -- ``gender_wage_stratification``
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
in the entire distribution --- the female P75 in CZ is below the male P50,
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

from config import COUNTRY_COLORS, LATEX_PICS_DIR, FIGURE_TEXT_SIZE, FIGURE_LABEL_SIZE, FIGURE_COMPACT_LABEL_SIZE
from stattool.data_quality import warn_fallback, warn_non_target_year
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    apply_geo_labels_pgf,
    add_pgf_tooltips,
    cm2in,
)
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────
COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
COUNTRY_LABELS = {"CZ": "CZ", "AT": "AT", "DE": "DE", "DK": "DK", "PL": "PL", "SK": "SK"}
NUDGE_LABELS = [(c, rf"\acs{{geo-{c}}}") for c in COUNTRIES]

apply_style_pgf()

# ==============================================================================
# Figure A -- Gender Pay Gap choropleth (earn_gr_gpgr2)
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
warn_non_target_year(source="Eurostat earn_gr_gpgr2", year=snap_year, context="Gender pay gap snapshot")

# Build Dataset for choropleth
gpg_df = (
    gpg_snap[[geo_col, val_col, "time"]]
    .rename(columns={geo_col: "geo", val_col: "value"})
    .copy()
)
ds_gpg = Dataset(gpg_df, name="Gender Pay Gap", unit="%",
                 source_url="Eurostat/earn_gr_gpgr2")

_values_gpg = (
    ds_gpg.df[ds_gpg.df["time"] <= snap_year]
    .sort_values("time").groupby("geo")["value"].last().to_dict()
)
_vmin_gpg = min(_values_gpg.values())
_vmax_gpg = max(_values_gpg.values())

STRINGS_GPG_MAP = {
    "title": f"Rozdíl ve mzdách mužů a žen podle percentilu ({snap_year})",
    "colorbar_label": r"nekorigovaný \acs{GPG} [\%]",
}

fig_a = choropleth(
    ds_gpg, year=snap_year,
    title=STRINGS_GPG_MAP["title"],
    # Sequential 0..vmax → use project-wide RdYlGn_r (matches other "more = worse"
    # choropleths so the rasterised colourbar dedups via _shared/).
    cmap="RdYlGn_r",
    vmin=_vmin_gpg,
    vmax=_vmax_gpg,
    colorbar_label=STRINGS_GPG_MAP["colorbar_label"],
    label_countries=True,
    highlight_colorbar=COUNTRIES,
)
apply_geo_labels_pgf(fig_a.axes[0], halo=True, values=_values_gpg, tooltip_fmt="{:.1f}")

savefig_pgf(fig_a, "problemy_gpg_mapa", strings=STRINGS_GPG_MAP, nudge_labels=NUDGE_LABELS)
save_figure_tex_pgf(
    "problemy_gpg_mapa",
    caption=f"Rozdíl ve mzdách mužů a žen \\((M-F)\\) v~\\si{{\\pps\\per\\hour}} podle percentilu, vybrané země \\acs{{geo-EU}}, {snap_year}",
    cite_keys="eurostat_gpg",
    label="fig:problemy_gpg_mapa",
    resizebox_width=r"\linewidth",
    cite_key="eurostat_gpg",
    strings=STRINGS_GPG_MAP,
    nudge_labels=NUDGE_LABELS,
)

# ==============================================================================
# Figure B -- Earnings distribution by sex (earn_ses_hourly)
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

_pli_latest = (
    _pli.sort_values("_pli_time")
    .groupby("_pli_geo", dropna=False)["_pli"]
    .last()
    .rename("_pli_latest")
)

ses_raw = ses_raw.merge(
    _pli,
    left_on=[s_geo, "time"],
    right_on=["_pli_geo", "_pli_time"],
    how="left",
)
ses_raw = ses_raw.merge(_pli_latest, left_on=s_geo, right_index=True, how="left")

_use_latest = ses_raw["_pli"].isna() & ses_raw["_pli_latest"].notna()
if _use_latest.any():
    _countries = sorted(set(ses_raw.loc[_use_latest, s_geo].astype(str)))
    warn_fallback(
        "PLI missing for exact SES year; latest available country PLI used for conversion "
        + ", ".join(_countries),
        source="Eurostat prc_ppp_ind",
    )
    ses_raw.loc[_use_latest, "_pli"] = ses_raw.loc[_use_latest, "_pli_latest"]

_missing_pli = ses_raw["_pli"].isna()
if _missing_pli.any():
    _countries_missing = sorted(set(ses_raw.loc[_missing_pli, s_geo].astype(str)))
    warn_fallback(
        "PLI unavailable for some SES rows; dropping unconvertible EUR rows (no EUR fallback) for "
        + ", ".join(_countries_missing),
        source="Eurostat prc_ppp_ind",
    )
    ses_raw = ses_raw[~_missing_pli].copy()

if ses_raw.empty:
    warn_fallback(
        "PLI unavailable for all SES rows; percentile profile omitted because EUR→PPS conversion is impossible",
        source="Eurostat prc_ppp_ind",
    )
else:
    ses_raw[s_val] = ses_raw[s_val] / ses_raw["_pli"]
    print("  EUR → PPS conversion applied")

ses_raw = ses_raw.drop(columns=["_pli_geo", "_pli_time", "_pli", "_pli_latest"], errors="ignore")

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
warn_non_target_year(source="Eurostat earn_ses_hourly", year=ses_year, context="SES percentile profile snapshot")

fig_b, ax_b = plt.subplots(figsize=cm2in(15, 9))

ses_ok = False
if _HAS_SES_DATA and s_indic and s_sex and s_geo:
    ses_ok = True

# Compute per-country gap (M − F) / M · 100 [%] at each percentile rank.
_gap_pivot_cols: dict[str, pd.Series] = {}
_xmax_rank = max(_INDIC_RANK.values())
for country in COUNTRIES:
    color = COUNTRY_COLORS.get(country, "#888888")
    sub = ses_snap[ses_snap[s_geo] == country].sort_values("_rank") if s_geo else pd.DataFrame()
    if not (ses_ok and not sub.empty and s_sex):
        continue
    sub_f = sub[sub[s_sex].astype(str).str.upper() == "F"].set_index("_rank")[s_val]
    sub_m = sub[sub[s_sex].astype(str).str.upper() == "M"].set_index("_rank")[s_val]
    common = sub_f.index.intersection(sub_m.index)
    if len(common) == 0:
        continue
    gap = (sub_m.loc[common] - sub_f.loc[common]).sort_index()
    ax_b.plot(gap.index, gap.values, color=color, linewidth=1.8, zorder=3)
    # Line-end country label (nudgeable via \Nudge… macros in TeX).
    last_rank = gap.index.max()
    ax_b.annotate(
        rf"\acs{{geo-{country}}}",
        xy=(last_rank, gap.loc[last_rank]),
        xytext=(4, 0),
        textcoords="offset points",
        fontsize=FIGURE_LABEL_SIZE,
        ha="left",
        va="center",
        color=color,
    )
    _gap_pivot_cols[country] = gap

if not ses_ok or not _gap_pivot_cols:
    ax_b.text(0.5, 0.5, "data\nnedostupná",
              ha="center", va="center",
              transform=ax_b.transAxes, fontsize=FIGURE_LABEL_SIZE, color="grey")
    ax_b.set_xticks([])
    ax_b.set_yticks([])

ranks = sorted(_INDIC_RANK.values())
ax_b.set_xticks(ranks)
ax_b.set_xticklabels([_INDIC_LABEL[r] for r in ranks], fontsize=FIGURE_LABEL_SIZE)
# Extend x-range slightly to accommodate line-end country labels.
ax_b.set_xlim(min(ranks) - 5, max(ranks) + 10)
ax_b.axhline(0, color="grey", linewidth=0.6, linestyle="--", alpha=0.7, zorder=1)
ax_b.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax_b.grid(which="minor", axis="y", linewidth=0.3, alpha=0.4)
ax_b.grid(which="major", axis="y", linewidth=0.6, alpha=0.7)
ax_b.tick_params(axis="both", labelsize=FIGURE_LABEL_SIZE)
STRINGS_STRAT = {
    "title": rf"Mzdový rozdíl mužů nad ženami podle percentilu ({ses_year})",
    "xlabel": "percentil mzdové distribuce",
    "ylabel": r"rozdíl \((M-F)\) [\si{\pps\per\hour}]",
}
ax_b.set_xlabel(STRINGS_STRAT["xlabel"], fontsize=FIGURE_LABEL_SIZE)
ax_b.set_ylabel(STRINGS_STRAT["ylabel"], fontsize=FIGURE_LABEL_SIZE)
ax_b.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:.1f}"))
ax_b.set_title(
    STRINGS_STRAT["title"],
    fontsize=FIGURE_TEXT_SIZE,
)

# Invisible hover tooltips at every (rank, gap) point.
if _gap_pivot_cols:
    _gap_pivot = pd.DataFrame(_gap_pivot_cols).sort_index()
    add_pgf_tooltips(ax_b, _gap_pivot, fmt="{:.2f}")

savefig_pgf(fig_b, "problemy_gpg_stratifikace", strings=STRINGS_STRAT, nudge_labels=NUDGE_LABELS)
save_figure_tex_pgf(
    "problemy_gpg_stratifikace",
    caption=(
        f"Mzdový rozdíl mužů nad ženami \\((M-F)\\) v~\\si{{\\pps\\per\\hour}} podle percentilu, vybrané země \\acs{{geo-EU}}, {ses_year}."
    ),
    cite_keys="eurostat_ses_hourly",
    label="fig:problemy_gpg_stratifikace",
    resizebox_width=r"\linewidth",
    cite_key="eurostat_ses_hourly",
    strings=STRINGS_STRAT,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
