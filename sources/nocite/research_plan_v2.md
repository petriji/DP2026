# Výzkumný a argumentační plán DP — verze 2
## Sociální dialog a kolektivní vyjednávání
### Petříček Jiří | MÚVS ČVUT | PRI | aktualizace: 2026-04-06

---

## GLOBÁLNÍ INSTRUKCE PRO CELOU PRÁCI

### Jazykový styl — pasivní forma
Veškerý český text se píše v **pasivních nebo neosobních konstrukcích**, ve stylu vědecké
práce.  Vzor: viz `templates/dev/texparts/analyza_fs_postup.tex`,
`adaptivni.tex`, `aliasing.tex`.
Příklady správné formy:
- „Je navržen postup…" (ne „Navrhuji postup…")
- „Data jsou čerpána z Eurostatu…" (ne „Čerpám data z Eurostatu…")
- „Bylo zjištěno, že…" (ne „Zjistil jsem, že…")
- „Lze konstatovat, že…"
- „Z grafu je patrné, že…"
- „Hodnota ukazatele dosahuje…"

### Modulární struktura — \\input pro každou myšlenku
Každá logická jednotka (odstavec tematicky uceleného textu, každý obrázek s popiskem,
každá tabulka) žije ve **vlastním `.tex` souboru** ve `texparts/`.  Struktura kapitoly
v `main.tex` je tak pouze kostra `\\input{}` volání.
Pojmenování: `texparts/<kapitola>/<tema>.tex`, např.:
  - `texparts/teorie/pojmy_zakladni.tex`
  - `texparts/teorie/legislativa_zp_24.tex`
  - `texparts/python/union_density_trend.tex`   ← figure+caption
  - `texparts/stav/ai_automatizace.tex`
  - `texparts/penny/pluralita_os.tex`
Pravidlo pro figure moduly: jeden `.tex` soubor obsahuje figure prostředí + caption +
label + krátký výkladový odstavec.  Příklad:
```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.92\linewidth]{../pics/python/union_density_trend}
  \caption{\centering Vývoj odborové hustoty ve vybraných zemích, 1990--2023.
           \cite{oecd_aias_ictwss}}
  \label{fig:union_density_trend}
\end{figure}
Z obrázku~\ref{fig:union_density_trend} je patrné, že …
```

### Matematický popis výpočtů proměnných
V sekci **Zpracování dat** (sec:datova_analyza) je povinný formální matematický popis
každé proměnné odvozené z dat.  Vzor ze šablony (analyza_fs_postup.tex — vzorce ARMAX):
```latex
\begin{equation}
  w_i = \frac{x_i^{\mathrm{PPS}}}{x_{\mathrm{EU27}}^{\mathrm{PPS}}} \cdot 100
  \label{eq:pps_index}
\end{equation}
kde $x_i^{\mathrm{PPS}}$ je hodnota ukazatele pro zemi~$i$ vyjádřená v paritě kupní
síly (PPS) a $x_{\mathrm{EU27}}^{\mathrm{PPS}}$ je průměr EU-27.
```
Každý vypočtený ukazatel musí mít: (a) slovní definici, (b) vzorec s LaTeX eq, (c) odkaz
na zdrojový datový soubor v `python/data/` a (d) citaci primárního zdroje dat.

### Ověření dat
Před finálním textem ke každé číselné hodnotě: ověřit v primárním zdroji (URL Eurostat/ILO),
uvést rok pozorování a verzi datasetu (datum stažení).  Formát: `\cite{klic}` + poznámka
s URL přímo v .bib záznamu (pole `url` + `urldate`).

### Analytické výstupy (Python) — nejsou povinné
Existující figury v `pics/python/` slouží jako **ilustrativní příklady**.  Není nutné
použít všechny.  Každá figura musí být zapojena argumentačně — pokud nepodporuje žádný
argument v textu, nepoužívat ji.  Případně nahradit tabulkou nebo odkazem na zdroj.

### Oponování hypotézy
V sekci **Hodnocení sociálního dialogu v ČR** (sec:hodnoceni) je záměrně strukturována
argumentace tak, aby nejprve byly prezentovány **protiargumenty** (nízké AROPE, vysoká
zaměstnanost ~81,7 %, mzdový růst 2024 +7,1 %, reálný růst +4,6 %) a teprve jejich
systematické vyvrácení daty (relativita AROPE hranic, produktivitní mezera, délka prac.
doby, nízká APZ) vede k potvrzení hypotézy.  Styl: akademická skepse, ne apologetika.

### Přerušení po každé kapitole
Po dokončení každé kapitoly / sekce: **zkompilovat** (`latexmk -pdf main.tex`), zkontrolovat
výstup PDF, provést git commit s popisnou zprávou, teprve poté pokračovat.
Příkaz: `cd latex && latexmk -pdf main.tex 2>&1 | grep -iE "Fatal|error" | head -10`

---

## DOSTUPNÉ ZDROJE — POUZE TYTO CITOVAT V BIBLATEX

### Fyzicky dostupné (v /sources nebo /templates):

#### Monografie a kapitoly
| Klíč (navrhovaný) | Soubor | Poznámka |
|---|---|---|
| `armstrong_hrm_2023` | `sources/A Handbook of HRM Practices - Michael Armstrong.pdf` | kap. collective bargaining |
| `cmkos_historie_2020` | `sources/Historie-odbory-a-spolecnost.pdf` | dějiny odborů |
| `mop_100let_2019` | `sources/100-let-MOP.pdf` | ILO 100 let |
| `cmkos_zprava_kv_2025` | `sources/8d_ČMKOS_Zpráva o průběhu kolektivního vyjednávání…2025.pdf` | stěžejní zdroj dat |
| `ks_penny_2026` | `sources/KS Penny Market na rok 2026_20260324124317.pdf` | případová studie |
| `Hala_SystemySocialnihoDialogu2013` | `sources/VZ361_Systemy_socialniho_dialogu_Hala_2013.pdf` | **KLÍČOVÝ KOMPARATIVNÍ ZDROJ** — 7 zemí EU, srovnávací tabulka, Německo, Rakousko, Slovensko, VB |

#### Články (dostupné PDF):
| Klíč | Soubor |
|---|---|
| `HRMcross2024` | `sources/Corp Soc Responsibility Env - 2024 - Wojtczuk-Turek…pdf` |
| `dvorakova_active_emp` | `sources/ActiveEmploymentPolicyCzechia.pdf` |
| `dvorakova_demograficke` | `sources/ZBORNKPRSPEVKOV_Obchodamarketing_2025-30-48.pdf` |
| `polents_ukrainian_refugees` | `sources/AnalysisofprospectsandproblemsinthedevelopmentofhumanresourcesfortheemploymentofUkrainianrefugees.pdf` |

#### Vlastní předchozí práce (nocite — NESMÍ být citovány v BibLaTeX, slouží jen jako zdroj argumentů a dat):
| Soubor | Obsah |
|---|---|
| `sources/nocite/PETRICEK_HOPO_Flexicurity.pdf` | Flexicurity paper — základ pro kap. flexicurity |
| `sources/nocite/PETRICEK_IND4_1IndustrialRevolution.pdf` | Průmysl 4.0 — základ hist. analogie |
| `sources/nocite/Diplomova prace Pastikova Iva 2024.pdf` | Vzor struktury DP u stejné vedoucí |
| `sources/nocite/MU-DP-2025-Jirous-Vojtech-DP_Jirous.pdf` | Vzor struktury DP u stejné vedoucí |
| `templates/dev/texparts/*.tex` | Vzor akademického stylu (pasivní forma, vzorce) |

> ⚠️ Klíče z nocite souborů **NIKDY** nedávat do `.bib` souborů.  Argumenty z nich
> přepsat do vlastního textu a podložit jiným dostupným zdrojem.

#### Eurostat datasety (BibLaTeX záznamy už jsou v socialnidialog.bib):
Klíče: `eurostat_ilc_peps01n`, `eurostat_nama_10_pc`, `eurostat_earn_nt_taxwedge`,
`eurostat_ilc_di12`, `eurostat_lfsi_emp_a`, `eurostat_lfsa_ewhun2`,
`eurostat_demo_pjanind`, `eurostat_prc_ppp_ind`, `etui_cba`

#### Záznamy k brzkému vytvoření (přidat do socialnidialog.bib nebo -zotero.bib):
```bibtex
@book{Hala_SystemySocialnihoDialogu2013,
  author    = {Hála, Jaroslav and Čambáliková, Monika and Pfeiferová, Štěpánka and Píšl, Radek and Vácha, Jan and Veverková, Soňa},
  title     = {Systémy sociálního dialogu se zaměřením na zaměstnavatelskou sféru ve vybraných zemích EU},
  year      = {2013},
  publisher = {VÚPSV, v.v.i.},
  address   = {Praha},
  isbn      = {978-80-7416-126-1},
  langid    = {czech},
  note      = {451. publikace VÚPSV; recenzenti: JUDr. Dana Hrabcová, Ph.D.; prof. Ing. Zuzana Dvořáková, CSc. Soubor: sources/VZ361\_Systemy\_socialniho\_dialogu\_Hala\_2013.pdf},
}

@book{cmkos_historie_2020,
  author    = {{ČMKOS}},
  title     = {Historie, odbory a společnost: cesta k lepší budoucnosti},
  year      = {2020},
  publisher = {ČMKOS},
  langid    = {czech},
  note      = {Soubor: sources/Historie-odbory-a-spolecnost.pdf},
}

@book{mop_100let_2019,
  author    = {Pokorný, Pavel and others},
  title     = {100 let Mezinárodní organizace práce},
  year      = {2019},
  publisher = {ČMKOS},
  langid    = {czech},
  note      = {Soubor: sources/100-let-MOP.pdf},
}

@report{cmkos_zprava_kv_2025,
  author      = {{ČMKOS}},
  title       = {Zpráva o průběhu kolektivního vyjednávání na vyšším stupni
                 a na podnikové úrovni v roce 2025},
  year        = {2026},
  institution = {ČMKOS},
  langid      = {czech},
  note        = {Předložena Radě ČMKOS 11.~3.~2026. Soubor: sources/8d\_ČMKOS\_Zpráva…},
}

@misc{ks_penny_2026,
  author  = {{ASO-ČR} and {OSPZV-ASO ČR}},
  title   = {Kolektivní smlouva Penny Market, s.\,r.\,o. na období 1.\,1.\,2026 --
             31.\,12.\,2026},
  year    = {2026},
  note    = {Soubor: sources/KS Penny Market na rok 2026\_20260324124317.pdf},
  langid  = {czech},
  url     = {https://www.ospzv-aso.cz/obsah/82/kolektivni-smlouva-s-penny-market-sro-na-rok-2026/337434},
  urldate = {2026-03-24},
}

@book{armstrong_hrm_2023,
  author    = {Armstrong, Michael and Taylor, Stephen},
  title     = {Armstrong's Handbook of Human Resource Management Practice},
  edition   = {16},
  year      = {2023},
  publisher = {Kogan Page},
  langid    = {english},
  note      = {Soubor: sources/A Handbook of HRM Practices - Michael Armstrong.pdf},
}

@online{zakonik_prace_2026,
  author  = {{Česká republika}},
  title   = {Zákon č.\,262/2006\,Sb., zákoník práce, znění od 1.\,1.\,2026},
  year    = {2026},
  url     = {https://www.zakonyprolidi.cz/cs/2006-262},
  urldate = {2026-04-02},
  langid  = {czech},
}

@online{zakon_kv_2026,
  author  = {{Česká republika}},
  title   = {Zákon č.\,2/1991\,Sb., o kolektivním vyjednávání, znění od 1.\,1.\,2026},
  year    = {2026},
  url     = {https://www.zakonyprolidi.cz/cs/1991-2},
  urldate = {2026-04-02},
  langid  = {czech},
}
```

> Po vytvoření těchto záznamů: spustit `latexmk` a ověřit, že nejsou `undefined reference`
> varování v `.blg` logu.

---

## PRIORITNÍ POŘADÍ PRÁCE

### Fáze 1 — Informační souhrn (pracovat první)
1. **2.2 Historický vývoj** — text z dostupných hist. zdrojů, bez analýzy dat
2. **2.1 Pojmy a legislativa** — definice, zákonné rámce
3. **3.3 Případová studie Penny Market** — analýza KS, srovnání se zákonným minimem
4. **3.2.1 Flexicurity** — syntetizovat z PETRICEK_HOPO (bez přímé citace), Armstrong, Dvořáková
5. **3.2.2 Srovnávací přehled 7 zemí** — zejména z `\parencite{Hala_SystemySocialnihoDialogu2013}` [klíčový!]

### Fáze 2 — Analytická část
5. **3.1 Výhled** — problémy CZ trhu práce (subsekce viz níže)
6. **3.2 Evropský kontext** — obalit existující figury interpretačním textem
7. **1 Úvod** + **3 Postup výzkumu / Zpracování dat** — po zvládnutí obsahu lze formulovat přesněji

### Fáze 3 — Evaluace a inovace
8. **3.4 Hodnocení SD v ČR** — SWOT + oponování hypotézy
9. **4 Návrh inovace**
10. **Závěr**

---

## ROZŠÍŘENÁ STRUKTURU SEKCE / SUBSEKCE

### Kap. 2.1 Pojmy a vztahy (navrhnout rozdělení na \\subsection nebo \\paragraph):
- `\subsection{Základní pojmy}` — SD, KV, KS, sociální partneři
- `\subsection{Legislativní rámec v ČR}` — ZP §§ 24–29, zákon 2/1991 §§ 1–10
  - `\paragraph{Pluralita odborových organizací (§ 24 ZP)}` — efekt na sílu KV
  - `\paragraph{Rozšiřování závaznosti KSVS (§ 7 zákona 2/1991)}` — mezera CZ vs. AT
- `\subsection{Mezinárodní rámec}` — ILO Conventions 87+98, EU Social Charter
- `\subsection{Ukazatele kvality sociálního dialogu}` — hustota odborů vs. pokrytí KV (odlišit!)

### Kap. 2.2 Historický vývoj:
- `\subsection{Vznik odborového hnutí — industrializace}`
- `\subsection{ILO a meziválečné období}`
- `\subsection{Odbory v Československu — ROH a komunistická deformace}`
- `\subsection{Transformace po roce 1989}`
- `\subsection{Průmysl 4.0 a AI}` — analogie s 19. stol.

### Kap. 3.1 Výhled — faktorová analýza (každý faktor = `\paragraph` nebo `\subsubsection`):
- `\subsection{Technologické změny}` — rozdíl: automatizace průmyslová (drahá, pomalá)
   vs. AI kancelářská (levná, rychlá) → eliminace junior pozic
- `\subsection{Demografické tlaky}` — stárnutí, old-age dependency ratio
- `\subsection{Migrace z Ukrajiny}` — integrace, nejistota výhledu
- `\subsection{Pracovní mobilita a brain drain}`
- `\subsection{OSVČ a švarc systém}` — daňová asymetrie (viz P5 Python analýza)
- `\subsection{Veřejný sektor}` — mzdová zaostalost, důsledky
- `\subsection{Agenturní zaměstnávání}`

### Kap. 3.2.2 Porovnání s dalšími modely (každý model `\subsection`):
- `\subsection{Rakouský model}` — Kammer-system, 98 % KV, ÖGB
- `\subsection{Německý model}` — Mitbestimmung, korporátní spolurozhodování, Hartz
- `\subsection{Polský a slovenský model}` — komparativní post-sovětský pohled

> 📚 **KLÍČOVÝ ZDROJ PRO KAP. 3.2 (i pro 2.1 a závěr):** `\parencite{Hala_SystemySocialnihoDialogu2013}`
> = Hála et al. (2013) *Systémy sociálního dialogu*, VÚPSV 2013, 372 s., recenz. Dvořáková.
> Podrobný transkript: `sources/scrape/Hala_VZ361_TRANSCRIPT.md`
>
> Použít zejména:
> - Srovnávací tabulku (s. 228–229) jako základ kap. 3.2 — pokrytí KS, odborová hustota, tripartita 7 zemí
> - Závěr (s. 286–288) pozn. 537: „...obdobně se to týká i dalších postkomunistických zemí včetně ČR" → přímá opora hypotézy
> - Úvod: Eurofound jako primární datový zdroj systémů SD v Evropě
> - Kap. I: definice SD (ILO), trend decentralizace, EU average CB coverage 66 %
> - „každý národní systém odráží specifické historické zkušenosti" (s. 287) — citovat v kap. 3.2 nebo závěru


### Kap. 3.3 Případová studie — Penny Market:
- `\subsection{Metodika případové studie}`
- `\subsection{Rozbor pracovněprávních podmínek KS 2026}` — systematické body
   `\paragraph{Pracovní doba}`, `\paragraph{Přesčasová práce}`, `\paragraph{Dovolená}`,
   `\paragraph{Odměňování}`, `\paragraph{Odborové organizace (pluralita)}`
- `\subsection{Srovnání s průměrem PKS v ČR}` — ČMKOS benchmarks
- `\subsection{Top Employer 2026 a role odborů v PR komunikaci}` — chybějící zmínka
- `\subsection{Paralela s modelem HR Business Partnera}`

### Kap. 3.4 Hodnocení:
- `\subsection{SWOT analýza sociálního dialogu v ČR}`
- `\subsection{Argumenty zpochybňující hypotézu}` — prezentovat poctivě protiargumenty
- `\subsection{Analytická konfrontace s daty}` — systematické vyvrácení protiargumentů
- `\subsection{Korelační analýza}` — hustota × GINI, pokrytí × pracovní hodiny
- `\subsection{Závěr: hodnocení hypotézy}`

---

## MATEMATICKÝ POPIS VÝPOČTŮ PROMĚNNÝCH (sekce Zpracování dat)

Každá proměnná použitá v analýzách musí být popsána:

### Příklady povinných vzorců:

**Index HDP v PPS (EU27 = 100):**
```latex
\begin{equation}
  g_i = \frac{\mathrm{HDP}_i^{\mathrm{PPS}}}{\overline{\mathrm{HDP}}_{\mathrm{EU27}}^{\mathrm{PPS}}} \cdot 100
\end{equation}
```
Zdroj dat: `python/data/A.PC_EU27_2020_HAB_MPPS_CP.B1GQ_*.csv` \cite{eurostat_nama_10_pc}

**Daňový klín (tax wedge, % labour cost):**
```latex
\begin{equation}
  \tau_i = \frac{T_i + S_i^{\mathrm{emp}} + S_i^{\mathrm{er}}}{w_i + S_i^{\mathrm{er}}}
\end{equation}
```
kde $T_i$ = osobní důchodová daň, $S_i^{\mathrm{emp}}$ = pojistné zaměstnance,
$S_i^{\mathrm{er}}$ = pojistné zaměstnavatele, $w_i$ = hrubá mzda.
Zdroj dat: `python/data/earn_nt_taxwedge_*.csv` \cite{eurostat_earn_nt_taxwedge}

**AROPE (definice):**
```latex
\begin{equation}
  \mathrm{AROPE}_i = \mathbf{1}\bigl[\mathrm{AROP}_i \cup \mathrm{SMD}_i \cup \mathrm{VLWI}_i\bigr]
\end{equation}
```
kde AROP = at risk of poverty, SMD = severe material deprivation, VLWI = very low work intensity.
Zdroj: \cite{eurostat_ilc_peps01n}

---

## OPONOVÁNÍ HYPOTÉZY — INSTRUKCE PRO SEC:HODNOCENI

Strukturovat jako:

1. **Protiargumenty k hypotéze** (uvést poctivě):
   - CZ AROPE = 12 % (nejnižší ze skupiny) — lze namítnout: slabý SD nezpůsobuje chudobu
   - Zaměstnanost 81,7 % — vysoká i bez silného SD
   - Reálný mzdový růst 2024 = +4,6 % — mzdy rostou i bez SD
   - GINI = 24,4 — nízká nerovnost → SD nemusí být nutný

2. **Systematické vyvrácení**:
   - AROPE hranice jsou **relativní** (60 % mediánu národního příjmu) → CZ nízké příjmy
     jsou méně koncentrované, ale absolutně nízké; srovnání v PPS ukazuje jiný obraz
   - Mzdový podíl HDP (wage share): CZ 27,8 % (ČMKOS 2025, str. 10) — nízký
   - Délka prac. týdne 39,6 h → zaměstnanec pracuje déle za méně v PPS
   - Produktivita práce +0,7 % vs. reálná mzda +4,6 % v 2024 → jednorázový dohon po
     inflaci; structural gap trvá
   - APZ výdaje: CZ ~0,3 % HDP vs. DK ~2 % → bez rekvalifikační kapacity je
     adaptabilita trhu závislá jen na mzdové deflaci (race to the bottom)

3. **Závěr**: Data přesvědčí — hypotéza potvrzena.

---

## KONTROLNÍ SEZNAM PO KAŽDÉ KAPITOLE

Po dokončení každé kapitoly/sekce provést (v tomto pořadí):
1. `cd latex && latexmk -pdf main.tex` — zkontrolovat nulový počet fatálních chyb
2. `.blg` log — ověřit, že nejsou `undefined citation` varování
3. PDF vizuální kontrola — zalamování, přetečení, správné obrázky
4. `git add -A && git commit -m "feat(kap.X): dokončena sekce Y"` — konkrétní popis
5. Teprve poté pokračovat na další kapitolu

---

## POZNÁMKY K EXISTUJÍCÍM PYTHON VÝSTUPŮM

Figury v `pics/python/` jsou **volitelné**.  Každá, která je zahrnuta, musí:
- mít vlastní `.tex` modul v `texparts/python/<nazev>.tex`
- být v textu zmíněna a interpretována (ne jen vložena)
- mít v caption odkaz `\cite{}` na primární datový zdroj

Pokud figura dostatečně neposiluje argument, **nahradit ji tabulkou** nebo ji vynechat.
Alternativa k `arope_groups.pdf` nebo `arope_timeline_CE.pdf`: citovat ČMKOS/Eurostat
přímo v textu bez figury — přijatelné.