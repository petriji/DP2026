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

# Paušální daň – celkové měsíční platby (pojistné + daň z příjmů)
# Formát: (max_příjem_Kč/měs., celková_platba_Kč/měs.)
# Pásmo 1: daň 100 + soc. 6 578 + zdrav. 3 306 = 9 984 Kč/měs.
# Pásmo 2: daň 4 963 + soc. 8 191 + zdrav. 3 591 = 16 745 Kč/měs.
# Pásmo 3: daň 9 320 + soc. 12 527 + zdrav. 5 292 = 27 139 Kč/měs.
PAUSALNI_DAN_TOTAL: list[tuple[int, int]] = [
    (83_333,   9_984),   # pásmo 1: příjmy ≤ 1 000 000 Kč/rok
    (125_000, 16_745),   # pásmo 2: příjmy ≤ 1 500 000 Kč/rok
    (166_667, 27_139),   # pásmo 3: příjmy ≤ 2 000 000 Kč/rok
]

# ── Daň z příjmů fyzických osob (DPFO) a odvody zaměstnance ──────────────────
# Zákon č. 586/1992 Sb. (zákon o daních z příjmů, ZDP).

# Sazby daně z příjmů (§ 16 ZDP):
INCOME_TAX_RATE_LOW: float  = 0.15   # 15 % (do 3× průměrné mzdy/měsíc)
INCOME_TAX_RATE_HIGH: float = 0.23   # 23 % (nad 3× průměrné mzdy/měsíc)
TAX_THRESHOLD_MONTHLY: int  = 3 * AVG_WAGE  # 146 901 Kč/měsíc (2026)

# Základní sleva na poplatníka (§ 35ba odst. 1 písm. a) ZDP):
SLEVA_POPLATNIK_MONTHLY: int = 2_570  # 2 570 Kč/měsíc (= 30 840 Kč/rok)

# Sazby pojistného zaměstnance (§ 7 zák. č. 589/1992 Sb., § 2 zák. č. 592/1992 Sb.):
#   Sociální (důchodové 6,5 % + nemocenské 0,6 %): 7,1 %
#   Zdravotní: 4,5 %
EMPLOYEE_SOCIAL_RATE: float = 0.071   # 7,1 % z hrubé mzdy
EMPLOYEE_HEALTH_RATE: float = 0.045   # 4,5 % z hrubé mzdy

# ── OSVČ – sazby zdravotního a sociálního pojistného ─────────────────────────
# Zákon č. 589/1992 Sb. (sociální) a zákon č. 592/1992 Sb. (zdravotní).
OSVC_SOCIAL_RATE: float = 0.292   # 29,2 % z vyměřovacího základu
OSVC_HEALTH_RATE: float = 0.135   # 13,5 % z vyměřovacího základu

# Minimální měsíční vyměřovací základ OSVČ pro zdravotní pojištění (2026):
# = 50 % průměrné mzdy.
OSVC_MIN_HEALTH_BASE: int = AVG_WAGE // 2  # 24 484 Kč/měsíc (2026)

# ── Minimální mzda ────────────────────────────────────────────────────────────
# Nařízení vlády č. 405/2025 Sb. – platné od 1. 1. 2026.
MIN_WAGE: int = 20_800  # CZK/měsíc (hrubá mzda, zaměstnanec)
# Celkové náklady zaměstnavatele při minimální mzdě (osa x ekvivalent):
MIN_WAGE_TOTAL_COST: int = int(MIN_WAGE * (1 + EMPLOYER_INS_RATE))  # ≈ 27 830 Kč

# ── Polohy zlomů (kinks) na ose x (celkové náklady / zisk) pro RH1/RH2 ───────
# Redukční hranice RH1 a RH2 jsou prahové hodnoty OVZ, nikoliv osy x.
# Na ose x = celkové náklady zaměstnavatele / zisk OSVČ se zlomy nacházejí:
#   Zaměstnanec: OVZ = gross = x / (1 + EMPLOYER_INS_RATE) → x_emp = RH × (1 + rate)
#   OSVČ:        OVZ = 50 % × x                            → x_osvc = RH / 0,50
EMP_RH1_X: int  = int(RH1 * (1 + EMPLOYER_INS_RATE))   # ≈ 28 829 Kč (zam. kink @ RH1)
EMP_RH2_X: int  = int(RH2 * (1 + EMPLOYER_INS_RATE))   # ≈ 262 272 Kč (mimo std. rozsah)
OSVC_RH1_X: int = int(RH1 / OSVC_BASE_RATIO)           # = 43 092 Kč (OSVČ kink @ RH1)
OSVC_RH2_X: int = int(RH2 / OSVC_BASE_RATIO)           # = 391 736 Kč (mimo std. rozsah)

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


def tax_wedge_employee(total_labor_cost: np.ndarray | float) -> np.ndarray | float:
    """Efektivní daňový klín zaměstnance [%] z celkových nákladů zaměstnavatele.

    Daňový klín = (celkové náklady − čistá mzda) / celkové náklady × 100.

    Celkové náklady = hrubá mzda × (1 + EMPLOYER_INS_RATE).
    Čistá mzda = hrubá − pojistné zaměstnance (soc. + zdrav.) − daň z příjmů.
    Základ daně = hrubá mzda (§ 6 odst. 12 ZDP; bez superhrubé od 2021).
    """
    x = np.asarray(total_labor_cost, dtype=float)
    gross = x / (1 + EMPLOYER_INS_RATE)
    employee_social = EMPLOYEE_SOCIAL_RATE * gross
    employee_health = EMPLOYEE_HEALTH_RATE * gross
    dan_raw = (
        np.minimum(gross, TAX_THRESHOLD_MONTHLY) * INCOME_TAX_RATE_LOW
        + np.maximum(gross - TAX_THRESHOLD_MONTHLY, 0) * INCOME_TAX_RATE_HIGH
    )
    dan = np.maximum(dan_raw - SLEVA_POPLATNIK_MONTHLY, 0)
    net_wage = gross - employee_social - employee_health - dan
    return (x - net_wage) / x * 100


def tax_wedge_osvc(profit: np.ndarray | float) -> np.ndarray | float:
    """Efektivní daňový klín OSVČ se standardními odvody [%] ze zisku.

    Daňový klín = (zisk − čistý příjem) / zisk × 100.

    Základ daně DPFO = zisk − sociální − zdravotní pojistné (§ 24/2/e ZDP).
    """
    x = np.asarray(profit, dtype=float)
    social_base = np.maximum(OSVC_BASE_RATIO * x, OSVC_MIN_MONTHLY_BASE)
    health_base = np.maximum(OSVC_BASE_RATIO * x, OSVC_MIN_HEALTH_BASE)
    social = OSVC_SOCIAL_RATE * social_base
    health = OSVC_HEALTH_RATE * health_base
    zdane = np.maximum(x - social - health, 0.0)
    dan_raw = (
        np.minimum(zdane, TAX_THRESHOLD_MONTHLY) * INCOME_TAX_RATE_LOW
        + np.maximum(zdane - TAX_THRESHOLD_MONTHLY, 0) * INCOME_TAX_RATE_HIGH
    )
    dan = np.maximum(dan_raw - SLEVA_POPLATNIK_MONTHLY, 0)
    net_income = x - social - health - dan
    return (x - net_income) / x * 100


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

    # Referenční čáry
    _add_vertical_ref(ax, MIN_WAGE_TOTAL_COST / 1_000,
                      f"Min.\u00a0mzda\n({_fmt_czk(MIN_WAGE_TOTAL_COST)})",
                      color="#cc6600", linestyle=(0, (4, 3)))
    avg_total_cost = int(AVG_WAGE * (1 + EMPLOYER_INS_RATE))
    _add_vertical_ref(ax, avg_total_cost / 1_000,
                      f"Celk.\u00a0nákl.\u00a0(prům.\u00a0mzda)\n({_fmt_czk(avg_total_cost)})",
                      color="#888888")
    # Zlomy křivek: RH1 odpovídá OVZ, nikoliv x → různé pozice pro zam. a OSVČ
    _add_vertical_ref(ax, EMP_RH1_X / 1_000,
                      f"1.\u00a0RH\u00a0(zam.)\n({_fmt_czk(EMP_RH1_X)})",
                      color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))
    _add_vertical_ref(ax, OSVC_RH1_X / 1_000,
                      f"1.\u00a0RH\u00a0(OSVČ)\n({_fmt_czk(OSVC_RH1_X)})",
                      color=c_osvc, alpha=0.35, linestyle=(0, (2, 6)))
    if EMP_RH2_X <= income_max:
        _add_vertical_ref(ax, EMP_RH2_X / 1_000, "2.\u00a0RH\u00a0(zam.)",
                          color=c_emp, alpha=0.25, linestyle=(0, (2, 6)))
    if OSVC_RH2_X <= income_max:
        _add_vertical_ref(ax, OSVC_RH2_X / 1_000, "2.\u00a0RH\u00a0(OSVČ)",
                          color=c_osvc, alpha=0.25, linestyle=(0, (2, 6)))

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
    _add_vertical_ref(ax_top, MIN_WAGE_TOTAL_COST / 1_000,
                      f"Min.\u00a0mzda\n({_fmt_czk(MIN_WAGE_TOTAL_COST)})",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax_top, avg_total_cost / 1_000,
                      f"Celk.\u00a0nákl.\u00a0(prům.\u00a0mzda)\n({_fmt_czk(avg_total_cost)})",
                      color="#888888")
    # RH kinks: kreslíme na x-pozicích kde skutečně mění sklon příslušná křivka
    if EMP_RH1_X <= income_max:
        _add_vertical_ref(ax_top, EMP_RH1_X / 1_000,
                          f"1.\u00a0RH\u00a0(zam.)\n({_fmt_czk(EMP_RH1_X)})",
                          color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))
    if OSVC_RH1_X <= income_max:
        _add_vertical_ref(ax_top, OSVC_RH1_X / 1_000,
                          f"1.\u00a0RH\u00a0(OSVČ)\n({_fmt_czk(OSVC_RH1_X)})",
                          color=c_osvc, alpha=0.35, linestyle=(0, (2, 6)))
    if EMP_RH2_X <= income_max:
        _add_vertical_ref(ax_top, EMP_RH2_X / 1_000, "2.\u00a0RH\u00a0(zam.)",
                          color=c_emp, alpha=0.25, linestyle=(0, (2, 6)))
    if OSVC_RH2_X <= income_max:
        _add_vertical_ref(ax_top, OSVC_RH2_X / 1_000, "2.\u00a0RH\u00a0(OSVČ)",
                          color=c_osvc, alpha=0.25, linestyle=(0, (2, 6)))

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

    # Referenční svislé čáry – dolní panel (stejné kink pozice jako horní)
    _add_vertical_ref(ax_bot, MIN_WAGE_TOTAL_COST / 1_000,
                      f"Min.\u00a0mzda",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax_bot, avg_total_cost / 1_000,
                      "Celk.\u00a0nákl.\u00a0(prům.\u00a0mzda)",
                      color="#888888")
    if EMP_RH1_X <= income_max:
        _add_vertical_ref(ax_bot, EMP_RH1_X / 1_000,
                          "1.\u00a0RH\u00a0(zam.)",
                          color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))
    if OSVC_RH1_X <= income_max:
        _add_vertical_ref(ax_bot, OSVC_RH1_X / 1_000,
                          "1.\u00a0RH\u00a0(OSVČ)",
                          color=c_osvc, alpha=0.35, linestyle=(0, (2, 6)))
    if EMP_RH2_X <= income_max:
        _add_vertical_ref(ax_bot, EMP_RH2_X / 1_000, "2.\u00a0RH\u00a0(zam.)",
                          color=c_emp, alpha=0.25, linestyle=(0, (2, 6)))
    if OSVC_RH2_X <= income_max:
        _add_vertical_ref(ax_bot, OSVC_RH2_X / 1_000, "2.\u00a0RH\u00a0(OSVČ)",
                          color=c_osvc, alpha=0.25, linestyle=(0, (2, 6)))

    ax_bot.set_xlabel("Celkové náklady zaměstnavatele / příjem OSVČ [tis.\u00a0Kč/měsíc]")
    ax_bot.set_ylabel("Náhradový poměr (důchod\u00a0/\u00a0nákl.)\u00a0[%]")
    ax_bot.set_xlim(0, income_max / 1_000)
    ax_bot.set_ylim(bottom=0)

    return fig


def plot_tax_wedge_comparison(
    income_max: int = 200_000,
    income_min: int = OSVC_MIN_MONTHLY_BASE * 2,
    years: int = INSURANCE_YEARS,
) -> plt.Figure:
    """Parametrický obrázek: náhradový poměr vs. daňový klín.

    Osa x = efektivní daňový klín [%]
        = (celk. náklady − čistý příjem) / celk. náklady × 100.
    Osa y = náhradový poměr [%]
        = důchod / celk. náklady × 100.

    Každá křivka je parametrizována příjmem (celkové náklady zaměstnavatele /
    zisk OSVČ) v rozsahu [income_min, income_max].  Přímé srovnání polohy křivek
    ukazuje, kolik procent nákladů práce se vrátí jako důchod pro danou
    odvodovou zátěž.

    Parameters
    ----------
    income_max:
        Horní mez parametrického příjmu [Kč/měsíc].
    income_min:
        Spodní mez příjmu [Kč/měsíc].  Pod touto hodnotou tvoří zákonný
        minimální základ OSVČ více než 50 % zisku, výpočet by byl umělý.
    years:
        Předpokládaná pojistná doba [roky].

    Returns
    -------
    matplotlib Figure objekt.
    """
    x = np.linspace(income_min, income_max, 2_000)  # Kč/měsíc

    # ── Datové vektory ─────────────────────────────────────────────────────────
    gross_emp = x / (1 + EMPLOYER_INS_RATE)

    tw_emp  = tax_wedge_employee(x)
    tw_osvc = tax_wedge_osvc(x)

    rr_emp  = pension_employee(gross_emp, years) / x * 100
    rr_osvc = pension_osvc(x, years) / x * 100

    # ── Barvy ──────────────────────────────────────────────────────────────────
    c_emp, c_osvc = PALETTE[0], PALETTE[1]
    c_pausalni    = [PALETTE[2], PALETTE[3], PALETTE[4]]
    band_labels   = [
        "Paušální daň – pásmo\u00a01",
        "Paušální daň – pásmo\u00a02",
        "Paušální daň – pásmo\u00a03",
    ]

    # ── Figury ─────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=cm2in(16, 12))

    ax.plot(tw_emp,  rr_emp,
            color=c_emp,  linewidth=2.0, label="Zaměstnanec (celk.\u00a0nákl.)")
    ax.plot(tw_osvc, rr_osvc,
            color=c_osvc, linewidth=2.0, linestyle="--",
            label="OSVČ – standardní odvody (zisk)")

    # Paušální daň – obě veličiny parametrizovány příjmem uvnitř pásma
    prev_max = 0
    for i, ((max_inc_p, monthly_base), (max_inc_t, total_pay)) in enumerate(
            zip(PAUSALNI_DAN, PAUSALNI_DAN_TOTAL)):
        x_band  = np.linspace(max(prev_max + 1, income_min), max_inc_t, 300)
        tw_band = total_pay / x_band * 100
        p_val   = _pension(monthly_base, years)
        rr_band = p_val / x_band * 100
        ax.plot(tw_band, rr_band,
                color=c_pausalni[i], linewidth=2.5, linestyle=":",
                label=band_labels[i])
        prev_max = max_inc_t

    # ── Anotace referenčních příjmových hladin ──────────────────────────────────
    avg_total_cost = int(AVG_WAGE * (1 + EMPLOYER_INS_RATE))
    ref_points = [
        (MIN_WAGE_TOTAL_COST, "Min.\u00a0mzda", "#cc6600"),
        (avg_total_cost,      "Prům.\u00a0mzda", "#888888"),
    ]
    for x_ref, lbl, col in ref_points:
        if income_min <= x_ref <= income_max:
            gross_r = x_ref / (1 + EMPLOYER_INS_RATE)
            tw_e = float(tax_wedge_employee(float(x_ref)))
            rr_e = float(pension_employee(float(gross_r), years)) / x_ref * 100
            ax.plot(tw_e, rr_e, "o", color=col, markersize=5, zorder=5)
            ax.annotate(lbl, (tw_e, rr_e), xytext=(4, 4),
                        textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color=col)
            tw_o = float(tax_wedge_osvc(float(x_ref)))
            rr_o = float(pension_osvc(float(x_ref), years)) / x_ref * 100
            ax.plot(tw_o, rr_o, "o", color=col, markersize=5, zorder=5)

    ax.set_xlabel("Daňový klín\u00a0[%]")
    ax.set_ylabel("Náhradový poměr (důchod\u00a0/\u00a0nákl.)\u00a0[%]")
    ax.set_title(
        "Náhradový poměr v závislosti na daňovém klínu\n"
        f"(parametry\u00a02026, pojistná doba\u00a0{years}\u00a0let)",
        loc="center",
    )
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 1,
              loc="upper right", borderaxespad=0.5)

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

    # ── Obrázek 3: náhradový poměr vs. daňový klín (parametrický) ────────────
    fig_tw = plot_tax_wedge_comparison()
    savefig(fig_tw, "cz_pension_wedge", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "cz_pension_wedge",
        caption=(
            r"Náhradový poměr v závislosti na efektivním daňovém klínu – "
            r"parametrický obrázek (parametr = celkové náklady zaměstnavatele "
            r"resp. zisk OSVČ, rozsah přibližně 39–200\,tis.\,Kč/měsíc). "
            r"Osa x: daňový klín = (náklady na práci\,−\,čistý příjem) / náklady na práci; "
            r"zahrnuje daň z~příjmů, pojistné zaměstnance i zaměstnavatele "
            r"(resp. sociální a zdravotní pojistné OSVČ). "
            r"Osa y: náhradový poměr = důchod\,/\,celkové náklady. "
            r"Body označené kroužkem odpovídají minimální a průměrné mzdě. "
            r"Čím výše a vlevo leží křivka, tím výšší důchod dostane pracovník "
            r"za danou odvodovou zátěž. "
            r"Parametry roku~2026, pojistná doba 40~let. "
            r"Výpočet dle zákona č.\,155/1995~Sb., č.\,270/2023~Sb., "
            r"č.\,586/1992~Sb.\ a nařízení vlády č.\,365/2025~Sb."
        ),
        label="fig:cz_pension_wedge",
        width=r"0.95\linewidth",
    )

    print("Hotovo.")
