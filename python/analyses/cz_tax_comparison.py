r"""
Effective taxation: OSVČ vs. zaměstnanec (CZ) – legislativní výpočet 2026.

Computes and plots the effective tax wedge (% of total labour cost/revenue)
for four worker types as a function of total employer cost / OSVČ revenue:

  1. Zaměstnanec (employee)
  2. OSVČ – výdajový paušál 60 % (výdaje)
  3. OSVČ – výdajový paušál 80 % (výdaje)
  4. OSVČ – paušální daň pásmo 1

Legislative basis (stav k 1. 1. 2026):
  - ZDP §§ 2a, 6, 7, 7a (zákon č. 586/1992 Sb., ve znění pozdějších předpisů)
  - SP (sociální pojistné): zákon č. 589/1992 Sb.
  - ZP (zdravotní pojistné): zákon č. 592/1992 Sb.
  - Nařízení vlády č. 405/2025 Sb. – minimální mzda 2026
  - Zákon č. 270/2023 Sb. – reforma důchodů (přepočítací koef. OSVČ VZ)
  - Zákon č. 582/1991 Sb. – paušální daň § 38l an.

Parameters (2026):
  - MIN_WAGE        = 20 800 Kč/měsíc
  - AVG_WAGE        = 48 967 Kč/měsíc  (průměrná mzda pro 2026)
  - DPFO_RATE_LOW   = 15 %  (základ do 4× průměrné roční mzdy)
  - DPFO_RATE_HIGH  = 23 %  (základ nad 4× průměrné roční mzdy)
  - DPFO_THRESHOLD  = 4 × 48 967 × 12 = 2 350 416 Kč/rok
  - SLEVA_POPLATNIK = 30 840 Kč/rok = 2 570 Kč/měsíc
  - EMP_SP_EMPL     =  6.5 % hrubé mzdy (zaměstnanec)
  - EMP_SP_EMPR     = 24.8 % hrubé mzdy (zaměstnavatel)
  - EMP_ZP_EMPL     =  4.5 % hrubé mzdy (zaměstnanec)
  - EMP_ZP_EMPR     =  9.0 % hrubé mzdy (zaměstnavatel)
  - OSVC_SP_RATE    = 29.2 % vyměřovacího základu (SP OSVČ)
  - OSVC_ZP_RATE    = 13.5 % vyměřovacího základu (ZP OSVČ)
  - OSVC_SP_BASE    = 55 % daňového základu OSVČ  (§ 5b zák. 589/1992)
  - OSVC_ZP_BASE    = 50 % daňového základu OSVČ
  - OSVC_SP_MIN     = 5 720 Kč/měsíc (2026, min. záloha SP OSVČ)
  - OSVC_ZP_MIN     = 3 306 Kč/měsíc (2026, min. záloha ZP OSVČ)
  - PAUSALNI_DAN_1  = 7 498 Kč/měsíc (pásmo 1; příjmy do 1 000 000 Kč/rok)

Output
------
  pics/python/cz_tax_comparison.pdf
  latex/texparts/python/cz_tax_comparison.tex  ← \input{} this in main.tex

Run
---
    python analyses/cz_tax_comparison.py
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

# ── Legislative parameters 2026 ───────────────────────────────────────────────

# Mzdové limity (NV č. 405/2025 Sb., zákon č. 586/1992 Sb.)
MIN_WAGE: int = 20_800          # minimální mzda Kč/měsíc
AVG_WAGE: int = 48_967          # průměrná mzda pro výpočty 2026

# DPFO (zákon č. 586/1992 Sb., § 16)
DPFO_RATE_LOW: float  = 0.15    # sazba do prahu
DPFO_RATE_HIGH: float = 0.23    # sazba nad prahem
DPFO_THRESHOLD_ANNUAL: float = 4.0 * AVG_WAGE * 12   # 4× průměrná roční mzda
SLEVA_POPLATNIK_ANNUAL: float = 30_840.0  # sleva na poplatníka Kč/rok

# Zaměstnanec – sazby pojistného
EMP_SP_EMPLOYEE: float = 0.065   # SP zaměstnanec
EMP_SP_EMPLOYER: float = 0.248   # SP zaměstnavatel
EMP_ZP_EMPLOYEE: float = 0.045   # ZP zaměstnanec
EMP_ZP_EMPLOYER: float = 0.090   # ZP zaměstnavatel
# Celkový náklad zaměstnavatele = hrubá mzda × (1 + SP_empr + ZP_empr)
EMP_TOTAL_COST_FACTOR: float = 1.0 + EMP_SP_EMPLOYER + EMP_ZP_EMPLOYER  # = 1.338

# OSVČ – sazby a základy (zákon č. 589/1992 Sb., zákon č. 592/1992 Sb.)
OSVC_SP_RATE: float = 0.292      # SP OSVČ (29,2 % VZ)
OSVC_ZP_RATE: float = 0.135      # ZP OSVČ (13,5 % VZ)
OSVC_SP_BASE_RATIO: float = 0.55 # VZ SP = 55 % daňového základu (§ 5b z. 589/1992)
OSVC_ZP_BASE_RATIO: float = 0.50 # VZ ZP = 50 % daňového základu
OSVC_SP_MIN: float = 5_720.0     # minimální záloha SP Kč/měsíc (2026)
OSVC_ZP_MIN: float = 3_306.0     # minimální záloha ZP Kč/měsíc (2026)

# Paušální daň pásmo 1 (§ 38l ZDP, příjmy ≤ 1 000 000 Kč/rok)
PAUSALNI_DAN_1_MONTHLY: float = 7_498.0   # celková měsíční platba
PAUSALNI_DAN_1_REVENUE_CAP: float = 1_000_000.0 / 12  # max příjmy ≤ 83 333 Kč/měs

# Výdajové paušály (ZDP § 7(7))
EXPENSE_RATE_60: float = 0.60   # 60% výdajový paušál (obchod, služby, …)
EXPENSE_RATE_80: float = 0.80   # 80% výdajový paušál (řemeslníci, zemědělci, …)


# ── Tax computation functions ─────────────────────────────────────────────────

def _dpfo_annual(income_base_annual: float) -> float:
    """Compute roční daň z příjmu fyzických osob before slevy."""
    if income_base_annual <= DPFO_THRESHOLD_ANNUAL:
        return DPFO_RATE_LOW * income_base_annual
    return (
        DPFO_RATE_LOW * DPFO_THRESHOLD_ANNUAL
        + DPFO_RATE_HIGH * (income_base_annual - DPFO_THRESHOLD_ANNUAL)
    )


def net_income_employee(gross_monthly: float) -> float:
    """Čistý příjem zaměstnance (Kč/měsíc) ze superhrubé mzdy.

    Hrubá mzda → odečteme SP+ZP zaměstnance → základ DPFO = hrubá mzda
    → DPFO – sleva na poplatníka.
    Negativní DPFO (přeplatek) ignorujeme (záloha, nevracíme bonusy zde).
    """
    sp_employee = gross_monthly * EMP_SP_EMPLOYEE
    zp_employee = gross_monthly * EMP_ZP_EMPLOYEE
    # Základ daně = hrubá mzda (od 2021 superhrubá zrušena)
    dpfo_base_annual = gross_monthly * 12
    dpfo_annual = _dpfo_annual(dpfo_base_annual)
    dpfo_after_sleva_monthly = max(0.0, (dpfo_annual - SLEVA_POPLATNIK_ANNUAL) / 12)
    return gross_monthly - sp_employee - zp_employee - dpfo_after_sleva_monthly


def tax_wedge_employee(total_employer_cost: float) -> float:
    """Efektivní daňový klín zaměstnance v procentech.

    X-osa: celkový náklad zaměstnavatele = hrubá mzda × 1,338.
    """
    gross = total_employer_cost / EMP_TOTAL_COST_FACTOR
    net = net_income_employee(gross)
    return (total_employer_cost - net) / total_employer_cost * 100.0


def net_income_osvc_vydajovy(revenue_monthly: float, expense_rate: float) -> float:
    """Čistý příjem OSVČ s výdajovým paušálem (Kč/měsíc).

    Daňový základ = příjmy × (1 – expense_rate).
    SP a ZP se počítají z příslušných % daňového základu s minimem.
    """
    tax_base_monthly = revenue_monthly * (1.0 - expense_rate)
    tax_base_annual = tax_base_monthly * 12

    sp_monthly = max(OSVC_SP_MIN, OSVC_SP_RATE * OSVC_SP_BASE_RATIO * tax_base_monthly)
    zp_monthly = max(OSVC_ZP_MIN, OSVC_ZP_RATE * OSVC_ZP_BASE_RATIO * tax_base_monthly)

    dpfo_annual = _dpfo_annual(tax_base_annual)
    dpfo_after_sleva_monthly = max(0.0, (dpfo_annual - SLEVA_POPLATNIK_ANNUAL) / 12)

    return revenue_monthly - sp_monthly - zp_monthly - dpfo_after_sleva_monthly


def tax_wedge_osvc_vydajovy(revenue_monthly: float, expense_rate: float) -> float:
    """Efektivní daňový klín OSVČ s výdajovým paušálem v procentech.

    X-osa: příjmy OSVČ (= celkové náklady subjektu na jejich práci).
    """
    net = net_income_osvc_vydajovy(revenue_monthly, expense_rate)
    return (revenue_monthly - net) / revenue_monthly * 100.0


def net_income_osvc_pausalni(revenue_monthly: float) -> float:
    """Čistý příjem OSVČ v paušálním daňovém režimu (pásmo 1).

    Platí konstantní platbu 7 498 Kč/měsíc nehledě na výši příjmů
    (do stropu 83 333 Kč/měsíc = 1 000 000 Kč/rok).
    Nad stropem přechází do standardního výdajového paušálu 60 %.
    """
    if revenue_monthly <= PAUSALNI_DAN_1_REVENUE_CAP:
        return revenue_monthly - PAUSALNI_DAN_1_MONTHLY
    # Nad stropem: fallback na výdajový paušál 60 %
    return net_income_osvc_vydajovy(revenue_monthly, EXPENSE_RATE_60)


def tax_wedge_osvc_pausalni(revenue_monthly: float) -> float:
    """Efektivní daňový klín OSVČ v paušálním daňovém režimu v procentech."""
    net = net_income_osvc_pausalni(revenue_monthly)
    return (revenue_monthly - net) / revenue_monthly * 100.0


# ── Compute series ────────────────────────────────────────────────────────────

# X-axis: total employer cost / OSVČ revenue (Kč/month), same scale for all
# Employee: X = gross × EMP_TOTAL_COST_FACTOR; OSVČ: X = revenue
X_MIN: float = MIN_WAGE * EMP_TOTAL_COST_FACTOR   # ~27 830 Kč/měs (min. mzda zaměstnanec)
X_MAX: float = 300_000.0   # horní hranice pro zobrazení
N_POINTS: int = 500

x = np.linspace(X_MIN, X_MAX, N_POINTS)

wedge_emp = np.array([tax_wedge_employee(xi) for xi in x])
wedge_60  = np.array([tax_wedge_osvc_vydajovy(xi, EXPENSE_RATE_60) for xi in x])
wedge_80  = np.array([tax_wedge_osvc_vydajovy(xi, EXPENSE_RATE_80) for xi in x])
wedge_pau = np.array([tax_wedge_osvc_pausalni(xi) for xi in x])

# ── Reference marks ───────────────────────────────────────────────────────────

# Min wage total employer cost
x_minwage = MIN_WAGE * EMP_TOTAL_COST_FACTOR
# Average wage total employer cost
x_avgwage = AVG_WAGE * EMP_TOTAL_COST_FACTOR
# Paušální daň revenue cap
x_pausalni_cap = PAUSALNI_DAN_1_REVENUE_CAP

# ── Figure ────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=cm2in(15, 9))

COLORS = {
    "employee": PALETTE[0],   # deep blue
    "osvc_60":  PALETTE[1],   # teal
    "osvc_80":  PALETTE[4],   # vermillion
    "pausalni": PALETTE[2],   # rose/pink
}

ax.plot(x / 1_000, wedge_emp, color=COLORS["employee"],
        linewidth=2.0, label="Zaměstnanec")
ax.plot(x / 1_000, wedge_60, color=COLORS["osvc_60"],
        linewidth=1.8, label="OSVČ – paušál 60 % výdajů")
ax.plot(x / 1_000, wedge_80, color=COLORS["osvc_80"],
        linewidth=1.8, label="OSVČ – paušál 80 % výdajů")
ax.plot(x / 1_000, wedge_pau, color=COLORS["pausalni"],
        linewidth=1.8, linestyle="--", label="OSVČ – paušální daň (pásmo 1)")

# Vertical reference lines
for xv, label, ls in [
    (x_minwage, "Min. mzda", ":"),
    (x_avgwage, "Průměrná mzda", "--"),
]:
    ax.axvline(xv / 1_000, color="#888888", linewidth=0.8, linestyle=ls, zorder=1)
    ax.text(
        xv / 1_000 + 0.5, ax.get_ylim()[0] if ax.get_ylim()[0] > 0 else 5,
        label, rotation=90, fontsize=FONT_SIZE - 2, color="#666666",
        va="bottom",
    )

# Paušální cap marker
ax.axvline(x_pausalni_cap / 1_000, color=COLORS["pausalni"],
           linewidth=0.7, linestyle=":", alpha=0.6, zorder=1)
ax.text(x_pausalni_cap / 1_000 + 0.5, 35,
        "Strop\npásmo 1", fontsize=FONT_SIZE - 2, color=COLORS["pausalni"],
        va="bottom", rotation=90)

ax.set_xlabel("Celkový náklad zaměstnavatele / příjmy OSVČ (tis. Kč/měsíc)")
ax.set_ylabel("Efektivní daňový klín (%)")
ax.set_title("Efektivní zdanění: zaměstnanec vs. OSVČ (CZ, 2026)")
ax.xaxis.set_major_locator(ticker.MultipleLocator(25))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(5))
ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
ax.yaxis.set_minor_locator(ticker.MultipleLocator(1))
ax.grid(which="minor", axis="both", linewidth=0.2, alpha=0.4, color="#DDDDDD")
ax.set_xlim(X_MIN / 1_000, X_MAX / 1_000)
ax.set_ylim(0, 50)
ax.legend(loc="lower right", framealpha=0.9)

fig.tight_layout()

# ── Save ──────────────────────────────────────────────────────────────────────

savefig(fig, "cz_tax_comparison", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "cz_tax_comparison",
    caption=(
        "Efektivní daňový klín (podíl odvodů a daní na celkovém nákladu "
        r"zaměstnavatele / příjmech OSVČ) v závislosti na výši příjmu, CZ~2026. "
        "Výdajový paušál 80~\\% (řemeslníci, zemědělci) vykazuje výrazně nižší "
        "klín než zaměstnanec při totožných ekonomických výdajích. "
        "Zdroj: vlastní výpočet dle ZDP, NV~č.~405/2025~Sb."
    ),
    label="fig:cz_tax_comparison",
    width=r"0.95\linewidth",
)

print("Done.")
