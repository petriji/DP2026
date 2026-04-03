# python — thesis figure pipeline

*Jiří Petříček 2026 · Built with Claude Sonnet 4.6, April 2026*

Generates PDF figures and LaTeX snippets from Eurostat data for the CTU thesis.
All outputs land in `pics/python/` (PDF figures) and `latex/texparts/python/` (.tex
environments) — both gitignored, both auto-created on first run.

## Setup

```bash
cd python
bash setup_venv.sh        # creates .venv with --copies (NTFS-safe)
```

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
├── stattool/               – data layer
│   ├── fetch.py            – Eurostat SDMX download + cache
│   ├── dataset.py          – Dataset wrapper (pivot, filter, normalise)
│   └── style.py            – Matplotlib style + savefig/save_figure_tex
├── statout/                – visualisation layer
│   ├── timeline.py         – line chart (single countries + groups)
│   ├── map_europe.py       – choropleth map (EPSG:3035)
│   ├── scatter.py          – scatter plot
│   └── table.py            – LaTeX table from DataFrame
└── analyses/               – one script per figure group
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
