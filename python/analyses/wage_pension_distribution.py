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

# X-axis evaluation grid (Kč/měsíc)
_X_MIN   =  5_000
_X_MAX   = 120_000
_X_GRID  = np.linspace(_X_MIN, _X_MAX, 2_000)

# Reference constants (2026 / latest available)
MIN_WAGE       = 20_800   # Kč/měsíc (nařízení vlády č.405/2025 Sb.)

# Colour assignments
_COLOR_WAGE    = PALETTE[0]   # deep blue
_COLOR_PENSION = PALETTE[4]   # vermillion

# ── CSSZ pension data URLs ────────────────────────────────────────────────────
# CSSZ publishes "Přehled starobních důchodů podle výše důchodu" as part of
# the annual statistical yearbook.  The Excel editions typically appear at:
#   https://www.cssz.cz/documents/20143/<doc_id>/<filename>.xlsx
# The table of interest has columns [výše důchodu bracket, počet důchodů, %].
# Attempt to fetch each year's edition; fall back when unavailable.
_CSSZ_URLS: list[tuple[int, str]] = [
    # (year, URL) – add newer editions here when available
    (2024, "https://www.cssz.cz/documents/20143/99587/"
           "CSSZ-SR-DP-2024-tabulky.xlsx"),
    (2023, "https://www.cssz.cz/documents/20143/9756022/"
           "CSSZ-SR-DP-2023-tabulky.xlsx"),
    (2022, "https://www.cssz.cz/documents/20143/9756022/"
           "CSSZ-SR-DP-2022-tabulky.xlsx"),
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
    amount_kw = ["výše", "výši", "důchod", "částka", "pásmo", "skupin"]
    count_kw  = ["počet", "count", "celkem"]

    for year, url in _CSSZ_URLS:
        try:
            path = fetch(url, suffix=".xlsx")
        except Exception as exc:
            print(f"  CSSZ {year} fetch failed: {exc}")
            continue

        # Try every sheet
        try:
            import openpyxl
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            sheets = wb.sheetnames
            wb.close()
        except Exception:
            sheets = list(range(6))

        for sheet in sheets:
            for skiprows in range(0, 12):
                try:
                    df = pd.read_excel(
                        path, sheet_name=sheet, skiprows=skiprows, header=0
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

mu_w, sig_w = fit_lognormal(wage_q)
mu_p, sig_p = fit_lognormal(pension_q)

med_wage    = float(wage_q.get(0.50, np.exp(mu_w)))
med_pension = float(pension_q.get(0.50, np.exp(mu_p)))

print(f"\nWage    fit: μ={mu_w:.4f}, σ={sig_w:.4f}  "
      f"→ median≈{np.exp(mu_w):,.0f} Kč")
print(f"Pension fit: μ={mu_p:.4f}, σ={sig_p:.4f}  "
      f"→ median≈{np.exp(mu_p):,.0f} Kč")

pdf_wage    = lognormal_pdf(_X_GRID, mu_w, sig_w)
pdf_pension = lognormal_pdf(_X_GRID, mu_p, sig_p)

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
    label=f"Mzdy zaměstnanců (ISPV {wage_year}/H1, podnikat. sféra)",
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
    med_wage / 1_000,
    color=_COLOR_WAGE, linewidth=1.0, linestyle="--", alpha=0.8,
    label=f"Medián mzdy {med_wage:,.0f} Kč",
)
ax.axvline(
    med_pension / 1_000,
    color=_COLOR_PENSION, linewidth=1.0, linestyle="--", alpha=0.8,
    label=f"Medián důchodu {med_pension:,.0f} Kč",
)

# Minimum wage reference
ax.axvline(
    MIN_WAGE / 1_000,
    color="gray", linewidth=0.9, linestyle=":", alpha=0.7,
    label=f"Minimální mzda {MIN_WAGE:,} Kč",
)

ax.set_xlabel("Hrubá mzda / výše důchodu (tis. Kč/měsíc)", fontsize=FONT_SIZE)
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
    "Rozložení mzdy zaměstnanců a starobních důchodů – ČR",
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
        f"Odhadnuté frekvenční distribuce hrubých mezd zaměstnanců "
        f"(ISPV {wage_year}/H1, podnikatelská sféra, MPSV/TREXIMA; "
        f"N\\,=\\,{N_WAGE // 1_000:,}\\,tis.\\ zaměstnanců) "
        f"a starobních důchodů (CSSZ {pension_year}; "
        f"N\\,=\\,{N_PENSION // 1_000:,}\\,tis.\\ příjemců). "
        "Obě distribuce jsou aproximovány log-normálním rozdělením "
        "fitovaným metodou nejmenších čtverců na percentilové profily "
        "(P10\\,--\\,P90). "
        "Osa y udává počet osob v intervalu šíře 1\\,tis.\\,Kč. "
        "Přerušované svislé čáry označují mediány; "
        "tečkovaná čára minimální mzdu."
    ),
    label="fig:wage_pension_distribution",
    width=r"0.95\linewidth",
    cite_key="mpsv_ispv",
)

print("\nDone.")
