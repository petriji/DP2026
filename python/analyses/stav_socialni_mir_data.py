"""Shared B4 social-peace benchmark data for ternary and map analyses.

This module is the single source of truth for:
- strike-days benchmark values (days lost per 1,000 employees),
- expert-assessed social-peace scores used as ternary B4 input.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from statout.timeline import EU27
from stattool.data_quality import warn_fallback, warn_non_target_year
from stattool.fetch import fetch, fetch_eurostat, fetch_ilostat

# EU27 as sorted list for reproducible output
_EU27: list[str] = sorted(EU27)

# ILO ISO3 -> ISO2 mapping for EU27.
_ISO3_TO_ISO2: dict[str, str] = {
    "AUT": "AT",
    "BEL": "BE",
    "BGR": "BG",
    "HRV": "HR",
    "CYP": "CY",
    "CZE": "CZ",
    "DNK": "DK",
    "EST": "EE",
    "FIN": "FI",
    "FRA": "FR",
    "DEU": "DE",
    "GRC": "GR",
    "HUN": "HU",
    "IRL": "IE",
    "ITA": "IT",
    "LVA": "LV",
    "LTU": "LT",
    "LUX": "LU",
    "MLT": "MT",
    "NLD": "NL",
    "POL": "PL",
    "PRT": "PT",
    "ROU": "RO",
    "SVK": "SK",
    "SVN": "SI",
    "ESP": "ES",
    "SWE": "SE",
}

# Final expert B4 score (0/25/50/75/100), country-level.
B4_EXPERT_SCORE: dict[str, float] = {
    "BG": 100.0,
    "CZ": 100.0,
    "HU": 75.0,
    "LT": 100.0,
    "LU": 100.0,
    "LV": 100.0,
    "MT": 100.0,
    "RO": 100.0,
    "SE": 100.0,
    "SK": 100.0,
    "AT": 75.0,
    "HR": 75.0,
    "IE": 75.0,
    "PL": 75.0,
    "SI": 75.0,
    "DE": 50.0,
    "DK": 50.0,
    "EE": 50.0,
    "FI": 50.0,
    "IT": 50.0,
    "NL": 50.0,
    "PT": 50.0,
    "BE": 25.0,
    "CY": 25.0,
    "ES": 25.0,
    "FR": 25.0,
    "GR": 25.0,
}


def b4_from_strike_days(days_per_1000: float) -> float:
    """Map strike-days benchmark to categorical social-peace score."""
    if days_per_1000 < 1.0:
        return 100.0
    if days_per_1000 < 10.0:
        return 75.0
    if days_per_1000 < 50.0:
        return 50.0
    if days_per_1000 < 100.0:
        return 25.0
    return 0.0


def _load_ilostat_days(force: bool = False) -> pd.DataFrame:
    """Load ILOSTAT strike-days series (EU27, annual)."""
    path = fetch_ilostat(
        "STR_DAYS_ECO_RT_A",
        params={"classif1": "ECO_AGGREGATE_TOTAL", "sex": "SEX_T"},
        force=force,
    )
    df = pd.read_csv(path, low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]

    obs_col = "obs_value" if "obs_value" in df.columns else "value"
    if obs_col not in df.columns:
        raise ValueError(f"ILOSTAT strike dataset has no value column: {list(df.columns)}")
    if "ref_area" not in df.columns:
        raise ValueError(f"ILOSTAT strike dataset has no ref_area column: {list(df.columns)}")

    time_col = "time"
    if time_col not in df.columns:
        for alt in ("ref_period", "year"):
            if alt in df.columns:
                time_col = alt
                break

    df[obs_col] = pd.to_numeric(df[obs_col], errors="coerce")
    df["time"] = pd.to_numeric(df[time_col], errors="coerce")
    df = df.dropna(subset=[obs_col, "time"]).copy()

    df["ref_area"] = df["ref_area"].astype(str).str.strip().str.upper()
    df["geo"] = df["ref_area"].map(_ISO3_TO_ISO2)
    df = df.dropna(subset=["geo"])
    df["time"] = df["time"].astype(int)

    # Keep one annual value per country/year.
    out = (
        df[["geo", "time", obs_col]]
        .rename(columns={obs_col: "days_per_1000"})
        .groupby(["geo", "time"], as_index=False)["days_per_1000"]
        .mean()
    )
    return out[out["geo"].isin(_EU27)]


def _load_dk_days_from_dst(force: bool = False) -> pd.DataFrame:
    """Compute DK strike-days per 1,000 workers from Statistics Denmark ABST1."""
    path_dk_days = fetch(
        "https://api.statbank.dk/v1/data/ABST1/CSV"
        "?lang=en&ENHED=300&BRANCHE=000&Tid=*",
        suffix=".csv",
        force=force,
    )
    df_dk = pd.read_csv(path_dk_days, sep=";", low_memory=False)
    df_dk.columns = [c.strip().upper() for c in df_dk.columns]

    time_col = next((c for c in df_dk.columns if c in ("TID", "YEAR", "TIME")), None)
    value_col = next((c for c in df_dk.columns if c in ("INDHOLD", "VALUE", "OBS_VALUE")), None)
    if not time_col or not value_col:
        raise ValueError(f"Unexpected ABST1 columns: {list(df_dk.columns)}")

    df_dk = df_dk[[time_col, value_col]].copy()
    df_dk.columns = ["time", "lost_days"]
    df_dk["time"] = pd.to_numeric(df_dk["time"], errors="coerce")
    df_dk["lost_days"] = pd.to_numeric(
        df_dk["lost_days"].astype(str).str.replace("\xa0", "").str.replace(" ", "").str.replace(",", "."),
        errors="coerce",
    )
    df_dk = df_dk.dropna(subset=["time", "lost_days"]).astype({"time": int})

    path_emp = fetch_eurostat(
        "lfsi_emp_a",
        "A.EMP_LFS.T.Y20-64.THS_PER.DK",
        start_period=2000,
        force=force,
    )
    df_emp = pd.read_csv(path_emp)
    df_emp["OBS_VALUE"] = pd.to_numeric(df_emp["OBS_VALUE"], errors="coerce")
    df_emp["time"] = pd.to_numeric(df_emp["TIME_PERIOD"].astype(str).str[:4], errors="coerce")
    df_emp = df_emp.dropna(subset=["OBS_VALUE", "time"])
    df_emp = df_emp[["time", "OBS_VALUE"]].rename(columns={"OBS_VALUE": "emp_thousands"})
    df_emp["time"] = df_emp["time"].astype(int)

    merged = df_dk.merge(df_emp, on="time", how="inner")
    merged["days_per_1000"] = merged["lost_days"] / merged["emp_thousands"]
    merged["geo"] = "DK"
    return merged[["geo", "time", "days_per_1000"]]


def _snapshot_latest(df: pd.DataFrame) -> tuple[dict[str, float], int]:
    """Country snapshot using latest available observation per country."""
    vals: dict[str, float] = {}
    max_year = int(df["time"].max())
    for geo in _EU27:
        s = df[df["geo"] == geo].sort_values("time", ascending=False)
        if not s.empty:
            vals[geo] = float(s.iloc[0]["days_per_1000"])
    return vals, max_year


@lru_cache(maxsize=1)
def _cached_strike_snapshot() -> tuple[dict[str, float], int]:
    return _build_strike_snapshot(force=False)


def _build_strike_snapshot(force: bool = False) -> tuple[dict[str, float], int]:
    ilo = _load_ilostat_days(force=force)
    dk = _load_dk_days_from_dst(force=force)
    all_days = pd.concat([ilo, dk], ignore_index=True)
    snap, ref_year = _snapshot_latest(all_days)
    warn_non_target_year(
        source="ILOSTAT + Statistics Denmark strike benchmark",
        year=ref_year,
        context="B4 strike benchmark latest available year",
    )
    missing = [geo for geo in _EU27 if geo not in snap]
    if missing:
        warn_fallback(
            "Strike-days benchmark missing for some countries; ternary B4 remains covered by expert scores",
            source="ILOSTAT + Statistics Denmark strike benchmark",
            year=ref_year,
        )
        print(
            "WARNING: missing strike-days benchmark data for countries: "
            + ", ".join(missing)
            + ". They will remain unfilled in the strike choropleth; "
            + "B4 scoring remains covered by expert scores."
        )
    return snap, ref_year


def get_b4_strike_days_per_1000(force: bool = False) -> dict[str, float]:
    """Return strike-days benchmark values per country for B4 construction."""
    if force:
        return _build_strike_snapshot(force=True)[0]
    return _cached_strike_snapshot()[0]


def get_b4_benchmark_year(force: bool = False) -> int:
    """Return the selected benchmark reference year used for strike-days snapshot."""
    if force:
        return _build_strike_snapshot(force=True)[1]
    return _cached_strike_snapshot()[1]


def build_b4_scores() -> pd.Series:
    """Build EU27 B4 score series strictly from expert score table.

    Strike-days benchmark is used for map evidence, not for ternary scoring.
    """
    missing = [geo for geo in _EU27 if geo not in B4_EXPERT_SCORE]
    if missing:
        raise ValueError(
            "B4 expert score table incomplete for EU27; missing countries: "
            + ", ".join(missing)
        )
    warn_fallback(
        "B4 ternary scores use the expert score table rather than directly observed strike benchmark values",
        source="Expert assumption",
        year=get_b4_benchmark_year(),
        hardcoded=True,
    )
    vals: dict[str, float] = {geo: float(B4_EXPERT_SCORE[geo]) for geo in _EU27}
    return pd.Series(vals)
