# Výzkumný a argumentační plán DP — verze 3
## Sociální dialog a kolektivní vyjednávání
### Petříček Jiří | MÚVS ČVUT | PRI | aktualizace: 2026-04-06

---

## ZMĚNOVÝ PŘEHLED oproti v2

1. **Kap. 2 přejmenována:** „Sociální dialog a kolektivní vyjednávání" → **„Legislativní, historický a teoretický rámec sociálního dialogu"** — reflektuje skutečný obsah: zákonný rámec (ZP, ZKV, ZZ, ZDP), historický vývoj a rešerše současného poznání.
2. **Legislativní rámec posilněn** — nově zahrnuje kompletní scrape ZP (§§ 2–3, 22–29, 52, 61–63, 109–118, 191–210, 213, 227–232, 241/241a, 276–287, 306, 307a–309, 317, 322, 338–341), ZKV (§§ 1–31), ZZ (§§ 1–2, 5(e), 7, 12, 14, 39–51, 58–60, 67–84, 104–120f, 139–140), ZDP (§§ 2a, 7, 7a) + podzákonné předpisy (NV 567/2006, NV 326/2023, NV 443/2024, Sdělení 17/2026, Sdělení 47/2026).
3. **Případová studie rozšířena** z jedné (Penny Market) na **4 případové studie** — 2 PKS (Penny Market 2026, Česká pošta 2025–2026) + 2 KSVS (OSPZV-ASO zemědělství 2026, OS PPP peněžnictví 2026–2027).
4. **Zdroje omezeny** na fyzicky dostupné a již zpracované (23 scrape souborů) — odstraněny reference na nedostupné monografie (Hrabcová, Ulrich, Andersen/Mailand, ÖGB).
5. **Hála et al. (2013)** a **ČMKOS Zpráva o KV 2025** zvýrazněny jako dva pilířové zdroje vedle legislativního rámce.
6. **Kap. 3.3 Flexicurity** odsunuta jako součást stavu trhu práce; **nová kap. 3.3 = Případové studie KS/KSVS**.
7. **Nová sekce §7 v TRANSCRIPT** (Švarc systém, agenturní zaměstnávání, paušální daň) integrována do argumentace kap. 2.1 i kap. 3.3.

---

## GLOBÁLNÍ INSTRUKCE PRO CELOU PRÁCI

*(beze změny viz v2 — pasivní forma, modulární \\input, matematický popis, ověření dat, oponování hypotézy, kontrolní seznam po každé kapitole)*

### Vysvětlení PPS (Purchasing Power Standard / Parita kupní síly)
V práci je opakovaně používán ukazatel **PPS** (Purchasing Power Standard). Je nutné jej vysvětlit
v textu při prvním použití (kap. 3.1 Metodologie) a definovat formálně:

> **PPS** (Purchasing Power Standard) je umělá měnová jednotka Eurostatu, která eliminuje rozdíly
> v cenových hladinách mezi zeměmi. Jeden PPS kupuje v každé zemi stejný objem zboží a služeb.
> Přepočet na PPS umožňuje srovnání reálné kupní síly obyvatel napříč EU —
> rozdíl mezi nominálním a PPS vyjádřením odhaluje, nakolik je cenová hladina dané země
> nižší/vyšší než průměr EU-27.

Formální definice (LaTeX):
```latex
\begin{equation}
  x_i^{\mathrm{PPS}} = \frac{x_i^{\mathrm{EUR}}}{\mathrm{PPP}_i / \mathrm{PPP}_{\mathrm{EU27}}}
  \label{eq:pps_conversion}
\end{equation}
```
kde $x_i^{\mathrm{EUR}}$ je hodnota ukazatele v EUR, $\mathrm{PPP}_i$ je parita kupní síly země $i$ a $\mathrm{PPP}_{\mathrm{EU27}}$ je průměr EU-27.

**Pravidlo:** Všude, kde se v práci srovnávají mzdy nebo příjmy mezi zeměmi, používat PPS vyjádření.
Nominální hodnoty v EUR použít pouze pro vnitrostátní srovnání. Příp PPS hodnoty dopočítat.

---

## 1. CÍL PRÁCE A HYPOTÉZA

**Cíl:** Zmapovat potenciál inovace sociálního dialogu v ČR pro konkurenceschopnost na trhu práce prostřednictvím analýzy relevantních statistických ukazatelů a porovnání v evropském kontextu.

**Hypotéza:** Český trh práce je zranitelnější vůči vývoji práce v blízké budoucnosti kvůli slabému sociálnímu dialogu.

**Výzkumné otázky:**
1. Jaké faktory budou v blízké budoucnosti působit na český trh práce?
2. Sehrává sociální dialog na vyspělých evropských trzích práce významnou roli?
3. Je sociální dialog a KV v ČR v evropském kontextu na dobré úrovni?
4. Jak lze inovovat sociální dialog pro zvýšení konkurenceschopnosti CZ trhu práce?

**Metody:**
- Kvantitativní: statistická analýza trendů, korelační analýza (Eurostat, OECD, MPSV, ČSSZ, ILO)
- Kvalitativní: syntéza literatury, komparativní analýza modelů, případové studie (4 KS/KSVS)
- Komparativní: časové, regionální a systémové

---

## 2. KAPITOLOVÁ STRUKTURA — ARGUMENTAČNÍ TOK

### KAPITOLA 1: Úvod

**Argument:** Uvést kontext: zrychlující se technologický vývoj (i4.0, AI) × model levné práce v ČR = narůstající napětí, které si žádá silný sociální dialog.

**Obsah:**
- Vymezení cíle a předmětu práce
- Vyslovení hypotézy
- Popis struktury práce, použitých metod (povrchově) a popis případových studií (4 KS)

**Zdroje:** Zadání DP, PJDP2026L (projekt DP), Armstrong HRM Handbook

**Status:** Nutno napsat. Stávající uvod.tex je z jiné práce.

**Rozsah:** cca 4000 znaků.

---

### KAPITOLA 2: Legislativní, historický a teoretický rámec

> **Přejmenování:** původní „Sociální dialog a kolektivní vyjednávání" — nový název lépe odráží, že kapitola pokrývá legislativu, historii i rešerši současného poznání.
úvod do kapitoly cca 2000 znaků - zdůvodnit proč je co shrnováno. Zmínit zaměření dosavadních DP (uložených v nocite) - systém odměňování, DP z právnikých fakult, jaký nový pohled přináší tato práce


#### 2.1 Pojmy a vztahy — legislativní úprava

**Argument:** Definovat pojmy přesně dle české legislativy a mezinárodních standardů ILO/EU. Legislativní rámec CZ je formálně srovnatelný s EU, ale faktická implementace zaostává.

**Vnitřní členění:**

| Subsekce | Obsah | Legislativní základ (TRANSCRIPT) |
|----------|-------|----------------------------------|
| Základní pojmy | SD, KV, KS, PSP (tripartita, bipartita) | Hála kap. I (definice ILO) |
| Zákon o KV | Proces KV, uzavírání KS, řešení sporů, rozšiřování závaznosti KSVS | ZKV §§ 1–31 (TRANSCRIPT §1) |
| ZP — kolektivní smlouvy | Pluralita OO, obsah a hierarchie KS, ochrana funkcionářů | ZP §§ 22–29 (TRANSCRIPT §2) |
| ZP — odměňování a zaručená mzda | Minimální mzda, příplatky, průměrný výdělek, zaručená mzda a její reforma (NV 567/2006 → NV 326/2023 → NV 443/2024) | ZP §§ 109–118 (TRANSCRIPT §2.5–2.6) |
| ZP — překážky v práci | Překážky na straně Z a ZL, náhrady mzdy | ZP §§ 191–210 (TRANSCRIPT §2.7) |
| ZP — výpověď a hromadné propouštění | Výpovědní důvody, souhlas OO, hromadné propouštění | ZP §§ 52, 61, 62–63 (TRANSCRIPT §2.8) |
| ZP — další pracovněprávní ochrana | Dovolená, pracovní řád, BOZP inspekce, převod zaměstnanců (TUPE) | ZP §§ 213, 306, 322, 338–341 |
| ZP — home office a práce na dálku | Rámec § 317, specifika § 241/241a (pečující), nadstandard v KS | ZP §§ 241/241a, 317 |
| ZP — závislá práce a nelegální práce | Definiční znaky závislé práce, Švarc systém, nelegální práce, sankce | ZP §§ 2–3; ZZ § 5(e), §§ 139–140 (TRANSCRIPT §7.1–7.3) |
| ZP — agenturní zaměstnávání | Trojúhelníkový vztah, rovné zacházení, 12měsíční limit, KS-only scope | ZP §§ 307a–309; ZZ §§ 14, 58, 60 (TRANSCRIPT §7.4) |
| ZDP — paušální daň a OSVČ | Podmínky paušálního režimu, 3 pásma, erozivní efekt na sociální systém | ZDP §§ 2a, 7, 7a (TRANSCRIPT §7.5) |
| Zákon o zaměstnanosti | Definice trhu práce, APZ, zprostředkování, agenturní licence | ZZ §§ 1–2, 7, 39–51, 67–84, 104–120f |
| Rozšiřování závaznosti KSVS | CZ praxe (2 rozšíření v 2025), srovnání s AT (98%), Sdělení 17/2026 a 47/2026 | ZKV § 7; Sdělení MPSV (TRANSCRIPT §4–5) |
| Mezinárodní rámec | ILO Conventions 87+98, EU Social Charter, Eurofound | Hála kap. I, 100 let MOP |

**Pilířové zdroje:**
- **Legislativní rámec:** `CZ_LegislativniRamec_TRANSCRIPT.md` (1 298 řádků, 7 oddílů) — kompletní scrape zákonů
- **Hála et al. (2013):** `Hala_VZ361_TRANSCRIPT.md` — komparativní systémy SD v EU (372 s.)
- **ČMKOS Zpráva o KV 2025:** `CMKOS_Zprava_KV_2025.md` — aktuální data o pokrytí KV, PKS benchmarks
- Armstrong HRM Handbook (kap. collective bargaining, employee relations)
- 100 let MOP (ILO konvence, historický kontext)

-> zavést zkratky pomocí acro (vložit záznamy do seznamu)

---

#### 2.2 Historický vývoj

**Argument:** Odborové hnutí vzniklo jako reakce na industrializaci; dnes je AI analogický šok. V ČR přetrvává trauma komunistického formálního odboritví → nedůvěra k odborům.

**Členění:**
1. Vznik odborů (19. stol.) — industrializace, sociální legislativa
2. ILO a meziválečné období — první republika, vznik odborové tradice v ČSR
3. Komunistické odbory — ROH, absence skutečného vyjednávání
4. Transformace po 1989 — vznik RHSD, ČMKOS, legislativní rámec
5. Strukturální pokles odborové hustoty (1990 → 2024: z ~80 % na 11 %)
6. Průmysl 4.0 a AI jako nový industrializační šok — historická analogie

**Zdroje:**
- ✅ `Historie_odbory_a_spolecnost.md` (ČMKOS 2020) — dějiny odborů
- ✅ `100_let_MOP.md` (Pokorný 2019) — ILO, meziválečné období
- ✅ `Hala_VZ361_TRANSCRIPT.md` — historický kontext SD v EU (kap. I, kap. VII/CZ)
- ✅ `PETRICEK_IND4_IndustrialRevolution_NOCITE.md` — argumenty (přepsat, nepřímo citovat)
- ⚠️ Data: OECD AIAS ICTWSS / ILOSTAT TUR (odborová hustota 1990–2024) — **DATA K STAŽENÍ**

---

#### 2.3 Přehled současného poznání

**Argument:** Rešerše dostupné literatury k sociálnímu dialogu — Hála (komparativní), Armstrong (HRM), Dvořáková (CZ kontext), ČMKOS zpráva (empirická data).

**Subsekce:**
1. Komparativní systémy SD v EU — **Hála et al. (2013)** jako hlavní zdroj
   - Srovnávací tabulka 7 zemí (Hála s. 228–229): pokrytí KS, odborová hustota, tripartita
   - Závěr Hály (s. 286–288): „obdobně se to týká i dalších postkomunistických zemí včetně ČR"
   - Trend decentralizace KV v Evropě (Hála kap. I)
   - EU average CB coverage 66 % (Hála kap. I)
   - **chybí Dánsko**
2. HRM perspektiva — Armstrong: Employee Advocate role, kolektivní vyjednávání jako HRM nástroj
3. CZ akademický kontext — Dvořáková (2012, 2024, 2025): ŘLZ, APZ, demografické trendy
4. Empirická evidence — **ČMKOS Zpráva o KV 2025** jako klíčový datový zdroj
   - Pokrytí KV v CZ: 32 %
   - PKS benchmarks: příplatky, dovolená, penzijní připojištění (71 % PKS)
   - Rozšiřování KSVS: 2 v roce 2025
   - Veřejný vs. soukromý sektor: mzdová disparita

**Zdroje:**
- ✅ `Hala_VZ361_TRANSCRIPT.md` — **klíčový komparativní zdroj**
- ✅ `Hala_VZ361_SystemySocialnihoDialogu.md` — summary/notes
- ✅ `CMKOS_Zprava_KV_2025.md` — empirická data KV
- ✅ `Armstrong_HRM_Handbook.md`
- ✅ `ActiveEmploymentPolicy_Dvorakova.md`
- ✅ `ZBORNKPRSPEVKOV_Dvorakova_DemografickeTrendy.md`
- ✅ `WojtczukTurek_SustainHRM_JobSatisfaction.md`
- ✅ `Weber_Industrie40_Arbeitsmarkt.md` (Industry 4.0 → labour market)

---

### KAPITOLA 3: Stav trhu práce (Praktická část)

#### 3.1 Postup výzkumu — metodologie

**Obsah:**
- Vymezení výzkumné strategie (kvantitativní + kvalitativní + komparativní)
- Zdůvodnění výběru zemí: AT (Kammer-system, 98 % KV, společná historie), DE (Mitbestimmung, obchodní partner), DK (flexicurity model), PL/SK (nové členské země)
- Popis datových zdrojů (Eurostat, OECD, MPSV, ČSSZ, ČMKOS, ILO, ETUI)
- Popis Python analytického pipeline
- Metoda případové studie — 4 KS (2 PKS + 2 KSVS): výběr podle dostupnosti, sektorové diverzity a hierarchické úrovně → viz 3.3
- Limity výzkumu

**Zdroje:** Armstrong HRM, PJDP2026L projekt DP

---

#### 3.2 Evropský kontext — srovnávací analýza

**Argument:** CZ má výrazně nižší odborovou hustotu a pokrytí KV než srovnatelné ekonomiky. Mezinárodní srovnání ukazuje korelaci: silný SD → kratší pracovní týden, lepší podmínky. CZ trh je „cheap labour trap" — HDP konverguje rychleji než reálné mzdy v PPS.

**Subsekce:**
1. Srovnávací přehled — flexicurity tabulka (6 zemí × 7 ukazatelů) — **existující flexicurity_table.tex**
2. Flexicurity — kritická analýza dánského modelu a jeho CZ deformace
   - DK zlatý trojúhelník: flexibilita + příjmová jistota + APZ
   - CZ adoptovala pouze flexibilitu (flexinovela ≥ 2007) bez investic do APZ
   - APZ výdaje: CZ ~0,3 % HDP vs. DK ~2 % HDP
3. Komparativní modely SD — syntéza z **Hála et al. (2013)**:
   - AT: Kammer-system → 98 % pokrytí s 26 % hustotou
   - DE: Mitbestimmung + Hartz reformy (varování)
   - DK: Ghent-system, dobrovolný rámec
   - PL/SK: postsovětská trajektorie, srovnání s CZ
4. Interpretace GINI/AROPE paradoxu — nízké CZ nerovnosti jsou důsledkem komunistické nivelizace a relativní definice chudoby, ne zásluhou SD

**Existující figury:** `gdp_ppp_timeline`, `tax_wedge_map`, `flexicurity_table`, `arope_map_2025`, `arope_timeline_CE`, `arope_groups`

**Zdroje:**
- ✅ `Hala_VZ361_TRANSCRIPT.md` — srovnávací tabulka zemí, kap. II–VII (AT/DE/DK/PL/SK/UK/CZ)
- ✅ `CMKOS_Zprava_KV_2025.md` — CZ empirická data
- ✅ `PETRICEK_HOPO_Flexicurity_NOCITE.md` — základ flexicurity argumentů (přepsat)
- ✅ Eurostat datasety (viz python/data/*.csv) — HDP, GINI, AROPE, zaměstnanost, prac. hodiny, daňový klín, PLI, old-age dependency
- ✅ ETUI CB coverage data (v flexicurity_table)

---

#### 3.3 Případové studie kolektivních smluv (NOVÝ FORMÁT — 4 studie)

**Argument:** Analýza 4 reálných KS ukazuje jak funguje kolektivní vyjednávání na dvou úrovních (PKS a KSVS) a ve 4 sektorech. Hierarchie KSVS → PKS (§ 27(1) ZP) je testována přímo konfrontací textu smluv. Legislativní re-evaluace odhaluje, kde KS substituují státní regulaci (zaručená mzda) a kde přetrvávají regulatorní mezery.

**Struktura společná pro každou studii:**
1. Identifikace stran, sektoru, platnosti
2. Pracovněprávní podmínky (pracovní doba, odměňování, příplatky, dovolená, BOZP, překážky)
3. Specifika KS nad zákonný rámec (nadstandard vs. zákonné minimum)
4. Legislativní re-evaluace (cross-reference se scrape TRANSCRIPT)
5. Srovnání s benchmarky (ČMKOS Zpráva, zákonné minimum, ostatní KS)

---

##### 3.3.1 PKS Penny Market 2026 (CZ-NACE 47.11 — maloobchod)

**Zaměstnavatel:** Penny Market, s.r.o. (~10 000 zaměstnanců)
**Smluvní strany:** 4 ZO (OSPO-ASO, OSPZV-ASO, UZO Opava, UZO Petřvald) — pluralita § 24 ZP
**Sektor:** Maloobchod s potravinami (CZ-NACE 47.11)

**Klíčová zjištění ze scrape:**
- Pracovní doba 40h = zákonné minimum, vyrovnávací období až 52 týdnů
- Přesčas příplatek 25 % = zákonné minimum (KSVS OSPZV-ASO stanoví 40 %)
- Penzijní připojištění 800 Kč/měs < KSVS (1 000–1 350 Kč)
- Top Employer 2026 certifikace — absence zmínky o sociálních partnerech
- § 27(1) ZP porušení: PKS horší než KSVS v přesčasu a penzijním příspěvku
- **Sektorový nesoulad:** KSVS OSPZV-ASO pokrývá NACE 01+10-12 (zemědělství/potravinářství), ne NACE 47.11 → vazba přes § 25(2) ZP (odborová afiliace) → argument pro centralizaci KV

**Zdroje:**
- ✅ `PennyMarket_KS_2026.md` (334 řádků) — kompletní scrape + re-evaluace
- ✅ `CMKOS_Zprava_KV_2025.md` — benchmarky PKS
- ✅ `CZ_LegislativniRamec_TRANSCRIPT.md` — cross-reference legislativy

---

##### 3.3.2 PKS Česká pošta, s.p. 2025–2026 (CZ-NACE 53 — poštovní služby)

**Zaměstnavatel:** Česká pošta, s.p. (~25 000 zaměstnanců) — státní podnik
**Smluvní strany:** Více OO — pluralita, státní podnik
**Sektor:** Poštovní a kurýrní služby (CZ-NACE 53)

**Klíčová zjištění ze scrape:**
- 12 tarifních stupňů → substituují zrušenou státní zaručenou mzdu (8 skupin NV 567/2006 → zrušeno NV 326/2023)
- Příplatky nad ZP: noční +5pp, so/ne +2pp
- TUPE riziko: státní podnik — transformace → §§ 338–341 ZP
- HO/péče o děti: žádná úprava v PKS (vs. benchmark KSVS OSPPP)
- Švarc nízké riziko v jádru; chybí agenturní limit (opominutí § 309(8))

**Zdroje:**
- ✅ `CeskaPostaSP_KS_2025_2026.md` (548 řádků) — kompletní scrape + re-evaluace

---

##### 3.3.3 KSVS OSPZV-ASO ČR / ZS ČR / ČMSZP 2026 (CZ-NACE 01 + 10–12 — zemědělství a potravinářství)

**Smluvní strany:** OSPZV-ASO ČR (odbory) × Zemědělský svaz ČR + ČMSZP (zaměstnavatelé)
**Sektor:** Zemědělství (NACE 01) a potravinářský průmysl (NACE 10–12)
**Extenze:** Sdělení 47/2026 Sb. — rozšíření závaznosti na NACE 01.1–01.6

**Klíčová zjištění ze scrape:**
- Tarifní systém (tarify dle platové třídy) → de facto náhrada zaručené mzdy
- Přesčas v noci/NVO 40 % = +15pp nadstandard nad ZP
- Příplatky: noční 20 %, so/ne 20 % — obojí +10pp nad ZP
- Inflační doložka (3 % trigger) — unikátní mechanismus v CZ kontextu
- Sdělení 47/2026: extenze pokrývá pouze NACE 01.1–01.6, nepůsobí na maloobchod
- § 306 pracovní řád — OO souhlas sjednán v KSVS
- Chybí limit agenturního zaměstnávání — zemědělství = významný uživatel agenturní práce
- **Mezisektorový přesah:** OSPZV-ASO organizuje pracovníky napříč celým potravinovým řetězcem (farma → zpracování → prodej) → argument pro centralizaci KV

**Zdroje:**
- ✅ `KSVS_ASO_CMSZP_2026.md` (498 řádků) — kompletní scrape + re-evaluace

---

##### 3.3.4 KSVS OS PPP / SBP 2026–2027 (CZ-NACE 64–66 — peněžnictví a pojišťovnictví)

**Smluvní strany:** OS pracovníků peněžnictví a pojišťovnictví (odbory) × Svaz bank a pojišťoven (zaměstnavatelé)
**Sektor:** Finanční služby (NACE 64–66)

**Klíčová zjištění ze scrape:**
- Minimální mzda 28 000 Kč = +25 % nad MM (22 750 Kč v 2026)
- So/ne příplatek 50 % = 5× zákon (10 %) — nejvyšší ze všech 4 KS
- § 61 souhlas OO k výpovědi funkcionáře — explicitně sjednán
- § 306 blokační právo OO nad pracovním řádem
- § 322 svazová inspekce BOZP — explicitně v KS
- HO čl. 7 — regulatorní gap-filling (vs. § 317 ZP pouhý rámec)
- Hromadné propouštění — anticipace digitalizace v bankovním sektoru
- Švarc irelevantní (ČNB compliance); agenturní limit chybí i zde

**Zdroje:**
- ✅ `KSVS_OSPPP_2026_2027.md` (409 řádků) — kompletní scrape + re-evaluace

---

##### 3.3.5 Průřezová analýza — srovnání 4 KS

**Srovnávací tabulka:**

| Parametr | Penny Market (PKS) | Česká pošta (PKS) | OSPZV-ASO (KSVS) | OS PPP (KSVS) | ZP minimum |
|----------|-------------------|-------------------|-------------------|---------------|------------|
| Přesčas příplatek | 25 % | 25 % + vol. čas | 40 % (noc/NVO) | nespecif. | 25 % |
| Noční příplatek | 10 % | 15 % | 20 % | nespecif. | 10 % |
| So/ne příplatek | 10 % | 12 % | 20 % | 50 % | 10 % |
| Dovolená | 5 týdnů | 5 týdnů | 5 týdnů | 5 týdnů | 4 týdny |
| Penzijní příspěvek | 800 Kč | ano (tarif) | 1 000–1 350 Kč | ano | — |
| HO úprava | ne | ne | ne | čl. 7 | § 317 rámec |
| Tarifní systém | ne | 12 stupňů | ano | min. 28 000 Kč | — |
| Inflační doložka | ne | ne | ano (3 %) | ne | — |
| Agenturní limit | ne | ne | ne | ne | § 309(6): 12 měs. |
| § 61 ochrana OO | ne | ne | ne | ano | § 61(2) |
| § 306 prac. řád OO | ne | ne | ano | ano | § 306(4) |

**Analytické závěry průřezu:**
1. **Hierarchie KSVS → PKS (§ 27(1)):** Penny Market fakticky porušuje — přesčas a penzijní příspěvek pod KSVS (jenže ta KSVS je jiný sektor...)
2. **KSVS jako substituent státní regulace:** Po zrušení 8 skupin zaručené mzdy (NV 326/2023) jsou tarifní tabulky v KSVS jedinou bariérou proti soutěži o nejnižší mzdu
3. **Sektorová diverzita:** Bankovnictví (OS PPP) vykazuje nejsilnější nadstandard — koreluje s vyšší přidanou hodnotou sektoru a vyšší vyjednávací silou OO
4. **Regulatorní mezery:** HO, agenturní zaměstnávání a hromadné propouštění — nedostatečně pokryté ve všech 4 KS
5. **Centralizace KV:** Mezisektorový přesah OSPZV-ASO (NACE 01 → 10–12 → 47) demonstruje potenciál i rizika centralizace

---

#### 3.4 Stav a výhled CZ trhu práce

**Argument:** CZ trh čelí souběžným výzvám, které zesilují zranitelnost.

**Subsekce:**

| Faktor | Klíčový argument | Dostupný zdroj |
|--------|------------------|----------------|
| AI a automatizace | Levná práce ohrožena; AI eliminuje junior pozice; zkracování inovačních cyklů | Weber (2015), PETRICEK_IND4 (nocite) |
| Demografické tlaky | Old-age dependency 32 %; stárnutí → zvýšené nároky na sociální systém | Eurostat `A.OLDDEP1`, Dvořáková demografie |
| Imigrace z Ukrajiny | ~340 000 uprchlíků → tlak v nízkokvalifikovaných sektorech | Polents/Dvořáková (2024) |
| OSVČ a Švarc systém | Nadprůměrné % OSVČ v EU; paušální daň → erodování sociálních odvodů | TRANSCRIPT §7.5 (ZDP §§ 2a/7/7a); ČMKOS |
| Agenturní zaměstnávání | Trojúhelníkový vztah; rovné zacházení často obcházeno; zemědělství jako rizikový sektor | TRANSCRIPT §7.4 (ZP §§ 307a–309) |
| Veřejný sektor | Mzdová zaostalost (vzdělávání +2,7 % vs. NH +7,1 %) → odliv kvalifikovaných | ČMKOS Zpráva kap. 3.8 |
| Regionální diferenciace | Praha +26,7 % nad průměrem NH; krajská nerovnost | ČMKOS Zpráva; MPSV/ISPV |

---

#### 3.5 Hodnocení sociálního dialogu v ČR

**Struktura argumentace (oponování hypotézy):**

1. **Protiargumenty** (uvést poctivě):
   - AROPE 12 % = nejnižší ze skupiny → **fig. A.3 choropleth**
   - Zaměstnanost 81,7 %
   - Reálný mzdový růst 2024 = +4,6 %
   - GINI 24,4 = nízká nerovnost → **fig. A.16 choropleth**

2. **Systematické vyvrácení**:
   - AROPE hranice = relativní (60 % mediánu) → nízké absolutní příjmy v PPS
   - Délka prac. týdne 39,6 h = nejdelší ze skupiny → pracovník pracuje déle za méně
   - HDP konverguje rychleji než mzdy → cheap labour trap přetrvává
   - APZ 0,3 % HDP → bez rekvalifikační kapacity = závislost na mzdové deflaci
   - Wage share 27,8 % HDP (ČMKOS) → nízký podíl zaměstnanců na produktu
   - **Příjmový GINI vs. majetkový GINI:** Nízký příjmový GINI (24,4) maskuje vysokou
     a rychle rostoucí **majetkovou** nerovnost. CZ wealth Gini = 77,7 (2021, Credit Suisse/UBS) —
     4\. nejvyšší v EU (po SE 87,2, LV 80,9, CY 80,7). Nárůst +15,1 bodu za 13 let
     (z 62,6 v 2008). Kontrast: SK = 50,3 (nejnižší v EU). → **fig. A.18 choropleth**

3. **Oligarchizace a koncentrace vlastnictví médií v ČR**
   - **Rychlá koncentrace majetku:** Po 2008 finanční krizi se česká média vrátila z rukou
     zahraničních vlastníků k domácím oligarchům. Do 2015 opustila trh poslední velká
     zahraniční skupina (Verlagsgruppe Passau → Penta Investments).
   - **Klíčoví vlastníci:**
     - Andrej Babiš: MAFRA (MF DNES, Lidové noviny, iDNES.cz) — od 2013
     - Penta Investments (SK): Vltava Labe Media — regionální média
     - Daniel Křetínský: Czech Media Invest (dříve Economia)
     - PPF (Kellner/Kellnerová): TV Nova (do prodeje 2020)
   - **RSF (Reportéři bez hranic):** CZ pokleslo z 13. místa (2015) na 40. místo (2021)
     ve World Press Freedom Index. RSF explicitně hovoří o „rise of the oligarchs" v českých médiích.
   - **Freedom House (2016):** Koncentrované vlastnictví médií + vlastnictví médií politiky =
     hlavní překážky svobody médií v ČR.
   - **Majetkový GINI jako indikátor:** CZ wealth Gini 77,7 (2021) je sice nižší než RU (87,8),
     ale tempo nárůstu je jedno z nejrychlejších v EU. Nízký příjmový GINI maskuje rychlou
     koncentraci majetku v rukou úzké skupiny (Forbes CZ: 11 miliardářů, 1,01 na milion obyvatel).
   - **Důsledek pro SD:** Oligarchizace podkopává sociální dialog: (a) zaměstnavatelská strana
     je ovládána úzkou skupinou, (b) média kontrolovaná oligarchy nedávají prostor odborovým
     tématům, (c) politické elity jsou propojeny s vlastnickými strukturami (Babiš = premiér +
     mediální vlastník), (d) veřejná debata o pracovních podmínkách je systematicky marginalizována.
   - **Zdroje:** RSF Czech Republic country profile; Freedom House Nations in Transit 2021;
     Wikipedia „Mass media in the Czech Republic"; Credit Suisse/UBS Global Wealth Databook 2021

3. **SWOT analýza SD v ČR**

4. **Korelační analýza** (scatter ploty — pokud data dostupná):
   - Odborová hustota × GINI (EU27 panel)
   - Pokrytí KV × průměrná týdenní pracovní doba

---

### KAPITOLA 4: Návrh inovace sociálního dialogu v ČR

**Inovace (očíslované):**

1. **Rozšíření závaznosti KSVS** — snížit práh, vzor AT → dosáhnout pokrytí nad 60 %
2. **Odbory jako agenti APZ** — Ghent model; spoluřízení rekvalifikačních programů ÚP
3. **Transparentnost odměňování** — EU Pay Transparency Directive (2023/970), mzdové tabulky
4. **Digitalizace KV** — veřejný registr PKS (vzor BE/NL)
5. **Posílení inspekce práce** — SÚIP personální navýšení, Švarc enforcement

> **Stanovisko DP k SÚIP:** Inspekce práce v ČR je na dobré kvalitativní úrovni. SÚIP + 8 krajských
> inspektorátů práce (KIP) disponuje cca 500+ (find source on SUIP) inspektory na ~5,3 mil. zaměstnanců, tj. poměr
> přibližně **1 inspektor : 10 600 pracovníků**. Toto splňuje benchmark ILO (Úmluva č. 81 +
> technické doporučení ILO): **1 inspektor na 10 000 zaměstnanců** v průmyslových tržních
> ekonomikách (1:15 000 pro industrializující se, 1:20 000 pro tranzitní/nejméně rozvinuté).
> Zdroj: *ILO, Labour Inspection: Policy and Practice* (ILC General Survey 2006, para. 263–265);
> potvrzeno rovněž v *Piore & Schrank (2008), "Toward managed flexibility"*.
> 
> **Důsledek pro argumentaci:** Problém CZ SD není v nedostatečném aparátu inspekce, ale v tom,
> že i kvalitní inspekce nemůže nahradit funkční systém kolektivního vyjednávání. SÚIP kontroluje
> dodržování platné legislativy, ale nemůže vyjednat nadstandardní podmínky — to je role KV.
> Inovace č. 5 proto nemá primárně směřovat k navýšení počtu inspektorů, ale k efektivnějšímu
> cílení kontrol (Švarc systémy, nelegální práce agentur) a k lepšímu propojení SÚIP ↔ odbory
> (§ 322 ZP svazová inspekce BOZP).
6. **Centralizace KV** — mezisektorové KSVS pokrývající celé hodnotové řetězce (argument z OSPZV-ASO)

**Paralela s HRM:** Employee Advocate role (Armstrong) — odbory jako nezávislý ekvivalent vs. interní HR BP (střet zájmů)

---

### KAPITOLA 5: Závěr

**Argument:** Hypotéza potvrzena/upřesněna: CZ trh práce je strukturálně zranitelnější kvůli kombinaci slabého SD, nízké APZ, modelu levné práce a nadcházejících šoků. 4 případové studie KS empiricky dokládají formální existenci KV bez faktického posilování pozice zaměstnanců. Prostor pro inovaci existuje.

---

## 3. DOSTUPNÉ ZDROJE — INVENTURA

### Pilířové zdroje (trojice)

| Pilíř | Soubor(y) | Obsah | Využití |
|-------|-----------|-------|---------|
| **Legislativní rámec** | `CZ_LegislativniRamec_TRANSCRIPT.md` (1 298 ř.) | ZKV, ZP, ZZ, ZDP, NV, Sdělení — kompletní scrape | kap. 2.1, 3.3 (re-evaluace), 3.5 |
| **Hála et al. (2013)** | `Hala_VZ361_TRANSCRIPT.md` + `_SystemySocialnihoDialogu.md` | Komparativní SD systémy 7 zemí EU, 372 s. | kap. 2.1, 2.3, 3.2 |
| **ČMKOS Zpráva o KV 2025** | `CMKOS_Zprava_KV_2025.md` | Pokrytí KV, PKS benchmarks, mzdy, KSVS rozšíření | kap. 2.3, 3.2, 3.3 (benchmarky), 3.5 |

### Případové studie

| Studie | Soubor | Řádků | Sektor |
|--------|--------|-------|--------|
| PKS Penny Market 2026 | `PennyMarket_KS_2026.md` | 334 | NACE 47.11 maloobchod |
| PKS Česká pošta 2025–2026 | `CeskaPostaSP_KS_2025_2026.md` | 548 | NACE 53 poštovní služby |
| KSVS OSPZV-ASO 2026 | `KSVS_ASO_CMSZP_2026.md` | 498 | NACE 01 + 10–12 zemědělství/potravinářství |
| KSVS OS PPP 2026–2027 | `KSVS_OSPPP_2026_2027.md` | 409 | NACE 64–66 peněžnictví/pojišťovnictví |

### Další scrape soubory

| Soubor | Použití v práci |
|--------|-----------------|
| `Armstrong_HRM_Handbook.md` | kap. 2.3, 4 (Employee Advocate) |
| `Historie_odbory_a_spolecnost.md` | kap. 2.2 |
| `100_let_MOP.md` | kap. 2.1, 2.2 |
| `ActiveEmploymentPolicy_Dvorakova.md` | kap. 3.4, 4 |
| `ZBORNKPRSPEVKOV_Dvorakova_DemografickeTrendy.md` | kap. 3.4 |
| `UkraineRefugees_Polents_Dvorakova.md` | kap. 3.4 |
| `Weber_Industrie40_Arbeitsmarkt.md` | kap. 3.4 |
| `WojtczukTurek_SustainHRM_JobSatisfaction.md` | kap. 2.3 |
| `SRLZ_Dvorakova_PrezentaceHRM.md` | kontext (nepřímo) |
| `PETRICEK_HOPO_Flexicurity_NOCITE.md` | kap. 3.2 (argumenty, nepřímo) |
| `PETRICEK_IND4_IndustrialRevolution_NOCITE.md` | kap. 2.2, 3.4 (argumenty, nepřímo) |
| `NOCITE_Petricek_Flexicurity_Denmark.md` | kap. 3.2 (argumenty, nepřímo) |
| `Zadani_DP_Petricek2026_TRANSCRIPT.md` | referenční (zadání) |
| `PJDP2026L_ProjektDP_TRANSCRIPT.md` | referenční (projekt DP) |

### Zdroje NEDOSTUPNÉ — nepoužívat

| Zdroj | Důvod |
|-------|-------|
| Hrabcová, D. Sociální dialog (2008) | Není v /sources |
| Ulrich, D. HR Champion (1997) | Není v /sources |
| Andersen/Mailand: Danish Flexicurity (2005) | Není v /sources |
| ÖGB Austria materiály | Nejsou v /sources | -> research from intenet
| OECD Employment Outlook (AI chapter) | Není v /sources | -> research from internet
| Ministry of Employment DK (2021) | Není v /sources | -> research from internet

> ⚠️ Pokud bude čas, pokusit se tyto zdroje získat. Jinak argumenty podložit dostupnými zdroji (Hála, Armstrong, ČMKOS).

---

## 4. PRIORITNÍ POŘADÍ PRÁCE

### Fáze 1 — Teoretická část
1. **Kap. 2.1 Legislativní rámec** — hlavní vstupy: TRANSCRIPT, ZKV, ZP, ZZ, ZDP
2. **Kap. 2.2 Historický vývoj** — hlavní vstupy: ČMKOS Historie, 100 let MOP, Hála
3. **Kap. 2.3 Přehled poznání** — hlavní vstupy: Hála, ČMKOS Zpráva, Armstrong

### Fáze 2 — Analytická část
4. **Kap. 3.1 Metodologie** — popsat metody, pipeline, výběr zemí a KS
5. **Kap. 3.2 Evropský kontext** — obalit existující figury textem; Hála komparace
6. **Kap. 3.3 Případové studie** — 4 × studie ze scrape; průřezová tabulka; legislativní re-evaluace
7. **Kap. 3.4 Stav a výhled** — faktory z ČMKOS, Dvořáková, TRANSCRIPT §7
8. **Kap. 1 Úvod** — po zvládnutí obsahu formulovat přesněji

### Fáze 3 — Evaluace a syntéza
9. **Kap. 3.5 Hodnocení SD** — SWOT + oponování hypotézy + korelační analýza
10. **Kap. 4 Návrh inovace** — 6 navržených inovací
11. **Kap. 5 Závěr**
12. **Bibliografie** — doplnit .bib záznamy

---

## 5. KRITICKÁ CESTA K HYPOTÉZE (aktualizovaná)

```
HYPOTÉZA: CZ trh práce je zranitelnější kvůli slabému sociálnímu dialogu

PILÍŘ 1 — Slabý sociální dialog (deskriptivní):
  → Union density 11 % (ETUI/ČMKOS) ← vs. AT 26 %/DK 67 %
  → KV coverage 32 % ← vs. AT 98 %/DK 80 %
  → Rozšiřování KSVS: 2 v 2025 (ČMKOS)
  → Historické příčiny: ROH + ztráta důvěry (ČMKOS Historie)
  → § 24 ZP pluralita → fragmentace (Penny Market: 4 ZO)

PILÍŘ 2 — Zranitelnost trhu práce (analytický):
  → Model levné práce: 39,6 h/týden za nízké reálné mzdy v PPS
  → HDP konverguje rychleji než mzdy (Eurostat)
  → AI + automatizace → exponovaná struktura ekonomiky (Weber 2015)
  → Demografický tlak: old-age dependency 32 % (Eurostat)
  → APZ 0,3 % HDP (ČMKOS) vs. DK 2 %
  → Švarc/OSVČ → erodování odvodové základny (TRANSCRIPT §7)

PILÍŘ 3 — Kauzální logika (komparativní + korelační):
  → Hála et al. 2013: srovnání 7 zemí → silnější SD = lepší výsledky
  → Scatter: union density × GINI (pokud data)
  → AT: 98 % pokrytí díky automatickému rozšiřování
  → DK: Ghent system → silný SD + silná APZ = pružný trh proti ČR rigidnímu

PILÍŘ 4 — Empirická verifikace (4 případové studie):
  → Penny Market: KS formálně existuje, reálně zákonné minimum
  → Česká pošta: tarifní systém jako substituent zaručené mzdy
  → OSPZV-ASO: mezisektorový přesah → argument pro centralizaci
  → OS PPP: bankovnictví = nejsilnější nadstandard → korelace s kvalitou SD

VÝSLEDEK → Hypotéza POTVRZENA:
  Slabý SD = neschopnost tlačit na mzdy, koordinovat APZ,
  adaptovat trh na technologické šoky → větší zranitelnost

INOVACE (normativní část): Rozšíření KSVS, Ghent APZ,
  transparentnost, centralizace KV, inspekce, digitalizace
```

---

## 6. BibLaTeX — ZÁZNAMY K VYTVOŘENÍ

```bibtex
@book{Hala_SystemySocialnihoDialogu2013,
  author    = {Hála, Jaroslav and Čambáliková, Monika and Pfeiferová, Štěpánka
               and Píšl, Radek and Vácha, Jan and Veverková, Soňa},
  title     = {Systémy sociálního dialogu se zaměřením na zaměstnavatelskou sféru
               ve vybraných zemích EU},
  year      = {2013},
  publisher = {VÚPSV, v.v.i.},
  address   = {Praha},
  isbn      = {978-80-7416-126-1},
  langid    = {czech},
}

@book{cmkos_historie_2020,
  author    = {{ČMKOS}},
  title     = {Historie, odbory a společnost: cesta k lepší budoucnosti},
  year      = {2020},
  publisher = {ČMKOS},
  langid    = {czech},
}

@book{mop_100let_2019,
  author    = {Pokorný, Pavel and others},
  title     = {100 let Mezinárodní organizace práce},
  year      = {2019},
  publisher = {ČMKOS},
  langid    = {czech},
}

@report{cmkos_zprava_kv_2025,
  author      = {{ČMKOS}},
  title       = {Zpráva o průběhu kolektivního vyjednávání na vyšším stupni
                 a na podnikové úrovni v roce 2025},
  year        = {2026},
  institution = {ČMKOS},
  langid      = {czech},
}

@misc{ks_penny_2026,
  author  = {{ASO-ČR} and {OSPZV-ASO ČR}},
  title   = {Kolektivní smlouva Penny Market, s.\,r.\,o. na období 1.\,1.\,2026 --
             31.\,12.\,2026},
  year    = {2026},
  langid  = {czech},
}

@misc{ks_ceska_posta_2025,
  author  = {{Česká pošta, s.p.} and {odborové organizace}},
  title   = {Podniková kolektivní smlouva České pošty, s.p. 2025--2026},
  year    = {2025},
  langid  = {czech},
}

@misc{ksvs_ospzv_aso_2026,
  author  = {{OSPZV-ASO ČR} and {Zemědělský svaz ČR} and {ČMSZP}},
  title   = {Kolektivní smlouva vyššího stupně na rok 2026 — zemědělství a potravinářství},
  year    = {2026},
  langid  = {czech},
}

@misc{ksvs_osppp_2026,
  author  = {{OS pracovníků peněžnictví a pojišťovnictví} and {Svaz bank a pojišťoven}},
  title   = {Kolektivní smlouva vyššího stupně na období 1.\,1.\,2026 -- 31.\,12.\,2027},
  year    = {2026},
  langid  = {czech},
}

@book{armstrong_hrm_2023,
  author    = {Armstrong, Michael and Taylor, Stephen},
  title     = {Armstrong's Handbook of Human Resource Management Practice},
  edition   = {16},
  year      = {2023},
  publisher = {Kogan Page},
  langid    = {english},
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

@online{zakon_zamestnanost_2026,
  author  = {{Česká republika}},
  title   = {Zákon č.\,435/2004\,Sb., o zaměstnanosti, znění od 1.\,1.\,2026},
  year    = {2026},
  url     = {https://www.zakonyprolidi.cz/cs/2004-435},
  urldate = {2026-04-02},
  langid  = {czech},
}

@online{zakon_dane_prijem_2026,
  author  = {{Česká republika}},
  title   = {Zákon č.\,586/1992\,Sb., o daních z příjmů, znění od 1.\,1.\,2026},
  year    = {2026},
  url     = {https://www.zakonyprolidi.cz/cs/1992-586},
  urldate = {2026-04-04},
  langid  = {czech},
}
```

---

*Plán sestaven: 2026-04-06. Verze 3 — konsolidace po dokončení všech scrape operací.*
