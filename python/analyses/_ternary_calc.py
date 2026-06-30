"""Ternary model data pipeline — EU27 coordinate calculation from Eurostat data.

Each axis is a weighted composite of Eurostat indicators, normalised min-max
to [0, 100] across the EU27 panel.  The final A%, B%, C% coordinates are
obtained by normalising the three axis scores to sum to 100 (ternary closure).

Axis A — Household/Employee potential  (weights: 60 / 30 / 10)
    A1 (60 %)  median equivalised disposable household income in PPS
                         [ilc_di01, D5]
  A2 (30 %)  actual weekly hours worked                [lfsa_ewhan2]  INVERTED
  A3 (10 %)  gender pay gap (%)                       [earn_gr_gpgr2] INVERTED

Axis B — Employer/Capital potential   (weights: 40 / 30 / 20 / 10)
    B1 (40 %)  3-year average job vacancy rate (% of total posts) [jvs_a_r21]
    B2 (30 %)  combined statutory corporate income tax rate (%) [OECD CTS_CIT] INVERTED
    B3 (20 %)  total labour costs per hour (EUR÷PLI→PPS)  [lc_lci_lev D1_D4_MD5 + prc_ppp_ind] INVERTED
        B4 (10 %)  expert social-peace score (fixed score table)
                 [documented institutional benchmark]

Axis C — State/Government potential   (weights: 40 / 30 / 20 / 10)
  C1 (40 %)  cumulative real GDP change 2020 → 2024   [nama_10_gdp]
  C2 (30 %)  GDP per capita in PPS (EU27 = 100)       [nama_10_pc]
  C3 (20 %)  employment rate 20–64 (%)                [lfsi_emp_a]
  C4 (10 %)  Gini coefficient of income inequality    [ilc_di12]       INVERTED

Normalisation: min-max over EU27 for the latest year with ≥ 18 observations.
Missing countries: resolved by older-year fallback where possible; unresolved
gaps raise an explicit error (no silent imputation).

Variables are numbered continuously in descending weight order within each axis.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from stattool.dataset import _OECD_ISO3_TO_ISO2
from statout.timeline import EU27
from analyses.stav_socialni_mir_data import build_b4_scores
from stattool.fetch import fetch_eurostat, fetch_oecd

# ── EU27 as sorted list for reproducible output ───────────────────────────────
_EU27: list[str] = sorted(EU27)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _snapshot(
    df: pd.DataFrame,
    *,
    min_coverage: int = 18,
) -> pd.Series:
    """Return a Series {geo → value} for the latest well-covered year,
    applying last observation carried forward (LOCF) for countries with
    missing values in the target year.
    """
    df = df.copy()
    if "geo" in df.columns:
        df["geo"] = df["geo"].replace({"EL": "GR", "UK": "GB"})
    df["OBS_VALUE"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    df = df[df["geo"].isin(_EU27)].dropna(subset=["OBS_VALUE"])
    df["_yr"] = df["TIME_PERIOD"].astype(str).str[:4].astype(int)

    coverage = df.groupby("_yr")["geo"].nunique()
    valid = coverage[coverage >= min_coverage]
    if valid.empty:
        raise ValueError(
            f"No year with ≥ {min_coverage} EU27 observations "
            f"(max coverage: {coverage.max()} in {coverage.idxmax()})"
        )
    latest_year = int(valid.index.max())

    # LOCF fallback
    res = {}
    for geo in _EU27:
        geo_df = df[(df["geo"] == geo) & (df["_yr"] <= latest_year)].sort_values("_yr", ascending=False)
        if not geo_df.empty:
            res[geo] = float(geo_df.iloc[0]["OBS_VALUE"])
        else:
            res[geo] = np.nan

    snap = pd.Series(res)
    print(f"  → snapshot year {latest_year} with LOCF ({snap.notna().sum()} countries matched)")
    return snap


def _minmax(
    series: pd.Series,
    *,
    inverted: bool = False,
    clip_lo: float | None = None,
    clip_hi: float | None = None,
) -> pd.Series:
    """Min-max normalise to [0, 100] over EU27.
    Optionally clips values within [clip_lo, clip_hi] to avoid outlier distortions.
    """
    full = series.reindex(_EU27)
    missing = [geo for geo in _EU27 if pd.isna(full.loc[geo])]
    if missing:
        raise ValueError(
            "Missing values before normalisation; unresolved countries: "
            + ", ".join(missing)
        )
    
    if clip_lo is not None:
        full = full.clip(lower=clip_lo)
    if clip_hi is not None:
        full = full.clip(upper=clip_hi)

    lo, hi = float(full.min()), float(full.max())
    if hi == lo:
        return pd.Series(50.0, index=full.index)

    norm = (full - lo) / (hi - lo) * 100.0
    return (100.0 - norm) if inverted else norm


def _wscore(components: list[tuple[pd.Series, float]]) -> pd.Series:
    """Weighted sum of normalised component Series (weights should sum to 1.0)."""
    result = pd.Series(0.0, index=_EU27)
    for series, weight in components:
        aligned = series.reindex(_EU27)
        missing = [geo for geo in _EU27 if pd.isna(aligned.loc[geo])]
        if missing:
            raise ValueError(
                "Missing values in weighted component; unresolved countries: "
                + ", ".join(missing)
            )
        result = result + aligned * weight
    return result


def _b1_snapshot_country_priority(df: pd.DataFrame) -> pd.Series:
    """Build B1 snapshot with per-country dimension fallback and older-year carry.

    Priority order per country:
    - NACE: B-S_X_O -> TOTAL -> B-S -> B-O
    - UNIT: AVG_3Y -> AVG_A
    - SIZE: GE10 -> TOTAL
    Within the first available combination, use the latest available year.
    """
    d = df.copy()
    if "geo" in d.columns:
        d["geo"] = d["geo"].replace({"EL": "GR", "UK": "GB"})
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    d = d.dropna(subset=["value"])
    d = d[d["geo"].isin(_EU27)]
    if "freq" in d.columns:
        d = d[d["freq"].isin(["A", "ANNUAL"])]
    d["_yr"] = pd.to_numeric(d["time"].astype(str).str[:4], errors="coerce")
    d = d.dropna(subset=["_yr"]).copy()
    d["_yr"] = d["_yr"].astype(int)

    nace_col = "nace_r2" if "nace_r2" in d.columns else ("nace_r2_1" if "nace_r2_1" in d.columns else None)
    unit_col = "unit" if "unit" in d.columns else None
    size_col = "sizeclas" if "sizeclas" in d.columns else None

    nace_pref = ["B-S_X_O", "TOTAL", "B-S", "B-O"] if nace_col else [None]
    unit_pref = ["AVG_3Y", "AVG_A"] if unit_col else [None]
    size_pref = ["GE10", "TOTAL"] if size_col else [None]

    out: dict[str, float] = {}
    for geo in _EU27:
        g = d[d["geo"] == geo]
        found = False
        for nace in nace_pref:
            g_n = g if nace is None else g[g[nace_col] == nace]
            if g_n.empty:
                continue
            for unit in unit_pref:
                g_u = g_n if unit is None else g_n[g_n[unit_col] == unit]
                if g_u.empty:
                    continue
                for size in size_pref:
                    g_s = g_u if size is None else g_u[g_u[size_col] == size]
                    if g_s.empty:
                        continue
                    row = g_s.sort_values("_yr", ascending=False).iloc[0]
                    out[geo] = float(row["value"])
                    found = True
                    break
                if found:
                    break
            if found:
                break
        if not found:
            out[geo] = np.nan

    snap = pd.Series(out)
    print(f"  → B1 country-priority snapshot ({snap.notna().sum()} countries matched)")
    return snap


def _rolling_mean_snapshot(
    df: pd.DataFrame,
    *,
    window_years: int = 5,
    min_coverage: int = 18,
) -> pd.Series:
    """Return country values averaged over the latest rolling window.

    Steps:
    1) pick latest year with at least ``min_coverage`` EU27 observations,
    2) build a country-year panel for the last ``window_years``,
    3) fill per-country gaps by forward/backward carry within the window,
    4) average per country over the window.
    """
    d = df.copy()
    if "geo" in d.columns:
        d["geo"] = d["geo"].replace({"EL": "GR", "UK": "GB"})
    d["OBS_VALUE"] = pd.to_numeric(d["OBS_VALUE"], errors="coerce")
    d = d[d["geo"].isin(_EU27)].dropna(subset=["OBS_VALUE"])
    d["_yr"] = d["TIME_PERIOD"].astype(str).str[:4].astype(int)

    coverage = d.groupby("_yr")["geo"].nunique()
    valid = coverage[coverage >= min_coverage]
    if valid.empty:
        raise ValueError(
            f"No year with ≥ {min_coverage} EU27 observations "
            f"(max coverage: {coverage.max()} in {coverage.idxmax()})"
        )

    latest_year = int(valid.index.max())
    start_year = latest_year - (window_years - 1)
    years = list(range(start_year, latest_year + 1))

    panel = (
        d[d["_yr"].between(start_year, latest_year)]
        .groupby(["geo", "_yr"], as_index=False)["OBS_VALUE"]
        .mean()
        .pivot(index="geo", columns="_yr", values="OBS_VALUE")
        .reindex(index=_EU27, columns=years)
    )
    panel = panel.ffill(axis=1).bfill(axis=1)
    out = panel.mean(axis=1)
    print(
        f"  → rolling-{window_years} snapshot {start_year}→{latest_year} "
        f"({out.notna().sum()} countries)"
    )
    return out


# ── Axis A ────────────────────────────────────────────────────────────────────

def _axis_a(force: bool = False) -> pd.Series:
    """Axis A: Household/Employee potential — raw score in [0, 100]."""

    # A1 (60 %) — median equivalised disposable household income in PPS
    # ilc_di01 dimensions: FREQ · QUANTILE · INDIC_IL · CURRENCY · GEO
    print("  A1 (ilc_di01 D5)…")
    path_a1 = fetch_eurostat(
        "ilc_di01",
        "A.D5.TC.PPS.",
        start_period=2018,
        force=force,
    )
    df_a1 = pd.read_csv(path_a1)
    snap_a1 = _snapshot(df_a1)
    norm_a1 = _minmax(snap_a1, inverted=False)

    # A2 (30 %) — actual weekly hours worked, all employment, age 15–64 (INVERTED)
    print("  A2 (lfsa_ewhan2)…")
    path_a2 = fetch_eurostat(
        "lfsa_ewhan2",
        "A.TOTAL.EMP.TOTAL.Y15-64.T.HR.",
        start_period=2018,
        force=force,
    )
    df_a2 = pd.read_csv(path_a2)
    snap_a2 = _snapshot(df_a2)
    norm_a2 = _minmax(snap_a2, inverted=True)

    # A3 (10 %) — gender pay gap (%), business economy (INVERTED)
    print("  A3 (earn_gr_gpgr2)…")
    path_a3 = fetch_eurostat(
        "earn_gr_gpgr2",
        "A.PC.B-S_X_O.",
        start_period=2018,
        force=force,
    )
    df_a3 = pd.read_csv(path_a3)
    snap_a3 = _snapshot(df_a3, min_coverage=18)
    norm_a3 = _minmax(snap_a3, inverted=True)

    return _wscore([(norm_a1, 0.60), (norm_a2, 0.30), (norm_a3, 0.10)])


# ── Axis B ────────────────────────────────────────────────────────────────────

def _axis_b(force: bool = False) -> pd.Series:
    """Axis B: Employer/Capital potential — raw score in [0, 100]."""

    # B1 (40 %) — 3-year average job vacancy rate (annual %),
    # all enterprise sizes, non-sector aggregate (INVERTED)
    # Per-country dimension fallback with older-year carry:
    # NACE B-S_X_O → TOTAL → B-S → B-O; UNIT AVG_3Y → AVG_A; SIZE GE10 → TOTAL.
    # INVERTED because high vacancy rate = tight labour market = hiring difficulties for employers.
    print("  B1 (jvs_a_r21, country-priority fallback)…")
    path_b1 = fetch_eurostat("jvs_a_r21", force=force)
    df_b1 = pd.read_csv(path_b1, na_values=["", ":", ": "])
    if "TIME_PERIOD" in df_b1.columns:
        df_b1 = df_b1.rename(columns={"TIME_PERIOD": "time"})
    if "OBS_VALUE" in df_b1.columns:
        df_b1 = df_b1.rename(columns={"OBS_VALUE": "value"})
    snap_b1 = _b1_snapshot_country_priority(df_b1)
    norm_b1 = _minmax(snap_b1, inverted=True)

    # B2 (30 %) — OECD combined statutory corporate income tax rate (INVERTED)
    # CTS_CIT / COMB_CIT_RATE is a direct employer-facing tax burden indicator.
    print("  B2 (OECD CTS_CIT, COMB_CIT_RATE)…")
    path_b2 = fetch_oecd("CTS_CIT", start_period=2000, force=force)
    df_b2_all = pd.read_csv(path_b2)
    df_b2_raw = df_b2_all[df_b2_all["CORP_TAX"] == "COMB_CIT_RATE"].copy()
    if "UNIT_MEASURE" in df_b2_raw.columns:
        df_b2_raw = df_b2_raw[df_b2_raw["UNIT_MEASURE"] == "PC"]
    df_b2_raw["geo"] = df_b2_raw["COU"].map(
        lambda x: _OECD_ISO3_TO_ISO2.get(str(x).upper(), str(x))
    )
    df_b2_raw = df_b2_raw[df_b2_raw["geo"].isin(_EU27)].copy()
    snap_b2 = _snapshot(df_b2_raw)

    missing_b2 = [geo for geo in _EU27 if pd.isna(snap_b2.loc[geo])]
    if missing_b2:
        print("  → B2 same-source OECD fallback for missing countries (CIT_RATE / CIT_RATE_LESS_SUB_NAT)…")
        for alt_measure in ["CIT_RATE", "CIT_RATE_LESS_SUB_NAT"]:
            if alt_measure not in set(df_b2_all["CORP_TAX"].dropna().unique()):
                continue
            alt = df_b2_all[df_b2_all["CORP_TAX"] == alt_measure].copy()
            if "UNIT_MEASURE" in alt.columns:
                alt = alt[alt["UNIT_MEASURE"] == "PC"]
            alt["geo"] = alt["COU"].map(
                lambda x: _OECD_ISO3_TO_ISO2.get(str(x).upper(), str(x))
            )
            alt = alt[alt["geo"].isin(_EU27)].copy()
            snap_alt = _snapshot(alt)
            for geo in list(missing_b2):
                alt_val = snap_alt.get(geo, np.nan)
                if pd.notna(alt_val):
                    snap_b2.loc[geo] = float(alt_val)
                    print(f"    {geo}: substituted from OECD {alt_measure}")
            missing_b2 = [geo for geo in _EU27 if pd.isna(snap_b2.loc[geo])]
            if not missing_b2:
                break

    # Final expert fallback for Cyprus only (non-OECD member in CTS_CIT).
    # Model value for EATR-like burden: 14.1 % (derived from 15 % nominal CIT
    # and standard depreciation adjustment for low-tax systems).
    missing_b2 = [geo for geo in _EU27 if pd.isna(snap_b2.loc[geo])]
    if missing_b2 == ["CY"]:
        snap_b2.loc["CY"] = 14.1
        print("  → B2 expert fallback: CY set to 14.1 % (EATR model value for 2026)")

    unresolved_b2 = [geo for geo in _EU27 if pd.isna(snap_b2.loc[geo])]
    if unresolved_b2:
        raise ValueError(
            "B2 unresolved after OECD same-source + expert fallback: "
            + ", ".join(unresolved_b2)
        )

    norm_b2 = _minmax(snap_b2, inverted=True, clip_lo=1.0, clip_hi=5.0)

    # B3 (20 %) — total labour costs per hour (PPS-adjusted), business economy excl. O (INVERTED)
    # Component D1_D4_MD5 = gross wages (D11) + employer social contributions (D12)
    # + other labour costs (D4) − subsidies (MD5).
    # lc_lci_lev only publishes EUR levels; PPS conversion is done manually:
    #   PPS_cost = EUR_cost / (PLI_GDP / 100)
    # where PLI_GDP = GDP Price Level Index (EU27=100, 2020 base) from prc_ppp_ind.
    print("  B3 (lc_lci_lev D1_D4_MD5 EUR ÷ prc_ppp_ind PLI → PPS)…")
    path_b3_eur = fetch_eurostat(
        "lc_lci_lev",
        "A.EUR.D1_D4_MD5.B-S_X_O.",   # total costs — same definition as eu_odvetvove_mzdy.py
        start_period=2018,
        force=force,
    )
    df_b3_eur = pd.read_csv(path_b3_eur)
    snap_b3_eur = _snapshot(df_b3_eur)

    # Determine the LC reference year so PLI is fetched for the same year.
    _df_tmp = df_b3_eur.copy()
    if "geo" in _df_tmp.columns:
        _df_tmp["geo"] = _df_tmp["geo"].replace({"EL": "GR", "UK": "GB"})
    _df_tmp["OBS_VALUE"] = pd.to_numeric(_df_tmp["OBS_VALUE"], errors="coerce")
    _df_tmp = _df_tmp[_df_tmp["geo"].isin(_EU27)].dropna(subset=["OBS_VALUE"])
    _df_tmp["_yr"] = _df_tmp["TIME_PERIOD"].astype(str).str[:4].astype(int)
    _lc_cov = _df_tmp.groupby("_yr")["geo"].nunique()
    _lc_valid = _lc_cov[_lc_cov >= 18]
    _lc_ref_year = int(_lc_valid.index.max()) if not _lc_valid.empty else int(_lc_cov.idxmax())

    # PLI data lags by 1–2 years: fetch from 2 years before LC reference year
    # and use the latest available year (≤ LC reference year) for the conversion.
    path_pli = fetch_eurostat(
        "prc_ppp_ind",
        "A.PLI_EU27_2020.GDP.",
        start_period=_lc_ref_year - 2,
        force=force,
    )
    df_pli = pd.read_csv(path_pli)
    if "geo" in df_pli.columns:
        df_pli["geo"] = df_pli["geo"].replace({"EL": "GR", "UK": "GB"})
    df_pli["OBS_VALUE"] = pd.to_numeric(df_pli["OBS_VALUE"], errors="coerce")
    df_pli["_yr"] = df_pli["TIME_PERIOD"].astype(str).str[:4].astype(int)
    df_pli = df_pli[df_pli["_yr"] <= _lc_ref_year].dropna(subset=["OBS_VALUE"])
    _pli_ref_year = int(df_pli["_yr"].max())
    # Filter PLI to chosen year; EU27 aggregate = 100 by definition (not in dataset)
    _pli_yr = df_pli[df_pli["_yr"] == _pli_ref_year].set_index("geo")["OBS_VALUE"].copy()
    _pli_yr["EU27_2020"] = 100.0
    print(f"  B3 LC ref year: {_lc_ref_year}, PLI ref year: {_pli_ref_year}, PLI countries: {len(_pli_yr)}")

    # Align PLI to EUR index; unresolved missing PLI is treated as a hard error.
    pli_aligned = _pli_yr.reindex(snap_b3_eur.index)
    pli_missing = [geo for geo in snap_b3_eur.index if pd.isna(pli_aligned.loc[geo])]
    if pli_missing:
        raise ValueError(
            "Missing PLI values for B3 conversion; unresolved countries: "
            + ", ".join(pli_missing)
        )
    snap_b3_pps = snap_b3_eur / (pli_aligned / 100.0)
    norm_b3 = _minmax(snap_b3_pps, inverted=True)

    # B4 (10 %) — expert social-peace score
    norm_b4 = build_b4_scores()

    return _wscore(
        [(norm_b1, 0.40), (norm_b2, 0.30), (norm_b3, 0.20), (norm_b4, 0.10)]
    )


# ── Axis C ────────────────────────────────────────────────────────────────────

def _axis_c(force: bool = False) -> pd.Series:
    """Axis C: State/Government potential — raw score in [0, 100]."""

    # C1 (40 %) — cumulative real GDP change 2020 → 2024
    # Compound annual growth rates (CLV_PCH_PRE) for 2021–2024; each rate is
    # % change vs. the previous year, so chaining them from 2021 to 2024
    # gives total growth relative to 2020 as base year.
    # Window rationale: 2020 = COVID shock year (stress-test baseline);
    # 2021–2024 captures recovery, energy/war-in-Ukraine crisis, and ECB
    # tightening; 2025 preliminary estimates excluded (less reliable).
    print("  C1 (nama_10_gdp, cumulative real GDP Δ 2020→2024)…")
    path_c1 = fetch_eurostat(
        "nama_10_gdp",
        "A.CLV_PCH_PRE.B1GQ.",
        start_period=2019,
        force=force,
    )
    df_c1 = pd.read_csv(path_c1)
    if "geo" in df_c1.columns:
        df_c1["geo"] = df_c1["geo"].replace({"EL": "GR", "UK": "GB"})
    df_c1["OBS_VALUE"] = pd.to_numeric(df_c1["OBS_VALUE"], errors="coerce")
    df_c1 = df_c1[df_c1["geo"].isin(_EU27)].dropna(subset=["OBS_VALUE"])
    df_c1["_yr"] = df_c1["TIME_PERIOD"].astype(str).str[:4].astype(int)

    cumulative: dict[str, float] = {}
    for geo, grp in df_c1.groupby("geo"):
        # Compound growth rates for 2021–2024 (rates relative to 2020 base)
        window = grp[(grp["_yr"] >= 2021) & (grp["_yr"] <= 2024)].sort_values("_yr")
        if window.empty:
            continue
        cum = 1.0
        for _, row in window.iterrows():
            cum *= 1.0 + row["OBS_VALUE"] / 100.0
        cumulative[str(geo)] = (cum - 1.0) * 100.0  # % change from 2020
    snap_c1 = pd.Series(cumulative)
    print(f"  → C1 window 2020→2024 ({len(snap_c1)} countries)")
    norm_c1 = _minmax(snap_c1, inverted=False)

    # C2 (30 %) — GDP per capita in PPS (EU27 = 100, CLIPPED)
    # Clipped at 150 % of the EU average to prevent extreme artificial GDP distortions
    # from Luxembourg (238.7 %) and Ireland (237.3 %) from compressing the rest of the EU.
    print("  C2 (nama_10_pc)…")
    path_c2 = fetch_eurostat(
        "nama_10_pc",
        "A.PC_EU27_2020_HAB_MPPS_CP.B1GQ.",
        start_period=2018,
        force=force,
    )
    df_c2 = pd.read_csv(path_c2)
    snap_c2 = _snapshot(df_c2)
    norm_c2 = _minmax(snap_c2, inverted=False, clip_hi=150.0)

    # C3 (20 %) — employment rate 20–64 (%)
    print("  C3 (lfsi_emp_a)…")
    path_c3 = fetch_eurostat(
        "lfsi_emp_a",
        "A.EMP_LFS.T.Y20-64.PC_POP.",
        start_period=2018,
        force=force,
    )
    df_c3 = pd.read_csv(path_c3)
    snap_c3 = _snapshot(df_c3)
    norm_c3 = _minmax(snap_c3, inverted=False)

    # C4 (10 %) — Gini coefficient of equivalised disposable income (INVERTED)
    print("  C4 (ilc_di12)…")
    path_c4 = fetch_eurostat(
        "ilc_di12",
        "A.TOTAL.GINI_HND.",
        start_period=2018,
        force=force,
    )
    df_c4 = pd.read_csv(path_c4)
    snap_c4 = _snapshot(df_c4, min_coverage=18)
    norm_c4 = _minmax(snap_c4, inverted=True)

    return _wscore(
        [(norm_c1, 0.40), (norm_c2, 0.30), (norm_c3, 0.20), (norm_c4, 0.10)]
    )


# ── Public API ────────────────────────────────────────────────────────────────

def calculate_eu27_axis_scores(force: bool = False) -> pd.DataFrame:
    """Calculate raw A/B/C axis scores for all EU27 countries.

    Returns a DataFrame indexed by ISO-2 code with columns:
    ``A_raw``, ``B_raw``, ``C_raw``, ``sum_raw``, ``mean_raw``.
    """
    print("── Axis A (households / employees) ──────────────────────────────")
    a_raw = _axis_a(force=force)
    print("── Axis B (employers / capital) ─────────────────────────────────")
    b_raw = _axis_b(force=force)
    print("── Axis C (state / government) ──────────────────────────────────")
    c_raw = _axis_c(force=force)

    scores = pd.DataFrame({"A_raw": a_raw, "B_raw": b_raw, "C_raw": c_raw})
    scores = scores.reindex(_EU27)
    scores["sum_raw"] = scores["A_raw"] + scores["B_raw"] + scores["C_raw"]
    scores["mean_raw"] = scores[["A_raw", "B_raw", "C_raw"]].mean(axis=1)
    return scores


def calculate_eu27_coordinates(
    force: bool = False,
) -> dict[str, tuple[int, int, int]]:
    """Calculate ternary coordinates for all 27 EU member states.

    Returns a dict mapping ISO-2 country code → (A%, B%, C%) where the three
    integers sum to 100, suitable for direct use in ``ternary_diagram()``.

    Parameters
    ----------
    force:
        Pass ``True`` to force re-download of all cached Eurostat data.
    """
    scores = calculate_eu27_axis_scores(force=force)
    a_raw = scores["A_raw"]
    b_raw = scores["B_raw"]
    c_raw = scores["C_raw"]

    coords: dict[str, tuple[int, int, int]] = {}
    for geo in _EU27:
        a = float(a_raw.get(geo, np.nan))
        b = float(b_raw.get(geo, np.nan))
        c = float(c_raw.get(geo, np.nan))
        if np.isnan(a) or np.isnan(b) or np.isnan(c):
            raise ValueError(
                f"NaN axis value for {geo}: A={a}, B={b}, C={c}. "
                "Resolve missing inputs instead of using fallback shares."
            )
        total = a + b + c
        if total == 0:
            raise ValueError(f"Zero total axis score for {geo}; cannot normalise ternary coordinates.")
        a_pct = int(round(a / total * 100))
        b_pct = int(round(b / total * 100))
        c_pct = 100 - a_pct - b_pct  # ensure exact closure to 100
        coords[geo] = (a_pct, b_pct, c_pct)

    return coords


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute EU27 ternary social-dialog coordinates from Eurostat."
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-download all cached Eurostat data.",
    )
    args = parser.parse_args()

    result = calculate_eu27_coordinates(force=args.force)

    print("\n── EU27 ternary coordinates ─────────────────────────────────────")
    print(f"{'GEO':>3}  {'A':>4}  {'B':>4}  {'C':>4}  sum")
    for geo, (a, b, c) in sorted(result.items()):
        print(f"{geo:>3}  {a:>4}  {b:>4}  {c:>4}  {a + b + c}")
