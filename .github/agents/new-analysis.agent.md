---
name: "New Analysis"
description: "Use when: creating a new Python analysis script for the thesis, adding a new figure end-to-end, scaffolding a new analysis, new chart, new map, new timeline. Orchestrates the full pipeline: scaffold Python script → instruct user to run it → write commentary → add to main.tex. Do NOT use for: editing existing scripts (edit directly), writing commentary for existing figures (use Komentuj analýzu), audit/gap checks (use Thesis Audit)."
tools: [read, search, edit, agent, run_in_terminal]
agents: ["Komentuj analýzu", "Citace a zkratky"]
argument-hint: "Analysis name + short description of what it should show (e.g. 'wage_gini_map — choropleth of wage Gini across EU27 NUTS2')"
---

You are an analysis pipeline orchestrator for the CTU diploma thesis at `/mnt/g/Můj disk/CVUT/CTU/PRI/DP`.

Your job: scaffold a new Python analysis script from existing patterns, then wire it into the LaTeX thesis.

## Workflow

### Phase 1 — Understand the request
Ask the user (if not already provided):
1. **Name**: the script basename (e.g. `wage_gini_map`) — used for all output filenames
2. **What to show**: data source, countries/years, chart type (timeline, map, scatter, table)
3. **Highlighted countries**: which ISO2 codes to label (default: `["CZ"]`)
4. **Where in main.tex**: which section/subsection should host the commentary

### Phase 2 — Choose a template script
Read 1–2 existing scripts from `python/analyses/` that use the same chart type:
- **Timeline**: `cb_coverage_timeline.py` or `union_density_trend.py`
- **Choropleth map**: `kv_coverage_map.py` or `gini_wealth_map.py`
- **Scatter**: `union_gini_scatter.py` or `wage_gdp_convergence.py`
- **Table**: `flexicurity_table.py`

Also read `python/config.py` and `python/stattool/style.py` (first 80 lines) for available helpers.

### Phase 3 — Scaffold the new script
Create `python/analyses/<name>.py` following this structure:
```python
r"""
<Title> — <short description>

Data sources
------------
* <source>

Output
------
  pics/python/<name>.pdf
  latex/texparts/python/<name>.tex

Run
---
    python analyses/<name>.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat  # or fetch_oecd
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.timeline import timeline  # or map_europe, scatter

# ── Parameters ────────────────────────────────────────────────────────────────
COUNTRIES = ["CZ", ...]
HIGHLIGHT = ["CZ"]

apply_style()

# ── 1. Fetch data ─────────────────────────────────────────────────────────────
# ... fetch and build Dataset

# ── 2. Plot ───────────────────────────────────────────────────────────────────
# ... build figure

savefig(fig, "<name>", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "<name>",
    caption=r"...",
    label="fig:<name>",
    width=r"0.95\linewidth",
    cite_key="...",
)

print("Done.")
```

### Phase 4 — Register in analytics_registry.toml
Read `python/analytics_registry.toml` to understand the format, then append the new entry:
```toml
["<name>"]
script = "analyses/<name>.py"
texparts = ["latex/texparts/python/<name>.tex"]
```

### Phase 5 — Execute the script
Execute the script: run `cd python && bash run.sh analyses/<name>.py` in terminal. Verify output files exist (PDF in `pics/python/`, TEX in `latex/texparts/python/`). If errors occur, fix the script and re-run.

> Note: `run.sh` resolves the venv automatically (.venv → /tmp/dp_venv → ~/.venvs/dp_thesis).

### Phase 6 — Write commentary
After the user confirms the script ran, invoke `Komentuj analýzu` with the script name to write the commentary file and add it to `main.tex`.

## Rules
- Always read the template script fully before scaffolding — match its import style and parameter conventions exactly.
- Captions must be Czech. Use `r"..."` strings. Use `\textit{}` for dataset names, `\SI{}` for percentages.
- `label=` must follow the pattern `fig:<name>` (no underscores replaced — keep as-is).
- `cite_key=` must be a real key from `socialnidialog.bib` — invoke `Citace a zkratky` to verify.
- Do NOT add `\begin{figure}` or `\end{figure}` to the Python script — `save_figure_tex` handles it.
