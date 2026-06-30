# Nerovnost příjmů a majetku v ČR — výzkumné poznámky
Jiří Petříček | MÚVS ČVUT | DP – Sociální dialog a KV | 2026-04-07

---

## 1. Příjmová nerovnost — Gini koeficient (Eurostat EU-SILC)

Zdroj: Eurostat, dataset `ilc_di12` — Gini koeficient ekvivalizovaného disponibilního příjmu.
Lokálně: `python/data/A.TOTAL.GINI_HND_45503ce0.csv`

Hodnoty 2023 (nebo nejnovější dostupný rok):

| Země | GINI příjem | Poznámka |
|------|------------|----------|
| SK | 21,6 | nejnižší EU |
| CZ | 24,4 | 2. nejnižší EU |
| DK | 28,9 | |
| PL | 27,2 | |
| DE | 29,7 | |
| AT | 30,2 | |
| EU-27 | 30,3 | průměr |
| BG | 41,3 | nejvyšší EU |

Historický trend CZ 2003–2023: stabilní, pohyb v pásmu 24–27. Dramatický trend neexistuje.
Nízký příjmový Gini bývá uváděn jako protiargument vůči potřebě SD — viz sec:hodnoceni.

Vyvrácení (argumenty pro text kap. 3.5):
- Nízký příjmový Gini při nízkém mediánu příjmu v PPS = „rovnost v chudobě."
  CZ mediánový majetek 23 502 USD vs. AT median 68 492 USD (UBS 2023). -> this comparison should be PPS
- Příjmový Gini neměří majetkovou nerovnost — ty jsou v CZ dramaticky vyšší (viz oddíl 2).
- Příjmový Gini neodráží délku pracovního týdne (CZ 39,6 h = nejdelší ze skupiny 6 zemí). -> ???
- Nízký Gini je zčásti historický artefakt komunistického vyrovnávání příjmů, nikoli výsledek
  fungujícího SD.

Doporučená vizualizace: timeline 6 zemí (CZ/AT/DE/DK/PL/SK), 2003–2023 — obrázek A.16.
Účel: zobrazit stabilitu CZ příjmového Gini jako protiargumentační kontext.
Neočekávám dramatický vzestupný trend — zajímavé je spíše SROVNÁNÍ s ostatními zeměmi.

---

## 2. Majetková nerovnost — wealth Gini (UBS/Credit Suisse Global Wealth Databook)

Zdroj: Credit Suisse / UBS Global Wealth Databook, tabulka 3-1.
Vydání 2022: https://www.credit-suisse.com/media/assets/corporate/docs/about-us/research/publications/global-wealth-databook-2022.pdf
Vydání 2023 (UBS přejal CS): https://www.ubs.com/global/en/wealth-management/global-wealth-report.html

Data nejsou na Eurostatu — nutno extrahovat z PDF tabulky (str. 119–122 vydání 2022).

Vývoj CZ wealth Gini:

| Rok | CZ wealth Gini |
|-----|---------------|
| 2008 | 62,6 |
| 2018 | 75,8 |
| 2019 | 72,5 |
| 2021 | 77,7 |

Nárůst 2008–2021: +15,1 bodu — jeden z nejvyšších nárůstů v EU za dané období.
Doporučená vizualizace: timeline CZ (přidat dostupné roky) + srovnávací body AT/DE/DK/SK — obrázek A.18.

Srovnání EU 2021:

| Země | Wealth Gini | Poznámka |
|------|-----------|----------|
| SK | 50,3 | nejnižší EU |
| HU | 66,5 | |
| PL | 70,7 | |
| AT | 74,5 | |
| DK | 73,6 | |
| CZ | 77,7 | 4. nejvyšší EU (mezi dostatečně velké státy) |
| DE | 77,9 | |
| NO | 79,4 | |
| LV | 80,9 | |
| CY | 80,7 | |
| SE | 87,2 | |
| RU | 87,8 | mimo EU |

Mean vs. median bohatství na dospělého (UBS 2023):

| Země | Mean (USD) | Median (USD) | Ratio mean/median |
|------|-----------|-------------|------------------|
| CZ | 90 393 | 23 502 | 3,85 |
| SK | 62 125 | 45 853 | 1,35 |
| AT | 245 225 | 68 492 | 3,58 |
| DE | 256 179 | 66 735 | 3,84 |
| DK | 409 954 | 186 041 | 2,20 |
| PL | 52 741 | 20 263 | 2,60 |

Vysoký ratio mean/median pro CZ (3,85) potvrzuje silnou koncentraci majetku v horním decilu,
při téměř nejnižším absolutním mediánu ze skupiny.

---

## 3. Podíl majetku v rukou oligarchů a horního decilu

Forbes Global Billionaires List 2025 — výběr:

| Země | Miliardáři | Na mil. obyv. |
|------|-----------|--------------|
| CZ | 11 | 1,01 |
| AT | 9 | 0,98 |
| SK | 2 | 0,37 |
| PL | 8 | 0,21 |
| DE | 79 | 0,94 |
| DK | 8 | 1,36 |
| SE | 42 | 4,08 |

Odhad podílu 11 CZ miliardářů na celkovém soukromém majetku:
- Průměrná hodnota CZ Forbes miliardáře: cca 2 mld. USD (hrubý odhad)
- Celkové bohatství 11 osob: cca 22 mld. USD
- Celkový soukromý majetek CZ (UBS 2023): 90 393 USD × 8,55 mil. dospělých ≈ 773 mld. USD
- Podíl: cca 2,8 %

Top 10% wealth share v CZ: WID.world data naznačují cca 60–65 % (nutno ověřit přímo
z WID.world; přidat URL https://wid.world/country/czech-republic/).

---

## 4. Oligarchizace médií — RSF a Freedom House

RSF World Press Freedom Index (https://rsf.org/en/czech-republic):
- 2015: CZ na 13. místě ze 180 zemí (výborné hodnocení)
- 2021: CZ na 40. místě — propad o 27 míst za 6 let
- RSF 2021: „rise of the oligarchs" — přímá formulace v country profilu
- RSF 2016: „Local oligarch conflicts of interest dominate Czech media"

Struktura vlastnictví médií (stav 2023–2025):

| Vlastník | Média | Poznámka |
|---------|-------|----------|
| Andrej Babiš / Agrofert | MAFRA: MF DNES, Lidové noviny, iDNES.cz, Metro | vlastní od 2013; prozatímní trust fund 2017+ |
| Penta Investments | Vltava Labe Media (regionální deníky) | odkoupeno 2015 od Verlagsgruppe Passau |
| Daniel Křetínský / CMI | Czech Media Invest (HN, Reflex, někdejší Economia) | |
| Ringier Axel Springer | Czech News Center: Blesk, Aha!, Sport | zahraniční vlastnictví — nadnárodní korporace |
| PPF Group | TV Nova | prodána CME v 2020 |
-> seznam, novinky, Právo ...Lukačovič

Freedom House Nations in Transit 2021:
- PM Andrej Babiš zvyšoval vliv nad CZ médii od koupě MAFRA (2013).
- Během pandemie COVID-19 čerpala MAFRA státní podpůrné prostředky disproporčně.
- Zákon č. 231/2001 Sb. — omezení křížového vlastnictví jsou označována za „minimální"
  (Freedom House 2016).

Důsledky pro sociální dialog (argumentační linie):
1. Médii vlastnění podnikatelé mají přímý zájem marginalizovat odborová témata.
2. Veřejná debata o odměňování a pracovních podmínkách je systematicky podreprezentována.
3. MAFRA (NACE 22 + distribuce) vlastněná Agrofertem (NACE 01/10–12) tvoří přímý střet zájmů
   s odborovou organizací OSPZV-ASO pokrývající identický sektor.
4. Politická propojenost vlastníků médií s vládními pozicemi (Babiš coby premier 2017–2021)
   oslabuje nestrannost veřejné diskuse o regulaci práce a SD.

---

## 5. Navrhované vizualizace (viz figures_tables_plan_v2.md)

A.16 — Income GINI timeline (6 zemí, 2003–2023)
- Data: Eurostat ilc_di12; soubor python/data/A.TOTAL.GINI_HND_45503ce0.csv
- Účel: protiargument v kap. sec:hodnoceni; ukazuje dlouhodobou stabilitu CZ a srovnání

A.18a — Wealth GINI timeline (CZ + vybrané roky pro AT/DE/DK/SK, 2008–2021)
- Data: UBS/Credit Suisse Databook PDF — nutno extrahovat tabulku 3-1
- Účel: dramatický nárůst CZ z 62,6 na 77,7 jako argument oligarchizace v kap. sec:hodnoceni

A.18b — Wealth GINI choropleth mapa EU (2021)
- Stejná data jako A.18a; mapa ukazuje geografický vzorec

A.19 — Scatter: odborová hustota nebo pokrytí KV × příjmový GINI (EU27 panel, 1 rok)
- X-osa: union density nebo CB coverage (OECD AIAS ICTWSS / ETUI)
- Y-osa: Gini příjmový (Eurostat ilc_di12)
- Očekávaná korelace: negativní
- Pozor: CZ je outlier (nízký GINI + slabý SD) — nutno zkusit vysvětlit v textu jako historický artefakt

---

## 6. Bibliografické záznamy (pro .bib soubory)

Tyto záznamy přidat do socialnidialog-bibtexmanager.bib nebo socialnidialog-zotero.bib.

[ubs_wealth_databook_2022]
  Author: UBS Group AG
  Title: Global Wealth Databook 2022
  Year: 2022
  Institution: UBS Group AG, Zurich
  URL: https://www.ubs.com/global/en/family-office-uhnw/reports/global-wealth-report-2023/
  Note: Tabulka 3-1 (str. 119-122): mean wealth, median wealth, Gini coefficient per country

[rsf_czech_2021]
  Author: Reporters Without Borders (RSF)
  Title: World Press Freedom Index 2021 — Czech Republic
  Year: 2021
  Institution: RSF — Reporters Without Borders, Paris
  URL: https://rsf.org/en/czech-republic

