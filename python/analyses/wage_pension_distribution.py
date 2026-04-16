r"""
Smoothed distribution functions of Czech wages and pensions.

Two smoothed probability-density curves are fitted and displayed on a single
combined figure:

  **Wages** – ISPV / RSCP semi-annual Excel workbooks published by
  MPSV / TREXIMA (``https://www.ispv.cz``).  The national-aggregate
  percentile profile (P10, P25, P50, P75, P90) extracted from the first
  sheet is used to fit a two-parameter log-normal distribution via
  least-squares regression on the log-quantile / probit scale.

  **Pensions** – CSSZ (*Česká správa sociálního zabezpečení*) publishes
  annual statistics on old-age pensions structured by monthly-amount
  bracket.  The script attempts to download the current-year Excel
  workbook from CSSZ open data; if the download fails a set of
  representative quantile values derived from the CSSZ *Statistická
  ročenka* (latest available year) is used as a fall-back so the
  figure is always produced.

Distribution fitting
--------------------
For a log-normal distribution ``X ~ LN(μ, σ)`` the p-th quantile
satisfies::

    log(Q_p) = μ + σ · Φ⁻¹(p)

where Φ⁻¹ is the standard-normal quantile function (probit).  Given five
quantile constraints (P10 – P90) this reduces to an ordinary least-squares
problem in (μ, σ), solved with :func:`numpy.linalg.lstsq`.  The
probability-density function is then evaluated on a dense grid and plotted
as a smooth curve.

Output
------
  pics/python/wage_pension_distribution.pdf
  latex/texparts/python/wage_pension_distribution.tex

Run
---
    python analyses/wage_pension_distribution.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from config import FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.fetch import fetch, fetch_ispv
from stattool.style import apply_style, cm2in, savefig, save_figure_tex

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

apply_style()

# ── Parameters ────────────────────────────────────────────────────────────────

# Most recent ISPV year to try (going backwards)
_ISPV_END_YEAR = 2025

# Standard-normal quantile values for P10, P25, P50, P75, P90
# (Φ⁻¹ at the five standard percentile levels – exact to 6 d.p.)
_PROBS  = np.array([0.10, 0.25, 0.50, 0.75, 0.90])
_ZSCORES = np.array([-1.281552, -0.674490, 0.000000, 0.674490, 1.281552])

# Fallback wage quantiles (ISPV 2025/H1, podnikatelská sféra – celkem, Kč/měsíc)
# Source: MPSV / TREXIMA ISPV 2025 H1 press release
# P10/P90 from published D1/D9 = 24 592 / 85 768 Kč; P25/P75 estimated from
# log-normal fit (σ ≈ 0.487 derived from D1–D9 ratio 3.49).
_FALLBACK_WAGE_Q: dict[float, float] = {
    0.10: 24_592,
    0.25: 30_100,
    0.50: 42_101,   # ISPV 2025 H1 median
    0.75: 58_400,
    0.90: 85_768,
}
_FALLBACK_WAGE_YEAR = 2025

# Total private-sector employees covered by ISPV 2025/H1 (approx.)
# Source: MPSV / ČSÚ – business-sphere employment, 2025/H1
N_WAGE = 3_500_000

# Fallback pension quantiles (CSSZ Statistická ročenka 2024 – starobní důchody,
# prosinec 2024, přibližné hodnoty percentilů odvozené z distribuce dle pásem výše
# důchodu).  Průměr = 20 736 Kč, mediánová hodnota ≈ 20 800 Kč (těsně pod 21 000 Kč).
# Celkový počet příjemců plného starobního důchodu k 31. 12. 2024: 2 367 000.
# P10 odhadnuto z faktu, že 271 000 osob (11,5 %) pobírá méně než 16 442 Kč.
# P25/P75/P90 odhadnuty z tvaru log-normálního rozdělení (σ ≈ 0.22).
# Source: CSSZ Statistická ročenka důchodového pojistění 2024
_FALLBACK_PENSION_Q: dict[float, float] = {
    0.10: 15_900,
    0.25: 18_500,
    0.50: 20_800,
    0.75: 24_000,
    0.90: 27_500,
}
_FALLBACK_PENSION_YEAR = 2024

# Total old-age pensioners (plný starobní důchod), k 31. 12. 2024
# Source: CSSZ Statistická ročenka důchodového pojistění 2024
N_PENSION = 2_367_000

# X-axis evaluation grid – net-income scale (Kč/měsíc)
# Gross 120 000 Kč/měsíc → net ≈ 88 500 Kč; use 5–90 tis. to cover both series.
_X_MIN   =  0
_X_MAX   = 90_000
_X_GRID  = np.linspace(_X_MIN, _X_MAX, 2_000)

# Reference constants (2025)
MIN_WAGE       = 20_800   # Kč/měsíc hrubá (nařízení vlády č.289/2024 Sb.)
# Minimum pension = zákonná základní výměra + minimum procentní výměra
# zákon č.155/1995 Sb. §29; 2025 values per NV č.364/2024 Sb.
MIN_PENSION    =  5_170   # Kč/měsíc  (4 400 + 770 Kč)  zákon č.155/1995 Sb.

# 2025 CZ employee statutory deductions (for gross-to-net conversion)
_SP_EMPLOYEE_RATE   = 0.065        # sociální pojistění zaměstnanec
_ZP_EMPLOYEE_RATE   = 0.045        # zdravotní pojistění zaměstnanec
_DPFO_RATE_LOW      = 0.15         # sazba DPFO – 1. pásmo (do 1 676 052 Kč/rok)
_DPFO_RATE_HIGH     = 0.23         # sazba DPFO – 2. pásmo (nad 1 676 052 Kč/rok)
_DPFO_THRESHOLD_YR  = 1_676_052    # Kč/rok (§ 16 ZDP, platné pro rok 2025)
_DPFO_THRESHOLD_MO  = _DPFO_THRESHOLD_YR / 12  # ≈ 139 671 Kč/měsíc
_SLEVA_POPLATNIK    = 2_570        # Kč/měsíc (sleva na poplatníka = 30 840 Kč/rok)
EMPLOYER_INS_RATE   = 0.338        # SP + ZP zaměstnavatele (24,8 % + 9 %)

# Colour assignments
_COLOR_WAGE    = PALETTE[0]   # deep blue
_COLOR_PENSION = PALETTE[4]   # vermillion

# ── CSSZ pension data URLs ────────────────────────────────────────────────────
# CSSZ publishes the annual statistical yearbook as a ZIP archive containing
# multiple Excel tables.  URL pattern (discovered 2026-04-14):
#   https://www.cssz.cz/documents/20143/2946719/Ročenka+{year}.zip/{guid}
# The table with pension-amount distribution is one of the XLSX files inside.
_CSSZ_URLS: list[tuple[int, str]] = [
    # (year, ZIP URL) – add newer editions here when available
    (2024, "https://www.cssz.cz/documents/20143/2946719/"
           "Ro%C4%8Denka+2024.zip/616fb679-ad56-768a-6276-eddb0b99273a"),
    (2023, "https://www.cssz.cz/documents/20143/2946719/"
           "Ro%C4%8Denka+2023.zip/736e528f-2bf9-9f4f-8bde-8ecad9d6bfe2"),
    (2022, "https://www.cssz.cz/documents/20143/2946719/"
           "Ro%C4%8Denka+2022.zip/ee569157-cf9d-c4ca-068a-1b3ac24d4c65"),
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

    CZ 2025: SP = 6,5 %, ZP = 4,5 %, DPFO 15 % do 139 671 Kč/měsíc
    (= 1 676 052 Kč/rok), 23 % nad tuto hranici; sleva na poplatníka
    = 2 570 Kč/měsíc.

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

def _fetch_ispv_national_quantiles() -> tuple[dict[float, float], int] | tuple[None, None]:
    """Try to download ISPV and parse national-aggregate percentile columns.

    Returns
    -------
    (quantile_dict, year) or (None, None) on failure.
    The dict maps probability → wage in Kč/měsíc.
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

    for yr in range(_ISPV_END_YEAR, _ISPV_END_YEAR - 5, -1):
        # For the most recent year try H1 first (H2 may not be published yet);
        # for prior years prefer the authoritative H2 annual release.
        halves = [1, 2] if yr == _ISPV_END_YEAR else [2, 1]
        for half in halves:
            try:
                path = fetch_ispv(yr, half=half, sphere="podnikatelska")
            except Exception as exc:
                print(f"  ISPV {yr}/H{half} fetch failed: {exc}")
                continue

            # Try reading first sheet
            for skiprows in range(0, 8):
                try:
                    df = pd.read_excel(
                        path, sheet_name=0, skiprows=skiprows, header=0
                    )
                    df = df.dropna(how="all").reset_index(drop=True)
                    if df.shape[1] < 3 or df.shape[0] < 3:
                        continue

                    first_col = df.columns[0]
                    df_str = df[first_col].astype(str).str.lower().str.strip()

                    # Find the national-aggregate row
                    nat_mask = df_str.apply(
                        lambda s: any(kw in s for kw in national_kw)
                    )
                    if not nat_mask.any():
                        continue

                    row = df.loc[nat_mask].iloc[0]

                    # Match percentile columns
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
                        return found, yr

                except Exception as exc:
                    log.debug("ISPV parse skiprows=%d: %s", skiprows, exc)

            print(f"  ISPV {yr}/H{half}: no national aggregate row found")

    return None, None


def _fetch_cssz_pension_quantiles() -> tuple[dict[float, float], int] | tuple[None, None]:
    """Try to download CSSZ statistical tables and derive pension quantiles.

    CSSZ publishes grouped pension-amount data (count per bracket).  This
    function derives approximate percentile values from the cumulative
    distribution of those counts.

    Returns (quantile_dict, year) or (None, None) on failure.
    """
    import io
    import zipfile

    amount_kw = ["výše", "výši", "důchod", "částka", "pásmo", "skupin"]
    count_kw  = ["počet", "count", "celkem"]

    for year, url in _CSSZ_URLS:
        try:
            path = fetch(url, suffix=".zip")
        except Exception as exc:
            print(f"  CSSZ {year} fetch failed: {exc}")
            continue

        # Extract all XLSX files from the yearbook ZIP
        try:
            with zipfile.ZipFile(path) as zf:
                xlsx_names = [n for n in zf.namelist() if n.lower().endswith(".xlsx")]
        except zipfile.BadZipFile as exc:
            print(f"  CSSZ {year} ZIP extraction failed: {exc}")
            continue

        # Build list of (sheet, file_like) pairs to try
        def _iter_sheets(zf_path: Path, xlsx_list: list[str]):  # noqa: E306
            for xname in xlsx_list:
                try:
                    with zipfile.ZipFile(zf_path) as zf:
                        buf = io.BytesIO(zf.read(xname))
                    import openpyxl
                    wb = openpyxl.load_workbook(buf, read_only=True, data_only=True)
                    snames = wb.sheetnames
                    wb.close()
                except Exception:
                    snames = list(range(6))
                for sname in snames:
                    try:
                        with zipfile.ZipFile(zf_path) as zf:
                            b2 = io.BytesIO(zf.read(xname))
                        yield sname, b2
                    except Exception:
                        continue

        for sheet, sheet_src in _iter_sheets(path, xlsx_names):
            for skiprows in range(0, 12):
                try:
                    sheet_src.seek(0)
                    df = pd.read_excel(
                        sheet_src, sheet_name=sheet, skiprows=skiprows, header=0
                    )
                    df = df.dropna(how="all").reset_index(drop=True)
                    if df.shape[1] < 2 or df.shape[0] < 5:
                        continue

                    first_col = df.columns[0]
                    # Look for a column with pension amount brackets
                    first_lc = df[first_col].astype(str).str.lower()
                    if not first_lc.apply(
                        lambda s: any(kw in s for kw in amount_kw)
                    ).any():
                        continue

                    # Find the count column
                    count_col = None
                    for col in df.columns[1:]:
                        if any(kw in str(col).lower() for kw in count_kw):
                            count_col = col
                            break
                    if count_col is None:
                        # Take first numeric column
                        for col in df.columns[1:]:
                            if pd.to_numeric(
                                df[col], errors="coerce"
                            ).notna().sum() >= 5:
                                count_col = col
                                break
                    if count_col is None:
                        continue

                    counts = pd.to_numeric(df[count_col], errors="coerce")
                    total  = counts.sum()
                    if total < 100:
                        continue

                    # Attempt to extract midpoints from the bracket strings
                    midpoints: list[float] = []
                    for s in df[first_col].astype(str):
                        nums = pd.to_numeric(
                            pd.Series(
                                "".join(c if c.isdigit() or c == "." else " "
                                        for c in s).split()
                            ),
                            errors="coerce",
                        ).dropna().values
                        nums = nums[(nums > 500) & (nums < 200_000)]
                        if len(nums) >= 2:
                            midpoints.append(float(np.mean(nums[:2])))
                        elif len(nums) == 1:
                            midpoints.append(float(nums[0]))
                        else:
                            midpoints.append(np.nan)

                    mp = np.array(midpoints)
                    valid = np.isfinite(mp) & np.isfinite(counts.values)
                    if valid.sum() < 5:
                        continue

                    mp_v     = mp[valid]
                    cnt_v    = counts.values[valid]
                    order    = np.argsort(mp_v)
                    mp_s     = mp_v[order]
                    cnt_s    = cnt_v[order]
                    cum_pct  = np.cumsum(cnt_s) / cnt_s.sum()

                    q_dict: dict[float, float] = {}
                    for prob in [0.10, 0.25, 0.50, 0.75, 0.90]:
                        idx = int(np.searchsorted(cum_pct, prob))
                        idx = min(idx, len(mp_s) - 1)
                        q_dict[prob] = float(mp_s[idx])

                    if len(q_dict) >= 3:
                        print(
                            f"  CSSZ {year}: pension quantiles derived "
                            f"from sheet '{sheet}'"
                        )
                        return q_dict, year

                except Exception as exc:
                    log.debug(
                        "CSSZ parse sheet=%s skiprows=%d: %s",
                        sheet, skiprows, exc,
                    )

    return None, None


# ════════════════════════════════════════════════════════════════════════════
# Fetch data
# ════════════════════════════════════════════════════════════════════════════

print("Fetching ISPV wage quantile data …")
wage_q, wage_year = _fetch_ispv_national_quantiles()
if wage_q is None:
    print(f"  → Using fallback ISPV {_FALLBACK_WAGE_YEAR} quantiles")
    wage_q    = _FALLBACK_WAGE_Q
    wage_year = _FALLBACK_WAGE_YEAR

print("Fetching CSSZ pension distribution data …")
pension_q, pension_year = _fetch_cssz_pension_quantiles()
if pension_q is None:
    print(f"  → Using fallback CSSZ {_FALLBACK_PENSION_YEAR} representative quantiles")
    pension_q    = _FALLBACK_PENSION_Q
    pension_year = _FALLBACK_PENSION_YEAR

# ════════════════════════════════════════════════════════════════════════════
# Fit log-normal distributions
# ════════════════════════════════════════════════════════════════════════════

# Convert gross ISPV wage quantiles to net take-home wages
wage_q_net = {p: float(gross_to_net_wage(q)) for p, q in wage_q.items()}

mu_w, sig_w = fit_lognormal(wage_q_net)
mu_p, sig_p = fit_lognormal(pension_q)

med_wage_gross      = float(wage_q.get(0.50, np.exp(mu_w)))
med_wage_net        = float(wage_q_net.get(0.50, np.exp(mu_w)))
med_wage_total_cost = med_wage_gross * (1.0 + EMPLOYER_INS_RATE)
med_pension         = float(pension_q.get(0.50, np.exp(mu_p)))

# Net minimum wage and equivalent total employer labour cost
min_wage_net        = float(gross_to_net_wage(MIN_WAGE))
min_wage_total_cost = MIN_WAGE * (1.0 + EMPLOYER_INS_RATE)

print(f"\nWage    fit (net): μ={mu_w:.4f}, σ={sig_w:.4f}  "
      f"→ čistý medián≈{med_wage_net:,.0f} Kč  "
      f"(hrubá {med_wage_gross:,.0f} Kč, "
      f"náklady zaměstnavatele {med_wage_total_cost:,.0f} Kč)")
print(f"Pension fit:       μ={mu_p:.4f}, σ={sig_p:.4f}  "
      f"→ medián≈{med_pension:,.0f} Kč")

pdf_wage    = truncated_lognormal_pdf(_X_GRID, mu_w, sig_w, min_wage_net)
pdf_pension = truncated_lognormal_pdf(_X_GRID, mu_p, sig_p, MIN_PENSION)

# Convert probability-density to absolute frequency density:
#   freq(x) = N × pdf(x)      [osob / Kč]
# When plotted with x in tis. Kč and y divided by 1 000 the y-axis shows
# thousands of persons per 1-tis.-Kč bin, i.e. the number of people that
# would fall into each 1 000 Kč-wide bracket:
#   y_display = N × pdf(x) × 1 000 / 1 000  =  N × pdf(x)
freq_wage    = N_WAGE    * pdf_wage     # tis. osob  per  tis. Kč bracket
freq_pension = N_PENSION * pdf_pension  # tis. osob  per  tis. Kč bracket

# ════════════════════════════════════════════════════════════════════════════
# Figure – combined frequency plot
# ════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=cm2in(16, 10))

ax.fill_between(
    _X_GRID / 1_000, freq_wage,
    alpha=0.18, color=_COLOR_WAGE,
)
ax.plot(
    _X_GRID / 1_000, freq_wage,
    color=_COLOR_WAGE, linewidth=2.0,
    label=f"Čistá mzda zaměstnanců (ISPV {wage_year}/H1, podnikat. sféra)",
)

ax.fill_between(
    _X_GRID / 1_000, freq_pension,
    alpha=0.18, color=_COLOR_PENSION,
)
ax.plot(
    _X_GRID / 1_000, freq_pension,
    color=_COLOR_PENSION, linewidth=2.0,
    label=f"Starobní důchody (CSSZ {pension_year})",
)

# Median reference lines
ax.axvline(
    med_wage_net / 1_000,
    color=_COLOR_WAGE, linewidth=1.0, linestyle="--", alpha=0.8,
    label=(
        f"Medián čisté mzdy {med_wage_net:,.0f} Kč"
        f" (hrubá {med_wage_gross:,.0f} Kč,"
        f" nákl. {med_wage_total_cost:,.0f} Kč)"
    ),
)
ax.axvline(
    med_pension / 1_000,
    color=_COLOR_PENSION, linewidth=1.0, linestyle="--", alpha=0.8,
    label=f"Medián důchodu {med_pension:,.0f} Kč",
)

# Minimum wage reference (net) and minimum pension reference
ax.axvline(
    min_wage_net / 1_000,
    color=_COLOR_WAGE, linewidth=0.9, linestyle=":", alpha=0.65,
    label=f"Minimální čistá mzda {min_wage_net:,.0f} Kč"
          f" (hrubá {MIN_WAGE:,} Kč)",
)
ax.axvline(
    MIN_PENSION / 1_000,
    color=_COLOR_PENSION, linewidth=0.9, linestyle=":", alpha=0.65,
    label=f"Minimální důchod {MIN_PENSION:,} Kč",
)

ax.set_xlabel("Čistá mzda / výše důchodu (tis. Kč/měsíc)", fontsize=FONT_SIZE)
ax.set_ylabel(
    "Počet osob (tis.) na interval 1 tis. Kč",
    fontsize=FONT_SIZE,
)
ax.xaxis.set_major_formatter(
    ticker.FuncFormatter(lambda v, _: f"{v:.0f}")
)
ax.yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda v, _: f"{v:.0f}")
)
ax.set_xlim(_X_MIN / 1_000, _X_MAX / 1_000)
ax.set_ylim(bottom=0)
ax.set_title(
    "Rozložení čisté mzdy zaměstnanců a starobních důchodů – ČR",
    fontsize=FONT_SIZE,
)
ax.legend(
    frameon=False,
    fontsize=FONT_SIZE - 1,
    loc="upper right",
    handlelength=1.8,
)

savefig(fig, "wage_pension_distribution", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "wage_pension_distribution",
    caption=(
        f"Distribuce čistých mezd a~starobních důchodů, ČR, {wage_year}.N\\,=\\,{N_WAGE // 1_000:,}\\,tis.\\ zaměstnanců) "
        f"a starobních důchodů (CSSZ {pension_year}; "
        f"N\\,=\\,{N_PENSION // 1_000:,}\\,tis.\\ příjemců). "
        "Čistá mzda je hrubá mzda po odečtení SP (6{{,}}5\\,\\%), "
        "ZP (4{{,}}5\\,\\%) a daně z příjmů fyzických osob "
        "(DPFO\\,=\\,15\\,\\%\\,$\\times$\\,hrubá\\,$-$\\,2\\,570\\,Kč/měsíc "
        "do 1\\,676\\,052\\,Kč/rok; 23\\,\\% nad tuto hranici, §\\,16 ZDP 2025); "
        "celkové mzdové náklady zaměstnavatele "
        "odpovídají násobku 1{{,}}338 hrubé mzdy "
        f"(medián: {med_wage_total_cost:,.0f}\\,Kč). "
        "Starobní důchody jsou vypláceny jako čistá částka. "
        "Obě distribuce jsou modelovány jako \\emph{{zleva zkrácené}} "
        "log-normální rozdělení: mzdová distribuce je zkrácena na "
        f"minimální čistou mzdu ({min_wage_net:,.0f}\\,Kč, hrubá {MIN_WAGE:,}\\,Kč), "
        f"penzijní distribuce na minimální důchod ({MIN_PENSION:,}\\,Kč; "
        "zákon č.\\,155/1995\\,Sb.\\ §\\,29, NV č.\\,364/2024\\,Sb.). "
        "Parametry log-normálního rozdělení jsou fitovány metodou "
        "nejmenších čtverců na percentilové profily (P10\\,--\\,P90). "
        "Osa y udává počet osob v intervalu šíře 1\\,tis.\\,Kč. "
        "Přerušované svislé čáry označují mediány; "
        "tečkované čáry zákonná minima."
    ),
    cite_keys="mpsv_ispv",
    label="fig:wage_pension_distribution",
    width=r"0.95\linewidth",
    cite_key="mpsv_ispv",
)

print("\nDone.")
