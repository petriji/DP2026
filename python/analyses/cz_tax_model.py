r"""Czech tax-wedge model – calculation functions and parametric wedge figure.

Tax wedge definition
--------------------
Daňový klín = podíl daní a odvodů na celkových nákladech práce (zaměstnancův
total labor cost) resp. na příjmech OSVČ.

  • Zaměstnanec: daňový klín = (celk. nákl. − čistá mzda) / celk. nákl.
    Zahrnuje: odvody zaměstnavatele (SP 24,8 % + ZP 9 %) + odvody zaměstnance
    (SP 7,1 % + ZP 4,5 %) + DPFO (15 % / 23 %) − sleva na poplatníka 2 570 Kč/měs.

  • OSVČ – standardní odvody (skutečné výdaje):
    Daňový klín = (SP + ZP + DPFO) / zisk.
    Základ DPFO = zisk − SP − ZP (§ 24/2/e ZDP, SP a ZP jsou odečitatelné
    u skutečných výdajů).
    Sleva na poplatníka 2 570 Kč/měs. uplatněna.

  • OSVČ – výdajový paušál (paušální výdaje):
    Daňový klín = (SP + ZP + DPFO) / příjmy.
    ZD DPFO = příjmy × (1 − sazba paušálu) – SP a ZP NEJSOU odečitatelné
    (ZDP § 7 odst. 7 – paušál vylučuje § 24/2/e).
    Sleva na poplatníka 2 570 Kč/měs. uplatněna.

  • OSVČ – paušální daň pásma 1–3:
    Celková platba je pevná (PAUSALNI_DAN_TOTAL). Sleva na poplatníka je již
    zahrnuta ve výši daňové složky (DPFO v pásmu 1 = 100 Kč = de facto po slevě).
    Daňový klín = celková_platba / příjmy (bez nutnosti separátně počítat DPFO).

SP VZ: 55 % ze základu daně (zákon č. 270/2023 Sb., od 2024).
ZP VZ: 50 % ze základu daně (zákon č. 592/1992 Sb.).

Figure
------
  plot_tax_wedge_comparison() – parametric single panel:
      X-axis: daňový klín [%]
      Y-axis: náhradový poměr [%] = důchod / čistý příjem
      Parameter: income (celkové náklady / příjmy), range ~39–300 tis. Kč/měsíc.
      Output: pics/python/cz_pension_wedge.pdf

Run
---
    python analyses/cz_tax_model.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# ── 2026 tax & levy parameters ────────────────────────────────────────────────
# Sources: zákon č. 586/1992 Sb. (ZDP), č. 589/1992 Sb., č. 592/1992 Sb.

# Průměrná mzda (§ 23b ZPDS; řídí prahové hodnoty ZDP a min. ZP základ)
AVG_WAGE: int = 48_967  # CZK/month (2026)

# Daň z příjmů fyzických osob (§ 16 ZDP)
INCOME_TAX_RATE_LOW: float  = 0.15   # 15 % (do 3× průměrné mzdy/měsíc)
INCOME_TAX_RATE_HIGH: float = 0.23   # 23 % (nad 3× průměrné mzdy/měsíc)
TAX_THRESHOLD_MONTHLY: int  = 3 * AVG_WAGE  # 146 901 Kč/měsíc (2026)

# Základní sleva na poplatníka (§ 35ba odst. 1 písm. a) ZDP)
SLEVA_POPLATNIK_MONTHLY: int = 2_570  # Kč/měsíc (= 30 840 Kč/rok)

# Odvody zaměstnance
# SP zaměstnance: zákon č. 589/1992 Sb. § 7; od 2024 zahrnuje nemocenské (zák. č. 270/2023 Sb.)
EMPLOYEE_PENSION_RATE:  float = 0.065  # 6,5 % důchodové pojištění
EMPLOYEE_SICKNESS_RATE: float = 0.006  # 0,6 % nemocenské pojištění (od 2024)
EMPLOYEE_SOCIAL_RATE:   float = EMPLOYEE_PENSION_RATE + EMPLOYEE_SICKNESS_RATE  # 7,1 % celkem
EMPLOYEE_HEALTH_RATE:   float = 0.045  # 4,5 % z hrubé mzdy (ZP, § 2 zák. č. 592/1992 Sb.)

# Odvody OSVČ
OSVC_ZP_BASE_RATIO:   float = 0.50   # ZP VZ = 50 % ze ZD (§ 3a zák. č. 592/1992 Sb.)
OSVC_SOCIAL_RATE:     float = 0.292  # 29,2 % z VZ SP (§ 7b zák. č. 589/1992 Sb.)
OSVC_HEALTH_RATE:     float = 0.135  # 13,5 % z VZ ZP (§ 3 zák. č. 592/1992 Sb.)
OSVC_MIN_HEALTH_BASE: int   = AVG_WAGE // 2  # 24 483 Kč/měsíc (2026; = 50 % prům. mzdy)

# ── Odvody zaměstnavatele / OSVČ ─────────────────────────────────────────────
# Sources: zákon č. 589/1992 Sb. (SP), zákon č. 592/1992 Sb. (ZP), č. 270/2023 Sb.
EMPLOYER_INS_RATE: float   = 0.338   # 33,8 % z hrubé mzdy (SP 24,8 % + ZP 9,0 %)
OSVC_BASE_RATIO: float     = 0.55    # SP VZ = 55 % ze základu daně (od 2024)
OSVC_MIN_MONTHLY_BASE: int = 19_587  # min. VZ pro SP (hlavní činn., 2026 = 40 % prům. mzdy)

# ── Paušální daň ──────────────────────────────────────────────────────────────
# Zákon č. 586/1992 Sb., § 2a. Formát: (max_příjem_Kč/měs., základ_Kč/měs.)
PAUSALNI_DAN: list[tuple[int, int]] = [
    (83_333,  22_527),   # pásmo 1: příjmy ≤ 1 000 000 Kč/rok
    (125_000, 28_050),   # pásmo 2: příjmy ≤ 1 500 000 Kč/rok
    (166_667, 42_900),   # pásmo 3: příjmy ≤ 2 000 000 Kč/rok
]

# Formát: (max_příjem_Kč/měs., celková_platba_Kč/měs.)
PAUSALNI_DAN_TOTAL: list[tuple[int, int]] = [
    (83_333,   9_984),   # pásmo 1: daň 100 + soc. 6 578 + zdrav. 3 306
    (125_000, 16_745),   # pásmo 2: daň 4 963 + soc. 8 191 + zdrav. 3 591
    (166_667, 27_139),   # pásmo 3: daň 9 320 + soc. 12 527 + zdrav. 5 292
]

# ── DPH ───────────────────────────────────────────────────────────────────────
# Zákon č. 235/2004 Sb., § 6. OSVČ plátce DPH nad 2 000 000 Kč/rok.
DPH_RATE: float            = 0.21     # základní sazba DPH: 21 %
DPH_THRESHOLD_MONTHLY: int = 166_666  # 2 000 000 Kč/rok ÷ 12 ≈ 166 666 Kč/měs.


def _revenue_after_dph(client_payment: np.ndarray | float) -> np.ndarray | float:
    """Skutečný příjem OSVČ po odvodu DPH (zákon č. 235/2004 Sb., § 6).

    Nad prahem obratu 2 000 000 Kč/rok (DPH_THRESHOLD_MONTHLY měsíčně) je OSVČ
    plátcem DPH.  Z platby klienta X si ponechá X / (1 + DPH_RATE); zbytek
    odvádí jako DPH.  Pod prahem klient platí cenu služby přímo (bez DPH).
    """
    x = np.asarray(client_payment, dtype=float)
    return np.where(x > DPH_THRESHOLD_MONTHLY, x / (1 + DPH_RATE), x)


# ── Výpočetní funkce ──────────────────────────────────────────────────────────

def tax_wedge_employee(total_labor_cost: np.ndarray | float) -> np.ndarray | float:
    """Efektivní daňový klín zaměstnance [%] z celkových nákladů zaměstnavatele.

    Daňový klín = (celkové náklady − čistá mzda) / celkové náklady × 100.

    Celkové náklady = hrubá mzda × (1 + EMPLOYER_INS_RATE).
    Čistá mzda = hrubá − pojistné zaměstnance (SP 7,1 % + ZP 4,5 %) − DPFO.
    Základ DPFO = hrubá mzda (§ 6 odst. 12 ZDP; bez superhrubé od 2021).
    Sleva na poplatníka (2 570 Kč/měs.) odečtena od DPFO.
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
    """Efektivní daňový klín OSVČ se standardními odvody (skutečné výdaje) [%].

    Daňový klín = (SP + ZP + DPFO) / zisk × 100.

    Pro skutečné výdaje: SP a ZP jsou odečitatelné od základu daně DPFO
    (§ 24 odst. 2 písm. e) ZDP).
    SP VZ = max(55 % × zisk, min. základ) – zákon č. 270/2023 Sb. (od 2024).
    ZP VZ = max(50 % × zisk, min. základ) – zákon č. 592/1992 Sb.
    Sleva na poplatníka (2 570 Kč/měs.) odečtena od DPFO.
    """
    x = np.asarray(profit, dtype=float)
    social_base = np.maximum(OSVC_BASE_RATIO * x, OSVC_MIN_MONTHLY_BASE)
    health_base = np.maximum(OSVC_ZP_BASE_RATIO * x, OSVC_MIN_HEALTH_BASE)
    social = OSVC_SOCIAL_RATE * social_base
    health = OSVC_HEALTH_RATE * health_base
    # Pro skutečné výdaje: SP + ZP odečitatelné od ZD DPFO (§ 24/2/e ZDP)
    zdane = np.maximum(x - social - health, 0.0)
    dan_raw = (
        np.minimum(zdane, TAX_THRESHOLD_MONTHLY) * INCOME_TAX_RATE_LOW
        + np.maximum(zdane - TAX_THRESHOLD_MONTHLY, 0) * INCOME_TAX_RATE_HIGH
    )
    dan = np.maximum(dan_raw - SLEVA_POPLATNIK_MONTHLY, 0)
    return (social + health + dan) / x * 100


def tax_wedge_osvc_vydajovy(revenue: np.ndarray | float,
                             expense_rate: float) -> np.ndarray | float:
    """Efektivní daňový klín OSVČ s výdajovým paušálem [%] z příjmů.

    Daňový klín = (SP + ZP + DPFO) / příjmy × 100.

    Výdajový paušál nahrazuje skutečné výdaje, takže SP a ZP NEJSOU
    odečitatelné od základu daně DPFO (ZDP § 7 odst. 7 – uplatnění paušálu
    vylučuje současné uplatnění § 24/2/e). Základ DPFO = příjmy × (1 − sazba).

    SP VZ = max(55 % × ZD, min. základ) – zákon č. 270/2023 Sb. (od 2024).
    ZP VZ = max(50 % × ZD, min. základ) – zákon č. 592/1992 Sb.
    Sleva na poplatníka (2 570 Kč/měs.) odečtena od DPFO.
    """
    x = np.asarray(revenue, dtype=float)
    actual_rev = _revenue_after_dph(x)           # příjmy po DPH (= x pod prahem)
    zd = (1.0 - expense_rate) * actual_rev       # základ daně = zisk (paušální výdaje)
    social_base = np.maximum(OSVC_BASE_RATIO * zd, OSVC_MIN_MONTHLY_BASE)
    health_base = np.maximum(OSVC_ZP_BASE_RATIO * zd, OSVC_MIN_HEALTH_BASE)
    social = OSVC_SOCIAL_RATE * social_base
    health = OSVC_HEALTH_RATE * health_base
    # ZD DPFO = paušální zisk; SP a ZP nejsou odečitatelné (viz docstring)
    dan_raw = (
        np.minimum(zd, TAX_THRESHOLD_MONTHLY) * INCOME_TAX_RATE_LOW
        + np.maximum(zd - TAX_THRESHOLD_MONTHLY, 0) * INCOME_TAX_RATE_HIGH
    )
    dan = np.maximum(dan_raw - SLEVA_POPLATNIK_MONTHLY, 0)
    dph = x - actual_rev                         # DPH odváděné státu (0 pod prahem)
    return (social + health + dan + dph) / x * 100


def tax_breakdown(
    income: float,
    mode: Literal["employee", "osvc_vydajovy", "osvc_pausalni"] = "employee",
    expense_rate: float = 0.60,
    pausalni_pasmo: int | None = None,
) -> dict[str, float]:
    """Vrátí itemizovaný rozpad daní a odvodů pro daný příjem a scénář.

    Umožňuje srovnání daňové a odvodové zátěže pro zaměstnance vs. OSVČ při
    stejné výši příjmů / celkových nákladů zaměstnavatele.

    Parameters
    ----------
    income : float
        Pro mode='employee': celkové náklady zaměstnavatele [Kč/měsíc]
        (= hrubá_mzda × 1,338).
        Pro mode='osvc_vydajovy' nebo 'osvc_pausalni': měsíční příjmy
        (revenue) OSVČ [Kč/měsíc].
    mode : str
        Scénář výpočtu:
        - 'employee': zaměstnanec (odvody zaměstnavatele + zaměstnance + DPFO).
        - 'osvc_vydajovy': OSVČ s výdajovým paušálem (sazba dle expense_rate).
          Sleva na poplatníka uplatněna.
        - 'osvc_pausalni': OSVČ v paušálním daňovém režimu (pásmo dle
          pausalni_pasmo). Celková platba je pevná; sleva na poplatníka je již
          zahrnuta v daňové složce paušální platby.
    expense_rate : float
        Sazba výdajového paušálu (0,40 / 0,60 / 0,80); pouze pro
        mode='osvc_vydajovy'.
    pausalni_pasmo : int | None
        Pásmo paušální daně (1, 2 nebo 3); vyžadováno pro mode='osvc_pausalni'.

    Returns
    -------
    dict s klíči:
        income          – vstupní příjem / náklady [Kč/měs.]
        zd              – základ daně DPFO [Kč/měs.]
        employer_sp     – SP zaměstnavatele (jen employee) [Kč/měs.]
        employer_zp     – ZP zaměstnavatele (jen employee) [Kč/měs.]
        sp_vz           – SP vyměřovací základ [Kč/měs.]
        sp              – sociální pojistné [Kč/měs.]
        zp_vz           – ZP vyměřovací základ [Kč/měs.]
        zp              – zdravotní pojistné [Kč/měs.]
        dpfo_base       – základ DPFO po případném odpočtu SP/ZP [Kč/měs.]
        dpfo_gross      – DPFO před slevou na poplatníka [Kč/měs.]
        sleva_poplatnik – uplatněná sleva na poplatníka [Kč/měs.]
        dpfo_net        – DPFO po slevě [Kč/měs.]
        total_charges   – celkové odvody + daň [Kč/měs.]
        net_income      – čistý příjem (od ZD po odečtení SP+ZP+DPFO) [Kč/měs.]
        tax_wedge_pct   – daňový klín [%]
        note            – poznámka k výpočtu
    """
    r: dict[str, float] = {
        "income":           income,
        "zd":               0.0,
        "employer_sp":      0.0,
        "employer_zp":      0.0,
        "sp_vz":            0.0,
        "sp":               0.0,
        "zp_vz":            0.0,
        "zp":               0.0,
        "dpfo_base":        0.0,
        "dpfo_gross":       0.0,
        "sleva_poplatnik":  0.0,
        "dpfo_net":         0.0,
        "total_charges":    0.0,
        "net_income":       0.0,
        "tax_wedge_pct":    0.0,
        "note":             "",
    }

    if mode == "employee":
        gross = income / (1 + EMPLOYER_INS_RATE)
        r["zd"]          = gross
        r["employer_sp"] = gross * 0.248   # SP zaměstnavatel: 24,8 %
        r["employer_zp"] = gross * 0.090   # ZP zaměstnavatel: 9,0 %
        r["sp_vz"]       = gross
        r["sp"]          = EMPLOYEE_SOCIAL_RATE * gross   # SP zaměstnanec: 7,1 %
        r["zp_vz"]       = gross
        r["zp"]          = EMPLOYEE_HEALTH_RATE * gross   # ZP zaměstnanec: 4,5 %
        r["dpfo_base"]   = gross                          # základ DPFO = hrubá mzda
        dpfo_raw = (
            min(gross, TAX_THRESHOLD_MONTHLY) * INCOME_TAX_RATE_LOW
            + max(gross - TAX_THRESHOLD_MONTHLY, 0) * INCOME_TAX_RATE_HIGH
        )
        r["dpfo_gross"]      = dpfo_raw
        r["sleva_poplatnik"] = min(dpfo_raw, SLEVA_POPLATNIK_MONTHLY)
        r["dpfo_net"]        = max(dpfo_raw - SLEVA_POPLATNIK_MONTHLY, 0)
        r["total_charges"]   = income - (gross - r["sp"] - r["zp"] - r["dpfo_net"])
        r["net_income"]      = gross - r["sp"] - r["zp"] - r["dpfo_net"]
        r["tax_wedge_pct"]   = r["total_charges"] / income * 100
        r["note"] = (
            "ZD DPFO = hrubá mzda; sleva na poplatníka uplatněna. "
            "Daňový klín zahrnuje odvody zaměstnavatele i zaměstnance."
        )

    elif mode == "osvc_vydajovy":
        actual_rev = float(_revenue_after_dph(float(income)))
        dph = income - actual_rev                    # DPH odváděné státu (0 pod prahem)
        zd = (1.0 - expense_rate) * actual_rev       # základ daně = paušální zisk
        sp_vz = max(OSVC_BASE_RATIO * zd, OSVC_MIN_MONTHLY_BASE)
        zp_vz = max(OSVC_ZP_BASE_RATIO * zd, OSVC_MIN_HEALTH_BASE)
        sp    = OSVC_SOCIAL_RATE * sp_vz
        zp    = OSVC_HEALTH_RATE * zp_vz
        # Výdajový paušál: SP a ZP NEodečitatelné od ZD DPFO (ZDP § 7 odst. 7)
        dpfo_base = zd
        dpfo_raw  = (
            min(dpfo_base, TAX_THRESHOLD_MONTHLY) * INCOME_TAX_RATE_LOW
            + max(dpfo_base - TAX_THRESHOLD_MONTHLY, 0) * INCOME_TAX_RATE_HIGH
        )
        r["zd"]              = zd
        r["sp_vz"]           = sp_vz
        r["sp"]              = sp
        r["zp_vz"]           = zp_vz
        r["zp"]              = zp
        r["dpfo_base"]       = dpfo_base
        r["dpfo_gross"]      = dpfo_raw
        r["sleva_poplatnik"] = min(dpfo_raw, SLEVA_POPLATNIK_MONTHLY)
        r["dpfo_net"]        = max(dpfo_raw - SLEVA_POPLATNIK_MONTHLY, 0)
        r["dph"]             = dph
        r["total_charges"]   = sp + zp + r["dpfo_net"] + dph
        r["net_income"]      = zd - sp - zp - r["dpfo_net"]
        r["tax_wedge_pct"]   = r["total_charges"] / income * 100
        dph_note = (
            f" DPH 21 % ({dph:,.0f} Kč/měs.) zahrnuto – OSVČ plátce DPH."
            if dph > 0 else ""
        )
        r["note"] = (
            f"Výdajový paušál {expense_rate*100:.0f}% = uznatelné výdaje; "
            f"ZD DPFO = {(1-expense_rate)*100:.0f}% příjmů (zisk po paušálu). "
            "SP a ZP nejsou odečitatelné od ZD DPFO (ZDP §7/7). "
            "Sleva na poplatníka uplatněna."
            + dph_note
        )

    elif mode == "osvc_pausalni":
        if pausalni_pasmo is None or pausalni_pasmo not in (1, 2, 3):
            raise ValueError("pausalni_pasmo must be 1, 2 or 3 for mode='osvc_pausalni'")
        idx = pausalni_pasmo - 1
        max_inc, sp_vz_fixed = PAUSALNI_DAN[idx]
        _,       total_pay   = PAUSALNI_DAN_TOTAL[idx]
        # Celková pevná platba = SP + ZP + DPFO (sleva na poplatníka již zahrnutá)
        sp = OSVC_SOCIAL_RATE * sp_vz_fixed
        # ZP = total_pay - sp - dpfo_net_pausalni
        # Dopočet: PAUSALNI_DAN_TOTAL obsahuje net DPFO, ZP vypočítáme jako zbytek
        # (viz komentář v konstantách: pásmo1: 100 daň + 6578 soc + 3306 zdrav = 9984)
        zp_map   = [3_306, 3_591, 5_292]        # ZP pevně na pásmo 1/2/3
        dpfo_net_pausalni = [100, 4_963, 9_320]  # DPFO (po slevě) na pásmo 1/2/3
        zp       = zp_map[idx]
        dpfo_net = dpfo_net_pausalni[idx]
        r["zd"]              = float(sp_vz_fixed)   # OVZ = pevný základ důchodového poj.
        r["sp_vz"]           = float(sp_vz_fixed)
        r["sp"]              = sp
        r["zp_vz"]           = float(zp / OSVC_HEALTH_RATE)  # přibližný ZP VZ
        r["zp"]              = float(zp)
        r["dpfo_base"]       = float("nan")        # základ DPFO pro paušál není odvozen
        r["dpfo_gross"]      = float("nan")        # ze skutečného příjmu
        r["sleva_poplatnik"] = float("nan")        # sleva zahrnuta ve výši DPFO
        r["dpfo_net"]        = float(dpfo_net)
        r["total_charges"]   = float(total_pay)
        r["net_income"]      = income - total_pay  # čistý příjem = příjmy − pevná platba
        r["tax_wedge_pct"]   = total_pay / income * 100
        r["note"] = (
            f"paušální daň pásmo {pausalni_pasmo}: celková platba {total_pay} Kč/měs. "
            f"(max. příjem {max_inc} Kč/měs.). "
            "Sleva na poplatníka je zahrnuta ve výši DPFO složky paušálu."
        )
    else:
        raise ValueError(f"Unknown mode: {mode!r}. Use 'employee', 'osvc_vydajovy' or 'osvc_pausalni'.")

    return r


# ── Pomocné výpočetní funkce pro nové obrázky ─────────────────────────────────

def net_income_employee(total_labor_cost: np.ndarray | float) -> np.ndarray | float:
    """Čistý příjem zaměstnance (odchozí mzda) z celkových nákladů zaměstnavatele.

    Čistý příjem = hrubá mzda − SP zaměstnance − ZP zaměstnance − DPFO (po slevě).
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
    return gross - employee_social - employee_health - dan


def net_income_osvc_vydajovy(revenue: np.ndarray | float,
                              expense_rate: float) -> np.ndarray | float:
    """Čistý příjem OSVČ s výdajovým paušálem po odvedení SP, ZP a DPFO.

    Čistý příjem = základ daně (ZD) − SP − ZP − DPFO (po slevě).
    ZD = příjmy × (1 − sazba paušálu).

    Výdajový paušál nahrazuje skutečné výdaje; výsledný čistý příjem je
    tedy příjem po zaplacení daní a pojistného, při uvažování paušálních
    výdajů jako skutečných nákladů.
    SP a ZP NEJSOU odečitatelné od ZD DPFO (ZDP § 7 odst. 7).
    """
    x = np.asarray(revenue, dtype=float)
    actual_rev = _revenue_after_dph(x)
    zd = (1.0 - expense_rate) * actual_rev
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


def sp_employee(total_labor_cost: np.ndarray | float) -> np.ndarray | float:
    """Celkové sociální pojistné zaměstnance + zaměstnavatele [Kč/měs.].

    Zahrnuje:
      • SP zaměstnance: 7,1 % z hrubé mzdy
      • SP zaměstnavatele: 24,8 % z hrubé mzdy
    Celkem: 31,9 % z hrubé mzdy = 31,9 / 133,8 × celkové náklady.
    """
    x = np.asarray(total_labor_cost, dtype=float)
    gross = x / (1 + EMPLOYER_INS_RATE)
    return (0.248 + EMPLOYEE_SOCIAL_RATE) * gross


def sp_osvc_vydajovy(revenue: np.ndarray | float,
                     expense_rate: float) -> np.ndarray | float:
    """Sociální pojistné OSVČ s výdajovým paušálem [Kč/měs.].

    SP = 29,2 % × max(55 % × ZD, min. základ).
    ZD = příjmy × (1 − sazba paušálu).
    """
    x = np.asarray(revenue, dtype=float)
    actual_rev = _revenue_after_dph(x)
    zd = (1.0 - expense_rate) * actual_rev
    social_base = np.maximum(OSVC_BASE_RATIO * zd, OSVC_MIN_MONTHLY_BASE)
    return OSVC_SOCIAL_RATE * social_base

