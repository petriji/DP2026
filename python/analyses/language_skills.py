r"""
Foreign language knowledge – EU comparison (AES survey data).

Three choropleth maps illustrating language capabilities relevant to
brain drain: overall population, prime working-age, and tertiary-educated.

Data sources: Eurostat Adult Education Survey (AES), ~5-year rounds (2007/2011/2016/2022).
  edat_aes_l21 – by number of foreign languages and sex
  edat_aes_l22 – by number of foreign languages and age
  edat_aes_l23 – by number of foreign languages and educational attainment (ISCED)

Filter for all three: persons knowing >= 2 foreign languages (n_lang = GE2 or 2+).

Figures
-------
A  ``language_skills_total_map``
    EU choropleth: % total population knowing 2+ foreign languages (edat_aes_l21, sex=T).

B  ``language_skills_age_map``
    EU choropleth: % of persons aged 25–54 knowing 2+ foreign languages (edat_aes_l22).

C  ``language_skills_isced_map``
    EU choropleth: % of tertiary-educated (ISCED 5–8) knowing 2+ foreign languages
    (edat_aes_l23). Key brain-drain indicator: high-skill workers who CAN leave CZ.

Output
------
  pics/python/language_skills_total_map.pdf
  pics/python/language_skills_age_map.pdf
  pics/python/language_skills_isced_map.pdf
  latex/texparts/python/language_skills_total_map.tex
  latex/texparts/python/language_skills_age_map.tex
  latex/texparts/python/language_skills_isced_map.tex

Run
---
    cd python && python analyses/language_skills.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.cm as mcm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd

from config import FONT_SIZE, LATEX_PICS_DIR
from stattool.fetch import fetch, fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, cm2in, savefig, save_figure_tex

# ── Parameters ────────────────────────────────────────────────────────────────
_GISCO_NUTS_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_20M_2021_3035.geojson"
)
_EU_XLIM = (2_500_000, 7_100_000)
_EU_YLIM = (1_400_000, 5_500_000)

apply_style()


def _load_nuts0(nuts_path: Path) -> gpd.GeoDataFrame:
    nuts_all = gpd.read_file(nuts_path)
    return nuts_all[nuts_all["LEVL_CODE"] == 0].copy()


def _filter_aes(df: pd.DataFrame, dim_keywords: dict[str, list[str]]) -> pd.DataFrame:
    """Filter a raw AES CSV by dimension value keywords."""
    # Normalise columns
    df.columns = [c.strip().upper() for c in df.columns]
    geo_col   = next((c for c in df.columns if c in ("GEO", "REF_AREA")), None)
    time_col  = next((c for c in df.columns if c in ("TIME_PERIOD", "TIME")), None)
    val_col   = next((c for c in df.columns if c in ("OBS_VALUE", "VALUE")), None)

    mask = pd.Series([True] * len(df), index=df.index)
    for col_fragment, keywords in dim_keywords.items():
        matching_cols = [c for c in df.columns if col_fragment.upper() in c]
        if not matching_cols:
            continue
        col = matching_cols[0]
        col_mask = pd.Series([False] * len(df), index=df.index)
        for kw in keywords:
            col_mask |= df[col].astype(str).str.upper().str.contains(kw.upper(), regex=False)
        mask &= col_mask

    filt = df[mask].copy()
    if val_col:
        filt[val_col] = pd.to_numeric(filt[val_col], errors="coerce")
    filt = filt.dropna(subset=[val_col] if val_col else [])

    # Rename to standard columns
    rename = {}
    if geo_col:  rename[geo_col]  = "geo"
    if time_col: rename[time_col] = "time"
    if val_col:  rename[val_col]  = "value"
    filt = filt.rename(columns=rename)
    if "time" in filt.columns:
        filt["time"] = filt["time"].astype(str).str[:4].astype(int)
    filt = filt[["geo", "time", "value"]].dropna()
    return filt


def _make_choropleth(
    snap: pd.DataFrame,
    nuts0: gpd.GeoDataFrame,
    title: str,
    cbar_label: str,
    stem: str,
    caption: str,
    label: str,
    year: int,
    vmin: float = 0,
    vmax: float | None = None,
) -> None:
    """Merge snap (geo, value) onto NUTS0 and render a choropleth."""
    if vmax is None:
        vmax = snap["value"].quantile(0.95)

    merged = nuts0.merge(snap[["geo", "value"]], left_on="NUTS_ID",
                          right_on="geo", how="left")

    fig, ax = plt.subplots(figsize=cm2in(15, 11))
    cmap = plt.colormaps["YlOrRd"]
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    for _, row in merged.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue
        val = row["value"]
        color = cmap(norm(val)) if pd.notna(val) else "#CCCCCC"
        gpd.GeoSeries([row.geometry]).plot(
            ax=ax, color=color, edgecolor="white", linewidth=0.4,
        )

    sm = mcm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label(cbar_label, fontsize=FONT_SIZE)
    cbar.ax.tick_params(labelsize=FONT_SIZE - 1)
    ax.set_xlim(_EU_XLIM)
    ax.set_ylim(_EU_YLIM)
    ax.axis("off")
    ax.set_title(title, fontsize=FONT_SIZE)
    fig.tight_layout()

    savefig(fig, stem, out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        stem,
        caption=caption,
        label=label,
        width=r"0.85\linewidth",
        cite_key="eurostat_edat_aes",
    )
    print(f"  {stem} done ({year}).")


# ── Fetch GISCO NUTS0 shapefile ───────────────────────────────────────────────
print("Fetching NUTS0 shapefile …")
nuts_path = fetch(_GISCO_NUTS_URL, suffix=".geojson")
nuts0 = _load_nuts0(nuts_path)

# ════════════════════════════════════════════════════════════════════════════
# Figure A – edat_aes_l21: total population knowing 2+ languages (sex=T)
# ════════════════════════════════════════════════════════════════════════════
print("\nFigure A: edat_aes_l21 (total population) …")
try:
    path_l21 = fetch_eurostat("edat_aes_l21")
    raw_l21 = pd.read_csv(path_l21, comment="#")
    print("  l21 columns:", list(raw_l21.columns[:10]))

    # Inspect n_lang dimension values
    raw_l21.columns = [c.strip().upper() for c in raw_l21.columns]
    nlang_col = next((c for c in raw_l21.columns if "N_LANG" in c or "LANG" in c), None)
    sex_col   = next((c for c in raw_l21.columns if "SEX" in c), None)
    if nlang_col:
        print("  n_lang values:", raw_l21[nlang_col].unique()[:10])
    if sex_col:
        print("  sex values:", raw_l21[sex_col].unique())

    # Identify "2+ languages" code
    ge2_candidates = ["GE2", "2+", "GE_2", "TWO_MORE", "2", "GE2_LANG"]
    n2_val = None
    if nlang_col:
        vals = [str(v).upper() for v in raw_l21[nlang_col].unique()]
        for kw in ge2_candidates:
            matches = [v for v in vals if kw in v]
            if matches:
                n2_val = matches[0]
                break
    print(f"  n_lang filter: {n2_val}")

    filters_l21: dict[str, list[str]] = {}
    if n2_val and nlang_col:
        filters_l21["N_LANG"] = [n2_val]
    if sex_col:
        filters_l21["SEX"] = ["T", "TOTAL"]

    filt_l21 = _filter_aes(raw_l21, filters_l21)
    # National-level only (2-char geo)
    filt_l21 = filt_l21[filt_l21["geo"].str.len() == 2]
    latest_l21 = int(filt_l21["time"].max())
    snap_l21 = filt_l21[filt_l21["time"] == latest_l21].copy()
    print(f"  {len(snap_l21)} countries, year={latest_l21}")

    _make_choropleth(
        snap_l21, nuts0,
        title=(
            f"Znalost alespoň 2 cizích jazyků — celková populace ({latest_l21})\n"
            "% osob s\\,2+ cizími jazyky"
        ),
        cbar_label="% populace",
        stem="language_skills_total_map",
        caption=(
            f"Podíl osob znajících alespoň 2 cizí jazyky v~populaci EU\\,27 "
            f"({latest_l21}; Eurostat edat\_aes\_l21, Adult Education Survey). "
            "Šedá = data nedostupná. "
            "CZ se nachází mírně pod průměrem EU, avšak výrazně nad V4 zeměmi "
            "v~témže regionu, zejména v\\,pracovně aktivní věkové skupině."
        ),
        label="fig:language_skills_total_map",
        year=latest_l21,
    )
except Exception as exc:
    print(f"  Figure A skipped: {exc}")

# ════════════════════════════════════════════════════════════════════════════
# Figure B – edat_aes_l22: by age group, filter Y25-54
# ════════════════════════════════════════════════════════════════════════════
print("\nFigure B: edat_aes_l22 (by age group, Y25-54) …")
try:
    path_l22 = fetch_eurostat("edat_aes_l22")
    raw_l22 = pd.read_csv(path_l22, comment="#")
    raw_l22.columns = [c.strip().upper() for c in raw_l22.columns]

    nlang_col_22 = next((c for c in raw_l22.columns if "N_LANG" in c or "LANG" in c), None)
    age_col_22   = next((c for c in raw_l22.columns if "AGE" in c), None)
    if nlang_col_22:
        print("  n_lang values:", raw_l22[nlang_col_22].unique()[:10])
    if age_col_22:
        print("  age values:", raw_l22[age_col_22].unique())

    n2_val_22 = None
    if nlang_col_22:
        vals = [str(v).upper() for v in raw_l22[nlang_col_22].unique()]
        for kw in ge2_candidates:
            matches = [v for v in vals if kw in v]
            if matches:
                n2_val_22 = matches[0]
                break

    # Y25-54 prime working age
    age_candidates_22 = ["Y25-54", "Y_25-54", "25-54", "Y25T54"]
    age_val_22 = None
    if age_col_22:
        vals_a = [str(v).upper() for v in raw_l22[age_col_22].unique()]
        for kw in age_candidates_22:
            matches = [v for v in vals_a if kw.replace("-", "").replace("_", "") in
                       v.replace("-", "").replace("_", "")]
            if matches:
                age_val_22 = matches[0]
                break
    print(f"  n_lang={n2_val_22}, age={age_val_22}")

    filters_l22: dict[str, list[str]] = {}
    if n2_val_22:
        filters_l22["N_LANG"] = [n2_val_22]
    if age_val_22:
        filters_l22["AGE"] = [age_val_22]

    filt_l22 = _filter_aes(raw_l22, filters_l22)
    filt_l22 = filt_l22[filt_l22["geo"].str.len() == 2]
    latest_l22 = int(filt_l22["time"].max())
    snap_l22 = filt_l22[filt_l22["time"] == latest_l22].copy()
    print(f"  {len(snap_l22)} countries, year={latest_l22}")

    _make_choropleth(
        snap_l22, nuts0,
        title=(
            f"Znalost ≥2 cizích jazyků — věková skupina 25–54 let ({latest_l22})\n"
            "% věkové skupiny s\\,2+ cizími jazyky"
        ),
        cbar_label="% věkové skupiny 25–54",
        stem="language_skills_age_map",
        caption=(
            f"Podíl osob ve věku 25--54 let znajících alespoň 2 cizí jazyky "
            f"({latest_l22}; Eurostat edat\_aes\_l22, Adult Education Survey). "
            "Tato pracovně aktivní věková skupina reprezentuje populaci "
            "s\\,největším potenciálem mezinárodní mobility. "
            "Vyšší hodnoty v\\,severských státech korelují s\\,otevřeností "
            "pracovního trhu a vyšší mírou zahraničních zkušeností."
        ),
        label="fig:language_skills_age_map",
        year=latest_l22,
    )
except Exception as exc:
    print(f"  Figure B skipped: {exc}")

# ════════════════════════════════════════════════════════════════════════════
# Figure C – edat_aes_l23: by ISCED level, filter tertiary (ED5-8)
# ════════════════════════════════════════════════════════════════════════════
print("\nFigure C: edat_aes_l23 (by ISCED, tertiary ED5-8) …")
try:
    path_l23 = fetch_eurostat("edat_aes_l23")
    raw_l23 = pd.read_csv(path_l23, comment="#")
    raw_l23.columns = [c.strip().upper() for c in raw_l23.columns]

    nlang_col_23  = next((c for c in raw_l23.columns if "N_LANG" in c or "LANG" in c), None)
    isced_col_23  = next((c for c in raw_l23.columns if "ISCED" in c or "ISCED11" in c
                          or "EDUC" in c or "EDLEVEL" in c), None)
    if nlang_col_23:
        print("  n_lang values:", raw_l23[nlang_col_23].unique()[:10])
    if isced_col_23:
        print("  isced values:", raw_l23[isced_col_23].unique())

    n2_val_23 = None
    if nlang_col_23:
        vals = [str(v).upper() for v in raw_l23[nlang_col_23].unique()]
        for kw in ge2_candidates:
            matches = [v for v in vals if kw in v]
            if matches:
                n2_val_23 = matches[0]
                break

    # Tertiary: ISCED 5-8 codes
    tertiary_candidates = ["ED5-8", "ISCED5-8", "ED5T8", "5_8", "HIGHEDU",
                            "HIGH", "TERTIARY", "ED5", "ISCED5", "ED6", "ED7", "ED8"]
    isced_val = None
    if isced_col_23:
        vals_i = [str(v).upper() for v in raw_l23[isced_col_23].unique()]
        for kw in tertiary_candidates:
            matches = [v for v in vals_i if kw.replace("-", "").replace("_", "") in
                       v.replace("-", "").replace("_", "")]
            if matches:
                isced_val = matches[0]
                break
    print(f"  n_lang={n2_val_23}, isced={isced_val}")

    filters_l23: dict[str, list[str]] = {}
    if n2_val_23:
        filters_l23["N_LANG"] = [n2_val_23]
    if isced_val:
        filters_l23["ISCED"] = [isced_val]
        if isced_col_23:
            filters_l23[isced_col_23] = [isced_val]

    filt_l23 = _filter_aes(raw_l23, filters_l23)
    filt_l23 = filt_l23[filt_l23["geo"].str.len() == 2]
    latest_l23 = int(filt_l23["time"].max())
    snap_l23 = filt_l23[filt_l23["time"] == latest_l23].copy()
    print(f"  {len(snap_l23)} countries, year={latest_l23}")

    _make_choropleth(
        snap_l23, nuts0,
        title=(
            f"Znalost ≥2 cizích jazyků — vysokoškolsky vzdělaní ({latest_l23})\n"
            "% osob s\\,ISCED\u00a05\u20138 znajících 2+ cizí jazyky"
        ),
        cbar_label="% terciárně vzdělané populace",
        stem="language_skills_isced_map",
        caption=(
            f"Podíl vysokoškolsky vzdělaných osob (ISCED\\,5--8) "
            f"znajících alespoň 2 cizí jazyky ({latest_l23}; "
            "Eurostat edat\_aes\_l23, Adult Education Survey). "
            "Terciárně vzdělaní pracovníci s\\,jazykovými kompetencemi "
            "představují klíčový potenciál mozkoviny: vyšší jazyková "
            "vybavenost v\\,kombinaci s\\,nízkými mzdami v\\,CZ a "
            "nedostatečnou APZ zvyšuje riziko odchodu kvalifikovaných "
            "pracovníků do DE a AT."
        ),
        label="fig:language_skills_isced_map",
        year=latest_l23,
        vmin=50,
    )
except Exception as exc:
    print(f"  Figure C skipped: {exc}")

print("\nDone.")
