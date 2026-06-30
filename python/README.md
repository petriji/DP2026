# python — thesis figure pipeline

*Jiří Petříček 2026 · Built with Claude Sonnet 4.6, April 2026*

Generates figures and LaTeX snippets for the CTU thesis.
Sources include Eurostat data (SDMX API) and Czech statutory models
(pension, tax wedge, DPH).

Two rendering backends:
- **PDF** (default): outputs a `.pdf` figure + a `texparts/python/<name>.tex` wrapper with `\begin{figure}`
- **PGF** (LaTeX-native): outputs a `.pgf` TeX fragment where figure text is rendered by LaTeX, supporting `\ac{}`, `\SI{}{}`, and `\acs{geo-XX}` directly in annotations. Produces a `texparts/figures/<name>.tex` file (git-tracked, hand-editable) and a one-line `texparts/python/<name>.tex` wrapper.

PGF export now includes companion-asset optimization:
- Companion rasters (typically `<name>-img0.png` colourbars) are deduplicated by content hash.
- Shared payloads are stored once in `python/figures/_shared/`.
- Generated `.pgf` files are rewritten to reference `_shared/img-<hash>.png`.
- Controlled in `python/config.py`:
  - `PGF_OPTIMIZE_ASSETS`
  - `PGF_DEDUP_COMPANION_IMAGES`
  - `PGF_RECOMPRESS_COMPANION_IMAGES` (reserved switch, currently no-op)

All generated outputs (`texparts/python/`, `figures/`) are gitignored and auto-created on first run.
`texparts/figures/` is **git-tracked** — do not delete it.

## PGF space-saving concepts (roadmap)

Implemented:
- Hash-based deduplication of PGF companion PNGs (`_shared/`).

Prepared switches (for next step):
- Companion PNG recompression/transcoding pipeline (`PGF_RECOMPRESS_COMPANION_IMAGES`).

Recommended future concepts:
- Force vector colourbars where possible (avoid rasterized gradient strips).
- Canonicalize colormap/limits/tick styling so colourbar rasters become identical more often.
- Optional post-build PDF object compression check (`qpdf --stream-data=compress`) in CI.

## Setup

```bash
cd python
bash setup_venv.sh        # creates .venv with --copies (NTFS-safe)
```

> **WSL2 + Windows drive (9p/drvfs):** Python `venv` requires symlinks
> (`lib64 → lib`) which are not supported on 9p mounts.  Create the venv
> on a native Linux filesystem instead:
> ```bash
> python3 -m venv /tmp/dp_venv
> /tmp/dp_venv/bin/pip install -r requirements.txt
> ```
> Then use `/tmp/dp_venv/bin/python` to run scripts (or source
> `python/.venv/bin/activate` which redirects there).
> Note: `/tmp/dp_venv` does not survive a WSL restart — recreate as needed.

## Run

```bash
bash run.sh analyses/stav_hdp_vyvoj.py   # single script
bash run.sh stats_analytics.py             # regenerate everything missing
bash run.sh stats_analytics.py --force all # force-regenerate all
bash run.sh stats_analytics.py --list      # show which texparts are referenced
```

## Optional review tooling

Acrobat PDF review ingestion lives under `tools/` and is intentionally separate
from the analytics/build pipeline. It converts reviewer comments and highlights
from dirty-build PDFs into `review/review_register.md` with ranked source
candidates for manual triage.

```bash
pip install -r requirements-review.txt
python tools/pdf_review_to_register.py ../review/*.pdf --repo-root .. --out ../review/review_register.md
```

See `tools/README-review.md` for details and caveats.

## LaTeX integration

Figures are generated automatically before every LaTeX build via two hooks:

- **LaTeX Workshop** (VS Code): use the recipe *`stats_analytics → pdflatex → biber → pdflatex×2`*; `stats_analytics.py` runs as the first tool, then the full bibliography cycle follows.
- **`latexmk`** (CLI): `latexmkrc` runs `stats_analytics.py` as a pre-build step; set `SKIP_PYTHON_ANALYTICS=1` to bypass it.

Both hooks are no-ops when all outputs already exist.

## Layout

```
python/
├── config.py               – paths, figure size, font, colour palette
├── analytics_registry.toml – maps keys → scripts + texpart patterns
├── stats_analytics.py      – orchestrator (called by latexmkrc pre-build)
├── requirements.txt        – pip dependencies
├── stattool/               – data layer
│   ├── fetch.py            – Eurostat SDMX download + cache
│   ├── dataset.py          – Dataset wrapper (pivot, filter, normalise)
│   └── style.py            – Matplotlib style + savefig/save_figure_tex + CZ figure annotation helpers (_fmt_czk, _add_vertical_ref, _add_linestyle_key, _bottom_legend)
├── statout/                – visualisation layer
│   ├── timeline.py         – line chart (single countries + groups)
│   ├── map_europe.py       – choropleth map (EPSG:3035)
│   ├── scatter.py          – scatter plot
│   └── table.py            – LaTeX table from DataFrame
└── analyses/               – one script per figure group
    ├── cz_tax_model.py     – CZ tax/levy: pure calculation module (no matplotlib, no external imports)
    ├── problemy_cz_duchod.py – CZ pension: pure calculation module (imports levy constants from cz_tax_model)
    ├── cz_calculator.py    – Individual pension calculator (VVZ/PK history, earnings history, early/late/children)
    ├── problemy_cz_model.py       – all 7 CZ model figures (imports from the two modules above)
    ├── stav_hdp_vyvoj.py – GDP per capita in PPS (EU timeline)
    ├── eu_danovy_klin.py    – OECD tax wedge choropleth
    ├── stav_arope.py    – At-risk-of-poverty maps + timeline
    ├── prakticka_srovnani.py – Flexicurity indicator table
    ├── stav_hustota_vyvoj.py – Trade union density over time
    ├── eu_apz_vydaje.py  – Labour market policy expenditure
    ├── eu_konvergence.py – Wage–GDP convergence scatter
    ├── korelace_hustota_gini.py – Union density vs Gini scatter
    ├── stav_ipp_mzdy.py  – IPP wage growth analysis
    ├── stav_ipp_doplnkove.py – IPP supplementary figures
    ├── problemy_sektor_mzdy.py – Sector wages, LCI growth, dispersion
    ├── problemy_stratifikace.py – Regional wages, gender gap, percentiles
    ├── vyhled_zavislost.py – Old-age dependency ratio map
    ├── stav_zamestnanost.py – Employment rate timeline
    ├── eu_prijem_pps.py   – Income in PPS choropleth
    ├── eu_gini_prijem.py – Gini coefficient timeline
    ├── problemy_mzda_duchod.py – Wage–pension distribution
    ├── eu_bohatstvi_mapa.py      – Gini wealth coefficient choropleth map
    ├── eu_bohatstvi_vyvoj.py – Gini wealth inequality over time
    ├── eu_bohatstvi_top20.py – Wealth shares (top 20 %) over time
    ├── eu_pokryti_kv_mapa.py      – Collective agreement coverage choropleth
    ├── korelace_analyza.py – KV coverage correlation analyses
    ├── eu_pokryti_prijem.py – KV coverage vs. income scatter
    ├── stav_ipp_rozsah.py       – IPP collective agreement breadth
    ├── eu_odvetvove_mzdy.py – Sector net wages in PPS
    ├── problemy_verejny_soukromy.py – Public vs. private sector wage comparison
    ├── problemy_gpg.py – Wage stratification by gender
    ├── eu_hustota_mapa.py    – Trade union density choropleth map
    ├── eu_apz_mapa.py  – LMP expenditure choropleth map
    ├── eu_cenova_hladina.py              – Price level index choropleth map
    ├── eu_osvc_mapa.py  – Self-employment rate choropleth map
    ├── stav_prijem_pomer.py – Net income ratio timeline
    ├── vyhled_porodnost.py    – Natality (TFR) maps and timeline
    ├── problemy_jazyky.py      – Language skills maps (age, ISCED, total)
    ├── problemy_dojezdeni.py – Cross-border commuting maps and timeline
    └── problemy_emigrace.py        – Czech emigration timeline
```

## Adding a new figure

**PDF backend:**
```
 you                      latexmkrc / LaTeX Workshop
  │                                │
  ├─ write analyses/my_script.py   │
  ├─ add [my_key] to               │
  │    analytics_registry.toml     │
  ├─ \input{texparts/python/…}     │
  │    or \inputpgffigure{…}       │
  │    in commentary / main.tex    │
  │                          build triggered
  │                                │
  │                        stats_analytics.py
  │                           detects missing output
  │                                │
  │                        analyses/my_script.py
  │                           runs → pics/ + texparts/
```

1. Write `analyses/my_script.py` — call `save_figure_tex()` or `save_table_tex()`.
2. Add a `[my_key]` section to `analytics_registry.toml`.
3. Add `\input{texparts/python/my_texpart}` to `main.tex`.
4. Build — the hook detects the missing output and runs your script.

## CZ pension & tax model

Three-file model + one calculator:
- **`cz_tax_model.py`** — pure calculation module (no external dependencies):
  tax/levy constants (`AVG_WAGE`, income tax rates, employee/OSVČ levy rates,
  `EMPLOYER_INS_RATE`, `OSVC_BASE_RATIO`, `OSVC_MIN_MONTHLY_BASE`); paušální
  daň tables (`PAUSALNI_DAN`, `PAUSALNI_DAN_TOTAL`); DPH constants and
  `_revenue_after_dph`.  Provides `tax_wedge_*`, `net_income_*`, `sp_*` functions.
- **`problemy_cz_duchod.py`** — pure calculation module: pension-domain constants
  (RH thresholds, OVZ rates, `INSURANCE_YEARS`, `MIN_TOTAL_PENSION`); imports
  shared levy constants from `cz_tax_model`.  Provides `pension_employee`,
  `pension_osvc_vydajovy`, and the internal `_pension`/`_rovz` helpers.
- **`cz_calculator.py`** — individual pension calculator: year-parameterised
  `get_params(year)` (VVZ/PK table, declining `first_limit_pct` 2026–2035),
  `compute_ovz()` from actual earnings history, `calculate_pension()` (full),
  `calculate_pension_simple()` (constant gross estimate), early/late retirement
  penalties, children bonus.  Zero above RH2 (zákon č. 270/2023 Sb.).
  Run directly for a CLI demo or import for custom analyses.
- **`problemy_cz_model.py`** — single entry point for all 7 figures; imports both
  modules above; defines figure-only constants (reference wages, OSVČ types,
  paušál segments); owns all matplotlib code.  Run directly or via the registry.

All three together model the Czech pension and tax system for a
švarc-systém comparison (employee vs OSVČ).

**X-axis convention:** all figures share the same x-axis = total cost to the
payer (employer or client).  For an employee this is `hrubá mzda × 1.338`; for
OSVČ it is their monthly revenue (what the client pays).

**OSVČ types modelled:**
- 80 % výdajový paušál (řemeslná živnost)
- 60 % (ostatní živnosti)
- 40 % (svobodná povolání)
- Paušální daň (all three pásma)

**DPH (VAT):** OSVČ with annual revenue > 2 000 000 Kč (166 666 Kč/month) must
register as plátce DPH.  Above this threshold the model reduces the OSVČ's
effective revenue by 21 % (the client pays `x`, the OSVČ keeps `x / 1.21`).
This affects all derived quantities (pension OVZ, tax base, net income, SP).
A red vertical reference line marks the DPH threshold on every figure.

**Reference wages:** minimum wage 22 400 Kč gross (NV 405/2025 Sb., from
1 Jan 2026 = 29 972 Kč employer total cost); median wage 43 241 Kč gross
(ISPV 2025 = 57 856 Kč employer total cost).

**Parameters:** 2026 statutory values (zákon č. 155/1995 Sb., zákon č. 270/2023
Sb., NV 365/2025 Sb., zákon č. 235/2004 Sb. o DPH).

**Outputs (registry keys):**

| Key | Script | Figures |
|-----|--------|---------|
| `cz_pension` | `problemy_cz_model.py` | `problemy_duchod_prijem`, `problemy_duchod_solidarita` |
| `cz_tax_model` | `problemy_cz_model.py` | `problemy_duchod_klin`, `problemy_danovy_klin_cz`, `problemy_cisty_prijem_cz`, `problemy_sp_odvody_cz`, `problemy_duchod_sp_pomer` |
