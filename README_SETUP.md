# Environment Setup — Diplomová práce (ČVUT MÚVS, 2026)

Prerequisites: Windows 10 (build 19041+) or Windows 11, administrator rights.

---

## Step 1 — Enable WSL 2 and install Ubuntu

Open **PowerShell as Administrator**:

```powershell
wsl --install
```

Reboot when prompted. Ubuntu 22.04 LTS is installed by default.  
After reboot, open Ubuntu from the Start menu and set your Linux username/password.

Verify WSL version:

```powershell
wsl --list --verbose
# Ubuntu entry must show VERSION 2
```

---

## Step 2 — Install TeX Live (full)

In the **Ubuntu terminal**:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install texlive-full -y
```

> Download ~5 GB; installation takes 15–30 min depending on connection speed.  
> Installs `pdflatex`, `latexmk`, `biber`, and all required packages.

Verify:

```bash
pdflatex --version
latexmk --version
biber --version
```

---

## Step 3 — Install VS Code and extensions

1. Download and install **VS Code** from <https://code.visualstudio.com>
2. Install the following extensions inside VS Code:
   - **Remote - WSL** (`ms-vscode-remote.remote-wsl`)
   - **LaTeX Workshop** (`James-Yu.latex-workshop`)

Open the project through Remote - WSL:  
`F1` → *Remote-WSL: Open Folder in WSL* → navigate to the cloned repository.

---

## Step 4 — Clone the repository

In the **Ubuntu terminal**:

```bash
sudo apt install git -y
git clone <REPO_URL>
cd <REPO_DIRECTORY>
```

---

## Step 5 — Configure LaTeX Workshop

The project's `latex/latexmkrc` sets the build output directory to `build/`.  
Add the following to your VS Code `settings.json` (workspace or user):

```json
"latex-workshop.latex.outDir": "%DIR%/build"
```

The default `latexmk` build tool in LaTeX Workshop is otherwise sufficient.  
To build, open `latex/main.tex` and press `Ctrl+Alt+B`.

---

## Step 6 — Compile manually (without VS Code)

From inside the `latex/` directory:

```bash
# Standard build
latexmk -pdf -outdir=build main.tex

# With TikZ externalization (required for diagrams)
latexmk -pdf -shell-escape -outdir=build main.tex

# Clean all build artefacts
latexmk -C -outdir=build main.tex
```

---

## Step 7 — Bibliography

`biber` is invoked automatically by `latexmk`. No manual step required.

Bibliography source files (in `latex/`):
- `socialnidialog.bib`
- `socialnidialog-zotero.bib`
- `socialnidialog-bibtexmanager.bib`

To manage references, use **Zotero** (<https://www.zotero.org>) with the
**Better BibTeX** plugin (<https://retorque.re/zotero-better-bibtex/>)
configured to auto-export the `.bib` files into `latex/`.

---

## Step 8 — Python data analysis

The `python/` sub-project generates all PDF figures and LaTeX table snippets
used in the thesis.

### 8.1 — Create a virtual environment

```bash
cd python
bash setup_venv.sh        # creates .venv with --copies (NTFS-safe)
```

> **WSL 2 + Windows drive (9p/drvfs):** Python `venv` requires symlinks which
> are not supported on NTFS mounts.  Create the venv on a native Linux
> filesystem instead:
> ```bash
> python3 -m venv /tmp/dp_venv
> /tmp/dp_venv/bin/pip install -r requirements.txt
> ```
> Run scripts via `/tmp/dp_venv/bin/python`.
> Note: `/tmp/dp_venv` does **not** survive a WSL restart — recreate as needed.

### 8.2 — Run the pipeline

```bash
bash run.sh stats_analytics.py              # regenerate all missing outputs
bash run.sh stats_analytics.py --force all  # force-regenerate everything
bash run.sh analyses/gdp_ppp_timeline.py    # single script
```

Outputs land in `pics/python/` (PDF figures) and `latex/texparts/python/`
(`.tex` fragments); both are gitignored and auto-created on first run.

### 8.3 — LaTeX integration

The pipeline runs automatically before every LaTeX build:

- **VS Code / LaTeX Workshop:** use the recipe
  *`stats_analytics → pdflatex → biber → pdflatex×2`*
- **`latexmk` (CLI):** `latexmkrc` invokes `stats_analytics.py` as a pre-build
  step.  Set `SKIP_PYTHON_ANALYTICS=1` to skip it.

Both hooks are no-ops when all outputs already exist.

---

## Notes on repository-local files

| File | Purpose |
|---|---|
| `latex/CTUthesis.cls` | Custom LaTeX class — contains all `\RequirePackage` declarations |
| `latex/latexmkrc` | Sets `$out_dir = 'build'` |
