r"""
Czech income-tax and social-insurance model for the 2026 tax year.

Models the effective tax burden (tax wedge) for:
  * Zaměstnanci (employees) – gross wage → net income
  * OSVČ using výdajový paušál (60 % and 80 %)
  * OSVČ using paušální daň (pásmo 1)

Legislation:
  ZDP zákon č. 586/1992 Sb.
  Zákon č. 270/2023 Sb. (progressive DPFO thresholds)
  NV č. 405/2025 Sb. (minimum wage 2026)
  NV č. 365/2025 Sb. (SP/ZP rates and assessment base 2026)

Figures
-------
  ``cz_tax_wedge``    – continuous tax-wedge curves over total employer cost
  ``cz_tax_breakdown`` – stacked-bar breakdown at key income levels

Output
------
  pics/python/cz_tax_wedge.pdf
  pics/python/cz_tax_breakdown.pdf
  latex/texparts/python/cz_tax_wedge.tex
  latex/texparts/python/cz_tax_breakdown.tex

Run
---
    python analyses/cz_tax_model.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from config import FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.style import apply_style, cm2in, savefig, save_figure_tex

apply_style()

# ── 2026 tax parameters ───────────────────────────────────────────────────────

MIN_WAGE: float = 20_800           # Kč/month  (NV č. 405/2025 Sb.)
AVG_WAGE: float = 48_967           # Kč/month  (všeobecný vyměřovací základ)

# Employer insurance (24.8 % SP + 9 % ZP → 33.8 %)
EMPLOYER_INS_RATE: float = 0.338

# Employee insurance
EMPLOYEE_SP_RATE: float = 0.065    # 6.5 % SP
EMPLOYEE_ZP_RATE: float = 0.045    # 4.5 % ZP
EMPLOYEE_INS_RATE: float = EMPLOYEE_SP_RATE + EMPLOYEE_ZP_RATE  # 11 %

# DPFO progressive rates (§ 16 ZDP)
DPFO_RATE_LOW: float  = 0.15       # 15 % up to 36× monthly avg wage
DPFO_RATE_HIGH: float = 0.23       # 23 % above that threshold
DPFO_THRESHOLD_YEAR: float = 36 * AVG_WAGE  # = 1 762 812 Kč/year (§ 16a ZDP)

# Základní sleva na dani (§ 35ba ZDP)
SLEVA_NA_POPLATNIKA: float = 30_840  # Kč/year

# OSVČ parameters
OSVC_SP_RATE: float     = 0.292    # 28 % + 1.2 % nemocenské = 29.2 %
OSVC_ZP_RATE: float     = 0.135    # 13.5 % ZP
OSVC_BASE_SP: float     = 0.55     # SP vyměřovací základ = 55 % základu daně
OSVC_BASE_ZP: float     = 0.50     # ZP vyměřovací základ = 50 % základu daně
OSVC_SP_MIN_MONTHLY: float = 5_720 # Kč/month (min záloha SP 2026)
OSVC_ZP_MIN_MONTHLY: float = 3_306 # Kč/month (min záloha ZP 2026)

# Paušální daň pásmo 1 (§ 2a zákona č. 586/1992 Sb.)
PAUSALNI_DAN_MONTHLY: float = 7_498   # Kč/month (SP+ZP+DPFO paušál pásmo 1)
PAUSALNI_REVENUE_MAX: float = 83_333  # Kč/month (příjmový strop pásmo 1)


# ── Employee functions ────────────────────────────────────────────────────────

def tax_breakdown_employee(gross_monthly: float) -> dict:
    """Return itemised tax breakdown for an employee.

    Parameters
    ----------
    gross_monthly:
        Gross monthly wage in Kč.

    Returns
    -------
    dict with keys: gross, employer_sp, employer_zp, employer_total,
    employee_sp, employee_zp, dpfo, net_income, tax_wedge.
    """
    # Employer contributions (on top of gross)
    employer_ins = gross_monthly * EMPLOYER_INS_RATE
    employer_total = gross_monthly + employer_ins

    # Employee social and health insurance
    employee_sp = gross_monthly * EMPLOYEE_SP_RATE
    employee_zp = gross_monthly * EMPLOYEE_ZP_RATE

    # DPFO – super-gross base = employer total; progressive
    annual_base = employer_total * 12
    if annual_base <= DPFO_THRESHOLD_YEAR:
        dpfo_annual = annual_base * DPFO_RATE_LOW
    else:
        dpfo_annual = (
            DPFO_THRESHOLD_YEAR * DPFO_RATE_LOW
            + (annual_base - DPFO_THRESHOLD_YEAR) * DPFO_RATE_HIGH
        )
    # Apply základní sleva (capped to zero)
    dpfo_annual = max(0.0, dpfo_annual - SLEVA_NA_POPLATNIKA)
    dpfo_monthly = dpfo_annual / 12

    net_income = gross_monthly - employee_sp - employee_zp - dpfo_monthly

    tax_wedge = (employer_total - net_income) / employer_total

    return {
        "gross":          gross_monthly,
        "employer_sp":    employer_ins * (24.8 / 33.8),   # approx split
        "employer_zp":    employer_ins * (9.0  / 33.8),
        "employer_total": employer_total,
        "employee_sp":    employee_sp,
        "employee_zp":    employee_zp,
        "dpfo":           dpfo_monthly,
        "net_income":     net_income,
        "tax_wedge":      tax_wedge,
    }


def tax_wedge_employee(gross_monthly: float) -> float:
    """Tax wedge for an employee.

    Tax wedge = (employer_total_cost − net_take_home) / employer_total_cost.
    """
    return tax_breakdown_employee(gross_monthly)["tax_wedge"]


def _employer_cost_to_gross(employer_cost: float) -> float:
    """Convert total employer cost to gross wage."""
    return employer_cost / (1 + EMPLOYER_INS_RATE)


# ── OSVČ výdajový paušál functions ───────────────────────────────────────────

def tax_breakdown_osvc(revenue_monthly: float, expense_rate: float = 0.60) -> dict:
    """Return itemised breakdown for OSVČ using výdajový paušál.

    Parameters
    ----------
    revenue_monthly:
        Monthly turnover (příjmy) in Kč.
    expense_rate:
        Paušální výdajový koeficient (0.80 / 0.60 / 0.40).

    Returns
    -------
    dict with keys analogous to tax_breakdown_employee.
    """
    annual_revenue = revenue_monthly * 12
    annual_expenses = annual_revenue * expense_rate
    tax_base_annual = annual_revenue - annual_expenses   # základ daně

    # SP
    sp_base_annual = max(tax_base_annual * OSVC_BASE_SP,
                         OSVC_SP_MIN_MONTHLY * 12)
    sp_annual = sp_base_annual * OSVC_SP_RATE
    sp_monthly = sp_annual / 12

    # ZP
    zp_base_annual = max(tax_base_annual * OSVC_BASE_ZP,
                         OSVC_ZP_MIN_MONTHLY * 12)
    zp_annual = zp_base_annual * OSVC_ZP_RATE
    zp_monthly = zp_annual / 12

    # DPFO – SP and ZP are deductible from tax base
    dpfo_base_annual = max(0.0, tax_base_annual - sp_annual - zp_annual)
    if dpfo_base_annual <= DPFO_THRESHOLD_YEAR:
        dpfo_annual = dpfo_base_annual * DPFO_RATE_LOW
    else:
        dpfo_annual = (
            DPFO_THRESHOLD_YEAR * DPFO_RATE_LOW
            + (dpfo_base_annual - DPFO_THRESHOLD_YEAR) * DPFO_RATE_HIGH
        )
    dpfo_annual = max(0.0, dpfo_annual - SLEVA_NA_POPLATNIKA)
    dpfo_monthly = dpfo_annual / 12

    net_income = revenue_monthly - sp_monthly - zp_monthly - dpfo_monthly

    # "Employer cost" for OSVČ = total revenue (no separate employer contribution)
    tax_wedge = (revenue_monthly - net_income) / revenue_monthly if revenue_monthly > 0 else 0.0

    return {
        "revenue":       revenue_monthly,
        "expense_rate":  expense_rate,
        "tax_base":      tax_base_annual / 12,
        "sp":            sp_monthly,
        "zp":            zp_monthly,
        "dpfo":          dpfo_monthly,
        "net_income":    net_income,
        "tax_wedge":     tax_wedge,
    }


def tax_wedge_osvc_vydajovy(revenue_monthly: float, expense_rate: float = 0.60) -> float:
    """Tax wedge for OSVČ using výdajový paušál."""
    return tax_breakdown_osvc(revenue_monthly, expense_rate)["tax_wedge"]


# ── OSVČ paušální daň ─────────────────────────────────────────────────────────

def tax_wedge_osvc_pausalni(revenue_monthly: float, pasmo: int = 1) -> float:
    """Tax wedge for OSVČ on paušální daň (pásmo 1 only).

    Returns NaN for revenues above the pásmo 1 cap (83 333 Kč/month).
    """
    if pasmo != 1:
        raise ValueError("Only pásmo 1 is implemented.")
    if revenue_monthly <= 0:
        return 0.0
    if revenue_monthly > PAUSALNI_REVENUE_MAX:
        return float("nan")
    net = revenue_monthly - PAUSALNI_DAN_MONTHLY
    return (revenue_monthly - net) / revenue_monthly


# ── Figure 1: continuous tax-wedge curves ────────────────────────────────────

# Build series over employer-cost axis for employees;
# for OSVČ use revenue axis (same x scale → comparable)
# We align x as "monthly cost to the economy" throughout.

EC = np.linspace(20_000, 300_000, 1_200)   # employer cost axis

# Employee: convert employer cost → gross
gross_arr = EC / (1 + EMPLOYER_INS_RATE)
wedge_emp   = np.array([tax_wedge_employee(g)          for g in gross_arr])

# OSVČ: revenue ≈ employer cost (no separate employer levy), same x axis
wedge_60    = np.array([tax_wedge_osvc_vydajovy(r, 0.60) for r in EC])
wedge_80    = np.array([tax_wedge_osvc_vydajovy(r, 0.80) for r in EC])

# Paušální daň (only valid up to cap)
wedge_paul  = np.array([tax_wedge_osvc_pausalni(r, 1)    for r in EC])

# Vertical guides
MIN_EC   = MIN_WAGE * (1 + EMPLOYER_INS_RATE)   # ≈ 27 873
AVG_EC   = AVG_WAGE * (1 + EMPLOYER_INS_RATE)   # ≈ 65 539

fig1, ax1 = plt.subplots(figsize=cm2in(15, 9))

ax1.plot(EC / 1_000, wedge_emp  * 100, color=PALETTE[0], label="Zaměstnanec")
ax1.plot(EC / 1_000, wedge_60   * 100, color=PALETTE[1], label="OSVČ výdaje 60 %")
ax1.plot(EC / 1_000, wedge_80   * 100, color=PALETTE[2], label="OSVČ výdaje 80 %")

# Paušální daň – mask NaN beyond cap
mask_paul = ~np.isnan(wedge_paul)
ax1.plot(EC[mask_paul] / 1_000, wedge_paul[mask_paul] * 100,
         color=PALETTE[3], linestyle="--", label="Paušální daň pásmo 1")
# Shade valid region for paušální daň
if mask_paul.any():
    ax1.axvspan(EC[mask_paul].min() / 1_000, EC[mask_paul].max() / 1_000,
                alpha=0.06, color=PALETTE[3], linewidth=0)

# Vertical guides
ax1.axvline(MIN_EC / 1_000, color="grey", linewidth=0.8, linestyle=":")
ax1.axvline(AVG_EC / 1_000, color="grey", linewidth=0.8, linestyle=":")
ybot = ax1.get_ylim()[0]
ax1.text(MIN_EC / 1_000 + 0.5, 10, "min.\nmzda", fontsize=FONT_SIZE - 1,
         color="grey", va="bottom")
ax1.text(AVG_EC / 1_000 + 0.5, 10, "prům.\nmzda", fontsize=FONT_SIZE - 1,
         color="grey", va="bottom")

ax1.set_xlabel("Celkové náklady práce (tis. Kč/měsíc)")
ax1.set_ylabel("Daňový klín (%)")
ax1.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=100, decimals=0))
ax1.legend(loc="lower right", framealpha=0.9)

savefig(fig1, "cz_tax_wedge", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "cz_tax_wedge",
    caption=(
        "Daňový klín jako funkce celkových nákladů práce pro zaměstnance "
        "a OSVČ v roce 2026. Svislé čáry označují minimální a průměrnou mzdu. "
        "Daňový klín = (náklady zaměstnavatele − čistý příjem) / náklady."
    ),
    label="fig:cz_tax_wedge",
    width=r"0.95\linewidth",
)

# ── Figure 2: stacked-bar breakdown at key income levels ─────────────────────

LEVELS = {
    "Min. mzda\n(20 800)":     MIN_WAGE,
    "Prům. mzda\n(48 967)":    AVG_WAGE,
    "2× prům.\n(97 934)":      AVG_WAGE * 2,
}

groups   = ["Zaměstnanec", "OSVČ 60 %", "OSVČ 80 %"]
n_levels = len(LEVELS)
n_groups = len(groups)

bar_width = 0.22
x_pos     = np.arange(n_levels)

fig2, ax2 = plt.subplots(figsize=cm2in(16, 10))

for gi, group in enumerate(groups):
    offsets = x_pos + (gi - 1) * bar_width

    nets, sps, zps, dpfos = [], [], [], []
    for label, wage in LEVELS.items():
        if group == "Zaměstnanec":
            bd = tax_breakdown_employee(wage)
            nets.append(bd["net_income"])
            sps.append(bd["employee_sp"] + bd["employer_sp"] + bd["employer_zp"])
            zps.append(bd["employee_zp"])
            dpfos.append(bd["dpfo"])
            total = bd["employer_total"]
        else:
            rate = 0.60 if "60" in group else 0.80
            bd = tax_breakdown_osvc(wage, rate)
            nets.append(bd["net_income"])
            sps.append(bd["sp"])
            zps.append(bd["zp"])
            dpfos.append(bd["dpfo"])
            total = wage

    nets_  = np.array(nets)  / 1_000
    sps_   = np.array(sps)   / 1_000
    zps_   = np.array(zps)   / 1_000
    dpfos_ = np.array(dpfos) / 1_000

    lbl = lambda s: s if gi == 0 else "_nolegend_"
    ax2.bar(offsets, nets_,  bar_width, label=lbl("Čistý příjem"), color=PALETTE[0], alpha=0.85)
    ax2.bar(offsets, sps_,   bar_width, bottom=nets_,         label=lbl("SP"), color=PALETTE[2])
    ax2.bar(offsets, zps_,   bar_width, bottom=nets_ + sps_,  label=lbl("ZP"), color=PALETTE[3])
    ax2.bar(offsets, dpfos_, bar_width, bottom=nets_ + sps_ + zps_, label=lbl("DPFO"), color=PALETTE[4])

    # Label group below bars
    for k, off in enumerate(offsets):
        ax2.text(off, -1.5, group, ha="center", va="top",
                 fontsize=FONT_SIZE - 1, rotation=45)

ax2.set_xticks(x_pos)
ax2.set_xticklabels(list(LEVELS.keys()))
ax2.set_ylabel("Tis. Kč / měsíc")
ax2.legend(loc="upper left", framealpha=0.9)

savefig(fig2, "cz_tax_breakdown", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "cz_tax_breakdown",
    caption=(
        "Struktura zdanění (SP, ZP, DPFO a čistý příjem) pro zaměstnance "
        "a OSVČ při minimální, průměrné a dvojnásobné průměrné mzdě, 2026."
    ),
    label="fig:cz_tax_breakdown",
    width=r"0.95\linewidth",
)

print("Done.")
