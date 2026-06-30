================================================================================
 SOFTWARE CREDITS
 Diplomová práce — Jiří Petříček, ČVUT MÚVS, 2026
================================================================================


--------------------------------------------------------------------------------
 DOCUMENT AUTHORING
--------------------------------------------------------------------------------

Visual Studio Code (latest)
  https://code.visualstudio.com
  License: MIT

  Extensions:
    LaTeX Workshop  (James-Yu.latex-workshop)
      https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop
    Remote - WSL  (ms-vscode-remote.remote-wsl)
      https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl


--------------------------------------------------------------------------------
 LaTeX DISTRIBUTION
--------------------------------------------------------------------------------

TeX Live 2023
  https://tug.org/texlive/
  License: various free/open licenses (per package)
  Components used: pdflatex, latexmk, biber


--------------------------------------------------------------------------------
 LaTeX PACKAGES  (all available via CTAN: https://ctan.org)
--------------------------------------------------------------------------------

babel (czech, english)          — language support
  https://ctan.org/pkg/babel

biblatex  (style: iso-numeric)  — bibliography, ISO 690 citations
  https://ctan.org/pkg/biblatex

biber                           — biblatex backend / bibliography processor
  https://ctan.org/pkg/biber

TikZ  (library: external)       — vector graphics and diagrams
  https://ctan.org/pkg/pgf

pgfplots                        — scientific plots
  https://ctan.org/pkg/pgfplots

siunitx                         — physical units typesetting
  https://ctan.org/pkg/siunitx

acro                            — acronym management
  https://ctan.org/pkg/acro

hyperref                        — PDF hyperlinks
  https://ctan.org/pkg/hyperref

csquotes                        — context-sensitive quotation marks
  https://ctan.org/pkg/csquotes

geometry                        — page margin settings
  https://ctan.org/pkg/geometry

titlesec (pagestyles)           — heading and header formatting
  https://ctan.org/pkg/titlesec

tocloft                         — table-of-contents formatting
  https://ctan.org/pkg/tocloft

xltabular                       — multi-page tables
  https://ctan.org/pkg/xltabular

booktabs                        — professional table rules
  https://ctan.org/pkg/booktabs

caption                         — figure/table caption formatting
  https://ctan.org/pkg/caption

subcaption                      — sub-figure captions
  https://ctan.org/pkg/subcaption

pdfpages                        — embedding external PDF pages
  https://ctan.org/pkg/pdfpages

microtype                       — microtypography optimisation
  https://ctan.org/pkg/microtype

ocg-p                           — PDF optional content groups (layers)
  https://ctan.org/pkg/ocg-p

amsmath                         — AMS mathematics
  https://ctan.org/pkg/amsmath

amsfonts                        — AMS fonts
  https://ctan.org/pkg/amsfonts

amssymb                         — AMS symbols
  https://ctan.org/pkg/amsfonts  (part of amsfonts)

lmodern                         — Latin Modern fonts
  https://ctan.org/pkg/lm

xcolor                          — colour definitions
  https://ctan.org/pkg/xcolor

blox                            — block diagrams (TikZ add-on)
  https://ctan.org/pkg/blox

standalone                      — compile standalone TikZ files
  https://ctan.org/pkg/standalone

enumitem                        — extended list environments
  https://ctan.org/pkg/enumitem

multicol                        — multi-column typesetting
  https://ctan.org/pkg/multicol

multirow                        — table cells spanning multiple rows
  https://ctan.org/pkg/multirow

array                           — extended array/tabular
  https://ctan.org/pkg/array

longtable                       — tables spanning multiple pages
  https://ctan.org/pkg/longtable

footmisc                        — footnote formatting
  https://ctan.org/pkg/footmisc

float                           — improved float placement
  https://ctan.org/pkg/float

wasysym                         — miscellaneous symbols
  https://ctan.org/pkg/wasysym

makeidx                         — index generation
  https://ctan.org/pkg/makeidx


--------------------------------------------------------------------------------
 BIBLIOGRAPHY MANAGEMENT
--------------------------------------------------------------------------------

Zotero (latest)
  https://www.zotero.org
  License: AGPL-3.0

  Plugin: Better BibTeX for Zotero
    https://retorque.re/zotero-better-bibtex/
    (used for auto-export of .bib files)


--------------------------------------------------------------------------------
 OPERATING ENVIRONMENT
--------------------------------------------------------------------------------

WSL 2 (Windows Subsystem for Linux)
  https://learn.microsoft.com/en-us/windows/wsl/
  Ubuntu 22.04 LTS
    https://releases.ubuntu.com/22.04/

Git
  https://git-scm.com
  License: LGPL-2.1


--------------------------------------------------------------------------------
 VERSION CONTROL HOSTING
--------------------------------------------------------------------------------

GitHub
  https://github.com/petriji/DP
  Branch: py_stats


--------------------------------------------------------------------------------
 PYTHON DATA ANALYSIS
--------------------------------------------------------------------------------

Python 3 (3.10+)
  https://www.python.org
  License: PSF-2.0

  pandas (>=2.0)                  — tabular data processing
    https://pandas.pydata.org

  geopandas (>=0.14)              — geospatial data and choropleth maps
    https://geopandas.org

  geodatasets                     — Natural Earth shapefiles (replaces geopandas.datasets)
    https://geodatasets.readthedocs.io

  matplotlib (>=3.8)              — visualisation
    https://matplotlib.org

  matplotlib-scalebar             — scale bar on choropleth maps
    https://github.com/ppinard/matplotlib-scalebar

  scipy                           — statistical distributions
    https://scipy.org

  requests                        — HTTP downloads (Eurostat SDMX API)
    https://requests.readthedocs.io

  tqdm                            — progress bars
    https://tqdm.github.io

  openpyxl                        — .xlsx support for pd.read_excel (IPP data)
    https://openpyxl.readthedocs.io

  xlrd (>=2.0.1)                  — .xls support for pd.read_excel (IPP 2007–2018)
    https://xlrd.readthedocs.io

================================================================================

