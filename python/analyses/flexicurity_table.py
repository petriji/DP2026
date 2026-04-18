r"""
Comparative labour-market flexicurity table — CZ, DK, DE, AT, PL, SK.

Indicator set (2025 / latest available):

  1.  GDP per capita [EUR PPS/yr]                – nama_10_pc
      ↳  CZ = 100 (normalised)                  – derived
  2.  Labour cost [PPS/h, total economy]         – lc_lci_lev ÷ prc_ppp_ind
      ↳  CZ = 100                                – derived
  3.  Average weekly hours worked [h/wk]         – lfsa_ewhun2
      ↳  CZ = 100                                – derived
  4.  Tax wedge [%, 100 % AW, single, 0 child]   – earn_nt_taxwedge
  5.  Disposable income [PPS/h]  ← derived       – row 2 × (1 − row 4 / 100)
      ↳  CZ = 100                                – derived
  6.  Low-wage earners [% employees, < 2/3 med.] – earn_ses_pub1s
  7.  Gini coefficient                           – ilc_di12
  8.  Employment rate 20–64 [%]                  – lfsi_emp_a
  9.  Job vacancy rate [%, B–S excl. O]          – jvs_a_nace2  (→ -- on 404)
  10. CB coverage [%]                            – OECD ICTWSS AdjCov / CBC ERB, 2022–2024
  11. Trade union density [%]                    – OECD ICTWSS TUD, 2022–2024
  12. Active LMP spending [% GDP]                – OECD LMPEXP (→ -- on error)
  13. Old-age dependency ratio (65+) [%]         – demo_pjanind OLDDEP1

Row labels embed \cite{} for non-italic rows; caption contains year only.
Sub-rows (↳) and the derived row 5 are wrapped in \textit{} via italic_rows.

Output
------
  latex/texparts/python/flexicurity_table.tex

Run
---
    python analyses/flexicurity_table.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from stattool.fetch import fetch_eurostat, fetch_oecd
from stattool.dataset import Dataset
from statout.table import save_table_tex

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "DK", "DE", "AT", "PL", "SK"]
COUNTRY_LABELS = {
    "CZ": "Česko",
    "DK": "Dánsko",
    "DE": "Německo",
    "AT": "Rakousko",
    "PL": "Polsko",
    "SK": "Slovensko",
}
GEO = "+".join(COUNTRIES)
YEAR = 2025   # table reference year; falls back to nearest prior available

# ICTWSS ISO3 → ISO2 mapping (EU…27 subset needed here)
_ICTWSS_ISO3 = {
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "HRV": "HR", "CYP": "CY",
    "CZE": "CZ", "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR",
    "DEU": "DE", "GRC": "GR", "HUN": "HU", "IRL": "IE", "ITA": "IT",
    "LVA": "LV", "LTU": "LT", "LUX": "LU", "MLT": "MT", "NLD": "NL",
    "POL": "PL", "PRT": "PT", "ROU": "RO", "SVK": "SK", "SVN": "SI",
    "ESP": "ES", "SWE": "SE",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _latest_by_geo(
    ds: Dataset, year: int
) -> tuple[dict[str, float], dict[str, int]]:
    """Return ({country: value}, {country: actual_year_used}) for the given year or nearest prior."""
    df = ds.df.copy()
    df = df.sort_values(ds.time_col, ascending=False)
    values: dict[str, float] = {}
    years_used: dict[str, int] = {}
    for geo in COUNTRIES:
        sub = df[df[ds.geo_col] == geo]
        exact = sub[sub[ds.time_col] == year]
        if not exact.empty and pd.notna(exact.iloc[0][ds.value_col]):
            values[geo] = float(exact.iloc[0][ds.value_col])
            years_used[geo] = year
        else:
            prior = sub[sub[ds.time_col] <= year].dropna(subset=[ds.value_col])
            if not prior.empty:
                values[geo] = float(prior.iloc[0][ds.value_col])
                years_used[geo] = int(prior.iloc[0][ds.time_col])
    return values, years_used


def _normed_cz100(values: dict[str, float]) -> dict[str, float]:
    """Return {country: value / CZ_value * 100} for CZ-normalised sub-rows."""
    cz = values.get("CZ")
    if not cz:
        return {}
    return {c: v / cz * 100 for c, v in values.items()}


def _row(label: str, values: dict[str, float], fmt: str = "{:.1f}",
         suffix: str = "") -> dict:
    def _cell(c: str) -> str:
        v = values.get(c)
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "--"
        return fmt.format(v) + suffix
    return {"Indikátor": label, **{COUNTRY_LABELS[c]: _cell(c) for c in COUNTRIES}}


def _row_str(label: str, values: dict[str, str]) -> dict:
    return {"Indikátor": label,
            **{COUNTRY_LABELS[c]: values.get(c, "--") for c in COUNTRIES}}


# ── 1. Download datasets ──────────────────────────────────────────────────────

print("Downloading Eurostat data …")

# GDP per capita in PPS (EUR absolute)
ds_gdp = Dataset.from_sdmx_csv(
    fetch_eurostat("nama_10_pc", f"A.CP_PPS_EU27_2020_HAB.B1GQ.{GEO}"),
    name="GDP/cap PPS", unit="EUR PPS/yr",
    source_url="Eurostat/nama_10_pc",
)

# Average weekly hours worked (all employed, all sectors, 15–64)
ds_hrs = Dataset.from_sdmx_csv(
    fetch_eurostat("lfsa_ewhun2", f"A.TOTAL.EMP.TOTAL.Y15-64.T.HR.{GEO}"),
    name="Weekly hours", unit="h/wk",
    source_url="Eurostat/lfsa_ewhun2",
)

# Price level index (GDP, EU27 = 100) — used to convert EUR/h → PPS/h
ds_pli = Dataset.from_sdmx_csv(
    fetch_eurostat("prc_ppp_ind", f"A.PLI_EU27_2020.GDP.{GEO}",
                   start_period=YEAR - 3),
    name="PLI GDP", unit="EU27=100",
    source_url="Eurostat/prc_ppp_ind",
)

# Labour cost EUR/h (total business economy, all labour cost components)
# lc_lci_lev dimensions: freq · unit · lcstruct · nace_r2 · geo
# Try B-S_X_O (business excl. public admin), fall back to B-S.
ds_lc_eur: "Dataset | None" = None
_lc_nace = ""
for _nace in ("B-S_X_O", "B-S"):
    try:
        _lc_path = fetch_eurostat(
            "lc_lci_lev",
            f"A.EUR.D1_D4_MD5.{_nace}.{GEO}",
            start_period=YEAR - 3,
        )
        ds_lc_eur = Dataset.from_sdmx_csv(
            _lc_path,
            name="Labour cost EUR/h", unit="EUR/h",
            source_url=f"Eurostat/lc_lci_lev/{_nace}",
        )
        _lc_nace = _nace
        print(f"  lc_lci_lev: using nace_r2={_nace}")
        break
    except Exception as _e:
        print(f"  lc_lci_lev/{_nace}: {_e}")
if ds_lc_eur is None:
    print("  WARNING: labour cost unavailable — rows 3 and 5 will show --")

# Tax wedge (100 % AW, single, 0 children)
ds_tax = Dataset.from_sdmx_csv(
    fetch_eurostat("earn_nt_taxwedge", f"A.{GEO}"),
    name="Tax wedge 100% AW", unit="%",
    source_url="Eurostat/earn_nt_taxwedge",
)

# Gini coefficient (disposable income, equivalised)
ds_gini = Dataset.from_sdmx_csv(
    fetch_eurostat("ilc_di12", f"A.TOTAL.GINI_HND.{GEO}"),
    name="Gini", unit="",
    source_url="Eurostat/ilc_di12",
)

# Employment rate 20–64
ds_emp = Dataset.from_sdmx_csv(
    fetch_eurostat("lfsi_emp_a", f"A.EMP_LFS.T.Y20-64.PC_POP.{GEO}"),
    name="Employment rate 20–64", unit="%",
    source_url="Eurostat/lfsi_emp_a",
)

# Job vacancy rate (B–S excl. O) — try several filter variants; graceful fallback to --
# jvs_a_nace2 dimensions: freq · nace_r2 · sizeclas · indic_em · geo
# Note: startPeriod causes 400 on this dataset — omit it.
ds_jvr: "Dataset | None" = None
for _jvr_filter in (
    f"A.B-S_X_O.GE10.JVR.{GEO}",      # 5-dim (standard structure)
    f"A.TOTAL.GE10.JVR.{GEO}",         # nace_r2=TOTAL fallback
    f"A.B-S_X_O..JVR.{GEO}",           # all sizeclas
):
    try:
        ds_jvr = Dataset.from_sdmx_csv(
            fetch_eurostat("jvs_a_nace2", _jvr_filter),
            name="Job vacancy rate", unit="%",
            source_url="Eurostat/jvs_a_nace2",
        )
        print(f"  jvs_a_nace2: using filter={_jvr_filter}")
        break
    except Exception as _e:
        print(f"  jvs_a_nace2/{_jvr_filter}: {_e}")
if ds_jvr is None:
    print("  WARNING: job vacancy rate unavailable — row 8 will show --")

# Old-age dependency ratio (65+ per working-age 15–64)
ds_dep = Dataset.from_sdmx_csv(
    fetch_eurostat("demo_pjanind", f"A.OLDDEP1.{GEO}"),
    name="Old-age dep.", unit="%",
    source_url="Eurostat/demo_pjanind",
    filters={"indic_de": "OLDDEP1"},
)

# Active LMP expenditure (% GDP) — OECD LMPEXP
# (Eurostat lmp_expsumm was discontinued; OECD provides same coverage)
print("Downloading OECD APZ data …")
ds_apz: "Dataset | None" = None
try:
    from stattool.dataset import _OECD_ISO3_TO_ISO2
    _apz_path = fetch_oecd("LMPEXP", start_period=YEAR - 5)
    _apz_raw = pd.read_csv(_apz_path)
    _apz_raw = _apz_raw[
        (_apz_raw["MEASURE"] == "EXP") &
        (_apz_raw["UNIT_MEASURE"] == "PT_B1GQ") &
        (_apz_raw["PROGRAMME"] == "LMP_20T70")
    ].copy()
    _apz_raw = _apz_raw.rename(
        columns={"REF_AREA": "geo", "TIME_PERIOD": "time", "OBS_VALUE": "value"}
    )
    _apz_raw["geo"] = _apz_raw["geo"].map(
        lambda x: _OECD_ISO3_TO_ISO2.get(str(x).upper(), str(x))
    )
    _apz_raw = _apz_raw[["geo", "time", "value"]].dropna(subset=["value"])
    ds_apz = Dataset(_apz_raw, name="APZ výdaje", unit="% HDP",
                     source_url="OECD/LMPEXP")
except Exception as _e:
    print(f"  WARNING: APZ data unavailable ({_e}) — row 11 will show --")

# Low-wage earners (% of all employees, < 2/3 national median gross hourly earnings)
# earn_ses_pub1s dimensions: freq · sex · geo  (SES survey: latest round 2022)
ds_lowwage: "Dataset | None" = None
try:
    ds_lowwage = Dataset.from_sdmx_csv(
        fetch_eurostat("earn_ses_pub1s", f"A.T.{GEO}"),
        name="Nízkopříjmoví zaměstnanci", unit="%",
        source_url="Eurostat/earn_ses_pub1s",
        filters={"sex": "T"},
    )
except Exception as _e:
    print(f"  WARNING: earn_ses_pub1s unavailable ({_e}) — low-wage row will show --")

# CB coverage — AdjCov from ICTWSS v2 CSV (all COUNTRIES except DE)
#               + CBC ERB from OECD API (DE only; AdjCov for DE unavailable after 1990)
print("Downloading ICTWSS CB coverage data …")
import csv, urllib.request
from io import StringIO
_ICTWSS_URL = "https://webfs.oecd.org/Els-com/ICTWSS-Database/ICTWSS_v2.csv"
_adjcov_records: list[dict] = []
try:
    with urllib.request.urlopen(_ICTWSS_URL, timeout=60) as _resp:
        _reader = csv.DictReader(StringIO(_resp.read().decode("utf-8-sig")))
        for _row_ictwss in _reader:
            _iso3 = _row_ictwss.get("iso3", "").strip().upper()
            _iso2 = _ICTWSS_ISO3.get(_iso3)
            if not _iso2 or _iso2 == "DE":
                continue
            _val = _row_ictwss.get("AdjCov", "").strip()
            _yr  = _row_ictwss.get("year", "").strip()
            if _val and _yr:
                _adjcov_records.append({"geo": _iso2, "time": int(_yr), "value": float(_val)})
except Exception as _e:
    print(f"  WARNING: ICTWSS AdjCov unavailable ({_e})")

ds_cba_adjcov: "Dataset | None" = None
if _adjcov_records:
    _df_adj = pd.DataFrame(_adjcov_records)
    ds_cba_adjcov = Dataset(_df_adj, name="Pokrytí KV (AdjCov)", unit="%",
                            source_url="OECD AIAS ICTWSS / AdjCov")
    print(f"  AdjCov: {_df_adj['geo'].nunique()} countries, "
          f"years {_df_adj['time'].min()}–{_df_adj['time'].max()}")

# CBC ERB (OECD API) — DE only
ds_cba_erb: "Dataset | None" = None
try:
    from stattool.dataset import _OECD_ISO3_TO_ISO2 as _O3
    _path_cbc = fetch_oecd("CBC", start_period=YEAR - 10)
    _df_cbc = pd.read_csv(_path_cbc)
    _df_cbc = _df_cbc[_df_cbc.get("MEASURE", _df_cbc.get("INDICATOR", "")) == "ERB"].copy() \
        if "MEASURE" in _df_cbc.columns or "INDICATOR" in _df_cbc.columns \
        else _df_cbc.copy()
    # normalise column names
    _df_cbc = _df_cbc.rename(columns={
        "REF_AREA": "geo", "TIME_PERIOD": "time", "OBS_VALUE": "value",
    })
    _df_cbc["geo"] = _df_cbc["geo"].map(lambda x: _O3.get(str(x).upper(), str(x)))
    # DE: AdjCov unavailable after 1990; SK: AdjCov last available 2015 → use ERB for both
    _df_cbc = _df_cbc[_df_cbc["geo"].isin(["DE", "SK"])][["geo", "time", "value"]].dropna(subset=["value"])
    if not _df_cbc.empty:
        ds_cba_erb = Dataset(_df_cbc, name="Pokrytí KV ERB (DE)", unit="%",
                             source_url="OECD CBC / ERB")
        print(f"  CBC ERB/DE: years {_df_cbc['time'].min()}–{_df_cbc['time'].max()}")
except Exception as _e:
    print(f"  WARNING: OECD CBC ERB unavailable ({_e}) — DE CBA will show --")

# Merge AdjCov + ERB into one Dataset for CB coverage
_cba_parts = [ds.df for ds in (ds_cba_adjcov, ds_cba_erb) if ds is not None]
if _cba_parts:
    ds_cba = Dataset(pd.concat(_cba_parts, ignore_index=True),
                     name="Pokrytí KV", unit="%",
                     source_url="OECD AIAS ICTWSS / AdjCov+ERB")
else:
    ds_cba = None
    print("  WARNING: CB coverage data entirely unavailable")

# Trade union density — OECD TUD
print("Downloading OECD TUD (union density) data …")
ds_density: "Dataset | None" = None
try:
    _path_tud = fetch_oecd("TUD", start_period=YEAR - 10)
    ds_density = Dataset.from_oecd_csv(
        _path_tud,
        name="Hustota odborů", unit="%",
        source_url="OECD AIAS ICTWSS / TUD",
        filters={"INDICATOR": "TUD"},
    )
    ds_density.df = ds_density.df[ds_density.df["geo"] != "OECD"].copy()
    print(f"  TUD: years {ds_density.years[0]}–{ds_density.years[-1]}")
except Exception as _e:
    print(f"  WARNING: TUD unavailable ({_e}) — union density row will show --")

print("Downloads complete.")

# ── 2. Extract values for reference year ─────────────────────────────────────

v_gdp,  _yr_gdp  = _latest_by_geo(ds_gdp,  YEAR)
v_hrs,  _yr_hrs  = _latest_by_geo(ds_hrs,  YEAR)
v_pli,  _yr_pli  = _latest_by_geo(ds_pli,  YEAR)
v_tax,  _yr_tax  = _latest_by_geo(ds_tax,  YEAR)
v_gini, _yr_gini = _latest_by_geo(ds_gini, YEAR)
v_emp,  _yr_emp  = _latest_by_geo(ds_emp,  YEAR)
v_dep,  _yr_dep  = _latest_by_geo(ds_dep,  YEAR)
v_jvr,  _yr_jvr  = _latest_by_geo(ds_jvr, YEAR) if ds_jvr else ({}, {})
v_apz,     _yr_apz     = _latest_by_geo(ds_apz,    YEAR) if ds_apz    else ({}, {})
v_lowwage, _yr_lowwage = _latest_by_geo(ds_lowwage, YEAR) if ds_lowwage else ({}, {})
v_cba,     _yr_cba     = _latest_by_geo(ds_cba,     YEAR) if ds_cba    else ({}, {})
v_density, _yr_density = _latest_by_geo(ds_density, YEAR) if ds_density else ({}, {})

# Labour cost EUR/h → PPS/h  (÷ PLI/100)
if ds_lc_eur is not None:
    v_lc_eur, _yr_lc_eur = _latest_by_geo(ds_lc_eur, YEAR)
    v_lc_pps = {
        c: v_lc_eur[c] / (v_pli[c] / 100)
        for c in COUNTRIES
        if c in v_lc_eur and c in v_pli and v_pli[c]
    }
else:
    v_lc_eur, _yr_lc_eur, v_lc_pps = {}, {}, {}

# Derived: disposable income PPS/h = labour_cost_pps × (1 − tax_wedge/100)
v_disp = {
    c: v_lc_pps[c] * (1.0 - v_tax[c] / 100.0)
    for c in COUNTRIES
    if c in v_lc_pps and c in v_tax
}

# CZ-normalised sub-rows
v_gdp_idx  = _normed_cz100(v_gdp)
v_hrs_idx  = _normed_cz100(v_hrs)
v_lc_idx   = _normed_cz100(v_lc_pps)
v_disp_idx = _normed_cz100(v_disp)

# ── 3a. Check for year deviations, warn user, ask for caption year ───────────
_year_map: dict[str, dict[str, int]] = {
    "HDP/obyvatele":     _yr_gdp,
    "Odprac. hodiny":    _yr_hrs,
    "PLI":               _yr_pli,
    "Náklady práce EUR": _yr_lc_eur,
    "Daňový klín":       _yr_tax,
    "Gini":              _yr_gini,
    "Zaměstnanost":      _yr_emp,
    "JVR":               _yr_jvr,
    "Věk. závislost":    _yr_dep,
    "APZ výdaje":        _yr_apz,
    "Nízkopříjm. zaměst.": _yr_lowwage,
    "Pokrytí KV":        _yr_cba,
    "Hustota odborů":    _yr_density,
}

_deviations: list[tuple[str, str, int]] = [
    (ind, geo, yr)
    for ind, yr_dict in _year_map.items()
    for geo, yr in yr_dict.items()
    if yr != YEAR
]

_caption_year = str(YEAR)

if _deviations:
    print(f"\nNOTE: no {YEAR} data for the following — using nearest prior year:")
    for _ind, _geo, _yr in sorted(_deviations):
        print(f"  {_ind:<25}  {_geo}  →  {_yr}")

# Build footnote markers: one letter per deviation year, assigned in ascending order.
from collections import defaultdict as _dd
_yr_to_inds_set: dict[int, set[str]] = _dd(set)
for _ind, _geo, _yr in _deviations:
    _yr_to_inds_set[_yr].add(_ind)
_MARK_CHARS = ["a", "b", "c", "d", "e"]
_mark_for_yr: dict[int, str] = {
    yr: _MARK_CHARS[i] for i, yr in enumerate(sorted(_yr_to_inds_set))
}
_ind_to_mark: dict[str, str] = {
    ind: _mark_for_yr[yr]
    for yr, inds in _yr_to_inds_set.items()
    for ind in inds
}


def _m(label: str, ind_key: str) -> str:
    """Append footnote marker to a row label if its data uses a fallback year."""
    mark = _ind_to_mark.get(ind_key, "")
    if not mark:
        return label
    sup = r"\textsuperscript{" + mark + r"}"
    if r"~\cite{" in label:
        return label.replace(r"~\cite{", sup + r"~\cite{", 1)
    return label + sup


# ── 3. Row label strings ──────────────────────────────────────────────────────

_SUB = r"\hspace{1.5em} (ČR\,=\,100\,\%)"

L_GDP      = _m(r"HDP [\ac{PPS}/os./rok]~\cite{eurostat_nama_10_pc}", "HDP/obyvatele")
L_GDP_IDX  = _SUB
L_LC       = _m(r"Úplné náklady práce [\ac{PPS}/h]~\cite{eurostat_lc_lci_lev}", "Náklady práce EUR")
L_LC_IDX   = _SUB
L_HRS      = _m(r"Odpracované hodiny [h/týd., průměr]~\cite{eurostat_lfsa_ewhun2}", "Odprac. hodiny")
L_HRS_IDX  = _SUB
L_TAX      = _m(r"Daňový klín (100\,\% prům.)~\cite{eurostat_earn_nt_taxwedge}", "Daňový klín")
L_DISP     = r"Disponibilní příjem [\ac{PPS}/h, průměrný]"  # italic — derived, no \cite{}
L_DISP_IDX = _SUB
L_LOWWAGE  = _m(r"Nízkopříjmoví zaměstnanci (2/3 mediánu)\,\%~\cite{eurostat_earn_ses_pub1s}", "Nízkopříjm. zaměst.")
L_GINI     = _m(r"Giniho koeficient~\cite{eurostat_ilc_di12}", "Gini")
L_EMP      = _m(r"Zaměstnanost (20--64 let)\,\%~\cite{eurostat_lfsi_emp_a}", "Zaměstnanost")
L_JVR      = _m(r"Volná prac. místa~\cite{eurostat_jvs_a_nace2}", "JVR")
L_CBA      = _m(r"Pokrytí \ac{KS}\,\%~\cite{oecd_aias_ictwss_CBC_ERB_pct}", "Pokrytí KV")
L_DENSITY  = _m(r"Hustota odborů\,\%~\cite{oecd_aias_ictwss_TUD_pct}", "Hustota odborů")
L_APZ      = _m(r"Výdaje na \ac{APZ}\,[\%\,\ac{HDP}]~\cite{oecd_lmpexp}", "APZ výdaje")
L_DEP      = _m(r"Index závislosti seniorů (65+)~\cite{eurostat_demo_pjanind}", "Věk. závislost")

# ── 4. Build table DataFrame ──────────────────────────────────────────────────

rows = [
    # ── GDP ───────────────────────────────────────────────────────────────────
    _row(L_GDP,      v_gdp,      fmt="{:,.0f}", suffix=r"\,€"),
    _row(L_GDP_IDX,  v_gdp_idx,  fmt="{:.1f}"),
    # ── Labour cost ───────────────────────────────────────────────────────────
    _row(L_LC,       v_lc_pps,   fmt="{:.1f}"),
    _row(L_LC_IDX,   v_lc_idx,   fmt="{:.1f}"),
    # ── Working hours ─────────────────────────────────────────────────────────
    _row(L_HRS,      v_hrs,      fmt="{:.1f}",  suffix=r"\,h"),
    _row(L_HRS_IDX,  v_hrs_idx,  fmt="{:.1f}"),
    # ── Tax group ─────────────────────────────────────────────────────────────
    _row(L_TAX,      v_tax,      fmt="{:.1f}",  suffix=r"\,\%"),
    # ── Derived disposable income (italic, no \cite{}) ────────────────────────
    _row(L_DISP,     v_disp,     fmt="{:.1f}"),
    _row(L_DISP_IDX, v_disp_idx, fmt="{:.1f}"),
    # ── Low-wage earners ──────────────────────────────────────────────────────
    _row(L_LOWWAGE,  v_lowwage,  fmt="{:.1f}",  suffix=r"\,\%"),
    # ── Inequality ────────────────────────────────────────────────────────────
    _row(L_GINI,     v_gini,     fmt="{:.1f}"),
    # ── Employment ────────────────────────────────────────────────────────────
    _row(L_EMP,      v_emp,      fmt="{:.1f}",  suffix=r"\,\%"),
    _row(L_JVR,      v_jvr,      fmt="{:.1f}",  suffix=r"\,\%"),
    # ── Social dialogue (OECD AIAS ICTWSS) ─────────────────────────────────────────
    _row(L_CBA,     v_cba,     fmt="{:.0f}", suffix=r"\,\%"),
    _row(L_DENSITY, v_density, fmt="{:.0f}", suffix=r"\,\%"),
    # ── Policy / demographics ─────────────────────────────────────────────────
    _row(L_APZ,      v_apz,      fmt="{:.2f}",  suffix=r"\,\%"),
    _row(L_DEP,      v_dep,      fmt="{:.1f}",  suffix=r"\,\%"),
]

df_table = (
    pd.DataFrame(rows)
    .set_index("Indikátor")
)
df_table = df_table[[COUNTRY_LABELS[c] for c in COUNTRIES]]

# ── 5. Structural parameters ──────────────────────────────────────────────────

italic_rows = [L_GDP_IDX, L_LC_IDX, L_HRS_IDX, L_DISP, L_DISP_IDX]

midrule_after = [
    L_HRS_IDX,  # end of pay/work block (GDP, LC, HRS)
    L_TAX,      # end of tax group
    L_DISP_IDX, # end of derived income group
    L_LOWWAGE,  # end of low-wage group
    L_GINI,     # end of inequality group
    L_JVR,      # end of employment group
    L_DENSITY,  # end of social-dialogue group
]

# ── 6. Write LaTeX table ──────────────────────────────────────────────────────

# Build footnote: one entry per fallback year with its letter marker.
_deviation_note = ""
if _mark_for_yr:
    _note_parts = [
        r"\textsuperscript{" + mark + r"}~nejnovější data " + str(yr)
        for yr, mark in sorted(_mark_for_yr.items())
    ]
    _deviation_note = " " + "; ".join(_note_parts) + "."

save_table_tex(
    df_table,
    "flexicurity_table",
    caption=(
        f"Vybrané ukazatele trhu práce — "
        f"{', '.join(COUNTRY_LABELS[c] for c in COUNTRIES)}. "
        f"Data za rok {_caption_year}."
    ),
    label="tab:flexicurity",
    note=(
        r"Náklady práce v \ac{PPS}/h\,=\,EUR/h\,$\div$\,(\ac{PLI}/100). "
        r"Disponibilní příjem\,=\,náklady práce\,$\times$\,$(1-\text{daňový klín}/100)$. "
        r"Daňový klín pro bezdětnou svobodnou osobu (single, 0~dětí). "
        r"Pokrytí \ac{KS}: OECD / AIAS ICTWSS \textit{AdjCov} (CZ, DK, AT, PL), "
        r"DE a SK: ERB (\textit{AdjCov} $\neq$ ERB). "
        r"Hustota odborů: ICTWSS \textit{TUD}."
        + _deviation_note
    ),
    col_format="Xrrrrrr",
    col_headers=COUNTRIES,
    index_name="Indikátor",
    midrule_after=midrule_after,
    italic_rows=italic_rows,
    long_table=True,
)
print("Done.")
