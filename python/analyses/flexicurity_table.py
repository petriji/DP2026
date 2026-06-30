r"""
Comparative labour-market flexicurity table — CZ, DK, DE, AT, PL, SK.

Indicator set (2024 / latest available):

  1.  GDP per capita [EUR PPS/yr]                – nama_10_pc
      ↳  CZ = 100 (normalised)                  – derived
  2.  Average weekly hours worked [h/wk]         – lfsa_ewhun2
      ↳  CZ = 100                                – derived
  3.  Labour cost [PPS/h, total economy]         – lc_lci_lev ÷ prc_ppp_ind
      ↳  CZ = 100                                – derived
  4.  Tax wedge [%, 100 % AW, single, 0 child]   – earn_nt_taxwedge
  5.  Disposable income [PPS/h]  ← derived       – row 3 × (1 − row 4 / 100)
      ↳  CZ = 100                                – derived
  6.  Gini coefficient                           – ilc_di12
  7.  Employment rate 20–64 [%]                  – lfsi_emp_a
  8.  Job vacancy rate [%, B–S excl. O]          – jvs_a_nace2  (→ -- on 404)
  9.  CB coverage [%]                            – ETUI static ≈ 2022–2024
  10. Trade union density [%]                    – ETUI static ≈ 2022–2024
  11. Active LMP spending [% GDP]                – OECD LMPEXP (→ -- on error)
  12. Old-age dependency ratio (65+) [%]         – demo_pjanind OLDDEP1

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

# Static data (ETUI Working Conditions Database / OECD, approx. 2022–2024)
_CB_COVERAGE   = {"CZ": r"32\,\%", "DK": r"80\,\%", "DE": r"52\,\%",
                  "AT": r"98\,\%", "PL": r"15\,\%", "SK": r"35\,\%"}
_UNION_DENSITY = {"CZ": r"11\,\%", "DK": r"67\,\%", "DE": r"16\,\%",
                  "AT": r"26\,\%", "PL": r"12\,\%", "SK": r"13\,\%"}

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

# Job vacancy rate (B–S excl. O) — try; graceful fallback to --
# jvs_a_nace2 dimensions: freq · nace_r2 · sizeclas · isco08 · indic_em · geo
# Note: startPeriod causes 400 on this dataset — omit it.
ds_jvr: "Dataset | None" = None
try:
    ds_jvr = Dataset.from_sdmx_csv(
        fetch_eurostat("jvs_a_nace2", f"A.B-S_X_O.GE10.TOTAL.JVR.{GEO}"),
        name="Job vacancy rate", unit="%",
        source_url="Eurostat/jvs_a_nace2",
    )
except Exception as _e:
    print(f"  WARNING: job vacancy rate unavailable ({_e}) — row 8 will show --")

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
        (_apz_raw["PROGRAMME"] == "_T")
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
v_apz,  _yr_apz  = _latest_by_geo(ds_apz, YEAR) if ds_apz else ({}, {})

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
}

_deviations: list[tuple[str, str, int]] = [
    (ind, geo, yr)
    for ind, yr_dict in _year_map.items()
    for geo, yr in yr_dict.items()
    if yr != YEAR
]

if _deviations:
    print(f"\nWARNING: no {YEAR} data for the following — using nearest prior year:")
    for _ind, _geo, _yr in sorted(_deviations):
        print(f"  {_ind:<25}  {_geo}  →  {_yr}")
    _fallback_years = sorted({yr for _, _, yr in _deviations})
    _suggest = (
        f"{_fallback_years[0]}\u2013{YEAR}"
        if len(_fallback_years) > 1 or _fallback_years[0] != YEAR
        else str(YEAR)
    )
    print(f"\nSuggested caption year: \"{_suggest} (nebo nejbližší dostupný)\"")
    _caption_year = input(f"Caption year text [{_suggest}]: ").strip() or _suggest
else:
    _caption_year = str(YEAR)

# ── 3. Row label strings ──────────────────────────────────────────────────────

_SUB = r"\hspace{1.5em}↳ (ČR\,=\,100\,\%)"

L_GDP      = r"HDP/obyvatele [\ac{PPS}/os./rok]~\cite{eurostat_nama_10_pc}"
L_GDP_IDX  = _SUB
L_HRS      = r"Odpracované hodiny [h/týd.]~\cite{eurostat_lfsa_ewhun2}"
L_HRS_IDX  = _SUB
L_LC       = r"Náklady práce [\ac{PPS}/h]~\cite{eurostat_lc_lci_lev}"
L_LC_IDX   = _SUB
L_TAX      = r"Daňový klín (100\,\% AW)~\cite{eurostat_earn_nt_taxwedge}"
L_DISP     = r"Disp. příjem [\ac{PPS}/h]"      # italic — derived, no \cite{}
L_DISP_IDX = _SUB
L_GINI     = r"Giniho koeficient~\cite{eurostat_ilc_di12}"
L_EMP      = r"Zaměstnanost 20--64\,\%~\cite{eurostat_lfsi_emp_a}"
L_JVR      = r"Volná prac. místa [JVR\,\%]~\cite{eurostat_jvs_a_nace2}"
L_CBA      = r"Pokrytí \ac{KS}\,\%~\cite{etui_cba}"
L_DENSITY  = r"Hustota odborů\,\%~\cite{etui_density}"
L_APZ      = r"Výdaje na \ac{APZ}\,[\%\,\ac{HDP}]~\cite{oecd_lmpexp}"
L_DEP      = r"Věk. závislost (65+)~\cite{eurostat_demo_pjanind}"

# ── 4. Build table DataFrame ──────────────────────────────────────────────────

rows = [
    # ── Productivity group ────────────────────────────────────────────────────
    _row(L_GDP,      v_gdp,      fmt="{:,.0f}", suffix=r"\,€"),
    _row(L_GDP_IDX,  v_gdp_idx,  fmt="{:.1f}"),
    _row(L_HRS,      v_hrs,      fmt="{:.1f}",  suffix=r"\,h"),
    _row(L_HRS_IDX,  v_hrs_idx,  fmt="{:.1f}"),
    _row(L_LC,       v_lc_pps,   fmt="{:.1f}"),
    _row(L_LC_IDX,   v_lc_idx,   fmt="{:.1f}"),
    # ── Tax group ─────────────────────────────────────────────────────────────
    _row(L_TAX,      v_tax,      fmt="{:.1f}",  suffix=r"\,\%"),
    # ── Derived disposable income (italic, no \cite{}) ────────────────────────
    _row(L_DISP,     v_disp,     fmt="{:.1f}"),
    _row(L_DISP_IDX, v_disp_idx, fmt="{:.1f}"),
    # ── Inequality ────────────────────────────────────────────────────────────
    _row(L_GINI,     v_gini,     fmt="{:.1f}"),
    # ── Employment ────────────────────────────────────────────────────────────
    _row(L_EMP,      v_emp,      fmt="{:.1f}",  suffix=r"\,\%"),
    _row(L_JVR,      v_jvr,      fmt="{:.1f}",  suffix=r"\,\%"),
    # ── Social dialogue (static ETUI) ─────────────────────────────────────────
    _row_str(L_CBA,     _CB_COVERAGE),
    _row_str(L_DENSITY, _UNION_DENSITY),
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

italic_rows = [L_GDP_IDX, L_HRS_IDX, L_LC_IDX, L_DISP, L_DISP_IDX]

midrule_after = [
    L_LC_IDX,   # end of productivity group
    L_TAX,      # end of tax group
    L_DISP_IDX, # end of derived income group
    L_GINI,     # end of inequality group
    L_JVR,      # end of employment group
    L_DENSITY,  # end of social-dialogue group
]

# ── 6. Write LaTeX table ──────────────────────────────────────────────────────

# Build footnote: group year deviations by year → indicators (+ countries if partial)
_deviation_parts: list[str] = []
if _deviations:
    from collections import defaultdict
    _yr_to_inds: dict[int, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for _ind, _geo, _yr in _deviations:
        _yr_to_inds[_yr][_ind].append(_geo)
    for _yr in sorted(_yr_to_inds):
        _pieces: list[str] = []
        for _ind, _geos in sorted(_yr_to_inds[_yr].items()):
            if set(_geos) == set(COUNTRIES):
                _pieces.append(_ind)
            else:
                _pieces.append(f"{_ind} ({', '.join(_geos)})")
        _deviation_parts.append(f"{', '.join(_pieces)}: {_yr}")
_deviation_note = (
    " Ukazatele za jiný rok (nejbližší dostupný): " + "; ".join(_deviation_parts) + "."
    if _deviation_parts else ""
)

save_table_tex(
    df_table,
    "flexicurity_table",
    caption=(
        f"Vybrané ukazatele trhu práce — "
        f"{', '.join(COUNTRY_LABELS[c] for c in COUNTRIES)}. "
        f"Data za rok {_caption_year} (nebo nejbližší dostupný)."
    ),
    label="tab:flexicurity",
    note=(
        r"Náklady práce v \ac{PPS}/h\,=\,EUR/h\,\div\,(PLI/100). "
        r"Disp. příjem\,=\,náklady práce\,$\times$\,$(1-\text{daňový klín}/100)$. "
        r"Zdroj statických dat (KS pokrytí, hustota odborů): ETUI, cca 2022--2024."
        + _deviation_note
                _pieces.append(f"{_ind} ({', '.join(_geos)})")
        _deviation_parts.append(f"{', '.join(_pieces)}: {_yr}")
_deviation_note = (
    " Ukazatele za jiný rok (nejbližší dostupný): " + "; ".join(_deviation_parts) + "."
    if _deviation_parts else ""
)

save_table_tex(
    df_table,
    "flexicurity_table",
    caption=(
        f"Vybrané ukazatele trhu práce — "
        f"{', '.join(COUNTRY_LABELS[c] for c in COUNTRIES)}. "
        f"Data za rok {_caption_year} (nebo nejbližší dostupný)."
    ),
    label="tab:flexicurity",
    note=(
        r"Náklady práce v \ac{PPS}/h\,=\,EUR/h\,\div\,(PLI/100). "
        r"Disp. příjem\,=\,náklady práce\,$\times$\,$(1-\text{daňový klín}/100)$. "
        r"Zdroj statických dat (KS pokrytí, hustota odborů): ETUI, cca 2022--2024."
        + _deviation_note
    ),
    col_format="Xrrrrrr",
    index_name="Indikátor",
    midrule_after=midrule_after,
    italic_rows=italic_rows,
)
print("Done.")
