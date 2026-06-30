r"""Czech old-age pension (starobní důchod) – calculation model and solidarity figure.

X-axis semantics (shared by all plot functions)
------------------------------------------------
For a fair economic comparison between an employee and an OSVČ doing equivalent
work, the x-axis represents the *total cost to the payer* (employer or client):

  • Zaměstnanec (employee):
      x = celkové náklady zaměstnavatele = hrubá mzda × (1 + EMPLOYER_INS_RATE)
          (employer social 24,8 % + health 9,0 % = 33,8 % on top of gross wage)
      OVZ = hrubá mzda = x / (1 + EMPLOYER_INS_RATE)

  • OSVČ – standardní odvody:
      x = zisk (příjmy − výdaje)      OVZ = max(50 % × zisk, OSVC_MIN_MONTHLY_BASE)

  • OSVČ – paušální daň pásma 1–3:
      x = měsíční příjmy (revenue); assessment base fixed per pásmo.
      Income ceilings (83 333 / 125 000 / 166 667 Kč/měs.) are revenue-based.

This normalisation makes the švarc-systém comparison meaningful: a client that
budgets 100 000 Kč/month either pays an employer for an employee 100 000 Kč total (gross
≈ 74 700 Kč) or an OSVČ 100 000 Kč as their revenue/profit.

All calculations use 2026 parameters:
  zákon č. 155/1995 Sb. (ZPDS), zákon č. 270/2023 Sb. (pension reform),
  nařízení vlády č. 365/2025 Sb. (valuation for 2026).

Pension formula (§ 33–34 ZPDS):
    pension = základní výměra + ROVZ × pojistná_doba × PCT_PER_YEAR

PCT_PER_YEAR = 1,495 % for 2026 (gradual reduction from 1,5 % to 1,45 % by 2035,
               zákon č. 270/2023 Sb., § 34 odst. 1).

Reduction (§ 15 ZPDS):
    ROVZ = min(OVZ, RH1) × 1.00
         + max(min(OVZ, RH2) − RH1, 0) × 0.26
         + max(OVZ − RH2, 0) × 0.22

Figures
-------
  plot_pension_comparison() – single panel: monthly pension vs x-axis cost.
      Output: pics/python/cz_pension_income.pdf

  plot_pension_solidarity()  – two panels:
      Top:    monthly pension (tis. Kč) – absolute values
      Bottom: replacement rate (%) = pension / x – the declining slope shows
              the solidarity mechanism; lower earners receive proportionally more.
      Output: pics/python/cz_pension_solidarity.pdf

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

# ── 2026 statutory parameters ─────────────────────────────────────────────────
# Sources: zákon č. 155/1995 Sb. ve znění pozdějších předpisů (ZPDS),
#          zákon č. 270/2023 Sb. (důchodová reforma),
#          nařízení vlády č. 365/2025 Sb. platné pro rok 2026.

# Průměrná mzda pro účely důchodového pojištění (§ 23b ZPDS)
AVG_WAGE: int = 48_967  # CZK/month (2026)

# Základní výměra starobního důchodu (§ 33 ZPDS)
ZAKLADNI_VYMERA: int = 4_900  # CZK/month (2026)

# Redukční hranice osobního vyměřovacího základu (§ 15 ZPDS)
RH1: int = 21_546   # 1. redukční hranice [CZK/month] (2026)
RH2: int = 195_868  # 2. redukční hranice [CZK/month] (2026)

# Sazba procentní výměry za rok pojištění (§ 34 ZPDS)
# Od roku 2026 se postupně snižuje z 1,5 % na 1,45 % (do roku 2035).
# Zákon č. 270/2023 Sb., § 34 odst. 1.
PCT_PER_YEAR: float = 0.01495  # 1,495 % z ROVZ za každý rok pojistné doby (2026)

# Předpokládaná pojistná doba (roky)
INSURANCE_YEARS: int = 40

# Minimální procentní výměra (§ 34 odst. 1 ZPDS) – dolní hranice procentní části
MIN_PROCENTNI_VYMERA: int = 4_900  # CZK/month (2026; navázáno na min. mzdu)

# Celková minimální výše důchodu (základní výměra + min. procentní výměra)
MIN_TOTAL_PENSION: int = ZAKLADNI_VYMERA + MIN_PROCENTNI_VYMERA  # CZK/month

# ── Náklady zaměstnavatele ────────────────────────────────────────────────────
# Odvody zaměstnavatele za zaměstnance nad rámec hrubé mzdy:
#   Sociální pojištění: 24,8 % (21,5 % důchodové + 2,1 % nemocenské
#                               + 1,2 % státní politika zaměstnanosti)
#   Zdravotní pojištění: 9,0 %
# Celkové náklady = hrubá mzda × (1 + EMPLOYER_INS_RATE).
# Hrubá mzda (= OVZ zaměstnance) = celkové náklady / (1 + EMPLOYER_INS_RATE).
EMPLOYER_INS_RATE: float = 0.338  # 33,8 % z hrubé mzdy

# ── OSVČ – specifika ──────────────────────────────────────────────────────────
# Vyměřovací základ OSVČ = 50 % z rozdílu příjmů a výdajů (§ 5b ZPDS).
OSVC_BASE_RATIO: float = 0.50

# Minimální měsíční vyměřovací základ OSVČ pro hlavní činnost (2026).
# = 40 % průměrné mzdy (od 2026 zvýšeno z 35 % v roce 2025).
OSVC_MIN_MONTHLY_BASE: int = 19_587  # CZK/month (2026; = 40 % × 48 967)

# ── Paušální daň – vyměřovací základy pro důchodové pojištění ─────────────────
# Zákon č. 586/1992 Sb. ve znění zákona č. 355/2021 Sb. a nařízení vlády 2026.
# Pro každé pásmo je stanoven PEVNÝ vyměřovací základ pro důchodové pojištění
# bez ohledu na skutečný příjem v daném pásmu.
# Formát: (max_příjem_Kč/měs., vyměřovací_základ_Kč/měs.)
# Pásmo 1: základ = 40 % prům. mzdy × 1,15 = 22 527 Kč; soc. = 6 578 Kč/měs.
# Pásmo 2: základ pevně 28 050 Kč; soc. = 8 191 Kč/měs.
# Pásmo 3: základ pevně 42 900 Kč; soc. = 12 527 Kč/měs.
# Sazba sociálního pojištění OSVČ: 29,2 % z vyměřovacího základu.
PAUSALNI_DAN: list[tuple[int, int]] = [
    (83_333,  22_527),   # pásmo 1: příjmy ≤ 1 000 000 Kč/rok
    (125_000, 28_050),   # pásmo 2: příjmy ≤ 1 500 000 Kč/rok
    (166_667, 42_900),   # pásmo 3: příjmy ≤ 2 000 000 Kč/rok
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
    Celkové náklady zaměstnavatele = hrubá_mzda × (1 + EMPLOYER_INS_RATE).
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

def _add_vertical_ref(ax: plt.Axes, x_kczk: float, label: str,
                      color: str, alpha: float = 0.7,
                      linestyle: tuple = (0, (3, 4))) -> None:
    """Přidá svislou referenční čáru s anotací do grafu ax.

    Anotace je umístěna pomocí souřadnic osy (axes fraction) pro y, aby
    nevyžadovala znalost rozsahu dat před dokončením layoutu.
    """
    ax.axvline(x_kczk, color=color, linewidth=0.8, linestyle=linestyle,
               alpha=alpha, zorder=1)
    ax.annotate(
        label,
        xy=(x_kczk, 1),
        xycoords=("data", "axes fraction"),
        xytext=(3, -2), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color=color, va="top",
    )


def plot_pension_comparison(
    income_max: int = 200_000,
    years: int = INSURANCE_YEARS,
) -> plt.Figure:
    """Vykreslí srovnání výše starobního důchodu v závislosti na celkových nákladech.

    Osa x = celkové náklady zaměstnavatele (pro zaměstnance) / zisk OSVČ.
    Pro zaměstnance: hrubá mzda = x / (1 + EMPLOYER_INS_RATE).

    Parameters
    ----------
    income_max:
        Horní mez osy x [Kč/měsíc] (= max celkové náklady zaměstnavatele / příjem OSVČ).
    years:
        Předpokládaná pojistná doba [roky] pro výpočet procentní výměry.

    Returns
    -------
    matplotlib Figure objekt.
    """
    x = np.linspace(0, income_max, 2_000)  # Kč/měsíc (total cost / profit)

    # Zaměstnanec: hrubá mzda = celkové náklady / (1 + EMPLOYER_INS_RATE)
    gross_emp = x / (1 + EMPLOYER_INS_RATE)
    p_emp     = pension_employee(gross_emp, years)
    p_osvc    = pension_osvc(x, years)

    fig, ax = plt.subplots(figsize=cm2in(16, 10))

    c_emp, c_osvc = PALETTE[0], PALETTE[1]
    c_pausalni    = [PALETTE[2], PALETTE[3], PALETTE[4]]
    band_labels   = [
        "Paušální daň – pásmo\u00a01",
        "Paušální daň – pásmo\u00a02",
        "Paušální daň – pásmo\u00a03",
    ]

    ax.plot(x / 1_000, p_emp  / 1_000,
            color=c_emp,  linewidth=2.0, label="Zaměstnanec (celk.\u00a0nákl.)")
    ax.plot(x / 1_000, p_osvc / 1_000,
            color=c_osvc, linewidth=2.0, linestyle="--",
            label="OSVČ – standardní odvody (zisk)")

    prev_max = 0
    for i, (max_income, monthly_base) in enumerate(PAUSALNI_DAN):
        p_val = _pension(monthly_base, years)
        x_seg = [prev_max / 1_000, max_income / 1_000]
        y_seg = [p_val / 1_000, p_val / 1_000]
        ax.plot(x_seg, y_seg,
                color=c_pausalni[i], linewidth=2.5, linestyle=":",
                label=band_labels[i])
        if i < len(PAUSALNI_DAN) - 1:
            ax.axvline(max_income / 1_000, color=c_pausalni[i],
                       linewidth=0.5, linestyle=":", alpha=0.4)
        prev_max = max_income

    # Minimální výše důchodu
    min_pension_kczk = MIN_TOTAL_PENSION / 1_000
    ax.axhline(min_pension_kczk, color="#555555", linewidth=0.8,
               linestyle=(0, (5, 5)), alpha=0.7, zorder=1)
    ax.annotate(
        f"Min. důchod ({_fmt_czk(MIN_TOTAL_PENSION)})",
        xy=(income_max * 0.01 / 1_000, min_pension_kczk),
        xytext=(3, 4), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color="#555555", va="bottom",
    )

    # Referenční čára: průměrná hrubá mzda přepočtená na celkové náklady zaměstnavatele
    avg_total_cost = int(AVG_WAGE * (1 + EMPLOYER_INS_RATE))
    _add_vertical_ref(ax, avg_total_cost / 1_000,
                      f"Celk.\u00a0nákl.\u00a0(prům.\u00a0mzda)\n({_fmt_czk(avg_total_cost)})",
                      color="#888888")
    _add_vertical_ref(ax, RH1 / 1_000,
                      f"1.\u00a0RH\n({_fmt_czk(RH1)})",
                      color="#AAAAAA", alpha=0.6, linestyle=(0, (2, 6)))
    if RH2 <= income_max:
        _add_vertical_ref(ax, RH2 / 1_000,
                          "2.\u00a0RH",
                          color="#BBBBBB", alpha=0.5, linestyle=(0, (2, 6)))

    ax.set_xlabel("Celkové náklady zaměstnavatele / příjem OSVČ [tis.\u00a0Kč/měsíc]")
    ax.set_ylabel("Měsíční starobní důchod [tis.\u00a0Kč]")
    ax.set_title(
        f"Výše starobního důchodu v závislosti na nákladech na práci\n"
        f"(pojistná doba\u00a0{years}\u00a0let, parametry\u00a02026)",
        loc="center",
    )
    ax.set_xlim(0, income_max / 1_000)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 1,
               loc="upper left", borderaxespad=0.5)

    return fig


def plot_pension_solidarity(
    income_max: int = 200_000,
    income_min_rr: int = OSVC_MIN_MONTHLY_BASE * 2,
    years: int = INSURANCE_YEARS,
) -> plt.Figure:
    """Dvoupanelový obrázek znázorňující solidární charakter důchodového systému.

    Osa x = celkové náklady zaměstnavatele (zaměstnanec) / zisk OSVČ.
    Pro zaměstnance: hrubá mzda = x / (1 + EMPLOYER_INS_RATE).
    Náhradový poměr = důchod / x (podíl důchodu na celkových nákladech / zisku).

    Horní panel zobrazuje absolutní výši důchodu.
    Dolní panel zobrazuje náhradový poměr – klesající průběh demonstruje solidaritu.

    Parameters
    ----------
    income_max:
        Horní mez osy x [Kč/měsíc].
    income_min_rr:
        Spodní mez x pro dolní panel [Kč/měsíc].
        Výchozí = OSVC_MIN_MONTHLY_BASE × 2: pod touto hodnotou tvoří zákonný
        minimální základ OSVČ víc než 50 % zisku (křivka OSVČ by byla umělá).
    years:
        Předpokládaná pojistná doba [roky].

    Returns
    -------
    matplotlib Figure objekt (dva panely sdílející osu x).
    """
    # ── Datové vektory ─────────────────────────────────────────────────────────
    x      = np.linspace(0, income_max, 2_000)              # Kč/měsíc (cost / profit)
    x_rr   = np.linspace(income_min_rr, income_max, 2_000)  # pro náhradový poměr

    # Zaměstnanec: hrubá mzda = celkové náklady / (1 + EMPLOYER_INS_RATE)
    gross_emp    = x    / (1 + EMPLOYER_INS_RATE)
    gross_emp_rr = x_rr / (1 + EMPLOYER_INS_RATE)

    p_emp    = pension_employee(gross_emp,    years)
    p_osvc   = pension_osvc(x,    years)

    p_emp_rr  = pension_employee(gross_emp_rr, years)
    p_osvc_rr = pension_osvc(x_rr, years)

    # ── Barvy ──────────────────────────────────────────────────────────────────
    c_emp, c_osvc = PALETTE[0], PALETTE[1]
    c_pausalni    = [PALETTE[2], PALETTE[3], PALETTE[4]]
    band_labels   = [
        "Paušální daň – pásmo\u00a01",
        "Paušální daň – pásmo\u00a02",
        "Paušální daň – pásmo\u00a03",
    ]

    # ── Vytvoření figury se dvěma panely ──────────────────────────────────────
    fig, (ax_top, ax_bot) = plt.subplots(
        2, 1,
        figsize=cm2in(16, 14),
        gridspec_kw={"height_ratios": [3, 2]},
        sharex=True,
    )
    fig.subplots_adjust(hspace=0.08)

    # ══════════════════════════════════════════════════════════════════════════
    # HORNÍ PANEL – výše důchodu [tis. Kč/měsíc]
    # ══════════════════════════════════════════════════════════════════════════
    ax_top.plot(x / 1_000, p_emp  / 1_000,
                color=c_emp,  linewidth=2.0, label="Zaměstnanec (celk.\u00a0nákl.)")
    ax_top.plot(x / 1_000, p_osvc / 1_000,
                color=c_osvc, linewidth=2.0, linestyle="--",
                label="OSVČ – standardní odvody (zisk)")

    prev_max = 0
    for i, (max_income, monthly_base) in enumerate(PAUSALNI_DAN):
        p_val  = _pension(monthly_base, years)
        x_seg  = [prev_max / 1_000, max_income / 1_000]
        y_seg  = [p_val / 1_000, p_val / 1_000]
        ax_top.plot(x_seg, y_seg,
                    color=c_pausalni[i], linewidth=2.5, linestyle=":",
                    label=band_labels[i])
        if i < len(PAUSALNI_DAN) - 1:
            ax_top.axvline(max_income / 1_000, color=c_pausalni[i],
                           linewidth=0.5, linestyle=":", alpha=0.4)
        prev_max = max_income

    # Minimální výše důchodu
    min_pension_kczk = MIN_TOTAL_PENSION / 1_000
    ax_top.axhline(min_pension_kczk, color="#555555", linewidth=0.8,
                   linestyle=(0, (5, 5)), alpha=0.7, zorder=1)
    ax_top.annotate(
        f"Min. důchod ({_fmt_czk(MIN_TOTAL_PENSION)})",
        xy=(income_max * 0.01 / 1_000, min_pension_kczk),
        xytext=(3, 4), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color="#555555", va="bottom",
    )

    # Referenční svislé čáry – průměrná hrubá mzda přepočtená na celkové náklady
    avg_total_cost = int(AVG_WAGE * (1 + EMPLOYER_INS_RATE))
    _add_vertical_ref(ax_top, avg_total_cost / 1_000,
                      f"Celk.\u00a0nákl.\u00a0(prům.\u00a0mzda)\n({_fmt_czk(avg_total_cost)})",
                      color="#888888")
    _add_vertical_ref(ax_top, RH1 / 1_000,
                      f"1.\u00a0RH\n({_fmt_czk(RH1)})",
                      color="#AAAAAA", alpha=0.6, linestyle=(0, (2, 6)))
    if RH2 <= income_max:
        _add_vertical_ref(ax_top, RH2 / 1_000,
                          "2.\u00a0RH",
                          color="#BBBBBB", alpha=0.5, linestyle=(0, (2, 6)))

    ax_top.set_ylabel("Měsíční starobní důchod [tis.\u00a0Kč]")
    ax_top.set_title(
        f"Výše a solidarita starobního důchodu v závislosti na nákladech na práci\n"
        f"(pojistná doba\u00a0{years}\u00a0let, parametry\u00a02026)",
        loc="center",
    )
    ax_top.set_xlim(0, income_max / 1_000)
    ax_top.set_ylim(bottom=0)
    ax_top.legend(
        frameon=False,
        fontsize=FONT_SIZE - 1,
        loc="upper left",
        borderaxespad=0.5,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # DOLNÍ PANEL – náhradový poměr [%] = důchod / x × 100
    # x = celkové náklady zaměstnavatele (zaměstnanec) / zisk OSVČ.
    # Klesající průběh = solidarita: nižší náklady/příjem → vyšší poměr.
    # ══════════════════════════════════════════════════════════════════════════
    rr_emp  = p_emp_rr  / x_rr * 100
    rr_osvc = p_osvc_rr / x_rr * 100

    ax_bot.plot(x_rr / 1_000, rr_emp,
                color=c_emp,  linewidth=2.0)
    ax_bot.plot(x_rr / 1_000, rr_osvc,
                color=c_osvc, linewidth=2.0, linestyle="--")

    # Paušální daň – náhradový poměr v rámci každého pásma
    prev_max = 0
    for i, (max_income, monthly_base) in enumerate(PAUSALNI_DAN):
        p_val  = _pension(monthly_base, years)
        x_band = np.linspace(max(prev_max + 1, income_min_rr), max_income, 300)
        rr_band = p_val / x_band * 100
        ax_bot.plot(x_band / 1_000, rr_band,
                    color=c_pausalni[i], linewidth=2.5, linestyle=":")
        if i < len(PAUSALNI_DAN) - 1:
            ax_bot.axvline(max_income / 1_000, color=c_pausalni[i],
                           linewidth=0.5, linestyle=":", alpha=0.4)
        prev_max = max_income

    # Referenční svislé čáry – dolní panel
    _add_vertical_ref(ax_bot, avg_total_cost / 1_000,
                      "Celk.\u00a0nákl.\u00a0(prům.\u00a0mzda)",
                      color="#888888")
    _add_vertical_ref(ax_bot, RH1 / 1_000,
                      "1.\u00a0RH",
                      color="#AAAAAA", alpha=0.6, linestyle=(0, (2, 6)))
    if RH2 <= income_max:
        _add_vertical_ref(ax_bot, RH2 / 1_000,
                          "2.\u00a0RH",
                          color="#BBBBBB", alpha=0.5, linestyle=(0, (2, 6)))

    ax_bot.set_xlabel("Celkové náklady zaměstnavatele / příjem OSVČ [tis.\u00a0Kč/měsíc]")
    ax_bot.set_ylabel("Náhradový poměr (důchod\u00a0/\u00a0nákl.)\u00a0[%]")
    ax_bot.set_xlim(0, income_max / 1_000)
    ax_bot.set_ylim(bottom=0)

    return fig


# ── Spuštění ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    apply_style()

    # ── Obrázek 1: přehledové srovnání (single-panel) ─────────────────────────
    fig_cmp = plot_pension_comparison()
    savefig(fig_cmp, "cz_pension_income", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "cz_pension_income",
        caption=(
            r"Výše starobního důchodu v závislosti na celkových nákladech "
            r"zaměstnavatele (zaměstnanec) resp. zisku (OSVČ) za měsíc. "
            r"Osa x odpovídá celkovým výdajům plátce: pro zaměstnance zahrnuje "
            r"hrubou mzdu i odvody zaměstnavatele (33,8\,\%); pro OSVČ se standardními "
            r"odvody je to zisk (příjmy\,−\,výdaje); pro OSVČ v~paušálním daňovém "
            r"režimu jde o~měsíční příjmy (revenue), přičemž výše důchodu je v~každém "
            r"pásmu pevná. "
            r"Parametry roku~2026, předpokládaná pojistná doba 40~let. "
            r"Výpočet dle zákona č.\,155/1995~Sb.\ (zákon o~důchodovém pojištění), "
            r"zákona č.\,270/2023~Sb.\ (důchodová reforma) "
            r"a nařízení vlády č.\,365/2025~Sb."
        ),
        label="fig:cz_pension_income",
        width=r"0.95\linewidth",
    )

    # ── Obrázek 2: solidární přerozdělení (two-panel) ─────────────────────────
    fig_sol = plot_pension_solidarity()
    savefig(fig_sol, "cz_pension_solidarity", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "cz_pension_solidarity",
        caption=(
            r"Výše starobního důchodu (horní panel) a náhradový poměr "
            r"(dolní panel) v závislosti na celkových nákladech zaměstnavatele "
            r"(zaměstnanec) resp. zisku (OSVČ) za měsíc – viz obrázek "
            r"\ref{fig:cz_pension_income} pro popis osy\,x. "
            r"Náhradový poměr = důchod\,/\,celkové náklady\,/\,zisk; "
            r"klesající průběh dokládá solidární přerozdělení ve prospěch nižších příjmů. "
            r"Parametry roku~2026, pojistná doba 40~let. "
            r"Výpočet dle zákona č.\,155/1995~Sb., zákona č.\,270/2023~Sb. "
            r"a nařízení vlády č.\,365/2025~Sb."
        ),
        label="fig:cz_pension_solidarity",
        width=r"0.95\linewidth",
    )

    print("Hotovo.")
