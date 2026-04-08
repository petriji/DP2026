"""
Czech Old-Age Pension (Starobní důchod) Calculation Model
=========================================================
Based on Zákon č. 155/1995 Sb. o důchodovém pojištění (as amended).

Key legislative references:
  - § 4   : Pension = základní výměra + procentní výměra
  - § 15  : Výpočtový základ (calculation base) from OVZ via reduction limits
  - § 16  : Osobní vyměřovací základ (personal assessment base)
  - § 17  : Koeficient nárůstu VVZ, přepočítací koeficient
  - § 18  : Rozhodné období (decisive period)
  - § 33  : Základní výměra = 10% průměrné mzdy
  - § 34  : Procentní výměra = rate × výpočtový základ × years
  - § 34a : Bonus per raised child (+500 CZK)
  - § 36  : Early retirement penalty
  - § 54  : Rounding rules

Government decree (Nařízení vlády) sets annual parameters:
  - Všeobecný vyměřovací základ (VVZ)
  - Přepočítací koeficient (PK)
  - Reduction limits and základní výměra (derived from průměrná mzda)
"""

import math
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
#  Annual parameters set by government decrees (NV)
# ---------------------------------------------------------------------------

# VVZ and PK values by year (source: annual NVs published in Sbírka zákonů)
# VVZ = všeobecný vyměřovací základ (average wage proxy for the given year)
# PK  = přepočítací koeficient for that VVZ year
VVZ_PK: dict[int, tuple[int, float]] = {
    # year: (VVZ, PK)
    # Historical values (selected, extend as needed):
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
    # For 2024, the NV is published in Sep 2025 – update when available.
    # Using an estimate here; replace with official values:
    2024: (43_967, 1.0500),
}


@dataclass
class PensionParams:
    """Parameters for a specific retirement year, derived from VVZ/PK."""
    year: int
    prumerna_mzda: int          # průměrná mzda for this year (§15(5))
    reduction_limit_1: int      # 1st redukční hranice (44% prům. mzdy)
    reduction_limit_2: int      # 2nd redukční hranice (400% prům. mzdy)
    zakladni_vymera: int        # základní výměra (10% prům. mzdy, rounded ↑ to 10)
    pct_rate_per_year: float    # % of VZ per insurance year (§34(1))
    first_limit_pct: float      # share counted below 1st limit (§15)


def _ceil_int(x: float) -> int:
    """Round up to whole CZK (§16(8), §15(4))."""
    return math.ceil(x)


def _ceil_to_10(x: float) -> int:
    """Round up to nearest 10 CZK (§54(3) for základní výměra)."""
    return math.ceil(x / 10) * 10


def get_prumerna_mzda(year: int) -> int:
    """
    Průměrná mzda for a given year (§15(5)).
    = VVZ(year-2) × PK(year-2), rounded up to whole CZK.
    Must not be lower than previous year's value.
    """
    ref_year = year - 2
    if ref_year not in VVZ_PK:
        raise ValueError(
            f"VVZ/PK data for year {ref_year} not available. "
            f"Add it to VVZ_PK dict."
        )
    vvz, pk = VVZ_PK[ref_year]
    pm = _ceil_int(vvz * pk)
    # Must not be lower than previous year (§15(5) last sentence)
    try:
        pm_prev = get_prumerna_mzda(year - 1)
        pm = max(pm, pm_prev)
    except (ValueError, RecursionError):
        pass
    return pm


def _pct_rate_per_year(year: int) -> float:
    """Percentage rate per year of insurance (§34(1))."""
    if year < 2026:
        return 1.5
    rates = {
        2026: 1.495, 2027: 1.490, 2028: 1.485, 2029: 1.480,
        2030: 1.475, 2031: 1.470, 2032: 1.465, 2033: 1.460,
        2034: 1.455,
    }
    return rates.get(year, 1.450)  # after 2034 → 1.450%


def _first_limit_pct(year: int) -> float:
    """
    Percentage counted up to 1st reduction limit (§15(2)-(3)).
    2015-2025: 100%
    2026: 99%, 2027: 98%, ..., after 2034: 90%
    """
    if year <= 2025:
        return 1.00
    pcts = {
        2026: 0.99, 2027: 0.98, 2028: 0.97, 2029: 0.96,
        2030: 0.95, 2031: 0.94, 2032: 0.93, 2033: 0.92,
        2034: 0.91,
    }
    return pcts.get(year, 0.90)  # after 2034 → 90%


def get_params(year: int) -> PensionParams:
    """Compute all pension parameters for a retirement year."""
    pm = get_prumerna_mzda(year)
    rl1 = _ceil_int(0.44 * pm)    # §15(4): 44% průměrné mzdy
    rl2 = _ceil_int(4.00 * pm)    # §15(4): 400% průměrné mzdy
    zv = _ceil_to_10(0.10 * pm)   # §33(1): 10% průměrné mzdy
    return PensionParams(
        year=year,
        prumerna_mzda=pm,
        reduction_limit_1=rl1,
        reduction_limit_2=rl2,
        zakladni_vymera=zv,
        pct_rate_per_year=_pct_rate_per_year(year),
        first_limit_pct=_first_limit_pct(year),
    )


# ---------------------------------------------------------------------------
#  Osobní vyměřovací základ (OVZ) – §16
# ---------------------------------------------------------------------------

def compute_ovz(
    annual_earnings: dict[int, float],
    excluded_days: int,
    year_of_retirement: int,
    year_of_birth: int,
) -> int:
    """
    Compute osobní vyměřovací základ (§16).

    Parameters
    ----------
    annual_earnings : dict[int, float]
        Mapping year → gross annual assessment base (vyměřovací základ)
        for each year in the decisive period.
    excluded_days : int
        Total vyloučené doby in calendar days (§16(4)-(5)).
    year_of_retirement : int
        Year in which pension is claimed.
    year_of_birth : int
        Year of birth (to determine decisive period start).

    Returns
    -------
    int
        Osobní vyměřovací základ in CZK (rounded up, §16(8)).
    """
    # Decisive period (§18(1)):
    # starts: calendar year after the year insured turned 18
    # ends:   calendar year before year of retirement
    period_start = year_of_birth + 19
    period_end = year_of_retirement - 1

    total_days = 0
    sum_annual_bases = 0.0

    for y in range(period_start, period_end + 1):
        # Calendar days in year
        import calendar
        days_in_year = 366 if calendar.isleap(y) else 365
        total_days += days_in_year

        earnings = annual_earnings.get(y, 0.0)
        # Compute koeficient nárůstu VVZ (§17(1))
        coeff = _compute_vvz_growth_coeff(y, year_of_retirement)
        annual_base = earnings * coeff
        sum_annual_bases += annual_base

    effective_days = total_days - excluded_days
    if effective_days <= 0:
        raise ValueError("Effective days in decisive period must be > 0")

    ovz = 30.4167 * sum_annual_bases / effective_days
    return _ceil_int(ovz)


def _compute_vvz_growth_coeff(
    earnings_year: int,
    retirement_year: int,
) -> float:
    """
    Koeficient nárůstu VVZ (§17(1)).
    = VVZ(ret_year-2) × PK(ret_year-2) / VVZ(earnings_year)
    Minimum value is 1.0.
    For earnings_year == ret_year-1 or ret_year → always 1.0 (§17(3)).
    """
    if earnings_year >= retirement_year - 1:
        return 1.0

    ref_year = retirement_year - 2
    if ref_year not in VVZ_PK or earnings_year not in VVZ_PK:
        # If data not available, return 1.0 (conservative)
        return 1.0

    vvz_ref, pk_ref = VVZ_PK[ref_year]
    vvz_earn, _ = VVZ_PK[earnings_year]

    coeff = (vvz_ref * pk_ref) / vvz_earn
    return max(coeff, 1.0)


# ---------------------------------------------------------------------------
#  Výpočtový základ (VZ) – §15
# ---------------------------------------------------------------------------

def compute_vypoctovy_zaklad(ovz: int, params: PensionParams) -> int:
    """
    Compute výpočtový základ from OVZ via reduction limits (§15).

    For post-2014:
      - up to 1st limit: first_limit_pct (100% until 2025, then declining)
      - from 1st to 2nd limit: 26%
      - above 2nd limit: 0% (ignored)

    Returns rounded-up CZK (§16(8)).
    """
    rl1 = params.reduction_limit_1
    rl2 = params.reduction_limit_2
    pct1 = params.first_limit_pct

    if ovz <= rl1:
        vz = ovz * pct1
    elif ovz <= rl2:
        vz = rl1 * pct1 + (ovz - rl1) * 0.26
    else:
        vz = rl1 * pct1 + (rl2 - rl1) * 0.26
        # above rl2 is ignored (§15(2)(c) / §15(3)(c))

    return _ceil_int(vz)


# ---------------------------------------------------------------------------
#  Final pension calculation
# ---------------------------------------------------------------------------

@dataclass
class PensionResult:
    """Result of pension calculation."""
    year: int
    zakladni_vymera: int         # basic component (CZK/month)
    procentni_vymera: int        # percentage component (CZK/month)
    total_pension: int           # total monthly pension (CZK)
    # Detailed breakdown:
    ovz: int                     # osobní vyměřovací základ
    vypoctovy_zaklad: int        # výpočtový základ
    years_of_insurance: int      # full years of insurance
    pct_rate: float              # percentage rate used
    children_bonus: int          # bonus for raised children
    early_penalty: int           # early retirement reduction
    late_bonus: int              # late retirement bonus
    params: PensionParams        # parameters used


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
    """
    Calculate Czech old-age pension (starobní důchod).

    Parameters
    ----------
    annual_earnings : dict[int, float]
        Year → annual gross assessment base (vyměřovací základ) in CZK.
        For employees this is the gross wage used for social insurance.
    year_of_birth : int
        Year of birth.
    year_of_retirement : int
        Year pension is claimed.
    years_of_insurance : int
        Total full years (365 days each) of insurance (doba pojištění).
    excluded_days : int
        Vyloučené doby in calendar days (§16(4)-(5)).
    children_raised : int
        Number of children raised (§34a, +500 CZK each).
    early_days : int
        Calendar days of early retirement before retirement age (§36).
        Set to 0 if retiring at or after retirement age.
    late_days : int
        Calendar days of continued work after entitlement without
        claiming pension (§34(3)). 
    has_45_years : bool
        Whether the person has ≥45 years of insurance (affects early
        retirement penalty rate: 0.75% vs 1.5% per 90 days).

    Returns
    -------
    PensionResult
    """
    params = get_params(year_of_retirement)

    # 1. Osobní vyměřovací základ (§16)
    ovz = compute_ovz(annual_earnings, excluded_days, year_of_retirement, year_of_birth)

    # 2. Výpočtový základ (§15)
    vz = compute_vypoctovy_zaklad(ovz, params)

    # 3. Základní výměra (§33(1))
    zakladni = params.zakladni_vymera

    # 4. Procentní výměra (§34(1))
    rate = params.pct_rate_per_year
    procentni_raw = rate / 100.0 * vz * years_of_insurance

    # 5. Late retirement bonus (§34(3)):
    #    +1.5% výpočtového základu per each 90 calendar days
    late_periods = late_days // 90
    late_bonus = _ceil_int(0.015 * vz * late_periods)

    # 6. Early retirement penalty (§36):
    #    has_45_years → -0.75% VZ per each (even started) 90 days
    #    otherwise   → -1.50% VZ per each (even started) 90 days
    early_penalty = 0
    if early_days > 0:
        early_periods = math.ceil(early_days / 90)
        penalty_rate = 0.0075 if has_45_years else 0.015
        early_penalty = _ceil_int(penalty_rate * vz * early_periods)

    # 7. Children bonus (§34a(2)): 500 CZK per child
    children_bonus = 500 * children_raised

    # Procentní výměra total
    procentni = _ceil_int(procentni_raw) + late_bonus - early_penalty + children_bonus

    # Minimum procentní výměra = základní výměra (§33(2) sentence 3)
    procentni = max(procentni, zakladni)

    # Procentní výměra rounded up to whole CZK (§54(3))
    procentni = _ceil_int(procentni)

    total = zakladni + procentni

    return PensionResult(
        year=year_of_retirement,
        zakladni_vymera=zakladni,
        procentni_vymera=procentni,
        total_pension=total,
        ovz=ovz,
        vypoctovy_zaklad=vz,
        years_of_insurance=years_of_insurance,
        pct_rate=rate,
        children_bonus=children_bonus,
        early_penalty=early_penalty,
        late_bonus=late_bonus,
        params=params,
    )


# ---------------------------------------------------------------------------
#  Simplified calculation (constant income assumption)
# ---------------------------------------------------------------------------

def calculate_pension_simple(
    monthly_gross: float,
    year_of_birth: int,
    year_of_retirement: int,
    years_of_insurance: int,
    children_raised: int = 0,
    early_days: int = 0,
    late_days: int = 0,
    has_45_years: bool = False,
) -> PensionResult:
    """
    Simplified pension calculation assuming constant monthly gross income
    over the entire decisive period (no inflation adjustment needed).

    This provides a quick estimate. For accurate results, use
    `calculate_pension()` with actual yearly earnings.

    Parameters
    ----------
    monthly_gross : float
        Constant monthly gross salary in CZK (treated as today's value).
    ...other params same as calculate_pension()
    """
    params = get_params(year_of_retirement)

    # With constant income = monthly_gross, OVZ ≈ monthly_gross
    # (since all yearly coefficients would normalize to current wages)
    ovz = _ceil_int(monthly_gross)

    vz = compute_vypoctovy_zaklad(ovz, params)

    zakladni = params.zakladni_vymera

    rate = params.pct_rate_per_year
    procentni_raw = rate / 100.0 * vz * years_of_insurance

    late_periods = late_days // 90
    late_bonus = _ceil_int(0.015 * vz * late_periods)

    early_penalty = 0
    if early_days > 0:
        early_periods = math.ceil(early_days / 90)
        penalty_rate = 0.0075 if has_45_years else 0.015
        early_penalty = _ceil_int(penalty_rate * vz * early_periods)

    children_bonus = 500 * children_raised

    procentni = _ceil_int(procentni_raw) + late_bonus - early_penalty + children_bonus
    procentni = max(procentni, zakladni)
    procentni = _ceil_int(procentni)

    total = zakladni + procentni

    return PensionResult(
        year=year_of_retirement,
        zakladni_vymera=zakladni,
        procentni_vymera=procentni,
        total_pension=total,
        ovz=ovz,
        vypoctovy_zaklad=vz,
        years_of_insurance=years_of_insurance,
        pct_rate=rate,
        children_bonus=children_bonus,
        early_penalty=early_penalty,
        late_bonus=late_bonus,
        params=params,
    )


# ---------------------------------------------------------------------------
#  Demo / CLI
# ---------------------------------------------------------------------------

def print_result(r: PensionResult) -> None:
    """Pretty-print a pension calculation result."""
    p = r.params
    print(f"{'='*60}")
    print(f"  VÝPOČET STAROBNÍHO DŮCHODU – rok přiznání {r.year}")
    print(f"{'='*60}")
    print(f"  Průměrná mzda (§15(5)):       {p.prumerna_mzda:>10,} Kč")
    print(f"  1. redukční hranice (44%):     {p.reduction_limit_1:>10,} Kč")
    print(f"  2. redukční hranice (400%):    {p.reduction_limit_2:>10,} Kč")
    print(f"  Podíl do 1.RH (§15):          {p.first_limit_pct*100:>9.0f} %")
    print(f"  Sazba za rok pojištění (§34):  {p.pct_rate_per_year:>9.3f} %")
    print(f"{'─'*60}")
    print(f"  Osobní vyměřovací základ:      {r.ovz:>10,} Kč")
    print(f"  Výpočtový základ (§15):        {r.vypoctovy_zaklad:>10,} Kč")
    print(f"  Doba pojištění:                {r.years_of_insurance:>10} let")
    print(f"{'─'*60}")
    print(f"  Základní výměra (§33):         {r.zakladni_vymera:>10,} Kč")
    print(f"  Procentní výměra (§34):        {r.procentni_vymera:>10,} Kč")
    if r.children_bonus > 0:
        print(f"    z toho bonus za děti (§34a): {r.children_bonus:>10,} Kč")
    if r.late_bonus > 0:
        print(f"    z toho bonus za odklad:      {r.late_bonus:>10,} Kč")
    if r.early_penalty > 0:
        print(f"    z toho srážka za předčasný:  {-r.early_penalty:>10,} Kč")
    print(f"{'─'*60}")
    print(f"  CELKEM MĚSÍČNÍ DŮCHOD:         {r.total_pension:>10,} Kč")
    print(f"{'='*60}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("  DEMO: Odhad starobního důchodu pro rok 2026")
    print("=" * 60)
    print()

    # Show parameters for 2026
    params_2026 = get_params(2026)
    print(f"Parametry pro rok 2026:")
    print(f"  Průměrná mzda:        {params_2026.prumerna_mzda:>10,} Kč")
    print(f"  1. redukční hranice:  {params_2026.reduction_limit_1:>10,} Kč")
    print(f"  2. redukční hranice:  {params_2026.reduction_limit_2:>10,} Kč")
    print(f"  Základní výměra:      {params_2026.zakladni_vymera:>10,} Kč")
    print()

    # Example 1: Average earner, 40 years of insurance
    print("─" * 60)
    print("Příklad 1: Průměrný příjem, 40 let pojištění")
    r1 = calculate_pension_simple(
        monthly_gross=45_000,
        year_of_birth=1961,
        year_of_retirement=2026,
        years_of_insurance=40,
    )
    print_result(r1)

    # Example 2: Higher earner, 42 years, 2 children
    print("─" * 60)
    print("Příklad 2: Vyšší příjem, 42 let pojištění, 2 děti")
    r2 = calculate_pension_simple(
        monthly_gross=80_000,
        year_of_birth=1961,
        year_of_retirement=2026,
        years_of_insurance=42,
        children_raised=2,
    )
    print_result(r2)

    # Example 3: Lower earner, 35 years
    print("─" * 60)
    print("Příklad 3: Nižší příjem, 35 let pojištění")
    r3 = calculate_pension_simple(
        monthly_gross=25_000,
        year_of_birth=1961,
        year_of_retirement=2026,
        years_of_insurance=35,
    )
    print_result(r3)

    # Example 4: Early retirement (2 years early, no 45-year condition)
    print("─" * 60)
    print("Příklad 4: Předčasný důchod (720 dní před důch. věkem)")
    r4 = calculate_pension_simple(
        monthly_gross=45_000,
        year_of_birth=1963,
        year_of_retirement=2026,
        years_of_insurance=38,
        early_days=720,
        has_45_years=False,
    )
    print_result(r4)

    # Example 5: Late retirement (360 days after entitlement)
    print("─" * 60)
    print("Příklad 5: Odložený důchod (360 dní po nároku)")
    r5 = calculate_pension_simple(
        monthly_gross=50_000,
        year_of_birth=1959,
        year_of_retirement=2026,
        years_of_insurance=43,
        late_days=360,
    )
    print_result(r5)
