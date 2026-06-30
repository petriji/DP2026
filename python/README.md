# python — thesis figure pipeline

*Jiří Petříček 2026 · Built with Claude Sonnet 4.6, April 2026*

> New to this repository? See [README_SETUP.md](../README_SETUP.md) at the
> repository root for how to install Python and create the virtual environment
> before following the pipeline details below.

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

## Dependencies

Core Python library requirements are specified in `python/requirements.txt`:
- **pandas** (`>=2.0`) — tabular data transformation and modeling
- **geopandas** (`>=0.14`) & **geodatasets** — geospatial maps and choropleths (from Natural Earth data)
- **matplotlib** (`>=3.8`) & **matplotlib-scalebar** — high-quality vector/PGF plotting
- **scipy** — statistical distribution matching and mathematical operations
- **requests** — secure HTTP downloads for Eurostat JSON/SDMX data
- **tqdm** — terminal execution feedback
- **openpyxl** & **xlrd** (`>=2.0.1`) — reading spreadsheet sheets (`.xlsx` and legacy `.xls` formats)

Optional reviewer comment parsing and importing utility dependencies are in `python/requirements-review.txt`:
- **PyMuPDF** (`>=1.24`) — PDF comment/highlight extraction and triage report compilation

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

> **Runtime:** a full `stats_analytics.py` run (from an empty cache) takes
> roughly **10 minutes**, dominated by network downloads from Eurostat/OECD/
> other providers — actual time depends heavily on your connection speed.
> Once source data is cached under `python/data/`, incremental re-runs (only
> regenerating missing outputs) are much faster. `--force all` re-runs every
> script but reuses cached downloads, so it doesn't repeat network time.

### Data quality warnings (target year = 2025)

The analytics runner now performs a post-run data-quality audit focused on year transparency:
- `stats_analytics.py` checks referenced generated outputs and warns when caption years do not include the target year.
- Default target year is `2025` (override with `--target-year` or `DP_TARGET_YEAR`).
- A machine-readable and prose-friendly report is written to:
  - `review/data_quality_report.json`
  - `review/data_quality_report.md`

Analysis scripts can emit standardised warnings via `stattool.data_quality`:
- `warn_fallback(...)` for secondary/hardcoded/expert fallback paths
- `warn_non_target_year(...)` for non-2025 data use

## Optional MCP data server

The repository includes an optional MCP server for agents that need structured
access to the existing data layer.  It is a thin wrapper around `stattool.fetch`
and `stattool.dataset`; the normal thesis build still calls those Python APIs
directly and does not require an MCP server to be running.

Run it from the repository root with the project virtual environment:

```bash
bash python/run.sh -m mcp_servers.dp_data_server
```

Typical VS Code MCP configuration:

```json
{
  "servers": {
    "dp-data": {
      "command": "bash",
      "args": ["${workspaceFolder}/python/run.sh", "-m", "mcp_servers.dp_data_server"]
    }
  }
}
```

Exposed tools are intentionally data-oriented and bounded in size:
- `eurostat_fetch`, `oecd_fetch`, `ilostat_fetch` fetch provider data into
  `python/data` and return coverage metadata.
- `dataset_coverage` and `dataset_preview` inspect cached files without sending
  whole datasets through MCP.
- `data_cache_list`, `analytics_registry_list`, and `data_quality_report` expose
  pipeline context for agents.

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

- **VS Code / LaTeX Workshop:** the **Build + Analytics** recipe (and its
  force/poster variants) runs `stats_analytics.py` first, then the full
  bibliography cycle. See the recipe table in
  [latex/README.md](../latex/README.md#vs-code--latex-workshop-recipes).
- **`latexmk`** (CLI): analytics regeneration is **opt-in** — `latexmkrc` only
  runs `stats_analytics.py` as a pre-build step when `RUN_PYTHON_ANALYTICS=1`
  is set (`RUN_PYTHON_ANALYTICS=1 latexmk -pdf -outdir=build main.tex`);
  otherwise the build uses whatever figures/tables already exist.

When run from the VS Code recipes, analytics output is saved to
`latex/build/stats-analytics.log` (or `stats-analytics-force.log` for the
force-regeneration variant).

When it does run, the hook is a no-op if all outputs already exist.

## A1 Poster figures

Poster figures use smaller font sizes than the thesis equivalents (one step
down) and are saved as `python/figures/*_poster.pgf` so they never overwrite
the thesis PGFs.  The poster variant is controlled by `DP_POSTER_RUN=1`.

### Full poster build recipe

```bash
# 1. Generate poster-optimised PGF figures
cd python
bash run_poster_figures.sh

# 2. Build the poster PDF (biber + two pdflatex passes for bibliography)
cd ../latex
pdflatex -interaction=nonstopmode -cnf-line=extra_mem_bot=15000000 \
         -cnf-line=extra_mem_top=15000000 -output-directory=build poster.tex
biber --input-directory=. --output-directory=build build/poster
pdflatex -interaction=nonstopmode -cnf-line=extra_mem_bot=15000000 \
         -cnf-line=extra_mem_top=15000000 -output-directory=build poster.tex
```

Output: `latex/build/poster.pdf`

### What `run_poster_figures.sh` does

Sets `DP_POSTER_RUN=1` and runs the six analysis scripts that produce poster
figures.  Each script detects the env var and:

- calls `poster_stem("stem")` → returns `"stem_poster"` so `savefig_pgf` writes
  `figures/stem_poster.pgf` without overwriting the thesis `figures/stem.pgf`
- applies poster-specific sizes (via `IS_POSTER_RUN`) inside shared helpers
  (`scatter.py`, `ternary.py`, `map_europe.py`)
- skips `save_figure_tex_pgf()` (thesis `.tex` wrappers are not needed for the poster)

Scripts run: `eu_pokryti_kv_mapa`, `eu_hustota_mapa`, `eu_apz_vydaje`,
`problemy_cz_model`, `korelace_analyza`, `practical_ternary_social_dialog`.

### Poster-specific size constants (`config.py`)

| Constant | Value | Purpose |
|---|---|---|
| `IS_POSTER_RUN` | `DP_POSTER_RUN == "1"` | gate poster-only code paths |
| `POSTER_FIGURE_LABEL_SIZE` | `FIGURE_LABEL_SIZE - 1` | axis/tick labels |
| `POSTER_FIGURE_COMPACT_LABEL_SIZE` | `FIGURE_COMPACT_LABEL_SIZE - 1` | y-labels in scatter 2×2 |
| `poster_stem(s)` | `s + "_poster"` or `s` | output filename selector |

## Layout

```
python/
├── config.py               – paths, figure size, font, colour palette
├── analytics_registry.toml – maps keys → scripts + texpart patterns
├── stats_analytics.py      – orchestrator (called by latexmkrc pre-build)
├── requirements.txt        – pip dependencies
├── mcp_servers/            – optional MCP servers for agent-facing data tools
├── stattool/               – data layer
│   ├── fetch.py            – Eurostat SDMX download + cache
│   ├── dataset.py          – Dataset wrapper (pivot, filter, normalise)
│   └── style.py            – Matplotlib style + savefig/save_figure_tex + CZ figure annotation helpers (_fmt_czk, _add_vertical_ref, _add_linestyle_key, _bottom_legend)
├── statout/                – visualisation layer
│   ├── timeline.py         – line chart (single countries + groups)
│   ├── map_europe.py       – choropleth map (EPSG:3035)
│   ├── scatter.py          – scatter plot
│   └── table.py            – LaTeX table from DataFrame
└── analyses/               – one script per figure group (60+ scripts)
```

> The full, authoritative list of analysis scripts and which figure/table each
> one produces is **[analytics_registry.toml](analytics_registry.toml)** — one
> `[key]` section per script, mapping it to its `texparts`/`pics` output stems.
> Run `bash run.sh stats_analytics.py --list` to print the same mapping from
> the command line. Do not maintain a second copy of this list here; it goes
> stale as scripts are added/renamed (as of writing, `analyses/` has 60+ files
> — always check `analytics_registry.toml` or the directory itself for the
> current set).

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
