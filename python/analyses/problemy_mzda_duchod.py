r"""
Smoothed distribution functions of Czech wages and pensions.

Data source: MPSV ISPV (Mzdová sféra), ČSSZ (Statistická ročenka důchodového pojištění)
Filter: log-normální proložení mzdové distribuce a rozdělení starobních důchodů v ČR (2024--2025)

Two smoothed probability-density curves are fitted and displayed on a single
combined figure:

  **Wages** -- ISPV / RSCP semi-annual Excel workbooks published by
  MPSV / TREXIMA (``https://www.ispv.cz``).  The national-aggregate
  percentile profile (P10, P25, P50, P75, P90) extracted from the first
  sheet is used to fit a two-parameter log-normal distribution via
  least-squares regression on the log-quantile / probit scale.

  **Pensions** -- CSSZ (*Česká správa sociálního zabezpečení*) publishes
  annual statistics on old-age pensions structured by monthly-amount
    bracket.  The script downloads the CSSZ yearbook ZIP and derives
    quantiles directly from the grouped pension-distribution table.

Distribution fitting
--------------------
For a log-normal distribution ``X ~ LN(μ, σ)`` the p-th quantile
satisfies::

    log(Q_p) = μ + σ · Φ⁻¹(p)

where Φ⁻¹ is the standard-normal quantile function (probit).  Given five
quantile constraints (P10 -- P90) this reduces to an ordinary least-squares
problem in (μ, σ), solved with :func:`numpy.linalg.lstsq`.  The
probability-density function is then evaluated on a dense grid and plotted
as a smooth curve.

Output
------
  pics/python/problemy_mzda_duchod.pdf
  latex/texparts/python/problemy_mzda_duchod.tex

Run
---
    python analyses/problemy_mzda_duchod.py
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from config import LATEX_PICS_DIR, PALETTE, FIGURE_TEXT_SIZE, FIGURE_LABEL_SIZE, FIGURE_COMPACT_LABEL_SIZE, FIGURE_HEIGHT_STANDARD_CM
from stattool.fetch import fetch, fetch_ispv
from stattool.data_quality import warn_non_target_year
from stattool.style import (
    _apply_figure_layout,
    _add_vertical_ref,
    _fmt_czk,
    apply_style_pgf,
    cm2in,
    save_figure_tex_pgf,
    savefig_pgf,
)

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

apply_style_pgf()

# ── Parameters ────────────────────────────────────────────────────────────────

# Most recent ISPV year to try (going backwards)
_ISPV_END_YEAR = 2025

# Standard-normal quantile values for P10, P25, P50, P75, P90
# (Φ⁻¹ at the five standard percentile levels -- exact to 6 d.p.)
_PROBS  = np.array([0.10, 0.25, 0.50, 0.75, 0.90])
_ZSCORES = np.array([-1.281552, -0.674490, 0.000000, 0.674490, 1.281552])

# N_WAGE and N_PENSION are extracted from source files at runtime
# (ISPV MZS/PLS M0 row "počet zaměstnanců" and CSSZ bracket totals respectively).
# The fallback values below are used only when parsing fails.
_N_WAGE_PRIVATE_FALLBACK = 3_500_000  # approx. MZS 2025 -- replace if source changes
_N_WAGE_PUBLIC_FALLBACK  =   700_000  # approx. PLS 2025 -- replace if source changes
_N_PENSION_FALLBACK      = 2_367_000  # approx. CSSZ 2024 -- replace if source changes

# X-axis evaluation grid -- net-income scale (Kč/měsíc)
# Gross 120 000 Kč/měsíc → net ≈ 88 500 Kč; use 5--70 tis. to cover both series.
_X_MIN   =  0
_X_MAX   = 70_000
_X_GRID  = np.linspace(_X_MIN, _X_MAX, 100)

# Reference constants (2025)
MIN_WAGE       = 20_800   # Kč/měsíc hrubá (nařízení vlády č.289/2024 Sb.)
# Minimum pension = zákonná základní výměra + minimum procentní výměra
# zákon č.155/1995 Sb. §29; 2025 values per NV č.364/2024 Sb.
MIN_PENSION    =  5_170   # Kč/měsíc  (4 400 + 770 Kč)  zákon č.155/1995 Sb.
POVERTY_THRESHOLD = 18_600  # Kč/měsíc, hranice příjmové chudoby (ČSÚ, 2025)

# 2025 CZ employee statutory deductions (for gross-to-net conversion)
# Import from cz_tax_model to keep rates consistent across all analyses
from cz_tax_model import EMPLOYEE_SOCIAL_RATE as _SP_EMPLOYEE_RATE  # 7,1 % (důch. 6,5 % + nemoc. 0,6 %)
from cz_tax_model import EMPLOYER_INS_RATE  # 33,8 % SP + ZP zaměstnavatele
_ZP_EMPLOYEE_RATE   = 0.045        # zdravotní pojistění zaměstnanec
_DPFO_RATE_LOW      = 0.15         # sazba DPFO -- 1. pásmo (do 1 676 052 Kč/rok)
_DPFO_RATE_HIGH     = 0.23         # sazba DPFO -- 2. pásmo (nad 1 676 052 Kč/rok)
_DPFO_THRESHOLD_YR  = 1_676_052    # Kč/rok (§ 16 ZDP, platné pro rok 2025)
_DPFO_THRESHOLD_MO  = _DPFO_THRESHOLD_YR / 12  # ≈ 139 671 Kč/měsíc
_SLEVA_POPLATNIK    = 2_570        # Kč/měsíc (sleva na poplatníka = 30 840 Kč/rok)

# Colour assignments
_COLOR_WAGE    = PALETTE[0]   # deep blue
_COLOR_WAGE_PUBLIC = "#5B8DB8"  # blue (public/salary sphere)
_COLOR_PENSION = PALETTE[4]   # vermillion

# ── PGF string substitutions ──────────────────────────────────────────────────
STRINGS = {
    "title": r"Distribuce čistých mezd/platů a starobních důchodů, \acs{geo-CZ}",
    "xlabel": r"čistá mzda / výše důchodu [tis.~Kč/měsíc]",
    "ylabel": r"počet osob v~intervalu \SI{1}{tis.~Kč} [tis.~osob]",
}

# ── CSSZ pension data URLs ────────────────────────────────────────────────────
# CSSZ publishes the annual statistical yearbook as a ZIP archive containing
# multiple Excel tables.  URL pattern (discovered 2026-04-14):
#   https://www.cssz.cz/documents/20143/2946719/Ročenka+{year}.zip/{guid}
# The pension-distribution table is one of the Excel files inside (.xls/.xlsx).
_CSSZ_URLS: list[tuple[int, str]] = [
    # (year, ZIP URL) -- add newer editions here when available
    (2024, "https://www.cssz.cz/documents/20143/2946719/"
           "Ro%C4%8Denka+2024.zip/616fb679-ad56-768a-6276-eddb0b99273a"),
    (2023, "https://www.cssz.cz/documents/20143/2946719/"
           "Ro%C4%8Denka+2023.zip/736e528f-2bf9-9f4f-8bde-8ecad9d6bfe2"),
    (2022, "https://www.cssz.cz/documents/20143/2946719/"
           "Ro%C4%8Denka+2022.zip/ee569157-cf9d-c4ca-068a-1b3ac24d4c65"),
]

# Current ISPV national workbook (GUID-based URL; old /files pattern is stale).
_ISPV_NAT_URLS: list[tuple[int, str]] = [
    (2025, "https://www.ispv.cz/getattachment/b568f503-6978-4af7-9f8a-d5aef8e46619"
           "/CR_254_MZS-xlsx.aspx?disposition=attachment"),
]

_ISPV_NAT_PUBLIC_URLS: list[tuple[int, str]] = [
    (2025, "https://www.ispv.cz/getattachment/64ad14f0-4b5b-4192-a2e2-3acceedff267"
           "/CR_254_PLS-xlsx.aspx?disposition=attachment"),
]


# ════════════════════════════════════════════════════════════════════════════
# Math helpers (no scipy required)
# ════════════════════════════════════════════════════════════════════════════

def _erf_approx(x: np.ndarray) -> np.ndarray:
    """Vectorised erf approximation (Abramowitz & Stegun 7.1.26).

    Maximum absolute error ≤ 1.5 × 10⁻⁷.
    """
    sign = np.sign(x)
    t = 1.0 / (1.0 + 0.3275911 * np.abs(x))
    poly = t * (
        0.254829592
        + t * (-0.284496736
               + t * (1.421413741
                      + t * (-1.453152027
                             + t * 1.061405429)))
    )
    result = 1.0 - poly * np.exp(-(x ** 2))
    return sign * result


def lognormal_pdf(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Log-normal probability-density function."""
    x_pos = np.maximum(x, 1e-12)
    return (
        np.exp(-0.5 * ((np.log(x_pos) - mu) / sigma) ** 2)
        / (x_pos * sigma * np.sqrt(2.0 * np.pi))
    )


def lognormal_cdf(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Log-normal cumulative distribution function."""
    x_pos = np.maximum(x, 1e-12)
    z = (np.log(x_pos) - mu) / (sigma * np.sqrt(2.0))
    return 0.5 * (1.0 + _erf_approx(z))


def truncated_lognormal_pdf(
    x: np.ndarray, mu: float, sigma: float, x_min: float
) -> np.ndarray:
    """Left-truncated log-normal PDF with hard lower bound at *x_min*.

    For a random variable X with X ∼ LN(μ, σ) conditioned on X ≥ x_min::

        f(x | x ≥ x_min) = f_LN(x) / (1 − F_LN(x_min))   for x ≥ x_min
        f(x | x ≥ x_min) = 0                                for x < x_min

    This properly models the fact that no wage/pension can fall below its
    legal minimum floor.
    """
    cdf_at_min = float(lognormal_cdf(np.array([x_min]), mu, sigma)[0])
    normalizer = max(1.0 - cdf_at_min, 1e-15)
    pdf = lognormal_pdf(x, mu, sigma)
    return np.where(np.asarray(x) >= x_min, pdf / normalizer, 0.0)


def fit_lognormal(quantile_dict: dict[float, float]) -> tuple[float, float]:
    """Fit log-normal (μ, σ) from a dict of {probability: quantile_value}.

    Uses ordinary least squares on the linear model::

        log(Q_p) = μ + σ · Φ⁻¹(p)

    At least two quantile observations are required.

    Returns
    -------
    mu, sigma : float
        Parameters of the fitted log-normal distribution.
    """
    probs = np.array(sorted(quantile_dict.keys()))
    qvals = np.array([quantile_dict[p] for p in probs])

    # Standard-normal quantiles at the given probabilities
    # Interpolate from the pre-computed _ZSCORES if within range,
    # or use a rational approximation otherwise.
    z = np.interp(probs, _PROBS, _ZSCORES)

    log_q = np.log(qvals)
    A = np.column_stack([np.ones_like(z), z])
    params, *_ = np.linalg.lstsq(A, log_q, rcond=None)
    mu, sigma = float(params[0]), float(params[1])

    # Ensure positive sigma (numerical safety)
    sigma = max(sigma, 1e-6)
    return mu, sigma


def gross_to_net_wage(gross: float | np.ndarray) -> float | np.ndarray:
    """Čistá měsíční mzda po odečtení zaměstnaneckých odvodů a DPFO.

    CZ 2025: SP = 7,1 % (důch. 6,5 % + nemoc. 0,6 %), ZP = 4,5 %,
    DPFO 15 % do 139 671 Kč/měsíc (= 1 676 052 Kč/rok), 23 % nad
    tuto hranici; sleva na poplatníka = 2 570 Kč/měsíc.

    Základ daně DPFO je hrubá mzda (od 1. 1. 2021 bylo zrušeno
    zdanění ze „superhrubé mzdy"; zákon č. 586/1992 Sb., §6 odst. 12).
    """
    g = np.asarray(gross, dtype=float)
    sp = _SP_EMPLOYEE_RATE * g
    zp = _ZP_EMPLOYEE_RATE * g
    # Two-bracket DPFO (§ 16 ZDP):
    #   15 % up to _DPFO_THRESHOLD_MO, 23 % on the excess
    dpfo_before_sleva = (
        np.minimum(g, _DPFO_THRESHOLD_MO) * _DPFO_RATE_LOW
        + np.maximum(g - _DPFO_THRESHOLD_MO, 0.0) * _DPFO_RATE_HIGH
    )
    dpfo = np.maximum(dpfo_before_sleva - _SLEVA_POPLATNIK, 0.0)
    return g - sp - zp - dpfo


# ════════════════════════════════════════════════════════════════════════════
# Data fetching helpers
# ════════════════════════════════════════════════════════════════════════════

def _fetch_ispv_national_quantiles() -> tuple[dict[float, float], int, int] | tuple[None, None, None]:
    """Try to download ISPV and parse national-aggregate percentile columns.

    Returns
    -------
    (quantile_dict, year, n_employees) or (None, None, None) on failure.
    The dict maps probability → wage in Kč/měsíc.
    n_employees is the total worker count from the MZS-M0 sheet.
    """
    kw_percentile = {
        "p10": 0.10,
        "p25": 0.25,
        "p50": 0.50,
        "p75": 0.75,
        "p90": 0.90,
        "medián": 0.50,
        "median": 0.50,
        "1. decil": 0.10,
        "1. kvartil": 0.25,
        "3. kvartil": 0.75,
        "9. decil": 0.90,
    }
    national_kw = ["celkem", "česká republika", "čr celkem", "total", "cr"]

    # Prefer current GUID-based national workbook.
    for yr, url in _ISPV_NAT_URLS:
        try:
            path = fetch(url, suffix=".xlsx")
            with open(path, "rb") as fh:
                if fh.read(2) != b"PK":
                    print(f"  ISPV {yr} GUID: downloaded file is not XLSX")
                    continue

            df = pd.read_excel(path, sheet_name="MZS-M0", header=None)
            found: dict[float, float] = {}
            row_markers = {
                0.10: "1. decil",
                0.25: "1. kvartil",
                0.50: "medián",
                0.75: "3. kvartil",
                0.90: "9. decil",
            }
            for prob, marker in row_markers.items():
                mask = df.apply(
                    lambda r: r.astype(str).str.lower().str.contains(marker, na=False).any(),
                    axis=1,
                )
                if not mask.any():
                    continue
                row = df.loc[mask].iloc[0]
                nums = pd.to_numeric(row, errors="coerce").dropna()
                nums = nums[(nums > 5_000) & (nums < 500_000)]
                if not nums.empty:
                    found[prob] = float(nums.iloc[-1])

            if len(found) >= 5:
                # Also extract employee count ("počet zaměstnanců") from MZS-M0.
                n_emp = _N_WAGE_PRIVATE_FALLBACK
                for _, row_e in df.iterrows():
                    row_str = row_e.astype(str).str.lower()
                    if row_str.str.contains(r"počet.{0,10}zaměst", regex=True).any():
                        nums_e = pd.to_numeric(row_e, errors="coerce").dropna()
                        # Employee counts are in thousands in some sheets, but
                        # in full integers (> 100 000) in the GUID workbook.
                        valid_e = nums_e[(nums_e > 100_000) & (nums_e < 10_000_000)]
                        if not valid_e.empty:
                            n_emp = int(valid_e.iloc[-1])
                            break
                        valid_e_tis = nums_e[(nums_e > 100) & (nums_e < 10_000)]
                        if not valid_e_tis.empty:
                            n_emp = int(valid_e_tis.iloc[-1]) * 1_000
                            break
                print(
                    f"  ISPV {yr} GUID: national quantiles parsed "
                    f"({len(found)} percentiles), N={n_emp:,}"
                )
                return found, yr, n_emp
            print(f"  ISPV {yr} GUID: quantile rows not found")
        except Exception as exc:
            print(f"  ISPV {yr} GUID fetch failed: {exc}")

    # Secondary attempt: legacy endpoints.
    for yr in range(_ISPV_END_YEAR, _ISPV_END_YEAR - 5, -1):
        halves = [1, 2] if yr == _ISPV_END_YEAR else [2, 1]
        for half in halves:
            try:
                path = fetch_ispv(yr, half=half, sphere="podnikatelska")
            except Exception as exc:
                print(f"  ISPV {yr}/H{half} fetch failed: {exc}")
                continue

            for skiprows in range(0, 8):
                try:
                    df = pd.read_excel(path, sheet_name=0, skiprows=skiprows, header=0)
                    df = df.dropna(how="all").reset_index(drop=True)
                    if df.shape[1] < 3 or df.shape[0] < 3:
                        continue

                    first_col = df.columns[0]
                    df_str = df[first_col].astype(str).str.lower().str.strip()
                    nat_mask = df_str.apply(lambda s: any(kw in s for kw in national_kw))
                    if not nat_mask.any():
                        continue

                    row = df.loc[nat_mask].iloc[0]
                    found: dict[float, float] = {}
                    for col in df.columns[1:]:
                        col_lc = str(col).lower().strip()
                        for kw, prob in kw_percentile.items():
                            if kw in col_lc:
                                val = pd.to_numeric(row[col], errors="coerce")
                                if pd.notna(val) and 5_000 < val < 500_000:
                                    found.setdefault(prob, float(val))
                                break

                    if len(found) >= 3:
                        print(
                            f"  ISPV {yr}/H{half}: national quantiles parsed "
                            f"({len(found)} percentiles)"
                        )
                        return found, yr, _N_WAGE_PRIVATE_FALLBACK
                except Exception as exc:
                    log.debug("ISPV parse skiprows=%d: %s", skiprows, exc)

            print(f"  ISPV {yr}/H{half}: no national aggregate row found")

    return None, None, None


def _fetch_ispv_public_quantiles() -> tuple[dict[float, float], int, int] | tuple[None, None, None]:
    """Try to download PLS and parse national-aggregate percentile columns.

    Returns
    -------
    (quantile_dict, year, n_employees) or (None, None, None) on failure.
    The dict maps probability → wage in Kč/měsíc.
    n_employees is the total worker count from the PLS-M0 sheet.
    """
    row_markers = {
        0.10: "1. decil",
        0.25: "1. kvartil",
        0.50: "medián",
        0.75: "3. kvartil",
        0.90: "9. decil",
    }

    for yr, url in _ISPV_NAT_PUBLIC_URLS:
        try:
            path = fetch(url, suffix=".xlsx")
            with open(path, "rb") as fh:
                if fh.read(2) != b"PK":
                    print(f"  PLS {yr} GUID: downloaded file is not XLSX")
                    continue

            try:
                xl = pd.ExcelFile(path, engine="openpyxl")
                m0_sheets = [s for s in xl.sheet_names if s.endswith("-M0")]
                if m0_sheets:
                    sheet = next((s for s in m0_sheets if "PLS" in s.upper()), m0_sheets[0])
                else:
                    sheet = next((s for s in xl.sheet_names if "M0" in s.upper()), xl.sheet_names[0])
            except Exception:
                sheet = "PLS-M0"

            df = pd.read_excel(path, sheet_name=sheet, header=None)
            found: dict[float, float] = {}
            for prob, marker in row_markers.items():
                mask = df.apply(
                    lambda r: r.astype(str).str.lower().str.contains(marker, na=False).any(),
                    axis=1,
                )
                if not mask.any():
                    continue
                row = df.loc[mask].iloc[0]
                nums = pd.to_numeric(row, errors="coerce").dropna()
                nums = nums[(nums > 5_000) & (nums < 500_000)]
                if not nums.empty:
                    found[prob] = float(nums.iloc[-1])

            if len(found) >= 5:
                n_emp = _N_WAGE_PUBLIC_FALLBACK
                for _, row_e in df.iterrows():
                    row_str = row_e.astype(str).str.lower()
                    if row_str.str.contains(r"počet.{0,10}zaměst", regex=True).any():
                        nums_e = pd.to_numeric(row_e, errors="coerce").dropna()
                        valid_e = nums_e[(nums_e > 100_000) & (nums_e < 10_000_000)]
                        if not valid_e.empty:
                            n_emp = int(valid_e.iloc[-1])
                            break
                        valid_e_tis = nums_e[(nums_e > 100) & (nums_e < 10_000)]
                        if not valid_e_tis.empty:
                            n_emp = int(valid_e_tis.iloc[-1]) * 1_000
                            break

                print(
                    f"  PLS {yr} GUID: national quantiles parsed "
                    f"({len(found)} percentiles), N={n_emp:,}"
                )
                return found, yr, n_emp

            print(f"  PLS {yr} GUID: quantile rows not found")
        except Exception as exc:
            print(f"  PLS {yr} GUID fetch failed: {exc}")

    return None, None, None


def _fetch_cssz_pension_quantiles() -> tuple[dict[float, float], int, int] | tuple[None, None, None]:
    """Try to download CSSZ statistical tables and derive pension quantiles.

    CSSZ publishes grouped pension-amount data (count per bracket).  This
    function derives approximate percentile values from the cumulative
    distribution of those counts.  The total bracket count is returned as
    the pensioner headcount (N_PENSION).

    Returns (quantile_dict, year, n_pensioners) or (None, None, None) on failure.
    """
    import io
    import zipfile

    for year, url in _CSSZ_URLS:
        try:
            path = fetch(url, suffix=".zip")
        except Exception as exc:
            print(f"  CSSZ {year} fetch failed: {exc}")
            continue

        # Extract pension-distribution workbook from the yearbook ZIP.
        try:
            with zipfile.ZipFile(path) as zf:
                candidates = [
                    n for n in zf.namelist()
                    if ("07.03" in n or "výše důchodu" in n.lower())
                    and n.lower().endswith((".xls", ".xlsx"))
                ]
                if not candidates:
                    print(f"  CSSZ {year}: pension workbook not found in ZIP")
                    continue
                wb_name = candidates[0]
                wb_bytes = io.BytesIO(zf.read(wb_name))
        except (zipfile.BadZipFile, KeyError) as exc:
            print(f"  CSSZ {year} ZIP extraction failed: {exc}")
            continue

        try:
            xls = pd.ExcelFile(wb_bytes)
            sheet_name = "S-celkem"
            if sheet_name not in xls.sheet_names:
                cands = [s for s in xls.sheet_names if "celkem" in s.lower()]
                if not cands:
                    print(f"  CSSZ {year}: 'S-celkem' sheet not found")
                    continue
                sheet_name = cands[0]

            wb_bytes.seek(0)
            df = pd.read_excel(wb_bytes, sheet_name=sheet_name, header=None)

            header_row = None
            for i in range(min(30, len(df))):
                cell0 = str(df.iloc[i, 0]).strip().lower()
                if cell0 == "měsíční výše" or cell0.startswith("měsíční výše"):
                    header_row = i
                    break
            if header_row is None:
                print(f"  CSSZ {year}: monthly-amount header not found")
                continue

            header = df.iloc[header_row]
            count_col = None
            for j, val in enumerate(header):
                if "celkem" in str(val).lower():
                    count_col = j
                    break
            if count_col is None:
                print(f"  CSSZ {year}: count column 'CELKEM' not found")
                continue

            bins: list[tuple[float, float, float]] = []
            for i in range(header_row + 1, len(df)):
                label = str(df.iloc[i, 0]).strip()
                if not label or label.lower() == "nan":
                    continue
                lcl = label.lower()
                if "neudáno" in lcl:
                    continue
                if "úhrn" in lcl or "prům." in lcl:
                    break

                clean = label.replace("\xa0", " ").strip()
                if "–" in clean or "-" in clean:
                    sep = "–" if "–" in clean else "-"
                    left, right = clean.split(sep, 1)
                    left_num = re.sub(r"\D", "", left)
                    right_num = re.sub(r"\D", "", right)
                    if not left_num or not right_num:
                        continue
                    lo = float(int(left_num))
                    hi = float(int(right_num))
                    # CSSZ uses shorthand like "1–4 999" for 1 000–4 999.
                    if lo < 100 and hi >= 1_000:
                        lo *= 1_000.0
                else:
                    nums = re.sub(r"\D", "", clean)
                    if not nums:
                        continue
                    lo = float(int(nums))
                    hi = float(int(nums) + 1_000)
                if hi <= lo:
                    continue

                cnt = pd.to_numeric(df.iloc[i, count_col], errors="coerce")
                if pd.isna(cnt) or cnt <= 0:
                    continue
                bins.append((lo, hi, float(cnt)))

            if len(bins) < 5:
                print(f"  CSSZ {year}: insufficient valid bins in {sheet_name}")
                continue

            bounds = np.array([[b[0], b[1]] for b in bins], dtype=float)
            counts = np.array([b[2] for b in bins], dtype=float)
            cum = np.cumsum(counts)
            total = float(cum[-1])
            if total < 100:
                print(f"  CSSZ {year}: insufficient observations ({total:.0f})")
                continue

            q_dict: dict[float, float] = {}
            for prob in [0.10, 0.25, 0.50, 0.75, 0.90]:
                target = prob * total
                idx = int(np.searchsorted(cum, target, side="left"))
                idx = min(max(idx, 0), len(counts) - 1)
                lo, hi = bounds[idx]
                bin_cnt = max(counts[idx], 1e-9)
                prev = cum[idx - 1] if idx > 0 else 0.0
                frac = np.clip((target - prev) / bin_cnt, 0.0, 1.0)
                q_dict[prob] = float(lo + frac * (hi - lo))

            n_pension = int(round(total))
            print(
                f"  CSSZ {year}: pension quantiles derived from "
                f"'{wb_name}' / '{sheet_name}', N={n_pension:,}"
            )
            return q_dict, year, n_pension

        except Exception as exc:
            log.debug("CSSZ %s parse failed: %s", year, exc)
            print(f"  CSSZ {year}: parse failed ({type(exc).__name__})")

    return None, None, None


# ════════════════════════════════════════════════════════════════════════════
# Fetch data
# ════════════════════════════════════════════════════════════════════════════

print("Fetching ISPV wage quantile data (private MZS + public PLS) …")
wage_q_private, wage_private_year, N_WAGE_PRIVATE = _fetch_ispv_national_quantiles()
if wage_q_private is None:
    raise RuntimeError(
        "ISPV private-sector (MZS) wage quantiles could not be fetched from live sources."
    )
wage_q_public, wage_public_year, N_WAGE_PUBLIC = _fetch_ispv_public_quantiles()
if wage_q_public is None:
    raise RuntimeError(
        "ISPV public-sector (PLS) wage quantiles could not be fetched from live sources."
    )

if N_WAGE_PRIVATE is None:
    from stattool.data_quality import warn_fallback
    warn_fallback("N_WAGE_PRIVATE", "ISPV MZS-M0 počet zaměstnanců not found", fallback=_N_WAGE_PRIVATE_FALLBACK)
    N_WAGE_PRIVATE = _N_WAGE_PRIVATE_FALLBACK
if N_WAGE_PUBLIC is None:
    from stattool.data_quality import warn_fallback
    warn_fallback("N_WAGE_PUBLIC", "ISPV PLS-M0 počet zaměstnanců not found", fallback=_N_WAGE_PUBLIC_FALLBACK)
    N_WAGE_PUBLIC = _N_WAGE_PUBLIC_FALLBACK

print("Fetching CSSZ pension distribution data …")
pension_q, pension_year, N_PENSION = _fetch_cssz_pension_quantiles()
if pension_q is None:
    raise RuntimeError(
        "CSSZ pension quantiles could not be fetched from live sources."
    )
if N_PENSION is None:
    from stattool.data_quality import warn_fallback
    warn_fallback("N_PENSION", "CSSZ bracket total not found", fallback=_N_PENSION_FALLBACK)
    N_PENSION = _N_PENSION_FALLBACK

print(f"  Worker headcount (MZS):     N_WAGE_PRIVATE = {N_WAGE_PRIVATE:,}")
print(f"  Worker headcount (PLS):     N_WAGE_PUBLIC  = {N_WAGE_PUBLIC:,}")
print(f"  Worker headcount (MZS+PLS): N_WAGE_TOTAL   = {N_WAGE_PRIVATE + N_WAGE_PUBLIC:,}")
print(f"  Pensioner headcount (CSSZ): N_PENSION = {N_PENSION:,}")

warn_non_target_year(source="MPSV/TREXIMA ISPV MZS", year=wage_private_year, context="Private wage distribution input")
warn_non_target_year(source="MPSV/TREXIMA ISPV PLS", year=wage_public_year, context="Public wage distribution input")
warn_non_target_year(source="CSSZ", year=pension_year, context="Pension distribution input")

# ════════════════════════════════════════════════════════════════════════════
# Fit log-normal distributions
# ════════════════════════════════════════════════════════════════════════════

# Convert gross ISPV wage quantiles to net take-home wages
wage_q_net_private = {p: float(gross_to_net_wage(q)) for p, q in wage_q_private.items()}
wage_q_net_public = {p: float(gross_to_net_wage(q)) for p, q in wage_q_public.items()}

mu_w, sig_w = fit_lognormal(wage_q_net_private)
mu_w_public, sig_w_public = fit_lognormal(wage_q_net_public)
mu_p, sig_p = fit_lognormal(pension_q)

med_wage_gross      = float(wage_q_private.get(0.50, np.exp(mu_w)))
med_wage_net        = float(wage_q_net_private.get(0.50, np.exp(mu_w)))
med_wage_total_cost = med_wage_gross * (1.0 + EMPLOYER_INS_RATE)
med_wage_public_net = float(wage_q_net_public.get(0.50, np.exp(mu_w_public)))
med_pension         = float(pension_q.get(0.50, np.exp(mu_p)))

# Net minimum wage and equivalent total employer labour cost
min_wage_net        = float(gross_to_net_wage(MIN_WAGE))
min_wage_total_cost = MIN_WAGE * (1.0 + EMPLOYER_INS_RATE)

# Ensure the sampled x-grid contains the exact minimum-wage cutoff so the
# truncated wage density shows the vertical edge at the correct x-position.
x_grid = np.unique(np.concatenate([_X_GRID, np.array([min_wage_net])]))

print(f"\nWage    fit (net): μ={mu_w:.4f}, σ={sig_w:.4f}  "
      f"→ čistý medián≈{med_wage_net:,.0f} Kč  "
      f"(hrubá {med_wage_gross:,.0f} Kč, "
      f"náklady zaměstnavatele {med_wage_total_cost:,.0f} Kč)")
print(f"Public wage fit:   μ={mu_w_public:.4f}, σ={sig_w_public:.4f}  "
    f"→ čistý medián≈{med_wage_public_net:,.0f} Kč")
print(f"Pension fit:       μ={mu_p:.4f}, σ={sig_p:.4f}  "
      f"→ medián≈{med_pension:,.0f} Kč")

pdf_wage    = truncated_lognormal_pdf(x_grid, mu_w, sig_w, min_wage_net)
pdf_wage_public = truncated_lognormal_pdf(x_grid, mu_w_public, sig_w_public, min_wage_net)
pdf_pension = truncated_lognormal_pdf(x_grid, mu_p, sig_p, MIN_PENSION)

# Convert density [1/Kč] to headcount per 1,000 Kč bin in thousands:
#   persons_in_bin = pdf(x) × Δx × N  where Δx = 1 000 Kč
#   thousands      = pdf(x) × 1_000 × N / 1_000 = pdf(x) × N
_Y_SCALE_WAGE    = float(N_WAGE_PRIVATE)
_Y_SCALE_WAGE_PUBLIC = float(N_WAGE_PUBLIC)
_Y_SCALE_PENSION = float(N_PENSION)
freq_wage    = pdf_wage    * _Y_SCALE_WAGE               # tis. osob
freq_wage_public = pdf_wage_public * _Y_SCALE_WAGE_PUBLIC  # tis. osob
freq_wage_combined = freq_wage + freq_wage_public          # tis. osob
freq_pension = pdf_pension * _Y_SCALE_PENSION            # tis. osob

# ════════════════════════════════════════════════════════════════════════════
# Figure -- combined frequency plot
# ════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=cm2in(15, FIGURE_HEIGHT_STANDARD_CM))


def _tooltip(ax, x, y, text):
    ax.text(
        x, y,
        r"\pdftooltip{\phantom{\rule{6pt}{6pt}}}{" + text + r"}",
        fontsize=FIGURE_LABEL_SIZE,
        ha="center", va="center", clip_on=False, zorder=10,
    )


def _fmt_int_space(v: float) -> str:
    """Format integer-like value with spaces as thousands separators."""
    return f"{int(round(v)):,}".replace(",", " ")


# ── Curves ────────────────────────────────────────────────────────────────────
ax.fill_between(
    x_grid / 1_000, freq_wage,
    alpha=0.10, color=_COLOR_WAGE, zorder=2,
)
ax.plot(
    x_grid / 1_000, freq_wage,
    color=_COLOR_WAGE, linewidth=1.6, zorder=4,
)
ax.plot(
    x_grid / 1_000, freq_wage_public,
    color=_COLOR_WAGE_PUBLIC, linewidth=1.5, linestyle=(0, (4, 2)), zorder=5,
)
ax.plot(
    x_grid / 1_000, freq_wage_combined,
    color="#7A7A7A", linewidth=1.0, linestyle=(0, (3, 2)), zorder=3,
)

ax.fill_between(
    x_grid / 1_000, freq_pension,
    alpha=0.10, color=_COLOR_PENSION, zorder=2,
)
ax.plot(
    x_grid / 1_000, freq_pension,
    color=_COLOR_PENSION, linewidth=1.6, zorder=4,
)

# ── Tooltips: original quantile data points only (no interpolated anchors) ──
for p, q_gross in wage_q_private.items():
    q_net = wage_q_net_private[p]
    y_q = float(truncated_lognormal_pdf(np.array([q_net]), mu_w, sig_w, min_wage_net)[0]) * _Y_SCALE_WAGE
    _tooltip(
        ax, q_net / 1_000, y_q,
        f"Čistá mzda {wage_private_year} P{int(p * 100)}: {_fmt_int_space(q_net)} Kč",
    )

for p, q_gross in wage_q_public.items():
    q_net = wage_q_net_public[p]
    y_q = float(truncated_lognormal_pdf(np.array([q_net]), mu_w_public, sig_w_public, min_wage_net)[0]) * _Y_SCALE_WAGE_PUBLIC
    _tooltip(
        ax, q_net / 1_000, y_q,
        f"Čistý plat {wage_public_year} P{int(p * 100)}: {_fmt_int_space(q_net)} Kč",
    )

for p, q in pension_q.items():
    y_q = float(truncated_lognormal_pdf(np.array([q]), mu_p, sig_p, MIN_PENSION)[0]) * _Y_SCALE_PENSION
    _tooltip(
        ax, q / 1_000, y_q,
        f"Starobní důchody {pension_year} P{int(p * 100)}: {_fmt_int_space(q)} Kč",
    )

# ── Vertical reference lines (labels above axis, tax/pension-model style) ────
_add_vertical_ref(
    ax, min_wage_net / 1_000,
    f"min.~čistá~mzda\n{_fmt_czk(int(round(min_wage_net)))}",
    color=_COLOR_WAGE, alpha=0.55, linestyle=(0, (1, 3)),
)
_add_vertical_ref(
    ax, med_wage_net / 1_000,
    "",
    color=_COLOR_WAGE, alpha=0.8, linestyle=(0, (4, 3)),
)
_add_vertical_ref(
    ax, MIN_PENSION / 1_000,
    f"min.~důchod\n{_fmt_czk(MIN_PENSION)}",
    color=_COLOR_PENSION, alpha=0.55, linestyle=(0, (1, 3)),
)
_add_vertical_ref(
    ax, POVERTY_THRESHOLD / 1_000,
    "",
    color="#aa0000", alpha=0.65, linestyle=(0, (2, 2)),
)
ax.annotate(
    "chudoba",
    xy=(POVERTY_THRESHOLD / 1_000, 180),
    xytext=(-3, 0), textcoords="offset points",
    fontsize=FIGURE_COMPACT_LABEL_SIZE, color="#aa0000",
    ha="right", va="center", zorder=6,
)
_add_vertical_ref(
    ax, med_pension / 1_000,
    "",
    color=_COLOR_PENSION, alpha=0.8, linestyle=(0, (4, 3)),
)

# Median labels are intentionally shifted to fixed x-positions for readability.
_ann_w = ax.annotate(
    f"medián~čisté~mzdy\n{_fmt_czk(int(round(med_wage_net)))}",
    xy=(48.0, 1),
    xycoords=("data", "axes fraction"),
    xytext=(0, 0),
    textcoords="offset points",
    fontsize=FIGURE_COMPACT_LABEL_SIZE,
    color=_COLOR_WAGE,
    va="bottom",
    ha="center",
    multialignment="center",
)
_ann_w.set_clip_on(False)

_ann_p = ax.annotate(
    f"medián~důchodu\n{_fmt_czk(int(round(med_pension)))}",
    xy=(32.0, 1),
    xycoords=("data", "axes fraction"),
    xytext=(0, 0),
    textcoords="offset points",
    fontsize=FIGURE_COMPACT_LABEL_SIZE,
    color=_COLOR_PENSION,
    va="bottom",
    ha="center",
    multialignment="center",
)
_ann_p.set_clip_on(False)

# Keep all x-line labels at footnote size for consistent visual hierarchy.
for _txt in ax.texts:
    _content = _txt.get_text()
    if (
        _content.startswith("min.~čistá~mzda")
        or _content.startswith("min.~důchod")
        or _content.startswith("hranice~chudoby")
    ):
        _txt.set_fontsize(FIGURE_COMPACT_LABEL_SIZE)

# ── Inline curve labels (left-aligned, above the line) ───────────────────────
_pension_label_x = 27_000.0
_wage_label_x    = 40_000.0
_public_label_x  = 31_000.0
_combined_label_x = 40_000.0
y_pension_at = float(lognormal_pdf(
    np.array([_pension_label_x]), mu_p, sig_p)[0])
y_wage_at = float(lognormal_pdf(
    np.array([_wage_label_x]), mu_w, sig_w)[0])
y_public_at = float(lognormal_pdf(
    np.array([_public_label_x]), mu_w_public, sig_w_public)[0])
y_pension_at *= _Y_SCALE_PENSION
y_wage_at *= _Y_SCALE_WAGE
y_public_at *= _Y_SCALE_WAGE_PUBLIC
y_combined_at = y_wage_at + y_public_at
ax.annotate(
    "starobní důchody",
    xy=(_pension_label_x / 1_000, y_pension_at),
    xytext=(2, 4), textcoords="offset points",
    fontsize=FIGURE_LABEL_SIZE, color=_COLOR_PENSION,
    ha="left", va="bottom", zorder=5,
)
ax.annotate(
    "čistá mzda (podnikatelská sféra)",
    xy=(_wage_label_x / 1_000, y_wage_at),
    xytext=(2, 4), textcoords="offset points",
    fontsize=FIGURE_LABEL_SIZE, color=_COLOR_WAGE,
    ha="left", va="bottom", zorder=5,
)
ax.annotate(
    "čistý plat (veřejná sféra)",
    xy=(_public_label_x / 1_000, y_public_at),
    xytext=(2, 4), textcoords="offset points",
    fontsize=FIGURE_LABEL_SIZE, color=_COLOR_WAGE_PUBLIC,
    ha="left", va="bottom", zorder=5,
)
ax.annotate(
    "mzdy celkem",
    xy=(_combined_label_x / 1_000, y_combined_at),
    xytext=(10, 10), textcoords="offset points",
    fontsize=FIGURE_LABEL_SIZE, color="#666666",
    ha="left", va="bottom", zorder=5,
)

# ── Axis styling ──────────────────────────────────────────────────────────────
ax.set_xlabel(STRINGS["xlabel"], fontsize=FIGURE_LABEL_SIZE)
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:.0f}"))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:.0f}"))
ax.set_ylabel(STRINGS["ylabel"], fontsize=FIGURE_LABEL_SIZE)
ax.tick_params(axis="both", labelsize=FIGURE_LABEL_SIZE)
ax.set_xlim(_X_MIN / 1_000, _X_MAX / 1_000)
ax.set_ylim(bottom=0)
ax.set_title(STRINGS["title"], fontsize=FIGURE_TEXT_SIZE)
ax.minorticks_on()
_apply_figure_layout(ax)
fig._suptitle_gap_pt = 5
_spa = dict(getattr(fig, "_subplots_adjust_kwargs", {}))
_spa["left"] = 0.11
_spa["right"] = 0.95
fig._subplots_adjust_kwargs = _spa
fig.subplots_adjust(left=0.11, right=0.95)

savefig_pgf(fig, "problemy_mzda_duchod", strings=STRINGS)
save_figure_tex_pgf(
    "problemy_mzda_duchod",
    caption=f"Distribuce čistých mezd/platů ({wage_private_year}) a~starobních důchodů ({pension_year}), \\acs{{geo-CZ}}",
    cite_keys=["mpsv_ispv", "cssz_rocenka_duchod"],
    label="fig:problemy_mzda_duchod",
    resizebox_width=r"\linewidth",
    strings=STRINGS,
)

print("\nDone.")
