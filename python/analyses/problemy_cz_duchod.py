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

Reduction (§ 15 ZPDS, zákon č. 270/2023 Sb.):
    ROVZ = min(OVZ, RH1) × 0.99
         + max(min(OVZ, RH2) − RH1, 0) × 0.26
         + max(OVZ − RH2, 0) × 0.00   # nad RH2 se nezapočítává

Figures
-------
  plot_pension_comparison() – single panel: monthly pension vs x-axis cost.
      Output: pics/python/problemy_duchod_prijem.pdf

  plot_pension_solidarity()  – two panels:
      Top:    monthly pension (tis. Kč) – absolute values
      Bottom: replacement rate (%) = pension / x – the declining slope shows
              the solidarity mechanism; lower earners receive proportionally more.
      Output: pics/python/problemy_duchod_solidarita.pdf

Run
---
    python analyses/cz_pension_model.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))


# ── 2026 statutory parameters ─────────────────────────────────────────────────
# Sources: zákon č. 155/1995 Sb. (ZPDS), zákon č. 270/2023 Sb. (důchodová reforma),
#          nařízení vlády č. 365/2025 Sb. (platné pro rok 2026).

# Základní výměra starobního důchodu (§ 33 ZPDS)
ZAKLADNI_VYMERA: int = 4_900  # CZK/month (2026)

# Redukční hranice osobního vyměřovacího základu (§ 15 ZPDS)
RH1: int = 21_546   # 1. redukční hranice [CZK/month] (2026)
RH2: int = 195_868  # 2. redukční hranice [CZK/month] (2026)

# Sazba procentní výměry za rok pojištění (§ 34 ZPDS)
# Od roku 2026 se postupně snižuje z 1,5 % na 1,45 % (do roku 2035).
PCT_PER_YEAR: float = 0.01495  # 1,495 % z ROVZ za každý rok pojistné doby (2026)

# Předpokládaná pojistná doba (roky)
INSURANCE_YEARS: int = 40

# Minimální procentní výměra (§ 34 odst. 1 ZPDS)
MIN_PROCENTNI_VYMERA: int = 4_900  # CZK/month (2026; navázáno na min. mzdu)

# Celková minimální výše důchodu (základní výměra + min. procentní výměra)
MIN_TOTAL_PENSION: int = ZAKLADNI_VYMERA + MIN_PROCENTNI_VYMERA  # CZK/month


# ── Shared levy parameters and DPH helper (defined in cz_tax_model) ────────
from cz_tax_model import (
    EMPLOYER_INS_RATE,
    OSVC_BASE_RATIO,
    OSVC_MIN_MONTHLY_BASE,
    PAUSALNI_DAN,
    _revenue_after_dph,
)

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
        # nad RH2 se nezapočítává
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
    actual_rev = _revenue_after_dph(rev)
    profit = (1.0 - expense_rate) * actual_rev
    ovz = np.maximum(OSVC_BASE_RATIO * profit, OSVC_MIN_MONTHLY_BASE)
    return _pension(ovz, years)

