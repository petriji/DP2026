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
```

## Layout

```
python/
├── config.py               – paths, figure size, font, colour palette
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
