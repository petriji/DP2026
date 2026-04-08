r"""
Czech pension model – analysis plots (CZ, 2026).

Generates three figures comparing pension outcomes and tax burden
for different worker types (zaměstnanec, OSVČ s výdajovými paušály).

Figures
-------
A – ``cz_pension_comparison``
    Absolute monthly pension as a function of lifetime average gross income.
    Shows: employee, OSVČ 60 %/80 %/40 % výdajový paušál.
    Highlights poverty threshold and minimum pension.

B – ``cz_replacement_rate``
    Náhradový poměr (pension / net income, %) as a function of gross income.
    Shows progressive compression of the replacement rate for high earners and
    the solidarity ceiling embedded in výpočtový základ.

C – ``cz_pension_sp_ratio``
    Return ratio: pension benefit vs. lifelong SP contributions.
    Shows how many months it takes to "recoup" SP contributions, parametrized
    by income level.

Legislative basis (stav k 1. 1. 2026):
  - Zákon č. 155/1995 Sb. (důchodové pojištění)
  - Zákon č. 270/2023 Sb. (reforma – accrual rate, první redukční hranice)
  - NV č. 365/2025 Sb. (parametry 2026)
  - NV č. 405/2025 Sb. (minimální mzda 2026)
  - ZDP § 7(7) – výdajové paušály OSVČ

Output
------
  pics/python/cz_pension_comparison.pdf
  pics/python/cz_replacement_rate.pdf
  pics/python/cz_pension_sp_ratio.pdf
  latex/texparts/python/cz_pension_comparison.tex
  latex/texparts/python/cz_replacement_rate.tex
  latex/texparts/python/cz_pension_sp_ratio.tex

Run
---
    python analyses/cz_pension_model.py
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

# ── Legislative parameters 2026 (NV č. 365/2025 Sb., NV č. 405/2025 Sb.) ─────

AVG_WAGE: int = 48_967         # průměrná mzda pro 2026 (Kč/měsíc)
MIN_WAGE: int = 20_800         # minimální mzda (NV č. 405/2025 Sb.)
MIN_PENSION: int = 5_340       # minimální důchod ≈ ZV + min. procentní výměra

# Redukční hranice výpočtového základu (§ 15 zák. 155/1995 Sb.)
RH1: int = 50_000              # 1. redukční hranice 2026 (Kč/měsíc)
RH2: int = 182_400             # 2. redukční hranice 2026 (Kč/měsíc)

# Základní výměra = 10 % průměrné mzdy (§ 33)
ZAKLADNI_VYMERA: int = 4_570   # Kč/měsíc (2026)

# Accrual rate: zákon č. 270/2023 Sb. – 1,495 % za rok pojištění (2026)
ACCRUAL_RATE: float = 0.01495

# Podíl výpočtového základu pod 1. RH: zákon č. 270/2023 Sb. – 99 % (2026)
FIRST_BRACKET_RATE: float = 0.99
# Podíl výpočtového základu mezi 1. a 2. RH: 26 %
SECOND_BRACKET_RATE: float = 0.26

# SP parametry
SP_EMPLOYEE_RATE: float = 0.065   # SP zaměstnanec
SP_EMPLOYER_RATE: float = 0.248   # SP zaměstnavatel
ZP_EMPLOYEE_RATE: float = 0.045   # ZP zaměstnanec
ZP_EMPLOYER_RATE: float = 0.090   # ZP zaměstnavatel
OSVC_SP_RATE: float = 0.292       # SP OSVČ
OSVC_SP_BASE_RATIO: float = 0.55  # VZ SP = 55 % daňového základu
OSVC_ZP_RATE: float = 0.135       # ZP OSVČ
OSVC_ZP_BASE_RATIO: float = 0.50  # VZ ZP = 50 % daňového základu
OSVC_SP_MIN: float = 5_720.0      # min. záloha SP OSVČ Kč/měs
OSVC_ZP_MIN: float = 3_306.0      # min. záloha ZP OSVČ Kč/měs

# DPFO parametry
DPFO_RATE_LOW: float = 0.15
DPFO_THRESHOLD_ANNUAL: float = 4.0 * AVG_WAGE * 12
SLEVA_POPLATNIK_ANNUAL: float = 30_840.0

# Referenční data
MEDIAN_EMP_WAGE: float = 40_709.0  # ISPV 2024 H2 medián hrubé mzdy (Kč/měs)
POVERTY_THRESHOLD: float = 18_600.0   # hranice chudoby 2025 (Kč/měsíc)

# Výdajové paušály OSVČ
EXPENSE_RATE_60: float = 0.60
EXPENSE_RATE_80: float = 0.80
EXPENSE_RATE_40: float = 0.40

# Stropy výdajových paušálů (ZDP § 7(7) – max. základ daně v Kč/rok)
OSVC_VYDAJOVY_CAP: dict[float, int] = {
    0.80: 133_333,  # 80 % výdaje: příjmy ≤ 2 000 000 Kč/rok → základ max 400 000/12
    0.60: 100_000,  # 60 % výdaje: příjmy ≤ 2 000 000 Kč/rok → základ max 1 200 000/12
    0.40:  66_667,  # 40 % výdaje: základ max 800 000 Kč/rok
}

# Předpokládané roky pojištění pro výpočet důchodu
YEARS_OF_INSURANCE: int = 40

# OSVČ typy pro grafy: (expense_rate, label, color, linewidth_multiplier)
OSVC_TYPES: list[tuple[float, str, str, float]] = [
    (EXPENSE_RATE_60, "OSVČ – 60 % výdaje", PALETTE[1], 1.8),
    (EXPENSE_RATE_80, "OSVČ – 80 % výdaje", PALETTE[4], 1.8),
    (EXPENSE_RATE_40, "OSVČ – 40 % výdaje", PALETTE[5], 1.4),
]


# ── Pension calculation functions ─────────────────────────────────────────────

def _vypoctovy_zaklad(ovz_monthly: float) -> float:
    """Výpočtový základ ze OVZ (§ 15 zák. 155/1995 Sb.)."""
    if ovz_monthly <= RH1:
        return ovz_monthly * FIRST_BRACKET_RATE
    if ovz_monthly <= RH2:
        return RH1 * FIRST_BRACKET_RATE + (ovz_monthly - RH1) * SECOND_BRACKET_RATE
    return RH1 * FIRST_BRACKET_RATE + (RH2 - RH1) * SECOND_BRACKET_RATE


def pension_employee(gross_monthly: float) -> float:
    """Měsíční starobní důchod zaměstnance (Kč/měsíc).

    Zjednodušený model: konstantní hrubá mzda po celou kariéru,
    OVZ ≈ hrubá mzda (viz pension_model.py pro přesný výpočet).
    """
    vz = _vypoctovy_zaklad(gross_monthly)
    procentni = ACCRUAL_RATE * vz * YEARS_OF_INSURANCE
    total = ZAKLADNI_VYMERA + procentni
    return max(total, float(MIN_PENSION))


def pension_osvc_vydajovy(revenue_monthly: float, expense_rate: float) -> float:
    """Měsíční starobní důchod OSVČ s výdajovým paušálem (Kč/měsíc).

    SP vyměřovací základ OSVČ = 55 % × daňový základ.
    Daňový základ = příjmy × (1 – expense_rate) s odpovídajícím stropem.
    Nad stropem se základ fixuje.
    """
    cap_monthly = OSVC_VYDAJOVY_CAP.get(expense_rate, 200_000)
    tax_base = min(revenue_monthly * (1.0 - expense_rate), cap_monthly)
    sp_base = OSVC_SP_BASE_RATIO * tax_base
    # OVZ ≈ SP vyměřovací základ (hrubý proxy)
    vz = _vypoctovy_zaklad(sp_base)
    procentni = ACCRUAL_RATE * vz * YEARS_OF_INSURANCE
    total = ZAKLADNI_VYMERA + procentni
    return max(total, float(MIN_PENSION))


# ── Net income functions ──────────────────────────────────────────────────────

def _dpfo_annual(income_base_annual: float) -> float:
    """Roční daň z příjmu fyzických osob before slevy."""
    if income_base_annual <= DPFO_THRESHOLD_ANNUAL:
        return DPFO_RATE_LOW * income_base_annual
    return (
        DPFO_RATE_LOW * DPFO_THRESHOLD_ANNUAL
        + 0.23 * (income_base_annual - DPFO_THRESHOLD_ANNUAL)
    )


def _net_income_emp(gross_monthly: float) -> float:
    """Čistý příjem zaměstnance (Kč/měsíc)."""
    sp = gross_monthly * SP_EMPLOYEE_RATE
    zp = gross_monthly * ZP_EMPLOYEE_RATE
    dpfo_monthly = max(0.0, (_dpfo_annual(gross_monthly * 12) - SLEVA_POPLATNIK_ANNUAL) / 12)
    return gross_monthly - sp - zp - dpfo_monthly


def _net_income_osvc_vydajovy(revenue_monthly: float, expense_rate: float) -> float:
    """Čistý příjem OSVČ s výdajovým paušálem (Kč/měsíc)."""
    cap_monthly = OSVC_VYDAJOVY_CAP.get(expense_rate, 200_000)
    tax_base = min(revenue_monthly * (1.0 - expense_rate), cap_monthly)
    sp = max(OSVC_SP_MIN, OSVC_SP_RATE * OSVC_SP_BASE_RATIO * tax_base)
    zp = max(OSVC_ZP_MIN, OSVC_ZP_RATE * OSVC_ZP_BASE_RATIO * tax_base)
    dpfo_monthly = max(0.0, (_dpfo_annual(tax_base * 12) - SLEVA_POPLATNIK_ANNUAL) / 12)
    return revenue_monthly - sp - zp - dpfo_monthly


# ── Compute series ────────────────────────────────────────────────────────────

X_MIN: float = MIN_WAGE
X_MAX: float = 200_000.0
N_POINTS: int = 500

x = np.linspace(X_MIN, X_MAX, N_POINTS)

# Pensions
pens_emp = np.array([pension_employee(xi) for xi in x])
pens_osvc = {
    er: np.array([pension_osvc_vydajovy(xi, er) for xi in x])
    for er, *_ in OSVC_TYPES
}

# Net incomes
net_emp = np.array([_net_income_emp(xi) for xi in x])
net_osvc = {
    er: np.array([_net_income_osvc_vydajovy(xi, er) for xi in x])
    for er, *_ in OSVC_TYPES
}

# Replacement rates (pension / net_income)
rr_emp = pens_emp / net_emp * 100.0
rr_osvc = {er: pens_osvc[er] / net_osvc[er] * 100.0 for er, *_ in OSVC_TYPES}

# SP contributions (employee side: SP+ZP employee; OSVČ: SP+ZP)
sp_emp_monthly = x * (SP_EMPLOYEE_RATE + ZP_EMPLOYEE_RATE)
sp_osvc_monthly = {
    er: np.maximum(OSVC_SP_MIN + OSVC_ZP_MIN,
                   OSVC_SP_RATE * OSVC_SP_BASE_RATIO * np.minimum(x * (1 - er),
                                                                    OSVC_VYDAJOVY_CAP.get(er, 200_000))
                   + OSVC_ZP_RATE * OSVC_ZP_BASE_RATIO * np.minimum(x * (1 - er),
                                                                      OSVC_VYDAJOVY_CAP.get(er, 200_000)))
    for er, *_ in OSVC_TYPES
}


# ── Figure A: Pension by income ───────────────────────────────────────────────

def plot_pension_comparison() -> plt.Figure:
    """Měsíční důchod jako funkce hrubého příjmu/příjmů OSVČ."""
    fig, ax = plt.subplots(figsize=cm2in(15, 9))

    ax.plot(x / 1_000, pens_emp / 1_000, color=PALETTE[0], linewidth=2.2,
            label="Zaměstnanec")
    for er, label, color, lw in OSVC_TYPES:
        data = pens_osvc[er]
        cap = OSVC_VYDAJOVY_CAP.get(er, 200_000)
        x_below = x[x <= cap]
        x_above = x[x > cap]
        d_below = data[x <= cap]
        d_above = data[x > cap]
        ax.plot(x_below / 1_000, d_below / 1_000, color=color, linewidth=lw,
                label=label)
        if len(x_above) > 0:
            ax.plot(x_above / 1_000, d_above / 1_000, color=color, linewidth=lw * 0.7,
                    alpha=0.45, linestyle="-.")

    # Reference lines
    ax.axhline(POVERTY_THRESHOLD / 1_000, color="#aa0000", linewidth=0.8,
               linestyle=":", zorder=1)
    ax.text(X_MAX / 1_000 * 0.98, POVERTY_THRESHOLD / 1_000 + 0.3,
            "Hranice chudoby", ha="right", fontsize=FONT_SIZE - 2, color="#aa0000")
    ax.axvline(MIN_WAGE / 1_000, color="#888888", linewidth=0.7, linestyle=":")
    ax.axvline(AVG_WAGE / 1_000, color="#888888", linewidth=0.7, linestyle="--")
    ax.text(AVG_WAGE / 1_000 + 0.5, 5, "Prům. mzda", rotation=90,
            fontsize=FONT_SIZE - 2, color="#666666", va="bottom")

    ax.set_xlabel("Hrubý příjem / příjmy OSVČ (tis. Kč/měsíc)")
    ax.set_ylabel("Měsíční důchod (tis. Kč/měsíc)")
    ax.set_title("Výše starobního důchodu dle příjmu (CZ, 2026, 40 let pojištění)")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(25))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.set_xlim(X_MIN / 1_000, X_MAX / 1_000)
    ax.set_ylim(0, None)
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig


# ── Figure B: Replacement rate by income ─────────────────────────────────────

def plot_replacement_rate() -> plt.Figure:
    """Náhradový poměr (důchod / čistý příjem) jako funkce příjmu."""
    fig, ax = plt.subplots(figsize=cm2in(15, 9))

    ax.plot(x / 1_000, rr_emp, color=PALETTE[0], linewidth=2.2,
            label="Zaměstnanec")
    for er, label, color, lw in OSVC_TYPES:
        data = rr_osvc[er]
        cap = OSVC_VYDAJOVY_CAP.get(er, 200_000)
        x_below = x[x <= cap]
        x_above = x[x > cap]
        ax.plot(x_below / 1_000, data[x <= cap], color=color,
                linewidth=lw, label=label)
        if len(x_above) > 0:
            ax.plot(x_above / 1_000, data[x > cap], color=color,
                    linewidth=lw * 0.7, alpha=0.45, linestyle="-.")

    ax.axhline(100.0, color="#888888", linewidth=0.6, linestyle=":", zorder=1)
    ax.axvline(MIN_WAGE / 1_000, color="#888888", linewidth=0.7, linestyle=":")
    ax.axvline(AVG_WAGE / 1_000, color="#888888", linewidth=0.7, linestyle="--")
    ax.text(AVG_WAGE / 1_000 + 0.5, 5, "Prům. mzda", rotation=90,
            fontsize=FONT_SIZE - 2, color="#666666", va="bottom")

    ax.set_xlabel("Hrubý příjem / příjmy OSVČ (tis. Kč/měsíc)")
    ax.set_ylabel("Náhradový poměr (%)")
    ax.set_title("Náhradový poměr důchodu (CZ, 2026, 40 let pojištění)")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(25))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.set_xlim(X_MIN / 1_000, X_MAX / 1_000)
    ax.set_ylim(0, 120)
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


# ── Figure C: SP contributions vs. pension (return ratio) ────────────────────

def plot_pension_sp_ratio() -> plt.Figure:
    """Kolik měsíců trvá, než důchod vyrovná celoživotní platby SP.

    Simplified: total SP paid over YEARS_OF_INSURANCE × 12 months
    ÷ monthly pension = break-even months.
    """
    # Total SP contributions over career (employee side for employee;
    # OSVČ own contributions for OSVČ)
    total_sp_emp = sp_emp_monthly * YEARS_OF_INSURANCE * 12
    breakeven_emp = total_sp_emp / pens_emp  # months to break even

    fig, ax = plt.subplots(figsize=cm2in(15, 9))

    ax.plot(x / 1_000, breakeven_emp, color=PALETTE[0], linewidth=2.2,
            label="Zaměstnanec (SP+ZP zaměstnanec)")

    for er, label, color, lw in OSVC_TYPES:
        total_sp_osvc = sp_osvc_monthly[er] * YEARS_OF_INSURANCE * 12
        breakeven_osvc = total_sp_osvc / pens_osvc[er]
        cap = OSVC_VYDAJOVY_CAP.get(er, 200_000)
        x_below = x[x <= cap]
        x_above = x[x > cap]
        ax.plot(x_below / 1_000, breakeven_osvc[x <= cap], color=color,
                linewidth=lw, label=label)
        if len(x_above) > 0:
            ax.plot(x_above / 1_000, breakeven_osvc[x > cap], color=color,
                    linewidth=lw * 0.7, alpha=0.45, linestyle="-.")

    # Reference: Czech life expectancy at 65 ≈ 18 years → 216 months
    life_expectancy_months = 216
    ax.axhline(life_expectancy_months, color="#aa0000", linewidth=0.8,
               linestyle=":", zorder=1)
    ax.text(X_MAX / 1_000 * 0.98, life_expectancy_months + 3,
            "Střední délka dožití při odchodu do důchodu\n(65 let, CZ ≈ 18 let)",
            ha="right", fontsize=FONT_SIZE - 2, color="#aa0000")
    ax.axvline(AVG_WAGE / 1_000, color="#888888", linewidth=0.7, linestyle="--")
    ax.text(AVG_WAGE / 1_000 + 0.5, 30, "Prům. mzda", rotation=90,
            fontsize=FONT_SIZE - 2, color="#666666", va="bottom")

    ax.set_xlabel("Hrubý příjem / příjmy OSVČ (tis. Kč/měsíc)")
    ax.set_ylabel("Počet měsíců důchodu k vyrovnání SP příspěvků")
    ax.set_title("Návratnost SP příspěvků (CZ, 2026, 40 let pojištění)")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(25))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(24))
    ax.set_xlim(X_MIN / 1_000, X_MAX / 1_000)
    ax.set_ylim(0, None)
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


# ── Generate and save all figures ─────────────────────────────────────────────

print("Generating pension model figures…")

fig_a = plot_pension_comparison()
savefig(fig_a, "cz_pension_comparison", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "cz_pension_comparison",
    caption=(
        "Výše měsíčního starobního důchodu v závislosti na výši příjmu pro "
        "zaměstnance a OSVČ s výdajovými paušály (CZ, 2026, 40~let~pojištění). "
        "Nad stropem výdajového paušálu (tečkovaná část křivky) se základ daně "
        "fixuje, čímž přestává růst i důchod OSVČ. "
        "Zdroj: vlastní výpočet dle zák.~č.~155/1995~Sb.,"
        " zák.~č.~270/2023~Sb., NV~č.~365/2025~Sb."
    ),
    label="fig:cz_pension_comparison",
    width=r"0.95\linewidth",
)

fig_b = plot_replacement_rate()
savefig(fig_b, "cz_replacement_rate", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "cz_replacement_rate",
    caption=(
        "Náhradový poměr (důchod jako \\% čistého příjmu) v závislosti na výši příjmu "
        "(CZ, 2026, 40~let~pojištění). "
        "OSVČ s vysokými paušálními výdaji vykazují nízký základ pro výpočet důchodu, "
        "a tedy nízký náhradový poměr přes vysoký čistý příjem. "
        "Zdroj: vlastní výpočet."
    ),
    label="fig:cz_replacement_rate",
    width=r"0.95\linewidth",
)

fig_c = plot_pension_sp_ratio()
savefig(fig_c, "cz_pension_sp_ratio", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "cz_pension_sp_ratio",
    caption=(
        "Počet měsíců čerpání důchodu potřebný k navrácení celoživotních plateb SP "
        "(zaměstnanec i OSVČ, vlastní část pojistného, CZ, 2026, 40~let pojištění). "
        "Přerušovaná červená linie odpovídá střední délce dožití při odchodu do důchodu "
        "v~65~letech (CZ, cca 18~let = 216~měsíců). "
        "Zdroj: vlastní výpočet."
    ),
    label="fig:cz_pension_sp_ratio",
    width=r"0.95\linewidth",
)

print("Done.")
