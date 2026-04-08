r"""Czech old-age pension (starobní důchod) – calculation model and income-comparison figure.

Compares monthly pension as a function of gross monthly income for:
  • Zaměstnanec (employee)          – assessment base = gross wage
  • OSVČ – standardní odvody        – assessment base = 50 % of profit
  • OSVČ – paušální daň pásmo 1    – fixed assessment base (příjmy ≤ 1 M Kč/rok)
  • OSVČ – paušální daň pásmo 2    – fixed assessment base (příjmy ≤ 1,5 M Kč/rok)
  • OSVČ – paušální daň pásmo 3    – fixed assessment base (příjmy ≤ 2 M Kč/rok)

All calculations assume 40 years of insurance (pojistná doba) and use 2024
parameters from zákon č. 155/1995 Sb. (ZPDS) and nařízení vlády č. 286/2023 Sb.

Pension formula (§ 33–34 ZPDS):
    pension = základní výměra + ROVZ × pojistná_doba × 0.015

Reduction (§ 15 ZPDS):
    ROVZ = min(OVZ, RH1) × 1.00
         + max(min(OVZ, RH2) − RH1, 0) × 0.26
         + max(OVZ − RH2, 0) × 0.22

Output
------
  pics/python/cz_pension_income.pdf
  latex/texparts/python/cz_pension_income.tex

Run
---
    python analyses/cz_pension_model.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.style import apply_style, cm2in, save_figure_tex, savefig

# ── 2024 statutory parameters ─────────────────────────────────────────────────
# Source: zákon č. 155/1995 Sb. ve znění pozdějších předpisů (ZPDS) a
#         nařízení vlády č. 286/2023 Sb. platné pro rok 2024.

# Průměrná mzda pro účely důchodového pojištění (§ 23b ZPDS)
AVG_WAGE: int = 40_638  # CZK/month (2024)

# Základní výměra starobního důchodu (§ 33 ZPDS)
ZAKLADNI_VYMERA: int = 4_040  # CZK/month (2024)

# Redukční hranice osobního vyměřovacího základu (§ 15 ZPDS)
RH1: int = 17_121   # 1. redukční hranice [CZK/month] (2024)
RH2: int = 155_644  # 2. redukční hranice [CZK/month] (2024)

# Sazba procentní výměry za rok pojištění (§ 34 ZPDS)
PCT_PER_YEAR: float = 0.015  # 1,5 % z ROVZ za každý rok pojistné doby

# Předpokládaná pojistná doba (roky)
INSURANCE_YEARS: int = 40

# Minimální procentní výměra (§ 34 odst. 1 ZPDS) – dolní hranice procentní části
MIN_PROCENTNI_VYMERA: int = 770  # CZK/month (2024)

# Celková minimální výše důchodu (základní výměra + min. procentní výměra)
MIN_TOTAL_PENSION: int = ZAKLADNI_VYMERA + MIN_PROCENTNI_VYMERA  # CZK/month

# ── OSVČ – specifika ──────────────────────────────────────────────────────────
# Vyměřovací základ OSVČ = 50 % z rozdílu příjmů a výdajů (§ 5b ZPDS).
OSVC_BASE_RATIO: float = 0.50

# Minimální měsíční vyměřovací základ OSVČ pro hlavní činnost (2024).
# Odvozuje se ze zákona a příslušného nařízení vlády.
OSVC_MIN_MONTHLY_BASE: int = 12_647  # CZK/month (2024)

# ── Paušální daň – vyměřovací základy pro důchodové pojištění ─────────────────
# Zákon č. 586/1992 Sb. ve znění zákona č. 355/2021 Sb. a nařízení vlády 2024.
# Pro každé pásmo je stanoven PEVNÝ vyměřovací základ pro důchodové pojištění
# bez ohledu na skutečný příjem v daném pásmu.
# Formát: (max_příjem_Kč/měs., vyměřovací_základ_Kč/měs.)
PAUSALNI_DAN: list[tuple[int, int]] = [
    (83_333,  14_047),   # pásmo 1: příjmy ≤ 1 000 000 Kč/rok
    (125_000, 20_565),   # pásmo 2: příjmy ≤ 1 500 000 Kč/rok
    (166_667, 27_084),   # pásmo 3: příjmy ≤ 2 000 000 Kč/rok
]

# ── Pomocné výpočetní funkce ──────────────────────────────────────────────────

def _fmt_czk(amount: int) -> str:
    """Formátuje celé číslo jako CZK s úzkými mezerami jako oddělovači tisíců.

    Příklad: 17121 → '17\u202f121\u00a0Kč'
    """
    return f"{amount:,}".replace(",", "\u202f") + "\u00a0Kč"


def _rovz(ovz: np.ndarray | float) -> np.ndarray | float:
    """Redukovaný osobní vyměřovací základ (ROVZ) dle § 15 ZPDS.

    Parameters
    ----------
    ovz:
        Osobní vyměřovací základ (OVZ) v Kč/měsíc.  Může být skalár nebo
        numpy pole.

    Returns
    -------
    ROVZ v Kč/měsíc (stejného typu/tvaru jako vstup).
    """
    return (
        np.minimum(ovz, RH1)
        + np.maximum(np.minimum(ovz, RH2) - RH1, 0) * 0.26
        + np.maximum(ovz - RH2, 0) * 0.22
    )


def _pension(ovz: np.ndarray | float, years: int = INSURANCE_YEARS) -> np.ndarray | float:
    """Měsíční starobní důchod (Kč/měsíc) pro daný OVZ a pojistnou dobu.

    Parameters
    ----------
    ovz:
        Osobní vyměřovací základ [Kč/měsíc].
    years:
        Délka pojistné doby [roky].

    Returns
    -------
    Výše starobního důchodu v Kč/měsíc.
    """
    procentni = np.maximum(_rovz(ovz) * years * PCT_PER_YEAR, MIN_PROCENTNI_VYMERA)
    return ZAKLADNI_VYMERA + procentni


def pension_employee(gross_income: np.ndarray | float,
                     years: int = INSURANCE_YEARS) -> np.ndarray | float:
    """Starobní důchod zaměstnance.

    Vyměřovací základ = hrubá mzda (100 %).
    """
    ovz = np.asarray(gross_income, dtype=float)
    return _pension(ovz, years)


def pension_osvc(gross_profit: np.ndarray | float,
                 years: int = INSURANCE_YEARS) -> np.ndarray | float:
    """Starobní důchod OSVČ se standardními odvody.

    Vyměřovací základ = 50 % ze zisku (příjmy − výdaje), minimálně
    OSVC_MIN_MONTHLY_BASE.
    """
    profit = np.asarray(gross_profit, dtype=float)
    ovz = np.maximum(OSVC_BASE_RATIO * profit, OSVC_MIN_MONTHLY_BASE)
    return _pension(ovz, years)


def pension_pausalni(gross_income: np.ndarray | float,
                     years: int = INSURANCE_YEARS) -> np.ndarray | float:
    """Starobní důchod OSVČ v paušálním režimu (odvodový paušál).

    Vyměřovací základ je pro každé pásmo PEVNÝ a nezávisí na skutečném příjmu
    v rámci pásma – viz PAUSALNI_DAN.  Vstupní příjem nad nejvyšší pásmové
    maximum je považován za nepřípustný pro paušální daň (vrací NaN).
    """
    income = np.asarray(gross_income, dtype=float)
    result = np.full_like(income, np.nan)
    for max_income, monthly_base in PAUSALNI_DAN:
        mask = income <= max_income
        ovz = float(monthly_base)
        result = np.where(mask & np.isnan(result), _pension(ovz, years), result)
    return result


# ── Vizualizace ───────────────────────────────────────────────────────────────

def plot_pension_comparison(
    income_max: int = 200_000,
    years: int = INSURANCE_YEARS,
) -> plt.Figure:
    """Vykreslí srovnání výše starobního důchodu v závislosti na hrubém příjmu.

    Parameters
    ----------
    income_max:
        Horní mez osy x [Kč/měsíc].
    years:
        Předpokládaná pojistná doba [roky] pro výpočet procentní výměry.

    Returns
    -------
    matplotlib Figure objekt.
    """
    income = np.linspace(0, income_max, 2_000)  # Kč/měsíc

    p_emp   = pension_employee(income, years)
    p_osvc  = pension_osvc(income, years)

    fig, ax = plt.subplots(figsize=cm2in(16, 10))

    # ── Křivky důchodů ────────────────────────────────────────────────────────
    c_emp, c_osvc = PALETTE[0], PALETTE[1]
    c_pausalni = [PALETTE[2], PALETTE[3], PALETTE[4]]

    ax.plot(income / 1_000, p_emp / 1_000,
            color=c_emp, linewidth=2.0, label="Zaměstnanec")
    ax.plot(income / 1_000, p_osvc / 1_000,
            color=c_osvc, linewidth=2.0, linestyle="--",
            label="OSVČ – standardní odvody")

    # Paušální daň – pro každé pásmo horizontální segment
    band_labels = ["Paušální daň – pásmo 1", "Paušální daň – pásmo 2", "Paušální daň – pásmo 3"]
    prev_max = 0
    for i, (max_income, monthly_base) in enumerate(PAUSALNI_DAN):
        p_val = _pension(monthly_base, years)
        x_seg = [prev_max / 1_000, max_income / 1_000]
        y_seg = [p_val / 1_000, p_val / 1_000]
        ax.plot(x_seg, y_seg,
                color=c_pausalni[i], linewidth=2.5, linestyle=":",
                label=band_labels[i])
        # Svislá oddělovací čára na hranici pásma
        if i < len(PAUSALNI_DAN) - 1:
            ax.axvline(max_income / 1_000, color=c_pausalni[i],
                       linewidth=0.6, linestyle=":", alpha=0.5)
        prev_max = max_income

    # ── Referenční přímky a anotace ───────────────────────────────────────────
    # Minimální výše důchodu (základní výměra + min. procentní výměra)
    min_pension_kc = MIN_TOTAL_PENSION / 1_000
    ax.axhline(min_pension_kc, color="#555555", linewidth=0.8,
               linestyle=(0, (5, 5)), alpha=0.7, zorder=1)
    ax.annotate(
        f"Min. důchod\n({_fmt_czk(MIN_TOTAL_PENSION)})",
        xy=(income_max * 0.01 / 1_000, min_pension_kc),
        xytext=(3, 4), textcoords="offset points",
        fontsize=FONT_SIZE - 1, color="#555555", va="bottom",
    )

    # Průměrná mzda – svislá čára
    ax.axvline(AVG_WAGE / 1_000, color="#888888", linewidth=0.8,
               linestyle=(0, (3, 4)), alpha=0.7, zorder=1)
    ax.annotate(
        f"Prům. mzda\n({_fmt_czk(AVG_WAGE)})",
        xy=(AVG_WAGE / 1_000, 0),
        xytext=(3, 4), textcoords="offset points",
        fontsize=FONT_SIZE - 1, color="#888888", va="bottom",
    )

    # 1. redukční hranice
    ax.axvline(RH1 / 1_000, color="#AAAAAA", linewidth=0.6,
               linestyle=(0, (2, 6)), alpha=0.6, zorder=1)
    ax.annotate(
        f"1.\u00a0RH\n({_fmt_czk(RH1)})",
        xy=(RH1 / 1_000, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 50),
        xytext=(3, -2), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color="#AAAAAA", va="top",
    )

    # 2. redukční hranice (mimo viditelný rozsah – jen popis na hraně)
    if RH2 / 1_000 <= income_max / 1_000:
        ax.axvline(RH2 / 1_000, color="#BBBBBB", linewidth=0.6,
                   linestyle=(0, (2, 6)), alpha=0.5, zorder=1)
        ax.annotate(
            f"2.\u00a0RH",
            xy=(RH2 / 1_000, 0),
            xytext=(3, 4), textcoords="offset points",
            fontsize=FONT_SIZE - 2, color="#BBBBBB", va="bottom",
        )

    # ── Formátování osy ───────────────────────────────────────────────────────
    ax.set_xlabel("Hrubý měsíční příjem [tis.\u00a0Kč]")
    ax.set_ylabel("Měsíční starobní důchod [tis.\u00a0Kč]")
    ax.set_title(
        f"Výše starobního důchodu v závislosti na příjmu\n"
        f"(pojistná doba\u00a0{years}\u00a0let, parametry\u00a02024)",
        loc="center",
    )
    ax.set_xlim(0, income_max / 1_000)
    ax.set_ylim(bottom=0)

    ax.legend(
        frameon=False,
        fontsize=FONT_SIZE - 1,
        loc="upper left",
        borderaxespad=0.5,
    )

    return fig


# ── Spuštění ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    apply_style()

    fig = plot_pension_comparison()
    savefig(fig, "cz_pension_income", out_dir=LATEX_PICS_DIR)

    save_figure_tex(
        "cz_pension_income",
        caption=(
            r"Výše starobního důchodu v závislosti na hrubém měsíčním příjmu "
            r"pro zaměstnance, OSVČ se standardními odvody a OSVČ v~paušálním "
            r"daňovém režimu (odvodový paušál). "
            r"Parametry roku~2024, předpokládaná pojistná doba 40~let. "
            r"Výpočet dle zákona č.\,155/1995~Sb. "
            r"(zákon o~důchodovém pojištění), nařízení vlády č.\,286/2023~Sb."
        ),
        label="fig:cz_pension_income",
        width=r"0.95\linewidth",
    )

    print("Hotovo.")
