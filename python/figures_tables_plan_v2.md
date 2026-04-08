# Plán figur a tabulek — DP Sociální dialog a KV
Jiří Petříček | MÚVS ČVUT | PRI | verze 2 | 2026-04-07
Nahrazuje figures_tables_plan.md (v1, 2026-04-06).

Kapitolové reference odpovídají labelům v latex/main.tex.

---

## Legenda — stav figury

- existuje     — soubor v pics/python/ nebo texparts/python/ je hotový
- python       — data existují v python/data/; Python skript nutno napsat/spustit
- stáhnout     — data nutno stáhnout, poté python
- volitelné    — zahrnout dle potřeby a kapacity

---

## Pravidlo volby typu vizualizace

Pokud pro daný indikátor existuje zajímavý trend (výrazný vzestup, pokles, konvergence),
zvolit timeline jako primární figuru. Pokud trend chybí nebo jsou nedostatečná časová data,
zvolit choropleth jako primární.

Příklady:
- A.6: odborová hustota CZ poklesla z 80 % (1990) na 11 % (2024) — timeline je primární (A.6a).
- A.9: APZ výdaje CZ stagnují ~0,3 % bez trendu — choropleth je primární (A.9a).
- A.16: příjmový Gini CZ stabilní 2003–2023 — timeline pro srovnání zemí (ne CZ trend).
- A.18: wealth Gini CZ +15,1 bodu za 13 let — timeline je primární (A.18a).

---

## A. Figury

### A.1 [existuje] HDP na obyvatele v PPS — timeline (6 zemí)
- Soubor:    pics/python/gdp_ppp_timeline.pdf
- LaTeX:     texparts/python/gdp_ppp_timeline.tex
- Typ:       časový graf, DK/CZ/DE/AT/PL/SK, 2000–2024
- Data:      Eurostat nama_10_pc (GDP per capita in PPS, EU27=100)
- CSV:       python/data/A.PC_EU27_2020_HAB_MPPS_CP.B1GQ_*.csv
- Kapitola:  sec:evropsky_kontext
- Argument:  CZ konverguje k EU průměru pomalým tempem; AT/DE stabilně nad 100

### A.2 [existuje] Daňový klín — choropleth mapa EU
- Soubor:    pics/python/tax_wedge_map.pdf
- LaTeX:     texparts/python/tax_wedge_map.tex
- Typ:       choropleth mapa EU
- Data:      Eurostat earn_nt_taxwedge
- CSV:       python/data/earn_nt_taxwedge_94b1ee6b.csv
- Kapitola:  sec:evropsky_kontext
- Argument:  CZ daňový klín 38,1 % — nad DK (33,5 %), pod DE (43,5 %)

### A.3 [existuje] AROPE — choropleth mapa EU — protiargument kap. 3.5
- Soubor:    pics/python/arope_map_2025.pdf
- LaTeX:     texparts/python/arope_map_2025.tex
- Typ:       choropleth mapa EU, AROPE rate
- Data:      Eurostat ilc_peps01n
- Kapitola:  sec:hodnoceni (protiargument — „v ČR je nízká chudoba, SD není potřeba")
- Argument:  CZ 12 % = nejnižší v EU; avšak relativní definice (60 % mediánu) →
             nízké absolutní příjmy v PPS; vyvrátit systematickým srovnáním PPS
- Poznámka:  Nepoužívat jako hlavní analytický nástroj. Pouze pro oponování protiargumentu.

### A.4 [existuje] AROPE timeline CE — doplněk k A.3
- Soubor:    pics/python/arope_timeline_CE.pdf
- LaTeX:     texparts/python/arope_timeline_CE.tex
- Kapitola:  ssec:flexicurity
- Účel:      Historický vývoj AROPE ve střední Evropě

### A.5 [existuje] AROPE skupiny — doplněk
- Soubor:    pics/python/arope_groups.pdf
- LaTeX:     texparts/python/arope_groups.tex
- Kapitola:  ssec:flexicurity

### A.6a [stáhnout] Odborová hustota — timeline (6 zemí, 1990–2024)
- Navrhovaný soubor: pics/python/union_density_timeline.pdf
- Typ:       čárový graf, DK/CZ/DE/AT/PL/SK, 1990–2024
- Data:      OECD AIAS ICTWSS (Trade Union Density); alternativa: ILOSTAT TUR, ETUI
- URL:       https://stats.oecd.org → Industrial Relations → Trade Union Density
- Kapitola:  sec:historie (historický vývoj), sec:evropsky_kontext (srovnání), sec:hodnoceni
- Argument:  Dramatický pokles CZ z ~80 % (1990) na 11 % (2024); DK stabilně nad 60 %

### A.6b [stáhnout] Odborová hustota — choropleth mapa EU (aktuální rok)
- Navrhovaný soubor: pics/python/union_density_map.pdf
- Typ:       choropleth mapa EU
- Data:      OECD AIAS ICTWSS; alternativa: ETUI
- Kapitola:  sec:evropsky_kontext (příčný řez), sec:hodnoceni
- Argument:  Geografický vzorec: severské/Ghent státy vysoko, V4 nízko

### A.7 [stáhnout] Pokrytí kolektivním vyjednáváním — choropleth mapa EU
- Navrhovaný soubor: pics/python/kv_coverage_map.pdf
- Typ:       choropleth mapa EU, adjusted CB coverage (%)
- Data:      OECD AIAS ICTWSS (Adjusted CB Coverage); ETUI
- Instituce CZ: CMKOS Zprava o KV 2025 → 32 %
- Instituce komparace: AT 98 % (WKÖ/ÖGB); DE 52 % (WSI Tarifarchiv); DK 80 % (DA/FH)
- Kapitola:  sec:pojmy (rozšiřování KSVS), sec:evropsky_kontext, sec:hodnoceni
- Argument:  CZ 32 % hluboko pod AT (98 %) a DK (80 %) → nedostatečné pokrytí

### A.8 [stáhnout] Mzdová konvergence vs. HDP konvergence — dual-axis timeline
- Navrhovaný soubor: pics/python/wage_gdp_convergence.pdf
- Typ:       dual-axis čárový graf, CZ/DE/AT, 1995–2024
- Data GDP:  Eurostat nama_10_pc (existuje v python/data/)
- Data mzdy: Eurostat earn_ses_pub1a nebo nama_10_lp_ulc; alternativa: OECD Average Wages;
             MPSV RSCP (Regionální statistika ceny práce) pro CZ regionální detajl
- Citace RSCP: https://www.mpsv.cz/web/cz/statisticky-informacni-system
- Kapitola:  sec:evropsky_kontext, sec:hodnoceni
- Argument:  HDP CZ konverguje k EU průměru rychleji než mzdy → cheap labour trap
- main.tex:  % \input{texparts/python/wage_gdp_convergence} % TODO

### A.9a [stáhnout] APZ výdaje (% HDP) — choropleth mapa EU
- Navrhovaný soubor: pics/python/lmp_expenditure_map.pdf
- Typ:       choropleth mapa EU, LMP expenditure % GDP
- Data:      Eurostat lmp_ind_exp nebo lmp_expsumm
- Kapitola:  ssec:flexicurity, sec:vyhled
- Argument:  CZ ~0,3 % HDP vs. DK ~2 % → CZ nemá rekvalifikační kapacitu
- main.tex:  % \input{texparts/python/lmp_expenditure} % TODO

### A.9b [stáhnout] APZ výdaje (% HDP) — timeline (6 zemí)
- Navrhovaný soubor: pics/python/lmp_expenditure_timeline.pdf
- Typ:       čárový graf, DK/CZ/DE/AT/PL/SK, 2005–2024
- Data:      Eurostat lmp_ind_exp (stejná data jako A.9a)
- Kapitola:  ssec:flexicurity, sec:vyhled
- Argument:  Zjistit, zda CZ konverguje; DK stabilně ~2 %

### A.10 [stáhnout] Scatter: pokrytí KV × čistý příjem v PPS (EU27)
- Navrhovaný soubor: pics/python/coverage_income_pps_scatter.pdf
- Typ:       scatter plot s regresní přímkou, 27 bodů (EU státy)
- Data X:    OECD AIAS ICTWSS — adjusted CB coverage
- Data Y:    Eurostat earn_nt_net (net earnings) v PPS nebo GDP per capita v PPS
- Kapitola:  sec:hodnoceni (korelační analýza)
- Argument:  Pozitivní korelace → vyšší pokrytí KV = vyšší čistý příjem v PPS

### A.11 [stáhnout] Podíl OSVČ — choropleth mapa EU
- Navrhovaný soubor: pics/python/self_employment_map.pdf
- Typ:       choropleth mapa EU, % zaměstnanosti
- Data:      Eurostat lfst_pganws nebo lfsa_esgan
- Kapitola:  sec:vyhled (OSVČ a Švarc)
- Argument:  CZ nadprůměrné % OSVČ → erodování odvodové základny

### A.12 [python] Old-age dependency ratio — choropleth mapa EU
- Navrhovaný soubor: pics/python/old_age_dependency_map.pdf
- Typ:       choropleth mapa EU
- Data:      Eurostat demo_pjanind, TPS00198
- CSV:       python/data/A.OLDDEP1_6dc9b0e3.csv
- Kapitola:  sec:vyhled (demografický tlak)
- Argument:  Stárnutí → tlak na sociální systém; zvyšuje důležitost APZ

### A.13 [python] Zaměstnanost (20–64) — timeline (6 zemí)
- Navrhovaný soubor: pics/python/employment_rate_timeline.pdf
- Typ:       čárový graf, 6 zemí, 2000–2024
- Data:      Eurostat lfsi_emp_a
- CSV:       python/data/A.EMP_LFS.T.Y20-64.PC_POP_945e8bea.csv
- Kapitola:  sec:evropsky_kontext, sec:hodnoceni (protiargument: vysoká zaměstnanost)
- Argument:  CZ 81,7 % — vysoká i bez silného SD → protiargument k vyvrácení

### A.14 [python] Efektivní zdanění OSVČ vs. zaměstnanec (CZ) — legislativní výpočet
- Navrhovaný soubor: pics/python/tax_osvc_vs_employee.pdf
- Typ:       čárový/plošný graf, efektivní odvody % hrubého příjmu (0–300K Kč/měs)
- Data:      Výpočet ze zákonného stavu k 1. 1. 2026 (ZDP §§ 2a/7/7a, NV sazby ČSSZ/VZP)
- Kapitola:  sec:vyhled (OSVČ/Švarc), sec:pojmy (ZDP)
- Argument:  OSVČ s výdajovým paušálem 80 % odvádí výrazně méně → daňová nespravedlnost

### A.15 [python] Příjem na obyvatele v PPS — choropleth mapa EU
- Navrhovaný soubor: pics/python/income_pps_map.pdf
- Typ:       choropleth mapa EU, GDP per capita v PPS (EU27=100)
- Data:      Eurostat nama_10_pc nebo earn_nt_net
- CSV:       python/data/A.PC_EU27_2020_HAB_MPPS_CP.B1GQ_*.csv (existuje)
- Kapitola:  sec:evropsky_kontext
- Argument:  Reálná kupní síla napříč EU; CZ pod průměrem, AT/DE/DK nad

### A.16 [python] Příjmový GINI — timeline (6 zemí, 2003–2023) — protiargument kap. 3.5
- Navrhovaný soubor: pics/python/gini_income_timeline.pdf
- Typ:       čárový graf, CZ/AT/DE/DK/PL/SK, 2003–2023
- Data:      Eurostat ilc_di12 (Gini coefficient of equivalised disposable income)
- CSV:       python/data/A.TOTAL.GINI_HND_45503ce0.csv
- Kapitola:  sec:hodnoceni (protiargument — nízká nerovnost CZ; vyvrátit A.17+A.18)
- Argument:  CZ příjmový GINI ~24,4 = jeden z nejnižších v EU; dlouhodobě stabilní.
             Protiargument: (a) nízký při nízkém mediánu = rovnost v chudobě,
             (b) maskuje majetkovou nerovnost → viz A.18, (c) trend neznamená zásluhu SD
- Poznámka:  Timeline, ne choropleth — srovnání trendu přes roky je průkaznější
             pro oponování hypotézy. Viz nerovnost_CZ.md pro detailní data.

### A.17 [stáhnout] Scatter: odborová hustota / pokrytí KV × příjmový GINI — EU27 panel
- Navrhovaný soubor: pics/python/union_gini_scatter.pdf
- Typ:       scatter plot s regresní přímkou; 27 bodů (EU státy), 1 rok
- Data X:    Odborová hustota nebo adjusted CB coverage (OECD AIAS ICTWSS / ETUI)
- Data Y:    Příjmový GINI (Eurostat ilc_di12)
- Kapitola:  sec:hodnoceni (korelační analýza — Pilíř 3 hypotézy)
- Argument:  Negativní korelace: silnější SD → nižší příjmová nerovnost (EU průřez)
- Pozor:     CZ je outlier — nízký GINI + slabý SD = historický artefakt; musí být
             vysvětlen v textu. SK podobný outlier. Outlieři mohou být zvýrazněni.
- main.tex:  % \input{texparts/python/union_gini_scatter} % TODO

### A.18a [stáhnout] Wealth GINI — timeline (CZ + referenční země, 2008–2021)
- Navrhovaný soubor: pics/python/gini_wealth_timeline.pdf
- Typ:       čárový graf, dostupné roky (2008, 2018, 2019, 2021) pro CZ; srovnání AT/DE/DK/SK
- Data:      Credit Suisse / UBS Global Wealth Databook, tabulka 3-1
             — nutno stáhnout PDF a extrahovat tabulku
- URL:       https://www.ubs.com/global/en/wealth-management/global-wealth-report.html
- Kapitola:  sec:hodnoceni (oligarchizace — argument PRO posílení SD)
- Argument:  CZ nárůst 62,6 → 77,7 (2008–2021) = +15,1 bodu, jeden z nejvyšších v EU.
             Dramatický trend kontrastující se stabilitou příjmového GINI (A.16).
             Viz nerovnost_CZ.md pro přehled dat.
- Klíčová data 2021: CZ 77,7 | SK 50,3 | AT 74,5 | DE 77,9 | DK 73,6 | SE 87,2

### A.18b [stáhnout] Wealth GINI — choropleth mapa EU (2021) — doplněk k A.18a
- Navrhovaný soubor: pics/python/gini_wealth_map.pdf
- Typ:       choropleth mapa EU
- Data:      Stejná jako A.18a (UBS/Credit Suisse Databook 2021)
- Kapitola:  sec:hodnoceni
- Poznámka:  Volitelný doplněk k Timeline A.18a; obsáhne geografický vzorec

### A.20 [stáhnout] Genderový mzdový gap — within-sector srovnání (RSCP/ISPV)
- Navrhovaný soubor: pics/python/gender_pay_gap_by_sector.pdf
- Typ:       grouped bar chart — průměrný hrubý měsíční výdělek mužů vs. žen,
             vodorovná osa = NACE sektory, svislá = Kč/měsíc (+ GPG % jako popisek)
- Data:      MPSV ISPV — tabulka průměrný hrubý měsíční výdělek × pohlaví × NACE sekce
             + počty zaměstnanců × pohlaví × NACE (pro filtrování dle podílu žen 40–60 %)
- URL:       https://www.mpsv.cz/web/cz/statisticky-informacni-system (záložka ISPV)
- Výběr sektorů (podíl žen 40–60 % dle ISPV, tj. sektory bez silné segregace):
  NACE G (maloobchod ~52 %), NACE I (ubytování ~55 %), NACE K (finance ~55 %),
  NACE O (veřejná správa ~56 %), NACE M (profesní služby ~47 %)
  Vyloučit: NACE J (ICT ~20 % žen), NACE Q (zdravotnictví ~80 % žen)
- Doplněk:   Referenční linie: Eurostat adjusted GPG CZ = 16,5 % (2023), dataset earn_gr_gpgr2
- Kapitola:  sec:vyhled (strukturální faktor), sec:hodnoceni (vyvrácení protiargumentu)
- Argument:  Vyvrácení standardního argumentu: "Ženy vydělávají méně, protože volí nízko-mzdové
             sektory." Zobrazením within-sector mezery v sektorech s vyrovnaným počtem pohlaví
             se prokazuje, že GPG má strukturální složku nezávislou na sektorové segregaci.
             Slabý SD (nízké pokrytí KV, absence transparentních tarifních tabulek) tuto mezeru
             neuzavírá — srovnání: NACE K (finance) má v CZ silnější KV → nižší GPG
             než NACE G (maloobchod) s fragmentovaným SD (Penny Market: 4 ZO, žádná mzdová tabulka).
             EU Pay Transparency Directive 2023/970: od 2026 povinné reportování GPG → agenda SD.
- Verze:     Možno zkombinovat s B.2 (průřezová tabulka KS): sekce s KSVS OS PPP mají
             nerozlišené tarifní tabulky (min = pro všechny) → implicit GPG redukce.

### A.19 [stáhnout] ČSSZ — OSVČ: pojistné odvody vs. zaměstnanci (timeline)
- Navrhovaný soubor: pics/python/cssz_osvc_timeline.pdf
- Typ:       dual-axis čárový graf nebo indexed area chart
- Možnost 1: Počet OSVČ platící minimální zálohy (ČSSZ statistická ročenka) vs. počet zaměstnanců
             → zobrazuje strukturální posun k minimálním odvodům
- Možnost 2: Průměrný vyměřovací základ OSVČ jako % průměrné hrubé mzdy zaměstnanců
             → zobrazuje rostoucí erodování příspěvkové základny
- Možnost 3: Počet uživatelů paušálního daňového režimu od 2021 (Finanční správa / MPSV)
             → dokládá akceleraci erosion od zavedení paušální daně
- Data:      ČSSZ Statistická ročenka (https://www.cssz.cz/statistiky)
             Alternativa: MPSV Statistická ročenka OSVČ
- Kapitola:  sec:vyhled (OSVČ a paušální daň), sec:pojmy (ZDP)
- Argument:  Paušální daň a strukturální pobídky k OSVČ erodu příspěvkovou základnu
             → oslabuje financování sociálního systému, který by měl APZ financovat

---

## B. Tabulky

### B.1 [existuje] Flexicurity srovnání (6 zemí × 7 ukazatelů)
- Soubor:    texparts/python/flexicurity_table.tex
- Kapitola:  sec:evropsky_kontext
- Obsah:     HDP/ob., odborová hustota, pokrytí KV, GINI, prac. hodiny, AROPE, daňový klín

### B.2 Průřezová tabulka 4 KS + ZP baseline + 2 DK reference (10+ parametrů)
- Navrhovaný soubor: texparts/python/ks_comparison_table.tex
- Data:      Scrape souborů PennyMarket, ČP, OSPZV-ASO, OS PPP + ZP zákonné minimum
             + DK Butiksoverenskomst (NACE 47) + DK Finansoverenskomst/Nordea (NACE 64)
             [DK data ke stažení z Dansk Erhverv / FA.dk / FAOS]
- Kapitola:  sec:penny (průřezová analýza) — nebo ssec:porovnani_modely pro DK sloupce
- Obsah:     Přesčas, noční, So/Ne, dovolená, penzijní příspěvek, HO, tarify,
             inflační doložka, agenturní limit, OO ochrana, vzdělávací fond
- Sloupec „ZP minimum" jako referenční základ pro CZ; DK jako pozitivní benchmark
- Poznámka: DK sloupce lze oddělit do tabulky B.8 (DK vs. CZ srovnání), pokud B.2 přeroste

### B.3 Srovnání PP vs. OSVČ vs. Švarc vs. Agentura — [volitelné]
- Navrhovaný soubor: texparts/python/pp_osvc_comparison.tex
- Data:      TRANSCRIPT §7.6 (srovnávací tabulka 8 parametrů)
- Kapitola:  sec:vyhled nebo sec:pojmy
- Obsah:     Právní základ, KS, sociální pojistné, zdanění, BOZP, výpověď, odbory, sankce

### B.4 Vývoj kontrol SÚIP — timeline figura (přesunuto z tabulky)
- Viz A.20 v plánovaných figurách (SÚIP enforcement timeline plot)
- Pozn.: Přesunuto z původního B.6 → figura je vhodnější pro časový vývoj

### B.5 SWOT analýza SD v ČR
- Navrhovaný soubor: texparts/hodnoceni/swot_sd.tex
- Kapitola:  sec:hodnoceni
- Obsah:     Silné stránky, slabiny, příležitosti, hrozby

### B.6 Srovnávací tabulka systémů SD (z Hály)
- Navrhovaný soubor: texparts/evropsky_kontext/hala_comparison.tex
- Data:      Hála et al. 2013, s. 228–229 (srovnávací tabulka 7 zemí)
- Kapitola:  sec:teorie, sec:evropsky_kontext
- Obsah:     Odborová hustota, pokrytí KV, tripartita, dominantní úroveň KV, extenze mechanismus

### B.7 Rozšiřování závaznosti KSVS — CZ vs. EU praxe — [volitelné]
- Navrhovaný soubor: texparts/dialog/rozsireni_ksvs.tex
- Data:      CMKOS Zprava o KV 2025 (2 rozšíření v CZ); MPSV Sdělení 17/2026, 47/2026
- Kapitola:  sec:pojmy (ZKV § 7), ch:inovace (inovace 1)

---

## C. Datové zdroje — přehled

### C.1 Primární datové portály

| Instituce | Zkratka | URL | Klíčové datasety pro DP |
|-----------|---------|-----|------------------------|
| Eurostat | Eurostat | ec.europa.eu/eurostat | GDP, GINI, AROPE, zaměstnanost, mzdy, LMP, tax wedge, PLI |
| OECD AIAS ICTWSS | OECD | stats.oecd.org — Industrial Relations | Odborová hustota, pokrytí KV |
| ILO (ILOSTAT) | ILO | ilostat.ilo.org | Union density (TUR), EPL |
| ETUI | ETUI | etui.org/databases | CB coverage, strike activity |
| UBS / Credit Suisse | UBS | ubs.com/… global-wealth-report | Wealth Gini, mean/median wealth |
| MPSV RSCP | RSCP | mpsv.cz → Statistický inf. systém | Regionální statistika ceny práce — mzdy dle regionu/sektoru |
| ČSSZ | CSSZ | cssz.cz/statistiky | Statistická ročenka: pojištěnci, vyměřovací základy |
| Forbes | Forbes | forbes.com/billionaires | Bilionáři — počet, majetek |
| WID.world | WID | wid.world/country/czech-republic | Top 10% / top 1% wealth share |

### C.2 Národní instituce — přehled pro 6 zemí

| Oblast | CZ | AT | DE | DK | PL | SK |
|--------|----|----|----|----|----|----|
| Statistický úřad | CSU | Statistik Austria | Destatis | DST | GUS | SU SR |
| Min. práce | MPSV | BMAW | BMAS | BM | MRPiPS | MPSVR SR |
| Sociální pojistné | CSSZ | DVSV | DRV | ATP | ZUS | Socialna poistovna |
| Úřad práce | UP CR | AMS | BA | STAR | UP (Powiatowy) | UPSVaR |
| Odbory (centrála) | CMKOS, ASO | OGB | DGB | FH (drive LO) | OPZZ, Solidarnost | KOZ SR |
| Zaměstnavatelé | SP CR, HK CR | WKO, IV | BDA, BDI | DA, DI | Lewiatan, ZRP | RUZ, AZZZ |
| Min. financí | MF CR | BMF | BMF | Skatteministeriet | MF | MF SR |
| Inspekce práce | SUIP | Arbeitsinspektorat | Gewerbeaufsicht | Arbejdstilsynet | PIP | IP |
| Mzdová data (region) | MPSV RSCP | Statistik Austria | IAB / Destatis | DST | GUS | MPSVR |

### C.3 Kontrolní seznam — co stáhnout

| # | Dataset | Zdroj | Priorita | Pro figuru |
|---|---------|-------|----------|-----------|
| 1 | Trade union density (EU, timeline 1990–2024) | OECD ICTWSS | vysoká | A.6a, A.6b |
| 2 | Adjusted CB coverage (EU, 1 rok + timeline) | OECD ICTWSS | vysoká | A.7, A.17 |
| 3 | LMP expenditure (% GDP, timeline) | Eurostat lmp_ind_exp | vysoká | A.9a, A.9b |
| 4 | Mean annual earnings v PPS (6 zemí, timeline) | Eurostat earn_ses_pub1a | vysoká | A.8 |
| 5 | Net earnings v PPS (EU27, 1 rok) | Eurostat earn_nt_net | vysoká | A.10, A.15 |
| 6 | Self-employment rate (EU) | Eurostat lfsa_esgan | střední | A.11 |
| 7 | Income GINI (6 zemí, 2003–2023) | Eurostat ilc_di12 (CSV existuje) | python | A.16 |
| 8 | Wealth Gini (EU, 2008–2021) | UBS/CS Databook PDF, tab. 3-1 | střední | A.18a, A.18b |
| 9 | CSSZ statistika OSVC pojistné / pojistenci | CSSZ statisticka rocenka | střední | A.19 |
| 10 | RSCP MPSV — mzdy dle sektoru CZ | MPSV RSCP portal | doplňkový | A.8, B.2 |
| 11 | ISPV — průměrný výdělek × pohlaví × NACE sekce + počty zaměstnanců | MPSV ISPV (součást RSCP portálu) | střední | A.20 |
| 12 | Eurostat adjusted GPG (earn_gr_gpgr2) — CZ/AT/DE/DK/SK, 2010–2023 | Eurostat | nízká (1 hodnota stačí) | A.20 (reference line) |
| 13 | Butiksoverenskomst 2023–2025 PDF (HK Handel × Dansk Erhverv) | DanskeErhverv.dk nebo HK.dk | střední | B.2 DK sloupec, ssec:porovnani_modely |
| 14 | Finansoverenskomsten PDF (FA × Finansforbundet) + Nordea podniková KS | FA.dk nebo FAOS Aftaledatabáze (faos.ku.dk) | střední | B.2 DK sloupec, ssec:porovnani_modely |

---

## D. Mapování figur a tabulek na kapitoly (main.tex)

| Sekce (main.tex label) | Figury | Tabulky |
|------------------------|--------|---------|
| sec:pojmy | — | B.7 (odkaz) |
| sec:historie | A.6a | — |
| sec:teorie | — | B.6 |
| sec:datova_analyza | — | — |
| sec:vyhled | A.9a, A.9b, A.11, A.12, A.19, A.20 | B.3 (volitelné) |
| sec:evropsky_kontext | A.1, A.2, A.6b, A.7, A.8, A.13, A.15 | B.1, B.6 |
| ssec:flexicurity | A.4, A.5, A.9a | — |
| ssec:porovnani_modely | — | B.6 (odkaz) |
| sec:penny | — | B.2 |
| sec:hodnoceni | A.3, A.10, A.13, A.16, A.17, A.18a, A.20 | B.5 |
| ch:inovace | A.14 | B.7 |

Poznámka k main.tex: Sekce sec:penny pokrývá pouze Penny Market.
Zbývající 3 případové studie (Česká pošta, OSPZV-ASO, OS PPP) nutno přidat jako
podsekce nebo novou sekci v main.tex (neproblematické — viz research_plan_v4.md).

---

Verze 2: 2026-04-07. Status emoji odstraněny, přidán A.17 (union×GINI scatter),
A.16 změněn na timeline (příjmový GINI), A.18a (wealth GINI timeline),
A.19 (CSSZ OSVC), RSCP MPSV do zdrojů, mapování na main.tex labely.
