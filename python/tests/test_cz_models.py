"""Verifikace CZ daňového a důchodového modelu pro 2026.

Očekávané hodnoty počítány ručně podle § zákona (ZDP, zák. č. 589/1992 Sb.,
zák. č. 592/1992 Sb., zák. č. 155/1995 Sb., zák. č. 270/2023 Sb.) a měly by se
shodovat s veřejnými kalkulačkami (kurzy.cz, MPSV) pro standardního
poplatníka bez doplňkových slev (děti, manželka, ZTP, studium).

Spuštění: ``pytest python/tests/test_cz_models.py -v``
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analyses"))

from cz_tax_model import (
    AVG_WAGE,
    MAX_SP_BASE_MONTHLY,
    OSVC_MIN_HEALTH_BASE,
    OSVC_MIN_MONTHLY_BASE,
    PAUSALNI_DAN_BREAKDOWN,
    EMPLOYER_INS_RATE,
    tax_breakdown,
)
from problemy_cz_duchod import (
    RH1, RH2, ZAKLADNI_VYMERA, PCT_PER_YEAR,
    pension_employee, pension_osvc, pension_osvc_vydajovy,
)


# ── Konstanty ─────────────────────────────────────────────────────────────────

def test_constants_2026() -> None:
    assert AVG_WAGE == 48_967
    assert MAX_SP_BASE_MONTHLY == 4 * AVG_WAGE == 195_868
    assert OSVC_MIN_HEALTH_BASE == 24_484          # ⌈48 967 / 2⌉
    assert OSVC_MIN_MONTHLY_BASE == 19_587         # 40 % prům. mzdy
    assert RH1 == 21_546                           # 44 % prům. mzdy
    assert RH2 == 195_868 == MAX_SP_BASE_MONTHLY   # 400 % prům. mzdy = SP cap
    assert ZAKLADNI_VYMERA == 4_900
    assert PCT_PER_YEAR == 0.01495


def test_pausalni_breakdown_consistency() -> None:
    """Total = SP + ZP + DPFO pro každé pásmo paušální daně."""
    for b in PAUSALNI_DAN_BREAKDOWN:
        assert b["sp"] + b["zp"] + b["dpfo"] == b["total"], b


# ── Zaměstnanec (T1–T4) ───────────────────────────────────────────────────────

@pytest.mark.parametrize("gross,exp", [
    (30_000,  {"dpfo": 1_930,  "sp": 2_130,  "zp": 1_350, "net": 24_590}),
    (48_000,  {"dpfo": 4_630,  "sp": 3_408,  "zp": 2_160, "net": 37_802}),
    (100_000, {"dpfo": 12_430, "sp": 7_100,  "zp": 4_500, "net": 75_970}),
    # T4: SP cap aktivní (gross > 195 868); DPFO progresivní 23 % nad 146 901
    #   DPFO = 146 901·0,15 + 53 099·0,23 − 2 570 = 31 678
    #   SP   = 0,071 · 195 868 = 13 907 (cap)
    #   ZP   = 0,045 · 200 000 = 9 000
    (200_000, {"dpfo": 31_678, "sp": 13_907, "zp": 9_000, "net": 145_415}),
])
def test_employee_breakdown(gross: int, exp: dict[str, int]) -> None:
    """Zaměstnanec: hrubá → DPFO/SP/ZP/čistá (bez dětí, manželky)."""
    if gross <= MAX_SP_BASE_MONTHLY:
        cost = gross * (1 + EMPLOYER_INS_RATE)
    else:
        cost = gross * 1.09 + 0.248 * MAX_SP_BASE_MONTHLY
    r = tax_breakdown(cost, mode="employee")
    assert round(r["dpfo_net"])    == exp["dpfo"]
    assert round(r["sp"])          == exp["sp"]
    assert round(r["zp"])          == exp["zp"]
    assert round(r["net_income"])  == exp["net"]


# ── OSVČ (T5–T8) ─────────────────────────────────────────────────────────────

def test_osvc_standardni_zisk_60k() -> None:
    """OSVČ skutečné výdaje, zisk 60 000 Kč/měs.

    SP VZ = 33 000 (55 %); SP = 9 636.
    ZP VZ = max(30 000, 24 484) = 30 000; ZP = 4 050.
    Pozn.: standardní režim s expense_rate=0 (zisk = ZD DPFO).
    """
    r = tax_breakdown(60_000, mode="osvc_vydajovy", expense_rate=0.0)
    assert round(r["sp_vz"])    == 33_000
    assert round(r["sp"])       == 9_636
    assert round(r["zp_vz"])    == 30_000
    assert round(r["zp"])       == 4_050
    # Pro expense_rate=0: SP/ZP NEjsou odečitatelné (paušál 0 %), ZD = 60 000
    assert round(r["dpfo_net"]) == 6_430   # 60 000·0,15 − 2 570


def test_osvc_pausal_60_pct_revenue_50k() -> None:
    """OSVČ výdajový paušál 60 %, příjmy 50 000 Kč/měs.

    ZD = 20 000; SP VZ = max(11 000, 19 587) = 19 587 → SP = 5 719,40.
    ZP VZ = max(10 000, 24 484) = 24 484 → ZP = 3 305,34.
    DPFO = 20 000·0,15 − 2 570 = 430. Čistý zisk z paušálu = 10 545,26.
    """
    r = tax_breakdown(50_000, mode="osvc_vydajovy", expense_rate=0.6)
    assert r["sp_vz"]            == 19_587
    assert round(r["sp"], 2)     == 5_719.40
    assert r["zp_vz"]            == 24_484
    assert round(r["zp"], 2)     == 3_305.34
    assert round(r["dpfo_net"])  == 430
    assert round(r["net_income"], 2) == 10_545.26


def test_osvc_pausalni_dan_pasmo1() -> None:
    """OSVČ paušální daň pásmo 1, příjmy 50 000 Kč/měs. → total 9 984 Kč."""
    r = tax_breakdown(50_000, mode="osvc_pausalni", pausalni_pasmo=1)
    assert r["total_charges"] == 9_984
    assert r["sp"]            == 6_578
    assert r["zp"]            == 3_306
    assert r["dpfo_net"]      == 100
    assert r["net_income"]    == 50_000 - 9_984


def test_osvc_pausal_60_pct_with_dph_revenue_200k() -> None:
    """OSVČ paušál 60 %, příjmy 200 000 Kč/měs. (nad prahem DPH 166 666).

    DPH 21 % → ponechá si 200 000 / 1,21 = 165 289,26.
    DPH odvedené státu: 34 710,74.
    ZD = 0,4 · 165 289,26 = 66 115,70.
    """
    r = tax_breakdown(200_000, mode="osvc_vydajovy", expense_rate=0.6)
    assert round(r["dph"], 2)            == 34_710.74
    assert round(r["zd"], 2)             == 66_115.70
    assert round(r["total_charges"], 2)  == 57_139.09
    assert round(r["tax_wedge_pct"], 2)  == 28.57


# ── Důchod (T9–T10) ───────────────────────────────────────────────────────────

def test_pension_gross_30k_40_years() -> None:
    """Zaměstnanec, hrubá 30 000 Kč/měs., 40 let pojištění (2026).

    OVZ = 30 000.
    ROVZ = 21 546·0,99 + (30 000 − 21 546)·0,26
         = 21 330,54 + 2 198,04 = 23 528,58.
    Procentní = ⌈23 528,58 · 40 · 0,01495⌉ = ⌈14 070,09⌉ ≈ 14 070,09 (bez ceilu).
    Celkem = 4 900 + 14 070,09 ≈ 18 970,09.
    """
    p = float(pension_employee(30_000, 40))
    assert round(p, 2) == 18_970.09


def test_pension_above_rh2_no_third_band() -> None:
    """Důchod při OVZ = 250 000 — testuje zrušení 3. pásma (270/2023, § 15).

    ROVZ = 21 546·0,99 + (195 868 − 21 546)·0,26 = 21 330,54 + 45 323,72 = 66 654,26.
    (3. pásmo nad RH2 → 0 %.)
    Procentní = 66 654,26 · 40 · 0,01495 = 39 859,25.
    Celkem = 4 900 + 39 859,25 = 44 759,25.
    """
    p = float(pension_employee(250_000, 40))
    assert round(p, 2) == 44_759.25
