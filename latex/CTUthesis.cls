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
%   Thesis type    : master (default)      bachelor          doctoral
%                    Sets cover text; interacts with draft/final and czech/english
%                    czech+final:  DIPLOMOVÁ PRÁCE / BAKALÁŘSKÁ PRÁCE / DISERTAČNÍ PRÁCE
%                    czech+draft:  REŠERŠE K DIPLOMOVÉ / BAKALÁŘSKÉ / DISERTAČNÍ PRÁCI
%                    english+final: MASTER'S THESIS / BACHELOR'S THESIS / DOCTORAL THESIS
%                    english+draft: RESEARCH FOR MASTER'S/BACHELOR'S/DOCTORAL THESIS
%   Debug          : debug                                  — overfull marks + colored link boxes
%   Page order     : openany (default)    openright
%   Cover page     : titlepage (default)  notitlepage       — suppresses \maketitle entirely
%   Header         : header (default)     noheader          — author/chapter running head + rule
%   Front matter   : frontmatter (def.)   nofrontmatter     — abstract, declarations, assignment
%   Acronym lists  : acro (default)       noacro            — acronym and variable lists
%   Bibliography   : bibliography (def.)  nobibliography
%   Software list  : software (default)   nosoftware
%   Back matter    : backmatter (default)  nobackmatter     — LOF, LOT, appendices
%   Back matter TOC: backmattertoc          nobackmattertoc (def.) — dotted TOC entries for back matter
%   Author email   : email (default)      noemail           — mailto link on author name on cover (always);
%                                                            email address printed below name on cover (draft only);
%                                                            mailto link in running header (if not disabled by noheader)
%   Language       : czech (default)      english           — switches babel hyphenation; translates cover texts and csquotes style
%                                                            headings, date, software list and acronym list headings
%   TikZ caching   : tikzextern                             — externalize TikZ figures (faster rebuilds)
%                    OFF by default; requires -shell-escape in the pdflatex recipe when active
%   Math layout    : leqno                fleqn             — left eq. numbers; flush-left display
%                    default: right-side eq. numbers, centered display equations
%   Sentinel       : CTUend              — no-op; keep as last option so all others can have
%                                          trailing commas (safe to comment/uncomment any line)
%
% Default: \documentclass[a4paper,12pt,oneside,onecolumn,final,openany,bachelor]{CTUthesis}
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
% \ifCTUbackmattertoc: when true, back-matter lists and bibliography appear in
%   the TOC with a dotted leader (section style).  Default: false.
\newif\ifCTUbackmattertoc  \CTUbackmattertocfalse
\newif\ifCTUemail       \CTUemailtrue
% \ifCTUenglish: false by default (Czech thesis); set true via english option.
%   Switches babel main language to English and translates all class-controlled
%   strings: cover text, university name, software list, and acronym list.
\newif\ifCTUenglish
% \CTU@thesistype: token set by bachelor/master/doctoral option; used to select
%   the correct nominative and dative thesis-type strings in \@course.
%   Default: bachelor.
\def\CTU@thesistype{bachelor}
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
% backmattertoc/nobackmattertoc: include or suppress back-matter entries
%   (bibliography, software, LOF, LOT, attachments) in the TOC.
%   When included they use a dotted leader (\l@section style), not bold chapter.
\DeclareOption{backmattertoc}{\CTUbackmattertoctrue}
\DeclareOption{nobackmattertoc}{\CTUbackmattertocfalse}
% email/noemail: add a mailto: hyperlink to the author name in running headers;
%   also display the email below the author table on the cover page (draft only).
\DeclareOption{email}{\CTUemailtrue}
\DeclareOption{noemail}{\CTUemailfalse}
% english: produce an English-language thesis — switches babel hyphenation to
%   English and translates all class-controlled UI strings (cover, chapter/appendix
%   names, self-citation, abstract headings, back matter list headings, \today).
%   All headings are hardcoded via \ifCTUenglish rather than relying on babel
%   caption strings, which are unreliable due to babel \AtBeginDocument ordering.
%   translates class-controlled headings: cover text, university name,
%   software list chapter, and acronym list heading.
\DeclareOption{english}{\CTUenglishtrue}
% Thesis type options: set \CTU@thesistype; controls the cover page text
%   in combination with the draft/final and czech/english options.
%   master (default): diplomová práce / master's thesis
%   bachelor        : bakalářská práce / bachelor's thesis
%   doctoral        : disertační práce / doctoral thesis
\DeclareOption{master}{\def\CTU@thesistype{master}}
\DeclareOption{bachelor}{\def\CTU@thesistype{bachelor}}
\DeclareOption{doctoral}{\def\CTU@thesistype{doctoral}}
% tikzextern: enable TikZ figure externalization (caches compiled figures as
%   PDFs in build/). Speeds up repeated builds when figures are unchanged.
%   Requires -shell-escape in the pdflatex recipe — see .vscode/settings.json.
\DeclareOption{tikzextern}{\CTUtikzexterntrue}
% CTUend: no-op sentinel option — always the last option in \documentclass[].
%   Its presence means every real option above it can have a trailing comma,
%   so toggling options by commenting/uncommenting lines never breaks syntax.
\DeclareOption{CTUend}{}
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
% Tunable Header Parameters
%   These lengths control how much of \textwidth each header slot may use before
%   falling back to a shorter form.  They are set to sensible defaults here and
%   can be overridden in the preamble with \setlength (after \documentclass but
%   before \begin{document}).
%
%   \CTUrheadmax  — right header slot budget.  Right-heading text is first tried
%                   in UPPERCASE; if that overflows the budget, mixed case is
%                   tried; if still over, the text is truncated at this width.
%                   Default: 0.75\textwidth (set at \begin{document}).
%
%   \CTUlheadmax  — left header slot budget for the full author name.
%                   Default: 0.25\textwidth.
%
%   \CTUlheadshortmax — left header slot budget for abbreviated author forms
%                   ("Surname, F.~M." / "Surname, F.").  Slightly wider than
%                   \CTUlheadmax to avoid suppressing marginally-long surnames.
%                   Default: 0.30\textwidth.
%
%   All three are initialised as fractions of \textwidth inside \AtBeginDocument
%   (where \textwidth is final) ONLY when the user has not assigned them a
%   positive value already — this way a preamble \setlength takes precedence.
% ==============================================================================
\newlength\CTUrheadmax
\newlength\CTUlheadmax
\newlength\CTUlheadshortmax
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
% \titlesecond{Text}: optional second line under the main thesis title.
%   Printed on title page (same font size as the main title) and appended to
%   the self-citation title in italics. It is intentionally excluded from
%   running headers (which continue to use only \Title).
\gdef\@titlesecond{}
\newcommand{\titlesecond}[1]{\gdef\@titlesecond{#1}}
% \supervisor{Name}: thesis supervisor for the self-citation entry.
%   Format: academic titles + name, e.g. "PhDr. Aleš Opekar, CSc."
%   Omit or leave commented to suppress the "Vedoucí práce" line.
\gdef\@supervisor{}
\newcommand{\supervisor}[1]{\gdef\@supervisor{#1}}
% \facultylogo{path}: optional faculty logo shown at bottom-left of citation
%   page.  Provide a path relative to the main .tex file.
%   Example: \facultylogo{logo/logo_MUVS_cb.pdf}
\gdef\@facultylogo{}
\newcommand{\facultylogo}[1]{\gdef\@facultylogo{#1}}
% \normostrana{N}: normostrana (standard-page) count for the citation page.
%   N = total body character count / 1800 (ISO 690 / Czech thesis convention).
%   Omit or leave commented to suppress the line entirely.
\gdef\@normostrana{}
\newcommand{\normostrana}[1]{\gdef\@normostrana{#1}}
% Raw keyword text captured from the files passed to \CTUabstract; used for
%   language-dependent PDF metadata.
\gdef\CTU@pdfkeywordscz{}
\gdef\CTU@pdfkeywordsen{}
\gdef\CTU@pdfpagelayout{SinglePage}
% \CTU@setpdfmetadata: populate the output PDF metadata from thesis metadata.
\newcommand\CTU@setpdfmetadata{%
  \pdfstringdef\CTU@pdftitle{\@title\ifx\@titlesecond\@empty\else: \@titlesecond\fi}%
  \pdfstringdef\CTU@pdfauthor{\@author}%
  \pdfstringdef\CTU@pdfsubject{\@course}%
  \ifCTUenglish
    \pdfstringdef\CTU@pdfkeywords{\CTU@pdfkeywordsen}%
  \else
    \pdfstringdef\CTU@pdfkeywords{\CTU@pdfkeywordscz}%
  \fi
  \hypersetup{%
    pdftitle={\CTU@pdftitle},%
    pdfauthor={\CTU@pdfauthor},%
    pdfsubject={\CTU@pdfsubject},%
    pdfkeywords={\CTU@pdfkeywords}%
  }%
}
% Quality-check counter macros --- populated from latexmkrc-generated tmp files.
%   Default -1 means "no data available"; CTU@runqualitychecks treats -1 as
%   a signal to skip the corresponding check silently (rather than warn "0").
\gdef\@CTUcitcount{-1}
\gdef\@CTUabstractchars{-1}
\gdef\@CTUabstractenchars{-1}
\gdef\@CTUkeywordschars{-1}
\gdef\@CTUkeywordsenchars{-1}
% Thesis-type-dependent minimum thresholds (Czech academic standards).
%   \CTU@normomin : minimum normostrana (40 bachelor / 60 master / 80 doctoral).
%   \CTU@citmin   : minimum cited references (20 bachelor; 40 master/doctoral).
%   Both are count commands (not macros expanding to digits) so they work
%   safely inside \ifnum comparisons without brace/token issues.
\newcount\CTU@normomin
\newcount\CTU@citmin
\AtBeginDocument{%
  \ifx\CTU@thesistype\CTU@type@bachelor
    \CTU@normomin=40\relax
    \CTU@citmin=20\relax
  \else\ifx\CTU@thesistype\CTU@type@doctoral
    \CTU@normomin=80\relax
    \CTU@citmin=40\relax
  \else
    \CTU@normomin=60\relax
    \CTU@citmin=40\relax
  \fi\fi}
% \@course: default set by the 3-way combination of draft/final, czech/english,
%   and bachelor/master/doctoral.  \course{} in the preamble overrides this.
%   Accent commands used because inputenc is loaded later in this class file.
% \CTU@selfcite@type: title-case thesis type for the self-citation entry.
%   Mirrors \@course but in sentence case (ISO 690 citation, not cover heading).
% Comparison tokens for \CTU@thesistype \ifx dispatch:
\def\CTU@type@bachelor{bachelor}
\def\CTU@type@doctoral{doctoral}
\if@draftmode
  \ifCTUenglish
    \ifx\CTU@thesistype\CTU@type@bachelor
      \def\@course{RESEARCH FOR BACHELOR'S THESIS}%
      \def\CTU@selfcite@type{Research for bachelor's thesis}%
    \else\ifx\CTU@thesistype\CTU@type@doctoral
      \def\@course{RESEARCH FOR DOCTORAL THESIS}%
      \def\CTU@selfcite@type{Research for doctoral thesis}%
    \else
      \def\@course{RESEARCH FOR MASTER'S THESIS}%
      \def\CTU@selfcite@type{Research for master's thesis}%
    \fi\fi
  \else
    \ifx\CTU@thesistype\CTU@type@bachelor
      \def\@course{RE\v{S}ER\v{S}E K~BAKAL\'{A}\v{R}SK\'{E} PR\'{A}CI}%
      \def\CTU@selfcite@type{Re\v{s}er\v{s}e k~bakal\'{a}\v{r}sk\'{e} pr\'{a}ci}%
    \else\ifx\CTU@thesistype\CTU@type@doctoral
      \def\@course{RE\v{S}ER\v{S}E K~DISERTA\v{C}N\'{I} PR\'{A}CI}%
      \def\CTU@selfcite@type{Re\v{s}er\v{s}e k~diserta\v{c}n\'{i} pr\'{a}ci}%
    \else
      \def\@course{RE\v{S}ER\v{S}E K~DIPLOMOV\'{E} PR\'{A}CI}%
      \def\CTU@selfcite@type{Re\v{s}er\v{s}e k~diplomov\'{e} pr\'{a}ci}%
    \fi\fi
  \fi
\else
  \ifCTUenglish
    \ifx\CTU@thesistype\CTU@type@bachelor
      \def\@course{BACHELOR'S THESIS}%
      \def\CTU@selfcite@type{Bachelor's thesis}%
    \else\ifx\CTU@thesistype\CTU@type@doctoral
      \def\@course{DOCTORAL THESIS}%
      \def\CTU@selfcite@type{Doctoral thesis}%
    \else
      \def\@course{MASTER'S THESIS}%
      \def\CTU@selfcite@type{Master's thesis}%
    \fi\fi
  \else
    \ifx\CTU@thesistype\CTU@type@bachelor
      \def\@course{BAKAL\'{A}\v{R}SK\'{A} PR\'{A}CE}%
      \def\CTU@selfcite@type{Bakal\'{a}\v{r}sk\'{a} pr\'{a}ce}%
    \else\ifx\CTU@thesistype\CTU@type@doctoral
      \def\@course{DISERTA\v{C}N\'{I} PR\'{A}CE}%
      \def\CTU@selfcite@type{Diserta\v{c}n\'{i} pr\'{a}ce}%
    \else
      \def\@course{DIPLOMOV\'{A} PR\'{A}CE}%
      \def\CTU@selfcite@type{Diplomov\'{a} pr\'{a}ce}%
    \fi\fi
  \fi
\fi
% \CTU@declaration@thesisword: Czech accusative noun for the thesis type used
%   in the statutory declaration.  Always Czech regardless of document language
%   (the declaration is a statutory requirement of Czech law).
\newcommand\CTU@declaration@thesisword{%
  \ifx\CTU@thesistype\CTU@type@bachelor bakal\'{a}\v{r}skou%
  \else\ifx\CTU@thesistype\CTU@type@doctoral diserta\v{c}n\'{i}%
  \else diplomovou%
  \fi\fi}
% Localised chapter/section headings for all back-matter lists.
%   Use these macros in main.tex instead of hardcoded Czech strings so the
%   correct heading is emitted automatically in both CZ and EN builds.
\newcommand\CTUsoftwarename{%
  \ifCTUenglish List of Software\else
    Seznam pou\v{z}it\'{e}ho softwaru\fi}
\newcommand\CTUacroname{%
  \ifCTUenglish List of Abbreviations\else
    Seznam pou\v{z}it\'ych zkratek\fi}
\newcommand\CTUvelname{%
  \ifCTUenglish List of Variables\else
    Seznam pou\v{z}it\'ych prom\v{e}nn\'ych\fi}
\newcommand\CTUidxname{%
  \ifCTUenglish List of Indices\else
    Seznam pou\v{z}it\'ych index\r{u}\fi}
\newcommand\CTUbibname{%
  \ifCTUenglish Bibliography\else
    Seznam pou\v{z}it\'e literatury\fi}
\newcommand\CTUprilohaname{%
  \ifCTUenglish List of Attachments\else
    Seznam p\v{r}\'{{\i}}loh\fi}
\newcommand\CTUcitacename{%
  \ifCTUenglish Quotes\else
    Citace\fi}
\newcommand\CTUlofname{%
  \ifCTUenglish List of Figures\else
    Seznam obr\'{a}zk\r{u}\fi}
\newcommand\CTUlotname{%
  \ifCTUenglish List of Tables\else
    Seznam tabulek\fi}
\newcommand\CTUtocname{%
  \ifCTUenglish Table of Contents\else
    Obsah\fi}
% \CTUacrobacklink: PDF "back to text" label shown above the acronym list
%   (via ocg-p; screen-only, hidden when printing). Localised.
\newcommand\CTUacrobacklink{%
  \ifCTUenglish BACK TO TEXT\else ZP\v{E}T DO TEXTU\fi}
% \CTUtoclink: label for the per-page TOC hyperlink in back-matter chapters
%   (bibliography, LOF, LOT; screen-only via OCG, works in all PDF viewers).
\newcommand\CTUtoclink{%
  \ifCTUenglish CONTENTS\else OBSAH\fi}
	\newcommand{\course}[1]{\gdef\@course{#1}
	}
% \@author / \@email: placeholder defaults; overwritten at load time when
%   latexmkrc has pre-generated main-gitauthor.tmp / main-gitemail.tmp from
%   git config (see latexmkrc).  Override in preamble with \author{} / \email{}.
\gdef\@author{Name Surname}
% \@authortitlebefore / \@authortitleafter: academic titles printed ONLY on the
%   cover page, flanking the author name.  Leave empty (default) to suppress.
%   Examples: \titlebefore{Ing.}  \titleafter{Ph.D.}
%   These intentionally do NOT affect \Author (used in running headers).
\gdef\@authortitlebefore{}
\gdef\@authortitleafter{}
	\newcommand{\titlebefore}[1]{\gdef\@authortitlebefore{#1}}
	\newcommand{\titleafter}[1]{\gdef\@authortitleafter{#1}}
% \@email: contact address; used in the page header mailto: link and below the
%   author table on the cover page when CTUemail is active.
\gdef\@email{address@e-mail.xy}
	\newcommand{\email}[1]{\gdef\@email{#1}
	}
% Short-author helpers — two variants:
%   \CTU@shortauthorall  "Surname, F.~M.~..." — initial of EVERY forename.
%   \CTU@shortauthorone  "Surname, F."         — initial of first forename only.
%
% \CTU@shortauthorall: walk forenames left-to-right, collecting each initial,
%   then emit "Surname, F.~M.~..."  (non-breaking spaces between initials).
\def\CTU@shortauthorall{\expandafter\CTU@sa@allgo\Author\@@ }
\def\CTU@sa@allgo#1 #2\@@{%
  \CTU@sa@alltail{\expandafter\@car#1\@nil}{#2}}
\def\CTU@sa@alltail#1#2{%
  \in@{ }{#2}%
  \ifin@ \CTU@sa@alladd{#1}#2\@@
  \else  #2,~#1.\fi}
\def\CTU@sa@alladd#1#2 #3\@@{%
  \CTU@sa@alltail{#1.~\@car#2\@nil}{#3}}
%
% \CTU@shortauthorone: same walk, but ignore all but the first forename initial.
%   Implemented by capturing the first initial in \CTU@sa@init and discarding
%   subsequent forenames while still finding the surname (last word).
\def\CTU@shortauthorone{\expandafter\CTU@sa@go\Author\@@ }
\def\CTU@sa@go#1 #2\@@{\def\CTU@sa@init{#1}\CTU@sa@tail{#2}}
\def\CTU@sa@tail#1{%
  \in@{ }{#1}%
  \ifin@\expandafter\CTU@sa@tails#1\@@
  \else #1,~\expandafter\@car\CTU@sa@init\@nil.\fi}
\def\CTU@sa@tails#1 #2\@@{\CTU@sa@tail{#2}}
% \CTU@headlink@mailto{text}: the mailto-link form of \CTU@headlink.
%   Reads \@email at expansion time (not baked-in), so it always uses the
%   current email address.  \CTU@headlink is \let to this at \AtBeginDocument
%   when CTUemail is active and \@email is non-empty.
\newcommand\CTU@headlink@mailto[1]{\href{mailto:\@email}{#1}}
% \CTU@coverfullauthor: author name with optional academic titles, for the
%   cover page only.  \@authortitlebefore / \@authortitleafter are empty by
%   default; non-empty values are separated from the name by a thin space (~).
\newcommand\CTU@coverfullauthor{%
  \ifx\@authortitlebefore\@empty\else\@authortitlebefore~\fi
  \@author
  \ifx\@authortitleafter\@empty\else~\@authortitleafter\fi}
% ==============================================================================
% Self-Citation Helpers
% ==============================================================================
% \CTU@selfcite@sn / \CTU@selfcite@fn are set at \AtBeginDocument by
% \CTU@precompute@selfcite below.  \CTU@selfcite uses them directly so that
% \MakeUppercase never sees delimited-argument macros (whose #1 #2\@@ patterns
% would cause "Illegal parameter number" inside \edef).
\gdef\CTU@selfcite@sn{}\gdef\CTU@selfcite@fn{}
\gdef\TitleSecond{}
%
% \CTU@precompute@selfcite: Called at \AtBeginDocument after \Author is set.
%   Splits \Author on spaces by redefining the tail helpers to store results
%   via \gdef rather than emitting tokens — no \edef, no expansion issues.
\newcommand\CTU@precompute@selfcite{%
  % --- surname (last space-delimited word) ---
  \begingroup
    \def\CTU@scs@go##1 ##2\@@{\CTU@scs@tail{##2}}%
    \def\CTU@scs@tail##1{%
      \in@{ }{##1}%
      \ifin@\expandafter\CTU@scs@nxt##1\@@
      \else\gdef\CTU@selfcite@sn{##1}\fi}%
    \def\CTU@scs@nxt##1 ##2\@@{\CTU@scs@tail{##2}}%
    \expandafter\CTU@scs@go\Author\@@ 
  \endgroup
  % --- firstnames (all words before the last) ---
  \begingroup
    \def\CTU@scf@go##1 ##2\@@{\CTU@scf@tail{##1}{##2}}%
    \def\CTU@scf@tail##1##2{%
      \in@{ }{##2}%
      \ifin@ ##1 \expandafter\CTU@scf@nxt##2\@@
      \else\gdef\CTU@selfcite@fn{##1}\fi}%
    \def\CTU@scf@nxt##1 ##2\@@{\CTU@scf@tail{##1}{##2}}%
    \expandafter\CTU@scf@go\Author\@@ 
  \endgroup}
% \CTU@addstop{text}: typeset text and append a period only when the expanded
%   text does not already end with one.  Uses expl3 string inspection so it is
%   unconditionally reliable — unlike \@addpunct it does not depend on the TeX
%   spacefactor being correctly propagated out of font groups or macro calls.
%   Used for the supervisor field which often ends with "Ph.D.".
\ExplSyntaxOn
\str_new:N \l__CTU_addstop_str
\newcommand \CTU@addstop [1] {%
  #1%
  \str_set:Nx \l__CTU_addstop_str {#1}%
  \str_if_eq:eeTF
    { \str_item:Nn \l__CTU_addstop_str { -1 } }
    { . }
    {}%         % already ends with a period — suppress
    { . }%      % no trailing period — add one
}
\ExplSyntaxOff
% \CTU@selfcite: full ISO-690 citation for this thesis.
%   Format mirrors the Czech standard example:
%   SURNAME, Firstname. Title. City, Year. Thesis type. University,
%   Faculty, Department. Vedoucí práce/Thesis supervisor: Supervisor.
%   \Author / \Title are \AtBeginDocument snapshots; they survive \maketitle.
\newcommand\CTU@selfcite{%
  % \CTU@selfcite@sn / \CTU@selfcite@fn are set at \AtBeginDocument by
  % \CTU@precompute@selfcite; they contain only plain token sequences safe
  % for \MakeUppercase (no delimited-macro expansion at call time).
  % \@addpunct{.} adds a full stop only when the preceding character did not
  % already set a high spacefactor (i.e. it is not itself a period) — this
  % prevents double dots after abbreviations such as "Ph.D." or "CSc.".
  \MakeUppercase{\CTU@selfcite@sn},
  \CTU@selfcite@fn\@addpunct{.}
  % \@addpunct must be INSIDE \textit{} so spacefactor reflects the last char
  % of the title, not the restored outer spacefactor after the font group closes.
  \textit{\Title\ifx\TitleSecond\@empty\else: \TitleSecond\fi\@addpunct{.}}
  \ifCTUenglish Prague\else Praha\fi,
  \number\year,
  % \ (backslash-space) is an explicit inter-word space; required here because
  % \fi is a control word and TeX eats the subsequent whitespace in state S.
  \@abspage@last~\ifCTUenglish p.\else s.\fi\ \CTU@selfcite@type.
  \ifCTUenglish Czech Technical University in Prague%
  \else \v{C}esk\'{e} vysok\'{e} u\v{c}en\'{i} technick\'{e} v~Praze\fi,
  \@faculty%
  \ifx\@department\relax\else, \@department\fi\@addpunct{.}
  \ifx\@supervisor\@empty\else
    \ifCTUenglish Thesis supervisor\else Vedouc\'{i} pr\'{a}ce\fi:
    \CTU@addstop{\@supervisor}%
  \fi}
% Snapshot metadata into shorthand macros used by page styles and headers.
%   \AtBeginDocument ensures any \author{}, \email{}, \title{}, \course{}
%   override in the preamble has already executed before the snapshot is taken.
%   These macros (\Author, \Email, \Title, \Course) do NOT need to be set
%   manually in main.tex — they are maintained entirely by the class.
% ==============================================================================
% Quality-Check Infrastructure
% ==============================================================================
% \CTU@qualitywarn{log-msg}{debug-label}:
%   Always emits a ClassWarning to the .log file.
%   In debug mode, also appends a full-width red colourbox to
%   \CTU@debugwarnlist, which \CTU@flushdebugwarnings renders in the PDF.
%   (xcolor is required for \colorbox — loaded later in this file but only
%   called at \AtBeginDocument time and beyond, so the order is safe.)
\gdef\CTU@debugwarnlist{}
\newcommand\CTU@qualitywarn[2]{%
  \ClassWarning{CTUthesis}{#1}%
  \if@debug
    \g@addto@macro\CTU@debugwarnlist{%
      \noindent\colorbox{red!25}{\parbox{\dimexpr\linewidth-2\fboxsep\relax}%
        {\small\sffamily\bfseries[CTUthesis] #2}}\par\smallskip}%
  \fi}
% \CTU@flushdebugwarnings: render all accumulated colourboxes and clear list.
%   Called from \CTUcitationpage so boxes appear on the citation page in the
%   PDF (only visible when the debug class option is active).
\newcommand\CTU@flushdebugwarnings{%
  \ifx\CTU@debugwarnlist\@empty\else
    \CTU@debugwarnlist
    \gdef\CTU@debugwarnlist{}%
  \fi}
% \CTU@runqualitychecks: load quality-metric tmp files then check all four
%   thresholds.  Called from \AtBeginDocument — warnings reach the .log as
%   early as possible; the PDF highlights are deferred to \CTUcitationpage.
\newcommand\CTU@runqualitychecks{%
  % Load latexmkrc-generated metric files (absent on first or plain-pdflatex
  % runs -> counter stays at the -1 default -> check silently skipped).
  % \makeatletter ensures @ has catcode 11 for the \@CTU... macro names in
  % these files (\AtBeginDocument hooks run with @ as catcode 12 in modern LaTeX).
  \makeatletter
  \InputIfFileExists{build/\jobname-textchecks.tmp}{}{}%
  \InputIfFileExists{build/\jobname-citcount.tmp}{}{}%
  \makeatother
  % (a) Normostrana threshold --------------------------------------------------
  \ifx\@normostrana\@empty\else
    \ifnum\@normostrana<\CTU@normomin\relax
      \CTU@qualitywarn{%
        Thesis scope is \@normostrana\space normostran
        (minimum \the\CTU@normomin\space for this thesis type)}{%
        Scope: \@normostrana\space normostran
        (min \the\CTU@normomin)}%
    \fi
  \fi
  % (b) Bibliography citation count -------------------------------------------
  \ifnum\@CTUcitcount<0 \else
    \ifnum\@CTUcitcount<\CTU@citmin\relax
      \CTU@qualitywarn{%
        Bibliography has \@CTUcitcount\space entries
        (minimum \the\CTU@citmin\space for this thesis type)}{%
        Bibliography: \@CTUcitcount\space entries
        (min \the\CTU@citmin)}%
    \fi
  \fi
  % (c) Abstract body character counts ----------------------------------------
  \ifnum\@CTUabstractchars<0 \else
    \ifnum\@CTUabstractchars<150
      \CTU@qualitywarn{%
        Czech abstract too short: \@CTUabstractchars\space chars (min 150)}{%
        Czech abstract: \@CTUabstractchars\space chars (min 150)}%
    \fi
    \ifnum\@CTUabstractchars>4000
      \CTU@qualitywarn{%
        Czech abstract too long: \@CTUabstractchars\space chars (max 4000)}{%
        Czech abstract: \@CTUabstractchars\space chars (max 4000)}%
    \fi
  \fi
  \ifnum\@CTUabstractenchars<0 \else
    \ifnum\@CTUabstractenchars<150
      \CTU@qualitywarn{%
        English abstract too short: \@CTUabstractenchars\space chars (min 150)}{%
        English abstract: \@CTUabstractenchars\space chars (min 150)}%
    \fi
    \ifnum\@CTUabstractenchars>4000
      \CTU@qualitywarn{%
        English abstract too long: \@CTUabstractenchars\space chars (max 4000)}{%
        English abstract: \@CTUabstractenchars\space chars (max 4000)}%
    \fi
  \fi
  % (d) Keywords body character counts ----------------------------------------
  \ifnum\@CTUkeywordschars<0 \else
    \ifnum\@CTUkeywordschars<20
      \CTU@qualitywarn{%
        Czech keywords too short: \@CTUkeywordschars\space chars (min 20)}{%
        Czech keywords: \@CTUkeywordschars\space chars (min 20)}%
    \fi
    \ifnum\@CTUkeywordschars>1000
      \CTU@qualitywarn{%
        Czech keywords too long: \@CTUkeywordschars\space chars (max 1000)}{%
        Czech keywords: \@CTUkeywordschars\space chars (max 1000)}%
    \fi
  \fi
  \ifnum\@CTUkeywordsenchars<0 \else
    \ifnum\@CTUkeywordsenchars<20
      \CTU@qualitywarn{%
        English keywords too short: \@CTUkeywordsenchars\space chars (min 20)}{%
        English keywords: \@CTUkeywordsenchars\space chars (min 20)}%
    \fi
    \ifnum\@CTUkeywordsenchars>1000
      \CTU@qualitywarn{%
        English keywords too long: \@CTUkeywordsenchars\space chars (max 1000)}{%
        English keywords: \@CTUkeywordsenchars\space chars (max 1000)}%
    \fi
  \fi}
\AtBeginDocument{%
  \let\Author\@author
  \let\Email\@email
  \let\Title\@title
  \let\TitleSecond\@titlesecond
  \let\Course\@course
  % Pre-compute selfcite surname and firstnames into \CTU@selfcite@sn / @fn.
  %   Splits \Author by executing the extractors with side-effect \gdef
  %   targets — no \edef, so UTF-8 accented names and delimiter tokens are safe.
  \CTU@precompute@selfcite
  % Auto-load normostrana count from latexmkrc-generated file only when the
  %   user has not already called \normostrana{} in the preamble.
  %   If the file is absent (e.g. first run, or plain pdflatex without latexmk)
  %   \@normostrana stays \@empty and the footer block is simply omitted —
  %   there is no fallback value, which is intentional (0 normostran would be
  %   misleading).  LaTeX Workshop: configure it to invoke latexmk so that
  %   latexmkrc runs texcount before each pdflatex call.
  \ifx\@normostrana\@empty
    \InputIfFileExists{build/\jobname-normostrana.tmp}{}{}%
  \fi
  % Run quality checks: loads abstract/keyword/citcount tmp files and emits a
  %   ClassWarning to the .log for each violated threshold.  Debug-mode PDF
  %   highlights are accumulated in \CTU@debugwarnlist and rendered later by
  %   \CTU@flushdebugwarnings inside \CTUcitationpage.
  \CTU@runqualitychecks
  % Initialise tunable header lengths from \textwidth (now finalised).
  %   Only set a length if the user has not already given it a positive value.
  \ifdim\CTUrheadmax=\z@      \setlength\CTUrheadmax{.75\textwidth}\fi
  \ifdim\CTUlheadmax=\z@      \setlength\CTUlheadmax{.25\textwidth}\fi
  \ifdim\CTUlheadshortmax=\z@ \setlength\CTUlheadshortmax{.30\textwidth}\fi
  % Encode the intended binding side for PDF viewers that honor page-layout
  %   hints: two-sided documents open as spreads with odd pages on the right.
  \if@twoside
    \gdef\CTU@pdfpagelayout{TwoPageRight}%
  \else
    \gdef\CTU@pdfpagelayout{SinglePage}%
  \fi
  \hypersetup{pdfdisplaydoctitle=true,pdfpagelayout=\CTU@pdfpagelayout}%
  % Apply the localised back-link preamble to the acronym list.
  % (Language switch lives in the post-babel \AtBeginDocument below; the
  %  \CTUacrobacklink macro already uses \ifCTUenglish so it is safe here.)
  \acsetup{list/preamble={%
    \Acrobatmenu{GoBack}{%
      \begin{ocg}[printocg=never]{name}{id1}{1}%
        \texttt{\CTUacrobacklink}%
      \end{ocg}}}}
  % \CTU@headlink{text}: wraps text in a mailto link when CTUemail is active
  %   and \@email is non-empty; otherwise passes text through.
  %   The macro reads \@email lazily at each shipout, so late \email{} calls
  %   in the preamble still take effect.
  \ifCTUemail
    \ifx\@email\@empty
      \global\let\CTU@headlink\@firstofone
    \else
      \global\let\CTU@headlink\CTU@headlink@mailto
    \fi
  \else
    \global\let\CTU@headlink\@firstofone
  \fi
  \settowidth\@tempdima{\Author}%
  \ifdim\@tempdima>\CTUlheadmax
    \settowidth\@tempdima{\CTU@shortauthorall}%
    \ifdim\@tempdima>\CTUlheadshortmax
      % all-initials overflows — try first-initial only
      \settowidth\@tempdima{\CTU@shortauthorone}%
      \ifdim\@tempdima>\CTUlheadshortmax
        \gdef\CTU@authorhead{}%  % suppress
      \else
        \gdef\CTU@authorhead{\CTU@headlink{\CTU@shortauthorone}}%
      \fi
    \else
      \gdef\CTU@authorhead{\CTU@headlink{\CTU@shortauthorall}}%
    \fi
  \else
    \gdef\CTU@authorhead{\CTU@headlink{\Author}}%
  \fi
  % Set base PDF metadata early; \CTUabstract refreshes it later once keyword
  %   files are known.
  \CTU@setpdfmetadata
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
	\ifCTUenglish Czech Technical University in Prague\else
	\v{C}esk\'{e} vysok\'{e} u\v{c}en\'{i} technick\'{e} v~Praze\fi
	\vskip 0.1cm
 	\@faculty
 	\vskip 0.1cm
 	\@department \par}
  \end{flushright}\par
  \vfill
 % \vskip 60\p@
  \begin{center}
    \includegraphics[scale=1]{logo/ctu_logo_black.pdf} 
    \vskip 0.7cm
    {\LARGE \sffamily \@course \par}%
    \vskip 0.8cm
    {\Large \sffamily \@title \par}%
    \ifx\@titlesecond\@empty\else
      {\Large \sffamily \@titlesecond \par}%
    \fi
    \vfill
    \begin{minipage}[b]{\textwidth}
    {\large
      \begin{xltabular}{\linewidth}{>{\centering\arraybackslash}X >{\centering\arraybackslash}X}%
        \ifCTUemail\ifx\@email\@empty
          \CTU@coverfullauthor
        \else\href{mailto:\@email}{\CTU@coverfullauthor}\fi
        \else\CTU@coverfullauthor\fi
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
\newcommand\CTU@abshead[1]{%
    \par\bigskip
    \@beginparpenalty\@lowpenalty
    \begin{center}%
      \bfseries #1%
      \@endparpenalty\@M
    \end{center}}
% \CTUabstract{cz-abstract}{cz-keywords}{en-abstract}{en-keywords}
% Convenience command: wraps the abstract environment and inserts the four
% section headings automatically, language-aware (\ifCTUenglish).
\newcommand\CTUabstract[4]{%
  \CatchFileDef\CTU@pdfkeywordscz{#2}{}%
  \CatchFileDef\CTU@pdfkeywordsen{#4}{}%
  \CTU@setpdfmetadata
  \begin{abstract}%
    \ifCTUenglish
      % English thesis: EN block first (matches \abstractname = "Abstract"),
      %   then CZ block with Czech headings.
      \input{#3}%
      \CTU@abshead{Keywords}%
      \begin{center}%
        \textit{\input{#4}}%
      \end{center}%
      \CTU@abshead{Abstrakt}%
      \input{#1}%
      \CTU@abshead{Kl\'{\i}\v{c}ov\'{a} slova}%
      \begin{center}%
        \textit{\input{#2}}%
      \end{center}%
    \else
      % Czech thesis: CZ block first (matches \abstractname = "Abstrakt"),
      %   then EN block with English headings.
      \input{#1}%
      \CTU@abshead{Kl\'{\i}\v{c}ov\'{a} slova}%
      \begin{center}%
        \textit{\input{#2}}%
      \end{center}%
      \CTU@abshead{Abstract}%
      \input{#3}%
      \CTU@abshead{Keywords}%
      \begin{center}%
        \textit{\input{#4}}%
      \end{center}%
    \fi
  \end{abstract}}
\newenvironment{abstract}{%
    \clearpage
    \thispagestyle{nonum}%
    \null\vfil
    \@beginparpenalty\@lowpenalty
    \begin{center}%
      \bfseries \ifCTUenglish Abstract\else Abstrakt\fi
      \@endparpenalty\@M
    \end{center}}%
   {\par\vfil\null\clearpage}
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
% Front Matter Environments
% ==============================================================================
% All front-matter pages use \thispagestyle{empty} (no header, no footer) and
% naturally increment the Arabic page counter (no reset), so TOC entries for
%   In debug mode the normostrana number is wrapped in a red colourbox when it
%   falls below the thesis-type minimum (\CTU@normomin).
\newcommand\CTU@normohighlight{%
  \if@debug
    \ifnum\@normostrana<\CTU@normomin\relax
      \colorbox{red!25}{\@normostrana}%
    \else
      \@normostrana
    \fi
  \else
    \@normostrana
  \fi}
% \CTU@citation@scope: "Rozsah práce" line shown below the citation text.
%   Shows only the normostrana count (with debug highlight when below minimum).
%   Suppressed entirely when normostrana is not set (no latexmk run yet).
\newcommand\CTU@citation@scope{%
  \ifx\@normostrana\@empty\else
    \ifCTUenglish Scope of thesis\else Rozsah pr\'{a}ce\fi:\space
    \CTU@normohighlight\space
    \ifCTUenglish standard pages\else normostran\fi\@addpunct{.}%
  \fi}%
%
% \CTUcitationpage[key]: isolated page containing the thesis self-citation.
%   Aligned to top; no header, no footer.
%   Optional argument: a biblatex key — uses \fullcite{key}.
%   Without argument: auto-generates ISO-690 entry via \CTU@selfcite.
%   "Rozsah práce" scope line appears two lines below the citation, flush left.
%   Faculty logo (if set) is pushed to the bottom of the page.
%   In debug mode, quality-check colourboxes are rendered below the citation.
\newcommand\CTUcitationpage[1][]{%
  \clearpage
  \thispagestyle{empty}%
  \noindent
  \@ifempty{#1}{\CTU@selfcite}{\fullcite{#1}}%
  \par\vspace{2\baselineskip}%
  \noindent\CTU@citation@scope\par
  \CTU@flushdebugwarnings
  \vspace*{\fill}%
  \ifx\@facultylogo\@empty\else
    \noindent\includegraphics[height=2.5\baselineskip]{\@facultylogo}\par
  \fi
  \clearpage
}
%
% ==============================================================================
% Front-matter free-standing pages: declaration, remarks, acknowledgements.
%   All three share a common top-aligned layout: \CTU@frontskip of vertical
%   space at the top of the text area, then content flows downward.  This
%   places the first line at a consistent position on every front-matter page.
% ==============================================================================
%
% \CTU@frontskip: vertical space from the top of the text area to the first
%   line of content on all free-standing front-matter pages.
\newlength\CTU@frontskip
\setlength\CTU@frontskip{4\baselineskip}
%
% \CTUsigskip: vertical space below the "V Praze" date line reserved for a
%   hand-written signature or an included signature image.
\newlength\CTUsigskip
\setlength\CTUsigskip{3\baselineskip}
%
% \CTU@declsig: internal — signature block appended at the end of every
%   declaration page.  Two blank lines, then "V Praze dne ..." flush left
%   with a dotted fill for the date, then \CTUsigskip space for the signature.
\newcommand\CTU@declsig{%
  \par\vspace{2\baselineskip}%
  \noindent V~Praze dne \makebox[4cm]{\dotfill}\par
  \vspace{\CTUsigskip}}%
%
% \CTU@declaration@default: the statutory Czech ethical declaration text.
%   \CTU@declaration@thesisword inserts the correct accusative noun.
%   Always Czech regardless of the document language (statutory requirement).
\newcommand\CTU@declaration@default{%
  Prohla\v{s}uji, \v{z}e jsem svou \CTU@declaration@thesisword{}
  pr\'{a}ci vypracoval samostatn\v{e}.
  D\'{a}le prohla\v{s}uji, \v{z}e jsem v\v{s}echny pou\v{z}it\'{e}
  zdroje spr\'{a}vn\v{e} a \'{u}pln\v{e} citoval a uv\'{a}d\'{i}m
  je v~p\v{r}ilo\v{z}en\'{e}m seznamu pou\v{z}it\'{e} literatury.\par
  Nem\'{a}m z\'{a}va\v{z}n\'{y} d\r{u}vod proti
  zp\v{r}\'{i}stup\v{n}ov\'{a}n\'{i} t\'{e}to z\'{a}v\v{e}re\v{c}n\'{e}
  pr\'{a}ce v~souladu se z\'{a}konem \v{c}.~121/2000~Sb.,
  o~pr\'{a}vu autorsk\'{e}m, o~pr\'{a}vech souvisej\'{i}c\'{i}ch
  s~pr\'{a}vem autorsk\'{y}m a o~zm\v{e}n\v{e} n\v{e}kter\'{y}ch
  z\'{a}kon\r{u} (autorsk\'{y} z\'{a}kon) v~platn\'{e}m zn\v{e}n\'{i}.}%
%
% \CTUdeclaration[text]: print the statutory Czech ethical declaration page.
%   No argument : auto-generated text from \CTU@declaration@default.
%   Optional arg: replaces the body text; signature block appended either way.
%   For a completely custom layout use the declaration environment instead.
\newcommand\CTUdeclaration[1][]{%
  \clearpage
  \thispagestyle{empty}%
  \vspace*{\CTU@frontskip}%
  \noindent
  \@ifempty{#1}{\CTU@declaration@default}{#1}%
  \CTU@declsig
  \clearpage
}
%
% declaration environment: full-override alternative to \CTUdeclaration.
%   Use when you need a different language or a completely custom layout.
%   The signature block (\CTU@declsig) is appended automatically at \end.
\newenvironment{declaration}{%
  \clearpage
  \thispagestyle{empty}%
  \vspace*{\CTU@frontskip}%
  \noindent\ignorespaces
}{%
  \CTU@declsig
  \clearpage
}
%
% thankspage environment: acknowledgements page.
\newenvironment{thankspage}{%
  \clearpage
  \thispagestyle{empty}%
  \vspace*{\CTU@frontskip}%
  \noindent\ignorespaces
}{%
  \par\clearpage
}
%
% remarkspage environment: optional remarks page (AI usage, image credits, …).
%   Include with \begin{remarkspage}…\end{remarkspage} in main.tex.
\newenvironment{remarkspage}{%
  \clearpage
  \thispagestyle{empty}%
  \vspace*{\CTU@frontskip}%
  \noindent\ignorespaces
}{%
  \par\clearpage
}
%
% \CTUassignment{file}: include the thesis assignment form as a full-page PDF.
%   Each page of the PDF gets \thispagestyle{empty}.
%   In twoside mode every assignment page is forced onto an odd (recto) page:
%   a blank verso is inserted before each page so the binding margin is always
%   on the left — assignment forms are single-sided originals.
%   When the file is not found an empty page with a warning message is emitted
%   instead of a hard error so the document still compiles.
%
%   Implementation note: pdfpages does not expose a per-page odd-forcing hook,
%   so in twoside mode we include one page at a time inside a loop.
%   \CTU@assignment@numpages is set via \pdfximage to count pages without
%   rendering; the loop uses \@tempcnta as the running page index.
\newcommand\CTUassignment[1]{%
  \IfFileExists{#1}{%
    \if@twoside
      % Count pages in the PDF so we can loop page-by-page.
      \pdfximage{#1}%
      \@tempcnta=1\relax
      \@whilenum\@tempcnta<\pdflastximagepages\do{%
        % Force current page to start on an odd (recto) page.
        \cleardoublepage
        \includepdf[pages={\the\@tempcnta},pagecommand={\thispagestyle{empty}}]{#1}%
        \advance\@tempcnta\@ne
      }%
      % Final page (or the only page when count is 1).
      \cleardoublepage
      \includepdf[pages={\the\@tempcnta},pagecommand={\thispagestyle{empty}}]{#1}%
    \else
      \includepdf[pages=-,pagecommand={\thispagestyle{empty}}]{#1}%
    \fi
  }{%
    % File not found: emit a blank page with a visible warning.
    \clearpage
    \thispagestyle{empty}%
    \vspace*{\fill}%
    \begin{center}
      \large\bfseries
      [{\ttfamily\detokenize{#1}} not found ---
       insert thesis assignment here]%
    \end{center}%
    \vspace*{\fill}%
    \ClassWarning{CTUthesis}{Assignment file `#1' not found.
      A placeholder page was inserted instead.}%
    \clearpage
  }%
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
    % Make the PDF open at the TOC anchor rather than the title page.
    \pdfcatalog{/OpenAction << /S /GoTo /D (CTU@toc) >>}%
    \chapter*{\CTUtocname
        \@mkboth{%
           \MakeUppercase\CTUtocname}{\MakeUppercase\CTUtocname}}%
    % Stable anchor placed HERE (after \chapter*'s internal \clearpage) so
    % it lands on the TOC page, not the preceding page.  Placed before
    % \@starttoc so navigating to CTU@toc shows the entries immediately.
    \hypertarget{CTU@toc}{}%
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
% Global flags: true when at least one captioned figure / table exists in the
% document.  Detected at \listoffigures / \listoftables call time by probing
% for the .lof / .lot files written by \@starttoc in the previous latexmk
% pass — this is robust against hyperref's \addcontentsline patch and any
% other package that wraps the TOC-writing machinery.
%
% First-run behaviour: on a clean build no .lof/.lot exists yet, so the list
% chapter is skipped on pass 1.  Pass 1 still writes the files via \@starttoc
% calls inside \caption; pass 2 then detects them and emits the chapter.
% latexmk automatically reruns to resolve cross-references, so the finished
% PDF always contains the correct lists.
\newif\if@CTUhasfigures
\newif\if@CTUhastables
\AtBeginDocument{%
  \IfFileExists{\jobname.lof}{\@CTUhasfigurestrue}{}%
  \IfFileExists{\jobname.lot}{\@CTUhastablestrue}{}%
}
\newcommand\listoffigures{%
    \if@CTUhasfigures
    \if@twocolumn
      \@restonecoltrue\onecolumn
    \else
      \@restonecolfalse
    \fi
    \chapter*{\CTUlofname}%
      \chaptermark{\CTUlofname}%
    \@starttoc{lof}%
    \if@restonecol\twocolumn\fi
    \fi
    }
\newcommand*\l@figure{\@dottedtocline{1}{1.5em}{2.3em}}
\newcommand\listoftables{%
    \if@CTUhastables
    \if@twocolumn
      \@restonecoltrue\onecolumn
    \else
      \@restonecolfalse
    \fi
    \chapter*{\CTUlotname}%
      \chaptermark{\CTUlotname}%
    \@starttoc{lot}%
    \if@restonecol\twocolumn\fi
    \fi
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
% English defaults; these are used for \chaptername/\appendixname (via \@chapapp)
%   and may also be overridden by babel when Czech is active.
%   Note: TOC, LOF, LOT, and abstract headings are NOT taken from these babel
%   strings — they use \ifCTUenglish directly to avoid AtBeginDocument ordering
%   issues with babel.
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
% Czech/English hyphenation patterns and csquotes quotation-mark styles.
%   All UI string translations are handled via \ifCTUenglish in the class;
%   babel is retained here solely for hyphenation and csquotes integration.
\RequirePackage[english,czech]{babel}
% Language switch hook registered HERE — after babel — so it fires after
% babel's own \AtBeginDocument hook that activates the main (Czech) language.
% This ensures \selectlanguage{english} wins and all caption names are English.
\AtBeginDocument{%
  \ifCTUenglish
    \selectlanguage{english}%
    \renewcommand\contentsname{Table of Contents}%
    \renewcommand\listfigurename{List of Figures}%
    \renewcommand\listtablename{List of Tables}%
    \acsetup{list/name={List of Abbreviations}}%
    \captionsetup[figure]{name={Fig.}}%
    \captionsetup[table] {name={Tab.}}%
  \else
    \captionsetup[figure]{name={Obr.}}%
    \captionsetup[table] {name={Tab.}}%
  \fi
}
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
% truncate: trims overlong text at a word boundary and appends \ldots.
%   Used in page headers so the right-head content stays within \CTUrheadmax.
\RequirePackage{truncate}
%\raggedbottom

% ==============================================================================
% Packages: Headings And TOC Entry Spacing
% ==============================================================================
% titlesec[pagestyles]: chapter/part title layout AND \newpagestyle commands
%   for the header/footer styles defined in the Page Styles section below.
%   fancyhdr is the legacy alternative — not loaded.
%\RequirePackage{fancyhdr}
\RequirePackage[pagestyles]{titlesec}
\titleformat{\part}[block]
	{\normalfont\Huge\bfseries\sffamily\filcenter}{}{0pt}{\MakeUppercase}[\thispagestyle{empty}]
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
%  \let-bound in \AtBeginDocument — safe because these are expanded at page-output
%  time, not at definition time)
%
%   Slot layout — oneside:
%     fancy/plain : left: Author          center: —   right: heading/Title
%                   footer center: page number
%   Slot layout — twoside:
%     fancy/plain : odd  (recto): left: Author  center: —  right: heading/Title
%                                 footer right:  page number (outer margin)
%                   even (verso): left: heading/Title  center: —  right: Author
%                                 footer left:   page number (outer margin)
%     Author is always adjacent to the spine (inner margin) on both sides.
%
%   nonum — front/back matter: as above for header; footer: centered Title.
%
%  titlesec \sethead/\setfoot signature:
%    \sethead[EL][EC][ER]{OL}{OC}{OR}
%    [brackets] = even-page slots (twoside only; silently ignored in oneside).
%    {braces}   = odd-page slots (and ALL pages in oneside).
%  \setfoot odd-page center carries \thepage in oneside (via \if@twoside guard);
%  in twoside mode the page number moves to the outer margin slot instead.
% ==============================================================================
% \CTU@rtext{text}: right-header text cascade (no hyperlink).
%   1. UPPERCASE fits (\@tempdima <= \CTUrheadmax): emit \MakeUppercase{text}.
%   2. Mixed case fits: emit text as-is.
%   3. Nothing fits: truncate mixed-case text at \CTUrheadmax with natural-width
%      output (local \@Trunc@Rebox patch, same as [fit] package option).
%   \@tempdima is a TeX scratch register; safe for sequential reuse here.
\newcommand\CTU@rtext[1]{%
  \settowidth\@tempdima{\MakeUppercase{#1}}%
  \ifdim\@tempdima>\CTUrheadmax
    % uppercase overflows — try mixed case
    \settowidth\@tempdima{#1}%
    \ifdim\@tempdima>\CTUrheadmax
      % mixed case also overflows — truncate
      \begingroup
        \def\@Trunc@Rebox{%
          \setbox\z@\hbox{\unhbox\z@\unskip\unskip\@tempa}%
          \ifdim\wd\z@>\hsize \hbox to\hsize{\unhbox\z@}\else \box\z@ \fi}%
        \truncate{\CTUrheadmax}{#1}%
      \endgroup
    \else
      #1%
    \fi
  \else
    \MakeUppercase{#1}%
  \fi}
% \CTU@rhead{anchor}{text}: right-header slot with hyperlink to heading.
%   Wraps \CTU@rtext output in \hyperlink{anchor}{...}.  The anchor names
%   follow hyperref's standard format:
%     chapter — chapter.\theHchapter  (= chapter.\thechapter by default)
%     section — section.\theHsection  (= chapter.\thesection)
%     subsec  — subsection.\theHsubsection
%     TOC     — CTU@toc  (placed by \tableofcontents above)
%   \hyperlink is always available here because hyperref is \RequirePackage'd.
\newcommand\CTU@rhead[2]{\hyperlink{#1}{\CTU@rtext{#2}}}
% \CTU@authorhead: left header slot.
%   The actual content is decided ONCE at \AtBeginDocument (see the snapshot
%   block above) and \gdef'd there. This \let just ensures the macro exists as
%   a no-op before \begin{document} so page-style definitions don't error.
\let\CTU@authorhead\@empty
% \CTU@rightheader: breadcrumb header for body pages (fancy pagestyle).
%   Shows the deepest active heading level only: SUBSECTION when inside one,
%   otherwise SECTION, otherwise CHAPTER. Right-aligned via \CTU@rhead.
%   \edef expands titlesec's mark macros so \ifx can test against \@empty.
\newcommand\CTU@rightheader{%
  \edef\CTU@tmp@se{\sectiontitle}%
  \edef\CTU@tmp@ss{\subsectiontitle}%
  \ifx\CTU@tmp@ss\@empty
    \ifx\CTU@tmp@se\@empty
      \CTU@rhead{chapter.\theHchapter}{\chaptertitle}%
    \else
      \CTU@rhead{section.\theHsection}{\CTU@tmp@se}%
    \fi
  \else
    \CTU@rhead{subsection.\theHsubsection}{\CTU@tmp@ss}%
  \fi}
\newpagestyle{fancy}{
	\ifCTUheader\headrule\fi
	\sethead[\ifCTUheader\CTU@rightheader\fi][][\ifCTUheader\CTU@authorhead\fi]
	        {\ifCTUheader\CTU@authorhead\fi}{}{\ifCTUheader\CTU@rightheader\fi}
	\setfoot[\thepage][\CTU@pagebacklink][]
	        {\CTU@pagebacklink}{\if@twoside\else\thepage\fi}{\if@twoside\thepage\fi}
}
\renewpagestyle{plain}{
	\ifCTUheader\headrule\fi
	\sethead[\ifCTUheader\CTU@rhead{CTU@toc}{\Title}\fi][][\ifCTUheader\CTU@authorhead\fi]
	        {\ifCTUheader\CTU@authorhead\fi}{}{\ifCTUheader\CTU@rhead{CTU@toc}{\Title}\fi}
	\setfoot[\thepage][\CTU@pagebacklink][]
	        {\CTU@pagebacklink}{\if@twoside\else\thepage\fi}{\if@twoside\thepage\fi}
}
\newpagestyle{nonum}{
	\ifCTUheader\headrule\fi
	\sethead[\ifCTUheader\CTU@rhead{CTU@toc}{\Course}\fi][][\ifCTUheader\CTU@authorhead\fi]
	        {\ifCTUheader\CTU@authorhead\fi}{}{\ifCTUheader\CTU@rhead{CTU@toc}{\Course}\fi}
	\footrule
	\setfoot{}{\begin{minipage}[t]{\textwidth}\centering\Title\end{minipage}}{}
}
% TOC pages use plain: shows roman page numbers while \pagenumbering{roman}
% is active (front matter), arabic once the body begins.
\tocloftpagestyle{plain}

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
% caption: styled captions with colon separator.
%   Language-neutral settings applied at load time; label names (Obr./Fig.,
%   Tab./Tab.) applied at \AtBeginDocument once \ifCTUenglish is known.
\RequirePackage{caption}
\captionsetup{labelfont=bf, labelsep=endash}
\captionsetup[figure]{labelfont={normalfont}, labelsep=colon}
\captionsetup[table] {labelfont={normalfont}, labelsep=colon}
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
  range-phrase           = {--},
  range-units            = single,
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
% contour: white outline around text for readability on coloured map backgrounds.
%   Used via \contour{white}{...} on country-code labels in PGF figures.
\RequirePackage[pdftex]{contour}
\contourlength{0.6pt}
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
% Common TikZ libraries used by hand-drawn schemas in texparts/figures/.
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,calc}

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
% ocg-p: PDF Optional Content Groups — screen-only "back to text" navigation
%   links (printocg=never).  Always loaded: used in the acro xltabular template
%   (via \CTUacrolistbacklink in acro_setup.tex) AND in the per-page back-link
%   of bibliography, LOF, and LOT (via \CTU@pagebacklink in the page style).
%   Must be loaded before acro.
\RequirePackage{ocg-p}
% \CTU@pagebacklink: per-page "back to text" button for back-matter chapters
%   (bibliography, LOF, LOT).  Activated by \CTU@backlinktrue; rendered on
%   every page via the center header slot of both 'plain' and 'fancy' styles.
%   Screen-only (OCG, printocg=never).  Each call advances \CTU@backlinkpagectr
%   to guarantee a unique OCG id even when the counter is not numeric.
\newcounter{CTU@backlinkpagectr}
\newif\ifCTU@backlink
\newcommand\CTU@pagebacklink{%
  \ifCTU@backlink
    \stepcounter{CTU@backlinkpagectr}%
    \Acrobatmenu{GoBack}{%
      \begin{ocg}[printocg=never]{CTU back link}{ctu-back-\arabic{CTU@backlinkpagectr}}{1}%
        \texttt{\CTUacrobacklink}%
      \end{ocg}}%
  \fi}
% acro: \ac{}, \acs{}, \acl{}, \acp{} acronym commands.
%   Configuration, templates, and sorting helpers are defined here (inside
%   \ifCTUacro) so the class fully owns the house-style acro setup.
%   Per-thesis declaration files (acro.tex, acro_variables.tex) are \input
%   separately in main.tex; \CTUuseLongSortForAcronyms is called there after
%   all declarations are loaded.
%   In noacro mode the package is skipped and lightweight stubs are defined
%   so \acs{}, \ac{} etc. in body text typeset the key (= short form) without
%   errors.  The \acsetup{} call in the \AtBeginDocument hook below is
%   harmlessly gobbled by the stub.
\ifCTUacro
  \RequirePackage{acro}
  % --------------------------------------------------------------------------
  % Global options
  % make-links=false: links and /Contents tooltips are created manually via
  %   \CTU@tooltiplink in the renewed templates below.  acro's built-in link
  %   mechanism only produces plain \hyperlink annotations with no /Contents,
  %   so it cannot carry the hover tooltip needed for Acrobat Reader.
  % list/display=used: \printacronyms omits entries that never appear in text.
  % list/template=xltabular: custom two-column table template defined below.
  % list/heading=chapter*: printed list gets an unnumbered chapter heading.
  \acsetup{%
    make-links     = false,%
    list/display   = used,%
    list/template  = xltabular,%
    list/heading   = chapter*%
  }
  % --------------------------------------------------------------------------
  % Per-page GoBack button for acro lists
  % Placed in the xltabular head so it repeats on every continuation page.
  % \Acrobatmenu{GoBack} is correct here: the user arrived via an \ac{} link
  % and GoBack returns to exactly that position in Acrobat.
  \newcounter{CTUacrolink}
  \newcommand\CTUacrolistbacklink{%
    \stepcounter{CTUacrolink}%
    \Acrobatmenu{GoBack}{%
      \begin{ocg}[printocg=never]{CTU acro backlink}{ctu-acro-backlink-\arabic{CTUacrolink}}{1}%
        \texttt{\CTUacrobacklink}%
      \end{ocg}}}
  \newcommand\CTUacrolisthead{%
    \multicolumn{2}{@{}l@{}}{\CTUacrolistbacklink}\\}
  % --------------------------------------------------------------------------
  % Long-sort helper
  % Overwrites each entry's `sort` property with its long form so
  % \printacronyms outputs entries in long-form alphabetical order.
  \ExplSyntaxOn
  \cs_new_protected:Npn \CTU_use_long_sort_for_acro_lists:
    {
      \acronymsmapTF
        {
          \acro_property_set:nne {\AcronymID} {sort}
            {\acro_property_get:ne {\AcronymID} {long}}
        }
        {}{}
    }
  \NewDocumentCommand{\CTUuseLongSortForAcronyms}{}
    {\CTU_use_long_sort_for_acro_lists:}
  \ExplSyntaxOff
  % --------------------------------------------------------------------------
  % Conditional variables-list helper
  % Suppresses the variables chapter when no vel-tag entries are used.
  \ExplSyntaxOn
  \cs_new_protected:Npn \CTU_if_variable_list_nonempty:TF #1#2
    {
      \group_begin:
        \keys_set:nn {acro/list} { include = vel , display = used }
        \acronymsmapTF {} { \group_end: #1 } { \group_end: #2 }
    }
  \NewDocumentCommand{\CTUifVariableListNonemptyTF}{mm}
    {\CTU_if_variable_list_nonempty:TF {#1}{#2}}
  \cs_new_protected:Npn \CTU_if_index_list_nonempty:TF #1#2
    {
      \group_begin:
        \keys_set:nn {acro/list} { include = idx , display = used }
        \acronymsmapTF {} { \group_end: #1 } { \group_end: #2 }
    }
  \NewDocumentCommand{\CTUifIndexListNonemptyTF}{mm}
    {\CTU_if_index_list_nonempty:TF {#1}{#2}}
  \ExplSyntaxOff
  % --------------------------------------------------------------------------
  % Index property
  % Variables that represent subscript/superscript indices (e.g. \square_0)
  % declare an `index` property holding the in-text display form (e.g.
  % \ensuremath{0}, \ensuremath{\Sigma}).  The `short` property retains the
  % full \square_N symbol used in the bold left column of the variables list.
  % When `index` is unset the behaviour is identical to the existing `short`
  % template.  Both sub- and superscript index variables use this mechanism.
  \DeclareAcroProperty{index}
  % --------------------------------------------------------------------------
  % List template: xltabular
  % Two-column layout: bold short form (with optional /alt) | long form with
  % optional (foreign, extra) parenthetical, dot-fill, and page references.
  % \hypertarget on the short-form cell ensures \ac{} links land on the bold
  % entry itself.  The repeated xltabular head repeats the GoBack button on
  % every page of a long list.
  \RenewAcroTemplate[list]{xltabular}{%
    \AcroNeedPackage{xltabular}%
    \acronymsmapF{%
      \AcroAddRow{%
        \hypertarget{\AcronymID}{\textbf{\acrowrite{short}}}%
        \acroifT{alt}{/\acrowrite{alt}}%
        &
        \acrowrite{list}%
        \acroifanyT{foreign,extra}{ (}%
        \acroifT{foreign}{\acrowrite{foreign}\acroifT{extra}{,}}%
        \acroifT{extra}{\acrowrite{extra}}%
        \acroifanyT{foreign,extra}{)}%
        \acropagefill
        \acropages
          {\acrotranslate{page}\nobreakspace}
          {\acrotranslate{pages}\nobreakspace}%
        \\}}
    {\AcroRerun}%
    \acroheading
    \acropreamble
    \par
    \begin{flushleft}
    \begin{xltabular}[l]{\linewidth}{@{} lX @{}}
    \CTUacrolisthead
    \endfirsthead
    \CTUacrolisthead
    \endhead
    \AcronymTable
    \end{xltabular}
    \end{flushleft}%
  }
  % --------------------------------------------------------------------------
  % Display templates for \ac{} (long-short) and \acs{} (short).
  %   make-links=false means acro creates no link annotations.  All links and
  %   /Contents tooltips are created here via \CTU@tooltiplink (defined after
  %   hyperref below), which wraps the text in a single GoTo Link annotation
  %   that carries /Contents — the tooltip mechanism supported by Acrobat Reader,
  %   Acrobat Pro, and PDF.js (LaTeX Workshop preview).
  %
  %   The tooltip text is the long form of the acronym.  \acrowrite{long} is a
  %   non-expandable \NewDocumentCommand so it cannot be used directly inside
  %   \pdfstringdef.  \acro_property_get:Vn IS expandable (defined with
  %   \cs_new:Npn) and returns the raw stored property tokens, which \pdfstringdef
  %   with unicode=true encodes correctly — including Czech/UTF-8 characters.
  %   \AcronymID is a plain LaTeX macro that acro sets to the current acronym
  %   ID string (e.g. "NC") immediately before each template body executes;
  %   the :Vn variant extracts its VALUE (the ID string) as the lookup key.
  %   The templates are defined inside \ExplSyntaxOn so that the expl3 function
  %   name \acro_property_get:Vn and \AcronymID are tokenized with expl3
  %   catcodes (colon and underscore as letters).
  \ExplSyntaxOn
  % Helper: emit (visible)+tooltip without a hyperlink.  Used for entries
  % with tag=geo whose acronym list is not printed (so no \hypertarget exists)
  % — calling \CTU@tooltiplink would create a goto-name link to a missing
  % destination, causing Acrobat to fall back to the cover page.
  \cs_new:Npn \CTU@geo_tooltip:nn #1#2 { \pdftooltip{#1}{#2} }
  \RenewAcroTemplate{long-short}{%
    \acroiffirstTF{%
      \str_if_eq:eeTF { \acro_property_get:Vn \AcronymID { tag } } { geo } {%
        \CTU@geo_tooltip:nn { \acrowrite{short} }
                            { \acro_property_get:Vn \AcronymID { long } }%
      }{%
      \CTU@tooltiplink{\AcronymID}{%
        \acrowrite{long}%
        \acspace(%
        \acrowrite{short}%
        \acroifT{foreign}{\footnote{\acrowrite{foreign}}}%
        \acroifT{alt}{ \acrotranslate{or} \acrowrite{alt}}%
        \acrogroupcite)%
      }{ \acro_property_get:Vn \AcronymID { long } }%
      }%
    }%
    {%
      \str_if_eq:eeTF { \acro_property_get:Vn \AcronymID { tag } } { geo } {%
        \CTU@geo_tooltip:nn { \acrowrite{short} }
                            { \acro_property_get:Vn \AcronymID { long } }%
      }{%
      \CTU@tooltiplink{\AcronymID}{\acrowrite{short}}
        { \acro_property_get:Vn \AcronymID { long } }%
      }%
    }%
  }
  % short template: when `index` is set (subscript/superscript index variable)
  %   show only the index part in text; otherwise show the normal short form.
  %   The `short` form (e.g. \square_0) is always shown in the variables list
  %   via \acrowrite{short} in the xltabular list template above.
  \RenewAcroTemplate{short}{%
    \str_if_eq:eeTF { \acro_property_get:Vn \AcronymID { tag } } { geo } {%
      \CTU@geo_tooltip:nn { \acrowrite{short} }
                          { \acro_property_get:Vn \AcronymID { long } }%
    }{%
    \tl_if_empty:eTF { \acro_property_get:Vn \AcronymID {index} }
      {%  no index property — normal short display
        \CTU@tooltiplink{\AcronymID}{\acrowrite{short}}
          { \acro_property_get:Vn \AcronymID { long } }%
      }%
      {%  index property set — show only the index part in text
        \CTU@tooltiplink{\AcronymID}{\acrowrite{index}}
          { \acro_property_get:Vn \AcronymID { long } }%
      }%
    }%
  }
  \ExplSyntaxOff
\else
  % --- noacro stubs -----------------------------------------------------------
  % In-text commands: emit the key, which equals the short form for every
  %   entry in this project (OS, NC, TCP, …).  Acceptable for fast drafts.
  \newcommand\ac   [1]{#1}%
  \newcommand\acs  [1]{#1}%
  \newcommand\acl  [1]{#1}%
  \newcommand\acp  [1]{#1}%
  \newcommand\acsp [1]{#1}%
  \newcommand\aclp [1]{#1}%
  \newcommand\acuse[1]{}%    % mark-as-used, no output
  \newcommand\acused[1]{}%
  % \acsetup is called from two \AtBeginDocument hooks in this class;
  %   the stub gobbles the argument so those calls are no-ops.
  \newcommand\acsetup[1]{}%
\fi
% catchfile: read external keyword files so their contents can populate PDF
%   metadata without duplicating them in the preamble.
\RequirePackage{catchfile}

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
  \RequirePackage[draft=false,unicode=true]{hyperref}
\else
  \RequirePackage[draft=false,hidelinks,unicode=true]{hyperref}
\fi
% bookmark: extended PDF bookmark control, loaded after hyperref.
%   Used (e.g.) for \bookmarksetup{startatroot} to lift standalone chapters
%   such as Závěr out of their enclosing \part in the bookmark panel.
\RequirePackage{bookmark}
% User-level alias so Python-generated PGF files can reference it without
% needing \makeatletter (which fails when TeX tokenises an argument group).
\newcommand{\CTUtooltiplink}[3]{\CTU@tooltiplink{#1}{#2}{#3}}
% \CTU@tooltiplink{destination}{visible text}{tooltip text}
%   Creates a single GoTo Link annotation whose /Contents entry is the tooltip.
%   This is the standard PDF mechanism for hover tooltips on hyperlinks and is
%   supported by Acrobat Reader, Acrobat Pro, and PDF.js (LaTeX Workshop).
%   Border/colour mirrors hyperref's internal-link style so debug-mode boxes
%   appear on acro and cite links exactly like all other internal links.
%   \pdfstringdef encodes the tooltip text via hyperref's Unicode-aware encoder.
%   NOTE: \pdfstartlink/\pdfendlink must not be inside an \hbox or \vbox.
\newcommand{\CTU@tooltiplink}[3]{%
  % \pdfstringdef and \pdfstartlink are not allowed in math mode.  When called
  % from \acs{var-X} or \acs{idx-Y} inside $...$, switch to restricted
  % horizontal mode via \mbox and re-enter math mode for the visible glyphs so
  % the link annotation is built around the math content.  This produces
  % clickable, tooltipped acronym links inside equations.
  \ifmmode
    \mbox{\CTU@tooltiplink{#1}{$#2$}{#3}}%
  \else
  % NOTE: do NOT pass #1 through \HyperDestNameFilter / \pdfstringdef.
  % With hyperref's [unicode=true], \pdfstringdef encodes the destination name
  % as UTF-16BE (with BOM), which then no longer matches the raw ASCII names
  % registered by biblatex (cite.<refsection>@<key>) and acro (<AcronymID>) in
  % the PDF /Dests Names tree.  The resulting goto name{...} lookup falls back
  % to the cover page in Acrobat.  Pass the destination tokens raw.
  \pdfstringdef\CTU@tip{#3}%
  \protected@edef\Hy@tempa{%
    \Hy@setpdfborder
    \ifx\@linkbordercolor\relax\else /C[\@linkbordercolor]\fi
    /Contents(\CTU@tip)%
  }%
  \leavevmode
  \pdfstartlink attr{\Hy@tempa} goto name{#1}\relax
  \Hy@colorlink\@linkcolor
  #2%
  \Hy@endcolorlink
  \pdfendlink
  \fi
}
% Strip formatting and normalise dashes in PDF tooltip strings.
% Also bypass the \exp_not:n (= \unexpanded) wrappers that acro3 and biblatex
% use when storing field values, so that the active UTF-8 byte chars (e.g. byte
% pair 0xC3 0xAD for U+00ED í) can be processed by hyperref's UTF-8→UTF-16BE
% machinery inside \pdfstringdef's \edef.  The change is local to each
% \pdfstringdef call (the PreHook runs inside its \begingroup).
\pdfstringdefDisableCommands{%
  \def\textit#1{#1}%
  \def\emph#1{#1}%
  \def\textbf#1{#1}%
  \def\textendash{--}%
  \def\textemdash{---}%
  % Make \exp_not:n a pass-through so storage wrappers don't block expansion.
  % \csname produces the expl3 cs regardless of the catcode of : in scope here.
  \expandafter\let\csname exp_not:n\endcsname\@firstofone%
}
% lastpage: sets the LastPage label at the end of the document; also stores
%   \@abspage@last (a plain Arabic integer) in the .aux file so self-citation
%   can report the total page count independently of how \thepage is formatted
%   (back matter uses \Roman{page}, which would make \pageref*{LastPage} return
%   a Roman numeral).
\RequirePackage{lastpage}
% pdfcomment: hover tooltip annotations in PDF viewers (Adobe Acrobat, Foxit).
%   Must be loaded AFTER hyperref (it uses hyperref internally).
%   Used via \pdftooltip{displayed}{tooltip text} in PGF figures.
%   Annotations are invisible in non-interactive viewers and in print.
\RequirePackage{pdfcomment}

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

% Bibliography list: render numeric labels as [N] (square brackets) to match
%   the in-text \cite[N] format produced by \DeclareCiteCommand below.
%   iso-numeric default is "N." (period); we override to "[N]".
\DeclareFieldFormat{labelnumberwidth}{\mkbibbrackets{#1}}
\setlength{\biblabelsep}{1em}

% \CTUaddtotoc{title}: conditionally add a back-matter entry to the TOC.
%   When \ifCTUbackmattertoc is true, writes a dotted-leader (section-style)
%   TOC entry via \addcontentsline{toc}{section}{title}.  The section level
%   shares \l@section's indent/numwidth but carries no number — the numwidth
%   space is therefore effectively zero (achieved by the section format).
%   \phantomsection is called before the \addcontentsline so that hyperref's
%   anchor lands on the correct page.
\newcommand\CTUaddtotoc[1]{%
  \ifCTUbackmattertoc
    \phantomsection
    \addcontentsline{toc}{section}{#1}%
  \fi}

% Custom biblatex heading for back-matter TOC integration.
%   \printbibliography[heading=CTUbib] uses this heading, which calls
%   \CTUaddtotoc internally so the TOC entry obeys the toggle.
\defbibheading{CTUbib}[\CTUbibname]{%
  \chapter*{#1}%
  \chaptermark{#1}%
  \CTUaddtotoc{#1}}

% \cite hover tooltips: each [N] in text gets a GoTo link with /Contents tooltip
%   showing the entry's title (and year when present).
%   \DeclareCiteCommand overrides iso-numeric's default \cite so every key in a
%   multi-key cite gets its own \CTU@tooltiplink.  Range compression is not used
%   in this project so disabling it here has no effect on existing citations.
%   Destination format matches biblatex's unconditional \hypertarget placed on
%   every bibliography entry: cite.<refsection>@<key>  (@ separator, not :).
%   Note: \bibhypertarget (used by verbose styles) produces the : form, but
%   iso-numeric does not call \bibhypertarget — only the @ form exists.
%   \thefield{} retrieves the field value with active UTF-8 byte chars intact so
%   that hyperref's \HyPsd@expand@utfviii machinery can produce correct UTF-16BE.
%   (\strfield uses \detokenize which converts active chars to catcode-12 bytes,
%   causing each UTF-8 byte to be misinterpreted as an individual Latin-1 code
%   point — the same root cause as the acro \exp_not:n issue addressed above.)
\DeclareCiteCommand{\cite}[\mkbibbrackets]
  {\usebibmacro{prenote}}
  {\usebibmacro{citeindex}%
   \CTU@tooltiplink{cite.\the\c@refsection @\thefield{entrykey}}
     {\thefield{labelnumber}}
     {\thefield{title}\iffieldundef{year}{}{, \thefield{year}}}}
  {\addcomma\addspace}
  {\usebibmacro{postnote}}

% ==============================================================================
% Back Matter Command
% ==============================================================================
% Default content-file paths (without .tex extension, resolved at call time).
%   Override in preamble with \softwarefile{path} / \attachmentsfile{path}.
\gdef\CTU@softwarefile{texparts/references/list_software}
\gdef\CTU@attachmentsfile{texparts/references/list_attachments}
\newcommand\softwarefile[1]{\gdef\CTU@softwarefile{#1}}
\newcommand\attachmentsfile[1]{\gdef\CTU@attachmentsfile{#1}}
% \CTUbackmatter: typeset all toggled back-matter sections in the standard order:
%   bibliography \u2192 software list \u2192 LOF \u2192 LOT \u2192 attachments list.
%   Responsibilities:
%     - \bookmarksetup{startatroot}: back-matter bookmarks are root siblings, not
%       children of the preceding body chapter or \part.
%     - page-number reset to Roman (back matter convention); first \clearpage.
%     - per-page back-to-text links on bibliography, LOF, and LOT pages (\CTU@backlinktrue).
%     - conditional guards (\ifCTUbiblio, \ifCTUsoftware, \ifCTUbackmatter).
%     - \CTUaddtotoc and \label for each section.
%   Call once, after the last body chapter (replaces manual back-matter code in main.tex).
\newcommand\CTUbackmatter{%
  \bookmarksetup{startatroot}%
  \clearpage
  \CTU@backlinktrue
  \renewcommand{\thepage}{\Roman{page}}%
  \phantomsection
  \ifCTUbiblio
    \printbibliography[heading=CTUbib]%
    \label{ch:bibliography}%
  \fi
  \ifCTUsoftware
    \chapter*{\CTUsoftwarename}%
    \chaptermark{\CTUsoftwarename}%
    \CTUaddtotoc{\CTUsoftwarename}%
    \InputIfFileExists{\CTU@softwarefile.tex}{}{}%
    \label{ch:software}%
  \fi
  \ifCTUbackmatter
    \listoffigures
    \CTUaddtotoc{\CTUlofname}%
    \label{ch:figures}%
    \listoftables
    \CTUaddtotoc{\CTUlotname}%
    \label{ch:tables}%
    \chapter*{\CTUprilohaname}%
    \chaptermark{\CTUprilohaname}%
    \CTUaddtotoc{\CTUprilohaname}%
    \InputIfFileExists{\CTU@attachmentsfile.tex}{}{}%
    \label{ch:attachments}%
  \fi}

% ==============================================================================
% \inputpgffigure{name} — include a matplotlib PGF figure
% ==============================================================================
% Includes the editable figure definition from texparts/figures/<name>.tex.
% The PGF file is expected at ../python/figures/<name>.pgf (relative to the
% latex/ directory, matching \graphicspath{{../python/figures/}}).
%
% If the .pgf file does not exist (script not yet run), a visible warning box
% is shown in the PDF instead of a hard compilation error.
%
% Usage in commentary files:  \inputpgffigure{vyhled_porodnost_vyvoj}
\newcommand{\inputpgffigure}[1]{%
  \IfFileExists{../python/figures/#1.pgf}{%
    \input{texparts/figures/#1}%
  }{%
    \begin{center}
      \fboxsep=8pt
      \colorbox{yellow!40}{%
        \parbox{0.85\linewidth}{%
          \color{red!70!black}\bfseries
          \texttt{[#1.pgf]} chybí --- spusťte odpovídající Python skript.%
        }%
      }%
    \end{center}%
  }%
}

\endinput
%%
%% End of file `CTUthesis.cls'.
