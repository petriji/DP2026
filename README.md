# Sociální dialog a kolektivní vyjednávání

Diplomová práce (master's thesis) — Jiří Petříček, ČVUT MÚVS, 2026.

This repository contains the full LaTeX source of the thesis *"Sociální dialog
a kolektivní vyjednávání"* (Social dialogue and collective bargaining), together
with a Python data pipeline that downloads statistical data (Eurostat, OECD,
MPSV, ISPV, …) and regenerates every figure and table used in the document.

## Repository layout

| Path | Contents |
|---|---|
| [latex/](latex/) | Thesis LaTeX sources, custom `CTUthesis`/`CTUposter` class, bibliography (`socialnidialog.bib`) |
| [python/](python/) | Data-analysis pipeline that generates figures/tables consumed by the LaTeX build |
| [sources/](sources/) | Curated source-material used for thesis prose |
| [review/](review/) | Build/data-quality audit outputs |
| [.github/](.github/) | Project conventions and Copilot agent/skill definitions |

## Quick start

Full step-by-step environment setup (WSL/Windows, native Linux, macOS) lives in
**[README_SETUP.md](README_SETUP.md)** — start there if you are setting up the
project for the first time.

A prebuilt, GitHub-hosted container image (GHCR) is available — no local
Docker build required:

```bash
docker pull ghcr.io/petriji/dp2026-thesis:latest
docker run --rm -it -v "$PWD":/workspace/DP2026 -v /workspace/DP2026/.venv \
  -w /workspace/DP2026 \
  ghcr.io/petriji/dp2026-thesis:latest bash tools/docker_verify_full_build.sh
```

The extra `-v /workspace/DP2026/.venv` creates an anonymous volume that shadows
any host-side `.venv` at the repo root. Without it, a pre-existing host `.venv`
leaks into the container (its `bin/python` symlink resolves to the host's own
`/usr/bin/python3`, which does not exist inside the container), causing
`python: command not found`.

The image is built and published automatically by
`.github/workflows/docker-ghcr.yml` on every push to `main`. Building locally
via `Dockerfile` + `docker-compose.yml` is also possible and documented in
[README_SETUP.md](README_SETUP.md), but not required.

Once TeX Live and Python are installed:

```bash
git clone https://github.com/petriji/DP2026.git
cd DP/latex
latexmk -pdf -outdir=build main.tex
```

The build automatically regenerates any missing figures/tables via the Python
pipeline before running `pdflatex`/`biber`. Expect roughly **10 minutes** for
the first analytics run (network-dependent, downloads/caches source datasets)
and roughly **40 minutes** for a full thesis build (compute-dependent, many
figures + multiple `pdflatex`/`biber` passes); subsequent builds are
incremental and much faster. If using VS Code with LaTeX Workshop, see the
recipe table in [latex/README.md](latex/README.md#vs-code--latex-workshop-recipes)
for pre-configured build variants (fast single-pass, analytics-only, full
clean rebuild, poster, publish).

Output: `latex/build/main.pdf`.

## Documentation index

- **[README_SETUP.md](README_SETUP.md)** — environment setup from scratch (OS, TeX Live, VS Code, Python venv)
- **[latex/README.md](latex/README.md)** — CTUthesis LaTeX conventions (acronyms, citations, figures, labels)
- **[python/README.md](python/README.md)** — data pipeline structure, adding new figures, running analyses
- **[CREDITS.md](CREDITS.md)** — software, libraries, and services used to author and build the thesis

## Building the poster

An accompanying A1 poster (`latex/poster.tex`) reuses the same figure pipeline
at a reduced font size. See the *"A1 Poster figures"* section in
[python/README.md](python/README.md) for the full build recipe.

## License

Academic thesis submitted to ČVUT (Czech Technical University in Prague),
Masarykův ústav vyšších studií. All rights reserved by the author unless
stated otherwise in individual source files. See [CREDITS.md](CREDITS.md) for
third-party tool/library licenses.
