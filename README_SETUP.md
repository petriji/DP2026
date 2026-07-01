# Environment Setup — Diplomová práce (ČVUT MÚVS, 2026)

This guide walks a new contributor through setting up a working environment to
**compile the thesis PDF from scratch**, with no prior knowledge of this
repository assumed. Pick the option matching your OS in each step; the rest of
the guide (cloning, compiling, Python pipeline) is the same for everyone.

> A ready-to-use container setup is available for this repository and future
> clones of `DP2026`. The **primary path is the prebuilt GitHub-hosted image
> (GHCR)** — no local Docker build required. Building locally via
> `Dockerfile`/`docker-compose.yml` remains available as an optional
> alternative for contributors who want to modify the container itself.

What you'll end up with:
- A working TeX Live installation (`pdflatex`, `latexmk`, `biber`)
- A Python 3.10+ virtual environment for the data/figure pipeline
- (Optional) VS Code with LaTeX Workshop for an integrated build workflow

---

## Container Quick Start (Docker) — recommended: prebuilt GHCR image

The fastest way to get a working environment is to pull the prebuilt image —
no local Docker build, no manual TeX Live/Python install.

- Workflow that builds/publishes it: `.github/workflows/docker-ghcr.yml`
- Published image: `ghcr.io/petriji/dp2026-thesis`
- Auto-publish on push to `main` and on version tags (`v*`)

**This requires the repository to have been pushed to GitHub at least once
with this workflow present, and the workflow to have run successfully** (on
push to `main`, or manually via the Actions tab). Until then, no image exists
yet at `ghcr.io/petriji/dp2026-thesis` to pull.

Pull and run the hosted image (works with this repo or a future `DP2026`
clone, unchanged):

```bash
git clone https://github.com/petriji/DP2026.git
cd DP2026

docker pull ghcr.io/petriji/dp2026-thesis:latest
docker run --rm -it -v "$PWD":/workspace/DP2026 -v /workspace/DP2026/.venv \
  -w /workspace/DP2026 \
  ghcr.io/petriji/dp2026-thesis:latest bash tools/docker_verify_full_build.sh
```

The extra `-v /workspace/DP2026/.venv` creates an anonymous volume that shadows
any host-side `.venv` at the repo root — without it, a pre-existing host
`.venv` leaks into the container (its `bin/python` symlink resolves to the
host's own `/usr/bin/python3`, absent inside the container), causing
`python: command not found`. `docker compose` (below) avoids this
automatically via its named `dp2026-venv` volume.

Requires a working local Docker installation with access to the Docker
daemon/socket (or an equivalent runtime such as Podman). If you don't have
Docker available locally, use the native setup in Step 1 onward instead.

### Optional: build the image locally instead of pulling from GHCR

Useful only if you are modifying the `Dockerfile` itself.

```bash
# From repository root
docker compose build dp2026

# Open a shell in the container
docker compose run --rm dp2026 bash

# Verify full pipeline + thesis build
docker compose run --rm dp2026 bash tools/docker_verify_full_build.sh
```

Container defaults:
- Workdir in container: `/workspace/DP2026`
- Repository mounted to: `/workspace/DP2026`
- Persistent venv volume: `dp2026-venv` (mounted to `/workspace/DP2026/.venv`)

---

## Step 1 — Set up a Linux environment

### Option A — Native Linux (Ubuntu/Debian-based, recommended for CI/servers)

Most distributions already give you a suitable shell; just make sure `apt` (or
your package manager's equivalent) is available. Skip to [Step 2](#step-2--install-tex-live-full).

### Option B — Windows via WSL 2

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

All subsequent `bash` steps in this guide run **inside the Ubuntu terminal**.

### Option C — macOS

Use a native macOS shell (Terminal.app/iTerm2) — no VM needed. Install
[Homebrew](https://brew.sh) first if you don't have it:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Wherever this guide says `apt install <pkg>`, use `brew install <pkg>` instead
(package names may differ slightly — noted per step).

---

## Step 2 — Install TeX Live (full)

**Linux (native or WSL):**

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install texlive-full -y
```

> Download ~5 GB; installation takes 15–30 min depending on connection speed.
> Installs `pdflatex`, `latexmk`, `biber`, and all required packages.

**macOS:**

```bash
brew install --cask mactex
```

> [MacTeX](https://tug.org/mactex/) is the macOS-equivalent full TeX Live
> distribution (~5 GB). Restart your terminal after install so `PATH` picks up
> `/Library/TeX/texbin`.

Verify (all platforms):

```bash
pdflatex --version
latexmk --version
biber --version
```

---

## Step 3 — Install VS Code and extensions (optional but recommended)

1. Download and install **VS Code** from <https://code.visualstudio.com>
2. Install the following extensions inside VS Code:
   - **LaTeX Workshop** (`James-Yu.latex-workshop`)
   - **Remote - WSL** (`ms-vscode-remote.remote-wsl`) — **Windows/WSL only**

If you're on WSL, open the project through Remote - WSL:
`F1` → *Remote-WSL: Open Folder in WSL* → navigate to the cloned repository.
On native Linux/macOS just open the cloned folder directly.

---

## Step 4 — Clone the repository

```bash
# Debian/Ubuntu (native or WSL) — install git if needed
sudo apt install git -y
# macOS: git ships with Xcode Command Line Tools, or `brew install git`

git clone https://github.com/petriji/DP2026.git
cd DP2026
```

---

## Step 5 — Configure LaTeX Workshop

Workspace settings for LaTeX Workshop are already committed in
[.vscode/settings.json](.vscode/settings.json) — opening this folder in VS
Code picks them up automatically, including `latex-workshop.latex.outDir`
(pointing at `build/`) and all custom build recipes. No manual configuration
is needed.

To build, open `latex/main.tex`, pick a recipe from the LaTeX Workshop sidebar
(or press `Ctrl+Alt+B` to run the last-used one). See
[latex/README.md](latex/README.md#vs-code--latex-workshop-recipes) for what
each recipe does.

---

## Step 6 — Compile manually (without VS Code)

From inside the `latex/` directory:

```bash
# Standard build
latexmk -pdf -outdir=build main.tex

# Standalone Python pipeline attachment
latexmk -pdf -outdir=build python_pipeline_attachment.tex

# With TikZ externalization (required for diagrams)
latexmk -pdf -shell-escape -outdir=build main.tex

# Clean all build artefacts
latexmk -C -outdir=build main.tex
```

> **Runtime:** a full thesis build (many TikZ/pgfplots figures, multiple
> `pdflatex`+`biber` passes) takes roughly **40 minutes**, varying widely with
> your machine's CPU speed. Incremental rebuilds after small edits are much
> faster since `latexmk` only reruns what changed.
>
> If using VS Code with LaTeX Workshop, [latex/README.md](latex/README.md#vs-code--latex-workshop-recipes)
> documents the pre-configured recipes (fast single-pass build, analytics-only,
> full clean rebuild, poster, publish) available from the sidebar / `Ctrl+Alt+B`.

---

## Step 7 — Bibliography

`biber` is invoked automatically by `latexmk`. No manual step required.

Bibliography source file (in `latex/`):
- `socialnidialog.bib`

To manage references, use **Zotero** (<https://www.zotero.org>) with the
**Better BibTeX** plugin (<https://retorque.re/zotero-better-bibtex/>)
configured to auto-export the `.bib` files into `latex/`.

---

## Step 8 — Python data analysis

The `python/` sub-project generates all PDF figures and LaTeX table snippets
used in the thesis. Requires Python 3.10+.

```bash
# Linux (native or WSL) — if python3-venv/pip aren't already installed
sudo apt install python3-venv python3-pip -y
# macOS — Homebrew's python3 already includes venv/pip
```

### 8.1 — Create a virtual environment

```bash
cd python
bash setup_venv.sh        # creates python/.venv with --copies (NTFS-safe)
```

`python/run.sh` (used by every command below and by the LaTeX build) resolves
the virtual environment in this order, so any of these locations works:

1. `python/.venv` — created by `setup_venv.sh` above (preferred)
2. `<repo-root>/.venv` — if you prefer a repo-root venv (e.g. `python3 -m venv .venv` from the repository root)
3. `/tmp/dp_venv` — fallback for filesystems where `venv` symlinks don't work
4. `~/.venvs/dp_thesis` — legacy fallback location

> **WSL 2 + Windows drive (9p/drvfs) only:** Python `venv` requires symlinks
> which are not supported on NTFS-backed mounts (`/mnt/c/...`). If your
> checkout lives on a Windows drive, create the venv on a native Linux
> filesystem instead (this does not apply to native Linux or macOS):
> ```bash
> python3 -m venv /tmp/dp_venv
> /tmp/dp_venv/bin/pip install -r requirements.txt
> ```
> Note: `/tmp/dp_venv` does **not** survive a WSL restart — recreate as needed.

### 8.2 — Run the pipeline

```bash
bash run.sh stats_analytics.py              # regenerate all missing outputs
bash run.sh stats_analytics.py --force all  # force-regenerate everything
bash run.sh analyses/stav_hdp_vyvoj.py      # single script
```

> **Runtime:** roughly **10 minutes** from an empty cache — dominated by
> network downloads from Eurostat/OECD/other providers, so actual time
> depends heavily on your connection speed. Cached datasets in `python/data/`
> make subsequent runs much faster.

Outputs land in `pics/python/` (PDF figures) and `latex/texparts/python/`
(`.tex` fragments); both are gitignored and auto-created on first run.
The standalone attachment `latex/python_pipeline_attachment.tex` documents this
flow as a brief PDF built to `latex/build/python_pipeline_attachment.pdf`.

### 8.3 — LaTeX integration

- **VS Code / LaTeX Workshop:** the **Build + Analytics** recipe (and its
  force-regenerate variants) runs `stats_analytics.py` before `latexmk`; see
  the recipe table in [latex/README.md](latex/README.md#vs-code--latex-workshop-recipes).
- **`latexmk` (CLI):** analytics regeneration is **off by default** — set
  `RUN_PYTHON_ANALYTICS=1` to have `latexmkrc` run `stats_analytics.py` as a
  pre-build step:
  ```bash
  RUN_PYTHON_ANALYTICS=1 latexmk -pdf -outdir=build main.tex
  ```

Without `RUN_PYTHON_ANALYTICS=1`, `latexmk` builds only from whatever
figures/tables already exist under `pics/python/` and `latex/texparts/python/`
— run the pipeline manually first (Step 8.2) if those are missing.

---

## Notes on repository-local files

| File | Purpose |
|---|---|
| `latex/CTUthesis.cls` | Custom LaTeX class — contains all `\RequirePackage` declarations |
| `latex/latexmkrc` | Sets `$out_dir = 'build'` |
