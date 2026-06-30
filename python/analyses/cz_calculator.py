r"""Czech old-age pension (starobní důchod) -- individual calculator.

Uses the statutory parameters and reduction formula from ``problemy_cz_duchod``
and the levy constants from ``cz_tax_model``.

Reduction formula (§ 15 ZPDS, zákon č. 270/2023 Sb.):
    ROVZ = min(OVZ, RH1) × 0.99             ← first_limit_pct declines 2026--2035
         + max(min(OVZ, RH2) − RH1, 0) × 0.26
         # third band (> RH2) abolished from 2026 → 0 %

VVZ/PK table and reduction limits are year-parameterised so the calculator
can handle both historical and future retirement years.

Public API
----------
    get_params(year)                    → PensionParams
    compute_ovz(earnings, ...)          → int
    calculate_pension(earnings, ...)    → PensionResult
    calculate_pension_simple(gross, ...)→ PensionResult   (fast estimate)
    print_result(result)                CLI-friendly output

Run
---
    python analyses/cz_calculator.py
"""

from __future__ import annotations

import calendar
import math
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from problemy_cz_duchod import (
    ZAKLADNI_VYMERA,
    RH1,
    RH2,
    PCT_PER_YEAR,
    INSURANCE_YEARS,
    MIN_PROCENTNI_VYMERA,
)


# ── VVZ / PK table (NV published annually in Sbírka zákonů) ──────────────────
# Format: year → (VVZ, PK)
# NV 253/2023 Sb. (2023), NV 286/2024 Sb. (2024);
# 2025 estimate -- replace with official NV when published.
VVZ_PK: dict[int, tuple[int, float]] = {
    2003: (16_769, 1.0665),
    2004: (17_882, 1.0532),
    2005: (18_809, 1.0707),
    2006: (19_447, 1.0753),
    2007: (20_050, 1.0942),
    2008: (21_527, 1.0184),
    2009: (21_527, 1.0269),
    2010: (22_355, 1.0249),
    2011: (22_446, 1.0315),
    2012: (23_233, 1.0015),
    2013: (25_903, 1.0273),
    2014: (25_903, 1.0273),
    2015: (26_357, 1.0246),
    2016: (27_156, 1.0396),
    2017: (28_232, 1.0612),
    2018: (30_156, 1.0843),
    2019: (32_510, 1.0715),
    2020: (34_766, 1.0194),
    2021: (36_119, 1.0773),
    2022: (38_294, 1.0530),
    2023: (40_638, 1.0819),
    2024: (43_967, 1.1137),  # NV 286/2024 Sb. -- PK back-calculated from NV 365/2025 (RH1=21 546)
    # 2025: (?,?),            # TODO: add NV 2025/2026 when published
}


# ── Year-parameterised pension parameters ─────────────────────────────────────

@dataclass
class PensionParams:
    """2026+ statutory parameters for a given retirement year."""
    year: int
    prumerna_mzda: int       # průměrná mzda (§ 15 odst. 5 ZPDS)
    rh1: int                 # 1. redukční hranice = 44 % prům. mzdy (§ 15 ZPDS)
    rh2: int                 # 2. redukční hranice = 400 % prům. mzdy (§ 15 ZPDS)
    zakladni_vymera: int     # základní výměra = 10 % prům. mzdy, ↑10 Kč (§ 33 ZPDS)
    pct_per_year: float      # sazba procentní výměry za rok (§ 34 ZPDS)
    first_limit_pct: float   # podíl ROVZ pod 1. RH (99 % → 90 %, zákon č. 270/2023)


def _ceil_int(x: float) -> int:
    return math.ceil(x)


def _ceil_to_10(x: float) -> int:
    return math.ceil(x / 10) * 10


def _pct_per_year(year: int) -> float:
    """Sazba procentní výměry za rok pojištění (§ 34 odst. 1 ZPDS)."""
    if year < 2026:
        return 1.5
    rates = {
        2026: 1.495, 2027: 1.490, 2028: 1.485, 2029: 1.480,
        2030: 1.475, 2031: 1.470, 2032: 1.465, 2033: 1.460,
        2034: 1.455,
    }
    return rates.get(year, 1.450)


def _first_limit_pct(year: int) -> float:
    """Podíl ROVZ zohledňovaný pod 1. RH (zákon č. 270/2023 Sb., § 15)."""
    if year <= 2025:
        return 1.00
    pcts = {
        2026: 0.99, 2027: 0.98, 2028: 0.97, 2029: 0.96,
        2030: 0.95, 2031: 0.94, 2032: 0.93, 2033: 0.92,
        2034: 0.91,
    }
    return pcts.get(year, 0.90)


def _prumerna_mzda(year: int) -> int:
    """Průměrná mzda pro rok *year* (§ 15 odst. 5 ZPDS).

    = ceil(VVZ(year-2) × PK(year-2)), nesmí klesnout oproti předchozímu roku.
    """
    ref = year - 2
    if ref not in VVZ_PK:
        raise ValueError(
            f"VVZ/PK data for {ref} not available -- add it to VVZ_PK."
        )
    vvz, pk = VVZ_PK[ref]
    pm = _ceil_int(vvz * pk)
    try:
        pm = max(pm, _prumerna_mzda(year - 1))
    except (ValueError, RecursionError):
        pass
    return pm


def get_params(year: int) -> PensionParams:
    """Spočítá parametry důchodového výpočtu pro rok *year*."""
    pm = _prumerna_mzda(year)
    return PensionParams(
        year=year,
        prumerna_mzda=pm,
        rh1=_ceil_int(0.44 * pm),   # § 15 odst. 4 ZPDS
        rh2=_ceil_int(4.00 * pm),   # § 15 odst. 4 ZPDS
        zakladni_vymera=_ceil_to_10(0.10 * pm),  # § 33 odst. 1 ZPDS + § 54
        pct_per_year=_pct_per_year(year),
        first_limit_pct=_first_limit_pct(year),
    )


# ── Výpočtový základ (§ 15 ZPDS) ─────────────────────────────────────────────

def compute_vypoctovy_zaklad(ovz: int, params: PensionParams) -> int:
    """ROVZ → výpočtový základ (§ 15 ZPDS, zákon č. 270/2023 Sb.).

    Pásma (2026):
      do 1. RH:           first_limit_pct (2026 = 99 %)
      1. RH -- 2. RH:      26 %
      nad 2. RH:          0 % (třetí pásmo zrušeno zákonem č. 270/2023 Sb.)
    """
    rh1 = params.rh1
    rh2 = params.rh2
    p1  = params.first_limit_pct

    if ovz <= rh1:
        vz = ovz * p1
    elif ovz <= rh2:
        vz = rh1 * p1 + (ovz - rh1) * 0.26
    else:
        vz = rh1 * p1 + (rh2 - rh1) * 0.26  # nad RH2 → 0 %

    return _ceil_int(vz)


# ── OVZ (§ 16 ZPDS) ───────────────────────────────────────────────────────────

def _vvz_growth_coeff(earnings_year: int, retirement_year: int) -> float:
    """Koeficient nárůstu VVZ (§ 17 odst. 1 ZPDS).

    = VVZ(ret-2) × PK(ret-2) / VVZ(earnings_year), min. 1,0.
    Pro earnings_year ≥ retirement_year − 1 → vždy 1,0 (§ 17 odst. 3).
    """
    if earnings_year >= retirement_year - 1:
        return 1.0
    ref = retirement_year - 2
    if ref not in VVZ_PK:
        raise ValueError(
            f"VVZ/PK[{ref}] not available -- add it to VVZ_PK "
            f"(needed to project earnings for retirement_year={retirement_year})."
        )
    if earnings_year not in VVZ_PK:
        raise ValueError(
            f"VVZ/PK[{earnings_year}] not available -- add it to VVZ_PK "
            f"(needed for earnings_year={earnings_year})."
        )
    vvz_ref, pk_ref = VVZ_PK[ref]
    vvz_earn, _     = VVZ_PK[earnings_year]
    return max((vvz_ref * pk_ref) / vvz_earn, 1.0)


def compute_ovz(
    annual_earnings: dict[int, float],
    year_of_birth: int,
    year_of_retirement: int,
    excluded_days: int = 0,
) -> int:
    """Osobní vyměřovací základ (§ 16 ZPDS).

    Parameters
    ----------
    annual_earnings:
        Rok → roční hrubý vyměřovací základ (Kč). Chybějící roky = 0.
    year_of_birth:
        Rok narození (určuje začátek rozhodného období).
    year_of_retirement:
        Rok přiznání důchodu.
    excluded_days:
        Vyloučené doby v kalendářních dnech (§ 16 odst. 4--5 ZPDS).
    """
    period_start = year_of_birth + 19   # rok po dovršení 18 let (§ 18 odst. 1)
    period_end   = year_of_retirement - 1

    total_days    = 0
    sum_bases     = 0.0

    for y in range(period_start, period_end + 1):
        days = 366 if calendar.isleap(y) else 365
        total_days += days
        coeff       = _vvz_growth_coeff(y, year_of_retirement)
        sum_bases  += annual_earnings.get(y, 0.0) * coeff

    effective_days = total_days - excluded_days
    if effective_days <= 0:
        raise ValueError("effective_days must be > 0")

    return _ceil_int(30.4167 * sum_bases / effective_days)


# ── Výsledek ──────────────────────────────────────────────────────────────────

@dataclass
class PensionResult:
    year: int
    zakladni_vymera: int     # základní výměra (Kč/měs.)
    procentni_vymera: int    # procentní výměra (Kč/měs.)
    total_pension: int       # celkový měsíční důchod (Kč)
    ovz: int                 # osobní vyměřovací základ
    vypoctovy_zaklad: int    # výpočtový základ
    years_of_insurance: int  # pojistná doba (roky)
    pct_rate: float          # sazba % výměry za rok
    children_bonus: int      # bonus za vychované děti (§ 34a)
    early_penalty: int       # krácení za předčasný odchod (§ 36)
    late_bonus: int          # zvýšení za odložení (§ 34 odst. 3)
    params: PensionParams


# ── Kalkulátor ────────────────────────────────────────────────────────────────

def _compute_components(
    ovz: int,
    params: PensionParams,
    years_of_insurance: int,
    children_raised: int,
    early_days: int,
    late_days: int,
    has_45_years: bool,
) -> tuple[int, int, int, int, int]:
    """Spočítá složky procentní výměry. Vrací (vz, procentni_raw_ceil,
    late_bonus, early_penalty, children_bonus)."""
    vz = compute_vypoctovy_zaklad(ovz, params)

    procentni_raw = _ceil_int(params.pct_per_year / 100.0 * vz * years_of_insurance)

    late_bonus    = _ceil_int(0.015 * vz * (late_days // 90))

    early_penalty = 0
    if early_days > 0:
        penalty_rate  = 0.0075 if has_45_years else 0.015
        early_penalty = _ceil_int(penalty_rate * vz * math.ceil(early_days / 90))

    children_bonus = 500 * children_raised

    return vz, procentni_raw, late_bonus, early_penalty, children_bonus


def calculate_pension(
    annual_earnings: dict[int, float],
    year_of_birth: int,
    year_of_retirement: int,
    years_of_insurance: int,
    excluded_days: int = 0,
    children_raised: int = 0,
    early_days: int = 0,
    late_days: int = 0,
    has_45_years: bool = False,
) -> PensionResult:
    """Vypočítá starobní důchod ze skutečné výdělkové historie.

    Parameters
    ----------
    annual_earnings:
        Rok → roční hrubý vyměřovací základ v Kč (pro zaměstnance = hrubá mzda
        pro SP; pro OSVČ = základ daně × OSVC_BASE_RATIO × 12).
    year_of_birth, year_of_retirement, years_of_insurance:
        Rok narození, rok přiznání, celková pojistná doba v celých rocích.
    excluded_days:
        Vyloučené doby (§ 16 odst. 4--5 ZPDS) v kalendářních dnech.
    children_raised:
        Počet vychovaných dětí (§ 34a ZPDS, +500 Kč/dítě).
    early_days:
        Dny předčasného odchodu před dosažením důchodového věku (§ 36 ZPDS).
    late_days:
        Dny odloženého přiznání po vzniku nároku (§ 34 odst. 3 ZPDS).
    has_45_years:
        Má ≥ 45 let pojištění → mírnější krácení 0,75 % místo 1,5 % (§ 36).
    """
    params = get_params(year_of_retirement)
    ovz = compute_ovz(annual_earnings, year_of_birth, year_of_retirement, excluded_days)

    vz, procentni_raw, late_bonus, early_penalty, children_bonus = _compute_components(
        ovz, params, years_of_insurance, children_raised, early_days, late_days, has_45_years
    )

    zakladni  = params.zakladni_vymera
    procentni = max(procentni_raw + late_bonus - early_penalty + children_bonus, zakladni)

    return PensionResult(
        year=year_of_retirement,
        zakladni_vymera=zakladni,
        procentni_vymera=procentni,
        total_pension=zakladni + procentni,
        ovz=ovz,
        vypoctovy_zaklad=vz,
        years_of_insurance=years_of_insurance,
        pct_rate=params.pct_per_year,
        children_bonus=children_bonus,
        early_penalty=early_penalty,
        late_bonus=late_bonus,
        params=params,
    )


def calculate_pension_simple(
    monthly_gross: float,
    year_of_retirement: int,
    years_of_insurance: int = INSURANCE_YEARS,
    children_raised: int = 0,
    early_days: int = 0,
    late_days: int = 0,
    has_45_years: bool = False,
) -> PensionResult:
    """Rychlý odhad důchodu při konstantním měsíčním hrubém příjmu.

    OVZ ≈ monthly_gross (koeficienty nárůstu VVZ se za konstantního příjmu
    vyruší -- vzájemná normalizace na aktuální mzdovou úroveň).

    Poznámka: Tato zjednodušená verze předpokládá vyměřovací základ SP =
    100 % hrubé mzdy (zaměstnanec).  Pro OSVC je VZ jen 55 % zisku, tj.
    správný odhad důchodu OSVC se počítá jako
    ``calculate_pension_simple(0.55 * monthly_profit, ...)`` nebo lze použít
    funkce ``pension_osvc()`` v ``problemy_cz_duchod``.

    Parameters
    ----------
    monthly_gross:
        Konstantní měsíční hrubá mzda v Kč (v dnešních cenách).
    year_of_retirement:
        Rok přiznání důchodu.
    years_of_insurance:
        Pojistná doba v celých rocích (výchozí = INSURANCE_YEARS = 40).
    """
    params = get_params(year_of_retirement)
    ovz    = _ceil_int(monthly_gross)

    vz, procentni_raw, late_bonus, early_penalty, children_bonus = _compute_components(
        ovz, params, years_of_insurance, children_raised, early_days, late_days, has_45_years
    )

    zakladni  = params.zakladni_vymera
    procentni = max(procentni_raw + late_bonus - early_penalty + children_bonus, zakladni)

    return PensionResult(
        year=year_of_retirement,
        zakladni_vymera=zakladni,
        procentni_vymera=procentni,
        total_pension=zakladni + procentni,
        ovz=ovz,
        vypoctovy_zaklad=vz,
        years_of_insurance=years_of_insurance,
        pct_rate=params.pct_per_year,
        children_bonus=children_bonus,
        early_penalty=early_penalty,
        late_bonus=late_bonus,
        params=params,
    )


# ── CLI výstup ────────────────────────────────────────────────────────────────

def print_result(r: PensionResult) -> None:
    p = r.params
    print(f"{'='*60}")
    print(f"  VÝPOČET STAROBNÍHO DŮCHODU -- rok přiznání {r.year}")
    print(f"{'='*60}")
    print(f"  Průměrná mzda (§ 15 odst. 5):  {p.prumerna_mzda:>10,} Kč")
    print(f"  1. redukční hranice (44 %):     {p.rh1:>10,} Kč")
    print(f"  2. redukční hranice (400 %):    {p.rh2:>10,} Kč")
    print(f"  Podíl pod 1. RH (§ 15):         {p.first_limit_pct*100:>9.0f} %")
    print(f"  Sazba za rok pojištění (§ 34):  {p.pct_per_year:>9.3f} %")
    print(f"{'─'*60}")
    print(f"  Osobní vyměřovací základ:       {r.ovz:>10,} Kč")
    print(f"  Výpočtový základ (§ 15):        {r.vypoctovy_zaklad:>10,} Kč")
    print(f"  Pojistná doba:                  {r.years_of_insurance:>10} let")
    print(f"{'─'*60}")
    print(f"  Základní výměra (§ 33):         {r.zakladni_vymera:>10,} Kč")
    print(f"  Procentní výměra (§ 34):        {r.procentni_vymera:>10,} Kč")
    if r.children_bonus:
        print(f"    z toho bonus za děti (§ 34a):{r.children_bonus:>10,} Kč")
    if r.late_bonus:
        print(f"    z toho zvýšení za odklad:    {r.late_bonus:>10,} Kč")
    if r.early_penalty:
        print(f"    z toho krácení (předčasný):  {-r.early_penalty:>10,} Kč")
    print(f"{'─'*60}")
    print(f"  CELKEM MĚSÍČNÍ DŮCHOD:          {r.total_pension:>10,} Kč")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("DEMO -- Odhad starobního důchodu pro rok 2026\n")

    cases = [
        ("Průměrný příjem, 40 let",        45_000, 2026, 40, {}),
        ("Vyšší příjem, 42 let, 2 děti",   80_000, 2026, 42, {"children_raised": 2}),
        ("Nižší příjem, 35 let",           25_000, 2026, 35, {}),
        ("Předčasný odchod 720 dní",       45_000, 2026, 38, {"early_days": 720}),
        ("Odložený důchod 360 dní",        50_000, 2026, 43, {"late_days": 360}),
    ]
    for title, gross, yr, ins, kw in cases:
        print(f"{'─'*60}\n{title}")
        print_result(calculate_pension_simple(gross, yr, ins, **kw))
