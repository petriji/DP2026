# python — thesis figure pipeline

*Jiří Petříček 2026 · Built with Claude Sonnet 4.6, April 2026*

Generates PDF figures and LaTeX snippets for the CTU thesis.
Sources include Eurostat data (SDMX API) and Czech statutory models
(pension, tax wedge, DPH).
All outputs land in `pics/python/` (PDF figures) and `latex/texparts/python/` (.tex
environments) — both gitignored, both auto-created on first run.

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
bash run.sh analyses/gdp_ppp_timeline.py   # single script
bash run.sh stats_analytics.py             # regenerate everything missing
bash run.sh stats_analytics.py --force all # force-regenerate all
bash run.sh stats_analytics.py --list      # show which texparts are referenced
```

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
    ├── cz_pension_model.py – CZ pension: pure calculation module (imports levy constants from cz_tax_model)
    ├── cz_calculator.py    – Individual pension calculator (VVZ/PK history, earnings history, early/late/children)
    ├── cz_figures.py       – all 7 CZ model figures (imports from the two modules above)
    ├── gdp_ppp_timeline.py – GDP per capita in PPS (EU timeline)
    ├── tax_wedge_map.py    – OECD tax wedge choropleth
    ├── arope_example.py    – At-risk-of-poverty maps + timeline
    ├── flexicurity_table.py – Flexicurity indicator table
    ├── union_density_trend.py – Trade union density over time
    ├── lmp_expenditure.py  – Labour market policy expenditure
    ├── wage_gdp_convergence.py – Wage–GDP convergence scatter
    ├── union_gini_scatter.py – Union density vs Gini scatter
    ├── ipp_wage_growth.py  – IPP wage growth analysis
    ├── ipp_supplementary.py – IPP supplementary figures
    ├── rscp_sector_wages.py – Sector wages, LCI growth, dispersion
    ├── rscp_stratification.py – Regional wages, gender gap, percentiles
    ├── old_age_dependency_map.py – Old-age dependency ratio map
    ├── employment_rate_timeline.py – Employment rate timeline
    ├── income_pps_map.py   – Income in PPS choropleth
    ├── gini_income_timeline.py – Gini coefficient timeline
    ├── wage_pension_distribution.py – Wage–pension distribution
    ├── gini_wealth_map.py      – Gini wealth coefficient choropleth map
    ├── gini_wealth_timeline.py – Gini wealth inequality over time
    ├── wealth_top20_timeline.py – Wealth shares (top 20 %) over time
    ├── kv_coverage_map.py      – Collective agreement coverage choropleth
    ├── correlation_analyses.py – KV coverage correlation analyses
    ├── coverage_income_scatter.py – KV coverage vs. income scatter
    ├── ipp_ca_breadth.py       – IPP collective agreement breadth
    ├── sector_wages_net_pps.py – Sector net wages in PPS
    ├── public_private_wages.py – Public vs. private sector wage comparison
    ├── gender_wage_stratification.py – Wage stratification by gender
    ├── union_density_map.py    – Trade union density choropleth map
    ├── lmp_expenditure_map.py  – LMP expenditure choropleth map
    ├── pli_map.py              – Price level index choropleth map
    ├── self_employment_map.py  – Self-employment rate choropleth map
    ├── net_income_ratio_timeline.py – Net income ratio timeline
    ├── natality_timeline.py    – Natality (TFR) maps and timeline
    ├── language_skills.py      – Language skills maps (age, ISCED, total)
    ├── cross_border_commuting.py – Cross-border commuting maps and timeline
    └── emigration_cz.py        – Czech emigration timeline
```

## Adding a new figure

```
 you                      latexmkrc / LaTeX Workshop
  │                                │
  ├─ write analyses/my_script.py   │
  ├─ add [my_key] to               │
  │    analytics_registry.toml     │
  ├─ \input{texparts/python/…}     │
  │    in main.tex                 │
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
- **`cz_pension_model.py`** — pure calculation module: pension-domain constants
  (RH thresholds, OVZ rates, `INSURANCE_YEARS`, `MIN_TOTAL_PENSION`); imports
  shared levy constants from `cz_tax_model`.  Provides `pension_employee`,
  `pension_osvc_vydajovy`, and the internal `_pension`/`_rovz` helpers.
- **`cz_calculator.py`** — individual pension calculator: year-parameterised
  `get_params(year)` (VVZ/PK table, declining `first_limit_pct` 2026–2035),
  `compute_ovz()` from actual earnings history, `calculate_pension()` (full),
  `calculate_pension_simple()` (constant gross estimate), early/late retirement
  penalties, children bonus.  Zero above RH2 (zákon č. 270/2023 Sb.).
  Run directly for a CLI demo or import for custom analyses.
- **`cz_figures.py`** — single entry point for all 7 figures; imports both
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
| `cz_pension` | `cz_figures.py` | `cz_pension_income`, `cz_pension_solidarity` |
| `cz_tax_model` | `cz_figures.py` | `cz_pension_wedge`, `cz_tax_wedge_vs_income`, `cz_net_income_vs_income`, `cz_sp_vs_income`, `cz_pension_sp_ratio` |
