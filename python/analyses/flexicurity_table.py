r"""
Comparative labour-market table – DK, CZ, DE, AT, PL, SK.

Extends the table in PETŘÍČEK, J.: How Flexicurity Works in Denmark (2026)
with Poland and Slovakia.

Indicators pulled from Eurostat REST API:
  1. GDP/capita (PPS, absolute EUR)          – nama_10_pc
  2. GDP/capita (PPS, EU27 = 100 index)      – nama_10_pc
  3. Gini coefficient (disposable income)    – ilc_di12
  4. Employment rate 20–64                   – lfsi_emp_a
  5. Tax wedge (100 % AW, single, 0 child)   – earn_nt_taxwedge
  6. AROPE rate                              – ilc_peps01n
  7. Avg. weekly hours worked                – lfsa_ewhun2
  8. Old-age dependency ratio (65+/15–64)    – demo_pjanind
  9. Price level index (GDP, EU27 = 100)     – prc_ppp_ind

Static data from ETUI / OECD (updated manually):
 10. Trade union density                     – ETUI/OECD ≈ 2022
 11. Collective bargaining coverage          – ETUI ≈ 2022

Output
------
  latex/texparts/flexicurity_table.tex  ← \input{} this in main.tex

Run
---
    python analyses/flexicurity_table.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from statout.table import save_table_tex

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["DK", "CZ", "DE", "AT", "PL", "SK"]
COUNTRY_LABELS = {
    "DK": "Dánsko",
    "CZ": "Česko",
    "DE": "Německo",
    "AT": "Rakousko",
    "PL": "Polsko",
    "SK": "Slovensko",
}
GEO = "+".join(COUNTRIES)
YEAR = 2023   # Table reference year; falls back to closest available

# Static data (ETUI Working Conditions Database / OECD, approx. 2022)
_UNION_DENSITY = {"DK": r"67\,\%", "CZ": r"11\,\%", "DE": r"16\,\%", "AT": r"26\,\%", "PL": r"12\,\%", "SK": r"13\,\%"}
_CB_COVERAGE   = {"DK": r"80\,\%", "CZ": r"32\,\%", "DE": r"52\,\%", "AT": r"98\,\%", "PL": r"15\,\%", "SK": r"35\,\%"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _latest_by_geo(ds: Dataset, year: int) -> dict[str, float]:
    """Return {country: value} for the given year (or nearest prior year)."""
    df = ds.df.copy()
    df = df.sort_values("time", ascending=False)
    result: dict[str, float] = {}
    for geo in COUNTRIES:
        sub = df[df[ds.geo_col] == geo]
        # Try exact year first, then fall back to most recent <= year
        exact = sub[sub[ds.time_col] == year]
        if not exact.empty and pd.notna(exact.iloc[0][ds.value_col]):
            result[geo] = float(exact.iloc[0][ds.value_col])
        else:
            prior = sub[sub[ds.time_col] <= year].dropna(subset=[ds.value_col])
            if not prior.empty:
                result[geo] = float(prior.iloc[0][ds.value_col])
    return result


def _row(label: str, values: dict[str, float], fmt: str = "{:.1f}",
         suffix: str = "") -> dict:
    def _cell(c):
        v = values.get(c)
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "--"
        return fmt.format(v) + suffix
    return {"Indikátor": label, **{COUNTRY_LABELS[c]: _cell(c) for c in COUNTRIES}}


def _row_str(label: str, values: dict[str, str]) -> dict:
    return {"Indikátor": label, **{COUNTRY_LABELS[c]: values.get(c, "--") for c in COUNTRIES}}


# ── 1. Download all indicators ────────────────────────────────────────────────

print("Downloading Eurostat data …")

# GDP per capita in PPS (EUR absolute)
ds_gdp = Dataset.from_sdmx_csv(
    fetch_eurostat("nama_10_pc", f"A.CP_PPS_EU27_2020_HAB.B1GQ.{GEO}"),
    name="GDP/cap PPS", unit="EUR PPS",
    source_url="Eurostat/nama_10_pc",
)
# GDP per capita index (EU27 = 100)
ds_gdp_idx = Dataset.from_sdmx_csv(
    fetch_eurostat("nama_10_pc", f"A.PC_EU27_2020_HAB_MPPS_CP.B1GQ.{GEO}"),
    name="GDP/cap index", unit="EU27=100",
    source_url="Eurostat/nama_10_pc",
)
# Gini coefficient
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
# Tax wedge
ds_tax = Dataset.from_sdmx_csv(
    fetch_eurostat("earn_nt_taxwedge", f"A.{GEO}"),
    name="Tax wedge", unit="%",
    source_url="Eurostat/earn_nt_taxwedge",
)
# AROPE rate
ds_arope = Dataset.from_sdmx_csv(
    fetch_eurostat("ilc_peps01n", f"A.PC.TOTAL.T.{GEO}"),
    name="AROPE", unit="%",
    source_url="Eurostat/ilc_peps01n",
    filters={"sex": "T", "age": "TOTAL"},
)
# Average weekly hours (all employees, all sectors, 15–64)
ds_hrs = Dataset.from_sdmx_csv(
    fetch_eurostat("lfsa_ewhun2", f"A.TOTAL.EMP.TOTAL.Y15-64.T.HR.{GEO}"),
    name="Weekly hours", unit="h",
    source_url="Eurostat/lfsa_ewhun2",
)
# Old-age dependency ratio (65+ per 100 working-age 15–64)
ds_dep = Dataset.from_sdmx_csv(
    fetch_eurostat("demo_pjanind", f"A.OLDDEP1.{GEO}"),
    name="Old-age dep.", unit="%",
    source_url="Eurostat/demo_pjanind",
)
# Price level index (GDP, EU27 = 100)
ds_pli = Dataset.from_sdmx_csv(
    fetch_eurostat("prc_ppp_ind", f"A.PLI_EU27_2020.GDP.{GEO}"),
    name="PLI GDP", unit="EU27=100",
    source_url="Eurostat/prc_ppp_ind",
)

print("Download complete.")

# ── 2. Extract values for reference year ─────────────────────────────────────

v_gdp      = _latest_by_geo(ds_gdp, YEAR)
v_gdp_idx  = _latest_by_geo(ds_gdp_idx, YEAR)
v_gini     = _latest_by_geo(ds_gini, YEAR)
v_emp      = _latest_by_geo(ds_emp, YEAR)
v_tax      = _latest_by_geo(ds_tax, YEAR)
v_arope    = _latest_by_geo(ds_arope, YEAR)
v_hrs      = _latest_by_geo(ds_hrs, YEAR)
v_dep      = _latest_by_geo(ds_dep, YEAR)
v_pli      = _latest_by_geo(ds_pli, YEAR)

# ── 3. Build table DataFrame ──────────────────────────────────────────────────

year_used = max(v_gdp_idx.get("CZ", YEAR - 1), YEAR - 2)  # approximate

rows = [
    _row("HDP/obyvatele (EUR PPS)",          v_gdp,     fmt="{:,.0f}", suffix="\\,€"),
    _row("HDP/obyvatele (EU27\\,=\\,100)",   v_gdp_idx, fmt="{:.1f}"),
    _row("Giniho koeficient",                v_gini,    fmt="{:.3f}"),
    _row("Zaměstnanost 20--64",              v_emp,     fmt="{:.1f}", suffix="\\,\\%"),
    _row("Daňový klín 100\\,\\% AW",         v_tax,     fmt="{:.1f}", suffix="\\,\\%"),
    _row("AROPE",                            v_arope,   fmt="{:.1f}", suffix="\\,\\%"),
    _row("Prům. týd. prac. hodiny",          v_hrs,     fmt="{:.1f}", suffix="\\,h"),
    _row("Index věkové závislosti",          v_dep,     fmt="{:.1f}", suffix="\\,\\%"),
    _row("Cenová hladina (EU27\\,=\\,100)",  v_pli,     fmt="{:.1f}"),
    _row_str("Hustota odborů\\,\\textsuperscript{a}",           _UNION_DENSITY),
    _row_str("Pokr. kol. vyjednáváním\\,\\textsuperscript{a}",  _CB_COVERAGE),
]

df_table = (
    pd.DataFrame(rows)
    .set_index("Indikátor")
    .rename(columns=COUNTRY_LABELS)
)
# Ensure country column order
df_table = df_table[[COUNTRY_LABELS[c] for c in COUNTRIES]]

# ── 4. Write LaTeX table ──────────────────────────────────────────────────────

actual_year = max(v_gdp.keys(), key=lambda c: v_gdp.get(c, 0), default=str(YEAR))
note = (
    "Data přibližně z roku "
    + str(YEAR)
    + "."
    " \\textsuperscript{a}~ETUI\u00a0/\u00a0OECD, cca\u00a02022."
)

save_table_tex(
    df_table,
    "flexicurity_table",
    caption=(
        "Srovnání vybraných ukazatelů trhu práce pro "
        "Dánsko, Česko, Německo, Rakousko, Polsko a Slovensko."
    ),
    label="tab:flexicurity",
    note=note,
    cite_keys=[
        "eurostat_nama_10_pc",
        "eurostat_ilc_di12",
        "eurostat_lfsi_emp_a",
        "eurostat_earn_nt_taxwedge",
        "eurostat_ilc_peps01n",
        "eurostat_lfsa_ewhun2",
        "eurostat_demo_pjanind",
        "eurostat_prc_ppp_ind",
        "etui_cba",
    ],
    col_format="Xrrrrrr",
    index_name="Indikátor",
)
print("Done.")
