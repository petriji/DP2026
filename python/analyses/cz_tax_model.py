r"""
Czech tax model – analysis plots (CZ, 2026).

Generates figures comparing tax burden, net income, and social insurance
for different worker types (zaměstnanec, OSVČ výdajové paušály, paušální daň).

Figures
-------
A – ``cz_tax_wedge_vs_income``
    Efektivní daňový klín (%) jako funkce hrubého příjmu / příjmů OSVČ.
    Zaměstnanec + OSVČ 60 %/80 %/40 % výdaje + paušální daň pásmo 1.

B – ``cz_net_income_vs_income``
    Čistý příjem (Kč/měs.) jako funkce hrubého příjmu / příjmů OSVČ.

C – ``cz_sp_vs_income``
    Efektivní sazba SP (zaměstnanec i OSVČ, vlastní část) jako % hrubého příjmu.

D – ``cz_tax_breakdown``
    Waterfall / stacked bar showing daňové složky při průměrné mzdě a 2× průměrná.

Legislative basis (stav k 1. 1. 2026):
  - ZDP § 2a, 6, 7, 7a, 38l (zákon č. 586/1992 Sb.)
  - SP: zákon č. 589/1992 Sb.
  - ZP: zákon č. 592/1992 Sb.
  - NV č. 405/2025 Sb. – minimální mzda 2026
  - Zákon č. 270/2023 Sb. – OSVČ SP base ratio

Output
------
  pics/python/cz_tax_wedge_vs_income.pdf
  pics/python/cz_net_income_vs_income.pdf
  pics/python/cz_sp_vs_income.pdf
  pics/python/cz_tax_breakdown.pdf
  latex/texparts/python/cz_tax_wedge_vs_income.tex
  latex/texparts/python/cz_net_income_vs_income.tex
  latex/texparts/python/cz_sp_vs_income.tex
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

# ── Legislative parameters 2026 ───────────────────────────────────────────────

MIN_WAGE: int = 20_800
AVG_WAGE: int = 48_967
POVERTY_THRESHOLD: float = 18_600.0    # hranice chudoby 2025 (Kč/měsíc)

# DPFO (zákon č. 586/1992 Sb., § 16)
DPFO_RATE_LOW: float  = 0.15
DPFO_RATE_HIGH: float = 0.23
DPFO_THRESHOLD_ANNUAL: float = 4.0 * AVG_WAGE * 12
SLEVA_POPLATNIK_ANNUAL: float = 30_840.0

# Zaměstnanec
EMP_SP_EMPLOYEE: float = 0.065
EMP_SP_EMPLOYER: float = 0.248
EMP_ZP_EMPLOYEE: float = 0.045
EMP_ZP_EMPLOYER: float = 0.090
EMP_TOTAL_COST_FACTOR: float = 1.0 + EMP_SP_EMPLOYER + EMP_ZP_EMPLOYER  # 1.338

# OSVČ
OSVC_SP_RATE: float = 0.292
OSVC_ZP_RATE: float = 0.135
OSVC_SP_BASE_RATIO: float = 0.55
OSVC_ZP_BASE_RATIO: float = 0.50
OSVC_SP_MIN: float = 5_720.0
OSVC_ZP_MIN: float = 3_306.0

# Paušální daň pásmo 1
PAUSALNI_DAN_1_MONTHLY: float = 7_498.0
PAUSALNI_DAN_1_REVENUE_CAP: float = 1_000_000.0 / 12

# Výdajové paušály
EXPENSE_RATE_60: float = 0.60
EXPENSE_RATE_80: float = 0.80
EXPENSE_RATE_40: float = 0.40

# OSVČ výdajový strop (max daňový základ Kč/měsíc)
OSVC_VYDAJOVY_CAP: dict[float, float] = {
    0.80: 133_333.0,
    0.60: 100_000.0,
    0.40:  66_667.0,
}

# Referenční bod (ISPV 2024 H2 medián)
MEDIAN_EMP_WAGE: float = 40_709.0

# OSVČ typy: (expense_rate, label, color, linewidth)
OSVC_TYPES: list[tuple[float, str, str, float]] = [
    (EXPENSE_RATE_60, "OSVČ – 60 % výdaje",  PALETTE[1], 1.8),
    (EXPENSE_RATE_80, "OSVČ – 80 % výdaje",  PALETTE[4], 1.8),
    (EXPENSE_RATE_40, "OSVČ – 40 % výdaje",  PALETTE[5], 1.4),
]


# ── Tax computation ───────────────────────────────────────────────────────────

def _dpfo_annual(income_base_annual: float) -> float:
    if income_base_annual <= DPFO_THRESHOLD_ANNUAL:
        return DPFO_RATE_LOW * income_base_annual
    return (
        DPFO_RATE_LOW * DPFO_THRESHOLD_ANNUAL
        + DPFO_RATE_HIGH * (income_base_annual - DPFO_THRESHOLD_ANNUAL)
    )


def sp_employee(gross_monthly: float) -> float:
    """Celkové SP+ZP za zaměstnance = zaměstnanec + zaměstnavatel (Kč/měsíc)."""
    return gross_monthly * (EMP_SP_EMPLOYEE + EMP_ZP_EMPLOYEE
                            + EMP_SP_EMPLOYER + EMP_ZP_EMPLOYER)


def sp_employee_own(gross_monthly: float) -> float:
    """SP+ZP zaměstnanec vlastní část (Kč/měsíc)."""
    return gross_monthly * (EMP_SP_EMPLOYEE + EMP_ZP_EMPLOYEE)


def sp_osvc_vydajovy(revenue_monthly: float, expense_rate: float) -> float:
    """Celkové SP+ZP OSVČ s výdajovým paušálem (Kč/měsíc)."""
    cap = OSVC_VYDAJOVY_CAP.get(expense_rate, 200_000.0)
    tax_base = min(revenue_monthly * (1.0 - expense_rate), cap)
    sp = max(OSVC_SP_MIN, OSVC_SP_RATE * OSVC_SP_BASE_RATIO * tax_base)
    zp = max(OSVC_ZP_MIN, OSVC_ZP_RATE * OSVC_ZP_BASE_RATIO * tax_base)
    return sp + zp


def net_income_employee(gross_monthly: float) -> float:
    """Čistý příjem zaměstnance (Kč/měsíc)."""
    sp_own = gross_monthly * (EMP_SP_EMPLOYEE + EMP_ZP_EMPLOYEE)
    dpfo_monthly = max(0.0, (_dpfo_annual(gross_monthly * 12) - SLEVA_POPLATNIK_ANNUAL) / 12)
    return gross_monthly - sp_own - dpfo_monthly


def net_income_osvc_vydajovy(revenue_monthly: float, expense_rate: float) -> float:
    """Čistý příjem OSVČ s výdajovým paušálem (Kč/měsíc)."""
    cap = OSVC_VYDAJOVY_CAP.get(expense_rate, 200_000.0)
    tax_base = min(revenue_monthly * (1.0 - expense_rate), cap)
    sp = max(OSVC_SP_MIN, OSVC_SP_RATE * OSVC_SP_BASE_RATIO * tax_base)
    zp = max(OSVC_ZP_MIN, OSVC_ZP_RATE * OSVC_ZP_BASE_RATIO * tax_base)
    dpfo_monthly = max(0.0, (_dpfo_annual(tax_base * 12) - SLEVA_POPLATNIK_ANNUAL) / 12)
    return revenue_monthly - sp - zp - dpfo_monthly


def net_income_osvc_pausalni(revenue_monthly: float) -> float:
    """Čistý příjem OSVČ – paušální daň pásmo 1 (Kč/měsíc)."""
    if revenue_monthly <= PAUSALNI_DAN_1_REVENUE_CAP:
        return revenue_monthly - PAUSALNI_DAN_1_MONTHLY
    return net_income_osvc_vydajovy(revenue_monthly, EXPENSE_RATE_60)


def tax_wedge_employee(gross_monthly: float) -> float:
    """Efektivní daňový klín zaměstnance (%) – báze: celkový náklad zaměstnavatele."""
    total_cost = gross_monthly * EMP_TOTAL_COST_FACTOR
    net = net_income_employee(gross_monthly)
    return (total_cost - net) / total_cost * 100.0


def tax_wedge_osvc_vydajovy(revenue_monthly: float, expense_rate: float) -> float:
    """Efektivní daňový klín OSVČ s výdajovým paušálem (%) – báze: příjmy."""
    net = net_income_osvc_vydajovy(revenue_monthly, expense_rate)
    return (revenue_monthly - net) / revenue_monthly * 100.0


def tax_wedge_osvc_pausalni(revenue_monthly: float) -> float:
    """Efektivní daňový klín OSVČ – paušální daň pásmo 1 (%) – báze: příjmy."""
    net = net_income_osvc_pausalni(revenue_monthly)
    return (revenue_monthly - net) / revenue_monthly * 100.0


def tax_breakdown(
    income_monthly: float,
    mode: str = "employee",
    expense_rate: float = EXPENSE_RATE_60,
    pausalni: bool = False,
) -> dict[str, float]:
    """Itemized tax breakdown (Kč/month) for a given income and mode.

    Parameters
    ----------
    income_monthly:
        Gross monthly income / OSVČ revenue.
    mode:
        ``"employee"`` or ``"osvc"``.
    expense_rate:
        OSVČ expense rate (used when mode="osvc" and not pausalni).
    pausalni:
        When True and mode="osvc", use paušální daň pásmo 1.

    Returns
    -------
    dict with keys: sp_own, zp_own, dpfo, net, total_cost, wedge_pct
    """
    if mode == "employee":
        sp_own = income_monthly * EMP_SP_EMPLOYEE
        zp_own = income_monthly * EMP_ZP_EMPLOYEE
        sp_empr = income_monthly * EMP_SP_EMPLOYER
        zp_empr = income_monthly * EMP_ZP_EMPLOYER
        dpfo = max(0.0, (_dpfo_annual(income_monthly * 12) - SLEVA_POPLATNIK_ANNUAL) / 12)
        net = income_monthly - sp_own - zp_own - dpfo
        total_cost = income_monthly * EMP_TOTAL_COST_FACTOR
        return dict(
            gross=income_monthly,
            sp_employee=sp_own,
            zp_employee=zp_own,
            sp_employer=sp_empr,
            zp_employer=zp_empr,
            dpfo=dpfo,
            net=net,
            total_cost=total_cost,
            wedge_pct=(total_cost - net) / total_cost * 100.0,
        )
    # OSVČ
    if pausalni and income_monthly <= PAUSALNI_DAN_1_REVENUE_CAP:
        net = net_income_osvc_pausalni(income_monthly)
        return dict(
            gross=income_monthly,
            sp_employee=None,
            zp_employee=None,
            sp_employer=None,
            zp_employer=None,
            pausalni_platba=PAUSALNI_DAN_1_MONTHLY,
            dpfo=None,
            net=net,
            total_cost=income_monthly,
            wedge_pct=(income_monthly - net) / income_monthly * 100.0,
        )
    cap = OSVC_VYDAJOVY_CAP.get(expense_rate, 200_000.0)
    tax_base = min(income_monthly * (1.0 - expense_rate), cap)
    sp = max(OSVC_SP_MIN, OSVC_SP_RATE * OSVC_SP_BASE_RATIO * tax_base)
    zp = max(OSVC_ZP_MIN, OSVC_ZP_RATE * OSVC_ZP_BASE_RATIO * tax_base)
    dpfo = max(0.0, (_dpfo_annual(tax_base * 12) - SLEVA_POPLATNIK_ANNUAL) / 12)
    net = income_monthly - sp - zp - dpfo
    return dict(
        gross=income_monthly,
        tax_base=tax_base,
        sp_osvc=sp,
        zp_osvc=zp,
        dpfo=dpfo,
        net=net,
        total_cost=income_monthly,
        wedge_pct=(income_monthly - net) / income_monthly * 100.0,
    )


# ── Compute series ────────────────────────────────────────────────────────────

X_MIN = float(MIN_WAGE)
X_MAX = 300_000.0
N_POINTS = 500
x = np.linspace(X_MIN, X_MAX, N_POINTS)

wedge_emp  = np.array([tax_wedge_employee(xi) for xi in x])
net_emp    = np.array([net_income_employee(xi) for xi in x])
sp_emp_pct = np.array([sp_employee_own(xi) / xi * 100.0 for xi in x])

wedge_osvc: dict[float, np.ndarray] = {}
net_osvc:   dict[float, np.ndarray] = {}
sp_osvc_pct: dict[float, np.ndarray] = {}
for er, *_ in OSVC_TYPES:
    wedge_osvc[er]   = np.array([tax_wedge_osvc_vydajovy(xi, er) for xi in x])
    net_osvc[er]     = np.array([net_income_osvc_vydajovy(xi, er) for xi in x])
    sp_osvc_pct[er]  = np.array([
        sp_osvc_vydajovy(xi, er) / xi * 100.0 for xi in x
    ])
wedge_pau = np.array([tax_wedge_osvc_pausalni(xi) for xi in x])
net_pau   = np.array([net_income_osvc_pausalni(xi) for xi in x])

# ── Helper: draw reference vlines ─────────────────────────────────────────────

def _vlines(ax: plt.Axes, y_label_pos: float = 5.0) -> None:
    ax.axvline(MIN_WAGE / 1_000, color="#888888", linewidth=0.7, linestyle=":")
    ax.axvline(AVG_WAGE / 1_000, color="#888888", linewidth=0.7, linestyle="--")
    ax.text(AVG_WAGE / 1_000 + 0.5, y_label_pos, "Prům. mzda",
            rotation=90, fontsize=FONT_SIZE - 2, color="#666666", va="bottom")
    # Median dot on employee line (for reference)
    ax.axvline(MEDIAN_EMP_WAGE / 1_000, color="#CCCCCC", linewidth=0.6,
               linestyle=":", zorder=0)


# ── Figure A: Tax wedge vs. income ────────────────────────────────────────────

def plot_tax_wedge_vs_income() -> plt.Figure:
    """Daňový klín jako funkce příjmu."""
    fig, ax = plt.subplots(figsize=cm2in(15, 9))

    ax.plot(x / 1_000, wedge_emp, color=PALETTE[0], linewidth=2.2,
            label="Zaměstnanec (náklad zaměstnavatele)")
    for er, label, color, lw in OSVC_TYPES:
        ax.plot(x / 1_000, wedge_osvc[er], color=color, linewidth=lw, label=label)
    ax.plot(x / 1_000, wedge_pau, color=PALETTE[2], linewidth=1.8,
            linestyle="--", label="OSVČ – paušální daň (pásmo 1)")

    _vlines(ax, y_label_pos=5.0)
    ax.set_xlabel("Hrubý příjem / příjmy OSVČ (tis. Kč/měsíc)")
    ax.set_ylabel("Efektivní daňový klín (%)")
    ax.set_title("Efektivní daňový klín dle příjmu (CZ, 2026)")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(25))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.set_xlim(X_MIN / 1_000, X_MAX / 1_000)
    ax.set_ylim(0, 55)
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig


# ── Figure B: Net income vs. income ──────────────────────────────────────────

def plot_net_income_vs_income() -> plt.Figure:
    """Čistý příjem jako funkce hrubého příjmu / příjmů OSVČ."""
    fig, ax = plt.subplots(figsize=cm2in(15, 9))

    ax.plot(x / 1_000, net_emp / 1_000, color=PALETTE[0], linewidth=2.2,
            label="Zaměstnanec")
    for er, label, color, lw in OSVC_TYPES:
        ax.plot(x / 1_000, net_osvc[er] / 1_000, color=color,
                linewidth=lw, label=label)
    ax.plot(x / 1_000, net_pau / 1_000, color=PALETTE[2], linewidth=1.8,
            linestyle="--", label="OSVČ – paušální daň (pásmo 1)")

    # 45° reference line (no tax)
    ax.plot(x / 1_000, x / 1_000, color="#CCCCCC", linewidth=0.7,
            linestyle=":", label="100 % (bez odvodů)")

    # Poverty threshold
    ax.axhline(POVERTY_THRESHOLD / 1_000, color="#aa0000", linewidth=0.8,
               linestyle=":")
    ax.text(X_MAX / 1_000 * 0.98, POVERTY_THRESHOLD / 1_000 + 0.3,
            "Hranice chudoby", ha="right", fontsize=FONT_SIZE - 2, color="#aa0000")

    _vlines(ax, y_label_pos=2.0)
    ax.set_xlabel("Hrubý příjem / příjmy OSVČ (tis. Kč/měsíc)")
    ax.set_ylabel("Čistý příjem (tis. Kč/měsíc)")
    ax.set_title("Čistý příjem dle hrubého příjmu / příjmů OSVČ (CZ, 2026)")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(25))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(25))
    ax.set_xlim(X_MIN / 1_000, X_MAX / 1_000)
    ax.set_ylim(0, None)
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig


# ── Figure C: SP effective rate ───────────────────────────────────────────────

def plot_sp_vs_income() -> plt.Figure:
    """Efektivní sazba SP (vlastní část) jako % příjmu."""
    fig, ax = plt.subplots(figsize=cm2in(15, 9))

    ax.plot(x / 1_000, sp_emp_pct, color=PALETTE[0], linewidth=2.2,
            label="Zaměstnanec (SP+ZP vlastní část, 11 %)")
    for er, label, color, lw in OSVC_TYPES:
        ax.plot(x / 1_000, sp_osvc_pct[er], color=color, linewidth=lw, label=label)

    _vlines(ax, y_label_pos=2.0)
    ax.set_xlabel("Hrubý příjem / příjmy OSVČ (tis. Kč/měsíc)")
    ax.set_ylabel("Efektivní sazba SP+ZP (vlastní část, % příjmu)")
    ax.set_title("Efektivní sazba sociálního a zdravotního pojistného (CZ, 2026)")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(25))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.set_xlim(X_MIN / 1_000, X_MAX / 1_000)
    ax.set_ylim(0, 20)
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


# ── Figure D: Stacked bar – tax breakdown at reference incomes ────────────────

def plot_tax_breakdown() -> plt.Figure:
    """Stacked bar: daňové složky při min/průměrné/2× průměrné mzdě."""
    reference_incomes = [MIN_WAGE, AVG_WAGE, 2 * AVG_WAGE]
    labels = ["Min. mzda", "Prům. mzda", "2× Prům. mzda"]
    modes = [
        ("Zaměstnanec",    "employee", None,  False),
        ("OSVČ 60 % výd.", "osvc",     EXPENSE_RATE_60, False),
        ("OSVČ 80 % výd.", "osvc",     EXPENSE_RATE_80, False),
    ]

    n_incomes = len(reference_incomes)
    n_modes   = len(modes)
    bar_width = 0.20
    group_gap = 0.8
    x_positions = np.array([i * (n_modes * bar_width + group_gap)
                             for i in range(n_incomes)])

    fig, ax = plt.subplots(figsize=cm2in(15, 10))

    components = [
        ("SP zaměstnavatel", PALETTE[6], lambda bd: bd.get("sp_employer", 0) or 0),
        ("ZP zaměstnavatel", PALETTE[3], lambda bd: bd.get("zp_employer", 0) or 0),
        ("SP zaměstnanec / OSVČ", PALETTE[0], lambda bd:
            bd.get("sp_employee", 0) or bd.get("sp_osvc", 0) or 0),
        ("ZP zaměstnanec / OSVČ", PALETTE[1], lambda bd:
            bd.get("zp_employee", 0) or bd.get("zp_osvc", 0) or 0),
        ("DPFO", PALETTE[4], lambda bd: bd.get("dpfo", 0) or 0),
        ("Čistý příjem", PALETTE[2], lambda bd: bd.get("net", 0)),
    ]

    first_pass = True
    for i, (mode_label, mode, er, pau) in enumerate(modes):
        x_pos = x_positions + i * bar_width
        for j, income in enumerate(reference_incomes):
            bd = tax_breakdown(income, mode=mode,
                               expense_rate=er or EXPENSE_RATE_60,
                               pausalni=pau)
            bottom = 0.0
            for comp_label, color, getter in components:
                val = getter(bd)
                ax.bar(
                    x_pos[j], val / 1_000, bar_width * 0.9,
                    bottom=bottom / 1_000,
                    color=color,
                    label=comp_label if first_pass and j == 0 else "_nolegend_",
                )
                bottom += val
            first_pass = False

    tick_x = x_positions + (n_modes - 1) * bar_width / 2
    ax.set_xticks(tick_x)
    # Each group: 3 sub-bars for the 3 modes
    sub_labels = "\n".join([f"  {ml}" for ml, *_ in modes])
    ax.set_xticklabels(labels)
    ax.set_ylabel("Kč/měsíc (tis.)")
    ax.set_title("Daňové složky při vybraných úrovních příjmu (CZ, 2026)")
    ax.legend(loc="upper left", fontsize=FONT_SIZE - 1)
    fig.tight_layout()
    return fig


# ── Generate and save all figures ─────────────────────────────────────────────

print("Generating tax model figures…")

fig_a = plot_tax_wedge_vs_income()
savefig(fig_a, "cz_tax_wedge_vs_income", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "cz_tax_wedge_vs_income",
    caption=(
        "Efektivní daňový klín (podíl odvodů a daní) dle výše příjmu/příjmů (CZ, 2026). "
        r"Zaměstnanec: báze = celkový náklad zaměstnavatele (hrubá mzda $\times$~1{,}338). "
        "OSVČ: báze = příjmy (= ekvivalent nákladu na práci). "
        "Zdroj: vlastní výpočet dle ZDP, NV~č.~405/2025~Sb."
    ),
    label="fig:cz_tax_wedge_vs_income",
    width=r"0.95\linewidth",
)

fig_b = plot_net_income_vs_income()
savefig(fig_b, "cz_net_income_vs_income", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "cz_net_income_vs_income",
    caption=(
        "Čistý příjem zaměstnance a OSVČ v závislosti na hrubém příjmu / příjmech OSVČ "
        "(CZ, 2026). Zdroj: vlastní výpočet."
    ),
    label="fig:cz_net_income_vs_income",
    width=r"0.95\linewidth",
)

fig_c = plot_sp_vs_income()
savefig(fig_c, "cz_sp_vs_income", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "cz_sp_vs_income",
    caption=(
        "Efektivní sazba sociálního a zdravotního pojistného (vlastní část pojistného) "
        "dle příjmu (CZ, 2026). Zdroj: vlastní výpočet."
    ),
    label="fig:cz_sp_vs_income",
    width=r"0.95\linewidth",
)

fig_d = plot_tax_breakdown()
savefig(fig_d, "cz_tax_breakdown", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "cz_tax_breakdown",
    caption=(
        "Složky daňového zatížení při minimální, průměrné a dvojnásobné průměrné mzdě "
        "pro zaměstnance a OSVČ s výdajovými paušály (CZ, 2026). Zdroj: vlastní výpočet."
    ),
    label="fig:cz_tax_breakdown",
    width=r"0.95\linewidth",
)

print("Done.")
