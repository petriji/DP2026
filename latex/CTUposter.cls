%%
%% CTUposter.cls — A1 conference / defence poster class for CTU theses.
%%
%% Standalone class (NOT derived from CTUthesis.cls — that one is built on
%% report.cls with chapter/cover machinery and fixed A4 geometry that is not
%% compatible with a single-page A1 poster).  The package set, language
%% handling, math, TikZ and bibliography setup deliberately mirror
%% CTUthesis.cls so that figure/acro/SI/cite macros from the thesis source
%% can be reused without changes.
%%
%% Layout
%%   • A1 portrait (594 mm × 841 mm) single page
%%   • Full-width title block on top (title, optional subtitle, author,
%%     affiliation, optional logo)
%%   • Body in two equal-width columns (multicols*)
%%   • Author-side commands:
%%       \postertitle{}, \postersubtitle{}, \posterauthor{},
%%       \posteraffiliation{}, \posteryear{}, \postercontact{},
%%       \posterlogo{path}, \postersupervisor{}
%%       \makepostertitle           — full-width header block
%%       \abstractCS{...} / \abstractEN{...}   — emphasized abstract boxes
%%       \postersummary{...}        — English summary near the end
%%       \postercontactblock         — hline + sans-serif contact + year
%%
%% Options
%%   english     — switch UI strings (Abstract / Summary / Contact / Year)
%%   czech       — default; same labels in Czech
%%   draft       — pdfdraft on graphics, faster compile, watermark
%%
%% Build
%%   pdflatex + biber (same toolchain as the main thesis).
%%
\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{CTUposter}[2026/04/23 v0.1 CTU A1 poster]

% ----------------------------------------------------------------------------
% Options
% ----------------------------------------------------------------------------
\newif\ifCTUP@english   \CTUP@englishfalse
\newif\ifCTUP@draft     \CTUP@draftfalse

\DeclareOption{english}{\CTUP@englishtrue}
\DeclareOption{czech}  {\CTUP@englishfalse}
\DeclareOption{draft}  {\CTUP@drafttrue}
\DeclareOption{final}  {\CTUP@draftfalse}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{extarticle}}
\ProcessOptions\relax

% Base class — extarticle gives 14/17/20pt sizes; we still scale further.
\LoadClass[a4paper,17pt]{extarticle}

% ----------------------------------------------------------------------------
% Page geometry — A1 portrait with generous symmetric margins
% ----------------------------------------------------------------------------
\RequirePackage[
  paperwidth   = 594mm,
  paperheight  = 841mm,
  left         = 25mm,
  right        = 25mm,
  top          = 25mm,
  bottom       = 25mm,
  includehead  = false,
  includefoot  = false,
]{geometry}

% ----------------------------------------------------------------------------
% Encoding, language, fonts
% ----------------------------------------------------------------------------
\RequirePackage[english,czech]{babel}
\RequirePackage[T1]{fontenc}
\RequirePackage[utf8]{inputenc}
\RequirePackage{lmodern}
\RequirePackage{microtype}
\RequirePackage{anyfontsize}      % allow arbitrary sizes (\fontsize{60}{72})

% ----------------------------------------------------------------------------
% Inherited thesis metadata (written by latexmkrc into build/main-*.tmp)
%
% These files are produced by the same latexmkrc that builds main.tex:
%   build/main-gitauthor.tmp   → \gdef\@author{...}
%   build/main-gitemail.tmp    → \gdef\@email{...}
%   build/main-normostrana.tmp → \normostrana{N}     (sets \@normostrana)
%   build/main-stats.tmp       → \@CTUnfigures, \@CTUntables, \@CTUnattachments,
%                                \@CTUgitrepo, \@CTUgittag, \@CTUgitsha
%
% On the poster we always read main-* (not <jobname>-*), because the poster
% jobname differs from the thesis but the metadata logically belongs to the
% thesis being summarised.  Missing files are silently ignored — every value
% has a safe default and may be overridden in the preamble.
% ----------------------------------------------------------------------------
% Defaults so undefined references never expand to \relax mid-document.
% (No \makeatletter needed — @ is a letter throughout a .cls file.)
\gdef\@author{Name Surname}
\gdef\@email{address@e-mail.xy}
\gdef\@normostrana{}
\gdef\@CTUnfigures{0}
\gdef\@CTUntables{0}
\gdef\@CTUnattachments{0}
\gdef\@CTUgitrepo{}
\gdef\@CTUgittag{}
\gdef\@CTUgitsha{}
% \normostrana is the public command used by latexmkrc's tmp file.
\providecommand\normostrana[1]{\gdef\@normostrana{#1}}
% Load tmp files only at \AtBeginDocument: the latexmkrc-generated stats and
% textcheck files contain their own \makeatletter…\makeatother pair, which
% would permanently change @'s catcode if read during class loading (where @
% is a letter).  At \AtBeginDocument @ is "other" anyway, so the embedded
% \makeatletter/other works as intended and is locally scoped.
\AtBeginDocument{%
  \InputIfFileExists{build/main-gitauthor.tmp}{}{}%
  \InputIfFileExists{build/main-gitemail.tmp}{}{}%
  \InputIfFileExists{build/main-normostrana.tmp}{}{}%
  \InputIfFileExists{build/main-stats.tmp}{}{}%
}

% Switch main language at \begin{document} when english option is given.
\AtBeginDocument{%
  \ifCTUP@english
    \selectlanguage{english}%
  \else
    \selectlanguage{czech}%
  \fi
}

% ----------------------------------------------------------------------------
% Graphics, captions, math, units, colors, TikZ
% ----------------------------------------------------------------------------
\RequirePackage[pdftex,final]{graphicx}
\graphicspath{{logo/}{../python/figures/}{texparts/figures/}}
\RequirePackage{float}
\RequirePackage{caption}
\RequirePackage{subcaption}
\captionsetup{font=small,labelfont=bf,skip=4pt}

\RequirePackage{amsmath,amsfonts,amssymb}
\RequirePackage{siunitx}
\sisetup{
  output-decimal-marker = {,},
  group-separator       = {\,},
  per-mode              = symbol,
  detect-weight         = true,
  detect-family         = true,
}
% Project-specific units (mirrors CTUthesis acro_variables.tex usage).
\DeclareSIUnit{\czk}{\text{Kč}}
\DeclareSIUnit{\eur}{\text{EUR}}
\DeclareSIUnit{\pps}{\text{PPS}}
\DeclareSIUnit{\person}{\text{os.}}
\DeclareSIUnit{\week}{\text{týd.}}
\DeclareSIUnit{\month}{\text{měs.}}

\RequirePackage{xcolor}
\definecolor{CTUblue}{RGB}{0,101,189}
\definecolor{CTUgrey}{RGB}{84,88,90}
\definecolor{CTUlight}{RGB}{235,238,243}

% Keep map labels readable on colored backgrounds (same as thesis class).
\RequirePackage[pdftex]{contour}
\contourlength{0.6pt}

\RequirePackage{tikz}
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,calc}
\RequirePackage{pgfplots}
\pgfplotsset{compat=1.18}

\RequirePackage{enumitem}
\setlist{nosep,leftmargin=*}

\RequirePackage{csquotes}

% Two-column body
\RequirePackage{multicol}
\setlength{\columnsep}{18mm}
\setlength{\columnseprule}{0pt}

% ----------------------------------------------------------------------------
% Hyperref (loaded late, before biblatex)
% ----------------------------------------------------------------------------
\RequirePackage[
  pdftex,
  draft         = false,
  hidelinks,
  unicode       = true,
  bookmarks     = false,
  pdfpagelayout = SinglePage,
]{hyperref}

% Tooltip annotations used by generated PGF assets.
\RequirePackage{pdfcomment}

% Compatibility macro referenced by generated PGF strings from thesis pipeline.
% On posters we keep the tooltip but do not create a goto destination link.
\newcommand{\CTUtooltiplink}[3]{\pdftooltip{#2}{#3}}

\RequirePackage[
  backend     = biber,
  style       = iso-numeric,
  sortlocale  = cs_CZ,
  autolang    = none,    % all entries typeset in the document main language
  bibencoding = UTF8,
]{biblatex}

% Force all bibliography entries to use the chosen biblio language strings
% („Dostupné z“, „cit.“, etc.) regardless of each entry's own `langid`.
% \CTUP@biblang holds the babel language used at \printbibliography time;
% the english class option flips it to english.
\DeclareLanguageMapping{czech}{czech-iso}
\DeclareLanguageMapping{english}{english-iso}
\ifCTUP@english
  \def\CTUP@biblang{english}%
\else
  \def\CTUP@biblang{czech}%
\fi
% Force the few user-visible bibliography strings into the chosen language.
% This is necessary because biblatex resolves \bibstring at \begin{document}
% from the entry's `langid` (or English when langid is missing) and a later
% \selectlanguage does not invalidate that resolution.  By redefining the
% English strings we override whatever default was baked in.
\AtBeginDocument{%
  \def\CTUP@bs@czech{%
    \DefineBibliographyStrings{english}{%
      urlfrom = {dostupn\'{e} z},%
      urlseen = {cit\adddot},%
      urlalso = {dostupn\'{e} tak\'{e} z},%
      bysupervisor = {vedouc\'{i} pr\'{a}ce},%
    }%
    \DefineBibliographyStrings{czech}{%
      urlfrom = {dostupn\'{e} z},%
      urlseen = {cit\adddot},%
    }%
  }%
  \def\CTUP@bs@english{%
    \DefineBibliographyStrings{english}{%
      urlfrom = {available from\addnbspace},%
      urlseen = {visited on},%
    }%
    \DefineBibliographyStrings{czech}{%
      urlfrom = {available from\addnbspace},%
      urlseen = {visited on},%
    }%
  }%
  \ifx\CTUP@biblang\CTUP@biblang@en\CTUP@bs@english\else\CTUP@bs@czech\fi
}
\def\CTUP@biblang@en{english}

% Bibliography list formatting — render entry numbers as "[1]" (matching the
% in-text citation form) instead of the iso-numeric default "1." marker.
%   labelnumberwidth = the bold "[N]" label printed in the left margin
%                      of every \printbibliography entry
%   bibenvname        — keep biblatex's default `bibliography` list env
% Keeps the in-text \cite{} appearance untouched (already uses brackets).
\DeclareFieldFormat{labelnumberwidth}{\mkbibbrackets{#1}}
\setlength{\biblabelsep}{1em}

% Global bibliography output policy (keeps .bib content intact):
%   - do not print the note field,
%   - shorten long personal-author lists to "et al.",
%   - keep full author lists for online/misc/report items
%     (typically institutions or contract parties).
\ExecuteBibliographyOptions{maxbibnames=2,minbibnames=1}
\AtEveryBibitem{%
  \clearfield{note}%
  \ifentrytype{online}{\defcounter{maxnames}{99}\defcounter{minnames}{1}}{}%
  \ifentrytype{misc}{\defcounter{maxnames}{99}\defcounter{minnames}{1}}{}%
  \ifentrytype{report}{\defcounter{maxnames}{99}\defcounter{minnames}{1}}{}%
}
\DefineBibliographyStrings{czech}{andothers = {et\addabbrvspace al\adddot}}
\DefineBibliographyStrings{english}{andothers = {et\addabbrvspace al\adddot}}

% ----------------------------------------------------------------------------
% Acro — loaded so that thesis text reused on the poster (with \ac{}, \acs{},
% \acp{}, \acl{}) typesets without errors.  No list is ever printed on the
% poster, so list-related templates and acronym links are deliberately omitted.
% Per-thesis declaration files (acro.tex, acro_variables.tex) must still be
% \input in the poster preamble — same as in main.tex.
% ----------------------------------------------------------------------------
\RequirePackage{acro}
\acsetup{
  make-links   = false,   % no acronym list target exists in the poster
  list/display = used,    % no effect (we never call \printacronyms)
  single       = false,   % expand on first use even if used only once
}
% Project-specific `index` property used by acro_variables.tex in the thesis.
\DeclareAcroProperty{index}

% ----------------------------------------------------------------------------
% Page style — empty (no headers, no footers, no page number on a single page)
% ----------------------------------------------------------------------------
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.6\baselineskip}
\renewcommand{\baselinestretch}{1.05}

% Section headings — large, sans-serif, blue
\RequirePackage[explicit]{titlesec}
\titleformat{\section}
  {\sffamily\bfseries\color{CTUblue}\fontsize{30}{36}\selectfont}
  {}{0pt}{#1}
\titlespacing*{\section}{0pt}{1.2\baselineskip}{0.4\baselineskip}

\titleformat{\subsection}
  {\sffamily\bfseries\color{CTUgrey}\fontsize{22}{26}\selectfont}
  {}{0pt}{#1}
\titlespacing*{\subsection}{0pt}{0.8\baselineskip}{0.3\baselineskip}

% ----------------------------------------------------------------------------
% Localized labels
% ----------------------------------------------------------------------------
\newcommand\CTUP@lbl@abstractCS{Abstrakt}
\newcommand\CTUP@lbl@abstractEN{Abstract}
\newcommand\CTUP@lbl@summary   {Summary}    % default doc=czech → English summary heading
\newcommand\CTUP@lbl@contact   {Kontakt}
\newcommand\CTUP@lbl@year      {Rok}
\newcommand\CTUP@lbl@phone     {Tel.}
\newcommand\CTUP@lbl@repo      {Repozitář}
\newcommand\CTUP@lbl@references{Literatura}
\newcommand\CTUP@lbl@stats@figs{obrázků}
\newcommand\CTUP@lbl@stats@tabs{tabulek}
\newcommand\CTUP@lbl@stats@atts{příloh}
\newcommand\CTUP@lbl@stats@nstr{normostran}
\AtBeginDocument{%
  \ifCTUP@english
    \renewcommand\CTUP@lbl@contact   {Contact}%
    \renewcommand\CTUP@lbl@year      {Year}%
    \renewcommand\CTUP@lbl@phone     {Phone}%
    \renewcommand\CTUP@lbl@repo      {Repository}%
    \renewcommand\CTUP@lbl@references{References}%
    \renewcommand\CTUP@lbl@stats@figs{figures}%
    \renewcommand\CTUP@lbl@stats@tabs{tables}%
    \renewcommand\CTUP@lbl@stats@atts{attachments}%
    \renewcommand\CTUP@lbl@stats@nstr{standard pages}%
    % English main language → \postersummary holds Czech summary, so heading
    % flips to "Shrnutí" automatically.
    \renewcommand\CTUP@lbl@summary   {Shrnutí}%
  \fi
}

% ----------------------------------------------------------------------------
% Metadata commands
%
% Every poster-side command may be omitted; sensible defaults are derived from
% the inherited thesis metadata above (git author/email, normostrana count,
% repository URL/tag).  Author/email default to the values written by
% latexmkrc into build/main-git*.tmp, so no preamble entries are required if
% the poster is built from the same git working tree as the thesis.
% ----------------------------------------------------------------------------
\newcommand{\postertitle}      [1]{\gdef\CTUP@title      {#1}}
\newcommand{\postersubtitle}   [1]{\gdef\CTUP@subtitle   {#1}}
\newcommand{\posterauthor}     [1]{\gdef\CTUP@author     {#1}}
\newcommand{\posteraffiliation}[1]{\gdef\CTUP@affil      {#1}}
\newcommand{\postersupervisor} [1]{\gdef\CTUP@supervisor {#1}}
\newcommand{\posteryear}       [1]{\gdef\CTUP@year       {#1}}
\newcommand{\posteremail}      [1]{\gdef\CTUP@emailx     {#1}}
\newcommand{\posterphone}      [1]{\gdef\CTUP@phone      {#1}}  % optional
\newcommand{\posterrepo}       [1]{\gdef\CTUP@repo       {#1}}  % URL; default = git remote
\newcommand{\posterrepotag}    [1]{\gdef\CTUP@repotag    {#1}}  % git tag (may be created later)
\newcommand{\posterlogo}       [1]{\gdef\CTUP@logo       {#1}}

\gdef\CTUP@title{}\gdef\CTUP@subtitle{}
\gdef\CTUP@affil{}\gdef\CTUP@supervisor{}
\gdef\CTUP@year{\the\year}\gdef\CTUP@logo{}
\gdef\CTUP@phone{}                                  % phone is optional
\gdef\CTUP@author{\@author}                         % default = git user.name
\gdef\CTUP@emailx{\@email}                          % default = git user.email
\gdef\CTUP@repo{\@CTUgitrepo}                       % default = git remote URL
\gdef\CTUP@repotag{\@CTUgittag}                     % default = latest git tag

% \CTU@posterurl: build "<repo>/tree/<ref>" link.
%   Falls back to \@CTUgitsha when no tag is set so the link still resolves.
%   When a future tag is intended, set \posterrepotag{v1.0} in the preamble —
%   the URL will be valid once that tag is pushed (the tag does NOT need to
%   exist at compile time; GitHub/GitLab return 404 only until it does).
\newcommand{\CTU@posterurl}{%
  \ifx\CTUP@repo\@empty\else
    \CTUP@repo
    \ifx\CTUP@repotag\@empty
      \ifx\@CTUgitsha\@empty\else /tree/\@CTUgitsha\fi
    \else
      /tree/\CTUP@repotag
    \fi
  \fi
}

% ----------------------------------------------------------------------------
% Title block — full page width across both columns
% ----------------------------------------------------------------------------
\newcommand{\makepostertitle}{%
  \begingroup
  \noindent
  \begin{minipage}[c]{\linewidth}%
    \centering
    \ifx\CTUP@logo\@empty\else
      {\includegraphics[height=28mm]{\CTUP@logo}\par\vspace{6mm}}%
    \fi
    {\sffamily\bfseries\color{CTUblue}\fontsize{60}{70}\selectfont
      \CTUP@title\par}%
    \ifx\CTUP@subtitle\@empty\else
      \vspace{4mm}%
      {\sffamily\color{CTUgrey}\fontsize{36}{42}\selectfont
        \CTUP@subtitle\par}%
    \fi
    \vspace{8mm}%
    {\sffamily\fontsize{26}{30}\selectfont \CTUP@author\par}%
    \ifx\CTUP@affil\@empty\else
      \vspace{2mm}%
      {\sffamily\color{CTUgrey}\fontsize{20}{24}\selectfont
        \CTUP@affil\par}%
    \fi
  \end{minipage}\par
  \vspace{6mm}%
  {\color{CTUblue}\hrule height 1.2mm}%
  \vspace{10mm}%
  \endgroup
}

% ----------------------------------------------------------------------------
% Two-column body environment
% ----------------------------------------------------------------------------
% Usage:
%   \begin{posterbody} ... \end{posterbody}
% Inside: standard text, \section{...}, figures via \captionof{figure}{...}
%   (use [H] floats sparingly — multicol does not support standard floats).
\newenvironment{posterbody}
  {\begin{multicols*}{2}}
  {\end{multicols*}}

% ----------------------------------------------------------------------------
% Abstract boxes — emphasized, placed at the top of the left column
% ----------------------------------------------------------------------------
\newcommand{\CTUP@abstractbox}[2]{%
  % #1 = label, #2 = body
  \begingroup
  \noindent
  \begin{tcolorbox}[
      enhanced,
      colback     = CTUlight,
      colframe    = CTUblue,
      boxrule     = 0.5mm,
      arc         = 2mm,
      left        = 4mm, right=4mm, top=3mm, bottom=3mm,
      title       = {\sffamily\bfseries #1},
      coltitle    = white,
      colbacktitle= CTUblue,
      fonttitle   = \large\bfseries,
    ]
    \itshape #2%
  \end{tcolorbox}\par\vspace{4mm}%
  \endgroup
}
\RequirePackage[most]{tcolorbox}

\newcommand{\abstractCS}[1]{\CTUP@abstractbox{\CTUP@lbl@abstractCS}{#1}}
\newcommand{\abstractEN}[1]{\CTUP@abstractbox{\CTUP@lbl@abstractEN}{#1}}

% ----------------------------------------------------------------------------
% English summary at the end of the body
% ----------------------------------------------------------------------------
\newcommand{\postersummary}[1]{%
  \par\vspace{6mm}%
  {\color{CTUblue}\hrule height 0.4mm}\vspace{4mm}%
  {\sffamily\bfseries\color{CTUblue}\large \CTUP@lbl@summary\par}%
  \vspace{2mm}%
  \begingroup\small #1\par\endgroup
}

% ----------------------------------------------------------------------------
% Contact block — hline, sans-serif, smaller; typically last item in column.
% Phone number is OPTIONAL — the line is suppressed when \posterphone{} is
% empty.  Repository URL is auto-derived from `git remote get-url origin`
% (written by latexmkrc) and points to the tag set by \posterrepotag{}.
% The tag does NOT need to exist at compile time; the URL becomes valid as
% soon as the tag is pushed to the remote.
% ----------------------------------------------------------------------------
\newcommand{\postercontactblock}{%
  % Keep contact details at the bottom of the current column.
  \par\vspace*{\fill}%
  \par\vspace{4mm}%
  {\color{CTUgrey}\hrule height 0.3mm}\vspace{3mm}%
  \begingroup
  \sffamily\small
  \textbf{\CTUP@lbl@contact:}\\
  \CTUP@author
  \ifx\CTUP@emailx\@empty\else
    \space\textbar\space \href{mailto:\CTUP@emailx}{\CTUP@emailx}%
  \fi
  \ifx\CTUP@phone\@empty\else
    \space\textbar\space \CTUP@lbl@phone~\CTUP@phone
  \fi
  \par
  \ifx\CTUP@supervisor\@empty\else
    \medskip\textit{\CTUP@supervisor}\par
  \fi
  \edef\CTUP@tmpurl{\CTU@posterurl}%
  \ifx\CTUP@tmpurl\@empty\else
    \medskip
    \textbf{\CTUP@lbl@repo:}\\
    \href{\CTUP@tmpurl}{\nolinkurl{\CTUP@tmpurl}}\par
  \fi
  \ifx\CTUP@year\@empty\else
    \medskip\textbf{\CTUP@lbl@year:}~\CTUP@year\par
  \fi
  \endgroup
}

% ----------------------------------------------------------------------------
% \posterthesisstats — inline summary of thesis-wide counters inherited from
% the latexmkrc tmp files.  Items with a zero count are omitted automatically
% so partial data still prints cleanly.
%   Output:  62 normostran · 18 obrázků · 7 tabulek · 3 přílohy
% ----------------------------------------------------------------------------
\newif\ifCTUP@firststat
\newcommand{\CTUP@statitem}[2]{%
  % #1 = number  #2 = label.  Print "N label" only when N > 0.
  \ifnum#1>0
    \ifCTUP@firststat\else\space\textbullet\space\fi
    \CTUP@firststatfalse
    #1~#2%
  \fi
}
\newcommand{\posterthesisstats}{%
  \CTUP@firststattrue
  \begingroup\sffamily\small\color{CTUgrey}
    \ifx\@normostrana\@empty\else
      \CTUP@firststatfalse \@normostrana~\CTUP@lbl@stats@nstr
    \fi
    \CTUP@statitem{\@CTUnfigures}    {\CTUP@lbl@stats@figs}%
    \CTUP@statitem{\@CTUntables}     {\CTUP@lbl@stats@tabs}%
    \CTUP@statitem{\@CTUnattachments}{\CTUP@lbl@stats@atts}%
  \par\endgroup
}

% ----------------------------------------------------------------------------
% \posterbibliography[opts] — optional References section for the poster.
%   Renders \printbibliography in a smaller font with tighter spacing so it
%   fits in a single column.  Section heading uses the localized label
%   (Reference / References) and the same styling as \section.
%   Entry numbers appear as "[1]", "[2]", … (set globally above via
%   \DeclareFieldFormat{labelnumberwidth}).  In-text \cite{} already use
%   bracketed numerals from iso-numeric.
%   The optional argument is forwarded to \printbibliography so callers can
%   pass `keyword=poster`, `nottype=online`, etc.
% ----------------------------------------------------------------------------
\newcommand{\posterbibliography}[1][]{%
  \par\vspace{4mm}%
  \begingroup
  % Heading — same look as \section but no \section{} so no TOC entry attempt.
  {\sffamily\bfseries\color{CTUblue}\fontsize{30}{36}\selectfont
    \CTUP@lbl@references\par}%
  \vspace{1mm}%
  \renewcommand*{\bibfont}{\scriptsize}%
  \setlength{\bibitemsep}{0.15\baselineskip}%
  \setlength{\bibhang}{1.2em}%
  % Allow generous inter-word spacing so long URLs and author names break
  % at the column boundary without producing overfull hboxes:
  \emergencystretch=2em
  \sloppy
  \selectlanguage{\CTUP@biblang}%
  \printbibliography[heading=none,#1]%
  \endgroup
}

% Override the default bibliography language (czech / english).  Place in the
% preamble before \posterbibliography to force a different label set than the
% one implied by the main class option.
\newcommand{\posterbibliolang}[1]{\def\CTUP@biblang{#1}}

% Print all bibliography entries (not only cited ones).
% Useful for posters with short text where citations may be sparse.
\newcommand{\posterbibliographyall}[1][]{%
  \nocite{*}%
  \posterbibliography[#1]%
}

% ----------------------------------------------------------------------------
% Convenience — \inputpgffigure mirrors the thesis macro so PGF/matplotlib
% figures dropped into texparts/figures/<name>.tex render identically.
% ----------------------------------------------------------------------------
\newcommand{\inputpgffigure}[1]{%
  \IfFileExists{../python/figures/#1.pgf}{%
    \input{texparts/figures/#1}%
  }{%
    \begin{center}
      \fboxsep=8pt
      \colorbox{yellow!40}{%
        \parbox{0.9\linewidth}{\color{red!70!black}\bfseries
          \texttt{[#1.pgf]} chybí --- spusťte odpovídající Python skript.}%
      }%
    \end{center}%
  }%
}

\endinput
