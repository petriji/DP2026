"""Generate a sourced workforce-structure table for chapter 4.

The table combines:
- ISPV employee headcounts (MZS + PLS),
- CSSZ open-data counts of self-employed persons (OSVC),
- PAQ range for estimated svarcsystem prevalence (parsed from bibliography note).

Output
------
- latex/texparts/python/stav_struktura_prac_sily.tex
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from statout.table import save_table_tex
from stattool.dataset import Dataset
from stattool.data_quality import warn_non_target_year
from stattool.fetch import fetch, fetch_eurostat


ISPV_MZS_URL = (
    "https://www.ispv.cz/getattachment/b568f503-6978-4af7-9f8a-d5aef8e46619"
    "/CR_254_MZS-xlsx.aspx?disposition=attachment"
)
ISPV_PLS_URL = (
    "https://www.ispv.cz/getattachment/64ad14f0-4b5b-4192-a2e2-3acceedff267"
    "/CR_254_PLS-xlsx.aspx?disposition=attachment"
)
ISPV_YEAR = 2025

CSSZ_OSVC_CSV_URL = "https://data.cssz.cz/dump/prehled-o-celkovem-poctu-osvc-v-cr.csv"

ROOT_DIR = Path(__file__).resolve().parents[2]
BIB_PATH = ROOT_DIR / "latex" / "socialnidialog.bib"


def _format_int(val: float) -> str:
    return f"{int(round(val)):,}".replace(",", r"\,")


def _format_pct(val: float) -> str:
    return f"{val:.1f}"


def _format_range(lo: int, hi: int) -> str:
    return f"{_format_int(lo)}--{_format_int(hi)}"


def _extract_employee_count(df: pd.DataFrame) -> int:
    """Extract employee count from an ISPV M0 sheet."""
    for _, row in df.iterrows():
        row_lc = row.astype(str).str.lower()
        if row_lc.str.contains(r"po[čc]et.{0,10}zam[ěe]st", regex=True).any():
            nums = pd.to_numeric(row, errors="coerce").dropna()
            valid = nums[(nums > 100_000) & (nums < 10_000_000)]
            if not valid.empty:
                return int(valid.iloc[-1])
            valid_thousands = nums[(nums > 100) & (nums < 10_000)]
            if not valid_thousands.empty:
                return int(valid_thousands.iloc[-1]) * 1_000
    raise ValueError("Employee count row not found in ISPV workbook")


def _fetch_ispv_headcount(url: str, sheet_hint: str) -> int:
    path = fetch(url, suffix=".xlsx")
    with open(path, "rb") as fh:
        if fh.read(2) != b"PK":
            raise ValueError(f"Downloaded file is not XLSX: {path}")

    xls = pd.ExcelFile(path, engine="openpyxl")
    m0_sheets = [s for s in xls.sheet_names if s.endswith("-M0")]
    if m0_sheets:
        sheet = next((s for s in m0_sheets if sheet_hint in s.upper()), m0_sheets[0])
    else:
        sheet = next((s for s in xls.sheet_names if "M0" in s.upper()), xls.sheet_names[0])

    df = pd.read_excel(path, sheet_name=sheet, header=None)
    return _extract_employee_count(df)


def _fetch_cssz_osvc_counts(preferred_year: int) -> tuple[int, int, pd.Timestamp]:
    path = fetch(CSSZ_OSVC_CSV_URL, suffix=".csv")
    df = pd.read_csv(path)

    required = [
        "datum",
        "vykonavana_cinnost_hlavni",
        "vykonavana_cinnost_vedlejsi",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSSZ dataset missing columns: {missing}")

    df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
    df["vykonavana_cinnost_hlavni"] = pd.to_numeric(df["vykonavana_cinnost_hlavni"], errors="coerce")
    df["vykonavana_cinnost_vedlejsi"] = pd.to_numeric(df["vykonavana_cinnost_vedlejsi"], errors="coerce")
    df = df.dropna(subset=["datum", "vykonavana_cinnost_hlavni", "vykonavana_cinnost_vedlejsi"])

    same_year = df[df["datum"].dt.year == preferred_year].sort_values("datum")
    if not same_year.empty:
        row = same_year.iloc[-1]
    else:
        row = df.sort_values("datum").iloc[-1]

    main = int(row["vykonavana_cinnost_hlavni"])
    secondary = int(row["vykonavana_cinnost_vedlejsi"])
    date = pd.Timestamp(row["datum"])
    return main, secondary, date


def _fetch_cz_employment_rate_20_64(preferred_year: int) -> tuple[float, int]:
    """Fetch CZ employment rate 20--64 from the same Eurostat source as long table.

    Dataset: lfsi_emp_a, filter A.EMP_LFS.T.Y20-64.PC_POP.CZ
    """
    path = fetch_eurostat("lfsi_emp_a", "A.EMP_LFS.T.Y20-64.PC_POP.CZ")
    ds = Dataset.from_sdmx_csv(
        path,
        name="Employment rate 20--64 (CZ)",
        unit="%",
        source_url="Eurostat/lfsi_emp_a",
    )

    df = ds.df.copy().sort_values(ds.time_col, ascending=False)
    df = df[df[ds.geo_col] == "CZ"].dropna(subset=[ds.value_col])

    exact = df[df[ds.time_col] == preferred_year]
    if not exact.empty:
        row = exact.iloc[0]
        return float(row[ds.value_col]), int(row[ds.time_col])

    prior = df[df[ds.time_col] <= preferred_year]
    if not prior.empty:
        row = prior.iloc[0]
        return float(row[ds.value_col]), int(row[ds.time_col])

    raise ValueError("Could not find CZ employment rate in Eurostat lfsi_emp_a")


def _extract_paq_svarc_range() -> tuple[int, int]:
    """Extract 100--175 thousand range from PAQ entry in socialnidialog.bib."""
    text = BIB_PATH.read_text(encoding="utf-8")
    m_entry = re.search(r"@[a-zA-Z]+\{PAQ_Svarcsystem,", text)
    if not m_entry:
        raise ValueError("PAQ_Svarcsystem entry not found in bibliography")

    start = m_entry.start()
    end = text.find("\n@", start + 1)
    if end == -1:
        end = len(text)
    entry = text[start:end]

    m_range = re.search(r"(\d{2,3})\s*--\s*(\d{2,3})\s*\\,?\s*tis", entry, flags=re.IGNORECASE)
    if not m_range:
        raise ValueError("Could not parse svarcsystem range from PAQ_Svarcsystem note")

    lo = int(m_range.group(1)) * 1_000
    hi = int(m_range.group(2)) * 1_000
    if lo > hi:
        lo, hi = hi, lo
    return lo, hi


def main() -> None:
    print("Fetching ISPV employee headcounts ...")
    n_mzs = _fetch_ispv_headcount(ISPV_MZS_URL, "MZS")
    n_pls = _fetch_ispv_headcount(ISPV_PLS_URL, "PLS")
    n_emp = n_mzs + n_pls
    warn_non_target_year(source="MPSV ISPV", year=ISPV_YEAR, context="Workforce structure table")

    print("Fetching CSSZ OSVC counts ...")
    osvc_main, osvc_secondary, cssz_date = _fetch_cssz_osvc_counts(preferred_year=ISPV_YEAR)
    osvc_total = osvc_main + osvc_secondary
    warn_non_target_year(source="CSSZ otevrena data", year=int(cssz_date.year), context="Workforce structure table")

    print("Extracting PAQ svarcsystem range ...")
    svarc_lo, svarc_hi = _extract_paq_svarc_range()

    print("Fetching CZ employment rate 20--64 (Eurostat lfsi_emp_a) ...")
    emp_rate_cz, emp_rate_year = _fetch_cz_employment_rate_20_64(preferred_year=ISPV_YEAR)
    warn_non_target_year(
        source="Eurostat lfsi_emp_a",
        year=emp_rate_year,
        context="Workforce manpower conversion",
    )

    # OSVC vedlejsi are treated as overlap with employees and are excluded
    # from the primary workforce total used in this table.
    workforce_total = n_emp + osvc_main
    manpower_total = workforce_total / (emp_rate_cz / 100.0)

    share_mzs = 100.0 * n_mzs / workforce_total
    share_pls = 100.0 * n_pls / workforce_total
    share_emp = 100.0 * n_emp / workforce_total
    share_osvc_main = 100.0 * osvc_main / workforce_total
    share_osvc_secondary = 100.0 * osvc_secondary / workforce_total
    share_svarc_lo = 100.0 * svarc_lo / workforce_total
    share_svarc_hi = 100.0 * svarc_hi / workforce_total

    rows = [
        {
            "Skupina": r"Zaměstnanci v~mzdové sféře",
            "Počet osob": _format_int(n_mzs),
            "Podíl z~celku [\\si{\\percent}]": _format_pct(share_mzs),
            "Zdroj": r"\acs{ISPV}",
        },
        {
            "Skupina": r"Zaměstnanci v~platové sféře",
            "Počet osob": _format_int(n_pls),
            "Podíl z~celku [\\si{\\percent}]": _format_pct(share_pls),
            "Zdroj": r"\acs{ISPV}",
        },
        {
            "Skupina": r"Zaměstnanci celkem",
            "Počet osob": _format_int(n_emp),
            "Podíl z~celku [\\si{\\percent}]": _format_pct(share_emp),
            "Zdroj": r"\acs{ISPV}",
        },
        {
            "Skupina": r"\acs{OSVČ} hlavní činnost",
            "Počet osob": _format_int(osvc_main),
            "Podíl z~celku [\\si{\\percent}]": _format_pct(share_osvc_main),
            "Zdroj": r"\acs{ČSSZ}",
        },
        {
            "Skupina": r"\acs{OSVČ} vedlejší činnost",
            "Počet osob": _format_int(osvc_secondary),
            "Podíl z~celku [\\si{\\percent}]": _format_pct(share_osvc_secondary),
            "Zdroj": r"\acs{ČSSZ}",
        },
        {
            "Skupina": r"z~toho odhad švarcsystému",
            "Počet osob": _format_range(svarc_lo, svarc_hi),
            "Podíl z~celku [\\si{\\percent}]": f"{share_svarc_lo:.1f}--{share_svarc_hi:.1f}",
            "Zdroj": r"PAQ",
        },
        {
            "Skupina": r"Celkový počet pracovníků\\(zaměstnanci + \acs{OSVČ} hlavní č.)",
            "Počet osob": _format_int(workforce_total),
            "Podíl z~celku [\\si{\\percent}]": "100",
            "Zdroj": r"výpočet",
        },
        {
            "Skupina": rf"Odhad velikosti pracovní síly při zaměstnanosti \SI{{{_format_pct(emp_rate_cz)}}}{{\percent}} (20--64 let)",
            "Počet osob": _format_int(manpower_total),
            "Podíl z~celku [\\si{\\percent}]": "--",
            "Zdroj": r"výpočet",
        },
    ]

    df = pd.DataFrame(rows).set_index("Skupina")

    save_table_tex(
        df,
        "stav_struktura_prac_sily",
        caption=f"Struktura pracovní síly v~\\acloc{{ČR}} ({ISPV_YEAR}). Zdroj dat: \\acs{{ISPV}}, \\acs{{ČSSZ}} a~PAQ Research.",
        label="tab:stav_struktura_prac_sily_cz",
        position="H",
        note=(
            r"OSVČ: statistická ročenka ČSSZ, rok~"
            + cssz_date.strftime("%Y")
            + r". OSVČ vedlejší jsou uvedeny kurzívou jako překryv se zaměstnanci a nejsou zahrnuty do celkové pracovní síly. "
            + r"Řádek švarcsystému je intervalový odhad dle PAQ Research z~podzimu 2025."
        ),
        cite_keys=["mpsv_ispv", "CSSZ_OtevrenaDataOSVC", "PAQ_Svarcsystem", "eurostat_lfsi_emp_a"],
        col_format=r"@{}>{\raggedright\arraybackslash}p{5.8cm}rr>{\raggedright\arraybackslash}p{4.2cm}@{}",
        index_name="Skupina",
        italic_rows=[r"\acs{OSVČ} vedlejší činnost", r"z~toho odhad švarcsystému"],
        midrule_after=[r"Zaměstnanci celkem", r"\acp{OSVČ} vedlejší činnost", r"Celkový počet pracovníků\\(zaměstnanci + \acs{OSVČ} hlavní č.)"],
    )

    print("Done:")
    print(f"  MZS={n_mzs:,}, PLS={n_pls:,}, employees={n_emp:,}")
    print(f"  OSVC main={osvc_main:,}, secondary={osvc_secondary:,}, total={osvc_total:,}")
    print(f"  Workforce total (excluding OSVC secondary)={int(round(workforce_total)):,}")
    print(f"  Manpower estimate at Eurostat employment rate={int(round(manpower_total)):,}")
    print(f"  Employment rate 20--64 (CZ)={emp_rate_cz:.1f}% (year {emp_rate_year})")


if __name__ == "__main__":
    main()
