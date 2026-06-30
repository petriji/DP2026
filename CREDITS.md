# Software Credits

Diplomová práce — Jiří Petříček, ČVUT MÚVS, 2026

This file lists the tools, libraries, and services used to author, compile, and
analyze data for this thesis. It mirrors the mandatory "Seznam použitého
softwaru" section rendered in the thesis PDF (`latex/texparts/references/list_software.tex`).

---

## Document authoring

- **[Visual Studio Code](https://code.visualstudio.com)** (latest) — MIT License
  - [LaTeX Workshop](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop) (`James-Yu.latex-workshop`)
  - [Remote - WSL](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl) (`ms-vscode-remote.remote-wsl`)

## LaTeX distribution

- **[TeX Live](https://tug.org/texlive/)** 2023 — various free/open licenses (per package)
  - Components used: `pdflatex`, `latexmk`, `biber`

## LaTeX packages

All available via [CTAN](https://ctan.org).

| Package | Purpose |
|---|---|
| [babel](https://ctan.org/pkg/babel) (czech, english) | language support |
| [biblatex](https://ctan.org/pkg/biblatex) (style: iso-numeric) | bibliography, ISO 690 citations |
| [biber](https://ctan.org/pkg/biber) | biblatex backend / bibliography processor |
| [TikZ](https://ctan.org/pkg/pgf) (library: external) | vector graphics and diagrams |
| [pgfplots](https://ctan.org/pkg/pgfplots) | scientific plots |
| [siunitx](https://ctan.org/pkg/siunitx) | physical units typesetting |
| [acro](https://ctan.org/pkg/acro) | acronym management |
| [hyperref](https://ctan.org/pkg/hyperref) | PDF hyperlinks |
| [csquotes](https://ctan.org/pkg/csquotes) | context-sensitive quotation marks |
| [geometry](https://ctan.org/pkg/geometry) | page margin settings |
| [titlesec](https://ctan.org/pkg/titlesec) (pagestyles) | heading and header formatting |
| [tocloft](https://ctan.org/pkg/tocloft) | table-of-contents formatting |
| [xltabular](https://ctan.org/pkg/xltabular) | multi-page tables |
| [booktabs](https://ctan.org/pkg/booktabs) | professional table rules |
| [caption](https://ctan.org/pkg/caption) | figure/table caption formatting |
| [subcaption](https://ctan.org/pkg/subcaption) | sub-figure captions |
| [pdfpages](https://ctan.org/pkg/pdfpages) | embedding external PDF pages |
| [microtype](https://ctan.org/pkg/microtype) | microtypography optimisation |
| [ocg-p](https://ctan.org/pkg/ocg-p) | PDF optional content groups (layers) |
| [amsmath](https://ctan.org/pkg/amsmath) | AMS mathematics |
| [amsfonts](https://ctan.org/pkg/amsfonts) | AMS fonts |
| [amssymb](https://ctan.org/pkg/amsfonts) (part of amsfonts) | AMS symbols |
| [lmodern](https://ctan.org/pkg/lm) | Latin Modern fonts |
| [xcolor](https://ctan.org/pkg/xcolor) | colour definitions |
| [blox](https://ctan.org/pkg/blox) | block diagrams (TikZ add-on) |
| [standalone](https://ctan.org/pkg/standalone) | compile standalone TikZ files |
| [enumitem](https://ctan.org/pkg/enumitem) | extended list environments |
| [multicol](https://ctan.org/pkg/multicol) | multi-column typesetting |
| [multirow](https://ctan.org/pkg/multirow) | table cells spanning multiple rows |
| [array](https://ctan.org/pkg/array) | extended array/tabular |
| [longtable](https://ctan.org/pkg/longtable) | tables spanning multiple pages |
| [footmisc](https://ctan.org/pkg/footmisc) | footnote formatting |
| [float](https://ctan.org/pkg/float) | improved float placement |
| [wasysym](https://ctan.org/pkg/wasysym) | miscellaneous symbols |
| [makeidx](https://ctan.org/pkg/makeidx) | index generation |

## Bibliography management

- **[Zotero](https://www.zotero.org)** (latest) — AGPL-3.0
  - Plugin: [Better BibTeX for Zotero](https://retorque.re/zotero-better-bibtex/) (used for auto-export of `.bib` files)

## Operating environment

- **[WSL 2](https://learn.microsoft.com/en-us/windows/wsl/)** (Windows Subsystem for Linux) — Ubuntu 22.04 LTS
- **[Git](https://git-scm.com)** — LGPL-2.1

## Version control hosting

- **[GitHub](https://github.com/petriji/DP)**

## Python data analysis

Python 3 (3.10+, [PSF-2.0](https://www.python.org)):

| Package | Purpose |
|---|---|
| pandas (`>=2.0`) | tabular data processing |
| geopandas (`>=0.14`) | geospatial data and choropleth maps |
| geodatasets | Natural Earth shapefiles (replaces `geopandas.datasets`) |
| matplotlib (`>=3.8`) | visualisation |
| matplotlib-scalebar | scale bar on choropleth maps |
| scipy | statistical distributions |
| requests | HTTP downloads (Eurostat SDMX API) |
| tqdm | progress bars |
| openpyxl | `.xlsx` support for `pd.read_excel` (IPP data) |
| xlrd (`>=2.0.1`) | `.xls` support for `pd.read_excel` (IPP 2007–2018) |
| numpy | numerical computing |
| shapely | geometry operations used by map rendering helpers |
| mcp (`>=1.9`) | optional MCP server wrappers around `stattool` data access |

See [python/requirements.txt](python/requirements.txt) for the authoritative, versioned list.
