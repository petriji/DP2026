# Dataset Index

Reference for every external dataset used in the analytics pipeline.
All downloads are cached in `python/data/` with hash-based filenames (`{filter}_{sha1[:8]}.csv`).
Re-download with `force=True` in `fetch_*()` calls.

---

## OECD Stats — SDMX API (`fetch_oecd`)

### `CTS_CIT` — Corporate Tax Statistics (statutory CIT rates)

Primary B2 source in the ternary model.

| Dimension | Code | Meaning |
|-----------|------|---------|
| `CORP_TAX` | `COMB_CIT_RATE` | Combined statutory corporate income tax rate |
| `UNIT_MEASURE` | `PC` | Percent |
| Frequency | annual | OECD annual panel |

| Script | Filter | Period |
|--------|--------|--------|
| `stav_korporatni_dan.py` | `CORP_TAX=COMB_CIT_RATE`, `UNIT_MEASURE=PC` | `2000`– |
| `_ternary_calc.py` (B2) | same as above, fallback chain `CIT_RATE` → `CIT_RATE_LESS_SUB_NAT` → expert `CY=14.1` (2026) | `2000`– |

---

## Eurostat — SDMX 2.1 API (`fetch_eurostat`)

Eurostat datasets use dot-separated SDMX dimension filters.
`+` selects multiple values in one dimension; trailing `.` = all geo codes.
`START_YEAR` refers to a per-script constant (typically `YEAR - 10` or `2004`).

### `nama_10_pc` — GDP per capita

National accounts aggregate — GDP per capita in PPS.

| Dimension | Code | Meaning |
|-----------|------|---------|
| freq | `A` | Annual |
| unit | `PC_EU27_2020_HAB_MPPS_CP` | Per capita, EU27_2020 = 100, current PPS |
| unit | `CP_PPS_EU27_2020_HAB` | Per capita, absolute PPS (EUR) |
| na_item | `B1GQ` | Gross domestic product at market prices |

| Script | Filter | Period |
|--------|--------|--------|
| `stav_hdp_vyvoj.py` | `A.PC_EU27_2020_HAB_MPPS_CP.B1GQ.` | `START_YEAR`– |
| `eu_prijem_pps.py` | `A.PC_EU27_2020_HAB_MPPS_CP.B1GQ.` | `START_YEAR`– |
| `stav_prijem_pomer.py` | `A.PC_EU27_2020_HAB_MPPS_CP.B1GQ.` | `START_YEAR`– |
| `korelace_analyza.py` | `A.PC_EU27_2020_HAB_MPPS_CP.B1GQ.` | `START_YEAR`– |
| `eu_pokryti_prijem.py` | `A.PC_EU27_2020_HAB_MPPS_CP.B1GQ.` | `START_YEAR`– |
| `prakticka_srovnani.py` | `A.CP_PPS_EU27_2020_HAB.B1GQ.{GEO}` | — |

---

### `nama_10_lp_ulc` — Labour productivity per hour worked

Nominal labour productivity per hour, PPS relative to EU27.

| Dimension | Code | Meaning |
|-----------|------|---------|
| freq | `A` | Annual |
| unit | `PC_EU27_2020_MPPS_CP` | % of EU27_2020 average in PPS |
| na_item | `NLPR_HW` | Nominal labour productivity per hour worked |

| Script | Filter | Period |
|--------|--------|--------|
| `eu_konvergence.py` | `A.PC_EU27_2020_MPPS_CP.NLPR_HW.` | `START_YEAR`– |
| `eu_produktivita_prijem_trajektorie.py` | `A.PC_EU27_2020_MPPS_CP.NLPR_HW.` | `START_YEAR`– |

---

### `ilc_di12` — Gini coefficient (equivalised disposable income)

Income inequality index, range 0–100. Based on EU-SILC survey.

| Dimension | Code | Meaning |
|-----------|------|---------|
| freq | `A` | Annual |
| hhtyp | `TOTAL` | All household types |
| indic_il | `GINI_HND` | Gini index, equivalised disposable income |

| Script | Filter | Period |
|--------|--------|--------|
| `eu_gini_prijem.py` | `A.TOTAL.GINI_HND.` | `START_YEAR`– |
| `korelace_hustota_gini.py` | `A.TOTAL.GINI_HND.` | `START_YEAR`– |
| `korelace_analyza.py` | `A.TOTAL.GINI_HND.` | `START_YEAR`– |
| `prakticka_srovnani.py` | `A.TOTAL.GINI_HND.{GEO}` | — |

---

### `earn_nt_net` — Net annual earnings

Net earnings after tax and SSC for a single person without children at 100 % of average worker.

| Dimension | Code | Meaning |
|-----------|------|---------|
| freq | `A` | Annual |
| currency | `PPS` | Purchasing power standard |
| estruct | `NET` | Net earnings |
| ecase | `P1_NCH_AW100` | Single, no children, 100 % average worker |

| Script | Filter | Period |
|--------|--------|--------|
| `stav_prijem_pomer.py` | `A.PPS.NET.P1_NCH_AW100.` | `START_YEAR`– |
| `eu_konvergence.py` | `A.PPS.NET.P1_NCH_AW100.` | `START_YEAR`– |
| `korelace_analyza.py` | `A.PPS.NET.P1_NCH_AW100.` | `START_YEAR`– |
| `eu_produktivita_prijem_trajektorie.py` | `A.PPS.NET.P1_NCH_AW100.` | `START_YEAR`– |

---

### `earn_nt_taxwedge` — Tax wedge on labour costs

Tax wedge as % of total labour costs (PIT + employee SSC + employer SSC − cash benefits).
Single person at 100 % average worker, no children.

| Script | Filter | Period |
|--------|--------|--------|
| `eu_danovy_klin.py` | *(none — all countries)* | `2015`– |
| `prakticka_srovnani.py` | `A.{GEO}` | — |

---

### `lfsa_ewhun2` — Average weekly hours worked

Usual weekly hours in main job, employed persons 15–64.

| Dimension | Code | Meaning |
|-----------|------|---------|
| worktime | `TOTAL` | All working-time arrangements |
| wstatus | `EMP` | Employed |
| nace_r2 | `TOTAL` | All NACE sectors |
| age | `Y15-64` | Age 15–64 |
| sex | `T` | Both sexes |
| unit | `HR` | Hours |

| Script | Filter | Period |
|--------|--------|--------|
| `korelace_analyza.py` | `A.TOTAL.EMP.TOTAL.Y15-64.T.HR.` | `START_YEAR`– |
| `eu_produktivita_prijem_trajektorie.py` | `A.TOTAL.EMP.TOTAL.Y15-64.T.HR.` | `START_YEAR`– |
| `prakticka_srovnani.py` | `A.TOTAL.EMP.TOTAL.Y15-64.T.HR.{GEO}` | — |
| `stav_stavky.py` | `A.TOTAL.EMP.TOTAL.Y15-64.T.HR.` | `START_YEAR`– |

---

### `lfsi_emp_a` — Employment rate (annual)

Employment rate of working-age population as % of population in that age group.

| Dimension | Code | Meaning |
|-----------|------|---------|
| indic_em | `EMP_LFS` | Employed (LFS definition) |
| sex | `T` | Both sexes |
| age | `Y20-64` | Age 20–64 |
| unit | `PC_POP` | % of population |
| unit | `THS_PER` | Thousands of persons (DK-specific) |

| Script | Filter | Period |
|--------|--------|--------|
| `stav_zamestnanost.py` | `A.EMP_LFS.T.Y20-64.PC_POP.{GEO}` | `START_YEAR`– |
| `prakticka_srovnani.py` | `A.EMP_LFS.T.Y20-64.PC_POP.{GEO}` | — |
| `stav_stavky.py` | `A.EMP_LFS.T.Y20-64.THS_PER.DK` | `START_YEAR`– |

---

### `earn_gr_gpgr2` — Gender pay gap (unadjusted)

Difference between average gross hourly earnings of male and female employees, as % of male earnings.

| Script | Filter | Period |
|--------|--------|--------|
| `problemy_gpg.py` | *(none — all countries)* | `2018`– |
| `problemy_stratifikace.py` | `A.PC.B-S_X_O.{GEO}` | `START_YEAR`– |

---

### `earn_ses_hourly` — SES hourly earnings (decile distribution)

Gross hourly earnings from Structure of Earnings Survey — D1, median, D9.

| Dimension | Code | Meaning |
|-----------|------|---------|
| nace_r2 | `B-S_X_O` | Business economy excl. public admin |
| isco08 | `TOTAL` | All occupations |
| worktime | `TOTAL` | All work arrangements |
| age | `TOTAL` | All age groups |
| sex | `M+F` | Both sexes |
| indic_se | `D1_E_EUR+MED_E_EUR+D9_E_EUR` | 1st decile + median + 9th decile (EUR) |

| Script | Filter | Period |
|--------|--------|--------|
| `problemy_gpg.py` | `A.B-S_X_O.TOTAL.TOTAL.TOTAL.M+F.D1_E_EUR+MED_E_EUR+D9_E_EUR.{GEO}` | — |

---

### `earn_ses_pub1s` — SES low-wage earners

Proportion of employees earning < 2/3 of national median gross hourly earnings.

| Script | Filter | Period |
|--------|--------|--------|
| `prakticka_srovnani.py` | `A.T.{GEO}` | — |

---

### `prc_ppp_ind` — Price level index (PLI)

Price level index relative to EU27 (2020) = 100. For converting EUR to comparable volumes.

| Dimension | Code | Meaning |
|-----------|------|---------|
| na_item | `PLI_EU27_2020` | Price level index, EU27_2020 = 100 |
| ppp_cat | `GDP` | GDP aggregation level |

| Script | Filter | Period |
|--------|--------|--------|
| `eu_cenova_hladina.py` | `A.PLI_EU27_2020.GDP.` | `START_YEAR`– |
| `prakticka_srovnani.py` | `A.PLI_EU27_2020.GDP.{GEO}` | `YEAR - 3`– |
| `eu_odvetvove_mzdy.py` | `A.PLI_EU27_2020.GDP.` | `DISPLAY_YEAR`– |

---

### `lc_lci_r2_a` — Labour cost index (annual, 2020 = 100)

Annual index of total hourly labour costs, base 2020 = 100.

| Dimension | Code | Meaning |
|-----------|------|---------|
| index_base | `I20` | Index 2020 = 100 |
| nace_r2 | `B-S` / `B-E` / `C` / `F` / `G-J` / `K-N` | NACE sector groups |
| lcstruct | `D1_D4_MD5` | Total labour costs (wages + employer SSC − subsidies) |

| Script | Filter | Period |
|--------|--------|--------|
| `stav_ipp_mzdy.py` | `A.I20.B-S.D1_D4_MD5.{GEO}` | `START_YEAR - 1`– |
| `stav_ipp_doplnkove.py` | `A.I20.B-S.D1_D4_MD5.CZ` | `START_YEAR - 1`– |
| `problemy_sektor_mzdy.py` | `A.I20.{NACE}.D1_D4_MD5.{GEO}` (loop over B-E, C, F, G-J, K-N) | `START_YEAR - 1`– |

---

### `lc_lci_lev` — Labour cost levels (EUR/hour)

Absolute hourly labour costs in EUR. Cross-country level comparison.

| Dimension | Code | Meaning |
|-----------|------|---------|
| currency | `EUR` | Euro |
| lcstruct | `D1_D4_MD5` | Total labour costs |
| nace_r2 | `B-S_X_O` / `C+G+J+K` | Business economy / selected sectors |

| Script | Filter | Period |
|--------|--------|--------|
| `prakticka_srovnani.py` | `A.EUR.D1_D4_MD5.B-S_X_O.{GEO}` (fallback `B-S`) | `YEAR - 3`– |
| `eu_odvetvove_mzdy.py` | `A.EUR.D1_D4_MD5.C+G+J+K.{GEO}` | `DISPLAY_YEAR`– |
| `eu_odvetvove_mzdy.py` | `A.EUR.D1_D4_MD5.C+G+J+K.` (all geo) | `DISPLAY_YEAR`– |

---

### `demo_pjanind` — Old-age dependency ratio

Ratio of population 65+ to population 20–64 (× 100).

| Dimension | Code | Meaning |
|-----------|------|---------|
| indic_de | `OLDDEP1` | Old-age dependency ratio I |

| Script | Filter | Period |
|--------|--------|--------|
| `vyhled_zavislost.py` | `A.OLDDEP1.` | `START_YEAR`– |
| `prakticka_srovnani.py` | `A.OLDDEP1.{GEO}` | — |

---

### `jvs_a_nace2` — Job vacancy rate

Job vacancy rate: vacancies / (occupied posts + vacancies) × 100.

| Dimension | Code | Meaning |
|-----------|------|---------|
| nace_r2 | `B-S_X_O` / `TOTAL` | Business economy / all sectors |
| sizeclas | `GE10` | Enterprises ≥ 10 employees |
| indic_em | `JVR` | Job vacancy rate |

| Script | Filter | Period |
|--------|--------|--------|
| `prakticka_srovnani.py` | `A.B-S_X_O.GE10.JVR.{GEO}` (fallbacks: `TOTAL`/`B-S_X_O..JVR`) | — |

---

### `ilc_peps01n` — AROPE rate

At risk of poverty or social exclusion (EU2030 definition). Combines income poverty, severe material/social deprivation, and very low work intensity.

| Dimension | Code | Meaning |
|-----------|------|---------|
| unit | `PC` | Percentage |
| age | `TOTAL` | All ages |
| sex | `T` | Both sexes |

| Script | Filter | Period |
|--------|--------|--------|
| `stav_arope.py` | `A.PC.TOTAL.T.` | — |

---

### `edat_aes_l21` — Foreign language skills: total population

Distribution of adult population by number of foreign languages known (Adult Education Survey). No pre-filter; post-filtered in code.

| Script | Filter | Period |
|--------|--------|--------|
| `problemy_jazyky.py` | *(none — full download)* | — |

### `edat_aes_l22` — Foreign language skills by age group

Same survey, broken down by age group. Post-filtered to Y25-54.

| Script | Filter | Period |
|--------|--------|--------|
| `problemy_jazyky.py` | *(none — full download)* | — |

### `edat_aes_l23` — Foreign language skills by education level

Same survey, broken down by ISCED level. Post-filtered to ED5-8 (tertiary).

| Script | Filter | Period |
|--------|--------|--------|
| `problemy_jazyky.py` | *(none — full download)* | — |

---

### `lfst_r_lfe2ecomm` — Cross-border commuting

Employment by place of residence vs. place of work (regional LFS). No pre-filter; post-filtered in code.

| Script | Filter | Period |
|--------|--------|--------|
| `problemy_dojezdeni.py` | *(none — full download)* | `START_YEAR`– |

### `lfst_r_lfe2emprtn` — Regional employment rates (NUTS 2)

Employment rates at NUTS 2 regional level.

| Dimension | Code | Meaning |
|-----------|------|---------|
| unit | `THS_PER` | Thousands of persons |
| sex | `T` | Both sexes |
| age | `TOTAL` | All age groups |

| Script | Filter | Period |
|--------|--------|--------|
| `problemy_dojezdeni.py` | `A.THS_PER.T.TOTAL.` | `2015`– |

---

### `demo_find` — Total fertility rate

Average number of live births per woman.

| Dimension | Code | Meaning |
|-----------|------|---------|
| indic_de | `TOTFERRT` | Total fertility rate |

| Script | Filter | Period |
|--------|--------|--------|
| `vyhled_porodnost.py` | `A.TOTFERRT.` | `START_YEAR`– |

---

### `prc_hicp_aind` — HICP inflation (annual average)

Harmonised Index of Consumer Prices — annual rate of change.

| Dimension | Code | Meaning |
|-----------|------|---------|
| unit | `RCH_A_AVG` | Rate of change, annual average |
| coicop | `CP00` | All items |

| Script | Filter | Period |
|--------|--------|--------|
| `stav_ipp_doplnkove.py` | `A.RCH_A_AVG.CP00.CZ` | `START_YEAR`– |

---

### `migr_emi1ctz` — Emigration by citizenship

Number of persons emigrating from the reporting country, by citizenship.

| Dimension | Code | Meaning |
|-----------|------|---------|
| citizen | `CZ` | Czech citizenship |
| agedef | *(empty)* | All age definitions |
| age | *(empty)* | All ages |
| unit | `NR` | Number of persons |
| sex | `T` | Both sexes |

| Script | Filter | Period |
|--------|--------|--------|
| `problemy_emigrace.py` | `A.CZ...NR.T.CZ` | `START_YEAR`– |

---

### `lfsa_egaps` — Self-employment share

Employment by professional status — total employed vs. self-employed.

| Dimension | Code | Meaning |
|-----------|------|---------|
| unit | `THS_PER` | Thousands of persons |
| sex | `T` | Both sexes |
| age | `Y15-74` | Age 15–74 |
| wstatus | `EMP+SELF` | Employed + self-employed (multi-value) |

| Script | Filter | Period |
|--------|--------|--------|
| `eu_osvc_mapa.py` | `A.THS_PER.T.Y15-74.EMP+SELF.` | `2015`– |

---

## OECD — SDMX API (`fetch_oecd`)

OECD datasets use `filter_expr="all"` (default) and are post-filtered in Python
by `INDICATOR`, `MEASURE`, `UNIT_MEASURE`, etc.

### `CBC` — Collective Bargaining Coverage

Percentage of employees covered by collective agreements (measure `ERB`).
Source: OECD/AIAS ICTWSS database.

| Script | Filter | start_period | Post-filter |
|--------|--------|-------------|-------------|
| `eu_pokryti_prijem.py` | `all` | `START_YEAR` | `ERB` measure |
| `korelace_analyza.py` | `all` | `START_YEAR` | `ERB` measure |
| `eu_pokryti_kv_vyvoj.py` | `all` | `1993` | `ERB` + `ERC` measures |
| `eu_pokryti_kv_mapa.py` | `all` | `2010` | `ERB` measure |
| `prakticka_srovnani.py` | `all` | `YEAR - 10` | `ERB` measure |

---

### `TUD` — Trade Union Density

Percentage of wage/salary earners who are trade union members.
Source: OECD/AIAS ICTWSS database.

| Script | Filter | start_period | Post-filter |
|--------|--------|-------------|-------------|
| `stav_hustota_vyvoj.py` | `all` | `1993` | `INDICATOR=TUD` |
| `eu_hustota_mapa.py` | `all` | `2010` | `INDICATOR=TUD` |
| `korelace_hustota_gini.py` | `all` | `2010` | `INDICATOR=TUD` |
| `korelace_analyza.py` | `all` | `2004` | `INDICATOR=TUD` |
| `prakticka_srovnani.py` | `all` | `YEAR - 10` | `INDICATOR=TUD` |

---

### `WEALTH` — Wealth Distribution (HFCS)

Household Finance and Consumption Survey — wealth inequality indicators.

| Script | Filter | start_period | Post-filter |
|--------|--------|-------------|-------------|
| `eu_bohatstvi_mapa.py` | `all` | `2008` | `SH_TOP10` (top-10 % share) |
| `eu_bohatstvi_vyvoj.py` | `all` | `2008` | `SH_TOP10` |
| `eu_bohatstvi_top20.py` | `all` | `2008` | `SH_TOP5` (top-5 % share) |

---

### `LMPEXP` — Labour Market Policy Expenditure

Public expenditure on labour market policies as % of GDP.

| Script | Filter | start_period | Post-filter |
|--------|--------|-------------|-------------|
| `eu_apz_vydaje.py` | `all` | `2004` | `MEASURE=EXP`, `UNIT_MEASURE=PT_B1GQ`, `PROGRAMME=_T` |
| `eu_apz_mapa.py` | `all` | — | same |
| `prakticka_srovnani.py` | `all` | `YEAR - 5` | same |

---

## ILOSTAT — REST API (`fetch_ilostat`)

### `STR_DAYS_ECO_RT_A` — Working days lost to strikes

Days not worked due to strikes and lockouts per 1 000 workers (annual).

| Script | Params | Notes |
|--------|--------|-------|
| `stav_stavky.py` | `classif1=ECO_AGGREGATE_TOTAL`, `sex=SEX_T` | DK missing → supplemented from Statistics Denmark |
| `stav_socialni_mir_data.py` | `classif1=ECO_AGGREGATE_TOTAL`, `sex=SEX_T` | Builds B4 strike benchmark snapshot for ternary + social-peace choropleths; DK supplemented from Statistics Denmark |

---

## IPP / ISPP — MPSV Excel (`fetch_ipp`)

Informace o pracovních podmínkách (Information on Working Conditions).
Published by MPSV via `kolektivnismlouvy.cz`. Excel workbooks, yearly.

- **Years 2007–2014:** `ISPP_*.xls` format (legacy XLS)
- **Years 2015–2018:** `IPP_*.xls`
- **Years 2019–2025:** `IPP_*.xlsx`

### `odmenovani` — Wage agreements in collective agreements

Sheet A15a — agreed wage increases by agreement type (higher-level vs. enterprise).

| Script | Years | Notes |
|--------|-------|-------|
| `stav_ipp_mzdy.py` | 2007–2025 | Extracts median negotiated wage increase |
| `stav_ipp_doplnkove.py` | 2007–2025 | Compared with LCI and HICP |

### `mzda_tarify` — Wage tariff provisions

Sheet A1a — share of collective agreements containing wage tariff tables.

| Script | Years | Notes |
|--------|-------|-------|
| `stav_ipp_rozsah.py` | 2007–2025 | Tracks provision breadth over time |

### `spoluprace_smluvnich_stran` — Social partner cooperation

Sheet A19a — cooperation provisions between trade unions and employers.

| Script | Years | Notes |
|--------|-------|-------|
| `stav_ipp_rozsah.py` | 2007–2025 | Alias `spoluprace_sml_stran` for 2007–2008 |

---

## ISPV / RSCP — TREXIMA Excel (`fetch_ispv`)

Informační systém o průměrném výdělku (Information System on Average Earnings).
Published by TREXIMA for MPSV via `ispv.cz`. NACE-level wage breakdowns.

### Private sphere (`podnikatelska`)

Contains: median, mean, P10, P25, P75, P90 gross monthly earnings by NACE section.

| Script | Years | Notes |
|--------|-------|-------|
| `problemy_sektor_mzdy.py` | 2016–2024 | NACE-level wage comparison (CZ) |
| `problemy_stratifikace.py` | 2016–2024 | P90/P10 stratification by NACE |
| `problemy_mzda_duchod.py` | 2016–2024 | Wage distribution vs. pension formula |

### Public sphere (`nepodnikatelska`)

Same structure for public-sector employees.

| Script | Years | Notes |
|--------|-------|-------|
| `problemy_verejny_soukromy.py` | 2025 (GUID) | Public vs. private wage comparison |

---

## Other direct downloads (`fetch` / `urllib`)

### ICTWSS v2 CSV — Adjusted collective bargaining coverage

URL: `https://webfs.oecd.org/Els-com/ICTWSS-Database/ICTWSS_v2.csv`
Variable `AdjCov` — adjusted CB coverage for EU27 (except DE, SK which use OECD CBC `ERB`).

| Script | Notes |
|--------|-------|
| `eu_pokryti_kv_vyvoj.py` | Full ICTWSS timeseries |
| `korelace_analyza.py` | Cross-section for scatter plots |
| `prakticka_srovnani.py` | Single-year value |

### GISCO NUTS GeoJSON — Regional boundaries

URL: `https://gisco-services.ec.europa.eu/.../NUTS_RG_20M_2021_3035.geojson`
NUTS regions at 20 m resolution, EPSG:3035 (LAEA Europe).

| Script | Notes |
|--------|-------|
| `problemy_dojezdeni.py` | NUTS 2/3 commuting map |
| `problemy_gpg.py` | Regional gender pay gap map |
| `problemy_jazyky.py` | Regional language proficiency map |

### Natural Earth GeoJSON — Country boundaries

Fetched via `statout/map_europe.py` for all choropleth maps.
`ne_110m_admin_0_countries` at 110 m resolution.

| Script | Notes |
|--------|-------|
| All `*_map.py` scripts | Background country polygons |

### Statistics Denmark ABST1 — Strike days (DK)

URL: `https://api.statbank.dk/v1/data/ABST1/CSV?lang=en&ENHED=300&BRANCHE=000&Tid=*`
Working days lost due to strikes — Denmark doesn't report to ILOSTAT.

| Script | Notes |
|--------|-------|
| `stav_stavky.py` | DK supplement to ILOSTAT data |

### ČSSZ pension yearbooks

URL pattern: `https://www.cssz.cz/documents/20143/2946719/Ročenka+{year}.zip/{guid}`
Excel tables with pension distribution data, years 2022–2024.

| Script | Notes |
|--------|-------|
| `problemy_mzda_duchod.py` | Pension amount distribution by decile |

### MPSV Čistá mzda workbooks

Workbooks `CR_254_MZS-xlsx` (wage sphere) and `CR_254_PLS-xlsx` (salary sphere).
Net wage reference data from MPSV.

| Script | Notes |
|--------|-------|
| *(reference data — not directly consumed by pipeline)* | — |

### ČZSO election results

Workbooks `Vysledky-ve-formatu-XLS_*.xlsx` — Czech election results.

| Script | Notes |
|--------|-------|
| *(not yet integrated into pipeline)* | 14 files cached |

---

## Scripts with no external data

These scripts use only built-in statutory constants or import from other analysis modules:

| Script | Purpose |
|--------|---------|
| `problemy_cz_duchod.py` | Czech pension formula (§ 155/1995 Sb.) |
| `cz_tax_model.py` | Czech tax wedge model (statutory rates) |
| `cz_calculator.py` | Pension calculator (imports `cz_pension_model`) |
| `problemy_cz_model.py` | Visualization of pension/tax model outputs |

---

## Cache file naming

Files in `python/data/` are named `{filter_or_url_path}_{sha1[:8]}.{ext}`.
The SHA-1 hash is computed from the full download URL, ensuring unique caching
even when the same dataset is fetched with different filters.

To identify which script produced a cached file, search for the hash suffix
in `fetch_*()` call sites — or re-run the script with `force=True` and observe
which file gets rewritten.
