#!/usr/bin/env python3
"""
Rename analysis scripts and generated files to section-prefixed names.

Maps every Python analysis script, its output stems (figures/texparts),
and all downstream files (PDF, commentary .tex, python .tex) to new
names prefixed by the thesis section where they appear.

Section prefixes:
  prakticka_   — \part{Praktická část} (between parts, before ch:vyzkum)
  stav_        — \chapter{Stav SD v ČR} (ch:stav) root
  problemy_    — \section{Problémy trhu práce} (sec:problemy)
  vyhled_      — \section{Výhledové faktory} (sec:vyhled)
  eu_          — \section{Evropský kontext} (sec:evropsky_kontext)
  korelace_    — \subsection{Korelační analýza} (ssec:korelace)

Usage:
  python rename_to_sections.py --dry-run   # preview changes
  python rename_to_sections.py             # execute all renames
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

BASE = Path("/home/jipet/DP")
ANALYSES_DIR = BASE / "python" / "analyses"
COMMENTARY_DIR = BASE / "latex" / "texparts" / "commentary"
PYTHON_TEX_DIR = BASE / "latex" / "texparts" / "python"
PICS_DIR = BASE / "pics" / "python"
MAIN_TEX = BASE / "latex" / "main.tex"
REGISTRY = BASE / "python" / "analytics_registry.toml"
README = BASE / "python" / "README.md"

# ──────────────────────────────────────────────────────────────────────────────
# Output stem mapping: old_stem → new_stem
# ──────────────────────────────────────────────────────────────────────────────
STEM_MAP: dict[str, str] = {
    # ── Part: Praktická část ──
    "flexicurity_table":              "prakticka_srovnani",

    # ── Chapter: Stav SD v ČR (ch:stav) ──
    "gdp_ppp_timeline":              "stav_hdp_vyvoj",
    "net_income_ratio_timeline":     "stav_prijem_pomer",
    "employment_rate_timeline":      "stav_zamestnanost",
    "union_density_trend":           "stav_hustota_vyvoj",
    "union_density_trend_2004":      "stav_hustota_vyvoj_2004",
    "ipp_wage_growth":               "stav_ipp_mzdy",
    "ipp_neg_vs_inflation":          "stav_ipp_inflace",
    "ipp_cumulative_real":           "stav_ipp_kumulativ",
    "ipp_actual_vs_neg_gap":         "stav_ipp_mezera",
    "ipp_ca_breadth":                "stav_ipp_rozsah",
    # arope: dynamic year suffix — handled by PARTIAL_STEMS below
    "arope_timeline_CE":             "stav_arope_vyvoj",
    "arope_groups":                  "stav_arope_skupiny",

    # ── Section: Problémy trhu práce (sec:problemy) ──
    "wage_pension_distribution":     "problemy_mzda_duchod",
    "cz_pension_income":             "problemy_duchod_prijem",
    "cz_pension_solidarity":         "problemy_duchod_solidarita",
    "cz_pension_wedge":              "problemy_duchod_klin",
    "cz_pension_sp_ratio":           "problemy_duchod_sp_pomer",
    "cz_tax_wedge_vs_income":        "problemy_danovy_klin_cz",
    "cz_net_income_vs_income":       "problemy_cisty_prijem_cz",
    "cz_sp_vs_income":               "problemy_sp_odvody_cz",
    "rscp_regional_wages_map":       "problemy_regiony_mapa",
    "rscp_regional_wages":           "problemy_regiony",
    "cross_border_commuting_timeline": "problemy_dojezdeni_vyvoj",
    "cross_border_commuting_map":    "problemy_dojezdeni_mapa",
    "cross_border_commuting_nuts2":  "problemy_dojezdeni_nuts2",
    "gender_pay_gap_map":            "problemy_gpg_mapa",
    "gender_wage_stratification":    "problemy_gpg_stratifikace",
    "rscp_gender_gap":               "problemy_gpg_sektor",
    "rscp_public_private_sector":    "problemy_verejny_soukromy",
    "rscp_public_private_distribution": "problemy_verejny_soukromy_dist",
    "rscp_sector_percentiles":       "problemy_sektor_percentily",
    "rscp_sector_dispersion":        "problemy_sektor_disperze",
    "rscp_sector_lci_growth":        "problemy_sektor_lci",
    "rscp_sector_wages_cz":          "problemy_sektor_mzdy_cz",
    "language_skills_total_map":     "problemy_jazyky_celkem",
    "language_skills_age_map":       "problemy_jazyky_vek",
    "language_skills_isced_map":     "problemy_jazyky_isced",
    "emigration_cz_timeline":        "problemy_emigrace_vyvoj",

    # ── Section: Výhledové faktory (sec:vyhled) ──
    "old_age_dependency_map":        "vyhled_zavislost_mapa",
    "natality_tfr_timeline":         "vyhled_porodnost_vyvoj",
    "natality_tfr_map":              "vyhled_porodnost_mapa",

    # ── Section: Evropský kontext (sec:evropsky_kontext) ──
    "pli_map":                       "eu_cenova_hladina",
    "tax_wedge_map":                 "eu_danovy_klin",
    "wage_gdp_convergence":          "eu_konvergence",
    "kv_coverage_map":               "eu_pokryti_kv_mapa",
    "cb_coverage_timeline":          "eu_pokryti_kv_vyvoj",
    "cb_coverage_timeline_2004":     "eu_pokryti_kv_vyvoj_2004",
    "union_density_map":             "eu_hustota_mapa",
    "income_pps_map":                "eu_prijem_pps",
    "gini_income_timeline":          "eu_gini_prijem",
    "wealth_top10_map":              "eu_bohatstvi_mapa",
    "wealth_top10_timeline":         "eu_bohatstvi_vyvoj",
    "wealth_top20_timeline":         "eu_bohatstvi_top20",
    "sector_wages_bar":              "eu_odvetvove_mzdy_bar",
    "sector_wages_deviation":        "eu_odvetvove_mzdy_odchylka",
    "sector_wages_map_combined":     "eu_odvetvove_mzdy_mapa",
    "sector_wages_map_C":            "eu_odvetvove_mzdy_mapa_C",
    "sector_wages_map_G":            "eu_odvetvove_mzdy_mapa_G",
    "sector_wages_map_J":            "eu_odvetvove_mzdy_mapa_J",
    "sector_wages_map_K":            "eu_odvetvove_mzdy_mapa_K",
    "lmp_expenditure":               "eu_apz_vydaje",
    "lmp_expenditure_2004":          "eu_apz_vydaje_2004",
    "lmp_expenditure_map":           "eu_apz_mapa",
    "self_employment_map":           "eu_osvc_mapa",
    "coverage_income_scatter":       "eu_pokryti_prijem",

    # ── Subsection: Korelační analýza (ssec:korelace) ──
    "scatter_combined":              "korelace_scatter",
    "coverage_correlation_table":    "korelace_tabulka",
    "union_gini_scatter":            "korelace_hustota_gini",

    # ── Unplaced (assigned to likely section) ──
    "strike_activity":               "stav_stavky",
}

# Partial-stem replacements for f-string patterns (applied in Python files only)
PARTIAL_STEMS: dict[str, str] = {
    "arope_map_": "stav_arope_mapa_",      # f"arope_map_{ds.latest_year}"
    "language_skills_":  "problemy_jazyky_",  # might appear as prefix in code
}

# ──────────────────────────────────────────────────────────────────────────────
# Script file mapping: old_filename → new_filename (in analyses/)
# ──────────────────────────────────────────────────────────────────────────────
SCRIPT_MAP: dict[str, str] = {
    "flexicurity_table.py":          "prakticka_srovnani.py",
    "gdp_ppp_timeline.py":          "stav_hdp_vyvoj.py",
    "net_income_ratio_timeline.py": "stav_prijem_pomer.py",
    "employment_rate_timeline.py":  "stav_zamestnanost.py",
    "union_density_trend.py":       "stav_hustota_vyvoj.py",
    "ipp_wage_growth.py":           "stav_ipp_mzdy.py",
    "ipp_supplementary.py":         "stav_ipp_doplnkove.py",
    "ipp_ca_breadth.py":            "stav_ipp_rozsah.py",
    "arope_example.py":             "stav_arope.py",
    "wage_pension_distribution.py": "problemy_mzda_duchod.py",
    "cz_figures.py":                "problemy_cz_model.py",
    "cz_pension_model.py":          "problemy_cz_duchod.py",
    "rscp_stratification.py":       "problemy_stratifikace.py",
    "cross_border_commuting.py":    "problemy_dojezdeni.py",
    "gender_wage_stratification.py": "problemy_gpg.py",
    "public_private_wages.py":      "problemy_verejny_soukromy.py",
    "rscp_sector_wages.py":         "problemy_sektor_mzdy.py",
    "language_skills.py":           "problemy_jazyky.py",
    "emigration_cz.py":             "problemy_emigrace.py",
    "old_age_dependency_map.py":    "vyhled_zavislost.py",
    "natality_timeline.py":         "vyhled_porodnost.py",
    "pli_map.py":                   "eu_cenova_hladina.py",
    "tax_wedge_map.py":             "eu_danovy_klin.py",
    "wage_gdp_convergence.py":      "eu_konvergence.py",
    "kv_coverage_map.py":           "eu_pokryti_kv_mapa.py",
    "cb_coverage_timeline.py":      "eu_pokryti_kv_vyvoj.py",
    "union_density_map.py":         "eu_hustota_mapa.py",
    "income_pps_map.py":            "eu_prijem_pps.py",
    "gini_income_timeline.py":      "eu_gini_prijem.py",
    "gini_wealth_map.py":           "eu_bohatstvi_mapa.py",
    "gini_wealth_timeline.py":      "eu_bohatstvi_vyvoj.py",
    "wealth_top20_timeline.py":     "eu_bohatstvi_top20.py",
    "sector_wages_net_pps.py":      "eu_odvetvove_mzdy.py",
    "lmp_expenditure.py":           "eu_apz_vydaje.py",
    "lmp_expenditure_map.py":       "eu_apz_mapa.py",
    "self_employment_map.py":       "eu_osvc_mapa.py",
    "coverage_income_scatter.py":   "eu_pokryti_prijem.py",
    "correlation_analyses.py":      "korelace_analyza.py",
    "union_gini_scatter.py":        "korelace_hustota_gini.py",
    "strike_activity.py":           "stav_stavky.py",
}

# Scripts NOT renamed (helper modules, no section assignment):
#   _shared_data.py, cz_tax_model.py, cz_calculator.py


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _replace_stems_in_text(text: str, *, include_partial: bool = False) -> str:
    """Replace all old stems with new stems in text (longest-first to avoid substring issues)."""
    for old, new in sorted(STEM_MAP.items(), key=lambda x: -len(x[0])):
        text = text.replace(f'"{old}"', f'"{new}"')
        text = text.replace(f"'{old}'", f"'{new}'")
        # Also handle unquoted path contexts in .tex files
        text = text.replace(f"/{old}", f"/{new}")
        text = text.replace(f"{{{old}}}", f"{{{new}}}")
        # Label references
        text = text.replace(f"fig:{old}", f"fig:{new}")
        text = text.replace(f"tab:{old}", f"tab:{new}")
    if include_partial:
        for old_prefix, new_prefix in PARTIAL_STEMS.items():
            text = text.replace(f'"{old_prefix}', f'"{new_prefix}')
            text = text.replace(f"'{old_prefix}", f"'{new_prefix}")
    return text


def _replace_script_imports(text: str) -> str:
    """Update cross-imports between renamed analysis scripts."""
    for old_file, new_file in SCRIPT_MAP.items():
        old_mod = old_file.replace(".py", "")
        new_mod = new_file.replace(".py", "")
        text = text.replace(f"analyses.{old_mod}", f"analyses.{new_mod}")
    return text


# ──────────────────────────────────────────────────────────────────────────────
# Main rename logic
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Rename analysis files to section-prefixed names")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    args = parser.parse_args()
    dry = args.dry_run

    moved_scripts: list[tuple[str, str]] = []
    moved_tex: list[tuple[str, str]] = []
    moved_pdf: list[tuple[str, str]] = []
    errors: list[str] = []

    # ── 1. Rename Python scripts ──────────────────────────────────────────
    print("═══ Phase 1: Rename Python scripts ═══")
    for old_name, new_name in sorted(SCRIPT_MAP.items()):
        old_path = ANALYSES_DIR / old_name
        new_path = ANALYSES_DIR / new_name
        if not old_path.exists():
            errors.append(f"MISSING script: {old_path}")
            continue
        if old_path == new_path:
            continue

        content = old_path.read_text(encoding="utf-8")
        content = _replace_stems_in_text(content, include_partial=True)
        content = _replace_script_imports(content)

        print(f"  {old_name:40s} → {new_name}")
        if not dry:
            new_path.write_text(content, encoding="utf-8")
            old_path.unlink()
        moved_scripts.append((old_name, new_name))

    # Also update _shared_data.py imports (though it currently has no stem references)
    shared = ANALYSES_DIR / "_shared_data.py"
    if shared.exists():
        text = shared.read_text(encoding="utf-8")
        updated = _replace_script_imports(text)
        if updated != text and not dry:
            shared.write_text(updated, encoding="utf-8")

    # ── 2. Rename commentary .tex files ───────────────────────────────────
    print("\n═══ Phase 2: Rename commentary .tex files ═══")
    for old_stem, new_stem in sorted(STEM_MAP.items()):
        old_tex = COMMENTARY_DIR / f"{old_stem}.tex"
        new_tex = COMMENTARY_DIR / f"{new_stem}.tex"
        if not old_tex.exists():
            continue
        if old_tex == new_tex:
            continue

        content = old_tex.read_text(encoding="utf-8")
        content = _replace_stems_in_text(content)

        print(f"  {old_stem + '.tex':50s} → {new_stem}.tex")
        if not dry:
            new_tex.write_text(content, encoding="utf-8")
            old_tex.unlink()
        moved_tex.append((f"commentary/{old_stem}.tex", f"commentary/{new_stem}.tex"))

    # Also handle arope_map_YYYY.tex (dynamic year stem)
    for f in sorted(COMMENTARY_DIR.glob("arope_map_*.tex")):
        year_part = f.stem.replace("arope_map_", "")
        new_stem = f"stav_arope_mapa_{year_part}"
        new_tex = COMMENTARY_DIR / f"{new_stem}.tex"
        content = f.read_text(encoding="utf-8")
        content = content.replace("arope_map_", "stav_arope_mapa_")
        content = _replace_stems_in_text(content)
        print(f"  {f.name:50s} → {new_stem}.tex")
        if not dry:
            new_tex.write_text(content, encoding="utf-8")
            f.unlink()
        moved_tex.append((f"commentary/{f.name}", f"commentary/{new_stem}.tex"))

    # ── 3. Rename python texpart .tex files ───────────────────────────────
    print("\n═══ Phase 3: Rename python texpart .tex files ═══")
    for old_stem, new_stem in sorted(STEM_MAP.items()):
        old_tex = PYTHON_TEX_DIR / f"{old_stem}.tex"
        new_tex = PYTHON_TEX_DIR / f"{new_stem}.tex"
        if not old_tex.exists():
            continue
        if old_tex == new_tex:
            continue

        content = old_tex.read_text(encoding="utf-8")
        content = _replace_stems_in_text(content)

        print(f"  {old_stem + '.tex':50s} → {new_stem}.tex")
        if not dry:
            new_tex.write_text(content, encoding="utf-8")
            old_tex.unlink()
        moved_tex.append((f"python/{old_stem}.tex", f"python/{new_stem}.tex"))

    # Handle arope_map_YYYY.tex in python texparts too
    for f in sorted(PYTHON_TEX_DIR.glob("arope_map_*.tex")):
        year_part = f.stem.replace("arope_map_", "")
        new_stem = f"stav_arope_mapa_{year_part}"
        new_tex = PYTHON_TEX_DIR / f"{new_stem}.tex"
        content = f.read_text(encoding="utf-8")
        content = content.replace("arope_map_", "stav_arope_mapa_")
        content = _replace_stems_in_text(content)
        print(f"  {f.name:50s} → {new_stem}.tex")
        if not dry:
            new_tex.write_text(content, encoding="utf-8")
            f.unlink()

    # ── 4. Rename PDF files ───────────────────────────────────────────────
    print("\n═══ Phase 4: Rename PDF figures ═══")
    for old_stem, new_stem in sorted(STEM_MAP.items()):
        old_pdf = PICS_DIR / f"{old_stem}.pdf"
        new_pdf = PICS_DIR / f"{new_stem}.pdf"
        if not old_pdf.exists():
            continue
        if old_pdf == new_pdf:
            continue
        print(f"  {old_stem + '.pdf':50s} → {new_stem}.pdf")
        if not dry:
            shutil.move(str(old_pdf), str(new_pdf))
        moved_pdf.append((old_stem, new_stem))

    # Handle arope_map_YYYY.pdf
    for f in sorted(PICS_DIR.glob("arope_map_*.pdf")):
        year_part = f.stem.replace("arope_map_", "")
        new_stem = f"stav_arope_mapa_{year_part}"
        new_pdf = PICS_DIR / f"{new_stem}.pdf"
        print(f"  {f.name:50s} → {new_stem}.pdf")
        if not dry:
            shutil.move(str(f), str(new_pdf))

    # ── 5. Update main.tex ────────────────────────────────────────────────
    print("\n═══ Phase 5: Update main.tex ═══")
    content = MAIN_TEX.read_text(encoding="utf-8")
    content = _replace_stems_in_text(content)
    # Handle arope dynamic stem in main.tex
    content = content.replace("arope_map_", "stav_arope_mapa_")
    if not dry:
        MAIN_TEX.write_text(content, encoding="utf-8")
    print("  main.tex updated")

    # ── 6. Update analytics_registry.toml ─────────────────────────────────
    print("\n═══ Phase 6: Update analytics_registry.toml ═══")
    content = REGISTRY.read_text(encoding="utf-8")
    # Replace script paths
    for old_script, new_script in SCRIPT_MAP.items():
        content = content.replace(f'"analyses/{old_script}"', f'"analyses/{new_script}"')
    # Replace stem references (longest first)
    for old_stem, new_stem in sorted(STEM_MAP.items(), key=lambda x: -len(x[0])):
        content = content.replace(f'"{old_stem}"', f'"{new_stem}"')
    # Handle arope wildcard pattern
    content = content.replace('"arope_map_*"', '"stav_arope_mapa_*"')
    if not dry:
        REGISTRY.write_text(content, encoding="utf-8")
    print("  analytics_registry.toml updated")

    # ── 7. Cross-reference scan ───────────────────────────────────────────
    # Update any \ref{fig:OLD} or \ref{tab:OLD} in ALL commentary tex files
    print("\n═══ Phase 7: Update cross-references in all tex files ═══")
    tex_dirs = [COMMENTARY_DIR, PYTHON_TEX_DIR, BASE / "latex" / "texparts"]
    count = 0
    for d in tex_dirs:
        if not d.exists():
            continue
        for tex_file in sorted(d.glob("**/*.tex")):
            if tex_file.name == "main.tex":
                continue
            text = tex_file.read_text(encoding="utf-8")
            updated = text
            for old_stem, new_stem in sorted(STEM_MAP.items(), key=lambda x: -len(x[0])):
                updated = updated.replace(f"fig:{old_stem}", f"fig:{new_stem}")
                updated = updated.replace(f"tab:{old_stem}", f"tab:{new_stem}")
            if updated != text:
                count += 1
                if not dry:
                    tex_file.write_text(updated, encoding="utf-8")
    print(f"  Updated cross-refs in {count} .tex files")

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'DRY RUN — ' if dry else ''}Summary:")
    print(f"  Scripts renamed: {len(moved_scripts)}")
    print(f"  TeX files renamed: {len(moved_tex)}")
    print(f"  PDF files renamed: {len(moved_pdf)}")
    if errors:
        print(f"\n  ERRORS ({len(errors)}):")
        for e in errors:
            print(f"    {e}")

    # Print unplaced files (not in main.tex)
    print("\n  Unplaced (not in main.tex, renamed but not added):")
    unplaced = [
        "eu_pokryti_kv_vyvoj", "eu_pokryti_kv_vyvoj_2004",
        "eu_bohatstvi_vyvoj", "eu_bohatstvi_top20",
        "eu_pokryti_prijem", "korelace_hustota_gini",
        "stav_stavky", "eu_odvetvove_mzdy_odchylka",
        "problemy_regiony", "problemy_duchod_prijem",
        "problemy_duchod_klin", "problemy_sektor_mzdy_cz",
        "stav_hustota_vyvoj",  # (only _2004 variant in main)
        "eu_apz_vydaje",       # (only _2004 variant in main)
    ]
    for stem in unplaced:
        print(f"    {stem}")


if __name__ == "__main__":
    main()
