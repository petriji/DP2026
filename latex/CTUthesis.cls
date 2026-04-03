%%
%% CTUthesis.cls — Custom LaTeX class for CTU (Prague) theses.
%%
%% Based on report.cls (classes.dtx, LaTeX2e standard distribution).
%% Extended with full package setup, page styles, custom macros, and
%% table/figure formatting for a pdflatex + biber workflow.
%%
%% Jiří Petříček 2019–2026
%% Refactored with Claude Sonnet 4.6, April 2026
%%
% ==============================================================================
% Class Declaration, Options, And Setup
% ==============================================================================
\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{CTUthesis}
              [2026/04/03]
%
% Usage reference — \documentclass[<options>]{CTUthesis}
%
%   Paper size     : a4paper (default)    a5paper
%   Font size      : 12pt (default)       10pt              11pt
%   Binding        : oneside (default)    twoside
%   Columns        : onecolumn (default)  twocolumn
%   Mode           : final (default)      draft             — cover text and date format
%                    final → "DIPLOMOVÁ PRÁCE", year only
%                    draft → "REŠERŠE K DIPLOMOVÉ PRÁCI", full date
%                    \course{} in preamble overrides cover text in either mode
%   Debug          : debug                                  — overfull marks + colored link boxes
%   Page order     : openany (default)    openright
%   Cover page     : titlepage (default)  notitlepage       — suppresses \maketitle entirely
%   Header         : header (default)     noheader          — author/chapter running head + rule
%   Front matter   : frontmatter (def.)   nofrontmatter     — abstract, declarations, assignment
%   Acronym lists  : acro (default)       noacro            — acronym and variable lists
%   Bibliography   : bibliography (def.)  nobibliography
%   Software list  : software (default)   nosoftware
%   Back matter    : backmatter (default)  nobackmatter     — LOF, LOT, appendices
%   Author email   : email (default)      noemail           — mailto link on author name on cover (always);
%                                                            email address printed below name on cover (draft only);
%                                                            mailto link in running header (if not disabled by noheader)
%   TikZ caching   : tikzextern                             — externalize TikZ figures (faster rebuilds)
%                    OFF by default; requires -shell-escape in the pdflatex recipe when active
%   Math layout    : leqno                fleqn             — left eq. numbers; flush-left display
%                    default: right-side eq. numbers, centered display equations
%
% Default: \documentclass[a4paper,12pt,oneside,onecolumn,final,openany]{CTUthesis}
%

% \@ptsize: set to 0/1/2 by the 10pt/11pt/12pt option; selects size1X.clo below.
\newcommand\@ptsize{}
% \if@restonecol: scratch flag for temporarily switching twocolumn → onecolumn.
\newif\if@restonecol
\newif\if@openright
% \if@titlepage: controls \maketitle; true by default so omitting the option
%   produces the CTU cover page as before.
\newif\if@titlepage
\@titlepagetrue
% \if@draftmode: true when draft option is given — controls cover text and date.
\newif\if@draftmode
% \if@debug: true when debug option is given — marks overfull boxes and shows
%   hyperlink targets as colored boxes (via hyperref without hidelinks).
\newif\if@debug
% Section visibility flags — all true by default; set to false via their no* option.
%   Prefixed CTU to avoid collisions: \ifCTUheader, \ifCTUfrontmatter, etc.
\newif\ifCTUheader      \CTUheadertrue
\newif\ifCTUfrontmatter \CTUfrontmattertrue
\newif\ifCTUacro        \CTUacrotrue
\newif\ifCTUbiblio      \CTUbibliotrue
\newif\ifCTUsoftware    \CTUsoftwaretrue
\newif\ifCTUbackmatter  \CTUbackmattertrue
\newif\ifCTUemail       \CTUemailtrue
% \ifCTUtikzextern: false by default; set true via tikzextern option.
%   When true, loads the external library and calls \tikzexternalize.
%   Requires the -shell-escape compiler flag — add it to the pdflatex
%   tool args in .vscode/settings.json when this option is active.
\newif\ifCTUtikzextern
% × "\if@compatibility" guards from report.cls have been removed: this class
%   requires LaTeX2e (see \NeedsTeXFormat above), so the 2.09 compat branches
%   were always dead code.
\DeclareOption{a4paper}
   {\setlength\paperheight {297mm}%
    \setlength\paperwidth  {210mm}}
\DeclareOption{a5paper}
   {\setlength\paperheight {210mm}%
    \setlength\paperwidth  {148mm}}
\DeclareOption{10pt}{\renewcommand\@ptsize{0}}
\DeclareOption{11pt}{\renewcommand\@ptsize{1}}
\DeclareOption{12pt}{\renewcommand\@ptsize{2}}
\DeclareOption{oneside}{\@twosidefalse \@mparswitchfalse}
\DeclareOption{twoside}{\@twosidetrue  \@mparswitchtrue}
% titlepage: \maketitle produces the CTU cover page (default).
% notitlepage: \maketitle is suppressed — use when the cover is supplied
%   externally (e.g. via \includepdf of the official assignment sheet).
\DeclareOption{titlepage}{\@titlepagetrue}
\DeclareOption{notitlepage}{\@titlepagefalse}
% draft: cover page shows "REŠERŠE K DIPLOMOVÉ PRÁCI" + full date.
%   Overfull marks and link visibility are NOT changed — use debug for those.
\DeclareOption{draft}{\@draftmodetrue}
% final: cover page shows "DIPLOMOVÁ PRÁCE" + year-only date (default).
\DeclareOption{final}{\@draftmodefalse}
% debug: visual debugging aids — black rule on overfull lines + colored
%   hyperlink boxes (hyperref loaded WITHOUT hidelinks).
\DeclareOption{debug}{\@debugtrue\setlength\overfullrule{5pt}}
\DeclareOption{openright}{\@openrighttrue}
\DeclareOption{openany}{\@openrightfalse}
\DeclareOption{onecolumn}{\@twocolumnfalse}
\DeclareOption{twocolumn}{\@twocolumntrue}
\DeclareOption{leqno}{\input{leqno.clo}}
\DeclareOption{fleqn}{\input{fleqn.clo}}
% header/noheader: show or suppress running page headers (headrule + author/chapter line).
\DeclareOption{header}{\CTUheadertrue}
\DeclareOption{noheader}{\CTUheaderfalse}
% frontmatter/nofrontmatter: include or suppress front matter
%   (ethical declaration, thank-you note, thesis assignment form, abstract).
\DeclareOption{frontmatter}{\CTUfrontmattertrue}
\DeclareOption{nofrontmatter}{\CTUfrontmatterfalse}
% acro/noacro: print or suppress the acronym and variable lists.
\DeclareOption{acro}{\CTUacrotrue}
\DeclareOption{noacro}{\CTUacrofalse}
% bibliography/nobibliography: print or suppress the bibliography.
\DeclareOption{bibliography}{\CTUbibliotrue}
\DeclareOption{nobibliography}{\CTUbibliofalse}
% software/nosoftware: print or suppress the list of software.
\DeclareOption{software}{\CTUsoftwaretrue}
\DeclareOption{nosoftware}{\CTUsoftwarefalse}
% backmatter/nobackmatter: print or suppress back matter except bibliography
%   (list of figures, list of tables, appendices).
\DeclareOption{backmatter}{\CTUbackmattertrue}
\DeclareOption{nobackmatter}{\CTUbackmatterfalse}
% email/noemail: add a mailto: hyperlink to the author name in running headers;
%   also display the email below the author table on the cover page (draft only).
\DeclareOption{email}{\CTUemailtrue}
\DeclareOption{noemail}{\CTUemailfalse}
% tikzextern: enable TikZ figure externalization (caches compiled figures as
%   PDFs in build/). Speeds up repeated builds when figures are unchanged.
%   Requires -shell-escape in the pdflatex recipe — see .vscode/settings.json.
\DeclareOption{tikzextern}{\CTUtikzexterntrue}
% (openbib option purged: referenced \@openbib@code and \newblock which were
%  removed with thebibliography; biblatex is used instead.)
% letterpaper is overridden by the a4paper DeclareOption above.
% 12pt → \@ptsize=2; oneside → no mirrored even/odd margins.
\ExecuteOptions{a4paper,12pt,oneside,onecolumn,final,openany}
\ProcessOptions
% size10.clo / size11.clo / size12.clo: defines \normalsize, \small, \large,
%   \footnotesize etc. for the selected base point size.
\input{size1\@ptsize.clo}
% ==============================================================================
% Layout Primitives
% ==============================================================================
\setlength\lineskip{1\p@}
\setlength\normallineskip{1\p@}
\renewcommand\baselinestretch{1.5}
\setlength\parskip{0\p@ \@plus \p@}
% Break-penalty thresholds used at list boundaries and by sectioning commands.
%   Lower value = break less strongly discouraged (51 < 151 < 301).
\@lowpenalty   51
\@medpenalty  151
\@highpenalty 301
% Float placement fractions — TeX respects these before falling back to a
%   dedicated float page.  dbltop*/dblfloatpage* variants apply in twocolumn mode.
\setcounter{topnumber}{2}
\renewcommand\topfraction{.7}
\setcounter{bottomnumber}{1}
\renewcommand\bottomfraction{.3}
\setcounter{totalnumber}{3}
\renewcommand\textfraction{.2}
\renewcommand\floatpagefraction{.5}
\setcounter{dbltopnumber}{2}
\renewcommand\dbltopfraction{.7}
\renewcommand\dblfloatpagefraction{.5}
% (\ps@headings and \ps@myheadings purged: titlesec [pagestyles] defines all
%  active page styles; \pagestyle{headings} is never used in this document.)
% ==============================================================================
% Thesis Metadata Commands
% ==============================================================================
% \faculty, \department, \course: user-level setters that store their argument
%   globally via \gdef so the value survives group boundaries.  Used in
%   \maketitle and the page styles (fancy/plain/nonum) via \@faculty etc.
\def\@faculty{\relax}
	\newcommand{\faculty}[1]{\gdef\@faculty{#1}
	}
\def\@department{\relax}
	\newcommand{\department}[1]{\gdef\@department{#1}
	}
% \@course: default set by draft/final mode; overridable via \course{} in preamble.
%   Accent commands used because inputenc is loaded later in this class file.
\if@draftmode
  \def\@course{RE\v{S}ER\v{S}E K~DIPLOMOV\'{E} PR\'{A}CI}
\else
  \def\@course{DIPLOMOV\'{A} PR\'{A}CE}
\fi
	\newcommand{\course}[1]{\gdef\@course{#1}
	}
% \@author / \@email: placeholder defaults; overwritten at load time when
%   latexmkrc has pre-generated main-gitauthor.tmp / main-gitemail.tmp from
%   git config (see latexmkrc).  Override in preamble with \author{} / \email{}.
\gdef\@author{Name Surname}
% \@email: contact address; used in the page header mailto: link and below the
%   author table on the cover page when CTUemail is active.
\gdef\@email{address@e-mail.xy}
	\newcommand{\email}[1]{\gdef\@email{#1}
	}
% Snapshot metadata into shorthand macros used by page styles and headers.
%   \AtBeginDocument ensures any \author{}, \email{}, \title{}, \course{}
%   override in the preamble has already executed before the snapshot is taken.
%   These macros (\Author, \Email, \Title, \Course) do NOT need to be set
%   manually in main.tex — they are maintained entirely by the class.
\AtBeginDocument{%
  \let\Author\@author
  \let\Email\@email
  \let\Title\@title
  \let\Course\@course
}
% ==============================================================================
% Title Page
% ==============================================================================
% Bespoke CTU cover page: logo, faculty/dept/course header, and an
% xltabular two-column author table.  Clears \author/\title after use.
\newcommand\maketitle{%
  \if@titlepage
  \begin{titlepage}%
\thispagestyle{empty}

  \begin{flushright}
	{\large
	\v{C}esk\'{e} vysok\'{e} u\v{c}en\'{i} technick\'{e} v~Praze
	\vskip 0.1cm
 	\@faculty
 	\vskip 0.1cm
 	\@department \par}
  \end{flushright}\par
  \vfill
 % \vskip 60\p@
  \begin{center}
    \includegraphics[scale=1]{ctu_logo_black.pdf} 
    \vskip 0.7cm
    {\LARGE \sffamily \@course \par}%
    \vskip 0.8cm
    {\Large \sffamily \@title \par}%
    \vfill
    \begin{minipage}[b]{\textwidth}
    {\large
      \begin{xltabular}{\linewidth}{>{\centering\arraybackslash}X >{\centering\arraybackslash}X}%
        \ifCTUemail\ifx\@email\@empty\@author\else\href{mailto:\@email}{\@author}\fi\else\@author\fi
      \end{xltabular}\par}%
     \end{minipage}
  % Email address on cover: printed below author table in draft mode only.
  \ifCTUemail\ifx\@email\@empty\else
    \if@draftmode
    \vskip 0.3cm
    {\small\href{mailto:\@email}{\texttt{\@email}}\par}%
    \fi
  \fi\fi
%      \vskip 0.8cm%
  \vfill
  {\normalsize \if@draftmode\@date\else\number\year\fi \par}%
  \end{center}\par
%  \@thanks
  \end{titlepage}%
  \setcounter{footnote}{0}%
  \global\let\thanks\relax
  \global\let\maketitle\relax
  \global\let\@thanks\@empty
  \global\let\@author\@empty
  \global\let\@date\@empty
  \global\let\@title\@empty
  \global\let\title\relax
  \global\let\author\relax
  \global\let\date\relax
  \global\let\and\relax
  \fi
}
% ==============================================================================
% Document Structure, Counters, And Sectioning
% ==============================================================================
\newcommand*\chaptermark[1]{}
\setcounter{secnumdepth}{2}
\newcounter {part}
\newcounter {chapter}
\newcounter {section}[chapter]
\newcounter {subsection}[section]
\newcounter {subsubsection}[subsection]
\newcounter {paragraph}[subsubsection]
\newcounter {subparagraph}[paragraph]
\renewcommand \thepart {\@Roman\c@part}
\renewcommand \thechapter {\@arabic\c@chapter}
\renewcommand \thesection {\thechapter.\@arabic\c@section}
\renewcommand\thesubsection   {\thesection.\@arabic\c@subsection}
\renewcommand\thesubsubsection{\thesubsection.\@arabic\c@subsubsection}
\renewcommand\theparagraph    {\thesubsubsection.\@arabic\c@paragraph}
\renewcommand\thesubparagraph {\theparagraph.\@arabic\c@subparagraph}
\newcommand\@chapapp{\chaptername}
% (\part body purged: titlesec's \titleclass{\part}{page} completely replaces
%  \part via \ttl@pageclass at load time; only the empty stub is needed.)
\newcommand\part{}
% \chapter: titlesec uses a COMPATIBILITY mechanism for chapter-level sections.
%   It does NOT replace \chapter; instead, \ttl@compatchapter patches
%   \@makechapterhead and \@makeschapterhead.  The dispatch chain must remain:
%     \chapter{T} → \secdef\@chapter\@schapter
%               → \@chapter → \@makechapterhead (patched by titlesec)
%   Without this, \chapter* (used in \tableofcontents etc.) is also broken.
\newcommand\chapter{\if@openright\cleardoublepage\else\clearpage\fi
                    \thispagestyle{plain}%
                    \global\@topnum\z@
                    \@afterindentfalse
                    \secdef\@chapter\@schapter}
% \@chapter: increments counter, writes TOC/LOF/LOT entries, calls
%   \@makechapterhead (which titlesec replaces via \ttl@compatchapter).
\def\@chapter[#1]#2{\ifnum \c@secnumdepth >\m@ne
                         \refstepcounter{chapter}%
                         \typeout{\@chapapp\space\thechapter.}%
                         \addcontentsline{toc}{chapter}%
                                   {\protect\numberline{\thechapter}#1}%
                    \else
                      \addcontentsline{toc}{chapter}{#1}%
                    \fi
                    \chaptermark{#1}%
                    \addtocontents{lof}{\protect\addvspace{10\p@}}%
                    \addtocontents{lot}{\protect\addvspace{10\p@}}%
                    \if@twocolumn
                      \@topnewpage[\@makechapterhead{#2}]%
                    \else
                      \@makechapterhead{#2}%
                      \@afterheading
                    \fi}
% \@schapter: starred form — no TOC entry; calls \@makeschapterhead
%   (also patched by titlesec).
\def\@schapter#1{\if@twocolumn
                   \@topnewpage[\@makeschapterhead{#1}]%
                 \else
                   \@makeschapterhead{#1}%
                   \@afterheading
                 \fi}
% (\@makechapterhead and \@makeschapterhead NOT defined here: titlesec's
%  \ttl@compatchapter creates them when \titleformat{\chapter} is processed.)
\newcommand\section{\@startsection {section}{1}{\z@}%
                                   {-3.5ex \@plus -1ex \@minus -.2ex}%
                                   {2.3ex \@plus.2ex}%
                                   {\normalfont\Large\bfseries}}
\newcommand\subsection{\@startsection{subsection}{2}{\z@}%
                                     {-3.25ex\@plus -1ex \@minus -.2ex}%
                                     {1.5ex \@plus .2ex}%
                                     {\normalfont\large\bfseries}}
\newcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}%
                                     {-3.25ex\@plus -1ex \@minus -.2ex}%
                                     {1.5ex \@plus .2ex}%
                                     {\normalfont\normalsize\bfseries}}
\newcommand\paragraph{\@startsection{paragraph}{4}{\z@}%
                                    {3.25ex \@plus1ex \@minus.2ex}%
                                    {-1em}%
                                    {\normalfont\normalsize\bfseries}}
\newcommand\subparagraph{\@startsection{subparagraph}{5}{\parindent}%
                                       {3.25ex \@plus1ex \@minus .2ex}%
                                       {-1em}%
                                      {\normalfont\normalsize\bfseries}}
% \appendix: resets chapter/section counters and switches \thechapter to
%   uppercase alpha (A, B, C …). \@chapapp becomes "Appendix" (or the
%   babel equivalent) so chapter headings and TOC entries read "Appendix A".
\newcommand\appendix{\par
  \setcounter{chapter}{0}%
  \setcounter{section}{0}%
  \gdef\@chapapp{\appendixname}%
  \gdef\thechapter{\@Alph\c@chapter}}
% ==============================================================================
% List Layout
% ==============================================================================
\if@twocolumn
  \setlength\leftmargini  {2em}
\else
  \setlength\leftmargini  {2.5em}
\fi
\leftmargin  \leftmargini
\setlength\leftmarginii  {2.2em}
\setlength\leftmarginiii {1.87em}
\setlength\leftmarginiv  {1.7em}
\if@twocolumn
  \setlength\leftmarginv  {.5em}
  \setlength\leftmarginvi {.5em}
\else
  \setlength\leftmarginv  {1em}
  \setlength\leftmarginvi {1em}
\fi
\setlength  \labelsep  {.5em}
\setlength  \labelwidth{\leftmargini}
\addtolength\labelwidth{-\labelsep}
\@beginparpenalty -\@lowpenalty
\@endparpenalty   -\@lowpenalty
\@itempenalty     -\@lowpenalty
% enumerate counter representation: arabic, alpha, roman, ALPHA (levels 1–4).
\renewcommand\theenumi{\@arabic\c@enumi}
\renewcommand\theenumii{\@alph\c@enumii}
\renewcommand\theenumiii{\@roman\c@enumiii}
\renewcommand\theenumiv{\@Alph\c@enumiv}
% enumerate label format per nesting level: 1.  (a)  i.  A.
\newcommand\labelenumi{\theenumi.}
\newcommand\labelenumii{(\theenumii)}
\newcommand\labelenumiii{\theenumiii.}
\newcommand\labelenumiv{\theenumiv.}
% reference prefix: \ref inside enumerate prepends parent labels.
\renewcommand\p@enumii{\theenumi}
\renewcommand\p@enumiii{\theenumi(\theenumii)}
\renewcommand\p@enumiv{\p@enumiii\theenumiii}
% itemize label symbols: •  –  *  ·  (levels 1–4).
\newcommand\labelitemi{\textbullet}
\newcommand\labelitemii{\normalfont\bfseries \textendash}
\newcommand\labelitemiii{\textasteriskcentered}
\newcommand\labelitemiv{\textperiodcentered}
\newenvironment{description}
               {\list{}{\labelwidth\z@ \itemindent-\leftmargin
                        \let\makelabel\descriptionlabel}}
               {\endlist}
\newcommand*\descriptionlabel[1]{\hspace\labelsep
                                \normalfont\bfseries #1}
% ==============================================================================
% Standard Text Environments
% ==============================================================================
\newenvironment{abstract}{%
    \titlepage
    \null\vfil
    \@beginparpenalty\@lowpenalty
    \begin{center}%
      \bfseries \abstractname
      \@endparpenalty\@M
    \end{center}}%
   {\par\vfil\null\endtitlepage}
% (verse, quotation, quote purged: unused in all CTUthesis projects.)
% LaTeX2e titlepage: page counter starts at 1; twoside restores it after.
\newenvironment{titlepage}
    {%
      \if@twocolumn
        \@restonecoltrue\onecolumn
      \else
        \@restonecolfalse\newpage
      \fi
      \thispagestyle{empty}%
      \setcounter{page}\@ne
    }%
    {\if@restonecol\twocolumn \else \newpage \fi
     \if@twoside\else
        \setcounter{page}\@ne
     \fi
    }
% ==============================================================================
% Primitive Spacing And Box Parameters
% ==============================================================================
\setlength\arraycolsep{5\p@}
\setlength\tabcolsep{6\p@}
\setlength\arrayrulewidth{.4\p@}
\setlength\doublerulesep{2\p@}
\setlength\tabbingsep{\labelsep}
\skip\@mpfootins = \skip\footins  % sync minipage footnote gap with body text
\setlength\fboxsep{3\p@}
\setlength\fboxrule{.4\p@}
% ==============================================================================
% Floats, Captions, And Equation Counter
% ==============================================================================
\@addtoreset {equation}{chapter}
\renewcommand\theequation
  {\ifnum \c@chapter>\z@ \thechapter.\fi \@arabic\c@equation}
\newcounter{figure}[chapter]
\renewcommand \thefigure
     {\ifnum \c@chapter>\z@ \thechapter.\fi \@arabic\c@figure}
% Float hook registers for the figure environment:
%   \fps@figure  — default placement specifiers (top / bottom / float-page).
%   \ftype@figure — type bit-mask: figures=1, tables=2 (controls \suppressfloats).
%   \ext@figure  — auxiliary file extension for the list of figures (.lof).
%   \fnum@figure — caption label string, e.g. "Figure\nobreakspace 1.3".
\def\fps@figure{tbp}
\def\ftype@figure{1}
\def\ext@figure{lof}
\def\fnum@figure{\figurename\nobreakspace\thefigure}
\newenvironment{figure}
               {\@float{figure}}
               {\end@float}
\newenvironment{figure*}
               {\@dblfloat{figure}}
               {\end@dblfloat}
\newcounter{table}[chapter]
\renewcommand \thetable
     {\ifnum \c@chapter>\z@ \thechapter.\fi \@arabic\c@table}
\def\fps@table{tbp}
\def\ftype@table{2}
\def\ext@table{lot}
\def\fnum@table{\tablename\nobreakspace\thetable}
\newenvironment{table}
               {\@float{table}}
               {\end@float}
\newenvironment{table*}
               {\@dblfloat{table}}
               {\end@dblfloat}
\newlength\abovecaptionskip
\newlength\belowcaptionskip
\setlength\abovecaptionskip{10\p@}
\setlength\belowcaptionskip{0\p@}
% abovecaptionskip / belowcaptionskip: consumed by the caption package.
% \@makecaption (purged): the caption package always replaces this renderer
%   entirely, so the class body definition was dead code.
% ==============================================================================
% Contents, Figures, And Tables Lists (TOC, LOF, LOT)
% ==============================================================================
\newcommand\@pnumwidth{1.55em}
\newcommand\@tocrmarg{2.55em}
\newcommand\@dotsep{4.5}
\setcounter{tocdepth}{2}
\newcommand\tableofcontents{%
    \if@twocolumn
      \@restonecoltrue\onecolumn
    \else
      \@restonecolfalse
    \fi
    \chapter*{\contentsname
        \@mkboth{%
           \MakeUppercase\contentsname}{\MakeUppercase\contentsname}}%
    \@starttoc{toc}%
    \if@restonecol\twocolumn\fi
    }
\newcommand*\l@part[2]{%
  \ifnum \c@tocdepth >-2\relax
    \addpenalty{-\@highpenalty}%
    \addvspace{2.25em \@plus\p@}%
    \setlength\@tempdima{3em}%
    \begingroup
      \parindent \z@ \rightskip \@pnumwidth
      \parfillskip -\@pnumwidth
      {\leavevmode
       \large \bfseries #1\hfil \hb@xt@\@pnumwidth{\hss #2}}\par
       \nobreak
         \global\@nobreaktrue
         \everypar{\global\@nobreakfalse\everypar{}}%
    \endgroup
  \fi}
\newcommand*\l@chapter[2]{%
  \ifnum \c@tocdepth >\m@ne
    \addpenalty{-\@highpenalty}%
    \vskip 1.0em \@plus\p@
    \setlength\@tempdima{1.5em}%
    \begingroup
      \parindent \z@ \rightskip \@pnumwidth
      \parfillskip -\@pnumwidth
      \leavevmode \bfseries
      \advance\leftskip\@tempdima
      \hskip -\leftskip
      #1\nobreak\hfil \nobreak\hb@xt@\@pnumwidth{\hss #2}\par
      \penalty\@highpenalty
    \endgroup
  \fi}
% \@dottedtocline{level}{indent}{numwidth}: TOC entry with a dotted leader.
%   indent = left offset from the page margin; numwidth = width for the label.
\newcommand*\l@section{\@dottedtocline{1}{1.5em}{2.3em}}
\newcommand*\l@subsection{\@dottedtocline{2}{3.8em}{3.2em}}
\newcommand*\l@subsubsection{\@dottedtocline{3}{7.0em}{4.1em}}
\newcommand*\l@paragraph{\@dottedtocline{4}{10em}{5em}}
\newcommand*\l@subparagraph{\@dottedtocline{5}{12em}{6em}}
\newcommand\listoffigures{%
    \if@twocolumn
      \@restonecoltrue\onecolumn
    \else
      \@restonecolfalse
    \fi
    \chapter*{\listfigurename}%
      \@mkboth{\MakeUppercase\listfigurename}%
              {\MakeUppercase\listfigurename}%
    \@starttoc{lof}%
    \if@restonecol\twocolumn\fi
    }
\newcommand*\l@figure{\@dottedtocline{1}{1.5em}{2.3em}}
\newcommand\listoftables{%
    \if@twocolumn
      \@restonecoltrue\onecolumn
    \else
      \@restonecolfalse
    \fi
    \chapter*{\listtablename}%
      \@mkboth{%
          \MakeUppercase\listtablename}%
         {\MakeUppercase\listtablename}%
    \@starttoc{lot}%
    \if@restonecol\twocolumn\fi
    }
\let\l@table\l@figure
% ==============================================================================
% Footnote Layout
% ==============================================================================
% (thebibliography, bibindent, \newblock, \@openbib@code purged: biblatex
%  replaces the bibliography output entirely.)
% (theindex, \@idxitem, \subitem, \subsubitem, \indexspace purged: makeidx
%  redefines theindex when loaded; these helpers are only used inside it.)
\renewcommand\footnoterule{%
  \kern-3\p@
  \hrule\@width.4\columnwidth
  \kern2.6\p@}
\@addtoreset{footnote}{chapter}
\newcommand\@makefntext[1]{%
    \parindent 1em%
    \noindent
    \hb@xt@1.8em{\hss\@makefnmark}#1}
% ==============================================================================
% String Names And Date
% ==============================================================================
% English defaults; babel overrides these with Czech equivalents (Obsah,
%   Seznam obrázků, …) when \selectlanguage{czech} is active.
\newcommand\contentsname{Contents}
\newcommand\listfigurename{List of Figures}
\newcommand\listtablename{List of Tables}
\newcommand\bibname{Bibliography}
\newcommand\indexname{Index}
\newcommand\figurename{Figure}
\newcommand\tablename{Table}
\newcommand\partname{Part}
\newcommand\chaptername{Chapter}
\newcommand\appendixname{Appendix}
\newcommand\abstractname{Abstract}
\def\today{\ifcase\month\or
  January\or February\or March\or April\or May\or June\or
  July\or August\or September\or October\or November\or December\fi
  \space\number\day, \number\year}
% ==============================================================================
% Final Layout Switches
% ==============================================================================
\setlength\columnsep{10\p@}
\setlength\columnseprule{0\p@}
\pagestyle{plain}
\pagenumbering{arabic}
% Vertical page filling: oneside → \raggedbottom (short pages not padded);
%   twoside gets \flushbottom by default.  twocolumn forces \flushbottom
%   so that both columns bottom-align on every page.
\if@twoside
\else
  \raggedbottom
\fi
\if@twocolumn
  \twocolumn
  \sloppy        % redundant: overridden by the unconditional \sloppy in Page Layout
  \flushbottom
\else
  \onecolumn
\fi
% ==============================================================================
% Packages: Encoding, Language, And Base Fonts
% ==============================================================================
% Czech/English hyphenation patterns and automatic captions driven by the
%   active document language.
\RequirePackage[english,czech]{babel}
% 8-bit font encoding — enables correct rendering of Czech accented characters
%   and proper PDF copy/paste behavior.
\RequirePackage[T1]{fontenc}
% UTF-8 encoded source files (á, č, ř etc.).
\RequirePackage[utf8]{inputenc}
% Latin Modern scalable fonts — required with T1 for sharp vector glyphs.
\RequirePackage{lmodern}
% Read git metadata files now that inputenc is active so UTF-8 names decode
%   correctly.  Files are written by latexmkrc / git-metadata.pl before
%   compilation starts and are kept in the build/ output directory.
%   Absent files are silently ignored (placeholder defaults remain in effect).
%   User's \author{}/\email{} in the preamble execute after the class and
%   override whatever was read here.
\InputIfFileExists{build/\jobname-gitauthor.tmp}{}{}%
\InputIfFileExists{build/\jobname-gitemail.tmp}{}{}%
% Note: \baselinestretch{1.5} is already set in the class body above.

% ==============================================================================
% Packages: Page Layout And Typography
% ==============================================================================
% Page margins — 3.5 cm left (binding side), 2.5 cm on other sides.
\RequirePackage[left=3.5cm, right=2.5cm, top=2.5cm, bottom=2.5cm]{geometry}
% Microtypography — character protrusion and font expansion. Reduces overfull
%   hboxes without manual hyphenation. The "Unable to apply patch 'item'"
%   warning is a known benign quirk of this package version.
\RequirePackage{microtype}
% Loose line-breaking: slightly wider word spacing to prevent overflow lines.
%\hyphenpenalty=10000  % alternative: disable automatic hyphenation entirely
\sloppy
% Keep footnotes at the physical page bottom on short pages.
\RequirePackage[bottom]{footmisc}
%\raggedbottom

% ==============================================================================
% Packages: Headings And TOC Entry Spacing
% ==============================================================================
% titlesec[pagestyles]: chapter/part title layout AND \newpagestyle commands
%   for the header/footer styles defined in the Page Styles section below.
%   fancyhdr is the legacy alternative — not loaded.
%\RequirePackage{fancyhdr}
\RequirePackage[pagestyles]{titlesec}
\titleformat{\part}[display]
	{\normalfont\Huge\bfseries\filcenter}{}{0pt}{\MakeUppercase}[]
\titlespacing*{\part}{0pt}{\fill}{\fill}
\titleformat{\chapter}
	{\normalfont\LARGE\bfseries}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{3.5ex plus 1ex minus .2ex}{2.3ex plus .2ex}
% tocloft[titles]: TOC/LOF/LOT layout — reduces vertical gap before chapters.
\RequirePackage[titles]{tocloft}
\setlength{\cftbeforechapskip}{5pt}
% Align LOF and LOT entries with the chapter-level left margin.
% (\l@figure and \l@table are defined by the class above; these override them.)
\renewcommand*\l@figure{\@dottedtocline{1}{0pt}{2.3em}}
\renewcommand*\l@table {\@dottedtocline{1}{0pt}{2.3em}}

% ==============================================================================
% Page Styles
% (require titlesec[pagestyles]; reference \Author, \Course, \Title which are
%  \let-bound in main.tex before \begin{document} — safe because these are
%  expanded at page-output time, not at definition time)
% ==============================================================================
% \CTU@authorhead: expands to \Author with a mailto: hyperlink when CTUemail is
%   set and \@email is non-empty; plain \Author otherwise.
%   \href is resolved at page-output time, so hyperref need not be loaded yet.
\newcommand\CTU@authorhead{%
  \ifCTUemail\ifx\@email\@empty\Author\else\href{mailto:\@email}{\Author}\fi
  \else\Author\fi}
\newpagestyle{fancy}{
	\ifCTUheader\headrule\fi
	\sethead{\ifCTUheader\CTU@authorhead\fi}{}{\ifCTUheader\MakeUppercase{\chaptertitle}\fi}
	\setfoot{}{\thepage}{}
}
\renewpagestyle{plain}{
	\ifCTUheader\headrule\fi
	\sethead{\ifCTUheader\CTU@authorhead\fi}{}{\ifCTUheader\Course\fi}
	\setfoot{}{\thepage}{}
}
\newpagestyle{nonum}{
	\ifCTUheader\headrule\fi
	\sethead{\ifCTUheader\CTU@authorhead\fi}{}{\ifCTUheader\MakeUppercase{\Course}\fi}
	\footrule
	\setfoot{}{\begin{minipage}[t]{\textwidth}\centering\Title\end{minipage}}{}
}
\tocloftpagestyle{nonum}

% ==============================================================================
% Packages: Figures And Captions
% ==============================================================================
% graphicx[pdftex,final]: \includegraphics with the pdflatex driver. Also satisfies
%   the class's own use of \includegraphics in \maketitle (CTU logo).
%   'final' overrides the global draft class option: images are ALWAYS rendered
%   regardless of draft/debug mode (graphicx draft = empty boxes instead of images).
\RequirePackage[pdftex,final]{graphicx}
% float: H (here, exactly) placement specifier for figures and tables.
\RequirePackage{float}
% caption: styled captions — Czech names "Obr." / "Tab." with colon separator.
\RequirePackage{caption}
\captionsetup{labelfont=bf, labelsep=endash}
\captionsetup[figure]{labelfont={normalfont}, name={Obr.}, labelsep=colon}
\captionsetup[table] {labelfont={normalfont}, name={Tab.}, labelsep=colon}
% subcaption: \begin{subfigure} for side-by-side figures with sub-captions.
\RequirePackage{subcaption}
% pdfpages: include external PDF pages (thesis assignment form, mandatory pages).
%   'final' overrides global draft class option (without it pdfpages shows empty boxes).
\RequirePackage[final]{pdfpages}

% ==============================================================================
% Packages: Tables
% ==============================================================================
% array: extended column type syntax — enables the >{\cmd} prefix used in the
%   custom column type definitions below.
\RequirePackage{array}
% longtable: tables spanning multiple pages; left-aligned.
\RequirePackage{longtable}
\setlength\LTleft{0pt}
% tabularx: auto-width X columns filling a fixed total table width.
\RequirePackage{tabularx}
% xltabular: longtable + tabularx combined — required by the acro list template.
%   Also satisfies the class's own use of xltabular in \maketitle.
\RequirePackage{xltabular}
% multirow: cells spanning multiple rows via \multirow.  dormant.
\RequirePackage{multirow}
% multicol: multi-column text flow via the multicols environment.  dormant.
\RequirePackage{multicol}
% booktabs: professional horizontal rules — \toprule, \midrule, \bottomrule.
\RequirePackage{booktabs}
% Custom tabularx column types used in thesis tables and the acro list.
\renewcommand{\tabularxcolumn}[1]{p{#1}}
\newcolumntype{R}{>{\raggedleft}X}                               % right-aligned
\newcolumntype{L}{>{\raggedright}X}                              % left-aligned
\newcolumntype{C}{>{\centering\arraybackslash}X}                 % centered
\newcolumntype{s}{>{\centering\arraybackslash\hsize=.4\hsize}X}  % narrow center

% ==============================================================================
% Packages: Mathematics And SI Units
% ==============================================================================
% amsmath: align, gather, cases, equation* etc. Provides \text{} for \xmcal.
\RequirePackage{amsmath}
% amsfonts: \mathbb (ℝ, ℕ), \mathfrak font commands.
\RequirePackage{amsfonts}
% amssymb: extended AMS symbol set — \square, \triangleright, \nexists etc.
\RequirePackage{amssymb}
% wasysym: miscellaneous symbols (\smiley, \diameter, \phone etc.).  dormant.
\RequirePackage{wasysym}
% makeidx: back-of-book index via \index{} calls and \makeindex.  dormant.
\RequirePackage{makeidx}
% siunitx: SI units — \SI{75}{\percent}, \SI{}{\watt\per\cubic\meter}.
%   Czech locale: decimal comma separator, centered dot for products.
\RequirePackage{siunitx}
\sisetup{
  output-decimal-marker = {,},
  exponent-product       = \cdot,
  product-units          = repeat,
  product-symbol         = \cdot,
}
% Custom calligraphic font family for math mode: \xmcal{H}, \xmcal{L} etc.
% (Integral/Laplace transform notation — @ is already a letter here.)
\DeclareFontFamily{OT1}{mathc}{}
\DeclareFontShape{OT1}{mathc}{m}{n}{ <-> mathc10 }{}
\DeclareRobustCommand\xmcal[1]{\text{\usefont{OT1}{mathc}{m}{n}#1}}
% Unity step function symbol (double-struck 1): \one
\def\one{\mbox{1\hspace{-4.25pt}\fontsize{12}{14.4}\selectfont\textrm{1}}}

% ==============================================================================
% Packages: Colors, TikZ, PGFPlots, And Block Diagrams
% ==============================================================================
% xcolor: color definitions — also required internally by tikz and pgfplots.
\RequirePackage{xcolor}
% tikz: PGF/TikZ vector graphics engine.
\RequirePackage{tikz}
% pgfplots: data-driven plots (frequency responses, curves etc.).
%   compat=newest: latest pgfplots features.
%   math parser=false: coordinates are plain number pairs, not expressions.
\RequirePackage{pgfplots}
\pgfplotsset{compat=newest}
\pgfplotsset{plot coordinates/math parser=false}
% Named lengths for consistent figure sizing across standalone TikZ files.
\newlength\figureheight
\newlength\figurewidth
% blox: TikZ block-diagram library — summing junctions, transfer-function blocks.
\RequirePackage{blox}
% standalone: lets TikZ files compile as independent documents.
\RequirePackage{standalone}
% tikzextern option: cache compiled TikZ figures as external PDFs.
%   Disabled by default — add tikzextern to \documentclass options and
%   add -shell-escape to the pdflatex tool args in .vscode/settings.json.
\ifCTUtikzextern
  \usetikzlibrary{external}%
  \tikzexternalize
\fi

% ==============================================================================
% Packages: Lists, Quotation Marks, And Inline Helpers
% ==============================================================================
% enumitem: list customization — [leftmargin=*] in software list, [nosep] etc.
\RequirePackage{enumitem}
% csquotes: context-sensitive quotation marks; mandatory biblatex companion.
%   \MakeOuterQuote{"}: straight " in source auto-converts to „…" in Czech.
\RequirePackage{csquotes}
\MakeOuterQuote{"}
% \juv: inline mark-up for footnote-style quotes.
\newcommand{\juv}[1]{,#1`}

% ==============================================================================
% Packages: Acronyms
% ==============================================================================
% ocg-p: PDF Optional Content Groups — PDF-only "back to text" navigation link
%   in the acro list (printocg=never). Must be loaded before acro.
\RequirePackage{ocg-p}
% acro: \ac{}, \acs{}, \acl{}, \acp{} acronym commands.
%   \acsetup and \DeclareAcronym entries are \input in main.tex
%   (project-specific content).
\RequirePackage{acro}

% ==============================================================================
% Packages: Hyperlinks (after most packages, before biblatex)
% ==============================================================================
% hyperref: PDF metadata, cross-reference targets, clickable links.
%   draft=false: always create real PDF links even when draft class option is active
%   (hyperref draft mode disables all link annotations — not what we want).
%   In debug mode, hidelinks is omitted — each link target becomes a colored
%   box, making missing or unexpected links easy to spot.
%   Requires 3 full compilations after any cross-reference change to stabilize.
\if@debug
  \RequirePackage[draft=false]{hyperref}
\else
  \RequirePackage[draft=false,hidelinks]{hyperref}
\fi

% ==============================================================================
% Packages: Bibliography
% ==============================================================================
% biblatex + biber: ISO 690 numeric citation style, Czech locale (cs_CZ)
%   sorting, per-entry language for multilingual bibliographies.
%   \addbibresource calls are in main.tex (thesis-specific .bib filenames).
\RequirePackage[
  backend     = biber,
  style       = iso-numeric,
  sortlocale  = cs_CZ,
  autolang    = other,
  bibencoding = UTF8,
]{biblatex}

\endinput
%%
%% End of file `CTUthesis.cls'.
