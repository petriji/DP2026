r"""
Czech statutory old-age pension model for the 2026 calculation rules.

Models pension entitlement and replacement rates for:
  * Zaměstnanci (employees)
  * OSVČ using výdajový paušál (40 %, 60 %, 80 %)
  * OSVČ on paušální daň pásmo 1

Legislation:
  Zákon č. 155/1995 Sb. (zákon o důchodovém pojištění)
  Zákon č. 270/2023 Sb. (progressive pension reform, new reduction boundaries)
  NV č. 365/2025 Sb. (all-purpose assessment base, vyměřovací základ 2026)

Figures
-------
  ``cz_pension_solidarity`` – 2-panel: absolute pension + replacement rate
  ``cz_pension_income``     – single-panel absolute pension comparison
  ``cz_tax_wedge_comparison`` – scatter: tax wedge vs. replacement rate

Output
------
  pics/python/cz_pension_solidarity.pdf
  pics/python/cz_pension_income.pdf
  pics/python/cz_tax_wedge_comparison.pdf
  latex/texparts/python/ (matching .tex files)

Run
---
    python analyses/cz_pension_model.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))  # for sibling analyses imports

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from config import FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.style import apply_style, cm2in, savefig, save_figure_tex

# Import tax functions for the wedge-vs-replacement scatter
from cz_tax_model import (
    tax_wedge_employee,
    tax_wedge_osvc_vydajovy,
    tax_wedge_osvc_pausalni,
    _employer_cost_to_gross,
    EMPLOYER_INS_RATE,
    MIN_WAGE,
    AVG_WAGE,
    OSVC_SP_RATE,
    OSVC_ZP_RATE,
    OSVC_BASE_SP,
    OSVC_BASE_ZP,
    OSVC_SP_MIN_MONTHLY,
    OSVC_ZP_MIN_MONTHLY,
)

apply_style()

# ── 2026 pension parameters ───────────────────────────────────────────────────

RH1: float  = 50_000          # 1. redukční hranice (Kč/month)
RH2: float  = 182_400         # 2. redukční hranice (Kč/month)
ZAKLADNI_VYMERA: float = 4_570    # základní výměra (Kč/month)
PCT_PER_YEAR: float = 0.01495     # procentní výměra za rok pojištění (§ 34 ZDP)

MEDIAN_EMP_WAGE: float = 40_709   # ISPV 2024 H2 median hrubá mzda zaměstnanec
PAUSALNI_BASE: float   = 14_690   # fiktivní základ paušální daně pásmo 1

DEFAULT_YEARS: int = 40


# ── Reduction function ────────────────────────────────────────────────────────

def _reduce_ovz(ovz_monthly: float) -> float:
    """Apply statutory reduction thresholds to personal assessment base.

    Parameters
    ----------
    ovz_monthly:
        Average monthly personal assessment base (OVZ) in Kč.

    Returns
    -------
    Reduced OVZ for procentní výměra calculation.
    """
    if ovz_monthly <= RH1:
        return ovz_monthly
    elif ovz_monthly <= RH2:
        return RH1 + (ovz_monthly - RH1) * 0.26
    else:
        return RH1 + (RH2 - RH1) * 0.26  # above RH2 → 0 % counted


# ── Pension calculation functions ─────────────────────────────────────────────

def pension_employee(gross_monthly: float, years: int = DEFAULT_YEARS) -> float:
    """Statutory monthly old-age pension for a full-career employee.

    The assessment base equals gross monthly wage (employee side).

    Parameters
    ----------
    gross_monthly:
        Average gross monthly wage over the career.
    years:
        Years of pensionable service.

    Returns
    -------
    Monthly pension in Kč.
    """
    ovz_reduced = _reduce_ovz(gross_monthly)
    procentni   = ovz_reduced * PCT_PER_YEAR * years
    return ZAKLADNI_VYMERA + procentni


def pension_osvc(
    revenue_monthly: float,
    expense_rate: float = 0.60,
    years: int = DEFAULT_YEARS,
) -> float:
    """Statutory monthly old-age pension for OSVČ using výdajový paušál.

    The OSVČ SP assessment base = 55 % of the tax base, where the tax base
    equals revenue × (1 − expense_rate).  This is the personal assessment
    base (OVZ) used for pension entitlement.

    Parameters
    ----------
    revenue_monthly:
        Monthly turnover in Kč.
    expense_rate:
        Výdajový paušál coefficient – the fraction of revenue recognised as
        expenses (default 0.60 for živnosti ostatní).  Pass 0.80 for živnosti
        řemeslné, 0.40 for jiné příjmy.
    years:
        Years of pensionable service.
    """
    annual_revenue = revenue_monthly * 12
    annual_tax_base = annual_revenue * (1 - expense_rate)
    sp_base_monthly = max(
        annual_tax_base * OSVC_BASE_SP / 12,
        OSVC_SP_MIN_MONTHLY,
    )
    ovz_reduced = _reduce_ovz(sp_base_monthly)
    procentni   = ovz_reduced * PCT_PER_YEAR * years
    return ZAKLADNI_VYMERA + procentni


def pension_pausalni(revenue_monthly: float, years: int = DEFAULT_YEARS) -> float:
    """Statutory monthly old-age pension for OSVČ on paušální daň.

    Uses the fixed PAUSALNI_BASE as the SP vyměřovací základ regardless of
    actual revenue (within pásmo 1 cap).
    """
    ovz_reduced = _reduce_ovz(PAUSALNI_BASE)
    procentni   = ovz_reduced * PCT_PER_YEAR * years
    return ZAKLADNI_VYMERA + procentni


def replacement_rate(pension: float, gross_monthly: float) -> float:
    """Pension replacement rate = pension / gross income."""
    if gross_monthly <= 0:
        return 0.0
    return pension / gross_monthly


# ── Build data arrays ─────────────────────────────────────────────────────────

X = np.linspace(MIN_WAGE, 200_000, 800)   # gross wage / OSVČ revenue axis

pen_emp     = np.array([pension_employee(x)          for x in X])
pen_vyd60   = np.array([pension_osvc(x, 0.60)         for x in X])  # výdaje 60 %
pen_vyd80   = np.array([pension_osvc(x, 0.80)         for x in X])  # výdaje 80 %
pen_vyd40   = np.array([pension_osvc(x, 0.40)         for x in X])  # výdaje 40 %
pen_paul    = np.array([pension_pausalni(x)            for x in X])  # constant

rr_emp      = np.array([replacement_rate(p, w) for p, w in zip(pen_emp,    X)])
rr_vyd60    = np.array([replacement_rate(p, r) for p, r in zip(pen_vyd60,  X)])
rr_vyd80    = np.array([replacement_rate(p, r) for p, r in zip(pen_vyd80,  X)])
rr_vyd40    = np.array([replacement_rate(p, r) for p, r in zip(pen_vyd40,  X)])
rr_paul     = np.array([replacement_rate(p, r) for p, r in zip(pen_paul,   X)])


# ── Figure 1: cz_pension_solidarity (2-panel) ─────────────────────────────────

fig1, (ax_a, ax_b) = plt.subplots(1, 2, figsize=cm2in(18, 9))

# Panel A – absolute pension
ax_a.plot(X / 1_000, pen_emp    / 1_000, color=PALETTE[0], label="Zaměstnanec")
ax_a.plot(X / 1_000, pen_vyd60  / 1_000, color=PALETTE[1], label="OSVČ výdaje 60 %")
ax_a.plot(X / 1_000, pen_vyd80  / 1_000, color=PALETTE[2], label="OSVČ výdaje 80 %")
ax_a.plot(X / 1_000, pen_vyd40  / 1_000, color=PALETTE[3], label="OSVČ výdaje 40 %")
ax_a.plot(X / 1_000, pen_paul   / 1_000, color=PALETTE[4], linestyle="--",
          label="Paušální daň pás. 1")

for ax in (ax_a, ax_b):
    ax.axvline(MIN_WAGE / 1_000, color="grey", linewidth=0.8, linestyle=":")
    ax.axvline(AVG_WAGE / 1_000, color="grey", linewidth=0.8, linestyle=":")

ax_a.scatter([MEDIAN_EMP_WAGE / 1_000],
             [pension_employee(MEDIAN_EMP_WAGE) / 1_000],
             color=PALETTE[0], s=30, zorder=5)
ax_a.set_xlabel("Hrubý příjem (tis. Kč/měsíc)")
ax_a.set_ylabel("Důchod (tis. Kč/měsíc)")
ax_a.set_title("Výše starobního důchodu")
ax_a.legend(fontsize=FONT_SIZE - 1, loc="upper left")

# Panel B – replacement rate
ax_b.plot(X / 1_000, rr_emp    * 100, color=PALETTE[0])
ax_b.plot(X / 1_000, rr_vyd60  * 100, color=PALETTE[1])
ax_b.plot(X / 1_000, rr_vyd80  * 100, color=PALETTE[2])
ax_b.plot(X / 1_000, rr_vyd40  * 100, color=PALETTE[3])
ax_b.plot(X / 1_000, rr_paul   * 100, color=PALETTE[4], linestyle="--")

ax_b.scatter([MEDIAN_EMP_WAGE / 1_000],
             [replacement_rate(pension_employee(MEDIAN_EMP_WAGE),
                               MEDIAN_EMP_WAGE) * 100],
             color=PALETTE[0], s=30, zorder=5)
ax_b.set_xlabel("Hrubý příjem (tis. Kč/měsíc)")
ax_b.set_ylabel("Náhradový poměr (%)")
ax_b.set_title("Náhradový poměr")
ax_b.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=100, decimals=0))

# Annotate min/avg lines on panel A
for ax, dy in [(ax_a, 1), (ax_b, 2)]:
    ax.text(MIN_WAGE / 1_000 + 0.3, ax.get_ylim()[0] + dy,
            "min.", fontsize=FONT_SIZE - 2, color="grey")
    ax.text(AVG_WAGE / 1_000 + 0.3, ax.get_ylim()[0] + dy,
            "prům.", fontsize=FONT_SIZE - 2, color="grey")

savefig(fig1, "cz_pension_solidarity", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "cz_pension_solidarity",
    caption=(
        "Výše starobního důchodu (vlevo) a náhradový poměr (vpravo) "
        "v závislosti na hrubém příjmu pro zaměstnance a různé formy OSVČ, "
        "parametry 2026. Tečkovaná svislá čára označuje minimální a průměrnou mzdu."
    ),
    label="fig:cz_pension_solidarity",
    width=r"0.95\linewidth",
)


# ── Figure 2: cz_pension_income (single panel) ────────────────────────────────

fig2, ax2 = plt.subplots(figsize=cm2in(15, 9))

ax2.plot(X / 1_000, pen_emp    / 1_000, color=PALETTE[0], label="Zaměstnanec")
ax2.plot(X / 1_000, pen_vyd60  / 1_000, color=PALETTE[1], label="OSVČ výdaje 60 %")
ax2.plot(X / 1_000, pen_vyd80  / 1_000, color=PALETTE[2], label="OSVČ výdaje 80 %")
ax2.plot(X / 1_000, pen_vyd40  / 1_000, color=PALETTE[3], label="OSVČ výdaje 40 %")
ax2.plot(X / 1_000, pen_paul   / 1_000, color=PALETTE[4], linestyle="--",
         label="Paušální daň pás. 1")

ax2.axvline(MIN_WAGE / 1_000,      color="grey", linewidth=0.8, linestyle=":")
ax2.axvline(AVG_WAGE / 1_000,      color="grey", linewidth=0.8, linestyle=":")
ax2.axvline(MEDIAN_EMP_WAGE / 1_000, color=PALETTE[0], linewidth=0.8,
            linestyle="-.", alpha=0.6)

ax2.text(MIN_WAGE / 1_000 + 0.3,      0.6, "min. mzda",
         fontsize=FONT_SIZE - 1, color="grey")
ax2.text(AVG_WAGE / 1_000 + 0.3,      0.6, "prům. mzda",
         fontsize=FONT_SIZE - 1, color="grey")
ax2.text(MEDIAN_EMP_WAGE / 1_000 + 0.3, 0.6, "medián mzdy",
         fontsize=FONT_SIZE - 1, color=PALETTE[0], alpha=0.8)

ax2.set_xlabel("Hrubý příjem (tis. Kč/měsíc)")
ax2.set_ylabel("Starobní důchod (tis. Kč/měsíc)")
ax2.legend(loc="upper left")

savefig(fig2, "cz_pension_income", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "cz_pension_income",
    caption=(
        "Výše statutárního starobního důchodu v závislosti na hrubém příjmu "
        "pro zaměstnance a OSVČ (různé formy paušálu), parametry 2026."
    ),
    label="fig:cz_pension_income",
    width=r"0.95\linewidth",
)


# ── Figure 3: cz_tax_wedge_comparison (scatter: tax wedge vs. replacement rate)

REV_RANGE = np.linspace(MIN_WAGE, 200_000, 400)

# Employee: convert revenue axis to gross wage (employer-cost / (1+ins))
gross_range   = REV_RANGE  # same scale – revenue IS the gross for employees here

tw_emp_arr    = np.array([tax_wedge_employee(g)              for g in gross_range])
tw_60_arr     = np.array([tax_wedge_osvc_vydajovy(r, 0.60)   for r in REV_RANGE])
tw_80_arr     = np.array([tax_wedge_osvc_vydajovy(r, 0.80)   for r in REV_RANGE])
tw_paul_arr   = np.array([tax_wedge_osvc_pausalni(r)         for r in REV_RANGE])

rr_emp_arr    = np.array([replacement_rate(pension_employee(g), g)              for g in gross_range])
rr_60_arr     = np.array([replacement_rate(pension_osvc(r, 0.60), r)            for r in REV_RANGE])
rr_80_arr     = np.array([replacement_rate(pension_osvc(r, 0.80), r)            for r in REV_RANGE])
rr_paul_arr   = np.array([replacement_rate(pension_pausalni(r), r)              for r in REV_RANGE])
mask_paul_sc  = ~np.isnan(tw_paul_arr)

fig3, ax3 = plt.subplots(figsize=cm2in(15, 9))

ax3.plot(tw_emp_arr   * 100, rr_emp_arr  * 100, color=PALETTE[0], label="Zaměstnanec")
ax3.plot(tw_60_arr    * 100, rr_60_arr   * 100, color=PALETTE[1], label="OSVČ výdaje 60 %")
ax3.plot(tw_80_arr    * 100, rr_80_arr   * 100, color=PALETTE[2], label="OSVČ výdaje 80 %")
ax3.plot(tw_paul_arr[mask_paul_sc] * 100, rr_paul_arr[mask_paul_sc] * 100,
         color=PALETTE[4], linestyle="--", label="Paušální daň pás. 1")

# Annotate min_wage and avg_wage dots on each series
for income, marker_color, series_tw, series_rr in [
    (MIN_WAGE, "k", tw_emp_arr, rr_emp_arr),
    (AVG_WAGE, "k", tw_emp_arr, rr_emp_arr),
]:
    idx = np.argmin(np.abs(gross_range - income))
    ax3.scatter(series_tw[idx] * 100, series_rr[idx] * 100,
                color=marker_color, s=25, zorder=5)
    label = "min. mzda" if income == MIN_WAGE else "prům. mzda"
    ax3.annotate(label,
                 (series_tw[idx] * 100, series_rr[idx] * 100),
                 textcoords="offset points", xytext=(4, 4),
                 fontsize=FONT_SIZE - 2, color="grey")

ax3.set_xlabel("Daňový klín (%)")
ax3.set_ylabel("Náhradový poměr (%)")
ax3.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=100, decimals=0))
ax3.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=100, decimals=0))
ax3.legend(loc="upper right")

savefig(fig3, "cz_tax_wedge_comparison", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "cz_tax_wedge_comparison",
    caption=(
        "Parametrický vztah mezi daňovým klínem a náhradovým poměrem "
        "starobního důchodu pro zaměstnance a OSVČ – každý bod odpovídá "
        "jedné úrovni příjmu z intervalu 20 800–200 000 Kč/měsíc (2026)."
    ),
    label="fig:cz_tax_wedge_comparison",
    width=r"0.95\linewidth",
)

print("Done.")
