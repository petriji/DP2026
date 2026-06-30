# Project Conventions — DP Sociální dialog

## Python analyses (`python/analyses/*.py`)
- All HTTP downloads via `stattool.fetch.fetch_eurostat()` / `fetch_oecd()` — never raw `requests`
- Output paths from `config`: `LATEX_PICS_DIR`, `LATEX_TEXPARTS_DIR`, `DATA_DIR`
- Call `stattool.style.apply_style()` before any matplotlib call
- `COUNTRIES = ["CZ", ...]` — CZ always first
- Bib keys: `eurostat_<dataset>`, `oecd_<dataset>`, `etui_cba`, `etui_density`, `mpsv_ipp_<year>`, `ispv_<year>`
- Use `stattool.data_quality.warn_fallback()` for any fallback path (secondary source, hardcoded, expert value)
- Use `stattool.data_quality.warn_non_target_year()` when selected data year differs from `DP_TARGET_YEAR` (default 2025)

## Generated LaTeX (`latex/texparts/python/*.tex`)
- `--` in data cells = missing data → re-download with `force=True`
- Captions must contain data year ≥ 2023
- Captions follow brief format: `<Co>, <teritoriální rozsah>, <rok(y)>. Zdroj dat: <Název>~\cite{key}.` — the data-source `\cite{}` belongs in the caption (one cite per source; chain `\cite{k1}\cite{k2}` if same source has multiple datasets)
- Source labels: Eurostat → `Eurostat`; OECD ICTWSS → `\acs{OECD}~\acs{ICTWSS}`; OECD HFCS/LMP → `\acs{OECD}~\acs{HFCS}` / `\acs{OECD}~\acs{LMP}`; MPSV ISPV → `\acs{MPSV}~\acs{ISPV}`; MPSV IPP → `\acs{MPSV}~\acs{IPP}`; Czech laws (model-based analyses) → `Model podle legislativy \aca{geo-CZ}`
- Captions stay brief (no methodology, no footnotes); methodology and trend discussion go into the commentary file

## Commentary files (`latex/texparts/commentary/*.tex`)
- Must end with `\input{texparts/python/<stem>}`
- Discuss **how the data were handled** (definition, scope, methodological notes, comparability caveats) and **trends observed** in the figure (what the chart shows, position of CZ vs. peers, direction of change) — these support claims made elsewhere in the thesis text
- Do NOT re-cite the data source — it is already in the caption; cite only OTHER sources used in the prose (e.g. literature, supporting datasets, laws not shown in the figure)
- Use `\SI{N}{\percent}` in prose, `N\,\%` in tables/math
- Custom SI units (defined in `acro_variables.tex`): `\eur` (€), `\czk` (Kč), `\pps` (PPS), `\week` (týd.), `\month` (měs.), `\person` (os.), `\rok` (rok) — use `\SI{N}{\eur}` etc., never bare `€` or `EUR` next to numbers
- **Never use `\year` as a siunitx unit** — it is a TeX primitive (integer register) and causes build errors; use `\rok` instead: `\SI{2024}{\rok}`
- Compound units via siunitx `\per`: `\SI{12{,}5}{\pps\per\hour}` → `PPS/h`; `\SI{18}{\eur\per\hour}` → `€/h` (slash notation is on globally via `per-mode=symbol`)
- Use `\ac{KEY}` in prose, `\acs{KEY}` in math/equations
- Czech declension: `\acgen{KEY}` (gen), `\acdat{KEY}` (dat), `\acacc{KEY}` (acc), `\acloc{KEY}` (loc), `\acins{KEY}` (ins); long-only: `\aclgen{KEY}` etc. Declared for: EU, HDP, TFR, KV, KS, KSVS, APZ, MPSV, expand if needed
- Force-first declension (re-introduces full form at start of block): `\acfacc{KEY}` (acc), `\acfgen{KEY}` (gen), `\acfdat{KEY}` (dat), `\acfloc{KEY}` (loc), `\acfins{KEY}` (ins); nominative: built-in `\acf{KEY}`. Legacy suffix forms (`\acaccf{KEY}` etc.) are kept as compatibility aliases. Use when an acronym repeats in a paragraph and needs re-introducing after a section break.
- Country codes — STRICT split:
  - `\acs{geo-XX}` (e.g. `\acs{geo-CZ}` = `CZ`) — **ONLY in figure/table content** (axis labels, legends, table cells, captions). Never in prose.
  - In prose, refer to Czech Republic as `\ac{ČR}` (separate acronym, `long=Česká republika`); declension `\acgen{ČR}` = `České republiky`, etc.
  - For other countries **in prose, use the long-only declined form**: `\aclgen{AT}` = `Rakouska`, `\aclgen{DE}` = `Německa`, `\aclgen{DK}` = `Dánska`, `\aclgen{PL}` = `Polska`, `\aclgen{SK}` = `Slovenska` (no parenthetical SHORT). Other cases analogously: `\aclacc{AT}`, `\aclloc{DK}`, etc.
  - Never use `\acgen{AT}` / `\ac{AT}` etc. in prose — these expand to `Rakouska (AT)` on first use and bare `AT` subsequently, which is a short-form country code in prose (forbidden).
  - For countries without declared declension forms (rare), write the plain Czech name directly (`Francie`, `Itálie`, `Belgie`).
  - All EU-27 `geo-XX` declared with `tag=geo`, hidden from printed acronym lists. `ČR` also tagged `geo` (well-known, not listed).
- Acro tags: `zkr` (abbreviations), `vel` (variables), `idx` (indices), `geo` (country codes), `nolist` (suppressed) — `zkr`/`vel`/`idx` printed in their own lists; `geo`/`nolist` hidden
- **Default acro usage policy** (apply everywhere unless noted):
  - **Prose default**: use declension/plural/case-sensitive commands (`\ac{}`, `\acgen{}`, `\acacc{}`, `\acp{}`, etc.) — never hand-type long forms
  - **Suppressed (`nolist`) entries in prose**: use `\acl{KEY}` or `\acf{KEY}` at first mention per chapter; `\ac{KEY}` on subsequent uses (still tracks usage)
  - **First-look prose** (abstract, poster, introduction, conclusion): prefer `\acl{KEY}` / `\acf{KEY}` so readers unfamiliar with the acronym see the expansion
  - **Figures and tables**: use `\acs{KEY}` for abbreviated labels; `\acs{geo-XX}` for ISO country codes
  - **Math mode**: use `\acs{KEY}` (short form); never `\ac{}` inside `$...$` or `equation`
  - **Chapter reset**: `\acresetall` fires at each `\chapter{}` — first use in a new chapter triggers full "long (SHORT)" expansion again; use force-first variants (`\acfacc{KEY}` etc.) when explicitly re-introducing after a section break mid-chapter
- Variable entries: `\acs{var-w}`. Index entries: `\acs{idx-z}` renders just `z` inline; the placeholder form `\square_z` is shown only in the indices list (driven by the `index` property). Indices are always paired with a variable both in math and prose: `\acs{var-N}_{\acs{idx-z},\acs{idx-M}}` → `N_{z,M}`. Accent indices use helper macros `\acidxbar{X}`, `\acidxtilde{X}`, `\acidxhat{X}` (auto-`\acuse`).
- Czech quotes: `CTUthesis.cls` activates `\MakeOuterQuote{"}` — bare ASCII `"word"` is the **preferred** form (auto-translates to `„word"` in PDF). Also correct: `\enquote{word}`. Never use Unicode `„` (U+201E) as opening without a matching `"` (U+201D) closing — that causes `Unbalanced groups` errors.

## Tables (`statout/table.py`)
- Sub-rows/derived rows in `italic_rows=`; derived rows must NOT have `\cite{}`
- `midrule_after=` for logical groups; `col_format="Xrrrrrr"` for 6-country tables

## Build workflow
- `python/run.sh stats_analytics.py` regenerates all figures/tables
- `cd latex && latexmk main.tex` builds PDF
- Registry: `python/analytics_registry.toml` maps scripts → texpart stems
- Adding a figure requires: script + .toml entry + `\input{}` or `\inputpgffigure{}` in main.tex
- `stats_analytics.py` performs a target-year caption audit and writes `review/data_quality_report.json` + `review/data_quality_report.md`
- Optional agent data MCP server: `bash python/run.sh -m mcp_servers.dp_data_server`. It wraps `stattool.fetch`/`Dataset` for bounded fetch, coverage, preview, registry, and data-quality-report tools. Do not make the deterministic LaTeX/Python build depend on this server.

## Build stability and error triage
- Never run concurrent TeX jobs for the same target (`main.tex`): one `latexmk`/`pdflatex` process at a time.
- Prefer `latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=build main.tex` for convergence.
- If manual passes are required, keep strict order: `pdflatex -> biber -> pdflatex -> pdflatex`.
- Treat `pdfTeX warning (dest): name{...} has been referenced but does not exist` as an acro hyperlink-target issue; do not "fix" by forcing unrelated bibliography edits.
- For csquotes/group failures (`Unbalanced groups`, `\end occurred inside a group`), audit Czech quote pairing in both `latex/texparts/**/*.tex` and `latex/socialnidialog.bib`; pure ASCII `"word"` is valid/preferred, while Unicode half-pairs such as `„word"` are errors.
- Early-pass undefined citations/references after cleanup are expected until biber + reruns complete; diagnose content only after full convergence.

## Agent behavior — required practices

### Rigour status in this workspace
- Rigour is disabled for this repository.
- Do not call Rigour tools (`mcp_rigour-*`) for checks, reviews, or pattern gates in this workspace.
- If quality validation is needed, use project-native checks (Python compile/tests, pipeline runs, and LaTeX build checks) instead.

### Ask before acting on ambiguous decisions
Use `vscode_askQuestions` when:
- A design decision has multiple reasonable options (e.g. dataset choice, indicator definition, country selection)
- Required information is not in context (e.g. year range, unit, comparison baseline)
- An action is irreversible or affects many files at once
Do NOT ask for confirmation on routine, clearly-scoped tasks described in the request.

### Citation integrity — MANDATORY
- **Only `socialnidialog.bib` entries are allowed as citations.** No external URLs, footnote-only attributions, or bare author-year strings may substitute for `\cite{key}` in LaTeX source.
- **Data must be backed by a bib entry.** Any dataset or statistic used in an analysis or commentary (Eurostat, OECD, MPSV, ISPV, ETUI, etc.) must have a corresponding BibLaTeX entry in `socialnidialog.bib`. If the entry is missing, add it via `Citace a zkratky` before using the data.
- If no bib entry can be created (missing metadata), do NOT use the data — raise the gap to the user.
- **Prefer end-of-block citations.** Place `\cite{}` at the end of the logical block/paragraph (or tightly-coupled sub-block), not inline in mid-sentence argument flow. Use the style `…konec věty.~\cite{key}` and chain multiple sources as `…konec věty.~\cite{key1}~\cite{key2}`.

### Source-evidence layer (`sources/`)
- `sources/transcripts/` holds raw OCR/copy-paste transcripts of source PDFs (large `.md` files); `sources/transcripts/nocite/` holds non-citable transcripts (own essays, working drafts, companion stanoviska).
- `sources/scrape/` holds the curated, structured extract for each source — one `.md` per source, starting with a fenced ```bibtex``` block whose key matches `socialnidialog.bib`.
- `sources/scrape/scraper-memory.md` is the master INDEX (file → topic → status → DP sections) plus cross-cutting data tables.
- `sources/scrape/_GLOSSARY_DP.md` is the thesis terminological glossary (KV, labour market, HRM, EU/ILO vocabulary in Czech + English, with acro key suggestions and scrape cross-links). Consult when choosing `\ac{}` IDs or checking term definitions.
- Use the `Scrape Sources` agent when adding/updating source extracts. Never cite a transcript directly — always cite the original source via the scrape's bib key.
- `NOCITE_*.md` and `*_TRANSCRIPT.md` scrapes are background only; their content can inform thesis prose but cannot be cited.

### Data credibility and comparability — handle carefully
- Always check that indicators are comparable across countries before plotting together (same definition, same year, same unit, same population scope)
- Note methodological breaks or coverage gaps in commentary (e.g. EU survey redesigns, national vs. Eurostat estimates)
- Prefer Eurostat/OECD harmonised series over national sources; document any deviation
- If two sources for the same indicator differ, raise the discrepancy rather than silently choosing one
- Never mix PPS and EUR series in the same axis without explicit normalisation
- `--` in generated tables = missing data → note it, do not silently drop countries

### Update READMEs and agents after structural changes
When a structural change is made (new module, renamed directory, new pipeline stage, new convention):
- Update `python/README.md` and/or `latex/README.md` as appropriate
- Update `.github/copilot-instructions.md` if the change affects project-wide conventions
- Update any relevant `.github/agents/*.agent.md` whose instructions reference the changed element
- Update `/memories/repo/*.md` notes that cover the changed area

### Use and propose workspace agents
- For tasks within an existing agent's domain, invoke it as a subagent (`runSubagent`) rather than doing the work inline
- Use `DP Thesis` as the main DP orchestration agent when a task spans multiple domains. It routes to specialized agents and keeps reusable CTUthesis mechanics separate from this thesis's data/evidence rules.
- Reusable CTUthesis agents: `Formatuj LaTeX`, `Acro Audit`, `Fix csquotes`, `CTUthesis Build Triage`.
- DP-specific agents: `Citace a zkratky`, `Scrape Sources`, `New Analysis`, `Sync Python From TeX`, `Thesis Audit`, `audit-bibliography`.
- After implementing a multi-step workflow that would recur (e.g. a new audit, a new sync pattern), propose saving it as a `.github/agents/*.agent.md` workspace agent
- When creating a new agent file: describe its domain, argumentHint, and explicit DO NOT USE cases (to avoid overlap with other agents)

## PGF figures (`apply_style_pgf` backend)
- Text rendered by LaTeX — `\ac{}`, `\SI{}{}`, `\acs{geo-XX}` work natively in figure text
- Include in commentary/main.tex: `\inputpgffigure{name}` (defined in `CTUthesis.cls`)
- Shows yellow warning box if `.pgf` missing (script not run); no hard error
- `texparts/figures/<name>.tex` — git-tracked, hand-editable; created once by Python, never overwritten
  - Contains: `\def\strNameCaption{...}%` + other string `\def`s + full `\begin{figure}...\end{figure}`
  - To regenerate defaults from data: delete file, re-run Python script
- `texparts/python/<name>.tex` — regenerated every run; single line `\inputpgffigure{name}` (backward compat)
- `python/figures/<name>.pgf` — regenerated every run; gitignored; macro references instead of literal strings
- Companion PNG assets from PGF export (typically colourbars) are deduplicated by content hash to `python/figures/_shared/`
- PGF files are rewritten to `_shared/img-<hash>.png` references (space-saving, cache-friendly)
- `strings={"key": "value"}` param on `savefig_pgf()` + `save_figure_tex_pgf()` drives the substitution
