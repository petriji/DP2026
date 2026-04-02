%%
%% This is file `CTUthesis.cls',
%%
%% The original source files were:
%%
%% classes.dtx  (with options: `report')
%% report.cls
%%
%% This is a customized default style file.
%% 
%% Jiří Petříček 2019
%% 
\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{CTUthesis}
              [2019/07/16]
\newcommand\@ptsize{}
\newif\if@restonecol
\newif\if@titlepage
\@titlepagetrue
\newif\if@openright
\if@compatibility\else
\DeclareOption{a4paper}
   {\setlength\paperheight {297mm}%
    \setlength\paperwidth  {210mm}}
\DeclareOption{a5paper}
   {\setlength\paperheight {210mm}%
    \setlength\paperwidth  {148mm}}
\fi
\if@compatibility
  \renewcommand\@ptsize{0}
\else
\DeclareOption{10pt}{\renewcommand\@ptsize{0}}
\fi
\DeclareOption{11pt}{\renewcommand\@ptsize{1}}
\DeclareOption{12pt}{\renewcommand\@ptsize{2}}
\if@compatibility\else
\DeclareOption{oneside}{\@twosidefalse \@mparswitchfalse}
\fi
\DeclareOption{twoside}{\@twosidetrue  \@mparswitchtrue}
\DeclareOption{draft}{\setlength\overfullrule{5pt}}
\if@compatibility\else
\DeclareOption{final}{\setlength\overfullrule{0pt}}
\fi
\DeclareOption{titlepage}{\@titlepagetrue}
\if@compatibility\else
\DeclareOption{notitlepage}{\@titlepagefalse}
\fi
\if@compatibility
\else
\DeclareOption{openright}{\@openrighttrue}
\DeclareOption{openany}{\@openrightfalse}
\fi
\if@compatibility\else
\DeclareOption{onecolumn}{\@twocolumnfalse}
\fi
\DeclareOption{twocolumn}{\@twocolumntrue}
\DeclareOption{leqno}{\input{leqno.clo}}
\DeclareOption{fleqn}{\input{fleqn.clo}}
\DeclareOption{openbib}{%
  \AtEndOfPackage{%
   \renewcommand\@openbib@code{%
      \advance\leftmargin\bibindent
      \itemindent -\bibindent
      \listparindent \itemindent
      \parsep \z@
      }%
   \renewcommand\newblock{\par}}%
}
\ExecuteOptions{letterpaper,12pt,oneside,onecolumn,final,openany}
\ProcessOptions
\input{size1\@ptsize.clo}
\setlength\lineskip{1\p@}
\setlength\normallineskip{1\p@}
\renewcommand\baselinestretch{1.5}
\setlength\parskip{0\p@ \@plus \p@}
\@lowpenalty   51
\@medpenalty  151
\@highpenalty 301
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
\if@twoside
  \def\ps@headings{%
      \let\@oddfoot\@empty\let\@evenfoot\@empty
      \def\@evenhead{\thepage\hfil\slshape\leftmark}%
      \def\@oddhead{{\slshape\rightmark}\hfil\thepage}%
      \let\@mkboth\markboth
    \def\chaptermark##1{%
      \markboth {\MakeUppercase{%
        \ifnum \c@secnumdepth >\m@ne
            \@chapapp\ \thechapter. \ %
        \fi
        ##1}}{}}%
    \def\sectionmark##1{%
      \markright {\MakeUppercase{%
        \ifnum \c@secnumdepth >\z@
          \thesection. \ %
        \fi
        ##1}}}}
\else
  \def\ps@headings{%
    \let\@oddfoot\@empty
    \def\@oddhead{{\slshape\rightmark}\hfil\thepage}%
    \let\@mkboth\markboth
    \def\chaptermark##1{%
      \markright {\MakeUppercase{%
        \ifnum \c@secnumdepth >\m@ne
            \@chapapp\ \thechapter. \ %
        \fi
        ##1}}}}
\fi
\def\ps@myheadings{%
    \let\@oddfoot\@empty\let\@evenfoot\@empty
    \def\@evenhead{\thepage\hfil\slshape\leftmark}%
    \def\@oddhead{{\slshape\rightmark}\hfil\thepage}%
    \let\@mkboth\@gobbletwo
    \let\chaptermark\@gobble
    \let\sectionmark\@gobble
    }
    %%%%
\def\@faculty{\relax}
	\newcommand{\faculty}[1]{\gdef\@faculty{#1}
	}
\def\@department{\relax}
	\newcommand{\department}[1]{\gdef\@department{#1}
	}
\def\@course{\relax}
	\newcommand{\course}[1]{\gdef\@course{#1}
	}
	%%%%
  \if@titlepage
  \newcommand\maketitle{\begin{titlepage}%
  \thispagestyle{empty}  
%  \let\footnotesize\small
%  \let\footnoterule\relax
%  \let\footnote\date
%   \let\footnote\thanks

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
        \@author
      \end{xltabular}\par}%
     \end{minipage}
%      \vskip 0.8cm%
  \vfill
  {\normalsize \@date \par}%       % Set date in \large size.
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
}
\else
\newcommand\maketitle{\par
  \begingroup
    \renewcommand\thefootnote{\@fnsymbol\c@footnote}%
    \def\@makefnmark{\rlap{\@textsuperscript{\normalfont\@thefnmark}}}%
    \long\def\@makefntext##1{\parindent 1em\noindent
            \hb@xt@1.8em{%
                \hss\@textsuperscript{\normalfont\@thefnmark}}##1}%
    \if@twocolumn
      \ifnum \col@number=\@ne
        \@maketitle
      \else
        \twocolumn[\@maketitle]%
      \fi
    \else
      \newpage
      \global\@topnum\z@   % Prevents figures from going at top of page.
      \@maketitle
    \fi
    \thispagestyle{plain}\@thanks
  \endgroup
  \setcounter{footnote}{0}%
  \global\let\thanks\relax
  \global\let\maketitle\relax
  \global\let\@maketitle\relax
  \global\let\@thanks\@empty
  \global\let\@author\@empty
  \global\let\@date\@empty
  \global\let\@title\@empty
  \global\let\title\relax
  \global\let\author\relax
  \global\let\date\relax
  \global\let\and\relax
}
\def\@maketitle{%
  \newpage
  \null
  \vskip 2em%
  \begin{center}%
  \let \footnote \thanks
    {\LARGE \@title \par}%
    \vskip 1.5em%
    {\large
      \lineskip .5em%
      \begin{tabular}[t]{c}%
        \@author
      \end{tabular}\par}%
    \vskip 1em%
    {\large \@date}%
  \end{center}%
  \par
  \vskip 1.5em}
\fi
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
\newcommand\part{%
  \if@openright
    \cleardoublepage
  \else
    \clearpage
  \fi
  \thispagestyle{plain}%
  \if@twocolumn
    \onecolumn
    \@tempswatrue
  \else
    \@tempswafalse
  \fi
  \null\vfil
  \secdef\@part\@spart}

\def\@part[#1]#2{%
    \ifnum \c@secnumdepth >-2\relax
      \refstepcounter{part}%
      \addcontentsline{toc}{part}{\thepart\hspace{1em}#1}%
    \else
      \addcontentsline{toc}{part}{#1}%
    \fi
    \markboth{}{}%
    {\centering
     \interlinepenalty \@M
     \normalfont
     \ifnum \c@secnumdepth >-2\relax
       \huge\bfseries \partname\nobreakspace\thepart
       \par
       \vskip 20\p@
     \fi
     \Huge \bfseries #2\par}%
    \@endpart}
\def\@spart#1{%
    {\centering
     \interlinepenalty \@M
     \normalfont
     \Huge \bfseries #1\par}%
    \@endpart}
\def\@endpart{\vfil\newpage
              \if@twoside
               \if@openright
                \null
                \thispagestyle{empty}%
                \newpage
               \fi
              \fi
              \if@tempswa
                \twocolumn
              \fi}
\newcommand\chapter{\if@openright\cleardoublepage\else\clearpage\fi
                    \thispagestyle{plain}%
                    \global\@topnum\z@
                    \@afterindentfalse
                    \secdef\@chapter\@schapter}
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
\def\@schapter#1{\if@twocolumn
                   \@topnewpage[\@makeschapterhead{#1}]%
                 \else
                   \@makeschapterhead{#1}%
                   \@afterheading
                 \fi}
\def\@makechapterhead#1{%
  \vspace*{22\p@}%
  {\parindent \z@ \raggedright \normalfont
  \ifnum \c@secnumdepth >\m@ne
       \LARGE\bfseries \thechapter\hspace*{20pt}  
       \bfseries #1
       \par\nobreak
    \fi
    \vskip 15\p@
  }}
\def\@makeschapterhead#1{%
  \vspace*{22\p@}%
  {\parindent \z@ \raggedright \normalfont
    \interlinepenalty\@M
    \Large \bfseries  #1\par\nobreak
    \vskip 15\p@
  }}
  %
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
\renewcommand\theenumi{\@arabic\c@enumi}
\renewcommand\theenumii{\@alph\c@enumii}
\renewcommand\theenumiii{\@roman\c@enumiii}
\renewcommand\theenumiv{\@Alph\c@enumiv}
\newcommand\labelenumi{\theenumi.}
\newcommand\labelenumii{(\theenumii)}
\newcommand\labelenumiii{\theenumiii.}
\newcommand\labelenumiv{\theenumiv.}
\renewcommand\p@enumii{\theenumi}
\renewcommand\p@enumiii{\theenumi(\theenumii)}
\renewcommand\p@enumiv{\p@enumiii\theenumiii}
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
\if@titlepage
  \newenvironment{abstract}{%
      \titlepage
      \null\vfil
      \@beginparpenalty\@lowpenalty
      \begin{center}%
        \bfseries \abstractname
        \@endparpenalty\@M
      \end{center}}%
     {\par\vfil\null\endtitlepage}
\else
  \newenvironment{abstract}{%
      \if@twocolumn
        \section*{\abstractname}%
      \else
        \small
        \begin{center}%
          {\bfseries \abstractname\vspace{-.5em}\vspace{\z@}}%
        \end{center}%
        \quotation
      \fi}
      {\if@twocolumn\else\endquotation\fi}
\fi
\newenvironment{verse}
               {\let\\\@centercr
                \list{}{\itemsep      \z@
                        \itemindent   -1.5em%
                        \listparindent\itemindent
                        \rightmargin  \leftmargin
                        \advance\leftmargin 1.5em}%
                \item\relax}
               {\endlist}
\newenvironment{quotation}
               {\list{}{\listparindent 1.5em%
                        \itemindent    \listparindent
                        \rightmargin   \leftmargin
                        \parsep        \z@ \@plus\p@}%
                \item\relax}
               {\endlist}
\newenvironment{quote}
               {\list{}{\rightmargin\leftmargin}%
                \item\relax}
               {\endlist}
\if@compatibility
\newenvironment{titlepage}
    {%
      \if@twocolumn
        \@restonecoltrue\onecolumn
      \else
        \@restonecolfalse\newpage
      \fi
      \thispagestyle{empty}%
      \setcounter{page}\z@
    }%
    {\if@restonecol\twocolumn \else \newpage \fi
    }
\else
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
\fi
\newcommand\appendix{\par
  \setcounter{chapter}{0}%
  \setcounter{section}{0}%
  \gdef\@chapapp{\appendixname}%
  \gdef\thechapter{\@Alph\c@chapter}}
\setlength\arraycolsep{5\p@}
\setlength\tabcolsep{6\p@}
\setlength\arrayrulewidth{.4\p@}
\setlength\doublerulesep{2\p@}
\setlength\tabbingsep{\labelsep}
\skip\@mpfootins = \skip\footins
\setlength\fboxsep{3\p@}
\setlength\fboxrule{.4\p@}
\@addtoreset {equation}{chapter}
\renewcommand\theequation
  {\ifnum \c@chapter>\z@ \thechapter.\fi \@arabic\c@equation}
\newcounter{figure}[chapter]
\renewcommand \thefigure
     {\ifnum \c@chapter>\z@ \thechapter.\fi \@arabic\c@figure}
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
\long\def\@makecaption#1#2{%
  \vskip\abovecaptionskip
  \sbox\@tempboxa{#1: #2}%
  \ifdim \wd\@tempboxa >\hsize
    #1: #2\par
  \else
    \global \@minipagefalse
    \hb@xt@\hsize{\hfil\box\@tempboxa\hfil}%
  \fi
  \vskip\belowcaptionskip}
\DeclareOldFontCommand{\rm}{\normalfont\rmfamily}{\mathrm}
\DeclareOldFontCommand{\sf}{\normalfont\sffamily}{\mathsf}
\DeclareOldFontCommand{\tt}{\normalfont\ttfamily}{\mathtt}
\DeclareOldFontCommand{\bf}{\normalfont\bfseries}{\mathbf}
\DeclareOldFontCommand{\it}{\normalfont\itshape}{\mathit}
\DeclareOldFontCommand{\sl}{\normalfont\slshape}{\@nomath\sl}
\DeclareOldFontCommand{\sc}{\normalfont\scshape}{\@nomath\sc}
\DeclareRobustCommand*\cal{\@fontswitch\relax\mathcal}
\DeclareRobustCommand*\mit{\@fontswitch\relax\mathnormal}
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
\newdimen\bibindent
\setlength\bibindent{1.5em}
\newenvironment{thebibliography}[1]
     {\chapter*{\bibname}%
      \@mkboth{\MakeUppercase\bibname}{\MakeUppercase\bibname}%
      \list{\@biblabel{\@arabic\c@enumiv}}%
           {\settowidth\labelwidth{\@biblabel{#1}}%
            \leftmargin\labelwidth
            \advance\leftmargin\labelsep
            \@openbib@code
            \usecounter{enumiv}%
            \let\p@enumiv\@empty
            \renewcommand\theenumiv{\@arabic\c@enumiv}}%
      \sloppy
      \clubpenalty4000
      \@clubpenalty \clubpenalty
      \widowpenalty4000%
      \sfcode`\.\@m}
     {\def\@noitemerr
       {\@latex@warning{Empty `thebibliography' environment}}%
      \endlist}
\newcommand\newblock{\hskip .11em\@plus.33em\@minus.07em}
\let\@openbib@code\@empty
\newenvironment{theindex}
               {\if@twocolumn
                  \@restonecolfalse
                \else
                  \@restonecoltrue
                \fi
                \twocolumn[\@makeschapterhead{\indexname}]%
                \@mkboth{\MakeUppercase\indexname}%
                        {\MakeUppercase\indexname}%
                \thispagestyle{plain}\parindent\z@
                \parskip\z@ \@plus .3\p@\relax
                \columnseprule \z@
                \columnsep 35\p@
                \let\item\@idxitem}
               {\if@restonecol\onecolumn\else\clearpage\fi}
\newcommand\@idxitem{\par\hangindent 40\p@}
\newcommand\subitem{\@idxitem \hspace*{20\p@}}
\newcommand\subsubitem{\@idxitem \hspace*{30\p@}}
\newcommand\indexspace{\par \vskip 10\p@ \@plus5\p@ \@minus3\p@\relax}
\renewcommand\footnoterule{%
  \kern-3\p@
  \hrule\@width.4\columnwidth
  \kern2.6\p@}
\@addtoreset{footnote}{chapter}
\newcommand\@makefntext[1]{%
    \parindent 1em%
    \noindent
    \hb@xt@1.8em{\hss\@makefnmark}#1}
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
\setlength\columnsep{10\p@}
\setlength\columnseprule{0\p@}
\pagestyle{plain}
\pagenumbering{arabic}
\if@twoside
\else
  \raggedbottom
\fi
\if@twocolumn
  \twocolumn
  \sloppy
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
\newpagestyle{fancy}{
	\headrule
	\sethead{\Author}{}{\MakeUppercase{\chaptertitle}}
	\setfoot{}{\thepage}{}
}
\renewpagestyle{plain}{
	\headrule
	\sethead{\Author}{}{\Course}
	\setfoot{}{\thepage}{}
}
\newpagestyle{nonum}{
	\headrule
	\sethead{\Author}{}{\MakeUppercase{\Course}}
	\footrule
	\setfoot{}{\begin{minipage}[t]{\textwidth}\centering\Title\end{minipage}}{}
}
\tocloftpagestyle{nonum}

% ==============================================================================
% Packages: Figures And Captions
% ==============================================================================
% graphicx[pdftex]: \includegraphics with the pdflatex driver. Also satisfies
%   the class's own use of \includegraphics in \maketitle (CTU logo).
\RequirePackage[pdftex]{graphicx}
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
\RequirePackage{pdfpages}

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
%   \usetikzlibrary{external} and \tikzexternalize are in main.tex because
%   tikzexternalize is a build-behavior directive, not boilerplate.
\RequirePackage{standalone}

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
%   hidelinks: suppress colored boxes; links remain clickable in PDF viewers.
%   Requires 3 full compilations after any cross-reference change to stabilize.
\RequirePackage[hidelinks]{hyperref}

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

% ==============================================================================
% Utility Macro: Concatenate External TeX Files
% ==============================================================================
% \inputAllFiles{dir}: shell-escapes to cat all *.tex files in a directory into
%   a temporary file that is then \input. For the optional Citace appendix.
%   Requires the -shell-escape compiler flag.
%   (No \makeatletter needed — @ is already a letter in class context.)
\def\app@exe{\immediate\write18}
\def\inputAllFiles#1{%
  \app@exe{ls #1/*.tex | xargs cat >> \jobname.tmp}%
  \InputIfFileExists{\jobname.tmp}{}
  \AtEndDocument{\app@exe{rm -f #1/\jobname.tmp}}}

\endinput
%%
%% End of file `CTUthesis.cls'.
