"""Shared data-loading helpers for thesis analyses.

Centralises repeated dataset fetches so that filter logic (LMP active-only,
ICTWSS AdjCov + CBC ERB merge, etc.) is defined in one place.
"""

from __future__ import annotations

import csv
import logging
from io import StringIO
from pathlib import Path
from typing import Optional

import pandas as pd

from stattool.dataset import Dataset, _OECD_ISO3_TO_ISO2
from stattool.fetch import fetch, fetch_eurostat, fetch_ipp, fetch_oecd

log = logging.getLogger(__name__)

# ISO-3166 alpha-3 → alpha-2 for EU-27 member states
_ISO3_TO_ISO2: dict[str, str] = {
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "HRV": "HR", "CYP": "CY",
    "CZE": "CZ", "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR",
    "DEU": "DE", "GRC": "GR", "HUN": "HU", "IRL": "IE", "ITA": "IT",
    "LVA": "LV", "LTU": "LT", "LUX": "LU", "MLT": "MT", "NLD": "NL",
    "POL": "PL", "PRT": "PT", "ROU": "RO", "SVK": "SK", "SVN": "SI",
    "ESP": "ES", "SWE": "SE",
}
_EU27_ISO3 = set(_ISO3_TO_ISO2.keys())

_ICTWSS_URL = "https://webfs.oecd.org/Els-com/ICTWSS-Database/ICTWSS_v2.csv"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Collective-bargaining coverage (ICTWSS AdjCov + OECD CBC ERB for DE, SK, SI)
# ═══════════════════════════════════════════════════════════════════════════════

def load_cb_coverage(*, start_period: int = 1990) -> Dataset:
    """Load CB coverage: ICTWSS AdjCov for EU-27 (exc. DE, SK, SI) + OECD CBC ERB."""
    # ── ICTWSS AdjCov ─────────────────────────────────────────────────────────
    ictwss_path = fetch(_ICTWSS_URL, suffix=".csv")
    raw_csv = ictwss_path.read_text(encoding="utf-8-sig")

    reader = csv.DictReader(StringIO(raw_csv))
    adjcov_records: list[dict] = []
    for row in reader:
        iso3 = row.get("iso3", "").strip().upper()
        if iso3 not in _EU27_ISO3 or iso3 in ("DEU", "SVK", "SVN"):
            continue
        val = row.get("AdjCov", "").strip()
        year = row.get("year", "").strip()
        if not val or not year:
            continue
        adjcov_records.append({
            "geo": _ISO3_TO_ISO2[iso3],
            "time": int(year),
            "value": float(val),
        })
    df_adjcov = pd.DataFrame(adjcov_records)

    # ── OECD CBC ERB (DE, SK, SI) ─────────────────────────────────────────────
    path_cbc = fetch_oecd("CBC", start_period=start_period)
    ds_cbc = Dataset.from_oecd_csv(
        path_cbc,
        name="Pokrytí KV",
        unit="%",
        source_url="OECD AIAS ICTWSS / CBC (ERB)",
        filters={"MEASURE": "ERB"},
    )
    df_erb = ds_cbc.df[ds_cbc.df["geo"].isin(["DE", "SK", "SI"])][
        ["geo", "time", "value"]
    ].copy()

    # ── Merge ─────────────────────────────────────────────────────────────────
    df = pd.concat([df_adjcov, df_erb], ignore_index=True)
    df = df[df["time"] >= start_period]

    return Dataset(
        df,
        name="Pokrytí KV",
        unit="%",
        source_url="ICTWSS AdjCov; OECD CBC ERB (DE, SK, SI)",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Trade union density (OECD TUD)
# ═══════════════════════════════════════════════════════════════════════════════

def load_union_density(*, start_period: int = 1990) -> Dataset:
    """Load trade union density from OECD AIAS ICTWSS / TUD."""
    path = fetch_oecd("TUD", start_period=start_period)
    ds = Dataset.from_oecd_csv(
        path,
        name="Hustota odborů",
        unit="%",
        source_url="OECD AIAS ICTWSS / TUD",
        filters={"INDICATOR": "TUD"},
    )
    ds.df = ds.df[ds.df["geo"] != "OECD"].copy()
    return ds


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Price level index (Eurostat prc_ppp_ind, GDP, EU27_2020 = 100)
# ═══════════════════════════════════════════════════════════════════════════════

def load_pli(*, start_period: int = 2005) -> Dataset:
    """Load PLI (GDP) for all countries. EU27 = 100 by definition."""
    path = fetch_eurostat(
        "prc_ppp_ind",
        f"A.PLI_EU27_2020.GDP.",
        start_period=start_period,
    )
    raw = pd.read_csv(path)
    raw = raw[["geo", "TIME_PERIOD", "OBS_VALUE"]].dropna(subset=["OBS_VALUE"])
    raw.columns = ["geo", "time", "value"]
    raw["time"] = raw["time"].astype(int)

    return Dataset(
        raw,
        name="Index cenové hladiny (PLI)",
        unit="EU27=100",
        source_url="Eurostat/prc_ppp_ind",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Active LMP expenditure (OECD LMPEXP, categories 2--7, % GDP)
# ═══════════════════════════════════════════════════════════════════════════════

def load_lmp_active(*, start_period: int = 1998) -> Dataset:
    """Load active LMP expenditure (cat. 2--7) as % GDP."""
    path = fetch_oecd("LMPEXP", start_period=start_period)
    raw = pd.read_csv(path)
    raw = raw[
        (raw["MEASURE"] == "EXP")
        & (raw["UNIT_MEASURE"] == "PT_B1GQ")
        & (raw["PROGRAMME"] == "LMP_20T70")
    ].copy()
    raw = raw.rename(columns={
        "REF_AREA": "geo",
        "TIME_PERIOD": "time",
        "OBS_VALUE": "value",
    })
    raw["geo"] = raw["geo"].map(
        lambda x: _OECD_ISO3_TO_ISO2.get(str(x).upper(), str(x))
    )
    raw = raw[["geo", "time", "value"]].dropna(subset=["value"])

    ds = Dataset(raw, name="Výdaje na APZ", unit="% HDP", source_url="OECD/LMPEXP")
    ds.df = ds.df[ds.df["geo"] != "OECD"].copy()
    return ds


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Employer organisation density (ICTWSS ED)
# ═══════════════════════════════════════════════════════════════════════════════

def load_employer_density(*, start_period: int = 1990) -> Dataset:
    """Load employer organisation density (ED) from ICTWSS v2 CSV.

    ED = share of employees working in firms that belong to an employer
    organisation (%).  Data are sparse for most EU-27 countries.
    """
    ictwss_path = fetch(_ICTWSS_URL, suffix=".csv")
    raw_csv = ictwss_path.read_text(encoding="utf-8-sig")

    reader = csv.DictReader(StringIO(raw_csv))
    records: list[dict] = []
    for row in reader:
        iso3 = row.get("iso3", "").strip().upper()
        if iso3 not in _EU27_ISO3:
            continue
        val = row.get("ED", "").strip()
        year = row.get("year", "").strip()
        if not val or not year:
            continue
        records.append({
            "geo": _ISO3_TO_ISO2[iso3],
            "time": int(year),
            "value": float(val),
        })

    df = pd.DataFrame(records)
    df = df[df["time"] >= start_period]

    return Dataset(
        df,
        name="Hustota zaměstnavatelských organizací",
        unit="%",
        source_url="OECD/AIAS ICTWSS v2 (ED)",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. IPP negotiated wage increase (MPSV odmenovani, sheet A15a)
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_ipp_negotiated_increase(path: Path, year: int) -> Optional[float]:
    """Extract avg negotiated wage increase (%) from one IPP odmenovani file.

    Reads sheet A15a and dynamically locates the ``prům.%`` column and
    "Celkem" aggregate row.  Returns None on failure.
    """
    try:
        df = pd.read_excel(path, sheet_name="A15a", header=None)
    except Exception as exc:
        log.warning("IPP %d: cannot read A15a from %s: %s", year, path.name, exc)
        return None

    # Find 'prům.%' column
    prumpc_col: int | None = None
    for row_idx in range(min(15, df.shape[0])):
        for col_idx in range(df.shape[1]):
            if str(df.iloc[row_idx, col_idx]).strip() == "prům.%":
                prumpc_col = col_idx
                break
        if prumpc_col is not None:
            break
    if prumpc_col is None:
        log.warning("IPP %d: 'prům.%%' column not found", year)
        return None

    # Find 'Celkem' row (check col 0 and 1 for pre-2009 shift)
    celkem_row: int | None = None
    for row_idx in range(df.shape[0]):
        for label_col in range(min(2, df.shape[1])):
            if str(df.iloc[row_idx, label_col]).strip().lower() == "celkem":
                celkem_row = row_idx
                break
        if celkem_row is not None:
            break
    if celkem_row is None:
        log.warning("IPP %d: 'Celkem' row not found", year)
        return None

    val = pd.to_numeric(df.iloc[celkem_row, prumpc_col], errors="coerce")
    if pd.notna(val) and 0 < val < 50:
        return float(val)

    log.warning("IPP %d: could not extract negotiated increase", year)
    return None


def extract_ipp_negotiated(
    start_year: int = 2007,
    end_year: int = 2025,
) -> dict[int, float]:
    """Download IPP odmenovani workbooks and extract negotiated wage increases.

    Returns {year: increase_pct} for successfully parsed years.
    """
    result: dict[int, float] = {}
    for yr in range(start_year, end_year + 1):
        try:
            path = fetch_ipp(yr, "odmenovani")
            val = _extract_ipp_negotiated_increase(path, yr)
            if val is not None:
                result[yr] = val
        except Exception as exc:
            log.info("IPP %d: skipped (%s)", yr, exc)
    return result
