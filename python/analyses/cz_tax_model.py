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
      Y-axis: náhradový poměr [%] = důchod / příjmy
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
    PAUSALNI_DAN,
    PAUSALNI_DAN_TOTAL,
    MIN_WAGE_TOTAL_COST,
    MEDIAN_EMP_TOTAL_COST,
    OSVC_TYPES,
    PASMO_COLORS,
    _add_vertical_ref,
    _fmt_czk,
    _pension,
    pension_employee,
    pension_osvc_vydajovy,
)


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


def plot_tax_wedge_comparison(
    income_max: int = 300_000,
    income_min: int = OSVC_MIN_MONTHLY_BASE * 2,
    years: int = INSURANCE_YEARS,
) -> plt.Figure:
    """Parametrický obrázek: náhradový poměr vs. daňový klín.

    Osa x = efektivní daňový klín [%] = (SP + ZP + DPFO) / příjmy × 100.
    Osa y = náhradový poměr [%] = důchod / příjmy × 100.

    Každá křivka je parametrizována příjmem (celkové náklady zaměstnavatele /
    příjmy OSVČ) v rozsahu [income_min, income_max].
    """
    x = np.linspace(income_min, income_max, 2_000)

    gross_emp = x / (1 + EMPLOYER_INS_RATE)
    tw_emp    = tax_wedge_employee(x)
    rr_emp    = pension_employee(gross_emp, years) / x * 100

    fig, ax = plt.subplots(figsize=cm2in(16, 12))
    c_emp = PALETTE[0]

    ax.plot(tw_emp, rr_emp,
            color=c_emp, linewidth=2.0, zorder=3)

    for expense_rate, label, color, max_pasmo in OSVC_TYPES:
        tw_osvc = tax_wedge_osvc_vydajovy(x, expense_rate)
        rr_osvc = pension_osvc_vydajovy(x, expense_rate, years) / x * 100
        ax.plot(tw_osvc, rr_osvc,
                color=color, linewidth=1.5, linestyle="--", zorder=3)

        prev_max = income_min
        for i, ((max_inc_p, monthly_base), (max_inc_t, total_pay)) in enumerate(
                zip(PAUSALNI_DAN[:max_pasmo], PAUSALNI_DAN_TOTAL[:max_pasmo])):
            x_band  = np.linspace(max(prev_max, income_min), max_inc_t, 300)
            tw_band = total_pay / x_band * 100
            p_val   = _pension(monthly_base, years)  # fixed VZ per pásmo
            rr_band = p_val / x_band * 100
            ax.plot(tw_band, rr_band,
                    color=PASMO_COLORS[i], linewidth=2.0, linestyle=":", zorder=2)
            prev_max = max_inc_t

    # Referenční body na křivkách pro min. mzdu a mediánové náklady zaměstnance
    ref_points = [
        (MIN_WAGE_TOTAL_COST,   "Min.\u00a0mzda",                "#cc6600"),
        (MEDIAN_EMP_TOTAL_COST, "Medián\u00a0(zam., ISPV\u00a02024)", "#888888"),
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
            for expense_rate_ref, _label, color_ref, _max_pasmo in OSVC_TYPES:
                tw_o = float(tax_wedge_osvc_vydajovy(float(x_ref), expense_rate_ref))
                rr_o = float(pension_osvc_vydajovy(float(x_ref), expense_rate_ref, years)) / x_ref * 100
                ax.plot(tw_o, rr_o, "o", color=col, markersize=5, zorder=5)

    ax.set_xlabel("Daňový klín\u00a0[%]")
    ax.set_ylabel("Náhradový poměr (důchod\u00a0/\u00a0příjmy)\u00a0[%]")
    ax.set_title(
        "Náhradový poměr v závislosti na daňovém klínu\n"
        f"(parametry\u00a02026, pojistná doba\u00a0{years}\u00a0let)",
        loc="center",
    )
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    # Inline popisky kurvek – zkratky v barvě u nejnižší hodnoty náhradového poměru
    # (tj. na konci křivky při nejvyšším příjmu income_max).
    x_end = float(income_max)
    gross_end = x_end / (1 + EMPLOYER_INS_RATE)
    tw_end_emp = float(tax_wedge_employee(x_end))
    rr_end_emp = float(pension_employee(gross_end, years)) / x_end * 100
    ax.annotate("Zam.", (tw_end_emp, rr_end_emp),
                xytext=(4, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color=c_emp, va="center")

    for expense_rate, label, color, max_pasmo in OSVC_TYPES:
        tw_end_o = float(tax_wedge_osvc_vydajovy(x_end, expense_rate))
        rr_end_o = float(pension_osvc_vydajovy(x_end, expense_rate, years)) / x_end * 100
        # Short label: extract the expense-rate percentage from label string
        short = f"OSVČ\u00a0{int(expense_rate * 100)}\u202f%"
        ax.annotate(short, (tw_end_o, rr_end_o),
                    xytext=(4, 0), textcoords="offset points",
                    fontsize=FONT_SIZE - 2, color=color, va="center")

    for i, ((max_inc_p, monthly_base), (max_inc_t, total_pay)) in enumerate(
            zip(PAUSALNI_DAN, PAUSALNI_DAN_TOTAL)):
        # The paušální band ends at max_inc_t; label at high-income end of band
        x_lab = float(min(income_max, max_inc_t))
        tw_lab = total_pay / x_lab * 100
        p_val  = _pension(monthly_base, years)
        rr_lab = p_val / x_lab * 100
        ax.annotate(f"Paušál {i + 1}", (tw_lab, rr_lab),
                    xytext=(4, 0), textcoords="offset points",
                    fontsize=FONT_SIZE - 2, color=PASMO_COLORS[i], va="center")

    return fig


# ── Spuštění ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    apply_style()

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
            r"Osa y: náhradový poměr = důchod\,/\,příjmy. "
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

    print("Hotovo.")
