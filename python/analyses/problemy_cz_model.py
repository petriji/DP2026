r"""Czech pension & tax figures – all matplotlib visualisation code.

All calculation is delegated to cz_pension_model and cz_tax_model.
This file only contains plot functions and the __main__ entry point.

Run
---
    python analyses/cz_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from config import FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.style import (
    apply_style, cm2in, save_figure_tex, savefig,
    _fmt_czk, _add_vertical_ref, _apply_figure_layout,
)

# ── Pension-model calc helpers ────────────────────────────────────────────────
from cz_pension_model import (
    INSURANCE_YEARS,
    MIN_TOTAL_PENSION,
    RH1,
    RH2,
    pension_employee,
    pension_osvc_vydajovy,
    _pension,
)

# ── Tax-model calc functions ──────────────────────────────────────────────────
from cz_tax_model import (
    EMPLOYER_INS_RATE,
    OSVC_MIN_MONTHLY_BASE,
    DPH_THRESHOLD_MONTHLY,
    PAUSALNI_DAN,
    PAUSALNI_DAN_TOTAL,
    OSVC_SOCIAL_RATE,
    tax_wedge_employee,
    tax_wedge_osvc_vydajovy,
    net_income_employee,
    net_income_osvc_vydajovy,
    sp_employee,
    sp_osvc_vydajovy,
)

# ── Figure-only constants ─────────────────────────────────────────────────────
# Reference wages: NV 405/2025 Sb. (min. wage, 2026) + ISPV 2025 (medians)
MIN_WAGE: int              = 22_400
MIN_WAGE_TOTAL_COST: int   = int(MIN_WAGE * (1 + EMPLOYER_INS_RATE))
MEDIAN_EMP_WAGE: int       = 43_241   # hrubá mzda (ISPV 2025)
MEDIAN_EMP_TOTAL_COST: int = int(MEDIAN_EMP_WAGE * (1 + EMPLOYER_INS_RATE))
IT_MEDIAN_WAGE: int        = 90_332   # ISCO 25 (ISPV CR mzs 2025)
IT_MEDIAN_TOTAL_COST: int  = int(IT_MEDIAN_WAGE * (1 + EMPLOYER_INS_RATE))
POVERTY_THRESHOLD: int     = 18_600   # ČSÚ 2025

# RH kink positions on the x-axis (total employer cost / OSVČ revenue)
EMP_RH1_X: int = int(RH1 * (1 + EMPLOYER_INS_RATE))
EMP_RH2_X: int = int(RH2 * (1 + EMPLOYER_INS_RATE))

# OSVČ types: (výdajový_paušál, label, colour)
OSVC_TYPES: list[tuple[float, str, str]] = [
    (0.80, "OSVČ 80\u202f%\u00a0výdajů (řemeslná živnost)",        PALETTE[4]),
    (0.60, "OSVČ 60\u202f%\u00a0výdajů (ost.\u00a0živnosti)",     PALETTE[1]),
    (0.40, "OSVČ 40\u202f%\u00a0výdajů (svobodná\u00a0povolání)", PALETTE[5]),
]

# Paušal eligibility segments: {expense_rate: [(x_start, x_end, pasmo_idx), ...]}
# § 2a zák. č. 586/1992 Sb.
PAUSALNI_SEGS: dict[float, list[tuple[int, int, int]]] = {
    0.40: [(0, 83_333, 0), (83_333, 125_000, 1), (125_000, 166_667, 2)],
    0.60: [(0, 125_000, 0), (125_000, 166_667, 1)],
    0.80: [(0, 166_667, 0)],
}

# Výdajový paušál income caps (§ 7 odst. 7 ZDP)
OSVC_VYDAJOVY_CAP: dict[float, int] = {0.80: 133_333, 0.60: 100_000, 0.40: 66_667}

# Švarc systém reference curve
SVARC_EXPENSE_RATE: float = 0.16
SVARC_LINESTYLE           = (0, (6, 1))

apply_style()


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

    # Theoretical: expense_rate=0 above cap – pouze jednou (40 %, šedivě)
    _mask40 = x >= OSVC_VYDAJOVY_CAP[0.40]
    if _mask40.any():
        x_above = x[_mask40]
        y_no_exp = fn_osvc(x_above, 0.0)
        ax.plot(x_above / 1_000, y_no_exp,
                color="#888888", linewidth=1.0, linestyle=(0, (3, 1.5)), alpha=0.7, zorder=2)

    # Švarc systém: 16 % výdajů nad paušálem – pouze jednou (40 %, šedivě)
    if _mask40.any():
        x_above = x[_mask40]
        y_svarc = fn_osvc(x_above, SVARC_EXPENSE_RATE)
        ax.plot(x_above / 1_000, y_svarc,
                color="#888888", linewidth=1.2, linestyle=SVARC_LINESTYLE, alpha=0.85, zorder=2)



# ── Pension figures ────────────────────────────────────────────────────────────

def plot_pension_comparison(
    income_max: int = 250_000,
    income_min: int = MIN_WAGE_TOTAL_COST,
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
    income_min:
        Spodní mez osy x [Kč/měsíc] (= min celkové náklady zaměstnavatele / příjmy OSVČ).
    years:
        Předpokládaná pojistná doba [roky] pro výpočet procentní výměry.

    Returns
    -------
    matplotlib Figure objekt.
    """
    x = np.linspace(income_min, income_max, 2_000)  # Kč/měsíc (total cost / revenue)

    gross_emp = x / (1 + EMPLOYER_INS_RATE)
    p_emp     = pension_employee(gross_emp, years)

    fig, ax = plt.subplots(figsize=cm2in(16, 13))
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

    # Theoretical: expense_rate=0 above the paušál income cap – only once (40 %, gray).
    _mask40 = x >= OSVC_VYDAJOVY_CAP[0.40]
    if _mask40.any():
        p_no_exp = pension_osvc_vydajovy(x[_mask40], 0.0, years)
        ax.plot(x[_mask40] / 1_000, p_no_exp / 1_000,
                color="#888888", linewidth=1.0, linestyle=(0, (3, 1.5)), alpha=0.7, zorder=2)

    # Švarc systém: 16 % výdajů nad paušálem – pouze jednou (40 %, šedivě)
    if _mask40.any():
        p_svarc = pension_osvc_vydajovy(x[_mask40], SVARC_EXPENSE_RATE, years)
        ax.plot(x[_mask40] / 1_000, p_svarc / 1_000,
                color="#888888", linewidth=1.2, linestyle=SVARC_LINESTYLE, alpha=0.85, zorder=2)

    # Minimální výše důchodu
    min_pension_kczk = MIN_TOTAL_PENSION / 1_000
    ax.axhline(min_pension_kczk, color="#555555", linewidth=0.8,
               linestyle=(0, (5, 5)), alpha=0.7, zorder=1)

    # Hranice chudoby
    poverty_kczk = POVERTY_THRESHOLD / 1_000
    ax.axhline(poverty_kczk, color="#aa0000", linewidth=0.8,
               linestyle=(0, (3, 4)), alpha=0.7, zorder=1)

    # Referenční svislé čáry
    _add_vertical_ref(ax, MIN_WAGE_TOTAL_COST / 1_000,
                      f"min.\u00a0mzda\n{_fmt_czk(MIN_WAGE_TOTAL_COST)}",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax, MEDIAN_EMP_TOTAL_COST / 1_000,
                      f"medián\u00a0\n{_fmt_czk(MEDIAN_EMP_TOTAL_COST)}",
                      color="#888888")
    _add_vertical_ref(ax, IT_MEDIAN_TOTAL_COST / 1_000,
                      f"medián\u00a0ICT\u00a0(ISCO\u00a025)\n{_fmt_czk(IT_MEDIAN_TOTAL_COST)}",
                      color="#1a7abf")
    if DPH_THRESHOLD_MONTHLY <= income_max:
        _add_vertical_ref(ax, DPH_THRESHOLD_MONTHLY / 1_000,
                          f"práh\u00a0DPH\n{_fmt_czk(DPH_THRESHOLD_MONTHLY)}",
                          color="#cc0000", linestyle=(0, (5, 3)))
    if EMP_RH1_X >= income_min:
        _add_vertical_ref(ax, EMP_RH1_X / 1_000,
                          f"1.\u00a0RH\u00a0\n{_fmt_czk(EMP_RH1_X)}",
                          color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))
    if EMP_RH2_X <= income_max:
        _add_vertical_ref(ax, EMP_RH2_X / 1_000,
                          f"2.\u00a0RH\u00a0\n{_fmt_czk(EMP_RH2_X)}",
                          color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))

    ax.set_xlabel("celkové náklady zaměstnavatele / příjmy OSVČ [tis.\u00a0Kč/měsíc]")
    ax.set_ylabel("starobní důchod [tis.\u00a0Kč/měsíc]")
    ax.set_title(
        f"Výše starobního důchodu v závislosti na nákladech na práci\n"
        f"(pojistná doba\u00a0{years}\u00a0let, parametry\u00a02026)",
        loc="center",
    )
    ax.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax.set_ylim(bottom=0)

    # Inline popisky křivek – pravý konec osy x
    x_end = float(income_max)
    gross_end = x_end / (1 + EMPLOYER_INS_RATE)
    p_end_emp = float(pension_employee(float(gross_end), years)) / 1_000
    ax.annotate("zaměstnanec", (x_end / 1_000, p_end_emp),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color=c_emp, va="center")
    # Labely pro hline (min. důchod a chudoba) – vpravo venku
    ax.annotate(
        "min. důchod",
        xy=(x_end / 1_000, min_pension_kczk),
        xytext=(3, 0), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color="#555555", va="center",
    )
    ax.annotate(
        "chudoba",
        xy=(x_end / 1_000, poverty_kczk),
        xytext=(3, 0), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color="#aa0000", va="center",
    )
    for expense_rate, _label, color in OSVC_TYPES:
        p_end_o = float(pension_osvc_vydajovy(float(x_end), expense_rate, years)) / 1_000
        ax.annotate(f"OSVČ\u00a0{int(expense_rate * 100)}\u202f%",
                    (x_end / 1_000, p_end_o),
                    xytext=(3, -4 if expense_rate == 0.80 else 0), textcoords="offset points",
                    fontsize=FONT_SIZE - 2, color=color, va="center")
    labeled_pidx_cmp: set[int] = set()
    for expense_rate, _label, color in OSVC_TYPES:
        segs = PAUSALNI_SEGS[expense_rate]
        for x_s, x_e, p_idx in segs:
            if p_idx in labeled_pidx_cmp:
                continue
            _, monthly_base = PAUSALNI_DAN[p_idx]
            p_val = _pension(monthly_base, years) / 1_000
            x_lab = float(min(income_max, x_e)) / 1_000
            ax.annotate(f"paušál\u00a0{p_idx + 1}", (x_lab, p_val),
                        xytext=(3, 0), textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color=color, va="center")
            labeled_pidx_cmp.add(p_idx)

    # Inline popisky šedých křivek – bez výdajů a Švarc
    p_no_exp_end = float(pension_osvc_vydajovy(float(x_end), 0.0, years)) / 1_000
    ax.annotate("bez výdajů", (x_end / 1_000, p_no_exp_end),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color="#888888", va="center")
    p_svarc_end = float(pension_osvc_vydajovy(float(x_end), SVARC_EXPENSE_RATE, years)) / 1_000
    ax.annotate("16 % výdajů", (x_end / 1_000, p_svarc_end),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color="#888888", va="center")
    _apply_figure_layout(ax)
    return fig


def plot_pension_solidarity(
    income_max: int = 250_000,
    income_min: int = MIN_WAGE_TOTAL_COST,
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
    income_min:
        Spodní mez osy x [Kč/měsíc].
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
        figsize=cm2in(16, 18),
        gridspec_kw={"height_ratios": [3, 2]},
        sharex=True,
    )
    fig.subplots_adjust(hspace=0.08)
    fig._subplots_adjust_kwargs = {"hspace": 0.08}

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

    # Theoretical: expense_rate=0 above cap – horní panel, pouze jednou (40 %, šedivě)
    _mask40 = x >= OSVC_VYDAJOVY_CAP[0.40]
    if _mask40.any():
        p_no_exp = pension_osvc_vydajovy(x[_mask40], 0.0, years)
        ax_top.plot(x[_mask40] / 1_000, p_no_exp / 1_000,
                    color="#888888", linewidth=1.0, linestyle=(0, (3, 1.5)), alpha=0.7, zorder=2)

    # Švarc systém: 16 % výdajů nad paušálem – horní panel, pouze jednou (40 %, šedivě)
    if _mask40.any():
        p_svarc = pension_osvc_vydajovy(x[_mask40], SVARC_EXPENSE_RATE, years)
        ax_top.plot(x[_mask40] / 1_000, p_svarc / 1_000,
                    color="#888888", linewidth=1.2, linestyle=SVARC_LINESTYLE, alpha=0.85, zorder=2)

    # Minimální výše důchodu – horní panel
    min_pension_kczk = MIN_TOTAL_PENSION / 1_000
    ax_top.axhline(min_pension_kczk, color="#555555", linewidth=0.8,
                   linestyle=(0, (5, 5)), alpha=0.7, zorder=1)

    # Hranice chudoby – horní panel
    poverty_kczk = POVERTY_THRESHOLD / 1_000
    ax_top.axhline(poverty_kczk, color="#aa0000", linewidth=0.8,
                   linestyle=(0, (3, 4)), alpha=0.7, zorder=1)

    # Referenční svislé čáry
    _add_vertical_ref(ax_top, MIN_WAGE_TOTAL_COST / 1_000,
                      f"min.\u00a0mzda\n{_fmt_czk(MIN_WAGE_TOTAL_COST)}",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax_top, MEDIAN_EMP_TOTAL_COST / 1_000,
                      f"medián\u00a0\n{_fmt_czk(MEDIAN_EMP_TOTAL_COST)}",
                      color="#888888")
    _add_vertical_ref(ax_top, IT_MEDIAN_TOTAL_COST / 1_000,
                      f"medián\u00a0ICT\u00a0(ISCO\u00a025)\n{_fmt_czk(IT_MEDIAN_TOTAL_COST)}",
                      color="#1a7abf")
    if DPH_THRESHOLD_MONTHLY <= income_max:
        _add_vertical_ref(ax_top, DPH_THRESHOLD_MONTHLY / 1_000,
                          f"práh\u00a0DPH\n{_fmt_czk(DPH_THRESHOLD_MONTHLY)}",
                          color="#cc0000", linestyle=(0, (5, 3)))
    if EMP_RH1_X >= income_min:
        _add_vertical_ref(ax_top, EMP_RH1_X / 1_000,
                          f"1.\u00a0RH\u00a0\n{_fmt_czk(EMP_RH1_X)}",
                          color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))
    if EMP_RH2_X <= income_max:
        _add_vertical_ref(ax_top, EMP_RH2_X / 1_000,
                          f"2.\u00a0RH\u00a0\n{_fmt_czk(EMP_RH2_X)}",
                          color=c_emp, alpha=0.35, linestyle=(0, (2, 6)))

    ax_top.set_ylabel("starobní důchod [tis.\u00a0Kč/měsíc]")
    ax_top.set_title(
        f"Výše starobního důchodu v závislosti na nákladech na práci\n"
        f"(pojistná doba\u00a0{years}\u00a0let, parametry\u00a02026)",
        loc="center",
    )
    ax_top.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax_top.set_ylim(bottom=0)

    # Inline popisky horního panelu – pravý konec osy x
    x_end = float(income_max)
    gross_end = x_end / (1 + EMPLOYER_INS_RATE)
    p_end_emp_top = float(pension_employee(float(gross_end), years)) / 1_000
    ax_top.annotate("zaměstnanec", (x_end / 1_000, p_end_emp_top),
                    xytext=(3, 0), textcoords="offset points",
                    fontsize=FONT_SIZE - 2, color=c_emp, va="center")
    # Label pro min. důchod – vpravo venku
    ax_top.annotate(
        "min. důchod",
        xy=(x_end / 1_000, min_pension_kczk),
        xytext=(3, 0), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color="#555555", va="center",
    )
    ax_top.annotate(
        "chudoba",
        xy=(x_end / 1_000, poverty_kczk),
        xytext=(3, 0), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color="#aa0000", va="center",
    )
    for expense_rate, _label, color in OSVC_TYPES:
        p_end_o = float(pension_osvc_vydajovy(float(x_end), expense_rate, years)) / 1_000
        ax_top.annotate(f"OSVČ\u00a0{int(expense_rate * 100)}\u202f%",
                        (x_end / 1_000, p_end_o),
                        xytext=(3, -4 if expense_rate == 0.80 else 0), textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color=color, va="center")
    labeled_pidx_sol: set[int] = set()
    for expense_rate, _label, color in OSVC_TYPES:
        segs = PAUSALNI_SEGS[expense_rate]
        for x_s, x_e, p_idx in segs:
            if p_idx in labeled_pidx_sol:
                continue
            _, monthly_base = PAUSALNI_DAN[p_idx]
            p_val = _pension(monthly_base, years) / 1_000
            x_lab = float(min(income_max, x_e)) / 1_000
            ax_top.annotate(f"paušál\u00a0{p_idx + 1}", (x_lab, p_val),
                            xytext=(3, 0), textcoords="offset points",
                            fontsize=FONT_SIZE - 2, color=color, va="center")
            labeled_pidx_sol.add(p_idx)

    # Inline popisky šedých křivek – bez výdajů a Švarc (horní panel)
    p_no_exp_top = float(pension_osvc_vydajovy(float(x_end), 0.0, years)) / 1_000
    ax_top.annotate("bez výdajů", (x_end / 1_000, p_no_exp_top),
                    xytext=(3, 0), textcoords="offset points",
                    fontsize=FONT_SIZE - 2, color="#888888", va="center")
    p_svarc_top = float(pension_osvc_vydajovy(float(x_end), SVARC_EXPENSE_RATE, years)) / 1_000
    ax_top.annotate("16 % výdajů", (x_end / 1_000, p_svarc_top),
                    xytext=(3, 0), textcoords="offset points",
                    fontsize=FONT_SIZE - 2, color="#888888", va="center")

    # ══════════════════════════════════════════════════════════════════════════
    # DOLNÍ PANEL – náhradový poměr [%] = důchod / čistý příjem × 100
    # ══════════════════════════════════════════════════════════════════════════
    rr_emp = p_emp_rr / net_income_employee(x_rr) * 100
    ax_bot.plot(x_rr / 1_000, rr_emp, color=c_emp, linewidth=2.0)

    _RR_CAP = 150.0  # y-axis upper limit; extreme values near min wage are hidden by ylim
    for expense_rate, label, color in OSVC_TYPES:
        p_osvc_rr = pension_osvc_vydajovy(x_rr, expense_rate, years)
        ni_osvc   = net_income_osvc_vydajovy(x_rr, expense_rate)
        # Mask only where net income ≤ 0; extreme positive outliers are handled
        # by the y-axis upper limit below (simpler than NaN-masking).
        rr_osvc = np.where(ni_osvc > 0,
                           p_osvc_rr / np.maximum(ni_osvc, 1.0) * 100,
                           np.nan)
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

    # Theoretical: expense_rate=0 above cap – dolní panel, pouze jednou (40 %, šedivě)
    _mask40_rr = x_rr >= OSVC_VYDAJOVY_CAP[0.40]
    if _mask40_rr.any():
        x_ab = x_rr[_mask40_rr]
        p_no_ab  = pension_osvc_vydajovy(x_ab, 0.0, years)
        ni_no_ab = net_income_osvc_vydajovy(x_ab, 0.0)
        rr_no_ab = np.where(ni_no_ab > 0,
                            p_no_ab / np.maximum(ni_no_ab, 1.0) * 100, np.nan)
        ax_bot.plot(x_ab / 1_000, rr_no_ab,
                    color="#888888", linewidth=1.0, linestyle=(0, (3, 1.5)), alpha=0.7, zorder=2)

    # Švarc systém: 16 % výdajů nad paušálem – dolní panel, pouze jednou (40 %, šedivě)
    if _mask40_rr.any():
        x_ab = x_rr[_mask40_rr]
        p_sv_ab  = pension_osvc_vydajovy(x_ab, SVARC_EXPENSE_RATE, years)
        ni_sv_ab = net_income_osvc_vydajovy(x_ab, SVARC_EXPENSE_RATE)
        rr_sv_ab = np.where(ni_sv_ab > 0,
                            p_sv_ab / np.maximum(ni_sv_ab, 1.0) * 100, np.nan)
        ax_bot.plot(x_ab / 1_000, rr_sv_ab,
                    color="#888888", linewidth=1.2, linestyle=SVARC_LINESTYLE, alpha=0.85, zorder=2)

    # Minimální výše důchodu – dolní panel: odstraněno (přeplněný panel)

    # Referenční svislé čáry – dolní panel (bez popisků, aby se neopakovali)
    ax_bot.axvline(MIN_WAGE_TOTAL_COST / 1_000, color="#cc6600", linewidth=0.8,
                   linestyle=(0, (4, 3)), alpha=0.7, zorder=1)
    ax_bot.axvline(MEDIAN_EMP_TOTAL_COST / 1_000, color="#888888", linewidth=0.8,
                   linestyle=(0, (3, 4)), alpha=0.7, zorder=1)
    ax_bot.axvline(IT_MEDIAN_TOTAL_COST / 1_000, color="#1a7abf", linewidth=0.8,
                   linestyle=(0, (3, 4)), alpha=0.7, zorder=1)
    if DPH_THRESHOLD_MONTHLY <= income_max:
        ax_bot.axvline(DPH_THRESHOLD_MONTHLY / 1_000, color="#cc0000", linewidth=0.8,
                       linestyle=(0, (5, 3)), alpha=0.7, zorder=1)
    if EMP_RH1_X <= income_max:
        ax_bot.axvline(EMP_RH1_X / 1_000, color=c_emp, linewidth=0.8,
                       linestyle=(0, (2, 6)), alpha=0.35, zorder=1)
    if EMP_RH2_X <= income_max:
        ax_bot.axvline(EMP_RH2_X / 1_000, color=c_emp, linewidth=0.8,
                       linestyle=(0, (2, 6)), alpha=0.35, zorder=1)

    ax_bot.set_xlabel("celkové náklady zaměstnavatele / příjmy OSVČ [tis.\u00a0Kč/měsíc]")
    ax_bot.set_ylabel("čistý náhradový poměr\u00a0[%]")
    ax_bot.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax_bot.set_ylim(0, _RR_CAP)

    # Inline popisky dolního panelu – pravý konec osy x
    x_end_rr = float(income_max)
    gross_end_rr = x_end_rr / (1 + EMPLOYER_INS_RATE)
    p_end_emp_rr = float(pension_employee(float(gross_end_rr), years))
    ni_end_emp = float(net_income_employee(float(x_end_rr)))
    if ni_end_emp > 0:
        rr_end_emp = p_end_emp_rr / ni_end_emp * 100
        ax_bot.annotate("zaměstnanec", (x_end_rr / 1_000, rr_end_emp),
                        xytext=(3, 0), textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color=c_emp, va="center")
    for expense_rate, _label, color in OSVC_TYPES:
        if expense_rate == 0.40:  # přeskočit OSVČ 40 % – překryv
            continue
        ni_end_o = float(net_income_osvc_vydajovy(float(x_end_rr), expense_rate))
        if ni_end_o <= 0:
            continue
        pen_end_o = float(pension_osvc_vydajovy(float(x_end_rr), expense_rate, years))
        rr_end_o = pen_end_o / max(ni_end_o, 1.0) * 100
        if rr_end_o <= _RR_CAP:
            ax_bot.annotate(f"OSVČ\u00a0{int(expense_rate * 100)}\u202f%",
                            (x_end_rr / 1_000, rr_end_o),
                            xytext=(3, 0), textcoords="offset points",
                            fontsize=FONT_SIZE - 2, color=color, va="center")

    # Inline popisky šedých křivek – bez výdajů a Švarc (dolní panel)
    p_no_bot = float(pension_osvc_vydajovy(float(x_end_rr), 0.0, years))
    ni_no_bot = float(net_income_osvc_vydajovy(float(x_end_rr), 0.0))
    if ni_no_bot > 0:
        rr_no_bot = p_no_bot / max(ni_no_bot, 1.0) * 100
        if rr_no_bot <= _RR_CAP:
            ax_bot.annotate("bez výdajů", (x_end_rr / 1_000, rr_no_bot),
                            xytext=(3, 0), textcoords="offset points",
                            fontsize=FONT_SIZE - 2, color="#888888", va="center")
    _apply_figure_layout(ax_bot, hspace=0.08)
    return fig


# ── Tax figures ────────────────────────────────────────────────────────────────

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
                      f"min.\u00a0mzda\n{_fmt_czk(MIN_WAGE_TOTAL_COST)}",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax, MEDIAN_EMP_TOTAL_COST / 1_000,
                      f"medián\u00a0\n{_fmt_czk(MEDIAN_EMP_TOTAL_COST)}",
                      color="#888888")
    _add_vertical_ref(ax, IT_MEDIAN_TOTAL_COST / 1_000,
                      f"medián\u00a0ICT\u00a0(ISCO\u00a025)\n{_fmt_czk(IT_MEDIAN_TOTAL_COST)}",
                      color="#1a7abf")
    if DPH_THRESHOLD_MONTHLY <= income_max:
        _add_vertical_ref(ax, DPH_THRESHOLD_MONTHLY / 1_000,
                          f"práh\u00a0DPH\n{_fmt_czk(DPH_THRESHOLD_MONTHLY)}",
                          color="#cc0000", linestyle=(0, (5, 3)))

    ax.set_xlabel("celkové náklady zaměstnavatele / příjmy OSVČ [tis.\u00a0Kč/měsíc]")
    ax.set_ylabel("daňový klín [%]")
    ax.set_title(
        "Daňový klín v závislosti na nákladech práce\n"
        "(parametry\u00a02026)",
        loc="center",
    )
    ax.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax.set_ylim(bottom=0)

    # Inline popisky křivek – umístěny na pravém konci každé křivky
    x_end = float(income_max)
    tw_end_emp = float(tax_wedge_employee(x_end))
    ax.annotate("zaměstnanec", (x_end / 1_000, tw_end_emp),
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
            ax.annotate(f"paušál\u00a0{p_idx + 1}", (x_lab / 1_000, tw_lab),
                        xytext=(4, 0), textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color=color, va="center")
            labeled_pidx2.add(p_idx)

    # Inline popisky šedých křivek – bez výdajů a Švarc
    tw_no_end = float(tax_wedge_osvc_vydajovy(x_end, 0.0))
    ax.annotate("bez výdajů", (x_end / 1_000, tw_no_end),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color="#888888", va="center")
    tw_sv_end = float(tax_wedge_osvc_vydajovy(x_end, SVARC_EXPENSE_RATE))
    ax.annotate("16 % výdajů", (x_end / 1_000, tw_sv_end),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color="#888888", va="center")
    _apply_figure_layout(ax)
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
                      f"min.\u00a0mzda\n{_fmt_czk(MIN_WAGE_TOTAL_COST)}",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax, MEDIAN_EMP_TOTAL_COST / 1_000,
                      f"medián\u00a0\n{_fmt_czk(MEDIAN_EMP_TOTAL_COST)}",
                      color="#888888")
    _add_vertical_ref(ax, IT_MEDIAN_TOTAL_COST / 1_000,
                      f"medián\u00a0ICT\u00a0(ISCO\u00a025)\n{_fmt_czk(IT_MEDIAN_TOTAL_COST)}",
                      color="#1a7abf")
    if DPH_THRESHOLD_MONTHLY <= income_max:
        _add_vertical_ref(ax, DPH_THRESHOLD_MONTHLY / 1_000,
                          f"práh\u00a0DPH\n{_fmt_czk(DPH_THRESHOLD_MONTHLY)}",
                          color="#cc0000", linestyle=(0, (5, 3)))

    ax.set_xlabel("celkové náklady zaměstnavatele / příjmy OSVČ [tis.\u00a0Kč/měsíc]")
    ax.set_ylabel("čistý příjem [tis.\u00a0Kč/měsíc]")
    ax.set_title(
        "Čistý příjem pracovníka v závislosti na nákladech práce\n"
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
        "chudoba",
        xy=(income_max / 1_000, poverty_kczk),
        xytext=(3, 0), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color="#aa0000", va="center",
    )

    # Inline popisky křivek
    x_end = float(income_max)
    ni_end_emp = float(net_income_employee(x_end)) / 1_000
    ax.annotate("zaměstnanec", (x_end / 1_000, ni_end_emp),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color=c_emp, va="center")
    for expense_rate, _label, color in OSVC_TYPES:
        ni_end_o = float(net_income_osvc_vydajovy(x_end, expense_rate)) / 1_000
        ax.annotate(f"OSVČ\u00a0{int(expense_rate * 100)}\u202f%",
                    (x_end / 1_000, ni_end_o),
                    xytext=(3, 0), textcoords="offset points",
                    fontsize=FONT_SIZE - 2, color=color, va="center")
    labeled_pidx_ni: set[int] = set()
    for expense_rate, _label, color in OSVC_TYPES:
        segs = PAUSALNI_SEGS[expense_rate]
        for x_s, x_e, p_idx in segs:
            if p_idx in labeled_pidx_ni:
                continue
            _, total_pay = PAUSALNI_DAN_TOTAL[p_idx]
            x_lab = float(min(income_max, x_e))
            ni_lab = (x_lab - float(total_pay)) / 1_000
            ax.annotate(f"paušál\u00a0{p_idx + 1}", (x_lab / 1_000, ni_lab),
                        xytext=(3, 0), textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color=color, va="center")
            labeled_pidx_ni.add(p_idx)

    # Inline popisky šedých křivek – bez výdajů a Švarc
    ni_no_end = float(net_income_osvc_vydajovy(x_end, 0.0)) / 1_000
    ax.annotate("bez výdajů", (x_end / 1_000, ni_no_end),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color="#888888", va="center")
    ni_sv_end = float(net_income_osvc_vydajovy(x_end, SVARC_EXPENSE_RATE)) / 1_000
    ax.annotate("16 % výdajů", (x_end / 1_000, ni_sv_end),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color="#888888", va="center")
    _apply_figure_layout(ax)
    return fig


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
                      f"min.\u00a0mzda\n{_fmt_czk(MIN_WAGE_TOTAL_COST)}",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax, MEDIAN_EMP_TOTAL_COST / 1_000,
                      f"medián\u00a0\n{_fmt_czk(MEDIAN_EMP_TOTAL_COST)}",
                      color="#888888")
    _add_vertical_ref(ax, IT_MEDIAN_TOTAL_COST / 1_000,
                      f"medián\u00a0ICT\u00a0(ISCO\u00a025)\n{_fmt_czk(IT_MEDIAN_TOTAL_COST)}",
                      color="#1a7abf")
    if DPH_THRESHOLD_MONTHLY <= income_max:
        _add_vertical_ref(ax, DPH_THRESHOLD_MONTHLY / 1_000,
                          f"práh\u00a0DPH\n{_fmt_czk(DPH_THRESHOLD_MONTHLY)}",
                          color="#cc0000", linestyle=(0, (5, 3)))

    ax.set_xlabel("celkové náklady zaměstnavatele / příjmy OSVČ [tis.\u00a0Kč/měsíc]")
    ax.set_ylabel("odvody na SP [tis.\u00a0Kč/měsíc]")
    ax.set_title(
        "Odvody na sociální pojistné v závislosti na nákladech práce\n"
        "(parametry\u00a02026; zaměstnanec: SP zaměstnance + SP zaměstnavatele)",
        loc="center",
    )
    ax.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax.set_ylim(bottom=0)

    # Inline popisky křivek
    x_end = float(income_max)
    sp_end_emp = float(sp_employee(x_end)) / 1_000
    ax.annotate("zaměstnanec", (x_end / 1_000, sp_end_emp),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color=c_emp, va="center")
    for expense_rate, _label, color in OSVC_TYPES:
        sp_end_o = float(sp_osvc_vydajovy(x_end, expense_rate)) / 1_000
        ax.annotate(f"OSVČ\u00a0{int(expense_rate * 100)}\u202f%",
                    (x_end / 1_000, sp_end_o),
                    xytext=(3, 0), textcoords="offset points",
                    fontsize=FONT_SIZE - 2, color=c_emp if expense_rate == 0 else color, va="center")
    labeled_pidx_sp: set[int] = set()
    for expense_rate, _label, color in OSVC_TYPES:
        segs = PAUSALNI_SEGS[expense_rate]
        for x_s, x_e, p_idx in segs:
            if p_idx in labeled_pidx_sp:
                continue
            _, monthly_base = PAUSALNI_DAN[p_idx]
            sp_lab = OSVC_SOCIAL_RATE * monthly_base / 1_000
            x_lab = float(min(income_max, x_e))
            ax.annotate(f"paušál\u00a0{p_idx + 1}", (x_lab / 1_000, sp_lab),
                        xytext=(3, 0), textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color=color, va="center")
            labeled_pidx_sp.add(p_idx)

    # Inline popisky šedých křivek – bez výdajů a Švarc
    sp_no_end = float(sp_osvc_vydajovy(x_end, 0.0)) / 1_000
    ax.annotate("bez výdajů", (x_end / 1_000, sp_no_end),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color="#888888", va="center")
    sp_sv_end = float(sp_osvc_vydajovy(x_end, SVARC_EXPENSE_RATE)) / 1_000
    ax.annotate("16 % výdajů", (x_end / 1_000, sp_sv_end),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color="#888888", va="center")
    _apply_figure_layout(ax)
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

    # Theoretical: expense_rate=0 above cap – pouze jednou (40 %, šedivě)
    _mask40 = x >= OSVC_VYDAJOVY_CAP[0.40]
    if _mask40.any():
        x_above = x[_mask40]
        pen_no = pension_osvc_vydajovy(x_above, 0.0, years)
        sp_no  = sp_osvc_vydajovy(x_above, 0.0)
        by_no  = INSURANCE_YEARS / (pen_no / np.maximum(sp_no, 1.0))
        ax.plot(x_above / 1_000, by_no,
                color="#888888", linewidth=1.0, linestyle=(0, (3, 1.5)), alpha=0.7, zorder=2)

    # Švarc systém: 16 % výdajů nad paušálem – pouze jednou (40 %, šedivě)
    if _mask40.any():
        x_above = x[_mask40]
        pen_sv = pension_osvc_vydajovy(x_above, SVARC_EXPENSE_RATE, years)
        sp_sv  = sp_osvc_vydajovy(x_above, SVARC_EXPENSE_RATE)
        by_sv  = INSURANCE_YEARS / (pen_sv / np.maximum(sp_sv, 1.0))
        ax.plot(x_above / 1_000, by_sv,
                color="#888888", linewidth=1.2, linestyle=SVARC_LINESTYLE, alpha=0.85, zorder=2)

    ax.axhline(24.7, color="#555555", linewidth=1.0, linestyle=(0, (5, 5)), alpha=0.8, zorder=1)
    ax.annotate(
        "průměrná délka pobírání\ndůchodu (24,7 let, 2024)",
        xy=(income_max * 0.98 / 1_000, 24.7),
        xytext=(-3, 4), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color="#555555", va="bottom", ha="right",
    )

    _add_vertical_ref(ax, MIN_WAGE_TOTAL_COST / 1_000,
                      f"min.\u00a0mzda\n{_fmt_czk(MIN_WAGE_TOTAL_COST)}",
                      color="#cc6600", linestyle=(0, (4, 3)))
    _add_vertical_ref(ax, MEDIAN_EMP_TOTAL_COST / 1_000,
                      f"medián\u00a0\n{_fmt_czk(MEDIAN_EMP_TOTAL_COST)}",
                      color="#888888")
    _add_vertical_ref(ax, IT_MEDIAN_TOTAL_COST / 1_000,
                      f"medián\u00a0ICT\u00a0(ISCO\u00a025)\n{_fmt_czk(IT_MEDIAN_TOTAL_COST)}",
                      color="#1a7abf")
    if DPH_THRESHOLD_MONTHLY <= income_max:
        _add_vertical_ref(ax, DPH_THRESHOLD_MONTHLY / 1_000,
                          f"práh\u00a0DPH\n{_fmt_czk(DPH_THRESHOLD_MONTHLY)}",
                          color="#cc0000", linestyle=(0, (5, 3)))

    ax.set_xlabel("celkové náklady zaměstnavatele / příjmy OSVČ [tis.\u00a0Kč/měsíc]")
    ax.set_ylabel("vyrovnání čerpání SD s odvody na SP – roky")
    ax.set_title(
        f"Počet let pobírání důchodu k vrácení 40 let odvodů na SP\n"
        f"(parametry\u00a02026, pojistná doba\u00a0{years}\u00a0let; "
        f"zaměstnanec: celkové SP)",
        loc="center",
    )
    ax.set_xlim(MIN_WAGE_TOTAL_COST / 1_000, income_max / 1_000)
    ax.set_ylim(bottom=0)

    # Inline popisky křivek
    x_end = float(income_max)
    gross_end = x_end / (1 + EMPLOYER_INS_RATE)
    pen_end_emp = float(pension_employee(float(gross_end), years))
    sp_end_emp_total = float(sp_employee(float(x_end)))
    by_end_emp = INSURANCE_YEARS / (pen_end_emp / max(sp_end_emp_total, 1.0))
    ax.annotate("zaměstnanec", (x_end / 1_000, by_end_emp),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color=c_emp, va="center")
    for expense_rate, _label, color in OSVC_TYPES:
        pen_end_o = float(pension_osvc_vydajovy(float(x_end), expense_rate, years))
        sp_end_o = float(sp_osvc_vydajovy(float(x_end), expense_rate))
        by_end_o = INSURANCE_YEARS / (pen_end_o / max(sp_end_o, 1.0))
        ax.annotate(f"OSVČ\u00a0{int(expense_rate * 100)}\u202f%",
                    (x_end / 1_000, by_end_o),
                    xytext=(3, 0), textcoords="offset points",
                    fontsize=FONT_SIZE - 2, color=color, va="center")
    labeled_pidx_rs: set[int] = set()
    for expense_rate, _label, color in OSVC_TYPES:
        segs = PAUSALNI_SEGS[expense_rate]
        for x_s, x_e, p_idx in segs:
            if p_idx in labeled_pidx_rs:
                continue
            _, monthly_base = PAUSALNI_DAN[p_idx]
            pen_band = _pension(monthly_base, years)
            sp_band = OSVC_SOCIAL_RATE * monthly_base
            by_band = INSURANCE_YEARS / (pen_band / max(sp_band, 1.0))
            x_lab = float(min(income_max, x_e))
            ax.annotate(f"paušál\u00a0{p_idx + 1}", (x_lab / 1_000, by_band),
                        xytext=(3, 0), textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color=color, va="center")
            labeled_pidx_rs.add(p_idx)

    # Inline popisky šedých křivek – bez výdajů a Švarc
    pen_no_end = float(pension_osvc_vydajovy(float(x_end), 0.0, years))
    sp_no_end  = float(sp_osvc_vydajovy(float(x_end), 0.0))
    by_no_end  = INSURANCE_YEARS / (pen_no_end / max(sp_no_end, 1.0))
    ax.annotate("bez výdajů", (x_end / 1_000, by_no_end),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color="#888888", va="center")
    pen_sv_end = float(pension_osvc_vydajovy(float(x_end), SVARC_EXPENSE_RATE, years))
    sp_sv_end  = float(sp_osvc_vydajovy(float(x_end), SVARC_EXPENSE_RATE))
    by_sv_end  = INSURANCE_YEARS / (pen_sv_end / max(sp_sv_end, 1.0))
    ax.annotate("16 % výdajů", (x_end / 1_000, by_sv_end),
                xytext=(3, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color="#888888", va="center")
    _apply_figure_layout(ax)
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

    # Theoretical: expense_rate=0 – pouze jednou (40 %, šedivě)
    _mask40 = x >= OSVC_VYDAJOVY_CAP[0.40]
    if _mask40.any():
        x_above = x[_mask40]
        tw_no   = tax_wedge_osvc_vydajovy(x_above, 0.0)
        ni_no   = net_income_osvc_vydajovy(x_above, 0.0)
        rr_no_raw = np.where(ni_no > 0,
                             pension_osvc_vydajovy(x_above, 0.0, years) / np.maximum(ni_no, 1.0) * 100,
                             np.nan)
        rr_no = np.where(rr_no_raw <= _RR_CAP, rr_no_raw, np.nan)
        ax.plot(tw_no, rr_no,
                color="#888888", linewidth=1.0, linestyle=(0, (3, 1.5)), alpha=0.7, zorder=2)

    # Švarc systém: 16 % výdajů nad paušálem – pouze jednou (40 %, šedivě)
    if _mask40.any():
        x_above = x[_mask40]
        tw_sv   = tax_wedge_osvc_vydajovy(x_above, SVARC_EXPENSE_RATE)
        ni_sv   = net_income_osvc_vydajovy(x_above, SVARC_EXPENSE_RATE)
        rr_sv_raw = np.where(ni_sv > 0,
                             pension_osvc_vydajovy(x_above, SVARC_EXPENSE_RATE, years) / np.maximum(ni_sv, 1.0) * 100,
                             np.nan)
        rr_sv = np.where(rr_sv_raw <= _RR_CAP, rr_sv_raw, np.nan)
        ax.plot(tw_sv, rr_sv,
                color="#888888", linewidth=1.2, linestyle=SVARC_LINESTYLE, alpha=0.85, zorder=2)

    # Referenční body na křivkách pro min. mzdu a mediánové náklady zaměstnance
    ref_points = [
        (MIN_WAGE_TOTAL_COST,   "min.\u00a0mzda",                "#cc6600"),
        (MEDIAN_EMP_TOTAL_COST, "medián\u00a0(zam., ISPV\u00a02025)", "#888888"),
        (IT_MEDIAN_TOTAL_COST,  "medián\u00a0ICT\u00a0(ISCO\u00a025)",  "#1a7abf"),
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

    ax.set_xlabel("daňový klín\u00a0[%]")
    ax.set_ylabel("čistý náhradový poměr [%]")
    ax.set_title(
        "Náhradový poměr v závislosti na daňovém klínu pro různé modely práce\n"
        f"(parametry\u00a02026, pojistná doba\u00a0{years}\u00a0let)",
        loc="center",
    )
    ax.set_xlim(left=0)
    ax.set_ylim(0, _RR_CAP)

    # Inline popisky kurvek – zkratky v barvě u nejnižší hodnoty náhradového poměru
    x_end = float(income_max)
    gross_end = x_end / (1 + EMPLOYER_INS_RATE)
    tw_end_emp = float(tax_wedge_employee(x_end))
    rr_end_emp = float(pension_employee(gross_end, years)) / float(net_income_employee(x_end)) * 100
    ax.annotate("zaměstnanec", (tw_end_emp, rr_end_emp),
                xytext=(4, 0), textcoords="offset points",
                fontsize=FONT_SIZE - 2, color=c_emp, va="center")

    for expense_rate, label, color in OSVC_TYPES:
        tw_end_o = float(tax_wedge_osvc_vydajovy(x_end, expense_rate))
        rr_end_o = float(pension_osvc_vydajovy(x_end, expense_rate, years)) / max(float(net_income_osvc_vydajovy(x_end, expense_rate)), 1.0) * 100
        short = f"OSVČ\u00a0{int(expense_rate * 100)}\u202f%"
        ax.annotate(short, (tw_end_o, rr_end_o),
                    xytext=(4, 0), textcoords="offset points",
                    fontsize=FONT_SIZE - 2, color=color, va="center")

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
            ax.annotate(f"paušál\u00a0{p_idx + 1}", (tw_lab, rr_lab),
                        xytext=(4, 0), textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color=color, va="center")
            labeled_pidx.add(p_idx)

    # Inline popisky šedých křivek – bez výdajů a Švarc
    tw_no_cmp = float(tax_wedge_osvc_vydajovy(x_end, 0.0))
    ni_no_cmp = float(net_income_osvc_vydajovy(x_end, 0.0))
    if ni_no_cmp > 0:
        rr_no_cmp = float(pension_osvc_vydajovy(x_end, 0.0, years)) / max(ni_no_cmp, 1.0) * 100
        if rr_no_cmp <= _RR_CAP:
            ax.annotate("bez výdajů", (tw_no_cmp, rr_no_cmp),
                        xytext=(4, 0), textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color="#888888", va="center")
    tw_sv_cmp = float(tax_wedge_osvc_vydajovy(x_end, SVARC_EXPENSE_RATE))
    ni_sv_cmp = float(net_income_osvc_vydajovy(x_end, SVARC_EXPENSE_RATE))
    if ni_sv_cmp > 0:
        rr_sv_cmp = float(pension_osvc_vydajovy(x_end, SVARC_EXPENSE_RATE, years)) / max(ni_sv_cmp, 1.0) * 100
        if rr_sv_cmp <= _RR_CAP:
            ax.annotate("16 % výdajů", (tw_sv_cmp, rr_sv_cmp),
                        xytext=(4, 0), textcoords="offset points",
                        fontsize=FONT_SIZE - 2, color="#888888", va="center")
    _apply_figure_layout(ax)
    return fig


# ── Spuštění ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # ── Obrázek 1: přehledové srovnání (single-panel) ─────────────────────────
    fig_cmp = plot_pension_comparison()
    savefig(fig_cmp, "problemy_duchod_prijem", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "problemy_duchod_prijem",
        caption=(
            r"Výše starobního důchodu v~závislosti na příjmu, parametry 2026. "
            r"Osa x odpovídá celkovým výdajům plátce: pro zaměstnance zahrnuje "
            r"hrubou mzdu i odvody zaměstnavatele (33,8\,\%); pro OSVČ se standardními "
            r"odvody je to zisk (příjmy\,$-$\,výdaje); pro OSVČ v~paušálním daňovém "
            r"režimu jde o~měsíční příjmy (revenue), přičemž výše důchodu je v~každém "
            r"pásmu pevná. "
            r"Parametry roku~2026, předpokládaná pojistná doba 40~let. "
            r"Výpočet dle zákona č.\,155/1995~Sb.\ (zákon o~důchodovém pojištění), "
            r"zákona č.\,270/2023~Sb.\ (důchodová reforma) "
            r"a nařízení vlády č.\,365/2025~Sb."
        ),
        cite_keys=["zakon_zpds_1995", "zakon_duchreforma_2023", "nv_365_2025"],
        label="fig:problemy_duchod_prijem",
        width=r"0.95\linewidth",
    )

    # ── Obrázek 2: solidární přerozdělení (two-panel) ─────────────────────────
    fig_sol = plot_pension_solidarity()
    savefig(fig_sol, "problemy_duchod_solidarita", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "problemy_duchod_solidarita",
        caption=(
            r"Náhradový poměr a~výše důchodu v~závislosti na příjmu, parametry 2026. "
            r"Parametry roku~2026, pojistná doba 40~let. "
            r"Výpočet dle zákona č.\,155/1995~Sb., zákona č.\,270/2023~Sb. "
            r"a nařízení vlády č.\,365/2025~Sb."
        ),
        cite_keys=["zakon_zpds_1995", "zakon_duchreforma_2023", "nv_365_2025"],
        label="fig:problemy_duchod_solidarita",
        width=r"0.95\linewidth",
    )

    # ── Obrázek 3: náhradový poměr vs. daňový klín (parametrický) ─────────────
    fig_tw = plot_tax_wedge_comparison()
    savefig(fig_tw, "problemy_duchod_klin", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "problemy_duchod_klin",
        caption=(
            r"Náhradový poměr a~efektivní daňový klín, OSVČ a~zaměstnanec. "
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
            r"(ISPV 2026; medián zisku OSVČ není statisticky k~dispozici). "
            r"Parametry roku~2026, pojistná doba 40~let. "
            r"Výpočet dle zákonů č.\,155/1995~Sb., č.\,270/2023~Sb., "
            r"č.\,586/1992~Sb., č.\,589/1992~Sb., č.\,592/1992~Sb. "
            r"a nařízení vlády č.\,365/2025~Sb."
        ),
        cite_keys=["zakon_zpds_1995", "zakon_duchreforma_2023",
                   "zakon_zdp_1992", "zakon_sp_1992", "zakon_zp_1992", "nv_365_2025"],
        label="fig:problemy_duchod_klin",
        width=r"0.95\linewidth",
    )

    # ── Obrázek 4: daňový klín vs. příjmy ────────────────────────────────────
    fig_twi = plot_tax_wedge_vs_income()
    savefig(fig_twi, "problemy_danovy_klin_cz", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "problemy_danovy_klin_cz",
        caption=(
            r"Efektivní daňový klín, zaměstnanec vs.\ OSVČ, parametry 2026. "
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
        cite_keys=["zakon_zdp_1992", "zakon_sp_1992", "zakon_zp_1992", "nv_365_2025"],
        label="fig:problemy_danovy_klin_cz",
        width=r"0.95\linewidth",
    )

    # ── Obrázek 5: čistý příjem vs. příjmy ───────────────────────────────────
    fig_ni = plot_net_income_vs_income()
    savefig(fig_ni, "problemy_cisty_prijem_cz", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "problemy_cisty_prijem_cz",
        caption=(
            r"Čistý příjem, zaměstnanec vs.\ OSVČ, parametry 2026. "
            r"Zaměstnanec: čistý příjem = hrubá mzda\,$-$\,SP\,$-$\,ZP\,$-$\,DPFO. "
            r"OSVČ s výdajovým paušálem: čistý příjem = základ daně (ZD)\,$-$\,SP\,$-$\,ZP\,$-$\,DPFO, "
            r"kde ZD\,=\,příjmy\,$\times$\,(1\,$-$\,sazba paušálu); paušální výdaje nejsou "
            r"součástí čistého příjmu (jsou uvažovány jako skutečné obchodní náklady). "
            r"OSVČ paušální daň: čistý příjem = příjmy\,$-$\,celková pevná platba "
            r"(skutečné výdaje nejsou modelovány). "
            r"Tři typy OSVČ (výdajový paušál 40\,\%, 60\,\%, 80\,\%) zobrazeny "
            r"přerušovaně (standardní odvody) a tečkovaně (paušální daň). "
            r"Parametry roku~2026. "
            r"Výpočet dle zákonů č.\,586/1992~Sb., č.\,589/1992~Sb., č.\,592/1992~Sb. "
            r"a nařízení vlády č.\,365/2025~Sb."
        ),
        cite_keys=["zakon_zdp_1992", "zakon_sp_1992", "zakon_zp_1992", "nv_365_2025"],
        label="fig:problemy_cisty_prijem_cz",
        width=r"0.95\linewidth",
    )

    # ── Obrázek 7: odvody na SP vs. příjmy ───────────────────────────────────
    fig_spi = plot_sp_vs_income()
    savefig(fig_spi, "problemy_sp_odvody_cz", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "problemy_sp_odvody_cz",
        caption=(
            r"Měsíční odvody na SP, zaměstnanec vs.\ OSVČ, parametry 2026. "
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
        cite_keys=["zakon_sp_1992", "zakon_duchreforma_2023", "nv_365_2025"],
        label="fig:problemy_sp_odvody_cz",
        width=r"0.95\linewidth",
    )

    # ── Obrázek 8: poměr důchod/SP vs. příjmy ────────────────────────────────
    fig_rsr = plot_pension_sp_ratio_vs_income()
    savefig(fig_rsr, "problemy_duchod_sp_pomer", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "problemy_duchod_sp_pomer",
        caption=(
            r"Poměr měsíčního důchodu k~odvodům na SP, parametry 2026. "
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
        cite_keys=["zakon_zpds_1995", "zakon_duchreforma_2023",
                   "zakon_sp_1992", "nv_365_2025"],
        label="fig:problemy_duchod_sp_pomer",
        width=r"0.95\linewidth",
    )

    print("Hotovo.")
