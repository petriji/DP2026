# Výzkumný a argumentační plán DP — verze 4
Sociální dialog a kolektivní vyjednávání
Jiří Petříček | MÚVS ČVUT | PRI | 2026-04-07
Nahrazuje research_plan_v3.md.

---

## Změnový přehled oproti v3

1. Sekce alignovány na labely v latex/main.tex (ch:ramec, sec:pojmy, sec:hodnoceni atd.).
2. Přidán MPSV RSCP (Regionální statistika ceny práce) jako primární datový zdroj.
3. Přidána CSSZ jako datový zdroj pro figuru A.19 (OSVC pojistné timeline).
4. Aktualizovány reference na figury: A.16 (GINI income timeline), A.17 (scatter), A.18 (wealth),
   A.19 (CSSZ OSVC) — viz figures_tables_plan_v2.md.
5. Nový podpůrný zdroj: sources/nocite/nerovnost_CZ.md.
7. Upozornění: main.tex má sec:penny pouze pro Penny Market — ostatní 3 studie nutno doplnit.

---

## 1. Cíl práce a hypotéza

Cíl: Zmapovat potenciál inovace sociálního dialogu v CR pro konkurenceschopnost na trhu
práce prostřednictvím analýzy relevantních statistických ukazatelů a porovnání v evropském
kontextu.

Hypotéza: Český trh práce je zranitelnější vůči vývoji práce v blízké budoucnosti kvůli
slabému sociálnímu dialogu.

Výzkumné otázky:
1. Jaké faktory budou v blízké budoucnosti působit na český trh práce?
2. Sehrává sociální dialog na vyspělých evropských trzích práce významnou roli?
3. Je sociální dialog a KV v CR v evropském kontextu na dobré úrovni?
4. Jak lze inovovat sociální dialog pro zvýšení konkurenceschopnosti CZ trhu práce?

Metody:
- Kvantitativní: statistická analýza trendů, korelační analýza (Eurostat, OECD, MPSV, CSSZ, ILO)
- Kvalitativní: syntéza literatury, komparativní analýza modelů, případové studie (4 KS/KSVS)
- Komparativní: časové, regionální a systémové

---

## 2. Kapitolová struktura souběžně s main.tex

Kapitoly odpovídají labelům v latex/main.tex. Komentáře v main.tex jsou závazné pro obsah.

---

### ch:uvod — Úvod

Argument: Uvést kontext — zrychlující se technologický vývoj (i4.0, AI) × model levné práce
v CR = narůstající napětí, které si žádá silný sociální dialog.

Obsah:
- Vymezení cíle a předmětu práce
- Vyslovení hypotézy
- Popis struktury práce, metod (povrchově) a případových studií (4 KS)

Zdroje: Zadani_DP_Petricek2026_TRANSCRIPT.md, PJDP2026L_ProjektDP_TRANSCRIPT.md,
        Armstrong_HRM_Handbook.md

Status: Přepsat celý texparts/uvod.tex (stávající obsah z jiné práce).
Rozsah: cca 4 000 znaků.

---

### ch:ramec — Legislativní, historický a teoretický rámec

Úvod do kapitoly (~2 000 znaků):
Zdůvodnit, proč je co shrnováno. Zmínit dosavadní DP spravené v nocite
(zaměřené na odměňování, DP z právnických fakult) a nový pohled této práce.

---

#### sec:pojmy — Pojmy a vztahy, legislativa

Argument: Definovat pojmy přesně dle české legislativy a mezinárodních standardů ILO/EU.
Legislativní rámec CZ je formálně srovnatelný s EU, ale faktická implementace zaostává.

Vnitřní členění:

| Subsekce | Obsah | Legislativní základ |
|----------|-------|---------------------|
| Základní pojmy | SD, KV, KS, PSP, tripartita, bipartita | Hala kap. I (ILO definice) |
| Zákon o KV | Proces KV, uzavírání KS, řešení sporů, rozšiřování závaznosti KSVS | ZKV §§ 1-31 |
| ZP — KS | Pluralita OO, obsah a hierarchie KS, ochrana funkcionářů | ZP §§ 22-29 |
| ZP — odměňování | Min. mzda, příplatky, průměrný výdělek, zaručená mzda, NV vývoj | ZP §§ 109-118 |
| ZP — překážky v práci | Překážky ZL a ZL, náhrady mzdy | ZP §§ 191-210 |
| ZP — výpověď | Výpovědní důvody, souhlas OO, hromadné propouštění | ZP §§ 52, 61, 62-63 |
| ZP — další ochrana | Dovolená, pracovní řád, BOZP inspekce, převod zaměstnanců (TUPE) | ZP §§ 213, 306, 322, 338-341 |
| ZP — home office | Rámec § 317, specifika § 241/241a (pečující), nadstandard v KS | ZP §§ 241/241a, 317 |
| ZP — závislá práce | Definiční znaky, Švarc systém, nelegální práce, sankce | ZP §§ 2-3; ZZ § 5(e), §§ 139-140 |
| ZP — agenturní zam. | Trojúhelníkový vztah, rovné zacházení, 12měsíční limit | ZP §§ 307a-309; ZZ §§ 14, 58, 60 |
| ZDP — OSVC | Paušální daň, 3 pásma, erodování sociálních odvodů | ZDP §§ 2a, 7, 7a |
| ZZ — trh práce | APZ, zprostředkování, agenturní licence | ZZ §§ 1-2, 7, 39-51, 67-84, 104-120f |
| Rozšiřování KSVS | CZ praxe (2 rozšíření v 2025), AT srovnání, Sdělení 17/2026 a 47/2026 | ZKV § 7 |
| Mezinárodní rámec | ILO Conventions 87+98, EU Social Charter, Eurofound | Hala kap. I |

Pilířové zdroje:
- CZ_LegislativniRamec_TRANSCRIPT.md (1 298 řádků, 7 oddílů)
- Hala_VZ361_TRANSCRIPT.md — komparativní systémy SD v EU
- CMKOS_Zprava_KV_2025.md — aktuální empirická data KV
- Armstrong_HRM_Handbook.md (kap. collective bargaining, employee relations)
- 100_let_MOP.md (ILO konvence, historický kontext)

Akronymy: Zavést zkratky pomocí acro (vložit záznamy do texparts/references/acro.tex).

---

#### sec:historie — Historický vývoj

Argument: Odborové hnutí vzniklo jako reakce na industrializaci; dnes je AI analogický šok.
V CR přetrvává trauma komunistického formálního odboritví → strukturální nedůvěra k odborům.

Členění:
1. Vznik odborů (19. stol.) — industrializace, sociální legislativa
2. ILO a meziválečné období — první republika, vznik odborové tradice v CSR
3. Komunistické odbory — ROH, absence skutečného vyjednávání
4. Transformace po 1989 — vznik RHSD, CMKOS, legislativní rámec
5. Strukturální pokles odborové hustoty (1990 → 2024: z ~80 % na 11 %)
6. Průmysl 4.0 a AI jako nový industrializační šok — historická analogie

Figury: A.6a — union density timeline (data k stažení z OECD ICTWSS).

Zdroje:
- Historie_odbory_a_spolecnost.md (CMKOS 2020)
- 100_let_MOP.md (Pokorny 2019)
- Hala_VZ361_TRANSCRIPT.md — historický kontext kap. I a kap. VII (CZ)
- PETRICEK_IND4_IndustrialRevolution_NOCITE.md — argumenty (přepsat, nepřímo citovat)
- Data: OECD AIAS ICTWSS / ILOSTAT TUR — nutno stáhnout

---

#### sec:teorie — Přehled současného poznání

Argument: Rešerše dostupné literatury k sociálnímu dialogu. Hlavní přínosy: Hala (komparativní),
Armstrong (HRM), Dvorakova (CZ kontext), CMKOS zpráva (empirická data).

Subsekce:
1. Komparativní systémy SD v EU — Hala et al. (2013) jako hlavní komparativní zdroj
   - Srovnávací tabulka 7 zemí (Hala s. 228-229): pokrytí KS, hustota, tripartita — viz B.6
   - Závěr Haly (s. 286-288): postkomunistické země vč. CR
   - Trend decentralizace KV v Evropě (Hala kap. I)
   - EU průměrné pokrytí KV 66 % (Hala kap. I)
   - Poznámka: Hala nezahrnuje DK — doplnit z jiných zdrojů (ETUI Benchmarking 2024)
2. HRM perspektiva — Armstrong: Employee Advocate role, KV jako HRM nástroj
3. CZ akademický kontext — Dvorakova (2012, 2024, 2025): RLZ, APZ, demografické trendy
4. Empirická evidence — CMKOS Zprava o KV 2025:
   - Pokrytí KV v CR: 32 %
   - PKS benchmarks: příplatky, dovolená, penzijní příspěvek (71 % PKS)
   - Rozšiřování KSVS: 2 v roce 2025 (Sdělení 17/2026 a 47/2026)
   - Veřejný vs. soukromý sektor: mzdová disparita

Zdroje:
- Hala_VZ361_TRANSCRIPT.md — klíčový komparativní zdroj
- Hala_VZ361_SystemySocialnihoDialogu.md — poznámky/shrnutí
- CMKOS_Zprava_KV_2025.md — empirická data KV
- Armstrong_HRM_Handbook.md
- ActiveEmploymentPolicy_Dvorakova.md
- ZBORNKPRSPEVKOV_Dvorakova_DemografickeTrendy.md
- WojtczukTurek_SustainHRM_JobSatisfaction.md
- Weber_Industrie40_Arbeitsmarkt.md (Industry 4.0 → trh práce)

---

### ch:vyzkum — Postup výzkumu (sec:datova_analyza)

Obsah:
- Výzkumná strategie: kvantitativní + kvalitativní + komparativní
- Zdůvodnění výběru zemí: AT (Kammer-system, 98 % KV, společná historie), DE (Mitbestimmung,
  obchodní partner), DK (flexicurity model), PL/SK (postsovětská trajektorie)
- Datové zdroje: Eurostat, OECD, MPSV (incl. RSCP), CSSZ, CMKOS, ILO, ETUI
- Python analytický pipeline: stažení CSV → čistění → vizualizace → PDF/TeX export
- Metoda případové studie: 4 KS (2 PKS + 2 KSVS): výběr dle dostupnosti, sektorové diverzity
  a hierarchické úrovně
- Limity: dostupnost dat, srovnatelnost definic přes země; CZ specifika (ISPV/RSCP)

Definice PPS (první použití — vložit do sec:datova_analyza nebo sec:pojmy):
PPS (Purchasing Power Standard) je umělá měnová jednotka Eurostatu eliminující rozdíly
v cenových hladinách mezi zeměmi. Formálně:
  x_PPS = x_EUR / (PPP_i / PPP_EU27)
kde x_EUR je hodnota v EUR, PPP_i je parita kupní síly země i, PPP_EU27 je průměr EU-27.
Pravidlo: Všude, kde se v práci srovnávají mzdy nebo příjmy, používat PPS vyjádření.

Zdroje: Armstrong_HRM_Handbook.md, PJDP2026L_ProjektDP_TRANSCRIPT.md

---

### ch:stav — Stav trhu práce

Úvod kapitoly (~1 000 znaků): CR trh práce v kontextu — struktura, zaměstnanost 81,7 %,
průměrná mzda 46 165 Kč/2024, regionální diferenciace Praha vs. zbytek CR.

---

#### sec:vyhled — Výhled

Faktory výhledu (strukturovat paragraf):

| Faktor | Klíčový argument | Zdroj |
|--------|-----------------|-------|
| AI a automatizace | Levná práce ohrožena; AI eliminuje junior pozice; i4.0 šok | Weber (2015), PETRICEK_IND4 |
| Demografické tlaky | Old-age dependency 32 %; stárnutí → tlak na soc. systém | Eurostat A.OLDDEP1, Dvorakova demografie |
| Imigrace z Ukrajiny | ~340 000 uprchlíků → tlak v nízkokvalifikovaných sektorech | Polents/Dvorakova (2024) |
| OSVC a Švarc systém | Nadprůměrné % OSVC v EU; paušální daň → erodování odvodové základny | TRANSCRIPT §7.5; CSSZ statistická ročenka |
| Agenturní zaměstnávání | Trojúhelníkový vztah; rovné zacházení obcházeno; zemědělství rizikové | TRANSCRIPT §7.4 (ZP §§ 307a-309) |
| Veřejný sektor | Mzdová zaostalost (vzdělávání +2,7 % vs. NH +7,1 % v 2024) | CMKOS Zprava kap. 3.8 |
| Regionální diferenciace | Praha +26,7 % nad průměrem NH | CMKOS Zprava; MPSV/RSCP |
| Genderová stratifikace | GPG 16,5 % (Eurostat 2023) — 5. nejvyšší v EU; within-sector mezera přetrvává i v sektorech s vyrovnaným počtem mužů a žen → strukturální nerovnost, ne jen sektorová volba | Eurostat earn_gr_gpgr2; MPSV ISPV/RSCP |

Figury: A.9a, A.9b (LMP timeline), A.11 (OSVC map), A.12 (old-age dependency), A.14 (tax OSVC),
        A.19 (CSSZ OSVC timeline — erodování příspěvkové základny), A.20 (GPG within-sector).

Datové zdroje — RSCP MPSV:
MPSV publikuje Regionální statistiku ceny práce (RSCP) čtvrtletně. Obsahuje průměrné mzdy dle
regionu (krajů), sektoru (NACE), pohlaví a věku. URL: https://www.mpsv.cz/web/cz/statisticky-informacni-system
Využití: Regionální diferenciace (Praha vs. zbytek), sektorové mzdy pro srovnání s KS tarifními
tabulkami (B.2), podklad pro wage_gdp_convergence (A.8).

Genderová dimenze RSCP/ISPV:
ISPV (Informační systém o průměrném výdělku — zdrojová databáze RSCP) obsahuje průměrný hrubý
měsíční výdělek průřezem pohlaví × sektor (NACE sekce) × počet zaměstnanců.
Tato dimenze umožňuje odpovědět na typický protiargument:
  Protiargument: "Ženy vydělávají méně, protože pracují v méně výnosných sektorech
                  (zdravotnictví, školství, sociální práce)."
  Metodika vyvrácení (figury A.20): Vybrat sektory NACE, kde je počet mužů a žen přibližně
  vyrovnaný (podíl 40–60 %). V těchto sektorech mezera vyjadřuje within-sector GPG,
  který není způsoben sektorovou segregací a nelze jej přičíst volbě zaměstnání.
  Sektory s přibližnou rovnováhou pohlaví v CZ dle ISPV:
  - NACE G (velkoobchod, maloobchod): ~52 % žen
  - NACE I (ubytování a stravování):  ~55 % žen
  - NACE K (finance a pojišťovnictví): ~55 % žen
  - NACE O (veřejná správa, obrana):   ~56 % žen
  - NACE M (profesní a vědecké služby): ~47 % žen
  Vyloučit silně segregované: NACE J (ICT, ~20 % žen), NACE Q (zdravotnictví, ~80 % žen).
  Výsledek: Zbytková within-sector mezera je strukturální — nevysvětlitelná pouhou sektorovou
  volbou. Přidaná hodnota SD: KSVS s nerozlišenými tarifními tabulkami (OS PPP: min. 28 000 Kč
  bez pohlaví) GPG snižují. EU Pay Transparency Directive 2023/970 → povinné reportování od 2026.
Využití: A.20 (within-sector GPG figure), sec:vyhled, sec:hodnoceni, ch:inovace (inovace č. 3).

Datové zdroje — CSSZ:
CSSZ Statistická ročenka (https://www.cssz.cz/statistiky) obsahuje:
- Počty pojistněnců (zaměstnanci, OSVC) v čase
- Průměrné vyměřovací základy OSVC vs. zaměstnanci
- Přehled plátců minimálních záloh
Využití: A.19 (OSVC pojistná timeline) — dokumentuje erozi příspěvkové základy.

---

#### sec:evropsky_kontext — Evropský kontext

Klíčový argument: CR pracuje nejdéle ze skupiny (39,6 h/týden), za nízké reálné mzdy (PPS),
s vysokým daňovým klínem (38,1 % vs. DK 33,5 %), s minimálním pokrytím KV → zaměstnanci
nedostávají podíl na produktivitě hospodářství. HDP konverguje rychleji než reálné mzdy.

Existující figury (main.tex — inputy aktivní nebo jako TODO komentáře):
- A.1 — gdp_ppp_timeline (existuje)
- A.2 — tax_wedge_map (existuje)
- B.1 — flexicurity_table (existuje)
- A.3 — arope_map_2025 (existuje)
- A.8 — wage_gdp_convergence (TODO — dotahnout)
- A.17 — union_gini_scatter (TODO — main.tex má komentář, nutno přidat)

Subsekce ssec:flexicurity — DK zlatý trojúhelník:
- Flexibilita + příjmová jistota + APZ
- CR adoptovala pouze flexibilitu bez APZ a silného KV → deformace modelu
- APZ: CR ~0,3 % HDP vs. DK ~2 % HDP
- DK: podpora v nez. ~90 % mzdy/2 roky vs. CR ~50 %/5 měsíců
- Zdroje: PETRICEK_HOPO_Flexicurity_NOCITE.md, NOCITE_Petricek_Flexicurity_Denmark.md

Subsekce ssec:porovnani_modely:
- AT: Kammer-system → 98 % pokrytí s 26 % hustotou
- DE: Mitbestimmung + Hartz reformy (varování před flexibilizací bez jistoty)
- PL/SK: postsovětská trajektorie, srovnání s CR
- Zdroj: Hala_VZ361_TRANSCRIPT.md kap. II-VII

---

#### sec:penny — Případové studie KS (4 studie)

Poznámka k main.tex: Stávající label sec:penny pokrývá jen Penny Market. Zbývající 3 studie nutno
přidat jako podsekce nebo novou sekci. Navrhuji přejmenovat na sec:pripadove_studie a přidat
podsekce. Update main.tex bude potřeba.

Argument: Analýza 4 reálných KS dokládá, jak funguje KV na dvou úrovních (PKS, KSVS)
a ve 4 sektorech. Hierarchie KSVS → PKS (§ 27(1) ZP) testována přímou konfrontací textů.
Legislativní re-evaluace odhaluje, kde KS substituují státní regulaci a kde přetrvávají mezery.

Společná struktura každé studie:
1. Identifikace stran, sektoru, platnosti
2. Pracovněprávní podmínky (pracovní doba, odměňování, příplatky, dovolená, BOZP, překážky)
3. Nadstandard nad ZP minimum
4. Legislativní re-evaluace (cross-reference s TRANSCRIPT)
5. Srovnání s benchmarky (CMKOS Zprava, ZP minimum, ostatní KS)

--- PKS Penny Market 2026 (NACE 47.11 — maloobchod s potravinami)

Zaměstnavatel: Penny Market, s.r.o. (~10 000 zaměstnanců)
Strany: 4 ZO (OSPO-ASO, OSPZV-ASO, UZO Opava, UZO Petrvald) — pluralita § 24 ZP
Klíčová zjištění:
- Pracovní doba 40h = zákonné minimum; vyrovnávání až 52 týdnů
- Přesčas příplatek 25 % = zákonné minimum (KSVS OSPZV-ASO stanoví 40 %)
- Penzijní příspěvek 800 Kč/měs < KSVS (1 000-1 350 Kč)
- Top Employer 2026 — tisková zpráva nezmíní sociální partnery → SD jako neviditelná HRM složka
- KSVS OSPZV-ASO na Penny jako zaměstnavatele **NEDOPADÁ** (Penny není člen ZS ČR/ČMSZP;
  §25(2)(a) ZP se neuplatní; extenze Sdělení 47/2026 pokrývá jen NACE 01.1–01.6)
- OSPZV-ASO je přímou smluvní stranou PKS (§25(1) ZP) — PKS platí autonomně
- Analytický paradox: OSPZV-ASO vyjednává v KSVS 40% noční přesčas a 1 000–1 350 Kč PP,
  v PKS Penny souhlasí s 25 % a 800 Kč → „dvojí standard" svazu = argument pro extenzní KSVS
  (inovace č. 1): bez závazného floor podniková úroveň podléhá race to the bottom
Zdroj: PennyMarket_KS_2026.md

--- PKS Česká pošta 2025-2026 (NACE 53 — poštovní služby)

Zaměstnavatel: Česká pošta, s.p. (~25 000 zaměstnanců) — státní podnik
Klíčová zjištění:
- 12 tarifních stupňů → substituují zrušenou zaručenou mzdu (NV 567/2006 → NV 326/2023)
- Příplatky nad ZP: noční +5pp, so/ne +2pp
- TUPE riziko: transformace státního podniku → §§ 338-341 ZP
- HO/péče o děti: žádná úprava v PKS
- Chybí agenturní limit (§ 309(8) opominutí)
Zdroj: CeskaPostaSP_KS_2025_2026.md

--- KSVS OSPZV-ASO / ZS CR / CMSZP 2026 (NACE 01 + 10-12 — zemědělství, potravinářství)

Strany: OSPZV-ASO CR (odbory) × ZS CR + CMSZP (zaměstnavatelé)
Extenze: Sdělení 47/2026 Sb. — rozšíření na NACE 01.1-01.6
Klíčová zjištění:
- Tarifní systém → de facto náhrada zaručené mzdy
- Přesčas v noci/NVO 40 % = +15pp nad ZP
- Inflační doložka (3 % trigger) — unikátní v CZ kontextu
- Sdělení 47/2026: extenze pokrývá NACE 01.1-01.6, ne maloobchod 47
- Chybí agenturní limit — zemědělství je významný uživatel agenturní práce
- Mezisektorový přesah OSPZV-ASO (NACE 01 → 10-12 → přímý signatář PKS u NACE 47) →
  KSVS na Penny NEDOPADÁ; argument pro rozšíření extenze přes celý hodnotový řetězec
Zdroj: KSVS_ASO_CMSZP_2026.md

--- KSVS OS PPP / SBP 2026-2027 (NACE 64-66 — peněžnictví, pojišťovnictví)

Strany: OS pracovníků peněžnictví a pojišťovnictví × Svaz bank a pojišťoven
Klíčová zjištění:
- Minimální mzda 28 000 Kč = +23 % nad MM (22 750 Kč v 2026)
- So/ne příplatek 50 % = 5× zákon (10 %) — nejvyšší ze všech 4 KS
- § 61 souhlas OO k výpovědi funkcionáře — explicitně sjednán
- § 306, § 322 — svazová inspekce BOZP, blokační právo OO nad prac. řádem, vše v KS
- HO čl. 7 — gap-filling oproti rámcovému § 317 ZP
Zdroj: KSVS_OSPPP_2026_2027.md

--- Průřezová analýza 4 KS (tabulka B.2)

| Parametr | Penny Market | Česká pošta | OSPZV-ASO | OS PPP | ZP min. |
|----------|-------------|-------------|-----------|--------|---------|
| Přesčas příplatek | 25 % | 25 % + vol. | 40 % (noc) | - | 25 % |
| Noční příplatek | 10 % *(PKS mlčí → ZP §116)* | 15 % | 20 % | - | 10 % |
| So/Ne příplatek | 10 % *(PKS mlčí → ZP §118)* | 12 % | 20 % | 50 % | 10 % |
| Dovolená | 5 týdnů | 5 týdnů | 5 týdnů | 5 týdnů | 4 týdny |
| Penzijní příspěvek | 800 Kč | dle tarifu | 1 000-1 350 Kč | ano | — |
| HO úprava | ne | ne | ne | čl. 7 | § 317 rámec |
| Tarifní systém | ne | 12 stupňů | ano | min. 28 000 Kč | — |
| Inflační doložka | ne | ne | ano (3 %) | ne | — |
| Agenturní limit | ne | ne | ne | ne | §309(6): 12 měs. |
| § 61 OO ochrana | ne | ne | ne | ano | § 61(2) |
| § 306 blokace OO | ne | ne | ano | ano | § 306(4) |

Analytické závěry průřezu:
1. KSVS jako substituent státní regulace: Po zrušení 8 skupin zaručené mzdy (NV 326/2023) jsou
   tarifní tabulky v KSVS jedinou bariérou proti race to the bottom.
2. Sektorová diverzita: bankovnictví (OS PPP) = nejsilnější nadstandard, koreluje s vyšší
   přidanou hodnotou a vyjednávací silou OO.
3. Regulatorní mezery: HO, agenturní zaměstnávání a hromadné propouštění — nedostatečně
   pokryté ve všech 4 KS. Digitalizace v bankovnictví = anticipovaný tlak na hromadné propouštění.
4. Centralizace KV: Mezisektorový přesah OSPZV-ASO (NACE 01 → 47) je argument pro KSVS
   pokrývající celý hodnotový řetězec.

--- Průřezová tabulka B.2 — DK sloupce

Tabulka B.2 by měla obsahovat i dva DK referenční sloupce (Butiksoverenskomst a Finansoverenskomst)
vedle 4 CZ studií a zákonného minima ZP. Přidat jako „DK maloobchod" a „DK finance" — bez
nárokování výsledné hodnocení, ale pro přímé srovnání klíčových parametrů.
Seznam parametrů pro DK sloupce viz DK případové studie níže.

---

--- DK srovnávací reference (2 KS) — ssec:porovnani_modely nebo box v sec:penny

Záměr: Dvě dánské studie slouží jako pozitivní referenční vzor (benchmark) pro inovační část
(ch:inovace). Není nutné je zpracovat na stejné hloubce jako CZ studie — postačí analytický
přehled klíčových parametrů s přímým srovnáním s ekvivalentními CZ KS.
Umístění v main.tex: Vhodné jako subsekce ssec:porovnani_modely nebo jako srovnávací box
po průřezové tabulce CZ studií.

Datové zdroje DK:
- Butiksoverenskomst text: Dansk Erhverv → https://www.danskeerhverv.dk nebo HK Handel PDF (stáhnout)
- Finansoverenskomsten text: FA (Finanssektorens Arbejdsgiverforening) → https://www.fa.dk/overenskomster/
- Eurofound DK CB profile: https://www.eurofound.europa.eu/countries/denmark/collective-bargaining
  (verifikováno 2026-04-07 — zdroj pro systémové popisy v textu)
- Finansforbundet EN: https://finansforbundet.dk/en/ (verifikováno 2026-04-07 — Nordea data)
Poznámka: Dánské kolektivní smlouvy nejsou zákonem rozšiřovány (§ — žádný Sdělení mechanismus).
  Pokrytí ~80 % je dosaženo čistě dobrovolnou odborovou hustotou (67 %) + Ghent model
  (nezaměstnanostní pojištění spravované odbory). Toto je klíčový argument pro inovaci č. 2 (DP).

--- DK sektorová KS: Butiksoverenskomst 2023–2025 (NACE 47 — maloobchod)

Strany: HK Handel (odbory FH) × Dansk Erhverv (zaměstnavatelé)
Platnost: OK23, podepis březen 2023, platnost 2023–2025; ~80 000 pracovníků
Systém KV: lønminimum (mzdové minimum) — sektorová KS stanoví tarifní dno,
           podniky vyjednávají nadstavbu individuálně / v PKS. (80 % dánského soukromého sektoru.)
Žádný mechanismus rozšiřování: 100% pokrytí NACE 47 dosaženo hustotou OO + kolektivní
  afiliací zaměstnavatelů v Dansk Erhverv — bez právního závazku státu (viz ZKV § 7 CZ kontrast).

Klíčová zjištění:
- Pracovní doba: 37 hodin/týden = sektorový standard (Da grundlovsaftale o 37 h platí od 1990)
- Tarifní systém: věkostupnicový + seniorní — sazba pro 20+ (2023): ~138 DKK/hod;
  po OK23 nárůst okolo 6 % → přibližně 142–144 DKK/hod (2024–2025); ověřit v textu KS
  [Srovnání: Penny Market CZ — žádný tarifní systém, zákonná minimální mzda 22 750 Kč/měs;
   DK ~144 DKK/h × 37 h × 4,33 = ~23 100 DKK/měs ≈ 75 000 Kč/měs (kurz 3,25 Kč/DKK);
   PPS-korektně: 23 100 DKK / PLI_DK × PLI_CZ — nutno přepočíst Eurostatovým PLI;
   absolutní rozdíl vs. PPS rozdíl = klíčový argument cheap labour trap]
- Přesčas: 50 % příplatek 1.–3. hodina přesčas; 100 % nad 3 hod; nebo náhradní volno
  [Srovnání: Penny Market CZ 25 % = zákonné minimum; DK 50–100 % sjednaných v KS]
- Noční/večerní příplatek: ~15–20 DKK/hod pro práci po 18 h; So/Ne supplement vyšší
  [Srovnání: Penny Market CZ noční/So/Ne = 10 % PV (ZP §116/§118 minimum; PKS mlčenlivá; KSVS na Penny nedopadá). DK smluvně 2–5× CZ zákonné minimum.]
- Dovolená: 6 týdnů (5 zákonných dle Ferieloven + 1 týden z KS = 6,0 týdnů)
  [Srovnání: Penny Market CZ 5 týdnů; CZ zákon 4 týdny; DK o 1 týden více]
- Penzijní příspěvek: 12 % (zaměstnavatel 8 % + zaměstnanec 4 %); platba do kolektivního
  penzijního fondu sjednaného v KS
  [Srovnání: Penny Market CZ 800 Kč/měs ≈ ~3,5 % hrubé mzdy; DK 8 % od zaměstnavatele]
- Seniorní dny (seniorordning): 1–2 placené dny volna/rok pro starší pracovníky
  [CZ: žádná analogie v CZ KS — téma pro ch:inovace]
- Barns første sygedag: plná náhrada mzdy za 1 den nemoci dítěte
  [CZ: ZP § 191 (neplacená překážka u zaměstnavatele), některé CZ PKS ji sjednávají]
- Kompetenzfond (vzdělávací levý): zaměstnavatel přispívá ~1 500 DKK/zaměstnanec/rok
  na rekvalifikaci (bipartitně spravovaný fond)
  [CZ: žádná analogie ve 4 CZ KS]
- Mírová klauzule (fredsforpligtelse): platí po dobu smlouvy; stávka legální pouze v okně
  před vyjednáváním (nebo solidaritní stávka); Arbejdsretten = pracovní soud; pokuta za porušení

Analytické závěry (pro text ssec:porovnani_modely):
a) Žádný rozšiřovací mechanismus → přesto 100% pokrytí NACE 47 = argument pro Ghent model
   (inovace č. 2): dobrovolná hustota OO vzrůstá, když KS přináší hmatatelné benefity.
b) Minimální mzdový systém: sector floor + company negotiation je v DK EFEKTIVNĚJŠÍ
   než CZ zákonná minimální mzda bez sector floor — protože DK company deals jdou nahoru od
   floor, zatímco CZ bez KSVS zákon je jediný floor a zaměstnavatelé se u něj drží.
c) Pension 12 % vs. CZ 800 Kč/měs = strukturální argument pro povinnné standby v KS (inovace č. 3).
d) Vzdělávací fond = inspirace pro Ghent-type APZ (inovace č. 2 — odbory jako agenti APZ).
e) Makroekonomická odolnost: OK22 jako automatický stabilizátor agregátní poptávky —
   viz sec:hodnoceni argument (inflační šok 2022–2023). Butiksoverenskomst DK pro NACE 47
   obsahuje inflační mechanismus a sector floor; CZ Penny Market PKS nemá ani jedno →
   pokles reálné mzdy zaměstnanců retailu byl v CZ hlubší než v DK → argument pro
   centralizaci KV nejen jako distribučního, ale i jako stabilizačního nástroje.
Zdroj (ke stažení): Butiksoverenskomst PDF z DanskeErhverv.dk nebo HK.dk

--- DK podniková KS: Nordea Denmark enterprise podsekce Finansoverenskomst 2024–2027 (NACE 64)

Strany: Nordea Bank A/S (~12 000 DK zaměstnanců) × Finansforbundet + Akademikerne
Rámec: Finansoverenskomsten (FA × Finansforbundet) — oborová KS + podniková nadstavba
Platnost: OK24 (veřejný sektor 2024-2027; finance sector OK24 analogicky obnovena), 3 roky
Systém KV: normalløn — oborová KS nestanoví minimální mzdu; VEŠKERÉ mzdy sjednány
           individuálně v podniku (roční lønsamtale); KS reguluje podmínky, ne výši mzdy.
           [Kontrast s CZ KSVS OS PPP: sektorová KS = pevné minimum 28 000 Kč/měs;
            DK finance = žádné sektorové minimum, reálné mzdy ~50 000–55 000 DKK/měs (DST 2024);
            PPS: DK finance median >> AT >> CZ finance]

Klíčová zjištění — Finansoverenskomst (oborová KB):
- Pracovní doba: 37 hodin/týden
- Penzijní příspěvek: ~17 % celkem (zaměstnavatel ~12 %, zaměstnanec ~5 %); skrze PFA
  [Srovnání: KSVS OS PPP CZ — neurčená výše penzijního příspěvku v textu KS]
- Dovolená: 6 týdnů
- Seniorní dny (seniorordning): věkostupnicové; typicky 1–5 dní/rok dle věku; sjednáno v KS
- Individuální roční mzdové přezkoumání (lønsamtale): výsledek závisí na kolektivní normě
  z OK24 + individuálním hodnocení
- Finanskompetencepuljen (vzdělávací fond): zaměstnavatel přispívá na odborné vzdělání;
  bipartitně spravován odbory + FA; zaměstnanec si volí kurzy z katalogu
- Parental leave supplement: zaměstnavatel doplácí nad státní dávku (týdny dle délky zaměstnání)
- Přesčas: primárně náhradní volno (afspadsering); peněžní prémie možná lokální dohodou
- Pracovní podmínky HO: rozsáhlé smluvní ujednání o home office — legalní základ + vybavení +
  bezpečnost; předchůdce EU Work-From-Home iniciativy (platí v KS řadu let před legislativou)

Klíčová zjištění — Nordea podniková nadstavba:
- Aktuální restrukturalizace: Nordea oznámila 1 500 propouštění (březen 2026; IT divize → únor 2026
  IT pracovníci; zdroj: Finansforbundet EN news). Enterprise KS obsahuje:
  - Postup pro hromadné propouštění (massefyringer): oznamovací lhůty, povinné konzultace
    s OO před oznámením (analogie § 62-63 ZP CZ, ale s delšími lhůtami a sociálním plánem)
  - Nárok na outplacement a rekvalifikaci (z Finanskompetencepuljenu)
  - Re-employment right: přednostní právo při nabírání v N+12 měsíců
  - Zaměstnanecká rada (samarbejdsudvalg, SU): bipartitní orgán na podniku — projednává
    organizační změny, AI implementaci, whistleblowing; není OO, ale komplementární orgán
    [Srovnání: CZ závodní výbor dle ZP, ale SP/HK CR odpírají SU zavedení]
- Transparentnost odměňování: Finansforbundet (březen 2026 EN) zveřejnil analýzu GPG
  v sektoru; popsáno jako „inexplicable" i po kontrole hierarchie → argument pro mzdové tabulky
  [Synergie s CZ inovací č. 3 a A.20 gender figure]

Analytické závěry (pro text ssec:porovnani_modely nebo sec:hodnoceni):
a) Normal wage system (normalløn) vs. CZ: zdánlivý paradox — DK KS nestanoví mzdy, přesto
   průměrné mzdy v DK finance NACE 64 = ~3–4× CZ PPS-adjusted → výsledek vysoké hustoty OO
   + ekonomické prosperity, ne direktivní mzdové regulace. Systém funguje, protože OO
   mají vyjednávací sílu (hustota 67 % DK vs. 11 % CZ).
b) Massefyringer: Nordea case ukazuje, jak silná podniková KS chrání zaměstnance při
   digitální restrukturalizaci — přímý kontrast k CZ, kde hromadné propouštění je zákonný
   formální postup bez mzdové ochrany v přechodném období.
c) Vzdělávací fond + outplacement = Ghent APZ v praxi na podnikové úrovni.
d) GPG: DK finance sektor má GPG i přes silné odbory → dokumentuje, že samotná existence KV
   nestačí; potřeba explicitní mzdové transparentnosti v KS (inovace č. 3).
Zdroj (ke stažení): Finansoverenskomsten PDF z FA.dk (https://www.fa.dk/overenskomster/);
  FAOS (Aftaledatabasen): https://faos.ku.dk/

---

#### sec:hodnoceni — Hodnocení sociálního dialogu v CR

Struktura: oponování hypotézy systematickým vyvrácením protiargumentů + SWOT + korelace.

1. Protiargumenty (uvést poctivě):
   - AROPE 12 % = nejnižší ze skupiny → fig. A.3 (choropleth)
   - Zaměstnanost 81,7 % → fig. A.13 (timeline)
   - Reálný mzdový růst 2024 = +4,6 %
   - Příjmový GINI 24,4 = nízká nerovnost → fig. A.16 (income GINI timeline)

2. Systematické vyvrácení:
   - AROPE hranice = relativní (60 % mediánu) → nízké absolutní příjmy v PPS
   - Délka prac. týdne 39,6 h = nejdelší ze skupiny → pracovník pracuje déle za méně
   - HDP konverguje rychleji než mzdy → cheap labour trap přetrvává
   - Inflační šok 2021–2023: index reálné mzdy CR klesl ~9–10 % kumulativně (2022–2023,
     Eurostat/ČSÚ) — jeden z největších poklesů v EU. Slabý SD nedokázal koordinovat
     mzdovou odezvu: decentralizované PKS zaostávaly za inflací (CPI 2022 = +15,1 %, CPI 2023
     = +10,7 %) → reálné příjmy domácností propadly → kontrakce spotřebitelské poptávky →
     HDP CR stagnoval 2022 (0,2 %) a klesl 2023 (cca –0,3 %). Mechanismus: slabý SD
     = žádný centralizovaný inflační doložkový mechanismus → pracovníci nesli celý
     nákladový šok sami → multiplikátorový efekt snížil agregátní poptávku.
     KONTRAST s DK: OK22 (Industriens Overenskomst, jaro 2022) sjednal rychlou mzdovou
     indexaci pro 600 000+ pracovníků, min. lønstigning kompenzoval inflaci sektorově;
     DK HDP 2022 = +3,8 %, 2023 = +1,9 % — SD absorboval šok a udržel domácí poptávku.
     → Argument: silný centralizovaný SD = automatický stabilizátor agregátní poptávky;
     slabý CZ model ho postrádá. Viz fig. A.1 (gdp_ppp_timeline), A.8 (wage_gdp_convergence).
     DATA KE DOPLNĚNÍ: index reálné mzdy CZ 2020–2024 z ČSÚ (tabulka PMH_CR);
     DK real wage index z Eurostat [earn_rwa_euind] nebo Danmarks Statistik.
   - APZ 0,3 % HDP bez rekvalifikační kapacity = závislost na mzdové deflaci
   - Wage share 27,8 % HDP (CMKOS) → nízký podíl zaměstnanců na produktu
   - Genderový mzdový gap 16,5 % (adjusted GPG, Eurostat 2023) = 5. nejvyšší v EU;
     slabý SD nevyjednává mzdovou rovnost — AT 14,5 %, DK 11,9 %, SK 10,7 %;
     within-sector analýza RSCP/ISPV: mezera přetrvává i v sektorech NACE G/I/K/M/O
     kde je počet mužů a žen srovnatelný → strukturální nerovnost nezávislá na sektorové volbě;
     viz A.20; inovace č. 3 (EU Pay Transparency Directive → mzdové tabulky v KS)
   - Příjmový vs. majetkový GINI: nízký příjmový GINI (24,4) kryje vysokou a rychle rostoucí
     majetkovou nerovnost. CZ wealth GINI = 77,7 (2021, UBS/Credit Suisse) — 4. nejvyšší v EU;
     nárůst +15,1 bodu za 13 let (62,6 v 2008 → 77,7 v 2021). Viz fig. A.18a (timeline),
     fig. A.18b (choropleth), nerovnost_CZ.md.

3. Oligarchizace a koncentrace vlastnictví médií:
   - Po 2008 krizi česká média přešla z rukou zahraničních vlastníků k domácím oligarchům.
     Do 2015 opustila trh poslední velká zahraniční skupina (Verlagsgruppe Passau → Penta).
   - Klíčoví vlastníci: Babiš/MAFRA (MF DNES, LN, iDNES.cz od 2013),
     Penta Investments (Vltava Labe Media), Křetínský/CMI (HN, Reflex).
   - RSF: CR pokleslo z 13. → 40. místa (2015–2021); RSF: „rise of the oligarchs."
   - Freedom House 2021: PM Babiš zvyšoval vliv nad médii od 2013; MAFRA čerpala
     státní podporu disproporčně v pandemii.
   - Důsledky pro SD: (a) zaměstnavatelská strana ovládaná úzkou skupinou, (b) média
     kontrolovaná oligarchy neposkytují prostor odborovým tématům, (c) politická propojenost
     vlastníků s vládními pozicemi, (d) veřejná debata o pracovních podmínkách marginalizovaná.
   - Detailní data: viz nerovnost_CZ.md oddíl 4.

4. SWOT analýza SD v CR → tabulka B.5
   Silné stránky: fungující RHSD, adekvátní právní rámec, CMKOS institucionální kapacita
   Slabiny: hustota 11 %, hist. nedůvěra, § 24 ZP pluralita, nízká APZ
   Příležitosti: rozšíření KSVS, Ghent APZ, EU Pay Directive 2023/970
   Hrozby: NERV deregulace, automatizace, politická  polarizace, oligarchizace médií

5. Korelační analýza (sekce hodnocení — Pilíř 3 hypotézy):
   - Odborová hustota × příjmový GINI (EU27 scatter) → fig. A.17 (union_gini_scatter)
     main.tex již má komentářový placeholder % \input{texparts/python/union_gini_scatter}
   - Pokrytí KV × čistý příjem v PPS (EU27 scatter) → fig. A.10 (coverage_income_pps_scatter)
   - Interpretace outlierů CR a SK: historický artefakt, vysvětlit v textu
   - Závěr: hypotéza POTVRZENA

---

### ch:inovace — Návrh inovace sociálního dialogu v CR

Inovace (očíslované):

1. Rozšíření závaznosti KSVS — snížit práh (§ 7 ZKV), vzor AT; cíl: pokrytí nad 60 %
2. Odbory jako agenti APZ — Ghent model; spoluřízení rekvalifikačních programů ÚP CR;
   nutnost zvýšit výdaje na APZ z 0,3 % → ~1 % HDP
3. Transparentnost odměňování — EU Pay Transparency Directive (2023/970), mzdové tabulky v KS
4. Digitalizace KV — veřejný registr PKS a KSVS transparentně dostupný (vzor BE/NL)
5. Posílení inspekce práce — SUIP cílení kontrol (Švarc, agenturní práce), §322 ZP BOZP
   Stanovisko DP: Inspekce práce je na dobré kvalitativní úrovni (cca 1:10 600 poměr
   inspektor:pracovník, splňuje ILO benchmark 1:10 000, ILC General Survey 2006, para. 263–265).
   Inovace č. 5 proto nesměřuje k navýšení počtu inspektorů, ale k efektivnějšímu cílení
   a k lepšímu propojení SUIP ↔ odbory (§ 322 ZP svazová inspekce BOZP).
6. Centralizace KV — mezisektorové KSVS pokrývající celé hodnotové řetězce (argument OSPZV-ASO)

Paralela s HRM: Employee Advocate role (Armstrong) — odbory jako nezávislý ekvivalent
vs. interní HR BP (střet zájmů).

Zdroje: ActiveEmploymentPolicy_Dvorakova.md, ETUI Benchmarking 2024

---

### ch:zaver — Závěr

Argument: Hypotéza potvrzena — CR trh práce je strukturálně zranitelnější kvůli kombinaci
slabého SD, nízké APZ, modelu levné práce a nadcházejících techno-demografických šoků.
4 případové studie KS empiricky dokládají formální existenci KV bez faktického posilování
pozice zaměstnanců. Prostor pro inovaci existuje, konkrétní návrhy v kap. ch:inovace.

Status: Přepsat celý texparts/zaver.tex (stávající obsah z jiné práce).

---

## 3. Dostupné zdroje — inventura

### Pilířové zdroje

| Pilíř | Soubor(y) | Obsah | Kapitola |
|-------|-----------|-------|----------|
| Legislativní rámec | CZ_LegislativniRamec_TRANSCRIPT.md (1 298 ř.) | ZKV, ZP, ZZ, ZDP, NV, Sdělení | sec:pojmy, sec:penny, sec:hodnoceni |
| Hala et al. (2013) | Hala_VZ361_TRANSCRIPT.md + _SystemySocialnihoDialogu.md | Komparativní SD 7 zemí EU, 372 s. | sec:pojmy, sec:teorie, sec:evropsky_kontext |
| CMKOS Zprava o KV 2025 | CMKOS_Zprava_KV_2025.md | Pokrytí KV, PKS benchmarks, KSVS rozšíření | sec:teorie, sec:evropsky_kontext, sec:penny |

### Případové studie KS

| Studie | Soubor | Řádků | Sektor |
|--------|--------|-------|--------|
| PKS Penny Market 2026 | PennyMarket_KS_2026.md | 334 | NACE 47.11 maloobchod |
| PKS Česká pošta 2025-2026 | CeskaPostaSP_KS_2025_2026.md | 548 | NACE 53 poštovní služby |
| KSVS OSPZV-ASO 2026 | KSVS_ASO_CMSZP_2026.md | 498 | NACE 01 + 10-12 |
| KSVS OS PPP 2026-2027 | KSVS_OSPPP_2026_2027.md | 409 | NACE 64-66 peněžnictví |
| DK Butiksoverenskomst 2023–2025 | — nutno stáhnout PDF | — | NACE 47 maloobchod (DK) |
| DK Finansoverenskomst + Nordea | — nutno stáhnout PDF | — | NACE 64 finance (DK) |

### Další scrape soubory

| Soubor | Kapitola |
|--------|----------|
| Armstrong_HRM_Handbook.md | sec:teorie, ch:inovace |
| Historie_odbory_a_spolecnost.md | sec:historie |
| 100_let_MOP.md | sec:pojmy, sec:historie |
| ActiveEmploymentPolicy_Dvorakova.md | sec:vyhled, ch:inovace |
| ZBORNKPRSPEVKOV_Dvorakova_DemografickeTrendy.md | sec:vyhled |
| UkraineRefugees_Polents_Dvorakova.md | sec:vyhled |
| Weber_Industrie40_Arbeitsmarkt.md | sec:vyhled |
| WojtczukTurek_SustainHRM_JobSatisfaction.md | sec:teorie |
| SRLZ_Dvorakova_PrezentaceHRM.md | kontext |
| PETRICEK_HOPO_Flexicurity_NOCITE.md | ssec:flexicurity (nepřímo) |
| PETRICEK_IND4_IndustrialRevolution_NOCITE.md | sec:historie, sec:vyhled (nepřímo) |
| NOCITE_Petricek_Flexicurity_Denmark.md | ssec:flexicurity (nepřímo) |
| nerovnost_CZ.md | sec:hodnoceni (GINI, majetkový GINI, RSF) |

### Zdroje dosud nedostupné — pozastavit nebo získat z internetu

| Zdroj | Priorita |
|-------|---------|
| Hrabcová, D. Sociální dialog (2008) | nízká — dostupné záznamy pokrývají |
| Ulrich, D. HR Champion (1997) | nízká — Armstrong covers |
| Andersen/Mailand: Danish Flexicurity (2005) | střední — viz web FAOS Copenhagen |
| OGB Austria materiály | střední — stáhnout web oegh.at |
| OECD Employment Outlook (AI chapter) | střední — stáhnout PDF z OECD |

---

## 4. Prioritní pořadí práce

Fáze 1 — Teoretická část:
1. sec:pojmy — TRANSCRIPT, ZKV, ZP, ZZ, ZDP
2. sec:historie — CMKOS Historie, 100 let MOP, Hala
3. sec:teorie — Hala, CMKOS Zprava, Armstrong

Fáze 2 — Analytická část:
4. ch:vyzkum — metodologie, pipeline, výběr zemí a KS
5. sec:evropsky_kontext — obalit existující figury textem; Hala komparace
6. sec:penny (rozšířit na 4 studie) — ze scrape; průřezová tabulka B.2; legislativní re-evaluace
7. sec:vyhled — CMKOS, Dvorakova, TRANSCRIPT §7, CSSZ data pro A.19
8. ch:uvod — po zvládnutí obsahu formulovat přesně

Fáze 3 — Evaluace a syntéza:
9. sec:hodnoceni — SWOT + oponování hypotézy + korelační analýza (A.17, A.10)
10. ch:inovace — 6 inovačních návrhů
11. ch:zaver
12. Bibliografie — doplnit .bib záznamy (viz nerovnost_CZ.md oddíl 6 pro 3 nové záznamy)

---

## 5. Kritická cesta k hypotéze

HYPOTEZA: CZ trh práce je zranitelnější kvůli slabému sociálnímu dialogu.

PILIR 1 — Slabý sociální dialog (deskriptivní):
  Union density 11 % (ETUI/CMKOS) vs. AT 26 % / DK 67 %
  KV coverage 32 % vs. AT 98 % / DK 80 %
  Rozšiřování KSVS: 2 v 2025 (CMKOS)
  Historické příčiny: ROH + ztráta důvěry (CMKOS Historie)
  § 24 ZP pluralita → fragmentace (Penny Market: 4 ZO)

PILIR 2 — Zranitelnost trhu práce (analytický):
  Model levné práce: 39,6 h/týden za nízké reálné mzdy v PPS
  HDP konverguje rychleji než mzdy (Eurostat, A.8)
  AI + automatizace → exponovaná ekonomická struktura (Weber 2015)
  Demografický tlak: old-age dependency 32 % (Eurostat)
  APZ 0,3 % HDP vs. DK 2 % (CMKOS/Eurostat)
  OSVC/Švarc → erodování odvodové základny (TRANSCRIPT §7; CSSZ data, A.19)
  Oligarchizace → oslabení veřejné debaty o práci (RSF, Freedom House)

PILIR 3 — Kauzální logika (komparativní + korelační):
  Hala et al. 2013: srovnání 7 zemí → silnější SD = lepší výsledky
  Scatter: union density × GINI (A.17) → negativní korelace EU27
  Scatter: CB coverage × net income PPS (A.10) → pozitivní korelace EU27
  AT: 98 % pokrytí díky automatickému rozšiřování KSVS
  DK: Ghent system → silný SD + APZ = pružný trh jako kontrast k CR

PILIR 4 — Empirická verifikace (4 případové studie):
  Penny Market: KS formálně existuje, reálně zákonné minimum nebo pod KSVS
  Česká pošta: tarifní systém jako substituent zaručené mzdy po NV 326/2023
  OSPZV-ASO: mezisektorový přesah → argument pro centralizaci KV
  OS PPP: bankovnictví = nejsilnější nadstandard → korelace s vyjednávací silou OO

VYSLEDEK → Hypotéza POTVRZENA:
  Slabý SD = neschopnost tlačit na mzdy, koordinovat APZ,
  adaptovat trh na technologické šoky → větší strukturální zranitelnost.

INOVACE (normativní část):
  Rozšíření KSVS, Ghent APZ, transparentnost, centralizace KV, inspekce, digitalizace.
