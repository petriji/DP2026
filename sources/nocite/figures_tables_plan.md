# Plán figur a tabulek — DP Sociální dialog a KV
### Petříček Jiří | MÚVS ČVUT | PRI | aktualizace: 2026-04-06

> Tento dokument obsahuje návrhy všech figur (grafů, map) a tabulek, které mohou podpořit
> argumentaci DP. Každá položka uvádí zdroj dat, instituci, protějšky (AT/DE/DK/PL/SK)
> a odkaz na kapitolu plánu v3.

---

## LEGENDA — STATUS

- ✅ = existuje (`pics/python/` nebo `texparts/python/`)
- 🔨 = data existují v `python/data/`, figuru nutno vytvořit/obalit textem
- ⬇️ = data nutno stáhnout
- ❓ = volitelné nebo nutno ověřit dostupnost

---

## PRAVIDLO VÝBĚRU TYPU VIZUALIZACE (A.6, A.9 a analogické páry)

> Pokud pro daný indikátor existuje **zajímavý trend** (výrazný vzestup, pokles, konvergence, divergence),
> zvolit **timeline** jako primární figuru a choropleth jako doplněk. Pokud trend není výrazný nebo nejsou
> dostatečná časová data, zvolit **choropleth mapu** jako primární a timeline vynechat nebo přidat jako volitelný.
>
> Příklad: A.6 — odborová hustota ČR poklesla z 80 % na 11 % (1990–2024) → **A.6a timeline je primární**,
> A.6b choropleth doplňuje. U A.9 — pokud APZ výdaje CZ stagnují na 0,3 % HDP bez trendu →
> **A.9a choropleth je primární**, A.9b timeline je doplňková.

---

## A. FIGURY (grafy, mapy)

### A.1 ✅ HDP na obyvatele v PPS — timeline (6 zemí)
- **Soubor:** `gdp_ppp_timeline.pdf`
- **Typ:** časový graf, DK/CZ/DE/AT/PL/SK, ~2000–2024
- **Data:** Eurostat `nama_10_pc` (GDP per capita in PPS, EU27=100)
- **CSV:** `A.PC_EU27_2020_HAB_MPPS_CP.B1GQ_*.csv`
- **Instituce:** Eurostat (EU), protějšky: národní statistické úřady potvrzují; OECD NAS pro validaci
- **Kapitola:** 3.2 (Evropský kontext)
- **Argument:** CZ konverguje k EU průměru pomalým tempem; AT/DE stabilně nad 100

### A.2 ✅ Daňový klín — mapa EU
- **Soubor:** `tax_wedge_map.pdf`
- **Typ:** Choropleth mapa EU, tax wedge at 100 % AW
- **Data:** Eurostat `earn_nt_taxwedge` (Tax wedge on labour costs)
- **CSV:** `earn_nt_taxwedge_94b1ee6b.csv`
- **Instituce:** Eurostat; OECD Taxing Wages (validace)
- **Protějšky:** AT: BMF; DE: BZSt; DK: Skatteministeriet; PL: MF; SK: MF SR
- **Kapitola:** 3.2
- **Argument:** CZ daňový klín 38,1 % — nad DK (33,5 %), pod DE (43,5 %)

### A.3 ✅ AROPE — mapa EU (2025 data) — PROTIARGUMENT
- **Soubor:** `arope_map_2025.pdf`
- **Typ:** Choropleth mapa EU, AROPE rate
- **Data:** Eurostat `ilc_peps01n` (At risk of poverty or social exclusion)
- **Instituce:** Eurostat EU-SILC
- **Kapitola:** 3.5 (protiargument — „v ČR je nízká chudoba, SD není potřeba")
- **Argument:** CZ 12 % = nejnižší v EU; avšak relativní definice (60 % mediánu) → nízké absolutní příjmy v PPS; nízký AROPE neznamená prosperitu, jen nízkou nerovnost příjmů
- **Poznámka:** Použít explicitně jako protiargument v hodnocení SD (kap. 3.5) a systematicky vyvrátit — viz vyvrácení v research_plan_v3.md.

### ~~A.4~~ ~~A.5~~ — AROPE timeline a skupiny — NEPOUŽÍVAT
> Existující figury `arope_timeline_CE.pdf` a `arope_groups.pdf` jsou k dispozici, ale AROPE
> není pro argumentaci DP dostatečně průkazný ukazatel. Pokud bude třeba, odkázat na A.3 mapu.

### A.6a ⬇️ Odborová hustota — timeline (6 zemí, 1990–2024)
- **Navrhovaný soubor:** `union_density_trend.pdf`
- **Typ:** Čárový graf, DK/CZ/DE/AT/PL/SK, 1990–2024
- **Data:** OECD AIAS ICTWSS database (Trade Union Density)
- **Zdroj URL:** `https://stats.oecd.org` → Industrial Relations → Trade Union Density
- **Alternativa:** ILOSTAT TUR; ETUI (etui.org/databases)
- **Instituce:**
  - CZ: ČMKOS, ČSÚ
  - AT: ÖGB, Statistik Austria
  - DE: DGB, Destatis
  - DK: LO/FH, Danmarks Statistik
  - PL: OPZZ/Solidarność, GUS
  - SK: KOZ SR, ŠÚ SR
- **Kapitola:** 2.2 (historický vývoj), 3.2 (srovnání), 3.5 (SWOT)
- **Argument:** Dramatický pokles CZ z ~80 % (1990) na 11 % (2024); DK stabilně nad 60 %

### A.6b ⬇️ Odborová hustota — choropleth mapa EU (aktuální rok)
- **Navrhovaný soubor:** `union_density_map.pdf`
- **Typ:** Choropleth mapa EU, odborová hustota (%, nejnovější dostupný rok)
- **Data:** OECD AIAS ICTWSS database (Trade Union Density); ETUI
- **Instituce:** Stejné jako A.6a
- **Kapitola:** 3.2 (příčný řez), 3.5
- **Argument:** Geografický vzorec: severské/Ghent státy vysoko, V4 nízko; vizuálně doplňuje timeline A.6a

### A.7 ⬇️ Pokrytí kolektivním vyjednáváním — mapa EU
- **Navrhovaný soubor:** `kv_coverage_map.pdf`
- **Typ:** Choropleth mapa EU (preferovat mapový formát jako u A.2/A.3)
- **Data:** OECD AIAS ICTWSS (Adjusted CB Coverage); ETUI
- **Instituce:**
  - CZ: ČMKOS Zpráva o KV → 32 %
  - AT: WKÖ/ÖGB → 98 %
  - DE: WSI Tarifarchiv → 52 %
  - DK: DA/FH → 80 %
  - PL: GUS → 15 %
  - SK: KOZ SR → 35 %
- **Kapitola:** 2.1 (rozšiřování KSVS), 3.2, 3.5
- **Argument:** CZ 32 % hluboko pod AT (98 %) a DK (80 %) → nedostatečné pokrytí

### A.8 ⬇️ Mzdová konvergence vs. HDP konvergence — dual chart
- **Navrhovaný soubor:** `wage_gdp_convergence.pdf`
- **Typ:** Dual-axis čárový graf; CZ/DE/AT: HDP index + wage index (EU27=100), ~1995–2024
- **Data HDP:** Eurostat `nama_10_pc` (existuje v python/data/)
- **Data mzdy:** Eurostat `earn_ses_pub1a` (mean annual earnings) NEBO `nama_10_lp_ulc` (unit labour cost)
- **Alternativa dat mezd:** OECD Average Wages; ILO Global Wage Database
- **Instituce mezd:**
  - CZ: ČSÚ (průměrná mzda), MPSV/ISPV (medián)
  - AT: Statistik Austria (Verdienststruktur)
  - DE: Destatis (Verdiensterhebung)
  - DK: Danmarks Statistik (Lønstruktur)
  - PL: GUS (Wynagrodzenia)
  - SK: ŠÚ SR (Priemerná mzda)
- **Kapitola:** 3.2, 3.5
- **Argument:** HDP CZ konverguje k EU průměru rychleji než mzdy → „cheap labour trap"

### A.9a ⬇️ APZ výdaje (% HDP) — mapa EU
- **Navrhovaný soubor:** `lmp_expenditure_map.pdf`
- **Typ:** Choropleth mapa EU, LMP expenditure as % GDP
- **Data:** Eurostat `lmp_ind_exp` nebo `lmp_expsumm` (LMP expenditure, % GDP)
- **Instituce:**
  - CZ: MPSV (Úřad práce), ČSSZ
  - AT: AMS (Arbeitsmarktservice)
  - DE: BA (Bundesagentur für Arbeit)
  - DK: STAR (Styrelsen for Arbejdsmarked og Rekruttering)
  - PL: MRPiPS (Ministerstwo Rodziny)
  - SK: ÚPSVaR
- **Kapitola:** 3.2 (flexicurity), 3.4, 4 (inovace — Ghent)
- **Argument:** CZ ~0,3 % HDP vs. DK ~2 % → CZ nemá rekvalifikační kapacitu

### A.9b ⬇️ APZ výdaje (% HDP) — timeline (6 zemí)
- **Navrhovaný soubor:** `lmp_expenditure_timeline.pdf`
- **Typ:** Čárový graf, DK/CZ/DE/AT/PL/SK, ~2005–2024
- **Data:** Eurostat `lmp_ind_exp` nebo `lmp_expsumm` (stejná data jako A.9a)
- **Instituce:** Stejné jako A.9a
- **Kapitola:** 3.2 (flexicurity), 3.4
- **Argument:** Časový vývoj ukazuje, zda CZ konverguje k EU průměru APZ výdajů; DK stabilně ~2 %

### A.10 ⬇️ Scatter: pokrytí KV × čistý příjem v PPS (EU27 panel)
- **Navrhovaný soubor:** `coverage_income_pps_scatter.pdf`
- **Typ:** Scatter plot s regresní přímkou, 27 bodů (EU členské státy), klíčové země zvýrazněny
- **Data pokrytí:** OECD AIAS ICTWSS (⬇️)
- **Data příjem:** Eurostat `earn_nt_net` (net earnings) v PPS NEBO `nama_10_gdp` per capita income v PPS
- **Kapitola:** 3.5 (korelační analýza)
- **Argument:** Kladná korelace → vyšší pokrytí KV = vyšší čistý příjem v PPS → SD zlepšuje životní úroveň
- **Poznámka:** GINI scatter by pravděpodobně neukázal korelaci (CZ paradox: nízký GINI + slabý SD). Čistý příjem v PPS je průkaznější.

### ~~A.11~~ — Scatter KV × pracovní hodiny — NEPOUŽÍVAT
> Nahrazeno A.10 (CB coverage × net income PPS) — průkaznější korelace.

### A.12 ⬇️ Podíl OSVČ — mapa EU
- **Navrhovaný soubor:** `self_employment_map.pdf`
- **Typ:** Choropleth mapa EU, % zaměstnanosti (preferovat mapový formát)
- **Data:** Eurostat `lfst_pganws` (self-employment rate) nebo `lfsa_esgan` (Employment by prof. status)
- **Instituce:**
  - CZ: ČSÚ (VŠPS), ČSSZ (registr OSVČ)
  - AT: Statistik Austria / WKÖ (EPU = Ein-Personen-Unternehmen)
  - DE: Destatis (Selbständige)
  - DK: Danmarks Statistik
  - PL: GUS (Pracujący na własny rachunek)
  - SK: ŠÚ SR
- **Kapitola:** 3.4 (OSVČ a Švarc)
- **Argument:** CZ nadprůměrné % OSVČ → erodování sociálních odvodů

### A.13 🔨 Old-age dependency ratio — choropleth mapa EU
- **Navrhovaný soubor:** `old_age_dependency_map.pdf`
- **Typ:** Choropleth mapa EU, old-age dependency ratio
- **Data:** Eurostat `demo_pjanind` → `TPS00198` (Old-age dependency ratio)
- **CSV:** `A.OLDDEP1_6dc9b0e3.csv` (existuje)
- **Instituce:**
  - CZ: ČSÚ, ČSSZ
  - AT: Statistik Austria
  - DE: Destatis
  - DK: Danmarks Statistik
  - PL: GUS
  - SK: ŠÚ SR
- **Kapitola:** 3.4 (demografický tlak)
- **Argument:** Stárnutí → tlak na sociální systém; zvyšuje důležitost APZ

### A.14 🔨 Zaměstnanost (20–64) — timeline
- **Navrhovaný soubor:** `employment_rate_timeline.pdf`
- **Typ:** Čárový graf, 6 zemí, 2000–2024
- **Data:** Eurostat `lfsi_emp_a` (Employment rate, 20–64)
- **CSV:** `A.EMP_LFS.T.Y20-64.PC_POP_945e8bea.csv` (existuje)
- **Instituce:**
  - CZ: ČSÚ (VŠPS), MPSV
  - AT: AMS, Statistik Austria
  - DE: BA, Destatis, IAB
  - DK: STAR, Danmarks Statistik
  - PL: GUS, MRPiPS
  - SK: ÚPSVaR, ŠÚ SR
- **Kapitola:** 3.2, 3.5 (protiargument: vysoká zaměstnanost)
- **Argument:** CZ 81,7 % — vysoká i bez silného SD → protiargument k vyvrácení

### A.15 🔨 Efektivní zdanění OSVČ vs. zaměstnanec (CZ) — aktuální legislativní stav
- **Navrhovaný soubor:** `tax_osvc_vs_employee.pdf`
- **Typ:** Čárový/plošný graf: efektivní odvody jako % hrubého příjmu (0–300K Kč/měs.)
- **Data:** Výpočet z **platné legislativy k 1. 1. 2026**: ZDP §§ 2a/7/7a (paušální daň 3 pásma, výdajový paušál), sociální pojistné zaměstnavatel 24,8 % + zaměstnanec 7,1 %, OSVČ 29,2 % z vyměřovacího základu 55 %, zdravotní 13,5 % (zaměstnavatel 9 % + zaměstnanec 4,5 %), OSVČ 13,5 % z 50 % příjmu. Minimální zálohy OSVČ aktualizovat dle aktuální vyhlášky.
- **Instituce:**
  - CZ: ČSSZ (sazby pojistného — platné od 1.1.2026), VZP (zdravotní pojistné), MF ČR (ZDP — konsolidovaná verze)
- **Kapitola:** 3.4 (OSVČ a Švarc), 2.1 (legislativní rámec — ZDP)
- **Argument:** OSVČ s výdajovým paušálem 80 % odvádí výrazně méně než zaměstnanec → daňová nespravedlnost
- **Poznámka:** Musí reflektovat aktuální právní stav, nikoli historický; ověřit sazby a stropy před generováním grafu

### A.16 🔨 Příjmový GINI — choropleth mapa EU — PROTIARGUMENT
- **Navrhovaný soubor:** `gini_income_map.pdf`
- **Typ:** Choropleth mapa EU, GINI koeficient (příjmový, z EU-SILC)
- **Data:** Eurostat `ilc_di12` (Gini coefficient of equivalised disposable income)
- **CSV:** `A.TOTAL.GINI_HND_45503ce0.csv` (existuje)
- **Instituce:** Eurostat EU-SILC
- **Kapitola:** 3.5 (protiargument — „CZ má nízkou nerovnost, SD není třeba")
- **Argument:** CZ příjmový GINI ~24,4 = jeden z nejnižších v EU; avšak: (a) nízký GINI při nízkém mediánu znamená jen „rovnost v chudobě", (b) příjmový GINI maskuje rostoucí **majetkovou** nerovnost (viz A.18), (c) GINI neměří kvalitu práce (hodiny, podmínky, jistota)
- **Poznámka:** Součást protiargumentačního bloku společně s A.3 (AROPE) a A.18 (majetkový GINI). Vizualizovat jako choropleth, ne timeline — zajímavý je průřez, ne trend.

### A.18 ⬇️ Majetkový GINI (wealth Gini) — choropleth mapa EU — OLIGARCHIZACE
- **Navrhovaný soubor:** `gini_wealth_map.pdf`
- **Typ:** Choropleth mapa EU/Evropy, wealth Gini coefficient
- **Data:** Credit Suisse / UBS Global Wealth Databook (tabulka 3-1)
- **Zdroj URL:** UBS Global Wealth Report; historicky Credit Suisse, od 2023 UBS
- **Kapitola:** 3.5 (oligarchizace — argument PRO posílení SD)
- **Argument:** CZ majetkový GINI = 77,7 (2021) — 4. nejvyšší v EU (po SE 87,2, LV 80,9, CY 80,7), dramatický nárůst z 62,6 (2008). Nízký příjmový GINI (24,4) maskuje vysokou a rychle rostoucí majetkovou nerovnost. Kontrast: SK majetkový GINI = 50,3 (nejnižší v EU). Zrychlující se koncentrace majetku posiluje argument pro funkční SD jako protiváhu.
- **Klíčová data (Credit Suisse 2021):**
  - CZ: 77,7 | SK: 50,3 | PL: 70,7 | AT: 74,5 | DE: 77,9 | DK: 73,6 | SE: 87,2 | RU: 87,8
  - CZ nárůst: 62,6 (2008) → 77,7 (2021) = +15,1 bodu za 13 let
- **Poznámka:** Wealth Gini ≠ income Gini. Data nejsou na Eurostatu — nutno stáhnout z UBS/Credit Suisse Databook (PDF → extrakce tabulky).

### A.17 🔨 Příjem na obyvatele v PPS — mapa EU
- **Navrhovaný soubor:** `income_pps_map.pdf`
- **Typ:** Choropleth mapa EU, čistý příjem / HDP na obyvatele v PPS (EU27=100)
- **Data:** Eurostat `nama_10_pc` (GDP per capita in PPS) nebo `earn_nt_net` (net earnings in PPS)
- **CSV:** `A.PC_EU27_2020_HAB_MPPS_CP.B1GQ_*.csv` (existuje pro HDP); `A.PLI_EU27_2020.GDP_09c23c62.csv` (PLI pro přepočet)
- **Instituce:** Eurostat; národní stat. úřady
- **Kapitola:** 3.2
- **Argument:** Vizualizace reálné kupní síly napříč EU — CZ pod průměrem, AT/DE/DK nad; mapový formát lépe ukazuje geografické vzorce

---

## B. TABULKY

### B.1 ✅ Flexicurity srovnávací tabulka (6 zemí × 7 ukazatelů)
- **Soubor:** `flexicurity_table.tex`
- **Data:** Kombinace Eurostat, ETUI, OECD
- **Kapitola:** 3.2
- **Obsah:** HDP/ob., odborová hustota, pokrytí KV, GINI, prac. hodiny, AROPE, daňový klín

### B.2 NOVÝ — Průřezová tabulka 4 KS + ZP baseline (10+ parametrů)
- **Navrhovaný soubor:** `texparts/python/ks_comparison_table.tex`
- **Data:** Scrape souborů PennyMarket, ČP, OSPZV-ASO, OS PPP + **ZP zákonné minimum jako referenční sloupec**
- **Kapitola:** 3.3.5 (průřezová analýza)
- **Obsah:** Přesčas, noční, so/ne, dovolená, penzijní příspěvek, HO, tarify, inflační doložka, agenturní limit, § 61, § 306 — viz tabulka v research_plan_v3.md
- **Poznámka:** Sloupec „ZP minimum" (plain zákoník práce) umožňuje čtenáři okamžitě vidět, o kolik každá KS zlepšuje zákonný standard

### B.3 ❓ TENTATIVNÍ — Srovnání PP vs. OSVČ vs. Švarc vs. Agentura
- **Navrhovaný soubor:** `texparts/python/pp_osvc_comparison.tex`
- **Data:** TRANSCRIPT §7.6 (srovnávací tabulka 8 parametrů)
- **Kapitola:** 2.1 (legislativní rámec) nebo 3.4 (OSVČ/Švarc)
- **Obsah:** Právní základ, KS, sociální pojistné, zdanění, BOZP, výpověď, odbory, sankce

### ~~B.4~~ ~~B.5~~ — Zaručená mzda / Příplatky — NEPOUŽÍVAT
> Zaručená mzda a příplatky jsou pokryty v průřezové tabulce B.2 a v textu kap. 2.1.
> Samostatné tabulky by redundantně duplikovaly informaci.

### B.6 NOVÝ → FIGURA — Vývoj kontrol a postihů nelegální práce v čase
- **Navrhovaný soubor:** `suip_enforcement_timeline.pdf` (přesunuto z tabulky na figuru/timeline plot)
- **Typ:** Čárový graf / dual-axis timeline: počet kontrol SÚIP + zjištění nelegální práce + uložené pokuty (Kč), ~2010–2025
- **Data:** SÚIP výroční zprávy (počet kontrol, zjištěné přestupky, uložené pokuty) + TRANSCRIPT §7.3 (ZZ §§ 139–140)
- **Kapitola:** 2.1, 3.4
- **Obsah:** Timeline zachycující vývoj v čase: počet kontrol SÚIP, zjištění nelegální práce, průměrná/maximální pokuta. Pokud data SÚIP nedostupná za celé období, alespoň dostupné roky + legislativní milníky (novelizace ZZ) jako anotace.
- **Instituce:** SÚIP (výroční zprávy), MPSV

### B.7 NOVÝ — SWOT analýza SD v ČR
- **Navrhovaný soubor:** `texparts/hodnoceni/swot_sd.tex`
- **Data:** Syntéza kap. 2–3
- **Kapitola:** 3.5
- **Obsah:** Silné stránky, Slabiny, Příležitosti, Hrozby

### B.8 NOVÝ — Srovnávací tabulka systémů SD (z Hály)
- **Navrhovaný soubor:** `texparts/evropsky_kontext/hala_comparison.tex`
- **Data:** Hála et al. 2013, s. 228–229 (srovnávací tabulka 7 zemí)
- **Instituce:**
  - CZ: ČMKOS, MPSV
  - AT: WKÖ, AK, ÖGB
  - DE: BDA, DGB
  - DK: DA, FH/LO
  - PL: OPZZ, Solidarność, Lewiatan
  - SK: RÚZ, KOZ SR
  - UK: CBI, TUC (Hála zahrnuje UK)
- **Kapitola:** 2.3, 3.2
- **Obsah:** Odborová hustota, pokrytí KV, tripartita, dominantní úroveň KV, extenze mechanismus

### ~~B.9~~ — Minimální mzda v PPS — NEPOUŽÍVAT
> Minimální mzda je pokryta v textu kap. 2.1 (§ 111 ZP) a v ČMKOS Zprávě. Samostatná tabulka není nutná.

### B.10 ❓ Rozšiřování závaznosti KSVS — CZ vs. EU praxe
- **Navrhovaný soubor:** `texparts/dialog/rozsireni_kvss.tex`
- **Data:** ČMKOS Zpráva o KV 2025 (2 rozšíření v CZ); Hála (komparace); MPSV Sdělení 17/2026, 47/2026
- **Instituce:**
  - CZ: MPSV (Sbírka zákonů — Sdělení)
  - AT: BMAW (automatické rozšíření přes Kammer)
  - DE: BMAS (Allgemeinverbindlicherklärung — AVE)
  - DK: není (dobrovolný systém, Ghent)
  - PL: MRPiPS
  - SK: MPSVR SR (zákon 2/1991 analogicky)
- **Kapitola:** 2.1 (ZKV § 7), 4 (inovace — rozšíření KSVS)
- **Argument:** CZ 2 rozšíření v 2025 vs. AT de facto univerzální pokrytí → klíčová inovační příležitost

### ~~B.11~~ — Paušální daň pásma — NEPOUŽÍVAT
> Paušální daň je pokryta v textu kap. 2.1 a v tabulce B.3 (PP vs. OSVČ srovnání). Samostatná tabulka zbytečná.

---

## C. DATOVÉ ZDROJE — PŘEHLED INSTITUCÍ

### C.1 Primární datové portály

| Instituce | Země | URL | Klíčové datasety |
|-----------|------|-----|-------------------|
| **Eurostat** | EU | ec.europa.eu/eurostat | GDP, GINI, AROPE, zaměstnanost, mzdy, LMP, tax wedge, PLI |
| **OECD AIAS ICTWSS** | mezinar. | stats.oecd.org → Industrial Relations | Odborová hustota, pokrytí KV |
| **ILO (ILOSTAT)** | mezinar. | ilostat.ilo.org | TUR (union density), EPL |
| **ETUI** | EU | etui.org/databases | CB coverage, strike activity |

### C.2 Národní instituce — přehled pro 6 zemí

| Oblast | CZ | AT | DE | DK | PL | SK |
|--------|----|----|----|----|----|----|
| **Stat. úřad** | ČSÚ | Statistik Austria | Destatis | DST | GUS | ŠÚ SR |
| **Min. práce** | MPSV | BMAW | BMAS | BM | MRPiPS | MPSVR SR |
| **Sociální pojistné** | ČSSZ | DVSV (Dachverband) | DRV | ATP | ZUS | Sociálna poisťovňa |
| **Úřad práce** | ÚP ČR | AMS | BA | STAR | UP (Powiatowy) | ÚPSVaR |
| **Odbory (centrála)** | ČMKOS, ASO | ÖGB | DGB | FH (dříve LO) | OPZZ, Solidarność | KOZ SR |
| **Zaměstnavatelé** | SP ČR, HK ČR | WKÖ, IV | BDA, BDI | DA, DI | Lewiatan, ZRP | RÚZ, AZZZ |
| **Min. financí** | MF ČR | BMF | BMF | Skatteministeriet | MF | MF SR |
| **Inspekce práce** | SÚIP | Arbeitsinspektorat | Gewerbeaufsicht | Arbejdstilsynet | PIP | IP |

### C.3 Kontrolní seznam — co stáhnout

| # | Dataset | Zdroj | Priorita | Pro figuru/tabulku |
|---|---------|-------|----------|-------------------|
| 1 | Trade union density (all EU + 6 zemí timeline, 1990–2024) | OECD ICTWSS | **VYSOKÁ** | A.6a, A.6b |
| 2 | Adjusted CB coverage (6 zemí) | OECD ICTWSS | **VYSOKÁ** | A.7 |
| 3 | LMP expenditure (% GDP, by type, timeline) | Eurostat `lmp_ind_exp` | **VYSOKÁ** | A.9a, A.9b |
| 4 | Mean annual earnings in PPS (6 zemí, timeline) | Eurostat `earn_ses_pub1a` | **VYSOKÁ** | A.8 |
| 5 | Self-employment rate (6 zemí) | Eurostat `lfsa_esgan` | STŘEDNÍ | A.12 |
| 6 | Minimum wages (EU) | Eurostat `earn_mw_cur` | STŘEDNÍ | B.9 |
| 7 | CB coverage EU-wide (27 zemí, 1 rok) | OECD/ETUI | **VYSOKÁ** | A.7 mapa, A.10 scatter |
| 8 | Net earnings in PPS (EU27, 1 rok) | Eurostat `earn_nt_net` | **VYSOKÁ** | A.10 scatter, A.17 mapa |
| 9 | UBS/Credit Suisse Global Wealth Databook (wealth Gini) | UBS (dříve Credit Suisse) | STŘEDNÍ | A.18 mapa |

---

## D. MAPOVÁNÍ FIGUR/TABULEK → KAPITOLY

| Kapitola | Figury | Tabulky |
|----------|--------|---------|
| 2.1 Legislativní rámec | B.6 | B.3 |
| 2.2 Historický vývoj | A.6a, A.6b | — |
| 2.3 Přehled poznání | — | B.8 |
| 3.1 Metodologie | — | — |
| 3.2 Evropský kontext | A.1, A.2, A.6b, A.7, A.8, A.9a, A.9b, A.14, A.17 | B.1, B.8 |
| 3.3 Případové studie | — | B.2 |
| 3.4 Stav a výhled | A.12, A.13, A.15, B.6 | B.3 (odkaz) |
| 3.5 Hodnocení SD | A.3, A.10, A.16, A.18 | B.7 |
| 4 Návrh inovace | — | B.10 (odkaz) |

---

*Plán sestaven: 2026-04-06. Aktualizace 2026-04-07: A.3 + A.16 přesunuty do protiargumentačního bloku (kap. 3.5), přidán A.18 (majetkový GINI — oligarchizace). Celkem: 18 figur (aktivních), 6 tabulek.*
