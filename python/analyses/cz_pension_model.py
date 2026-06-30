r"""Czech old-age pension (starobní důchod) – calculation model and figures.

X-axis semantics (shared by all plot functions)
------------------------------------------------
For a fair economic comparison between an employee and an OSVČ doing equivalent
work, the x-axis represents the *total cost to the payer* (employer or client):

  • Zaměstnanec (employee):
      x = celkové náklady zaměstnavatele = hrubá mzda × (1 + EMPLOYER_INS_RATE)
          (employer social 24,8 % + health 9,0 % = 33,8 % on top of gross wage)
      OVZ = hrubá mzda = x / (1 + EMPLOYER_INS_RATE)

  • OSVČ – standardní odvody:
      x = zisk (příjmy − výdaje)      OVZ = max(55 % × zisk, OSVC_MIN_MONTHLY_BASE)

  • OSVČ – paušální daň:
      x = měsíční příjmy (revenue); assessment base fixed per pásmo.
      Dostupná pásma dle typu OSVČ (§ 2a zákona č. 586/1992 Sb.):
        40 % výd. paušál: pásmo 1 (≤ 83 333 Kč/měs.), 2 (≤ 125 000), 3 (≤ 166 667)
        60 % výd. paušál: pásmo 1 (≤ 125 000 Kč/měs.), 2 (≤ 166 667)
        80 % výd. paušál: pásmo 1 only (≤ 166 667 Kč/měs.)

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
    ROVZ = min(OVZ, RH1) × 0.99
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

from matplotlib.lines import Line2D

from config import FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.style import apply_style, cm2in, save_figure_tex, savefig

apply_style()

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
# Vyměřovací základ OSVČ pro sociální pojištění (SP) = 55 % ze základu daně.
# Zákon č. 589/1992 Sb. § 5b ve znění zákona č. 270/2023 Sb. (důchodová reforma):
# sazba VZ pro SP zvýšena z 50 % na 55 % s účinností od 1. 1. 2024.
# Pro důchodové pojištění je OVZ totožný s VZ pro SP (§ 11 ZPDS).
OSVC_BASE_RATIO: float = 0.55   # SP VZ / OVZ = 55 % ze základu daně (2024–)

# Vyměřovací základ OSVČ pro zdravotní pojištění (ZP) = 50 % ze základu daně.
# Zákon č. 592/1992 Sb. § 3a (beze změny reformou).
OSVC_ZP_BASE_RATIO: float = 0.50  # ZP VZ = 50 % ze základu daně

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

# ── Mediánová mzda zaměstnance ────────────────────────────────────────────────
# Zdroj: ISPV (Informační systém o průměrném výdělku), ČSÚ/MPSV, rok 2024.
# Medián hrubé měsíční mzdy zaměstnanců v podnikatelské sféře: 40 709 Kč.
# ISPV se vztahuje pouze na zaměstnance v podnicích; pro OSVČ srovnatelná
# statistika mediánu zisku není zveřejňována (viz komentář ve funkci
# plot_tax_wedge_comparison()).
MEDIAN_EMP_WAGE: int = 40_709   # CZK/měsíc hrubé mzdy (ISPV 2024)
MEDIAN_EMP_TOTAL_COST: int = int(MEDIAN_EMP_WAGE * (1 + EMPLOYER_INS_RATE))  # ≈ 54 469 Kč

# ── Hranice chudoby ───────────────────────────────────────────────────────────
# Zdroj: ČSÚ, rok 2025. Definice: 60 % mediánu čistého příjmu domácnosti.
POVERTY_THRESHOLD: int = 18_600  # CZK/měsíc (2025)

# ── Polohy zlomů (kinks) na ose x (celkové náklady / příjmy) pro RH1/RH2 ─────
# Redukční hranice RH1 a RH2 jsou prahové hodnoty OVZ, nikoliv osy x.
# Zaměstnanec: OVZ = hrubá = x / (1 + EMPLOYER_INS_RATE) → kink = RH × (1 + rate)
# OSVČ s výdajovým paušálem r: OVZ = 55 % × (1-r) × x → kink = RH / (0,55 × (1-r))
EMP_RH1_X: int  = int(RH1 * (1 + EMPLOYER_INS_RATE))   # ≈ 28 829 Kč (zam. kink @ RH1)
EMP_RH2_X: int  = int(RH2 * (1 + EMPLOYER_INS_RATE))   # ≈ 262 272 Kč (mimo std. rozsah)
OSVC_RH1_X: int = int(RH1 / OSVC_BASE_RATIO)           # ≈ 39 175 Kč (OSVČ kink @ RH1, r=0)
OSVC_RH2_X: int = int(RH2 / OSVC_BASE_RATIO)           # ≈ 356 124 Kč (mimo std. rozsah)

# ── OSVČ typy pro srovnání ────────────────────────────────────────────────────
# Formát: (výdajový_paušál, popisek, barva)
# výdajový_paušál: podíl příjmů uznaný jako výdaje → zisk = příjmy × (1 − sazba)
OSVC_TYPES: list[tuple[float, str, str]] = [
    (0.80, "OSVČ 80\u202f%\u00a0výdajů (řemeslná živnost)",          PALETTE[4]),
    (0.60, "OSVČ 60\u202f%\u00a0výdajů (ost.\u00a0živnosti)",       PALETTE[1]),
    (0.40, "OSVČ 40\u202f%\u00a0výdajů (svobodná\u00a0povolání)",   PALETTE[5]),
]

# Barvy paušální daně – jedna barva na pásmo (nezávisle na typu OSVČ,
# protože VZ paušálu je pevný na pásmo a křivky různých typů OSVČ se překrývají).
PASMO_COLORS: list[str] = [PALETTE[2], PALETTE[3], PALETTE[6]]  # pásmo 1, 2, 3

# ── Paušální daň – segmenty platnosti pro každý typ OSVČ ─────────────────────
# Dle § 2a zákona č. 586/1992 Sb. ve znění zákona č. 355/2021 Sb.:
#   40 % výdajový paušál (svobodná povolání): 3 pásma, standardní rozsahy
#     Pásmo 1: příjmy 0–1 000 000 Kč/rok = 0–83 333 Kč/měs.
#     Pásmo 2: příjmy 1 000 000–1 500 000 Kč/rok = 83 333–125 000 Kč/měs.
#     Pásmo 3: příjmy 1 500 000–2 000 000 Kč/rok = 125 000–166 667 Kč/měs.
#   60 % výdajový paušál (obecné živnosti): 2 pásma, vyšší příjmové limity
#     Pásmo 1: příjmy 0–1 500 000 Kč/rok = 0–125 000 Kč/měs. (viz § 2a odst. 4)
#     Pásmo 2: příjmy 1 500 000–2 000 000 Kč/rok = 125 000–166 667 Kč/měs.
#   80 % výdajový paušál (řemeslné živnosti): 1 pásmo po celý příjmový rozsah
#     Pásmo 1: příjmy 0–2 000 000 Kč/rok = 0–166 667 Kč/měs. (viz § 2a odst. 5)
#
# Formát: {výdajový_paušál: [(x_start, x_end, pasmo_index), ...]}
#   x_start / x_end: měsíční příjmový rozsah [Kč/měs.]; x_start=0 → MIN_WAGE_TOTAL_COST
#   pasmo_index: index do PAUSALNI_DAN a PAUSALNI_DAN_TOTAL (0=pásmo 1, 1=pásmo 2, 2=pásmo 3)
PAUSALNI_SEGS: dict[float, list[tuple[int, int, int]]] = {
    0.40: [
        (0,       83_333,  0),   # pásmo 1: příjmy 0–83 333 Kč/měs.
        (83_333,  125_000, 1),   # pásmo 2: příjmy 83 333–125 000 Kč/měs.
        (125_000, 166_667, 2),   # pásmo 3: příjmy 125 000–166 667 Kč/měs.
    ],
    0.60: [
        (0,       125_000, 0),   # pásmo 1: příjmy 0–125 000 Kč/měs. (rozšířený limit)
        (125_000, 166_667, 1),   # pásmo 2: příjmy 125 000–166 667 Kč/měs.
    ],
    0.80: [
        (0,       166_667, 0),   # pásmo 1: příjmy 0–166 667 Kč/měs. (celý rozsah)
    ],
}

# Limity měsíčních příjmů pro výdajový paušál (zákon č. 586/1992 Sb., § 7 odst. 7)
# Nad těmito hranicemi výdajová sazba přestává platit – je třeba uplatnit skutečné
# výdaje (daňová evidence). Hodnoty = roční strop výdajů ÷ 12:
#   80 %: max roční výdaje 1 600 000 Kč → příjmový limit = 1 600 000 ÷ 12 ≈ 133 333 Kč/měs.
#   60 %: max roční výdaje 1 200 000 Kč → příjmový limit = 1 200 000 ÷ 12 = 100 000 Kč/měs.
#   40 %: max roční výdaje   800 000 Kč → příjmový limit =   800 000 ÷ 12 ≈  66 667 Kč/měs.
# V grafech se linestyle změní na '-.' pro příjmy nad limitem.
OSVC_VYDAJOVY_CAP: dict[float, int] = {
    0.80: 133_333,  # max měsíční příjmy pro uplatnění 80 % paušálu
    0.60: 100_000,  # max měsíční příjmy pro uplatnění 60 % paušálu
    0.40:  66_667,  # max měsíční příjmy pro uplatnění 40 % paušálu
}

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
        np.minimum(ovz, RH1) * 0.99
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


def pension_osvc_vydajovy(revenue: np.ndarray | float,
                          expense_rate: float,
                          years: int = INSURANCE_YEARS) -> np.ndarray | float:
    """Starobní důchod OSVČ s výdajovým paušálem dané sazby.

    Parameters
    ----------
    revenue:
        Měsíční příjmy OSVČ (= x na ose x: co zaplatí klient) [Kč/měsíc].
    expense_rate:
        Sazba výdajového paušálu (0,40 / 0,60 / 0,80).
        Zisk = příjmy × (1 − expense_rate).
    """
    rev = np.asarray(revenue, dtype=float)
    profit = (1.0 - expense_rate) * rev
    ovz = np.maximum(OSVC_BASE_RATIO * profit, OSVC_MIN_MONTHLY_BASE)
    return _pension(ovz, years)


def _net_income_emp(total_cost: np.ndarray | float) -> np.ndarray | float:
    """Čistý příjem zaměstnance z celkových nákladů zaměstnavatele."""
    x = np.asarray(total_cost, dtype=float)
    gross = x / (1 + EMPLOYER_INS_RATE)
    sp_e = EMPLOYEE_SOCIAL_RATE * gross
    zp_e = EMPLOYEE_HEALTH_RATE * gross
    dan_raw = (
        np.minimum(gross, TAX_THRESHOLD_MONTHLY) * INCOME_TAX_RATE_LOW
        + np.maximum(gross - TAX_THRESHOLD_MONTHLY, 0) * INCOME_TAX_RATE_HIGH
    )
    dan = np.maximum(dan_raw - SLEVA_POPLATNIK_MONTHLY, 0)
    return gross - sp_e - zp_e - dan


def _net_income_osvc_vydajovy(revenue: np.ndarray | float,
                               expense_rate: float) -> np.ndarray | float:
    """Čistý příjem OSVČ s výdajovým paušálem (ZD − SP − ZP − DPFO)."""
    x = np.asarray(revenue, dtype=float)
    zd = (1.0 - expense_rate) * x
    social_base = np.maximum(OSVC_BASE_RATIO * zd, OSVC_MIN_MONTHLY_BASE)
    health_base = np.maximum(OSVC_ZP_BASE_RATIO * zd, OSVC_MIN_HEALTH_BASE)
    social = OSVC_SOCIAL_RATE * social_base
    health = OSVC_HEALTH_RATE * health_base
    dan_raw = (
        np.minimum(zd, TAX_THRESHOLD_MONTHLY) * INCOME_TAX_RATE_LOW
        + np.maximum(zd - TAX_THRESHOLD_MONTHLY, 0) * INCOME_TAX_RATE_HIGH
    )
    dan = np.maximum(dan_raw - SLEVA_POPLATNIK_MONTHLY, 0)
    return zd - social - health - dan


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

    Osa x = celkové náklady zaměstnavatele (pro zaměstnance) / měsíční příjmy OSVČ.
    Pro zaměstnance: hrubá mzda = x / (1 + EMPLOYER_INS_RATE).
    Pro OSVČ: příjmy = x, zisk = x × (1 − výdajový_paušál).

    Parameters
    ----------
    income_max:
        Horní mez osy x [Kč/měsíc] (= max celkové náklady zaměstnavatele / příjmy OSVČ).
    years:
        Předpokládaná pojistná doba [roky] pro výpočet procentní výměry.

    Returns
    -------
    matplotlib Figure objekt.
    """
    x = np.linspace(MIN_WAGE_TOTAL_COST, income_max, 2_000)  # Kč/měsíc (total cost / revenue)

    gross_emp = x / (1 + EMPLOYER_INS_RATE)
    p_emp     = pension_employee(gross_emp, years)

    fig, ax = plt.subplots(figsize=cm2in(16, 10))
    c_emp = PALETTE[0]

    # Zaměstnanec
    ax.plot(x / 1_000, p_emp / 1_000,
            color=c_emp, linewidth=2.0, zorder=3)

    # OSVČ typy – standardní odvody (dashed below cap, dash-dot above cap) + paušální daň
    for expense_rate, label, color in OSVC_TYPES:
        p_osvc = pension_osvc_vydajovy(x, expense_rate, years)
        cap = OSVC_VYDAJOVY_CAP[expense_rate]
        idx = int(np.searchsorted(x, cap, side='right'))
        if idx > 0:
            ax.plot(x[:idx] / 1_000, p_osvc[:idx] / 1_000,
                    color=color, linewidth=1.5, linestyle="--", zorder=3)
        if idx < len(x):
            start = max(0, idx - 1)
            ax.plot(x[start:] / 1_000, p_osvc[start:] / 1_000,
                    color=color, linewidth=1.5, linestyle="-.", alpha=0.45, zorder=3)

        segs = PAUSALNI_SEGS[expense_rate]
        for seg_i, (x_s, x_e, p_idx) in enumerate(segs):
            _, monthly_base = PAUSALNI_DAN[p_idx]
            p_val  = _pension(monthly_base, years)
            x_start = max(x_s, MIN_WAGE_TOTAL_COST)
            x_end   = min(x_e, income_max)
            if x_start >= x_end:
                continue
            x_seg = [x_start / 1_000, x_end / 1_000]
            y_seg = [p_val / 1_000, p_val / 1_000]
            ax.plot(x_seg, y_seg,
                    color=color, linewidth=2.0, linestyle=":", zorder=2)
            if seg_i < len(segs) - 1 and x_e <= income_max:
                ax.axvline(x_e / 1_000, color=color,
                           linewidth=0.5, linestyle=":", alpha=0.4)

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

    # Hranice chudoby
    poverty_kczk = POVERTY_THRESHOLD / 1_000
    ax.axhline(poverty_kczk, color="#aa0000", linewidth=0.8,
               linestyle=(0, (3, 4)), alpha=0.7, zorder=1)
    ax.annotate(
        f"Hranice chudoby ({_fmt_czk(POVERTY_THRESHOLD)}, 2025)",
        xy=(income_max * 0.01 / 1_000, poverty_kczk),
        xytext=(3, 4), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color="#aa0000", va="bottom",
    )

    # Referenční svislé čáry
    _add_vertical_ref(ax, MIN_WAGE_TOTAL_COST / 1_000,
                      f"Min.\u00a0mzda\n({_fmt_czk(MIN_WAGE_TOTAL_COST)})",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax, MEDIAN_EMP_TOTAL_COST / 1_000,
                      f"Medián\u00a0(zam.)\n({_fmt_czk(MEDIAN_EMP_TOTAL_COST)})",
                      color="#888888")
    if EMP_RH1_X <= income_max:
        _add_vertical_ref(ax, EMP_RH1_X / 1_000,
                          f"1.\u00a0RH\u00a0(zam.)\n({_fmt_czk(EMP_RH1_X)})",
                          color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))
    if EMP_RH2_X <= income_max:
        _add_vertical_ref(ax, EMP_RH2_X / 1_000,
                          f"2.\u00a0RH\u00a0(zam.)\n({_fmt_czk(EMP_RH2_X)})",
                          color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))

    ax.set_xlabel("Celkové náklady zaměstnavatele / příjmy OSVČ [tis.\u00a0Kč/měsíc]")
    ax.set_ylabel("Měsíční starobní důchod [tis.\u00a0Kč]")
    ax.set_title(
        f"Výše starobního důchodu v závislosti na nákladech na práci\n"
        f"(pojistná doba\u00a0{years}\u00a0let, parametry\u00a02026)",
        loc="center",
    )
    ax.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax.set_ylim(bottom=0)

    # Legenda mimo osy – dole pod grafem; ručně sestavené handles pro přehlednost
    legend_handles = [
        Line2D([0], [0], color=c_emp, linewidth=2.0,
               label="Zaměstnanec (celk.\u00a0nákl.)"),
    ]
    for _er, lbl, col in OSVC_TYPES:
        legend_handles.append(
            Line2D([0], [0], color=col, linewidth=1.5, linestyle="--", label=lbl))
    legend_handles.append(
        Line2D([0], [0], color="#888888", linewidth=1.5, linestyle="-.", alpha=0.45,
               label="OSVČ výd.\u00a0paušál nad limitem příjmů"))
    legend_handles.append(
        Line2D([0], [0], color="#555555", linewidth=2.0, linestyle=":",
               label="Paušální daň (tečkovaně, barva dle typu OSVČ)"))
    fig.legend(handles=legend_handles, frameon=False, fontsize=FONT_SIZE - 2,
               loc="lower center", bbox_to_anchor=(0.5, -0.01), ncols=2)

    fig.subplots_adjust(bottom=0.20)
    return fig


def plot_pension_solidarity(
    income_max: int = 200_000,
    income_min_rr: int = OSVC_MIN_MONTHLY_BASE * 2,
    years: int = INSURANCE_YEARS,
) -> plt.Figure:
    """Dvoupanelový obrázek znázorňující solidární charakter důchodového systému.

    Osa x = celkové náklady zaměstnavatele (zaměstnanec) / měsíční příjmy OSVČ.
    Pro zaměstnance: hrubá mzda = x / (1 + EMPLOYER_INS_RATE).
    Náhradový poměr = důchod / x.

    Horní panel zobrazuje absolutní výši důchodu.
    Dolní panel zobrazuje náhradový poměr – klesající průběh demonstruje solidaritu.

    Parameters
    ----------
    income_max:
        Horní mez osy x [Kč/měsíc].
    income_min_rr:
        Spodní mez x pro dolní panel [Kč/měsíc].
        Výchozí = OSVC_MIN_MONTHLY_BASE × 2: pod touto hodnotou tvoří zákonný
        minimální základ OSVČ více než 50 % zisku (křivka OSVČ by byla umělá).
    years:
        Předpokládaná pojistná doba [roky].

    Returns
    -------
    matplotlib Figure objekt (dva panely sdílející osu x).
    """
    # ── Datové vektory ─────────────────────────────────────────────────────────
    x    = np.linspace(MIN_WAGE_TOTAL_COST, income_max, 2_000)
    x_rr = np.linspace(MIN_WAGE_TOTAL_COST, income_max, 2_000)

    gross_emp    = x    / (1 + EMPLOYER_INS_RATE)
    gross_emp_rr = x_rr / (1 + EMPLOYER_INS_RATE)

    p_emp    = pension_employee(gross_emp,    years)
    p_emp_rr = pension_employee(gross_emp_rr, years)

    # ── Vytvoření figury se dvěma panely ──────────────────────────────────────
    fig, (ax_top, ax_bot) = plt.subplots(
        2, 1,
        figsize=cm2in(16, 14),
        gridspec_kw={"height_ratios": [3, 2]},
        sharex=True,
    )
    fig.subplots_adjust(hspace=0.08)

    c_emp = PALETTE[0]

    # ══════════════════════════════════════════════════════════════════════════
    # HORNÍ PANEL – výše důchodu [tis. Kč/měsíc]
    # ══════════════════════════════════════════════════════════════════════════
    ax_top.plot(x / 1_000, p_emp / 1_000,
                color=c_emp, linewidth=2.0, zorder=3)

    for expense_rate, label, color in OSVC_TYPES:
        p_osvc = pension_osvc_vydajovy(x, expense_rate, years)
        cap = OSVC_VYDAJOVY_CAP[expense_rate]
        idx = int(np.searchsorted(x, cap, side='right'))
        if idx > 0:
            ax_top.plot(x[:idx] / 1_000, p_osvc[:idx] / 1_000,
                        color=color, linewidth=1.5, linestyle="--", zorder=3)
        if idx < len(x):
            start = max(0, idx - 1)
            ax_top.plot(x[start:] / 1_000, p_osvc[start:] / 1_000,
                        color=color, linewidth=1.5, linestyle="-.", alpha=0.45, zorder=3)

        segs = PAUSALNI_SEGS[expense_rate]
        for seg_i, (x_s, x_e, p_idx) in enumerate(segs):
            _, monthly_base = PAUSALNI_DAN[p_idx]
            p_val = _pension(monthly_base, years)
            x_start = max(x_s, MIN_WAGE_TOTAL_COST)
            x_end   = min(x_e, income_max)
            if x_start >= x_end:
                continue
            x_seg = [x_start / 1_000, x_end / 1_000]
            y_seg = [p_val / 1_000, p_val / 1_000]
            ax_top.plot(x_seg, y_seg,
                        color=color, linewidth=2.0, linestyle=":", zorder=2)
            if seg_i < len(segs) - 1 and x_e <= income_max:
                ax_top.axvline(x_e / 1_000, color=color,
                               linewidth=0.5, linestyle=":", alpha=0.4)

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

    # Referenční svislé čáry
    _add_vertical_ref(ax_top, MIN_WAGE_TOTAL_COST / 1_000,
                      f"Min.\u00a0mzda\n({_fmt_czk(MIN_WAGE_TOTAL_COST)})",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax_top, MEDIAN_EMP_TOTAL_COST / 1_000,
                      f"Medián\u00a0(zam.)\n({_fmt_czk(MEDIAN_EMP_TOTAL_COST)})",
                      color="#888888")
    if EMP_RH1_X <= income_max:
        _add_vertical_ref(ax_top, EMP_RH1_X / 1_000,
                          f"1.\u00a0RH\u00a0(zam.)\n({_fmt_czk(EMP_RH1_X)})",
                          color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))
    if EMP_RH2_X <= income_max:
        _add_vertical_ref(ax_top, EMP_RH2_X / 1_000,
                          f"2.\u00a0RH\u00a0(zam.)\n({_fmt_czk(EMP_RH2_X)})",
                          color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))

    ax_top.set_ylabel("Měsíční starobní důchod [tis.\u00a0Kč]")
    ax_top.set_title(
        f"Výše a solidarita starobního důchodu v závislosti na nákladech na práci\n"
        f"(pojistná doba\u00a0{years}\u00a0let, parametry\u00a02026)",
        loc="center",
    )
    ax_top.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax_top.set_ylim(bottom=0)

    # ══════════════════════════════════════════════════════════════════════════
    # DOLNÍ PANEL – náhradový poměr [%] = důchod / x × 100
    # ══════════════════════════════════════════════════════════════════════════
    rr_emp = p_emp_rr / _net_income_emp(x_rr) * 100
    ax_bot.plot(x_rr / 1_000, rr_emp, color=c_emp, linewidth=2.0)

    _RR_CAP = 250.0  # clip extreme ratios at the start of each OSVČ series
    for expense_rate, label, color in OSVC_TYPES:
        p_osvc_rr = pension_osvc_vydajovy(x_rr, expense_rate, years)
        ni_osvc   = _net_income_osvc_vydajovy(x_rr, expense_rate)
        # Mask points where net income ≤ 0 or ratio would exceed display cap
        # (e.g. OSVČ 80 % has negative/tiny net income near min wage causing
        # extreme replacement-rate spikes that distort the y-axis scale).
        rr_raw  = np.where(ni_osvc > 0,
                           p_osvc_rr / np.maximum(ni_osvc, 1.0) * 100,
                           np.nan)
        rr_osvc = np.where(rr_raw <= _RR_CAP, rr_raw, np.nan)
        cap = OSVC_VYDAJOVY_CAP[expense_rate]
        idx = int(np.searchsorted(x_rr, cap, side='right'))
        if idx > 0:
            ax_bot.plot(x_rr[:idx] / 1_000, rr_osvc[:idx],
                        color=color, linewidth=1.5, linestyle="--")
        if idx < len(x_rr):
            start = max(0, idx - 1)
            ax_bot.plot(x_rr[start:] / 1_000, rr_osvc[start:],
                        color=color, linewidth=1.5, linestyle="-.", alpha=0.45)

        segs = PAUSALNI_SEGS[expense_rate]
        for seg_i, (x_s, x_e, p_idx) in enumerate(segs):
            _, monthly_base = PAUSALNI_DAN[p_idx]
            _, total_pay_band = PAUSALNI_DAN_TOTAL[p_idx]
            p_val  = _pension(monthly_base, years)
            x_start = max(x_s, MIN_WAGE_TOTAL_COST)
            x_end   = min(x_e, income_max)
            if x_start >= x_end:
                continue
            x_band  = np.linspace(x_start, x_end, 300)
            rr_band = p_val / np.maximum(x_band - total_pay_band, 1) * 100
            ax_bot.plot(x_band / 1_000, rr_band,
                        color=color, linewidth=2.0, linestyle=":")
            if seg_i < len(segs) - 1 and x_e <= income_max:
                ax_bot.axvline(x_e / 1_000, color=color,
                               linewidth=0.5, linestyle=":", alpha=0.4)

    # Referenční svislé čáry – dolní panel
    _add_vertical_ref(ax_bot, MIN_WAGE_TOTAL_COST / 1_000,
                      "Min.\u00a0mzda",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax_bot, MEDIAN_EMP_TOTAL_COST / 1_000,
                      "Medián\u00a0(zam.)",
                      color="#888888")
    if EMP_RH1_X <= income_max:
        _add_vertical_ref(ax_bot, EMP_RH1_X / 1_000,
                          "1.\u00a0RH\u00a0(zam.)",
                          color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))
    if EMP_RH2_X <= income_max:
        _add_vertical_ref(ax_bot, EMP_RH2_X / 1_000,
                          "2.\u00a0RH\u00a0(zam.)",
                          color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))

    ax_bot.set_xlabel("Celkové náklady zaměstnavatele / příjmy OSVČ [tis.\u00a0Kč/měsíc]")
    ax_bot.set_ylabel("Náhradový poměr (důchod\u00a0/\u00a0čistý\u00a0příjem)\u00a0[%]")
    ax_bot.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax_bot.set_ylim(0, _RR_CAP)

    # Legenda mimo osy – dole pod figúrou; sdílena oběma panely
    legend_handles = [
        Line2D([0], [0], color=c_emp, linewidth=2.0,
               label="Zaměstnanec (celk.\u00a0nákl.)"),
    ]
    for _er, lbl, col in OSVC_TYPES:
        legend_handles.append(
            Line2D([0], [0], color=col, linewidth=1.5, linestyle="--", label=lbl))
    legend_handles.append(
        Line2D([0], [0], color="#888888", linewidth=1.5, linestyle="-.", alpha=0.45,
               label="OSVČ výd.\u00a0paušál nad limitem příjmů"))
    legend_handles.append(
        Line2D([0], [0], color="#555555", linewidth=2.0, linestyle=":",
               label="Paušální daň (tečkovaně, barva dle typu OSVČ)"))
    fig.legend(handles=legend_handles, frameon=False, fontsize=FONT_SIZE - 2,
               loc="lower center", bbox_to_anchor=(0.5, -0.01), ncols=2)

    fig.subplots_adjust(bottom=0.18)
    return fig

if __name__ == "__main__":
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
            r"Náhradový poměr = důchod\,/\,čistý příjem; "
            r"klesající průběh dokládá solidární přerozdělení ve prospěch nižších příjmů. "
            r"Parametry roku~2026, pojistná doba 40~let. "
            r"Výpočet dle zákona č.\,155/1995~Sb., zákona č.\,270/2023~Sb. "
            r"a nařízení vlády č.\,365/2025~Sb."
        ),
        label="fig:cz_pension_solidarity",
        width=r"0.95\linewidth",
    )

    print("Hotovo.")
