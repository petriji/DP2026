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

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from config import FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.style import apply_style, cm2in, save_figure_tex, savefig

# Import shared 2026 parameters and pension/helper functions
from cz_pension_model import (
    AVG_WAGE,
    EMPLOYER_INS_RATE,
    INSURANCE_YEARS,
    INCOME_TAX_RATE_LOW,
    INCOME_TAX_RATE_HIGH,
    TAX_THRESHOLD_MONTHLY,
    SLEVA_POPLATNIK_MONTHLY,
    EMPLOYEE_SOCIAL_RATE,
    EMPLOYEE_HEALTH_RATE,
    OSVC_BASE_RATIO,
    OSVC_ZP_BASE_RATIO,
    OSVC_SOCIAL_RATE,
    OSVC_HEALTH_RATE,
    OSVC_MIN_MONTHLY_BASE,
    OSVC_MIN_HEALTH_BASE,
    OSVC_VYDAJOVY_CAP,
    PAUSALNI_DAN,
    PAUSALNI_DAN_TOTAL,
    PAUSALNI_SEGS,
    MIN_WAGE_TOTAL_COST,
    MEDIAN_EMP_TOTAL_COST,
    IT_MEDIAN_TOTAL_COST,
    POVERTY_THRESHOLD,
    OSVC_TYPES,
    PASMO_COLORS,
    _add_vertical_ref,
    _fmt_czk,
    _pension,
    pension_employee,
    pension_osvc_vydajovy,
)


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
    zd = (1.0 - expense_rate) * x               # základ daně = zisk (paušální výdaje)
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
    return (social + health + dan) / x * 100


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
        zd = (1.0 - expense_rate) * income          # základ daně = paušální zisk
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
        r["total_charges"]   = sp + zp + r["dpfo_net"]
        r["net_income"]      = zd - sp - zp - r["dpfo_net"]
        r["tax_wedge_pct"]   = r["total_charges"] / income * 100
        r["note"] = (
            f"Výdajový paušál {expense_rate*100:.0f}% = uznatelné výdaje; "
            f"ZD DPFO = {(1-expense_rate)*100:.0f}% příjmů (zisk po paušálu). "
            "SP a ZP nejsou odečitatelné od ZD DPFO (ZDP §7/7). "
            "Sleva na poplatníka uplatněna."
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
            f"Paušální daň pásmo {pausalni_pasmo}: celková platba {total_pay} Kč/měs. "
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


def _plot_osvc_lines(
    ax: plt.Axes,
    x: np.ndarray,
    fn_osvc,
    fn_pausalni,
    income_max: int,
) -> None:
    """Pomocná funkce: vykreslí křivky pro všechny typy OSVČ (standardní + paušální).

    fn_osvc(x, expense_rate) → y hodnoty pro standardní odvody.
    fn_pausalni(x_band, total_pay, i) → y hodnoty pro paušální daň pásmo i.
    """
    for expense_rate, _label, color in OSVC_TYPES:
        y_osvc = fn_osvc(x, expense_rate)
        cap = OSVC_VYDAJOVY_CAP[expense_rate]
        idx = int(np.searchsorted(x, cap, side='right'))
        if idx > 0:
            ax.plot(x[:idx] / 1_000, y_osvc[:idx],
                    color=color, linewidth=1.5, linestyle="--", zorder=3)
        if idx < len(x):
            start = max(0, idx - 1)
            ax.plot(x[start:] / 1_000, y_osvc[start:],
                    color=color, linewidth=1.5, linestyle="-.", alpha=0.45, zorder=3)

        segs = PAUSALNI_SEGS[expense_rate]
        for seg_i, (x_s, x_e, p_idx) in enumerate(segs):
            _, total_pay = PAUSALNI_DAN_TOTAL[p_idx]
            x_start = max(x_s, MIN_WAGE_TOTAL_COST)
            x_end   = min(x_e, income_max)
            if x_start >= x_end:
                continue
            x_band = np.linspace(x_start, x_end, 300)
            y_band = fn_pausalni(x_band, total_pay, p_idx)
            ax.plot(x_band / 1_000, y_band,
                    color=color, linewidth=2.0, linestyle=":", zorder=2)
            if seg_i < len(segs) - 1 and x_e <= income_max:
                ax.axvline(x_e / 1_000, color=color,
                           linewidth=0.5, linestyle=":", alpha=0.4)


def _bottom_legend(fig: plt.Figure, c_emp: str) -> None:
    """Přidá sdílenou legendu dole mimo osy (stejný formát jako v cz_pension_model)."""
    fig.subplots_adjust(bottom=0.20)
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


def plot_tax_wedge_vs_income(
    income_max: int = 250_000,
) -> plt.Figure:
    """Obrázek: efektivní daňový klín [%] v závislosti na příjmech / nákladech.

    Osa x = celkové náklady zaměstnavatele / příjmy OSVČ [tis. Kč/měsíc].
    Osa y = efektivní daňový klín [%] = (SP + ZP + DPFO) / příjmy × 100.

    Pro zaměstnance zahrnuje odvody zaměstnavatele i zaměstnance.
    Pro OSVČ s výdajovým paušálem SP a ZP nejsou odečitatelné od ZD DPFO
    (ZDP § 7 odst. 7). Sleva na poplatníka 2 570 Kč/měs. uplatněna.
    """
    x = np.linspace(MIN_WAGE_TOTAL_COST, income_max, 2_000)
    c_emp = PALETTE[0]
    tw_emp = tax_wedge_employee(x)

    fig, ax = plt.subplots(figsize=cm2in(16, 10))

    ax.plot(x / 1_000, tw_emp, color=c_emp, linewidth=2.0, zorder=3)

    _plot_osvc_lines(
        ax, x,
        fn_osvc=lambda x_v, er: tax_wedge_osvc_vydajovy(x_v, er),
        fn_pausalni=lambda x_b, tp, _i: tp / x_b * 100,
        income_max=income_max,
    )

    # Referenční svislé čáry
    _add_vertical_ref(ax, MIN_WAGE_TOTAL_COST / 1_000,
                      f"Min.\u00a0mzda\n({_fmt_czk(MIN_WAGE_TOTAL_COST)})",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax, MEDIAN_EMP_TOTAL_COST / 1_000,
                      f"Medián\u00a0(zam.)\n({_fmt_czk(MEDIAN_EMP_TOTAL_COST)})",
                      color="#888888")
    _add_vertical_ref(ax, IT_MEDIAN_TOTAL_COST / 1_000,
                      f"Medián\u00a0ICT\u00a0(ISCO\u00a025)\n({_fmt_czk(IT_MEDIAN_TOTAL_COST)})",
                      color="#1a7abf")

    ax.set_xlabel("Celkové náklady zaměstnavatele / příjmy OSVČ [tis.\u00a0Kč/měsíc]")
    ax.set_ylabel("Efektivní daňový klín [%]")
    ax.set_title(
        "Efektivní daňový klín v závislosti na příjmech / nákladech na práci\n"
        "(parametry\u00a02026)",
        loc="center",
    )
    ax.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax.set_ylim(bottom=0)

    # Inline popisky křivek – umístěny na pravém konci každé křivky
    x_end = float(income_max)
    tw_end_emp = float(tax_wedge_employee(x_end))
    ax.annotate("Zam.", (x_end / 1_000, tw_end_emp),
                xytext=(4, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color=c_emp, va="center")

    for expense_rate, _label, color in OSVC_TYPES:
        tw_end_o = float(tax_wedge_osvc_vydajovy(x_end, expense_rate))
        osvc_label = f"OSVČ\u00a0{int(expense_rate * 100)}\u202f%"
        ax.annotate(osvc_label, (x_end / 1_000, tw_end_o),
                    xytext=(4, 0), textcoords="offset points",
                    fontsize=FONT_SIZE - 2, color=color, va="center")

    # Paušální pásmo – popisky na konci každého pásma; barva dle OSVČ typu
    labeled_pidx2: set[int] = set()
    for expense_rate, _label, color in OSVC_TYPES:
        segs = PAUSALNI_SEGS[expense_rate]
        for x_s, x_e, p_idx in segs:
            if p_idx in labeled_pidx2:
                continue
            total_pay = PAUSALNI_DAN_TOTAL[p_idx][1]
            x_lab = float(min(income_max, x_e))
            tw_lab = float(total_pay) / x_lab * 100
            ax.annotate(f"Paušál\u00a0{p_idx + 1}", (x_lab / 1_000, tw_lab),
                        xytext=(4, 0), textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color=color, va="center")
            labeled_pidx2.add(p_idx)

    return fig


def plot_net_income_vs_income(
    income_max: int = 250_000,
) -> plt.Figure:
    """Obrázek: čistý příjem [tis. Kč] v závislosti na příjmech / nákladech.

    Osa x = celkové náklady zaměstnavatele / příjmy OSVČ [tis. Kč/měsíc].
    Osa y = čistý příjem [tis. Kč/měsíc].

    Zaměstnanec: čistý = hrubá mzda − SP − ZP − DPFO.
    OSVČ s výdajovým paušálem: čistý = ZD − SP − ZP − DPFO
        (ZD = příjmy × (1 − sazba paušálu); paušální výdaje nejsou součástí čistého).
    OSVČ paušální daň: čistý = příjmy − celková pevná platba
        (skutečné výdaje nejsou modelovány).
    """
    x = np.linspace(MIN_WAGE_TOTAL_COST, income_max, 2_000)
    c_emp = PALETTE[0]
    ni_emp = net_income_employee(x)

    fig, ax = plt.subplots(figsize=cm2in(16, 10))

    ax.plot(x / 1_000, ni_emp / 1_000, color=c_emp, linewidth=2.0, zorder=3)

    _plot_osvc_lines(
        ax, x,
        fn_osvc=lambda x_v, er: net_income_osvc_vydajovy(x_v, er) / 1_000,
        fn_pausalni=lambda x_b, tp, _i: (x_b - tp) / 1_000,
        income_max=income_max,
    )

    # Referenční svislé čáry
    _add_vertical_ref(ax, MIN_WAGE_TOTAL_COST / 1_000,
                      f"Min.\u00a0mzda\n({_fmt_czk(MIN_WAGE_TOTAL_COST)})",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax, MEDIAN_EMP_TOTAL_COST / 1_000,
                      f"Medián\u00a0(zam.)\n({_fmt_czk(MEDIAN_EMP_TOTAL_COST)})",
                      color="#888888")
    _add_vertical_ref(ax, IT_MEDIAN_TOTAL_COST / 1_000,
                      f"Medián\u00a0ICT\u00a0(ISCO\u00a025)\n({_fmt_czk(IT_MEDIAN_TOTAL_COST)})",
                      color="#1a7abf")

    ax.set_xlabel("Celkové náklady zaměstnavatele / příjmy OSVČ [tis.\u00a0Kč/měsíc]")
    ax.set_ylabel("Čistý příjem [tis.\u00a0Kč/měsíc]")
    ax.set_title(
        "Čistý příjem v závislosti na příjmech / nákladech na práci\n"
        "(parametry\u00a02026; OSVČ s výdajovým paušálem: po odečtení paušálních výdajů)",
        loc="center",
    )
    ax.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax.set_ylim(bottom=0)

    # Hranice chudoby
    poverty_kczk = POVERTY_THRESHOLD / 1_000
    ax.axhline(poverty_kczk, color="#aa0000", linewidth=0.8,
               linestyle=(0, (3, 4)), alpha=0.7, zorder=1)
    ax.annotate(
        f"Hranice chudoby ({_fmt_czk(POVERTY_THRESHOLD)}, 2025)",
        xy=(MIN_WAGE_TOTAL_COST / 1_000, poverty_kczk),
        xytext=(3, 4), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color="#aa0000", va="bottom",
    )

    _bottom_legend(fig, c_emp)
    return fig


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
    zd = (1.0 - expense_rate) * x
    social_base = np.maximum(OSVC_BASE_RATIO * zd, OSVC_MIN_MONTHLY_BASE)
    return OSVC_SOCIAL_RATE * social_base


def plot_sp_vs_income(
    income_max: int = 250_000,
) -> plt.Figure:
    """Obrázek: měsíční odvody na SP [tis. Kč] v závislosti na příjmech / nákladech.

    Osa x = celkové náklady zaměstnavatele / příjmy OSVČ [tis. Kč/měsíc].
    Osa y = měsíční odvody na sociální pojistné [tis. Kč/měsíc].

    Zaměstnanec: SP zaměstnance (7,1 %) + SP zaměstnavatele (24,8 %) = 31,9 % z hrubé.
    OSVČ: SP = 29,2 % × max(55 % × ZD, min. základ).
    Paušální daň: SP = 29,2 % × pevný vyměřovací základ pásma.
    """
    x = np.linspace(MIN_WAGE_TOTAL_COST, income_max, 2_000)
    c_emp = PALETTE[0]
    sp_emp = sp_employee(x) / 1_000

    fig, ax = plt.subplots(figsize=cm2in(16, 10))
    ax.plot(x / 1_000, sp_emp, color=c_emp, linewidth=2.0, zorder=3)

    _plot_osvc_lines(
        ax, x,
        fn_osvc=lambda x_v, er: sp_osvc_vydajovy(x_v, er) / 1_000,
        fn_pausalni=lambda x_b, _tp, i: np.full_like(
            x_b, OSVC_SOCIAL_RATE * PAUSALNI_DAN[i][1] / 1_000),
        income_max=income_max,
    )

    _add_vertical_ref(ax, MIN_WAGE_TOTAL_COST / 1_000,
                      f"Min.\u00a0mzda\n({_fmt_czk(MIN_WAGE_TOTAL_COST)})",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax, MEDIAN_EMP_TOTAL_COST / 1_000,
                      f"Medián\u00a0(zam.)\n({_fmt_czk(MEDIAN_EMP_TOTAL_COST)})",
                      color="#888888")
    _add_vertical_ref(ax, IT_MEDIAN_TOTAL_COST / 1_000,
                      f"Medián\u00a0ICT\u00a0(ISCO\u00a025)\n({_fmt_czk(IT_MEDIAN_TOTAL_COST)})",
                      color="#1a7abf")

    ax.set_xlabel("Celkové náklady zaměstnavatele / příjmy OSVČ [tis.\u00a0Kč/měsíc]")
    ax.set_ylabel("Odvody na SP [tis.\u00a0Kč/měsíc]")
    ax.set_title(
        "Odvody na sociální pojistné v závislosti na příjmech / nákladech na práci\n"
        "(parametry\u00a02026; zaměstnanec: SP zaměstnance + SP zaměstnavatele)",
        loc="center",
    )
    ax.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax.set_ylim(bottom=0)

    _bottom_legend(fig, c_emp)
    return fig


def plot_pension_sp_ratio_vs_income(
    income_max: int = 250_000,
    years: int = INSURANCE_YEARS,
) -> plt.Figure:
    """Obrázek: poměr důchod/odvody na SP v závislosti na příjmech / nákladech.

    Osa x = celkové náklady zaměstnavatele / příjmy OSVČ [tis. Kč/měsíc].
    Osa y = měsíční důchod / měsíční odvody na SP (bezrozměrné).

    Ukazuje, kolik Kč měsíčního důchodu připadá na každou Kč měsíčně odváděnou na SP.
    Vyšší hodnota = vyšší návratnost (rentabilita) odvodů na SP.
    """
    x = np.linspace(MIN_WAGE_TOTAL_COST, income_max, 2_000)
    c_emp = PALETTE[0]
    gross_emp = x / (1 + EMPLOYER_INS_RATE)
    breakeven_years_emp = INSURANCE_YEARS / (pension_employee(gross_emp, years) / sp_employee(x))

    fig, ax = plt.subplots(figsize=cm2in(16, 10))
    ax.plot(x / 1_000, breakeven_years_emp, color=c_emp, linewidth=2.0, zorder=3)

    for expense_rate, _label, color in OSVC_TYPES:
        pen_o = pension_osvc_vydajovy(x, expense_rate, years)
        sp_o = sp_osvc_vydajovy(x, expense_rate)
        breakeven_years_o = INSURANCE_YEARS / (pen_o / sp_o)
        cap = OSVC_VYDAJOVY_CAP[expense_rate]
        idx = int(np.searchsorted(x, cap, side='right'))
        if idx > 0:
            ax.plot(x[:idx] / 1_000, breakeven_years_o[:idx],
                    color=color, linewidth=1.5, linestyle="--", zorder=3)
        if idx < len(x):
            start = max(0, idx - 1)
            ax.plot(x[start:] / 1_000, breakeven_years_o[start:],
                    color=color, linewidth=1.5, linestyle="-.", alpha=0.45, zorder=3)

        segs = PAUSALNI_SEGS[expense_rate]
        for seg_i, (x_s, x_e, p_idx) in enumerate(segs):
            monthly_base = PAUSALNI_DAN[p_idx][1]
            x_start = max(x_s, MIN_WAGE_TOTAL_COST)
            x_end   = min(x_e, income_max)
            if x_start >= x_end:
                continue
            x_band = np.linspace(x_start, x_end, 300)
            pen_band = _pension(monthly_base, years)
            sp_band = OSVC_SOCIAL_RATE * monthly_base
            breakeven_years_band = np.full_like(x_band, INSURANCE_YEARS / (pen_band / sp_band))
            ax.plot(x_band / 1_000, breakeven_years_band,
                    color=color, linewidth=2.0, linestyle=":", zorder=2)

    ax.axhline(24.7, color="#555555", linewidth=1.0, linestyle=(0, (5, 5)), alpha=0.8, zorder=1)
    ax.annotate(
        "Průměrná délka pobírání\ndůchodu (24,7 let, 2024)",
        xy=(income_max * 0.98 / 1_000, 24.7),
        xytext=(-3, 4), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color="#555555", va="bottom", ha="right",
    )

    _add_vertical_ref(ax, MIN_WAGE_TOTAL_COST / 1_000,
                      f"Min.\u00a0mzda\n({_fmt_czk(MIN_WAGE_TOTAL_COST)})",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax, MEDIAN_EMP_TOTAL_COST / 1_000,
                      f"Medián\u00a0(zam.)\n({_fmt_czk(MEDIAN_EMP_TOTAL_COST)})",
                      color="#888888")
    _add_vertical_ref(ax, IT_MEDIAN_TOTAL_COST / 1_000,
                      f"Medián\u00a0ICT\u00a0(ISCO\u00a025)\n({_fmt_czk(IT_MEDIAN_TOTAL_COST)})",
                      color="#1a7abf")

    ax.set_xlabel("Celkové náklady zaměstnavatele / příjmy OSVČ [tis.\u00a0Kč/měsíc]")
    ax.set_ylabel("Roky důchodu ke splacení 40 let odvodů na SP")
    ax.set_title(
        f"Počet let pobírání důchodu k vrácení 40 let odvodů na SP\n"
        f"(parametry\u00a02026, pojistná doba\u00a0{years}\u00a0let; "
        f"zaměstnanec: celkové SP)",
        loc="center",
    )
    ax.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax.set_ylim(bottom=0)

    _bottom_legend(fig, c_emp)
    return fig


def plot_tax_wedge_comparison(
    income_max: int = 250_000,
    income_min: int = MIN_WAGE_TOTAL_COST,
    years: int = INSURANCE_YEARS,
) -> plt.Figure:
    """Parametrický obrázek: náhradový poměr vs. daňový klín.

    Osa x = efektivní daňový klín [%] = (SP + ZP + DPFO) / příjmy × 100.
    Osa y = náhradový poměr [%] = důchod / čistý příjem × 100.

    Každá křivka je parametrizována příjmem (celkové náklady zaměstnavatele /
    příjmy OSVČ) v rozsahu [income_min, income_max].
    """
    x = np.linspace(income_min, income_max, 2_000)

    gross_emp = x / (1 + EMPLOYER_INS_RATE)
    tw_emp    = tax_wedge_employee(x)
    rr_emp    = pension_employee(gross_emp, years) / net_income_employee(x) * 100

    fig, ax = plt.subplots(figsize=cm2in(16, 12))
    c_emp = PALETTE[0]

    ax.plot(tw_emp, rr_emp,
            color=c_emp, linewidth=2.0, zorder=3)

    _RR_CAP = 250.0  # clip extreme ratios near the low-income start of OSVČ series
    for expense_rate, label, color in OSVC_TYPES:
        tw_osvc = tax_wedge_osvc_vydajovy(x, expense_rate)
        ni_osvc = net_income_osvc_vydajovy(x, expense_rate)
        # Mask points where net income ≤ 0 or replacement rate exceeds display cap
        # (OSVČ 80 % at low income has negative/tiny net income that creates
        # extreme spikes near the minimum wage).
        rr_raw  = np.where(ni_osvc > 0,
                           pension_osvc_vydajovy(x, expense_rate, years) / np.maximum(ni_osvc, 1.0) * 100,
                           np.nan)
        rr_osvc = np.where(rr_raw <= _RR_CAP, rr_raw, np.nan)
        cap = OSVC_VYDAJOVY_CAP[expense_rate]
        mask_below = x <= cap
        mask_above = ~mask_below
        if mask_below.any():
            ax.plot(tw_osvc[mask_below], rr_osvc[mask_below],
                    color=color, linewidth=1.5, linestyle="--", zorder=3)
        if mask_above.any():
            start = max(0, int(np.where(mask_above)[0][0]) - 1)
            ax.plot(tw_osvc[start:], rr_osvc[start:],
                    color=color, linewidth=1.5, linestyle="-.", alpha=0.45, zorder=3)

        segs = PAUSALNI_SEGS[expense_rate]
        for seg_i, (x_s, x_e, p_idx) in enumerate(segs):
            monthly_base = PAUSALNI_DAN[p_idx][1]
            total_pay    = PAUSALNI_DAN_TOTAL[p_idx][1]
            x_start = max(x_s, income_min)
            x_end_s = min(x_e, income_max)
            if x_start >= x_end_s:
                continue
            x_band  = np.linspace(x_start, x_end_s, 300)
            tw_band = total_pay / x_band * 100
            p_val   = _pension(monthly_base, years)  # fixed VZ per pásmo
            net_band = np.maximum(x_band - float(total_pay), 1.0)
            rr_band = p_val / net_band * 100
            ax.plot(tw_band, rr_band,
                    color=color, linewidth=2.0, linestyle=":", zorder=2)

    # Referenční body na křivkách pro min. mzdu a mediánové náklady zaměstnance
    ref_points = [
        (MIN_WAGE_TOTAL_COST,   "Min.\u00a0mzda",                "#cc6600"),
        (MEDIAN_EMP_TOTAL_COST, "Medián\u00a0(zam., ISPV\u00a02024)", "#888888"),
        (IT_MEDIAN_TOTAL_COST,  "Medián\u00a0ICT\u00a0(ISCO\u00a025)",  "#1a7abf"),
    ]
    for x_ref, lbl, col in ref_points:
        if income_min <= x_ref <= income_max:
            gross_r = x_ref / (1 + EMPLOYER_INS_RATE)
            tw_e = float(tax_wedge_employee(float(x_ref)))
            rr_e = float(pension_employee(float(gross_r), years)) / float(net_income_employee(float(x_ref))) * 100
            ax.plot(tw_e, rr_e, "o", color=col, markersize=5, zorder=5)
            ax.annotate(lbl, (tw_e, rr_e), xytext=(4, 4),
                        textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color=col)
            for expense_rate_ref, _label, color_ref in OSVC_TYPES:
                ni_o = float(net_income_osvc_vydajovy(float(x_ref), expense_rate_ref))
                if ni_o <= 0:
                    continue
                tw_o = float(tax_wedge_osvc_vydajovy(float(x_ref), expense_rate_ref))
                rr_o = float(pension_osvc_vydajovy(float(x_ref), expense_rate_ref, years)) / max(ni_o, 1.0) * 100
                if rr_o <= _RR_CAP:
                    ax.plot(tw_o, rr_o, "o", color=col, markersize=5, zorder=5)

    ax.set_xlabel("Daňový klín\u00a0[%]")
    ax.set_ylabel("Náhradový poměr (důchod\u00a0/\u00a0čistý\u00a0příjem)\u00a0[%]")
    ax.set_title(
        "Náhradový poměr v závislosti na daňovém klínu\n"
        f"(parametry\u00a02026, pojistná doba\u00a0{years}\u00a0let)",
        loc="center",
    )
    ax.set_xlim(left=0)
    ax.set_ylim(0, _RR_CAP)

    # Inline popisky kurvek – zkratky v barvě u nejnižší hodnoty náhradového poměru
    # (tj. na konci křivky při nejvyšším příjmu income_max).
    x_end = float(income_max)
    gross_end = x_end / (1 + EMPLOYER_INS_RATE)
    tw_end_emp = float(tax_wedge_employee(x_end))
    rr_end_emp = float(pension_employee(gross_end, years)) / float(net_income_employee(x_end)) * 100
    ax.annotate("Zam.", (tw_end_emp, rr_end_emp),
                xytext=(4, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color=c_emp, va="center")

    for expense_rate, label, color in OSVC_TYPES:
        tw_end_o = float(tax_wedge_osvc_vydajovy(x_end, expense_rate))
        rr_end_o = float(pension_osvc_vydajovy(x_end, expense_rate, years)) / max(float(net_income_osvc_vydajovy(x_end, expense_rate)), 1.0) * 100
        # Short label: extract the expense-rate percentage from label string
        short = f"OSVČ\u00a0{int(expense_rate * 100)}\u202f%"
        ax.annotate(short, (tw_end_o, rr_end_o),
                    xytext=(4, 0), textcoords="offset points",
                    fontsize=FONT_SIZE - 2, color=color, va="center")

    # Inline labels for paušální segments: label each unique pásmo at the end of its
    # highest-income segment, using the OSVČ type color of that type's last segment.
    labeled_pidx: set[int] = set()
    for expense_rate, _label, color in OSVC_TYPES:
        segs = PAUSALNI_SEGS[expense_rate]
        for seg_i, (x_s, x_e, p_idx) in enumerate(segs):
            if p_idx in labeled_pidx:
                continue
            monthly_base = PAUSALNI_DAN[p_idx][1]
            total_pay    = PAUSALNI_DAN_TOTAL[p_idx][1]
            x_lab = float(min(income_max, x_e))
            if x_lab < income_min:
                continue
            tw_lab  = total_pay / x_lab * 100
            p_val   = _pension(monthly_base, years)
            net_lab = max(float(x_lab) - float(total_pay), 1.0)
            rr_lab  = p_val / net_lab * 100
            ax.annotate(f"Paušál\u00a0{p_idx + 1}", (tw_lab, rr_lab),
                        xytext=(4, 0), textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color=color, va="center")
            labeled_pidx.add(p_idx)

    return fig


# ── Spuštění ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    fig_tw = plot_tax_wedge_comparison()
    savefig(fig_tw, "cz_pension_wedge", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "cz_pension_wedge",
        caption=(
            r"Náhradový poměr v závislosti na efektivním daňovém klínu – "
            r"parametrický obrázek (parametr = celkové náklady zaměstnavatele "
            r"resp. příjmy OSVČ, rozsah přibližně 39–300\,tis.\,Kč/měsíc). "
            r"Osa x: daňový klín = (SP + ZP + DPFO) / příjmy; zahrnuje daň "
            r"z~příjmů a pojistné (zaměstnanec: i část zaměstnavatele). "
            r"Pro výdajový paušál SP a ZP nejsou odečitatelné od základu DPFO "
            r"(ZDP § 7 odst. 7). Sleva na poplatníka 2\,570\,Kč/měs.\ "
            r"uplatněna pro zaměstnance a OSVČ se standardními/výdajovými odvody; "
            r"pro paušální daň je již zahrnuta v pevné platbě. "
            r"Osa y: náhradový poměr = důchod\,/\,čistý příjem. "
            r"Tři typy OSVČ (výdajový paušál 40\,\%, 60\,\%, 80\,\%) "
            r"zobrazeny přerušovaně (standardní odvody) a tečkovaně (paušální daň). "
            r"Body označené kroužkem odpovídají minimální mzdě a mediánu zaměstnaneckých mezd "
            r"(ISPV 2024; medián zisku OSVČ není statisticky k~dispozici). "
            r"Parametry roku~2026, pojistná doba 40~let. "
            r"Výpočet dle zákonů č.\,155/1995~Sb., č.\,270/2023~Sb., "
            r"č.\,586/1992~Sb., č.\,589/1992~Sb., č.\,592/1992~Sb. "
            r"a nařízení vlády č.\,365/2025~Sb."
        ),
        label="fig:cz_pension_wedge",
        width=r"0.95\linewidth",
    )

    # ── Obrázek 4: daňový klín vs. příjmy ────────────────────────────────────
    fig_twi = plot_tax_wedge_vs_income()
    savefig(fig_twi, "cz_tax_wedge_vs_income", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "cz_tax_wedge_vs_income",
        caption=(
            r"Efektivní daňový klín v závislosti na celkových nákladech zaměstnavatele "
            r"(zaměstnanec) resp. příjmech OSVČ za měsíc. "
            r"Daňový klín = (SP + ZP + DPFO) / příjmy; pro zaměstnance zahrnuje "
            r"odvody zaměstnavatele i zaměstnance a DPFO (po slevě na poplatníka). "
            r"Pro OSVČ s výdajovým paušálem SP a ZP nejsou odečitatelné od základu "
            r"DPFO (ZDP § 7 odst. 7); sleva na poplatníka 2\,570\,Kč/měs.\ uplatněna. "
            r"Pro paušální daň: daňový klín = celková pevná platba\,/\,příjmy. "
            r"Tři typy OSVČ (výdajový paušál 40\,\%, 60\,\%, 80\,\%) zobrazeny "
            r"přerušovaně (standardní odvody) a tečkovaně (paušální daň). "
            r"Parametry roku~2026. "
            r"Výpočet dle zákonů č.\,586/1992~Sb., č.\,589/1992~Sb., č.\,592/1992~Sb. "
            r"a nařízení vlády č.\,365/2025~Sb."
        ),
        label="fig:cz_tax_wedge_vs_income",
        width=r"0.95\linewidth",
    )

    # ── Obrázek 5: čistý příjem vs. příjmy ───────────────────────────────────
    fig_ni = plot_net_income_vs_income()
    savefig(fig_ni, "cz_net_income_vs_income", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "cz_net_income_vs_income",
        caption=(
            r"Čistý příjem v závislosti na celkových nákladech zaměstnavatele "
            r"(zaměstnanec) resp. příjmech OSVČ za měsíc. "
            r"Zaměstnanec: čistý příjem = hrubá mzda\,−\,SP\,−\,ZP\,−\,DPFO. "
            r"OSVČ s výdajovým paušálem: čistý příjem = základ daně (ZD)\,−\,SP\,−\,ZP\,−\,DPFO, "
            r"kde ZD\,=\,příjmy\,×\,(1\,−\,sazba paušálu); paušální výdaje nejsou "
            r"součástí čistého příjmu (jsou uvažovány jako skutečné obchodní náklady). "
            r"OSVČ paušální daň: čistý příjem = příjmy\,−\,celková pevná platba "
            r"(skutečné výdaje nejsou modelovány). "
            r"Tři typy OSVČ (výdajový paušál 40\,\%, 60\,\%, 80\,\%) zobrazeny "
            r"přerušovaně (standardní odvody) a tečkovaně (paušální daň). "
            r"Parametry roku~2026. "
            r"Výpočet dle zákonů č.\,586/1992~Sb., č.\,589/1992~Sb., č.\,592/1992~Sb. "
            r"a nařízení vlády č.\,365/2025~Sb."
        ),
        label="fig:cz_net_income_vs_income",
        width=r"0.95\linewidth",
    )

    # ── Obrázek 7: odvody na SP vs. příjmy ───────────────────────────────────
    fig_spi = plot_sp_vs_income()
    savefig(fig_spi, "cz_sp_vs_income", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "cz_sp_vs_income",
        caption=(
            r"Měsíční odvody na sociální pojistné (SP) v závislosti na celkových "
            r"nákladech zaměstnavatele (zaměstnanec) resp. příjmech OSVČ za měsíc. "
            r"Zaměstnanec: celkové SP = SP zaměstnance (7,1\,\%) + SP zaměstnavatele "
            r"(24,8\,\%) = 31,9\,\% z hrubé mzdy. "
            r"OSVČ s výdajovým paušálem: SP = 29,2\,\% × max(55\,\% × ZD, min.\,základ). "
            r"Paušální daň: SP = 29,2\,\% × pevný vyměřovací základ pásma. "
            r"Tři typy OSVČ (výdajový paušál 40\,\%, 60\,\%, 80\,\%) zobrazeny "
            r"přerušovaně (standardní odvody) a tečkovaně (paušální daň). "
            r"Parametry roku~2026. "
            r"Výpočet dle zákonů č.\,589/1992~Sb., č.\,270/2023~Sb. "
            r"a nařízení vlády č.\,365/2025~Sb."
        ),
        label="fig:cz_sp_vs_income",
        width=r"0.95\linewidth",
    )

    # ── Obrázek 8: poměr důchod/SP vs. příjmy ────────────────────────────────
    fig_rsr = plot_pension_sp_ratio_vs_income()
    savefig(fig_rsr, "cz_pension_sp_ratio", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "cz_pension_sp_ratio",
        caption=(
            r"Poměr měsíčního starobního důchodu k měsíčním odvodům na SP "
            r"v závislosti na celkových nákladech zaměstnavatele (zaměstnanec) "
            r"resp. příjmech OSVČ za měsíc. "
            r"Hodnota 2,0 znamená, že za každou Kč měsíčně odváděnou na SP "
            r"je vyplácen důchod 2\,Kč/měsíc (při pojistné době 40~let). "
            r"Zaměstnanec: celkové SP = SP zaměstnance + SP zaměstnavatele. "
            r"OSVČ: SP = 29,2\,\% × vyměřovací základ (standardní nebo pevný pro paušál). "
            r"Tři typy OSVČ (výdajový paušál 40\,\%, 60\,\%, 80\,\%) zobrazeny "
            r"přerušovaně (standardní odvody) a tečkovaně (paušální daň). "
            r"Parametry roku~2026, pojistná doba 40~let. "
            r"Výpočet dle zákonů č.\,155/1995~Sb., č.\,270/2023~Sb., "
            r"č.\,589/1992~Sb. a nařízení vlády č.\,365/2025~Sb."
        ),
        label="fig:cz_pension_sp_ratio",
        width=r"0.95\linewidth",
    )

    print("Hotovo.")
