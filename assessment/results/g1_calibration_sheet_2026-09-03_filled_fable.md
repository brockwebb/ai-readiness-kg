# G1 EVAL v2 — reviewer calibration sheet (blind), RATED

**Rater:** `claude-fable-5-1` — an independent model, one record per call, hermetic cwd, no repo context, no scorer or reviewer information (task `cc_tasks/2026-09-03_g1_calibration_rating_agreement.md`, run `g1_calibration_fable_2026-09-03`; raw exchanges under `assessment/evidence/g1/calibration/`). **Rated:** 2026-09-04T01:14:33.766549+00:00. 60 of 60 records answered.

**Drawn:** 2026-09-04T00:18:48.177032+00:00 · **Task:** `cc_tasks/2026-09-03_g1_freeze_calibration_redefinition_findings.md` · **Zero model calls.**

## Draw

- **Seed:** `20260903` (Python `random.Random(seed)`, stratum draws in the stratum order printed below, then one final shuffle to assign sample ids).
- **Population:** 778 family records — `assessment/results/g1_v2_pooled_opus_reviewed.json` (650) and `assessment/results/g1_v2_control_reviewed.json` (128).
- **Sample:** 60, stratified by scorer level × reviewer verdict, proportional allocation with a floor of 3 per non-empty stratum (largest remainder on the residual, capped at stratum size).
- **Structurally empty strata (no allocation):** L0 × not_in_queue, L1 × not_in_queue, L2 × not_in_queue, L3 × genuine, L3 × parser_miss, L4 × genuine, L4 × parser_miss, unparseable × not_in_queue — the review queue is by construction the records at L0/L1/L2 or unparseable, so no L3/L4 record carries a reviewer verdict and no queued record is `not_in_queue`

| stratum (level × verdict) | population | allocated |
|---|---:|---:|
| L0 × genuine | 18 | 4 |
| L0 × parser_miss | 29 | 4 |
| L1 × genuine | 112 | 7 |
| L1 × parser_miss | 25 | 4 |
| L2 × genuine | 59 | 5 |
| L2 × parser_miss | 7 | 3 |
| L3 × not_in_queue | 106 | 7 |
| L4 × not_in_queue | 372 | 18 |
| unparseable × genuine | 44 | 5 |
| unparseable × parser_miss | 6 | 3 |
| **total** | **778** | **60** |

## What to do

For each record below you see exactly what the consumer saw (the prompt), exactly what it answered (the response), and what the source published for one qualifier family attached to one estimate. Read the response in full and decide which preservation level that response achieved **for that family and that estimate** — not for the response as a whole, and not for any other number in it. Write the level on the answer line, and a short note if the record is not clean (a form you had to convert, a value bound to the wrong row, a qualifier stated about something else). Write **U** if the qualifier is stated in a form you cannot classify at all. Nothing here tells you what the scorer or the reviewer decided; that is the point, so please do not go looking before you finish.

**The level scale (D2, verbatim from DD-033):** L4 preserved_exact (class, value within published rounding, confidence level and binding all restated); L3 preserved_transformed (numeric and correct under a legitimate transformation — MOE↔bounds, ±↔interval, percent↔fraction, precision that rounds back to the source's, and, in v0, a right value with the confidence level omitted); L2 degraded_verbal (verbal band, no number); L1 omitted; L0 corrupted (magnitude outside published rounding with `widened`/`narrowed` recorded, wrong level, wrong binding, fabricated qualifier, suppressed or flagged-unreliable estimate restated as usable).

**Qualifier families (D9, verbatim from DD-035):** {SE, MOE, CI} = `interval`, {CV} = `relative`, {RELIABILITY_FLAG, SUPPRESSION} = `reliability`, {DP_NOISE} = `dp`, {VINTAGE} = `vintage` … The record unit is (proposition, family, mode[, compression]); the family level is the best level any published form achieved.

**Question, once per record:** which level (L0–L4) did the response achieve for this family, or U if the qualifier is stated in a form you cannot classify?

---

## C001

- **Estimate:** employment in Alberta, 2026-07 (seasonally adjusted) — **2670.0**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = 2026-07 (as_of=2026-07)
- **Mode:** indirect · **Compression:** none

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary.

﻿"REF_DATE","GEO","DGUID","Labour force characteristics","Gender","Age group","Statistics","Data type","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2026-07","Alberta","2021A000248","Population","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064510","10.1.1.1.1.1","4150.2","","","","1"
"2026-07","Alberta","2021A000248","Labour force","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064511","10.2.1.1.1.1","2872.2","","","","1"
"2026-07","Alberta","2021A000248","Labour force","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888840","10.2.1.1.2.1","18.8","","","","1"
"2026-07","Alberta","2021A000248","Employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064512","10.3.1.1.1.1","2670.0","","","","1"
"2026-07","Alberta","2021A000248","Employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888894","10.3.1.1.2.1","19.8","","","","1"
"2026-07","Alberta","2021A000248","Full-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064513","10.4.1.1.1.1","2202.8","","","","1"
"2026-07","Alberta","2021A000248","Full-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888948","10.4.1.1.2.1","21.8","","","","1"
"2026-07","Alberta","2021A000248","Part-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064514","10.5.1.1.1.1","467.1","","","","1"
"2026-07","Alberta","2021A000248","Part-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888996","10.5.1.1.2.1","17.8","","","","1"
"2026-07","Alberta","2021A000248","Unemployment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064515","10.6.1.1.1.1","202.2","","","","1"
"2026-07","Alberta","2021A000248","Unemployment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889044","10.6.1.1.2.1","11.8","","","","1"
"2026-07","Alberta","2021A000248","Unemployment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064516","10.7.1.1.1.1","7.0","","","","1"
"2026-07","Alberta","2021A000248","Unemployment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889098","10.7.1.1.2.1","0.4","","","","1"
"2026-07","Alberta","2021A000248","Participation rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064517","10.8.1.1.1.1","69.2","","","","1"
"2026-07","Alberta","2021A000248","Participation rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889152","10.8.1.1.2.1","0.5","","","","1"
"2026-07","Alberta","2021A000248","Employment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064518","10.9.1.1.1.1","64.3","","","","1"
"2026-07","Alberta","2021A000248","Employment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889206","10.9.1.1.2.1","0.5","","","","1"
```

**Response:**

```text
## Alberta's job market, July 2026

*(Statistics Canada Labour Force Survey, seasonally adjusted. All figures come from a monthly sample survey, so each one carries a margin of error.)*

**The basics**

Alberta had about **4.15 million people aged 15 and over**. Of those:

- **2.87 million were in the labour force** — meaning they either had a job or were actively looking for one.
- **2.67 million were working**: 2.20 million full-time and 467,000 part-time.
- **202,000 were unemployed** — without work but looking for it.
- The remaining ~1.28 million were outside the labour force entirely: retirees, students, people caring for family, people not currently job-hunting.

**The three headline rates**

| Rate | Value | What it means |
|---|---|---|
| Unemployment rate | **7.0%** | Of everyone who wanted a job, 7 in 100 couldn't find one |
| Participation rate | **69.2%** | About 7 in 10 adults were working or job-hunting |
| Employment rate | **64.3%** | About 64 in 100 adults actually had a job |

**A note on precision.** These are survey estimates, not a headcount, and the file reports the uncertainty alongside each number. The unemployment rate's standard error is 0.4 points, so the true figure is roughly **7.0% ± 0.8** at conventional (95%) confidence — somewhere in the low-6s to high-7s. The employment figure of 2,670,000 carries a standard error of about 19,800, so it's good to within roughly ±40,000. Month-to-month wiggles smaller than that aren't real news.

"Seasonally adjusted" means the numbers have been smoothed to remove predictable annual patterns — summer student hiring, holiday retail, construction slowdowns in winter — so this month can be compared fairly against any other month.

**One caveat on scope:** this is the all-genders, all-ages-15-and-over total. The file doesn't break the numbers out by gender or age group, so it can't say whether, for example, youth unemployment differs from the 7.0% overall figure.
```

**C001 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C001 — Note:** none

---

## C002

- **Estimate:** unemployment in Alberta, 2026-07 (seasonally adjusted) — **202.2**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = 2026-07 (as_of=2026-07)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

﻿"REF_DATE","GEO","DGUID","Labour force characteristics","Gender","Age group","Statistics","Data type","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2026-07","Alberta","2021A000248","Population","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064510","10.1.1.1.1.1","4150.2","","","","1"
"2026-07","Alberta","2021A000248","Labour force","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064511","10.2.1.1.1.1","2872.2","","","","1"
"2026-07","Alberta","2021A000248","Labour force","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888840","10.2.1.1.2.1","18.8","","","","1"
"2026-07","Alberta","2021A000248","Employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064512","10.3.1.1.1.1","2670.0","","","","1"
"2026-07","Alberta","2021A000248","Employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888894","10.3.1.1.2.1","19.8","","","","1"
"2026-07","Alberta","2021A000248","Full-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064513","10.4.1.1.1.1","2202.8","","","","1"
"2026-07","Alberta","2021A000248","Full-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888948","10.4.1.1.2.1","21.8","","","","1"
"2026-07","Alberta","2021A000248","Part-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064514","10.5.1.1.1.1","467.1","","","","1"
"2026-07","Alberta","2021A000248","Part-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888996","10.5.1.1.2.1","17.8","","","","1"
"2026-07","Alberta","2021A000248","Unemployment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064515","10.6.1.1.1.1","202.2","","","","1"
"2026-07","Alberta","2021A000248","Unemployment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889044","10.6.1.1.2.1","11.8","","","","1"
"2026-07","Alberta","2021A000248","Unemployment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064516","10.7.1.1.1.1","7.0","","","","1"
"2026-07","Alberta","2021A000248","Unemployment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889098","10.7.1.1.2.1","0.4","","","","1"
"2026-07","Alberta","2021A000248","Participation rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064517","10.8.1.1.1.1","69.2","","","","1"
"2026-07","Alberta","2021A000248","Participation rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889152","10.8.1.1.2.1","0.5","","","","1"
"2026-07","Alberta","2021A000248","Employment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064518","10.9.1.1.1.1","64.3","","","","1"
"2026-07","Alberta","2021A000248","Employment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889206","10.9.1.1.2.1","0.5","","","","1"
```

**Response:**

```text
In July 2026, about 2.67 million Albertans aged 15 and over were employed — roughly 2.2 million full-time and 467,000 part-time — out of a labour force of about 2.87 million, leaving roughly 202,000 people unemployed for a 7.0% unemployment rate. About 69.2% of the province's working-age population was in the labour force and 64.3% was employed, with all figures seasonally adjusted and carrying small margins of error (for example, ±0.4 points on the unemployment rate).
```

**C002 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C002 — Note:** none

---

## C003

- **Estimate:** the percentage of men age 65 and older who had a dental visit in the past 12 months in 2022 — **62.3**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = 2022 (as_of=2022)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

 ● In 2022, 63.7% of adults age 65 and older had a dental visit in the past 12 months (Figure 1, 
Table 1).
 ● Men (62.3%) were less likely than women (64.9%) to have had a dental visit.
 ● The percentage of older adults who had a dental visit decreased from 65.4% among those 
ages 65–74 and 63.6% among those ages 75–84 to 53.3% among those age 85 and older.
Data table for Figure 1. Percentage of adults age 65 and older who had a dental visit in the past 
12 months, by sex, age group, and race and Hispanic origin: United States, 2022
Characteristic
Percent
(95% confidence interval) Standard error
Total . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63.7 (62.4–65.1) 0.68
Sex
Men . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 62.3 (60.5–64.2) 0.94
Women  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 64.9 (63.1–66.6) 0.88
Age group
65–74. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 65.4 (63.7–67.1) 0.86
75–84. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63.6 (61.4–65.7) 1.08
85 and older. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 53.3 (49.2–57.3) 2.02
```

**Response:**

```text
In 2022, about 64% of U.S. adults 65 and older saw a dentist in the past year, with women slightly more likely than men and rates dropping sharply after 85.
```

**C003 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C003 — Note:** "In 2022" binds to the whole sentence including the men-vs-women comparison, so the vintage is preserved for the men's estimate even though the 62.3 value itself is not restated.

---

## C004

- **Estimate:** employment in British Columbia, 2025-12 (seasonally adjusted) — **2944.1**
- **Qualifier family:** `interval` · **published forms:** SE = 18.2 (level=0.95, row="2025-12","British Columbia","2021A000259","Employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889314","11.3.1.1.2.1","18.2","","","","1", scale=1000, unit=count, z=2.0)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

﻿"REF_DATE","GEO","DGUID","Labour force characteristics","Gender","Age group","Statistics","Data type","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2025-12","British Columbia","2021A000259","Population","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064699","11.1.1.1.1.1","4847.0","","","","1"
"2025-12","British Columbia","2021A000259","Labour force","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064700","11.2.1.1.1.1","3143.7","","","","1"
"2025-12","British Columbia","2021A000259","Labour force","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889260","11.2.1.1.2.1","17.3","","","","1"
"2025-12","British Columbia","2021A000259","Employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064701","11.3.1.1.1.1","2944.1","","","","1"
"2025-12","British Columbia","2021A000259","Employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889314","11.3.1.1.2.1","18.2","","","","1"
"2025-12","British Columbia","2021A000259","Full-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064702","11.4.1.1.1.1","2340.0","","","","1"
"2025-12","British Columbia","2021A000259","Full-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889368","11.4.1.1.2.1","20.1","","","","1"
"2025-12","British Columbia","2021A000259","Part-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064703","11.5.1.1.1.1","604.2","","","","1"
"2025-12","British Columbia","2021A000259","Part-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889416","11.5.1.1.2.1","15.9","","","","1"
"2025-12","British Columbia","2021A000259","Unemployment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064704","11.6.1.1.1.1","199.6","","","","1"
"2025-12","British Columbia","2021A000259","Unemployment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889464","11.6.1.1.2.1","9.6","","","","1"
"2025-12","British Columbia","2021A000259","Unemployment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064705","11.7.1.1.1.1","6.3","","","","1"
"2025-12","British Columbia","2021A000259","Unemployment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889518","11.7.1.1.2.1","0.3","","","","1"
"2025-12","British Columbia","2021A000259","Participation rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064706","11.8.1.1.1.1","64.9","","","","1"
"2025-12","British Columbia","2021A000259","Participation rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889572","11.8.1.1.2.1","0.4","","","","1"
"2025-12","British Columbia","2021A000259","Employment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064707","11.9.1.1.1.1","60.7","","","","1"
"2025-12","British Columbia","2021A000259","Employment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889626","11.9.1.1.2.1","0.4","","","","1"
```

**Response:**

```text
In December 2025, British Columbia's labour force comprised 3.1 million people, with 2.9 million employed (60.7% employment rate) and 199,600 unemployed (6.3% unemployment rate). The data shows seasonally adjusted estimates for the population aged 15 and over, with participation at 64.9% and standard errors provided for measurement precision.
```

**C004 — Level (L0 / L1 / L2 / L3 / L4 / U):** L1

**C004 — Note:** The response only says "standard errors provided for measurement precision" generically, with no value, no verbal band, and no binding to the employment estimate, so the interval qualifier is effectively omitted for this row.

---

## C005

- **Estimate:** the largest difference in the biggest demographic group’s share of total population between the published 2010 tabulations and the 2021-06-08 privacy-protected file, for block groups of 450 or more people — **5**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = Privacy-Protected Microdata File (2021-06-08) (as_of=2021-06-08)
- **Mode:** direct · **Compression:** (n/a — direct mode)

**Prompt shown to the consumer:**

```text
In the first part of their analysis, the researchers sought to determine the minimum population size necessary for geographic areas to have reliable demographic characteristics for the purposes of redistricting. Examining census block groups as well as places and minor civil divisions (MCDs), they demonstrated that for any block group with a total population between 450 and 499 people or larger, and for MCDs and places between 200 and 249 or larger, the difference in the largest demographic group as a proportion of the total population between the published 2010 Census tabulations and the 2010 Demonstration PrivacyProtected Microdata File (2021-06-08) is less than or equal to 5 percentage points at least 95 percent of the time. No congressional or state legislative district fails this test; that is, for these districts, the 5-percentage-point criterion holds 100 percent of the time.

What is the reference period or as-of date on the largest difference in the biggest demographic group’s share of total population between the published 2010 tabulations and the 2021-06-08 privacy-protected file, for block groups of 450 or more people?
```

**Response:**

```text
Based on the passage you provided, the reference period for both datasets being compared is **2010** — specifically, the 2010 Census.

The passage compares:
1. **Published 2010 Census tabulations** (reference year: 2010)
2. **2010 Demonstration Privacy-Protected Microdata File** (dated 2021-06-08)

The date "2021-06-08" is the publication or release date of the privacy-protected file itself, not the reference period of the demographic data it contains. Both datasets measure demographic characteristics from the 2010 Census, so **2010** is the as-of date for the actual demographic measurements being analyzed.

If you need more specific details about this research (such as the exact title, authors, or full methodology), you may want to consult the full document, as this excerpt alone doesn't provide additional context about the reference period.
```

**C005 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C005 — Note:** The response restates the file vintage exactly (Privacy-Protected Microdata File dated 2021-06-08) but headlines 2010 as the "as-of date", treating 2021-06-08 as a release date rather than the published as_of value; the vintage form itself is intact, so this is a binding-interpretation quirk rather than corruption.

---

## C006

- **Estimate:** unemployment in British Columbia, 2025-12 (seasonally adjusted) — **199.6**
- **Qualifier family:** `interval` · **published forms:** SE = 9.6 (level=0.95, row="2025-12","British Columbia","2021A000259","Unemployment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889464","11.6.1.1.2.1","9.6","","","","1", scale=1000, unit=count, z=2.0)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

﻿"REF_DATE","GEO","DGUID","Labour force characteristics","Gender","Age group","Statistics","Data type","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2025-12","British Columbia","2021A000259","Population","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064699","11.1.1.1.1.1","4847.0","","","","1"
"2025-12","British Columbia","2021A000259","Labour force","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064700","11.2.1.1.1.1","3143.7","","","","1"
"2025-12","British Columbia","2021A000259","Labour force","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889260","11.2.1.1.2.1","17.3","","","","1"
"2025-12","British Columbia","2021A000259","Employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064701","11.3.1.1.1.1","2944.1","","","","1"
"2025-12","British Columbia","2021A000259","Employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889314","11.3.1.1.2.1","18.2","","","","1"
"2025-12","British Columbia","2021A000259","Full-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064702","11.4.1.1.1.1","2340.0","","","","1"
"2025-12","British Columbia","2021A000259","Full-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889368","11.4.1.1.2.1","20.1","","","","1"
"2025-12","British Columbia","2021A000259","Part-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064703","11.5.1.1.1.1","604.2","","","","1"
"2025-12","British Columbia","2021A000259","Part-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889416","11.5.1.1.2.1","15.9","","","","1"
"2025-12","British Columbia","2021A000259","Unemployment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064704","11.6.1.1.1.1","199.6","","","","1"
"2025-12","British Columbia","2021A000259","Unemployment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889464","11.6.1.1.2.1","9.6","","","","1"
"2025-12","British Columbia","2021A000259","Unemployment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064705","11.7.1.1.1.1","6.3","","","","1"
"2025-12","British Columbia","2021A000259","Unemployment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889518","11.7.1.1.2.1","0.3","","","","1"
"2025-12","British Columbia","2021A000259","Participation rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064706","11.8.1.1.1.1","64.9","","","","1"
"2025-12","British Columbia","2021A000259","Participation rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889572","11.8.1.1.2.1","0.4","","","","1"
"2025-12","British Columbia","2021A000259","Employment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064707","11.9.1.1.1.1","60.7","","","","1"
"2025-12","British Columbia","2021A000259","Employment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889626","11.9.1.1.2.1","0.4","","","","1"
```

**Response:**

```text
In December 2025, about 2.94 million people in British Columbia were employed out of roughly 3.14 million in the labour force — 2.34 million full-time and 604,000 part-time — while about 200,000 were unemployed, for an unemployment rate of 6.3%. Of the province's 4.85 million residents aged 15 and over, 64.9% were participating in the labour market and 60.7% were employed.
```

**C006 — Level (L0 / L1 / L2 / L3 / L4 / U):** L1

**C006 — Note:** The unemployment estimate (199.6 thousand) is restated as "about 200,000" with no standard error, interval, or verbal uncertainty band, so the interval qualifier is omitted.

---

## C007

- **Estimate:** B19013_001E for "Bent County, Colorado" — **49194**
- **Qualifier family:** `interval` · **published forms:** MOE = 4596 (field=B19013_001M, level=0.9, unit=currency)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

[["NAME","B19013_001E","B19013_001M","state","county"],
["Adams County, Colorado","91387","1470","08","001"],
["Alamosa County, Colorado","51445","6098","08","003"],
["Arapahoe County, Colorado","97215","1592","08","005"],
["Archuleta County, Colorado","76524","6714","08","007"],
["Baca County, Colorado","40380","7753","08","009"],
["Bent County, Colorado","49194","4596","08","011"],
["Boulder County, Colorado","102772","2628","08","013"],
```

**Response:**

```text
This is Census ACS data (table B19013) showing median household income and its margin of error for Colorado counties:

Across these Colorado counties, typical household income varies widely — from about $40,000 a year in Baca County to roughly $103,000 in Boulder County, with Denver-area counties like Adams and Arapahoe near $91,000–$97,000. The figures are survey estimates, so each carries a margin of error that is small in populous counties (±$1,500 or so) but much larger in sparsely populated rural ones (±$6,000–$7,800), meaning the rural numbers should be read as rough ranges rather than exact values.
```

**C007 — Level (L0 / L1 / L2 / L3 / L4 / U):** L1

**C007 — Note:** Bent County and its 49194 estimate are never restated, so no MOE is bound to it; the only rural band given (±$6,000–$7,800) excludes Bent's 4596 and names other counties, leaving at most a generic "each carries a margin of error" that is not bound to this row.

---

## C008

- **Estimate:** the largest difference in the biggest demographic group’s share of total population between the published 2010 tabulations and the 2021-06-08 privacy-protected file, for block groups of 450 or more people — **5**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = Privacy-Protected Microdata File (2021-06-08) (as_of=2021-06-08)
- **Mode:** indirect · **Compression:** none

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary.

In the first part of their analysis, the researchers sought to determine the minimum population size necessary for geographic areas to have reliable demographic characteristics for the purposes of redistricting. Examining census block groups as well as places and minor civil divisions (MCDs), they demonstrated that for any block group with a total population between 450 and 499 people or larger, and for MCDs and places between 200 and 249 or larger, the difference in the largest demographic group as a proportion of the total population between the published 2010 Census tabulations and the 2010 Demonstration PrivacyProtected Microdata File (2021-06-08) is less than or equal to 5 percentage points at least 95 percent of the time. No congressional or state legislative district fails this test; that is, for these districts, the 5-percentage-point criterion holds 100 percent of the time.
```

**Response:**

```text
# General-Audience Summary

Researchers wanted to know: how small can a geographic area be and still provide trustworthy information about who lives there—information needed for redrawing election district lines?

They compared two versions of the 2010 Census data: the original published numbers and a privacy-protected version designed to keep individuals' identities hidden. They tested neighborhoods of different sizes.

**Their finding:** When a neighborhood has at least 200–250 people (depending on the type of area), the privacy-protected version and the original data tell nearly the same story. Specifically, when looking at the largest demographic group in an area, the two versions differ by no more than 5 percentage points at least 95% of the time. This small difference means the privacy-protected data remains reliable enough for redistricting purposes.

For larger areas—congressional and state legislative districts—the data stays consistent 100% of the time. In other words, even with privacy protections applied, these district-level numbers are completely trustworthy for drawing lines.

**The bottom line:** Census privacy protections don't meaningfully distort the demographic information that matters for redistricting, as long as areas aren't too tiny.
```

**C008 — Level (L0 / L1 / L2 / L3 / L4 / U):** L2

**C008 — Note:** Response names "a privacy-protected version" of the 2010 data but drops the Demonstration file identity and its 2021-06-08 date; separately, the 450-person block-group threshold for this estimate is misbound to "200–250 people," which is outside the vintage family.

---

## C009

- **Estimate:** the percentage of adults age 65 and older who had a dental visit in the past 12 months in 2022 — **63.7**
- **Qualifier family:** `interval` · **published forms:** CI (form=bounds, level=0.95, lower=62.4, lower_text=62.4, row=Total . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63.7 (62.4–65.1) 0.68, unit=percent, upper=65.1, upper_text=65.1); SE = 0.68 (level=0.95, row=Total . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63.7 (62.4–65.1) 0.68, unit=percent_points)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

 ● In 2022, 63.7% of adults age 65 and older had a dental visit in the past 12 months (Figure 1, 
Table 1).
 ● Men (62.3%) were less likely than women (64.9%) to have had a dental visit.
 ● The percentage of older adults who had a dental visit decreased from 65.4% among those 
ages 65–74 and 63.6% among those ages 75–84 to 53.3% among those age 85 and older.
Data table for Figure 1. Percentage of adults age 65 and older who had a dental visit in the past 
12 months, by sex, age group, and race and Hispanic origin: United States, 2022
Characteristic
Percent
(95% confidence interval) Standard error
Total . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63.7 (62.4–65.1) 0.68
Sex
Men . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 62.3 (60.5–64.2) 0.94
Women  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 64.9 (63.1–66.6) 0.88
Age group
65–74. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 65.4 (63.7–67.1) 0.86
75–84. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63.6 (61.4–65.7) 1.08
85 and older. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 53.3 (49.2–57.3) 2.02
```

**Response:**

```text
In 2022, about 64% of U.S. adults age 65 and older saw a dentist in the past year, with women slightly more likely to go than men (64.9% vs. 62.3%). Dental visits became less common with age, dropping from 65.4% among those ages 65–74 to 53.3% among those age 85 and older.
```

**C009 — Level (L0 / L1 / L2 / L3 / L4 / U):** L1

**C009 — Note:** The response gives only the rounded point estimate ("about 64%") with no CI, SE, or verbal uncertainty band for the Total row.

---

## C010

- **Estimate:** diabetes (12 and over) in Région de Lanaudière, Quebec, 2021/2022 (percent) — **8.9**
- **Qualifier family:** `interval` · **published forms:** CI (form=bounds, level=0.95, lower=7.2, lower_text=7.2, rows=['"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","Low 95% confidence interval, percent","Percent","239","units","0","v115551989","36.1.1.10.5","7.2","","","","1"', '"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","High 95% confidence interval, percent","Percent","239","units","0","v115551990","36.1.1.10.6","11.0","","","","1"'], unit=percent, upper=11.0, upper_text=11.0)
- **Mode:** direct · **Compression:** (n/a — direct mode)

**Prompt shown to the consumer:**

```text
﻿"REF_DATE","GEO","DGUID","Age group","Sex","Indicators","Characteristics","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Percent","Percent","239","units","0","v115551964","36.1.1.7.4","33.7","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Low 95% confidence interval, percent","Percent","239","units","0","v115551965","36.1.1.7.5","30.1","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","High 95% confidence interval, percent","Percent","239","units","0","v115551966","36.1.1.7.6","37.5","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Percent","Percent","239","units","0","v115551972","36.1.1.8.4","26.5","E","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Low 95% confidence interval, percent","Percent","239","units","0","v115551973","36.1.1.8.5","15.8","E","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","High 95% confidence interval, percent","Percent","239","units","0","v115551974","36.1.1.8.6","40.9","E","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Percent","Percent","239","units","0","v115551980","36.1.1.9.4","19.3","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Low 95% confidence interval, percent","Percent","239","units","0","v115551981","36.1.1.9.5","16.8","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","High 95% confidence interval, percent","Percent","239","units","0","v115551982","36.1.1.9.6","22.1","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","Percent","Percent","239","units","0","v115551988","36.1.1.10.4","8.9","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","Low 95% confidence interval, percent","Percent","239","units","0","v115551989","36.1.1.10.5","7.2","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","High 95% confidence interval, percent","Percent","239","units","0","v115551990","36.1.1.10.6","11.0","","","","1"
Symbol Legend
Description,Symbol
"not available for a specific reference period","..",
"less than the limit of detection","<LOD",
"value rounded to 0 (zero) where there is a meaningful distinction between true zero and the value that was rounded","0s",
"data quality: excellent","A",
"data quality: very good","B",
"data quality: good","C",
"data quality: acceptable","D",
"use with caution","E",
"too unreliable to be published","F",
"not applicable","...",
"preliminary","p",
"revised","r",
"suppressed to meet the confidentiality requirements of the Statistics Act","x",

What is the confidence interval on diabetes (12 and over) in Région de Lanaudière, Quebec, 2021/2022 (percent)?
```

**Response:**

```text
Based on the CSV data provided, the 95% confidence interval for diabetes prevalence among those 12 years and over in Région de Lanaudière, Quebec for 2021/2022 is:

**7.2% to 11.0%**

The point estimate is 8.9%, with a lower bound of 7.2% and an upper bound of 11.0%.
```

**C010 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C010 — Note:** none

---

## C011

- **Estimate:** the CV ceiling for Category 1 LFS estimates (no release restrictions) — **16.5**
- **Qualifier family:** `reliability` · **published forms:** RELIABILITY_FLAG = no release restrictions (polarity=reliable)
- **Mode:** direct · **Compression:** (n/a — direct mode)

**Prompt shown to the consumer:**

```text
**Guidelines on data reliability** Household surveys within Statistics Canada generally use the following guidelines and reliability categories in interpreting CV values for data accuracy and in the dissemination of statistical information. **Category 1** – If the CV is ≤ 16.5% – no release restrictions: data are of sufficient accuracy that no special warnings to users or other restrictions are required. **Category 2** – If the CV is > 16.5% and ≤ 33.3% – release with caveats: data are potentially useful for some purposes but should be accompanied by a warning to users regarding their accuracy. **Category 3** – If the CV > 33.3% – not recommended for release: data contain a level of error that makes them so potentially misleading that they should not be released in most circumstances. If users insist on inclusion of Category 3 data in a non-standard product, even after being advised of their accuracy, the data should be accompanied by a disclaimer. The user should acknowledge the warnings given and undertake not to disseminate, present or report the data, directly or indirectly, without this disclaimer.

What is the reliability assessment on the CV ceiling for Category 1 LFS estimates (no release restrictions)?
```

**Response:**

```text
**CV ≤ 16.5% → Category 1: no release restrictions.**

The reliability assessment at that ceiling is that the estimate is *of sufficient accuracy that no special warnings to users or other restrictions are required* — it can be disseminated as-is, with no caveat, footnote, or qualifier attached.

Two details on the boundary itself:

- **16.5% is inclusive.** An estimate with a CV of exactly 16.5% is still Category 1. The next category begins strictly above it (> 16.5% and ≤ 33.3% → release with caveats).
- **The ceiling is a dissemination rule, not a claim of negligible error.** A CV of 16.5% still means the standard error is roughly a sixth of the estimate — e.g. an estimate of 100,000 carries a standard error near 16,500, so a 95% interval spans roughly ±32,000. Category 1 asserts that this level of sampling error doesn't require warning the user, not that the estimate is precise in an absolute sense. Analytically, a Category 1 estimate can still be too imprecise to support a specific comparison (small month-to-month change, fine cross-tabulation), and that judgment sits with the analyst, not the category.
```

**C011 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C011 — Note:** none

---

## C012

- **Estimate:** the number of people employed full-time in agriculture, forestry and fishing in the UK in 2016 — **155,000**
- **Qualifier family:** `relative` · **published forms:** CV = 8 (unit=percent)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

The total turnover of plastering businesses in the UK was estimated at £2,322 million in 2016, with a standard error of £201 million. A different survey estimated that the total number of people employed full-time in agriculture, forestry and fishing in the UK was 155,000 in 2016, with a standard error of 12,400 employees It is difficult to compare these two standard errors. By calculating the coefficient of variation for each, the results show that both estimates have a similar level of precision: * £201 million divided by £2,322 million equals 0.087 – a coefficient of variation of 8.7% * 12,400 divided by 155,000 equals 0.08 – a coefficient of variation of 8%
```

**Response:**

```text
In 2016, UK plastering businesses turned over an estimated £2,322 million (give or take £201 million), while about 155,000 people worked full-time in agriculture, forestry and fishing (give or take 12,400) — figures whose margins of error can't be compared directly because one is in pounds and the other in people. Dividing each margin by its estimate puts both on the same scale as a percentage (8.7% and 8%), showing the two estimates are about equally reliable.
```

**C012 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C012 — Note:** CV of 8% is restated exactly and bound to the agriculture estimate by parallel order, but the class is described as "margin divided by estimate as a percentage" rather than named coefficient of variation, and the SE is mislabelled a margin of error.

---

## C013

- **Estimate:** B19013_001E for "Bannock County, Idaho" — **64080**
- **Qualifier family:** `interval` · **published forms:** MOE = 2470 (field=B19013_001M, level=0.9, unit=currency)
- **Mode:** indirect · **Compression:** none

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary.

[["NAME","B19013_001E","B19013_001M","state","county"],
["Ada County, Idaho","88907","1710","16","001"],
["Adams County, Idaho","59286","4144","16","003"],
["Bannock County, Idaho","64080","2470","16","005"],
["Bear Lake County, Idaho","67304","6987","16","007"],
["Benewah County, Idaho","56553","3912","16","009"],
```

**Response:**

```text
This is a slice of U.S. Census Bureau data — American Community Survey table **B19013, median household income** — for counties in Idaho (state FIPS code 16), listed alphabetically and cut off after the first five.

The columns mean:
- **NAME** — the county
- **B19013_001E** — the *estimate*: the median household income in dollars (half of households earn more, half less)
- **B19013_001M** — the *margin of error* on that estimate, in dollars (Census reports these at 90% confidence)
- **state / county** — FIPS geographic codes

In plain terms:

| County | Typical household income | Give or take |
|---|---|---|
| Ada | ~$88,900 | ±$1,700 |
| Adams | ~$59,300 | ±$4,100 |
| Bannock | ~$64,100 | ±$2,500 |
| Bear Lake | ~$67,300 | ±$7,000 |
| Benewah | ~$56,600 | ±$3,900 |

**The story:** Ada County — home to Boise, the state's population center — stands out, with a typical household bringing in roughly $89,000 a year, about 50% more than the lowest counties shown. The rural counties cluster in the $56,000–$67,000 range.

**One caveat worth keeping:** the margins of error scale with how few people were surveyed. Ada County's figure is tight (±2%), so you can take it at face value. Bear Lake County's is ±$7,000 (over 10%) — its "$67,304" really means "somewhere between about $60,000 and $74,000." So Bear Lake looking richer than Bannock is not a difference you should treat as real; the ranges overlap heavily. Comparisons among the small rural counties are much shakier than the headline numbers suggest.
```

**C013 — Level (L0 / L1 / L2 / L3 / L4 / U):** L3

**C013 — Note:** MOE restated as ±$2,500 (rounded from 2470) with 90% level and correct Bannock binding; rounding to hundreds is a legitimate transformation, not exact.

---

## C014

- **Estimate:** the number of never-married females living in Arlington County (2015 ACS 1-year) — **43,104**
- **Qualifier family:** `interval` · **published forms:** MOE = 2,642 (level=0.9, unit=count); SE = 1,606 (unit=count)
- **Mode:** indirect · **Compression:** none

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary.

The example below shows how to calculate the MOE and SE for the estimated number of never-married females living in the three Virginia counties/independent cities that border Washington, DC (Fairfax and Arlington counties, Alexandria City) from the 2015 ACS 1-year estimates. Table 8.1. Data for Example 1 From Three Virginia Counties/Independent Cities: 2015 Characteristic Estimate MOE Never-married females living in Fairfax County (Component 1) ................................. 135,173 ±3,860 Never-married females living in Arlington County (Component 2) ................................. 43,104 ±2,642 Never-married females living in Alexandria City (Component 3) .................................. 24,842 ±1,957 Source: U.S. Census Bureau, data.census.gov, Table B12001: “Sex by Marital Status for the Population 15 Years and Over.” 60 Understanding and Using American Community Survey Data 60 What All Data Users Need to Know U.S. Census Bureau The aggregate estimate is: Obtain MOEs of the component estimates: MOE (Fairfax) = ±3,860 MOE (Arlington) = ±2,642 MOE (Alexandria) = ±1,957 Using formula (1), calculate the MOE for the aggregate estimate: Thus, the derived estimate of the number of never-married females living in the three Virginia counties/independent cities that border Washington, DC, is 203,119, and the MOE for the estimate is ±5,070. The SE of this derived estimate can be calculated from the SEs of the component estimates as follows: 1. Calculate the SE of each component estimate from its MOE using: (2) SE (Fairfax) = 3,860 / 1.645 = 2,347 SE (Arlington) = 2,642 / 1.645 = 1,606 SE (Alexandria) = 1,957 / 1.645 = 1,190 2. Calculate the SE of the aggregate estimate: (3) With the three component estimates in this example, this becomes: To assess the reliability of this derived estimate, users may find it helpful to calculate the CV as follows: (4) Understanding and Using American Community Survey Data 61 What All Data Users Need to Know 61 U.S. Census Bureau This CV indicates that the sampling error of this estimate is very small relative to the estimate itself, so the number of never-married females residing in the Virginia tri-county area bordering Washington, DC, can be considered a very reliable estimate.
```

**Response:**

```text
## Adding Up Survey Estimates: A Worked Example

**The question:** How many never-married women live in the three Virginia communities that border Washington, DC — Fairfax County, Arlington County, and Alexandria City?

Because the American Community Survey (ACS) is a *sample* survey rather than a full count, every number it publishes is an estimate that comes with a stated range of uncertainty. That range is the **margin of error (MOE)**. Here are the 2015 ACS 1-year figures:

| Area | Estimate | Margin of error |
|---|---|---|
| Fairfax County | 135,173 | ±3,860 |
| Arlington County | 43,104 | ±2,642 |
| Alexandria City | 24,842 | ±1,957 |

*Source: U.S. Census Bureau, data.census.gov, Table B12001, "Sex by Marital Status for the Population 15 Years and Over."*

### Step 1: Add the estimates

135,173 + 43,104 + 24,842 = **203,119**

### Step 2: Combine the margins of error

Margins of error do **not** simply add up. If you added them (3,860 + 2,642 + 1,957 = 8,459), you would badly overstate the uncertainty, because the three areas' errors are independent and tend to partially cancel each other out. Instead, square each one, add the squares, and take the square root:

√(3,860² + 2,642² + 1,957²) = √25,709,613 ≈ **±5,070**

So the combined estimate is **203,119 ± 5,070** never-married women.

### Step 3: Convert to standard errors (optional)

The MOE is just a rescaled **standard error (SE)** — the ACS uses a 90 percent confidence level, so MOE = 1.645 × SE. Divide by 1.645 to go the other direction:

- Fairfax: 3,860 ÷ 1.645 = 2,347
- Arlington: 2,642 ÷ 1.645 = 1,606
- Alexandria: 1,957 ÷ 1.645 = 1,190

Combine them the same way — square, sum, square root:

√(2,347² + 1,606² + 1,190²) ≈ **3,083**

(Equivalently, 5,070 ÷ 1.645 ≈ 3,083.)

### Step 4: Judge how reliable the result is

A convenient reliability yardstick is the **coefficient of variation (CV)** — the standard error expressed as a percentage of the estimate:

CV = (3,083 ÷ 203,119) × 100 ≈ **1.5 percent**

### What this means

A CV of about 1.5 percent means the sampling error is very small relative to the size of the estimate. In plain terms: the survey's uncertainty amounts to roughly a percent and a half of the number itself. The figure of about 203,000 never-married women in the Virginia communities bordering Washington, DC, is a **highly reliable estimate**, and users can cite it with confidence.
```

**C014 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C014 — Note:** Arlington MOE ±2,642 restated in the table bound to the correct row, with the 90 percent confidence level stated explicitly in Step 3, and SE 1,606 also restated exactly.

---

## C015

- **Estimate:** the unemployment rate in Newfoundland and Labrador in January 2024 — **10.4**
- **Qualifier family:** `relative` · **published forms:** CV = 7.5 (unit=percent)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

For example, in January 2024, there were 28,000 unemployed persons in Newfoundland and Labrador and 275,900 participants in the labour force, giving an unemployment rate of 10.4%. Table 7.1 gives the CVs for the two counts as 5.0% and 2.5%, respectively. An approximation of the CV for the unemployment rate of 10.4% using the above formula would be: 5.0% + 2.5% = 7.5%
```

**Response:**

```text
In January 2024, Newfoundland and Labrador's 10.4% unemployment rate came from 28,000 unemployed and 275,900 in the labour force, with an estimated error measure of roughly 7.5%.
```

**C015 — Level (L0 / L1 / L2 / L3 / L4 / U):** L3

**C015 — Note:** CV value 7.5% is restated numerically and correctly but the class is genericized to "estimated error measure" (not named as CV/relative), which a lay reader could misread as a ±7.5% margin; binding to the 10.4% rate is loose but plausible.

---

## C016

- **Estimate:** the number of people aged 16 years and over in employment in the UK, July to September 2019 — **32.75**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = July to September 2019 (as_of=July to September 2019)
- **Mode:** indirect · **Compression:** none

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary.

Estimates for July to September 2019 show 32.75 million people aged 16 years and over in employment in the UK, with a confidence interval of plus or minus 177,000 people based on the results from a sample. If we took a large number of samples repeatedly, 95% of the confidence intervals would contain the unknown population estimate.
```

**Response:**

```text
Between July and September 2019, an estimated 32.75 million people aged 16 and over were in work in the UK.

That figure comes from a survey of a sample of people, not from counting everyone, so it carries some uncertainty. The margin of error is about 177,000 people either way — meaning the true number is likely somewhere between roughly 32.57 million and 32.93 million.

The "95%" part works like this: if you repeated the survey many times with different samples, about 95 out of every 100 ranges calculated this way would contain the true figure for the whole population. It's a statement about how reliable the method is over many repeats, not a claim that there's a 95% chance the true number sits in this particular range.
```

**C016 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C016 — Note:** none

---

## C017

- **Estimate:** overweight or obese youth (12 to 17, self-reported BMI) in Région de Lanaudière, Quebec, 2021/2022 (percent) — **26.5**
- **Qualifier family:** `interval` · **published forms:** CI (form=bounds, level=0.95, lower=15.8, lower_text=15.8, rows=['"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Low 95% confidence interval, percent","Percent","239","units","0","v115551973","36.1.1.8.5","15.8","E","","","1"', '"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","High 95% confidence interval, percent","Percent","239","units","0","v115551974","36.1.1.8.6","40.9","E","","","1"'], unit=percent, upper=40.9, upper_text=40.9)
- **Mode:** indirect · **Compression:** none

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary.

﻿"REF_DATE","GEO","DGUID","Age group","Sex","Indicators","Characteristics","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Percent","Percent","239","units","0","v115551964","36.1.1.7.4","33.7","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Low 95% confidence interval, percent","Percent","239","units","0","v115551965","36.1.1.7.5","30.1","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","High 95% confidence interval, percent","Percent","239","units","0","v115551966","36.1.1.7.6","37.5","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Percent","Percent","239","units","0","v115551972","36.1.1.8.4","26.5","E","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Low 95% confidence interval, percent","Percent","239","units","0","v115551973","36.1.1.8.5","15.8","E","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","High 95% confidence interval, percent","Percent","239","units","0","v115551974","36.1.1.8.6","40.9","E","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Percent","Percent","239","units","0","v115551980","36.1.1.9.4","19.3","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Low 95% confidence interval, percent","Percent","239","units","0","v115551981","36.1.1.9.5","16.8","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","High 95% confidence interval, percent","Percent","239","units","0","v115551982","36.1.1.9.6","22.1","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","Percent","Percent","239","units","0","v115551988","36.1.1.10.4","8.9","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","Low 95% confidence interval, percent","Percent","239","units","0","v115551989","36.1.1.10.5","7.2","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","High 95% confidence interval, percent","Percent","239","units","0","v115551990","36.1.1.10.6","11.0","","","","1"
Symbol Legend
Description,Symbol
"not available for a specific reference period","..",
"less than the limit of detection","<LOD",
"value rounded to 0 (zero) where there is a meaningful distinction between true zero and the value that was rounded","0s",
"data quality: excellent","A",
"data quality: very good","B",
"data quality: good","C",
"data quality: acceptable","D",
"use with caution","E",
"too unreliable to be published","F",
"not applicable","...",
"preliminary","p",
"revised","r",
"suppressed to meet the confidentiality requirements of the Statistics Act","x",
```

**Response:**

```text
## Health in the Lanaudière region of Quebec, 2021–2022

This is Statistics Canada survey data for one health region — Lanaudière, north of Montreal — covering residents aged 12 and over, men and women combined. Four findings:

**Adult obesity — about 34%.** Roughly one in three adults 18 and over was in the obese range based on height and weight they reported themselves (adjusted to correct for the well-known tendency to overstate height and understate weight). Because this comes from a sample rather than a census, the true figure is very likely somewhere between 30% and 38%.

**Youth overweight or obesity — about 27%.** Around one in four young people aged 12 to 17 was overweight or obese. This number is the shakiest of the set: Statistics Canada flags it "use with caution," and the plausible range runs from 16% all the way to 41% — too few young people were surveyed in this region to pin it down. Treat it as a rough signal, not a precise measurement.

**Arthritis — about 19%.** Nearly one in five residents 15 and over reported having arthritis (likely range: 17% to 22%).

**Diabetes — about 9%.** Roughly one in eleven residents reported diabetes (likely range: 7% to 11%).

**How to read the ranges.** Every figure here comes from asking a sample of people, not everyone. The "95% confidence interval" is the band within which the real regional figure almost certainly falls. Narrow bands (arthritis, diabetes) mean a solid estimate; the wide band on the youth figure means that one is genuinely uncertain.

**One caveat throughout:** these are self-reported answers, not measurements taken or diagnoses confirmed by a clinician.
```

**C017 — Level (L0 / L1 / L2 / L3 / L4 / U):** L3

**C017 — Note:** Bounds restated as 16% and 41% (source 15.8 and 40.9), a coarser rounding that is consistent with the source; binding to the youth estimate and the 95% level are both intact.

---

## C018

- **Estimate:** the illustrative month-to-month change in total employment (LFS guide example) — **60,000**
- **Qualifier family:** `interval` · **published forms:** CI = 35,000 to 85,000 (form=bounds, level=0.68, lower=35000, lower_text=35,000, upper=85000, upper_text=85,000, z=1.0)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

The lower and upper bounds of a 68% confidence interval can be computed by adding or subtracting one standard error (25,000) from 60,000. This means that there are approximately two chances in three (68%) that the range (35,000 to 85,000) contains the real value of the change between the two months. * A 95% confidence interval can be constructed by adding and subtracting 50,000 (two standard errors) from 60,000. This means that there are approximately nineteen chances in twenty (95%) that the range (10,000 to 110,000) contains the real value of the change between the two months. **Conducting hypothesis tests** Standard errors may also be used to perform hypothesis testing, a procedure that can be used for comparing population parameters using sample estimates. The larger the observed change between two estimates relative to its standard error, the better the chance that we are observing a real change as opposed to a change due to sampling variability. One simple way to conduct a hypothesis test is with a confidence interval. If the 95% confidence interval of an observed estimate of change does not contain zero, then the change is considered statistically significant at the 5% level of significance. The level of significance is the probability of concluding that there is a change, when in fact the actual change is zero. If the confidence interval of the estimate does contain zero, it is less likely to reflect a real change and more likely to be due to sampling variability. To illustrate, let us say that between two months, the published estimate for total employment increased by 60,000 and the associated standard error for the movement estimate was 25,000. Since the 95% confidence interval (10,000 to 110,000) does not contain zero, this change in employment is considered significant at the 5% level of significance.
```

**Response:**

```text
If employment rose by an estimated 60,000 between two months, the survey's margin of error means the true change is probably somewhere between 10,000 and 110,000 — with about a 19-in-20 chance of falling in that range. Because that range doesn't include zero, statisticians treat the increase as a real change rather than a fluke of sampling.
```

**C018 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C018 — Note:** Response restates the source's 95% CI (10,000–110,000, "19-in-20") exactly and bound to 60,000, but the record lists only the 68% form (35,000–85,000), so the match is to an unlisted published form, not a widening of the listed one.

---

## C019

- **Estimate:** the total turnover of the UK private education industry in 2016 — **42,649**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = In 2016 (as_of=2016)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

In 2016, the UK private education industry was estimated to have generated a total turnover of £42,649 million. The standard error for this estimate is £526.8 million. The 95% confidence interval around this estimate is calculated as: Margin of error = 1.96 × £526.8 million = £1,032.5 million The 95% confidence interval is therefore £42,649 million plus or minus £1,032.5 million, which equals £41,616 million and £43,682 million respectively. This means that if we drew 20 random samples and calculated an analogous confidence interval for each, on average, 19 out of 20 (95%) would contain the true population value and 1 in 20 (5%) would not. Therefore, there is a 95% chance that the true population value lies between £41,616 million and £43,682 million.
```

**Response:**

```text
In 2016, UK private education turnover was estimated at about £42.6 billion, with the true figure very likely falling between £41.6 billion and £43.7 billion.

(25 words. Note: the source's closing line — "there is a 95% chance the true value lies between…" — is the common misreading of a confidence interval; the preceding "19 in 20 samples" sentence is the correct statement, so I kept the wording hedged rather than reproducing the probability claim.)
```

**C019 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C019 — Note:** none

---

## C020

- **Estimate:** the global privacy-loss budget (epsilon) for the P.L. 94-171 redistricting data, housing units — **2.47**
- **Qualifier family:** `dp` · **published forms:** DP_NOISE = 0.07 (parameter=rho); DP_NOISE = 0.0000000001 (parameter=delta)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

Global Privacy-Loss Budget: Units Global rho . . . . . . . . . . . . . . . . . . 0.07 Global epsilon . . . . . . . . . . . . . . . 2.47 Delta . . . . . . . . . . . . . . . . . . . . . . . 10–10 Source: U.S. Census Bureau. Privacy-Loss Budget: Units Geographic level Rho allocation United States . . . . . . . . . . . . . . . 1/205 State . . . . . . . . . . . . . . . . . . . . . . . 1/205 County . . . . . . . . . . . . . . . . . . . . . 7/82 Tract . . . . . . . . . . . . . . . . . . . . . . . 364/1,025 Optimized block group1 . . . . . . 1,759/4,100 Block . . . . . . . . . . . . . . . . . . . . . . 99/820
```

**Response:**

```text
The Census Bureau capped total privacy loss for its Units data at epsilon 2.47, splitting that budget across geographic levels, with most going to tracts, block groups, and blocks.
```

**C020 — Level (L0 / L1 / L2 / L3 / L4 / U):** L1

**C020 — Note:** The response restates the epsilon estimate but neither rho (0.07) nor delta (10⁻¹⁰) appears in any form; the allocation clause loosely attributes the rho split to the epsilon budget but that is not a stated dp qualifier.

---

## C021

- **Estimate:** total turnover of private-provision education in the UK in 2016, in £ millions (Annual Business Survey) — **42,649**
- **Qualifier family:** `relative` · **published forms:** CV = 1 (unit=percent)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

Table 1: Total turnover estimates, standard error and relative standard error for education and water and waste management, UK, 2016 Total turnover in | Standard error in | Relative standard error (or coefficient of variation)2 ---|---|--£ millions1 | £ millions2 Industry 1: Education (private provision only) | 42,649 | 526.8 | 0.01 (or 1%) Industry 2: Water supply; sewerage, waste management and remediation activities | 34,677 | 222.7 | 0.01 (or 1%)
```

**Response:**

```text
In 2016, private education providers in the UK had total turnover of about £42.6 billion, while water supply, sewerage, waste management and remediation businesses had about £34.7 billion. Both estimates are precise, with a margin of error (standard error) of only about 1% of the total — roughly £527 million and £223 million respectively.
```

**C021 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C021 — Note:** CV value (1%) and binding preserved, but labelled "margin of error (standard error)" rather than relative standard error/CV; "of the total" recovers the relative meaning.

---

## C022

- **Estimate:** B19013_001E for "Boulder County, Colorado" — **102772**
- **Qualifier family:** `interval` · **published forms:** MOE = 2628 (field=B19013_001M, level=0.9, unit=currency)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

[["NAME","B19013_001E","B19013_001M","state","county"],
["Adams County, Colorado","91387","1470","08","001"],
["Alamosa County, Colorado","51445","6098","08","003"],
["Arapahoe County, Colorado","97215","1592","08","005"],
["Archuleta County, Colorado","76524","6714","08","007"],
["Baca County, Colorado","40380","7753","08","009"],
["Bent County, Colorado","49194","4596","08","011"],
["Boulder County, Colorado","102772","2628","08","013"],
```

**Response:**

```text
Median household incomes across these Colorado counties range from about $40,000 in rural Baca County to roughly $103,000 in Boulder County, based on Census survey estimates.
```

**C022 — Level (L0 / L1 / L2 / L3 / L4 / U):** L1

**C022 — Note:** Boulder's estimate is restated within rounding, but the MOE is absent; "roughly" reflects rounding and "based on Census survey estimates" is generic provenance, not a verbal uncertainty band for this interval.

---

## C023

- **Estimate:** the share of counties whose privacy-protected total population (2021-06-08 PPMF) is within the stated bound of their published 2010 total population — **90**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = PPMF vintage 2021-06-08 (as_of=2021-06-08)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

The latest PPMF vintage 2021-06-08 is the Production Settings run, which uses the same software and settings for the 2020 production run of the redistricting data. Users can compare tabulated values from the PPMFs to published 2010 data to identify the amount of uncertainty that can be expected for a given geography or characteristic. Users can also calculate new measures of the spread of the uncertainty. For example, comparing tabulations from the PPMFs with the published 2010 data will show that 90 percent of counties have a privacy-protected total population that is within ± four people of their published total population.
```

**Response:**

```text
The newest privacy-protected census test file mirrors the real 2020 settings, letting users gauge accuracy — 90 percent of counties land within four people of their published 2010 population.
```

**C023 — Level (L0 / L1 / L2 / L3 / L4 / U):** L2

**C023 — Note:** The as_of date 2021-06-08 is dropped; only the relative descriptor "newest" survives, which I treat as the verbal-band analogue for vintage, though the L2 definition is interval-shaped and fits vintage loosely.

---

## C024

- **Estimate:** the minimum estimate size for release, Ontario (LFS, thousands) — **1.5**
- **Qualifier family:** `reliability` · **published forms:** SUPPRESSION = suppresses estimates below
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

The LFS suppresses estimates below the levels presented in Table 7.4. Table 7.4 Minimum size for release, Canada, provinces and territories Table summaryThis table displays the results of Minimum size for release, Canada, provinces and territories Minimum size for release, calculated using thousands units of measure (appearing as column headers). Minimum size for release --thousands **Source:** Labour Force Survey (3701). Canada | **1.5** Newfoundland and Labrador | 0.5 Prince Edward Island | 0.2 Nova Scotia | 0.5 New Brunswick | 0.5 Quebec | 1.5 Ontario | 1.5 Manitoba | 0.5 Saskatchewan | 0.5 Alberta | 1.5 British Columbia | 1.5 Yukon | 0.2
```

**Response:**

```text
The Labour Force Survey doesn't publish estimates that fall below a minimum size threshold, which varies by region: 1,500 people for Canada overall and for Quebec, Ontario, Alberta, and British Columbia; 500 for Newfoundland and Labrador, Nova Scotia, New Brunswick, Manitoba, and Saskatchewan; and 200 for Prince Edward Island and Yukon. Any estimate smaller than its region's cutoff is suppressed rather than released.
```

**C024 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C024 — Note:** Suppression rule and Ontario's 1.5-thousand threshold both restated correctly; "thousands" was expanded to "1,500 people", an exact unit change rather than a value change.

---

## C025

- **Estimate:** the median CV above which an ACS 1-year detailed table is filtered out — **0.61**
- **Qualifier family:** `reliability` · **published forms:** SUPPRESSION = filtered out
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

For both base and collapsed detailed tables, a table is filtered out if the median CV value for the table is greater than 0.61, or in other words, if more than half of the estimates in it have a CV greater than 0.61, suggesting very low reliability. A CV greater than 0.61 is equivalent to saying the estimate is not significantly different from zero at the 90 percent confidence level. Zero estimates, which have an undefined CV, are assigned a CV of 1.0 for determining the median CV. Only lines at the lowest level of detail in a table are included in the calculation of the median CV.
```

**Response:**

```text
We drop a table from publication when most of its estimates are too shaky to trust — specifically, when over half the numbers at the most detailed level have a margin of error so wide that the estimate can't be told apart from zero (a coefficient of variation above 0.61, roughly the 90 percent confidence threshold).

This rule applies to both the base and collapsed detailed tables, and estimates of zero — which have no meaningful error measure — are counted as unreliable when we check whether the table clears the bar.
```

**C025 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C025 — Note:** none

---

## C026

- **Estimate:** total turnover of water supply, sewerage, waste management and remediation activities in the UK in 2016, in £ millions — **34,677**
- **Qualifier family:** `relative` · **published forms:** CV = 1 (unit=percent)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

Table 1: Total turnover estimates, standard error and relative standard error for education and water and waste management, UK, 2016 Total turnover in | Standard error in | Relative standard error (or coefficient of variation)2 ---|---|--£ millions1 | £ millions2 Industry 1: Education (private provision only) | 42,649 | 526.8 | 0.01 (or 1%) Industry 2: Water supply; sewerage, waste management and remediation activities | 34,677 | 222.7 | 0.01 (or 1%)
```

**Response:**

```text
In 2016, UK private education turnover was estimated at £42.6 billion and water and waste management at £34.7 billion, each accurate to within about 1%.
```

**C026 — Level (L0 / L1 / L2 / L3 / L4 / U):** L3

**C026 — Note:** CV of 1% is restated numerically and bound to the 34,677 estimate, but recast as an accuracy bound ("accurate to within about 1%") rather than a relative standard error, so the class is transformed and no confidence level is given.

---

## C027

- **Estimate:** the number of never-married females living in Arlington County (2015 ACS 1-year) — **43,104**
- **Qualifier family:** `interval` · **published forms:** MOE = 2,642 (level=0.9, unit=count); SE = 1,606 (unit=count)
- **Mode:** direct · **Compression:** (n/a — direct mode)

**Prompt shown to the consumer:**

```text
The example below shows how to calculate the MOE and SE for the estimated number of never-married females living in the three Virginia counties/independent cities that border Washington, DC (Fairfax and Arlington counties, Alexandria City) from the 2015 ACS 1-year estimates. Table 8.1. Data for Example 1 From Three Virginia Counties/Independent Cities: 2015 Characteristic Estimate MOE Never-married females living in Fairfax County (Component 1) ................................. 135,173 ±3,860 Never-married females living in Arlington County (Component 2) ................................. 43,104 ±2,642 Never-married females living in Alexandria City (Component 3) .................................. 24,842 ±1,957 Source: U.S. Census Bureau, data.census.gov, Table B12001: “Sex by Marital Status for the Population 15 Years and Over.” 60 Understanding and Using American Community Survey Data 60 What All Data Users Need to Know U.S. Census Bureau The aggregate estimate is: Obtain MOEs of the component estimates: MOE (Fairfax) = ±3,860 MOE (Arlington) = ±2,642 MOE (Alexandria) = ±1,957 Using formula (1), calculate the MOE for the aggregate estimate: Thus, the derived estimate of the number of never-married females living in the three Virginia counties/independent cities that border Washington, DC, is 203,119, and the MOE for the estimate is ±5,070. The SE of this derived estimate can be calculated from the SEs of the component estimates as follows: 1. Calculate the SE of each component estimate from its MOE using: (2) SE (Fairfax) = 3,860 / 1.645 = 2,347 SE (Arlington) = 2,642 / 1.645 = 1,606 SE (Alexandria) = 1,957 / 1.645 = 1,190 2. Calculate the SE of the aggregate estimate: (3) With the three component estimates in this example, this becomes: To assess the reliability of this derived estimate, users may find it helpful to calculate the CV as follows: (4) Understanding and Using American Community Survey Data 61 What All Data Users Need to Know 61 U.S. Census Bureau This CV indicates that the sampling error of this estimate is very small relative to the estimate itself, so the number of never-married females residing in the Virginia tri-county area bordering Washington, DC, can be considered a very reliable estimate.

What is the margin of error on the number of never-married females living in Arlington County (2015 ACS 1-year)?
```

**Response:**

```text
±2,642 — from Table 8.1, the 2015 ACS 1-year estimate of never-married females in Arlington County is 43,104 ±2,642. Its corresponding standard error is 2,642 / 1.645 ≈ 1,606.
```

**C027 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C027 — Note:** none

---

## C028

- **Estimate:** the number of Loudoun County, Virginia households with income of $15,000 to $24,999 in 2015 (Table DP03) — **3,497**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = from the 2015 ACS 1-year estimates (as_of=2015, period=1-year)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

Data.census.gov includes a collapsed income distribution within Demographic Profile DP03 that makes it possible to assess the difference in results from the approximation method illustrated above versus a direct estimation method that accounts for covariance between the component estimates of the subgroups. The relevant portion of this data.census.gov table, from the 2015 ACS 1-year estimates, is shown in Table 8.3 below. Table 8.3. Data From Demographic Profile DP03 for Loudoun County, Virginia: 2015 Household income category Subgroup # Estimate MOE SE CV $15,000 to $24,999 .... 1 3,497 ±1,037 630 18.0 $25,000 to $34,999 .... 2 3,537 ±973 591 16.7 $35,000 to $49,999 .... 3 7,270 ±1,554 945 13.0 Source: U.S. Census Bureau, data.census.gov, Table DP03: “Selected Economic Characteristics.” While the MOEs, SEs, and CVs for new Subgroup 1 and Subgroup 3 are almost identical to those derived from the approximation method, this is not the case for new Subgroup 2. The user-derived MOE is ±931 compared with the published MOE of ±973, and the derived CV is only 16.0 percent compared with a CV of 16.7 percent based on the published MOE for Subgroup 2.
```

**Response:**

```text
Census data for Loudoun County, Virginia shows the shortcut method for combining income groups slightly understates uncertainty, giving a margin of error of ±931 instead of ±973.
```

**C028 — Level (L0 / L1 / L2 / L3 / L4 / U):** L1

**C028 — Note:** The response never states the 2015 / 1-year vintage (nor the 3,497 estimate itself); it restates only the MOE comparison, so vintage is omitted rather than degraded.

---

## C029

- **Estimate:** the unemployment rate in Newfoundland and Labrador in January 2024 — **10.4**
- **Qualifier family:** `relative` · **published forms:** CV = 7.5 (unit=percent)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

For example, in January 2024, there were 28,000 unemployed persons in Newfoundland and Labrador and 275,900 participants in the labour force, giving an unemployment rate of 10.4%. Table 7.1 gives the CVs for the two counts as 5.0% and 2.5%, respectively. An approximation of the CV for the unemployment rate of 10.4% using the above formula would be: 5.0% + 2.5% = 7.5%
```

**Response:**

```text
In January 2024, Newfoundland and Labrador's unemployment rate was 10.4% — 28,000 unemployed people out of a labour force of 275,900 — but because these are survey estimates, each number carries some uncertainty: about 5.0% for the unemployed count and 2.5% for the labour force count. Adding those two figures gives a rough uncertainty of 7.5% for the unemployment rate itself.
```

**C029 — Level (L0 / L1 / L2 / L3 / L4 / U):** L3

**C029 — Note:** The 7.5 value is numeric and bound to the unemployment rate, but the class is degraded to a generic "rough uncertainty" rather than a CV/relative measure, which a general reader could misread as an absolute ±7.5 points.

---

## C030

- **Estimate:** the percentage of non-Hispanic Asian children aged 8–17 with elevated blood pressure, United States, 2013–2014 (NHANES; Table I) — **0.9**
- **Qualifier family:** `reliability` · **published forms:** SUPPRESSION = suppressed
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

Table I. Percentage of children aged 8–17 years with elevated and normal or borderline blood pressure, by race and Hispanic origin: United States, 2013–2014 Race and Hispanic origin and blood pressure Sample size Effective sample size 1 Percent estimate Standard error of percent Relative standard error 2 Lower bound 3 Upper bound 3 Absolute CI width 4 Relative CI width 5 Degrees of freedom Non-Hispanic white, elevated . . . . . . . . . . . . . . . . 460 8 583.0 0.5 0.29 58.0 0.1 1.6 1.6 320.0 15 Non-Hispanic white, normal or borderline . . . . . . . 460 8 583.0 99.5 0.29 0.3 98.4 99.9 1.6 1.6 15 Non-Hispanic black, elevated . . . . . . . . . . . . . . . . 447 145.3 6 2.0 1.17 58.5 0.3 6.4 6.1 305.0 13 Non-Hispanic black, normal or borderline . . . . . . . 447 145.3 7 98.0 1.17 1.2 93.6 99.7 6.1 6.2 13 Non-Hispanic Asian, elevated . . . . . . . . . . . . . . . . 164 124.8 6 0.9 0.83 92.2 0.0 5.1 5.1 566.7 13 Non-Hispanic Asian, normal or borderline . . . . . . . 164 124.8 7 99.1 0.83 0.8 94.9 100.0 5.1 5.2 13 Hispanic, elevated . . . . . . . . . 589 8 946.8 2.5 0.51 20.4 1.4 4.1 2.7 108.0 15 Hispanic, normal or borderline . . . . . . . . . . . . . . . 589 8 946.8 97.5 0.51 0.5 95.9 98.6 2.7 2.8 15 1 Sample size divided by the design effect. It is calculated in this table using this formula: . 2 Standard error divided by the estimated percent multiplied by 100%. 3 Lower and upper confidence bounds were computed using the Korn-Graubard method. 4 Difference between the upper and lower confidence bounds. 5 Absolute width divided by the estimated percent multiplied by 100%. 6 Relative CI width is greater than 130%. Estimate would be suppressed. 7 Estimate would have a footnote indicating its complement is suppressed. 8 Effective sample size is greater than sample size. Sample size used in CI calculations. NOTES: CI is confidence interval. Percent estimate and its lower and upper confidence bounds are equal to the proportion estimate and its lower and upper confidence bounds, respectively, multiplied by 100. Standard error of percent and absolute CI width are expressed in percentage points. Numbers in the table are subject to rounding. SOURCE: NCHS, National Health and Nutrition Examination Survey. Series 2, No. 175  Page 9 points, so the relative CI width should be examined. ● Relative CI widths for elevated high blood pressure for non-Hispanic black and non-Hispanic Asian children are greater than 130%, so these estimates would be suppressed. ● The number of events is greater than 0 (and not equal to the denominator) and there are more than 8 degrees of freedom for all estimates, so estimates that have met all other sample size and CI criteria would be presented. ● If the outcome of interest is the complement (normal or borderline high blood pressure), the absolute CI widths are the same. However, the relative CI widths for nonHispanic black and non-Hispanic Asian children are less than 130%, so these estimates would be presented with a note indicating that their complements do not meet presentation standards. ● Estimates of elevated blood pressure for non-Hispanic white children would be presented using the NCHS Data Presentation Standards for Proportions but would have been suppressed or identified as unreliable based on the RSE > 30% criterion.
```

**Response:**

```text
In 2013–2014, few U.S. children aged 8–17 had elevated blood pressure, but estimates for Black and Asian children were too imprecise to report reliably.
```

**C030 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C030 — Note:** Suppression is paraphrased as "too imprecise to report reliably," correctly bound to Asian children, and the 0.9 estimate is not restated as usable.

---

## C031

- **Estimate:** the prevalence of low HDL-C in adults age 20 and older during August 2021–August 2023 (crude) — **13.8**
- **Qualifier family:** `interval` · **published forms:** CI (form=bounds, level=0.95, lower=12.1, lower_text=12.1, row=20 and older (crude)  . . . . . . . . . . . . . . . 5,498 13.8 (12.1–15.7) 0.8, unit=percent, upper=15.7, upper_text=15.7); SE = 0.8 (level=0.95, row=20 and older (crude)  . . . . . . . . . . . . . . . 5,498 13.8 (12.1–15.7) 0.8, unit=percent_points)
- **Mode:** indirect · **Compression:** none

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary.

During August 2021–August 2023, the prevalence of low HDL-C was 13.8% in adults and was 
higher in men (21.5%) than in women (6.6%), overall and within each age group  
(Figure 2, Table 2).
Data table for Figure 2. Prevalence of low high-density lipoprotein cholesterol in adults age 20 
and older, by sex and age group: United States, August 2021–August 2023
Sex and age group Sample size
Percent 
 (95% confidence interval) Standard error
Total
20 and older (age adjusted). . . . . . . . . . 5,498 14.2 (12.5–15.9) 0.9
20 and older (crude)  . . . . . . . . . . . . . . . 5,498 13.8 (12.1–15.7) 0.8
20–39 . . . . . . . . . . . . . . . . . . . . . . . . . 1,383 16.2 (12.7–20.1) 1.7
40–59 . . . . . . . . . . . . . . . . . . . . . . . . . 1,598 13.8 (11.6–16.3) 1.1
60 and older . . . . . . . . . . . . . . . . . . . . 2,517 11.2 (10.0–12.5) 0.5
Men
20 and older (age adjusted). . . . . . . . . . 2,481 21.8 (19.1–24.7) 1.5
20 and older (crude)  . . . . . . . . . . . . . . . 2,481 21.5 (18.6–24.6) 1.4
20–39 . . . . . . . . . . . . . . . . . . . . . . . . . 598 25.1 (19.3–31.6) 2.8
40–59 . . . . . . . . . . . . . . . . . . . . . . . . . 706 20.8 (17.3–24.8) 1.7
60 and older . . . . . . . . . . . . . . . . . . . . 1,177 17.9 (15.7–20.2) 1.0
Women
20 and older (age adjusted). . . . . . . . . . 3,017 6.8 (5.6–8.2) 0.7
20 and older (crude)  . . . . . . . . . . . . . . . 3,017 6.6 (5.4–8.0) 0.6
20–39 . . . . . . . . . . . . . . . . . . . . . . . . . 785 7.6 (5.4–10.3) 1.1
40–59 . . . . . . . . . . . . . . . . . . . . . . . . . 892 7.0 (5.4–8.9) 0.7
60 and older . . . . . . . . . . . . . . . . . . . . 1,340 5.2 (4.1–6.5) 0.4
```

**Response:**

```text
## Plain-language summary

**Low "good" cholesterol in U.S. adults, August 2021–August 2023**

HDL cholesterol is the "good" kind — it helps clear other cholesterol out of the bloodstream, so having too little of it is a heart-disease risk factor. During this period, about **1 in 7 U.S. adults age 20 and older (13.8%) had low HDL cholesterol.**

**Men were affected about three times as often as women:** 21.5% of men versus 6.6% of women. That gap held at every age.

**Low HDL was most common in younger adults and least common in older ones:**

| Age group | All adults | Men | Women |
|---|---|---|---|
| 20–39 | 16.2% | 25.1% | 7.6% |
| 40–59 | 13.8% | 20.8% | 7.0% |
| 60 and older | 11.2% | 17.9% | 5.2% |

So roughly a quarter of men in their 20s and 30s had low HDL, compared with fewer than 1 in 12 women the same age.

**About the numbers:** These come from a national health survey of 5,498 adults, so they are estimates for the whole country rather than exact counts. Each figure carries a margin of error — for example, the overall 13.8% could reasonably fall anywhere between about 12.1% and 15.7%. The estimates for older adults are based on larger samples and are therefore more precise than those for the youngest group.

One technical note: the brief reports both "crude" percentages (the actual share of adults surveyed) and "age-adjusted" ones (14.2% overall), which mathematically remove the effect of the population's age mix so that comparisons across groups or over time aren't skewed by one group simply being older.
```

**C031 — Level (L0 / L1 / L2 / L3 / L4 / U):** L3

**C031 — Note:** Bounds 12.1–15.7 restated correctly and bound to the 13.8% overall estimate, but the 95% confidence level is omitted (v0 L3 allowance).

---

## C032

- **Estimate:** the number of one-person households in Colorado in 2015 (2015 ACS 1-year estimate) — **564,757**
- **Qualifier family:** `interval` · **published forms:** MOE = 10,127 (level=0.9, unit=count)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

A margin of error (MOE) describes the precision of an ACS estimate at a given level of confidence. The confidence level associated with the MOE indicates the likelihood that the ACS sample estimate is within a certain range (the MOE) of the population value. The MOEs for published ACS estimates are provided at a 90 percent confidence level. From these MOEs, data users can easily calculate 90 percent confidence intervals that define a range expected to contain the true or population value of an estimate 90 percent of the time. For example, in the Data Profile for Selected Social Characteristics (Table DP02) for Colorado, a portion of which is shown in Figure 7.1, data from the 2015 ACS 1-year estimates indicate that there were 564,757 one-person households in the state in 2015 with an MOE of 10,127. By adding and subtracting the MOE from the point estimate, we can calculate the 90 percent confidence interval for that estimate: 564,757 – 10,127 = 554,630 = Lower bound of the interval 564,757 + 10,127 = 574,884 = Upper bound of the interval 56 U.S. Census Bureau, American Community Survey, Sample Size and Data Quality, <www.census.gov/acs/www/methodology/sample-size -and-data-quality/>. 54 Understanding and Using American Community Survey Data 54 What All Data Users Need to Know U.S. Census Bureau 564,757 – 10,127 = 554,630 = Lower bound of the interval 564,757 + 10,127 = 574,884 = Upper bound of the interval Source: U.S. Census Bureau, data.census.gov, Table DP02: “Selected Social Characteristics in the United States.” Figure 7.1. Sample Estimates and Margins of Error in Data.census.gov: 2015 Therefore, we can be 90 percent confident that the true number of one-person households in Colorado in 2015 falls somewhere between 554,630 and 574,884. Put another way, if the ACS were independently conducted 100 times in 2015, sampling theory suggests that 90 times the estimate of one-person households in Colorado would fall in the given confidence interval. Estimates with smaller MOEs—relative to the value of the estimate—will have narrower confidence intervals indicating that the estimate is more precise and has less sampling error associated with it. TIP: When constructing confidence intervals from MOEs, data users should be aware of any “natural” limits on the upper and lower bounds. For example, if a population estimate is near zero, the calculated value of the lower confidence bound may be less than zero. However, a negative number of people does not make sense, so the lower confidence bound should be reported as zero instead. For other estimates, such as income, negative values may be valid. Another natural limit would be 100 percent for the upper confidence bound of a percent estimate. Data users should always keep the context and meaning of an estimate in mind when creating and interpreting confidence intervals. Standard Errors and Coefficients of Variation A standard error (SE) measures the variability of an estimate due to sampling and provides the basis for calculating the MOE. The SE provides a quantitative measure of the extent to which an estimate derived from a sample can be expected to deviate from the value for the full population. SEs are needed to calculate coefficients of Understanding and Using American Community Survey Data 55 What All Data Users Need to Know 55 U.S. Census Bureau variation and to conduct tests of statistical significance. Data users can easily calculate the SE of an ACS estimate by dividing the positive value of its MOE by 1.645 as shown below:57 (1) Using the data in Table 7.1, the SE for the number of one-person households in Colorado in 2015 would be: The SE for an estimate depends on the underlying variability in the population for that characteristic and the sample size used for the survey. In general, the larger the sample size, the smaller the SE of the estimates produced from the sample data. This relationship between sample size and SE is the reason that ACS estimates for less populous areas are only published using multiple years of data. Combining data from multiple ACS 1-year files increases sample size and helps to reduce SEs. Coefficients of variation are another useful measure of sampling error. A coefficient of variation (CV) measures the relative amount of sampling error that is associated with a sample estimate. The CV is calculated as the ratio of the SE for an estimate to the estimate itself and is usually expressed as a percent: (2) A small CV indicates that the SE is small relative to the estimate, and a data user can be more confident that the estimate is close to the population value. The CV is also an indicator of the reliability of an estimate. When the SE of an estimate is close to the value of the estimate, the CV will be larger, indicating that the estimate has a large amount of sampling error associated with it and is not very reliable. For the example of one-person households in Colorado, the CV would be calculated as: 58 A CV of 1.1 percent indicates that the ACS estimate of one-person households in Colorado has a relatively small amount of sampling error and is quite reliable. Data users often find it easier to interpret and compare CVs across a series of ACS estimates than to interpret and compare SEs.
```

**Response:**

```text
A margin of error tells you how precise a Census Bureau ACS estimate is: the Bureau publishes MOEs at a 90 percent confidence level, so adding and subtracting the MOE from an estimate gives a range that should contain the true population value 90 percent of the time — for example, Colorado's 2015 estimate of 564,757 one-person households (MOE 10,127) means the real number was likely between 554,630 and 574,884. Related measures derived from the MOE, the standard error and the coefficient of variation, indicate how much sampling error an estimate carries, with smaller values signaling a more reliable estimate.
```

**C032 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C032 — Note:** none

---

## C033

- **Estimate:** the prevalence of low HDL-C in women age 20 and older during August 2021–August 2023 (crude) — **6.6**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = August 2021–August 2023 (as_of=August 2021–August 2023)
- **Mode:** indirect · **Compression:** none

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary.

During August 2021–August 2023, the prevalence of low HDL-C was 13.8% in adults and was 
higher in men (21.5%) than in women (6.6%), overall and within each age group  
(Figure 2, Table 2).
Data table for Figure 2. Prevalence of low high-density lipoprotein cholesterol in adults age 20 
and older, by sex and age group: United States, August 2021–August 2023
Sex and age group Sample size
Percent 
 (95% confidence interval) Standard error
Total
20 and older (age adjusted). . . . . . . . . . 5,498 14.2 (12.5–15.9) 0.9
20 and older (crude)  . . . . . . . . . . . . . . . 5,498 13.8 (12.1–15.7) 0.8
20–39 . . . . . . . . . . . . . . . . . . . . . . . . . 1,383 16.2 (12.7–20.1) 1.7
40–59 . . . . . . . . . . . . . . . . . . . . . . . . . 1,598 13.8 (11.6–16.3) 1.1
60 and older . . . . . . . . . . . . . . . . . . . . 2,517 11.2 (10.0–12.5) 0.5
Men
20 and older (age adjusted). . . . . . . . . . 2,481 21.8 (19.1–24.7) 1.5
20 and older (crude)  . . . . . . . . . . . . . . . 2,481 21.5 (18.6–24.6) 1.4
20–39 . . . . . . . . . . . . . . . . . . . . . . . . . 598 25.1 (19.3–31.6) 2.8
40–59 . . . . . . . . . . . . . . . . . . . . . . . . . 706 20.8 (17.3–24.8) 1.7
60 and older . . . . . . . . . . . . . . . . . . . . 1,177 17.9 (15.7–20.2) 1.0
Women
20 and older (age adjusted). . . . . . . . . . 3,017 6.8 (5.6–8.2) 0.7
20 and older (crude)  . . . . . . . . . . . . . . . 3,017 6.6 (5.4–8.0) 0.6
20–39 . . . . . . . . . . . . . . . . . . . . . . . . . 785 7.6 (5.4–10.3) 1.1
40–59 . . . . . . . . . . . . . . . . . . . . . . . . . 892 7.0 (5.4–8.9) 0.7
60 and older . . . . . . . . . . . . . . . . . . . . 1,340 5.2 (4.1–6.5) 0.4
```

**Response:**

```text
# Low HDL Cholesterol in American Adults: Key Findings

Between August 2021 and August 2023, roughly **1 in 7 American adults** (13.8%) had low levels of "good" cholesterol (HDL cholesterol). This is a known risk factor for heart disease.

## Key Patterns

**Men are hit harder than women:** About **1 in 5 men** (21.5%) had low HDL, compared to about **1 in 15 women** (6.6%) — more than triple the rate.

**Age matters, but differently for men and women:**
- **Ages 20–39:** Men had the highest prevalence (25%), while younger women were close behind (7.6%)
- **Ages 40–59:** The gender gap stayed wide (men at 20.8%, women at 7%)
- **Ages 60+:** The rate dropped for both groups (men 17.9%, women 5.2%), though men still had roughly 3.5 times the rate of women

This data comes from a representative sample of over 5,400 American adults and suggests that low HDL is a widespread concern, particularly for men across all age groups.
```

**C033 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C033 — Note:** none

---

## C034

- **Estimate:** the number of never-married females living in Fairfax County (2015 ACS 1-year) — **135,173**
- **Qualifier family:** `interval` · **published forms:** SE = 2,347 (unit=count); MOE = 3,860 (level=0.9, unit=count)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

The example below shows how to calculate the MOE and SE for the estimated number of never-married females living in the three Virginia counties/independent cities that border Washington, DC (Fairfax and Arlington counties, Alexandria City) from the 2015 ACS 1-year estimates. Table 8.1. Data for Example 1 From Three Virginia Counties/Independent Cities: 2015 Characteristic Estimate MOE Never-married females living in Fairfax County (Component 1) ................................. 135,173 ±3,860 Never-married females living in Arlington County (Component 2) ................................. 43,104 ±2,642 Never-married females living in Alexandria City (Component 3) .................................. 24,842 ±1,957 Source: U.S. Census Bureau, data.census.gov, Table B12001: “Sex by Marital Status for the Population 15 Years and Over.” 60 Understanding and Using American Community Survey Data 60 What All Data Users Need to Know U.S. Census Bureau The aggregate estimate is: Obtain MOEs of the component estimates: MOE (Fairfax) = ±3,860 MOE (Arlington) = ±2,642 MOE (Alexandria) = ±1,957 Using formula (1), calculate the MOE for the aggregate estimate: Thus, the derived estimate of the number of never-married females living in the three Virginia counties/independent cities that border Washington, DC, is 203,119, and the MOE for the estimate is ±5,070. The SE of this derived estimate can be calculated from the SEs of the component estimates as follows: 1. Calculate the SE of each component estimate from its MOE using: (2) SE (Fairfax) = 3,860 / 1.645 = 2,347 SE (Arlington) = 2,642 / 1.645 = 1,606 SE (Alexandria) = 1,957 / 1.645 = 1,190 2. Calculate the SE of the aggregate estimate: (3) With the three component estimates in this example, this becomes: To assess the reliability of this derived estimate, users may find it helpful to calculate the CV as follows: (4) Understanding and Using American Community Survey Data 61 What All Data Users Need to Know 61 U.S. Census Bureau This CV indicates that the sampling error of this estimate is very small relative to the estimate itself, so the number of never-married females residing in the Virginia tri-county area bordering Washington, DC, can be considered a very reliable estimate.
```

**Response:**

```text
A Census Bureau example adds never-married female counts from three Virginia areas near Washington, DC, reaching 203,119, and shows how to confirm the combined total is highly reliable.
```

**C034 — Level (L0 / L1 / L2 / L3 / L4 / U):** L1

**C034 — Note:** The response never restates the Fairfax estimate (135,173) or any of its MOE/SE; the only reliability language is a verbal claim about the aggregate total (203,119), not the Fairfax row.

---

## C035

- **Estimate:** total turnover of private-provision education in the UK in 2016, in £ millions (Annual Business Survey) — **42,649**
- **Qualifier family:** `relative` · **published forms:** CV = 1 (unit=percent)
- **Mode:** indirect · **Compression:** none

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary.

Table 1: Total turnover estimates, standard error and relative standard error for education and water and waste management, UK, 2016 Total turnover in | Standard error in | Relative standard error (or coefficient of variation)2 ---|---|--£ millions1 | £ millions2 Industry 1: Education (private provision only) | 42,649 | 526.8 | 0.01 (or 1%) Industry 2: Water supply; sewerage, waste management and remediation activities | 34,677 | 222.7 | 0.01 (or 1%)
```

**Response:**

```text
**Table 1: How much money two UK industries took in during 2016 — and how confident we are in those figures**

| Industry | Total turnover (£ millions) | Standard error (£ millions) | Relative standard error |
|---|---|---|---|
| Education (private providers only) | 42,649 | 526.8 | 0.01 (1%) |
| Water supply; sewerage, waste management and remediation | 34,677 | 222.7 | 0.01 (1%) |

**In plain terms**

These numbers come from a survey rather than a count of every business, so each total is an estimate. The extra columns say how precise that estimate is.

- **Private education providers** took in about **£42.6 billion** in 2016.
- **Water, sewerage and waste companies** took in about **£34.7 billion**.

The **standard error** is the typical amount an estimate like this would wobble by if the survey were run again with a different sample of businesses — roughly £527 million for education and £223 million for water and waste. The **relative standard error** simply expresses that wobble as a share of the total. For both industries it is about **1%**, meaning the estimates are considered reliable: the true figure is very likely close to the number shown.

(Note: your source text labels both money columns with the same footnote-mangled heading; the second column is the standard error in £ millions, not a separate turnover figure.)
```

**C035 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C035 — Note:** none

---

## C036

- **Estimate:** B19013_001E for "Boulder County, Colorado" — **102772**
- **Qualifier family:** `interval` · **published forms:** MOE = 2628 (field=B19013_001M, level=0.9, unit=currency)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

[["NAME","B19013_001E","B19013_001M","state","county"],
["Adams County, Colorado","91387","1470","08","001"],
["Alamosa County, Colorado","51445","6098","08","003"],
["Arapahoe County, Colorado","97215","1592","08","005"],
["Archuleta County, Colorado","76524","6714","08","007"],
["Baca County, Colorado","40380","7753","08","009"],
["Bent County, Colorado","49194","4596","08","011"],
["Boulder County, Colorado","102772","2628","08","013"],
```

**Response:**

```text
This is Census ACS data (table B19013) showing median household income and its margin of error for Colorado counties:

Across these Colorado counties, typical household income varies widely — from about $40,000 a year in Baca County to roughly $103,000 in Boulder County, with Denver-area counties like Adams and Arapahoe near $91,000–$97,000. The figures are survey estimates, so each carries a margin of error that is small in populous counties (±$1,500 or so) but much larger in sparsely populated rural ones (±$6,000–$7,800), meaning the rural numbers should be read as rough ranges rather than exact values.
```

**C036 — Level (L0 / L1 / L2 / L3 / L4 / U):** L2

**C036 — Note:** Boulder's MOE is only covered verbally ("small in populous counties"); the ±$1,500 figure is bound to Adams/Arapahoe-scale values, and if read as applying to Boulder it would be narrowed (2628→~1500), i.e. L0.

---

## C037

- **Estimate:** the percentage of adults age 85 and older who had a dental visit in the past 12 months in 2022 — **53.3**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = 2022 (as_of=2022)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

 ● In 2022, 63.7% of adults age 65 and older had a dental visit in the past 12 months (Figure 1, 
Table 1).
 ● Men (62.3%) were less likely than women (64.9%) to have had a dental visit.
 ● The percentage of older adults who had a dental visit decreased from 65.4% among those 
ages 65–74 and 63.6% among those ages 75–84 to 53.3% among those age 85 and older.
Data table for Figure 1. Percentage of adults age 65 and older who had a dental visit in the past 
12 months, by sex, age group, and race and Hispanic origin: United States, 2022
Characteristic
Percent
(95% confidence interval) Standard error
Total . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63.7 (62.4–65.1) 0.68
Sex
Men . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 62.3 (60.5–64.2) 0.94
Women  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 64.9 (63.1–66.6) 0.88
Age group
65–74. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 65.4 (63.7–67.1) 0.86
75–84. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63.6 (61.4–65.7) 1.08
85 and older. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 53.3 (49.2–57.3) 2.02
```

**Response:**

```text
In 2022, about 64% of U.S. adults 65 and older saw a dentist in the past year, with women slightly more likely than men and rates dropping sharply after 85.
```

**C037 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C037 — Note:** "In 2022" binds to the whole sentence including the 85+ drop, but the 53.3 estimate itself is only referenced verbally ("dropping sharply after 85"), not restated numerically.

---

## C038

- **Estimate:** the total turnover of plastering businesses in the UK in 2016 — **2,322**
- **Qualifier family:** `relative` · **published forms:** CV = 8.7 (unit=percent)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

The total turnover of plastering businesses in the UK was estimated at £2,322 million in 2016, with a standard error of £201 million. A different survey estimated that the total number of people employed full-time in agriculture, forestry and fishing in the UK was 155,000 in 2016, with a standard error of 12,400 employees It is difficult to compare these two standard errors. By calculating the coefficient of variation for each, the results show that both estimates have a similar level of precision: * £201 million divided by £2,322 million equals 0.087 – a coefficient of variation of 8.7% * 12,400 divided by 155,000 equals 0.08 – a coefficient of variation of 8%
```

**Response:**

```text
Two very different UK statistics — plastering industry turnover and farming employment — turn out to be about equally reliable, since each estimate's uncertainty is roughly 8% of its size.
```

**C038 — Level (L0 / L1 / L2 / L3 / L4 / U):** L0

**C038 — Note:** The plastering CV of 8.7% is restated as "roughly 8%" jointly bound to both estimates, which is the agriculture CV and falls outside 8.7's published rounding (narrowed); the hedge "roughly" makes it borderline with L3.

---

## C039

- **Estimate:** diabetes (12 and over) in Prince Edward Island, 2022 (percent) — **8.9**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = 2022 (as_of=2022)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

﻿"REF_DATE","GEO","DGUID","Age group","Sex","Indicators","Characteristics","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Percent","Percent","239","units","0","v110794140","3.1.1.7.4","36.4","","","","1"
"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Low 95% confidence interval, percent","Percent","239","units","0","v110794141","3.1.1.7.5","30.0","","","","1"
"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","High 95% confidence interval, percent","Percent","239","units","0","v110794142","3.1.1.7.6","43.2","","","","1"
"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Percent","Percent","239","units","0","v110794147","3.1.1.8.4","32.1","E","","","1"
"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Low 95% confidence interval, percent","Percent","239","units","0","v110794148","3.1.1.8.5","21.2","E","","","1"
"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","High 95% confidence interval, percent","Percent","239","units","0","v110794149","3.1.1.8.6","45.4","E","","","1"
"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Percent","Percent","239","units","0","v110794154","3.1.1.9.4","18.6","","","","1"
"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Low 95% confidence interval, percent","Percent","239","units","0","v110794155","3.1.1.9.5","14.9","","","","1"
"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","High 95% confidence interval, percent","Percent","239","units","0","v110794156","3.1.1.9.6","22.9","","","","1"
"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Diabetes","Percent","Percent","239","units","0","v110794161","3.1.1.10.4","8.9","","","","1"
"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Diabetes","Low 95% confidence interval, percent","Percent","239","units","0","v110794162","3.1.1.10.5","6.2","","","","1"
"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Diabetes","High 95% confidence interval, percent","Percent","239","units","0","v110794163","3.1.1.10.6","12.6","","","","1"
Symbol Legend
Description,Symbol
"not available for a specific reference period","..",
"less than the limit of detection","<LOD",
"value rounded to 0 (zero) where there is a meaningful distinction between true zero and the value that was rounded","0s",
"data quality: excellent","A",
"data quality: very good","B",
"data quality: good","C",
"data quality: acceptable","D",
"use with caution","E",
"too unreliable to be published","F",
"not applicable","...",
"preliminary","p",
"revised","r",
"suppressed to meet the confidentiality requirements of the Statistics Act","x",
```

**Response:**

```text
In 2022, Statistics Canada estimated that in Prince Edward Island 36.4% of adults were obese, 32.1% of youth overweight or obese, 18.6% had arthritis, and 8.9% diabetes.
```

**C039 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C039 — Note:** none

---

## C040

- **Estimate:** the global privacy-loss budget (epsilon) for the P.L. 94-171 redistricting data, housing units — **2.47**
- **Qualifier family:** `dp` · **published forms:** DP_NOISE = 0.07 (parameter=rho); DP_NOISE = 0.0000000001 (parameter=delta)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

Global Privacy-Loss Budget: Units Global rho . . . . . . . . . . . . . . . . . . 0.07 Global epsilon . . . . . . . . . . . . . . . 2.47 Delta . . . . . . . . . . . . . . . . . . . . . . . 10–10 Source: U.S. Census Bureau. Privacy-Loss Budget: Units Geographic level Rho allocation United States . . . . . . . . . . . . . . . 1/205 State . . . . . . . . . . . . . . . . . . . . . . . 1/205 County . . . . . . . . . . . . . . . . . . . . . 7/82 Tract . . . . . . . . . . . . . . . . . . . . . . . 364/1,025 Optimized block group1 . . . . . . 1,759/4,100 Block . . . . . . . . . . . . . . . . . . . . . . 99/820
```

**Response:**

```text
To protect confidentiality, the Census Bureau spent a fixed, deliberately small amount of "privacy loss" on its unit-level statistics — a global budget of rho = 0.07 (roughly epsilon = 2.47 at delta = 10⁻¹⁰), meaning the published numbers carry enough statistical noise that no individual record can be reliably identified. That budget was divided across geographic levels, with the great majority going to mid-sized areas — about 43% to block groups and 36% to tracts — followed by blocks (12%) and counties (9%), and only about half a percent each to the state and national totals.
```

**C040 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C040 — Note:** none

---

## C041

- **Estimate:** the number of never-married females living in Arlington County (2015 ACS 1-year) — **43,104**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = 2015 ACS 1-year estimates (as_of=2015, period=1-year)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

The example below shows how to calculate the MOE and SE for the estimated number of never-married females living in the three Virginia counties/independent cities that border Washington, DC (Fairfax and Arlington counties, Alexandria City) from the 2015 ACS 1-year estimates. Table 8.1. Data for Example 1 From Three Virginia Counties/Independent Cities: 2015 Characteristic Estimate MOE Never-married females living in Fairfax County (Component 1) ................................. 135,173 ±3,860 Never-married females living in Arlington County (Component 2) ................................. 43,104 ±2,642 Never-married females living in Alexandria City (Component 3) .................................. 24,842 ±1,957 Source: U.S. Census Bureau, data.census.gov, Table B12001: “Sex by Marital Status for the Population 15 Years and Over.” 60 Understanding and Using American Community Survey Data 60 What All Data Users Need to Know U.S. Census Bureau The aggregate estimate is: Obtain MOEs of the component estimates: MOE (Fairfax) = ±3,860 MOE (Arlington) = ±2,642 MOE (Alexandria) = ±1,957 Using formula (1), calculate the MOE for the aggregate estimate: Thus, the derived estimate of the number of never-married females living in the three Virginia counties/independent cities that border Washington, DC, is 203,119, and the MOE for the estimate is ±5,070. The SE of this derived estimate can be calculated from the SEs of the component estimates as follows: 1. Calculate the SE of each component estimate from its MOE using: (2) SE (Fairfax) = 3,860 / 1.645 = 2,347 SE (Arlington) = 2,642 / 1.645 = 1,606 SE (Alexandria) = 1,957 / 1.645 = 1,190 2. Calculate the SE of the aggregate estimate: (3) With the three component estimates in this example, this becomes: To assess the reliability of this derived estimate, users may find it helpful to calculate the CV as follows: (4) Understanding and Using American Community Survey Data 61 What All Data Users Need to Know 61 U.S. Census Bureau This CV indicates that the sampling error of this estimate is very small relative to the estimate itself, so the number of never-married females residing in the Virginia tri-county area bordering Washington, DC, can be considered a very reliable estimate.
```

**Response:**

```text
The Census Bureau's example adds up the number of never-married women in Fairfax County, Arlington County, and Alexandria City, Virginia, from the 2015 ACS to get a combined total of 203,119 — with a margin of error of about ±5,070, found by squaring each county's margin of error, adding them, and taking the square root.

Because that margin is tiny compared with the estimate itself, the combined figure is considered very reliable.
```

**C041 — Level (L0 / L1 / L2 / L3 / L4 / U):** L3

**C041 — Note:** Vintage given as "2015 ACS" with the 1-year period dropped, and it is bound to the three-county aggregate rather than to Arlington's 43,104, which the response never restates.

---

## C042

- **Estimate:** B19013_001E for "Bannock County, Idaho" — **64080**
- **Qualifier family:** `interval` · **published forms:** MOE = 2470 (field=B19013_001M, level=0.9, unit=currency)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

[["NAME","B19013_001E","B19013_001M","state","county"],
["Ada County, Idaho","88907","1710","16","001"],
["Adams County, Idaho","59286","4144","16","003"],
["Bannock County, Idaho","64080","2470","16","005"],
["Bear Lake County, Idaho","67304","6987","16","007"],
["Benewah County, Idaho","56553","3912","16","009"],
```

**Response:**

```text
Census data showing median household income for Idaho counties — about $88,900 in Ada, $59,300 in Adams, $64,100 in Bannock, $67,300 in Bear Lake, and $56,600 in Benewah.
```

**C042 — Level (L0 / L1 / L2 / L3 / L4 / U):** L1

**C042 — Note:** The response restates the Bannock estimate (rounded to $64,100) but gives no margin of error, interval, or verbal uncertainty band, so the interval family is omitted.

---

## C043

- **Estimate:** the degrees-of-freedom threshold below which an NCHS rate is flagged for statistical review — **8**
- **Qualifier family:** `reliability` · **published forms:** RELIABILITY_FLAG = flagged for statistical review (polarity=unreliable)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

Table A. National Center for Health Statistics standards for rates and counts Statistic Standard for rates Standard for counts Sample size threshold Estimated rates should be based on a minimum sample size and effective sample size (when applicable) of 10 in both numerator and denominator. Estimated counts should be based on a minimum sample size and effective sample size (when applicable) of 10. Confidence interval (CI) If the sample size criteria are met, calculate a 95% two-sided CI using the appropriate method and obtain its relative width. Estimated rates should have a relative CI width of 160% or lower. If the sample size criteria are met, calculate a 95% twosided CI using the appropriate method and obtain its relative width. Estimated counts should have a relative CI width of 160% or lower. Degrees of freedom When applicable for complex surveys, if the sample size and CI criteria are met for presentation and degrees of freedom are fewer than 8 for either numerator or denominator, then the rate should be flagged for statistical review by the clearance official. This review may result in presentation or suppression of the rate. When applicable for complex surveys, if the sample size and CI criteria are met for presentation and degrees of freedom are fewer than 8, then the count should be flagged for statistical review by the clearance official. This review may result in presentation or suppression of the count. SOURCE: National Center for Health Statistics.
```

**Response:**

```text
The National Center for Health Statistics only publishes rates and counts based on at least 10 cases with reasonably precise confidence intervals, flagging results from very small surveys for expert review.
```

**C043 — Level (L0 / L1 / L2 / L3 / L4 / U):** L2

**C043 — Note:** Flag for review is preserved only verbally; the degrees-of-freedom threshold of 8 is dropped and paraphrased as "very small surveys."

---

## C044

- **Estimate:** the share of counties whose privacy-protected total population (2021-06-08 PPMF) is within the stated bound of their published 2010 total population — **90**
- **Qualifier family:** `dp` · **published forms:** DP_NOISE = four (parameter=bound, unit=count)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

The latest PPMF vintage 2021-06-08 is the Production Settings run, which uses the same software and settings for the 2020 production run of the redistricting data. Users can compare tabulated values from the PPMFs to published 2010 data to identify the amount of uncertainty that can be expected for a given geography or characteristic. Users can also calculate new measures of the spread of the uncertainty. For example, comparing tabulations from the PPMFs with the published 2010 data will show that 90 percent of counties have a privacy-protected total population that is within ± four people of their published total population.
```

**Response:**

```text
The newest privacy-protected census test file mirrors the real 2020 settings, letting users gauge accuracy — 90 percent of counties land within four people of their published 2010 population.
```

**C044 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C044 — Note:** The ± sign is dropped, but "within four people" still states the same symmetric bound, value, unit, and binding to the county population comparison.

---

## C045

- **Estimate:** the percentage of householders aged 65 or older who live alone in Florida (2015 ACS) — **12.6**
- **Qualifier family:** `interval` · **published forms:** MOE = 0.2 (level=0.9, unit=percent_points)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

The example below shows how to determine if the difference in the estimated percentage of householders age 65 or older who live alone between Florida (estimated percentage = 12.6, MOE = 0.2) and Arizona (estimated percentage = 10.5, MOE = 0.3) is statistically significant, based on 2015 ACS data. Using formula (1) above, first calculate the corresponding standard errors for Florida (0.122) and Arizona (0.182) by dividing the MOEs by 1.645. Then, using formula (3) above, calculate the test value as follows: Understanding and Using American Community Survey Data 57 What All Data Users Need to Know 57 U.S. Census Bureau Since the test value (9.581) is greater than the critical value for a confidence level of 90 percent (1.645), the difference in the percentages is statistically significant at a 90 percent confidence level. A rough interpretation of the result is that the user can be 90 percent certain that a difference exists between the percentage of householders aged 65 or older who live alone in Florida and in Arizona. By contrast, if the corresponding estimate for Indiana (estimated percentage = 10.8, MOE = 0.2, SE = 0.122) were compared with the estimate for Arizona, formula (3) would yield: Since the test value (1.369) is less than the critical value for a confidence level of 90 percent (1.645), the difference in percentages is not statistically significant. A rough interpretation of the result is that the user cannot be certain to any sufficient degree that the observed difference in the estimates between Indiana and Arizona was not due to chance.
```

**Response:**

```text
Census data comes with a margin of error, so you compare two states by dividing that difference by its uncertainty — Florida clearly differs from Arizona, Indiana doesn't.
```

**C045 — Level (L0 / L1 / L2 / L3 / L4 / U):** L2

**C045 — Note:** The response never restates the 12.6 estimate and only says census data "comes with a margin of error" generically, so the verbal qualifier is not bound to the Florida figure; arguably L1.

---

## C046

- **Estimate:** overweight or obese youth (12 to 17, self-reported BMI) in Région de Laval, Quebec, 2021/2022 (percent) — **38.9**
- **Qualifier family:** `interval` · **published forms:** CI (form=bounds, level=0.95, lower=26.7, lower_text=26.7, rows=['"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Low 95% confidence interval, percent","Percent","239","units","0","v115548669","35.1.1.8.5","26.7","E","","","1"', '"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","High 95% confidence interval, percent","Percent","239","units","0","v115548670","35.1.1.8.6","52.7","E","","","1"'], unit=percent, upper=52.7, upper_text=52.7)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

﻿"REF_DATE","GEO","DGUID","Age group","Sex","Indicators","Characteristics","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Percent","Percent","239","units","0","v115548660","35.1.1.7.4","28.9","","","","1"
"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Low 95% confidence interval, percent","Percent","239","units","0","v115548661","35.1.1.7.5","25.3","","","","1"
"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","High 95% confidence interval, percent","Percent","239","units","0","v115548662","35.1.1.7.6","32.8","","","","1"
"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Percent","Percent","239","units","0","v115548668","35.1.1.8.4","38.9","E","","","1"
"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Low 95% confidence interval, percent","Percent","239","units","0","v115548669","35.1.1.8.5","26.7","E","","","1"
"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","High 95% confidence interval, percent","Percent","239","units","0","v115548670","35.1.1.8.6","52.7","E","","","1"
"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Percent","Percent","239","units","0","v115548676","35.1.1.9.4","16.5","","","","1"
"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Low 95% confidence interval, percent","Percent","239","units","0","v115548677","35.1.1.9.5","14.3","","","","1"
"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","High 95% confidence interval, percent","Percent","239","units","0","v115548678","35.1.1.9.6","18.9","","","","1"
"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Diabetes","Percent","Percent","239","units","0","v115548684","35.1.1.10.4","8.7","","","","1"
"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Diabetes","Low 95% confidence interval, percent","Percent","239","units","0","v115548685","35.1.1.10.5","7.1","","","","1"
"2021/2022","Région de Laval, Quebec","2015A00072413","Total, 12 years and over","Both sexes","Diabetes","High 95% confidence interval, percent","Percent","239","units","0","v115548686","35.1.1.10.6","10.8","","","","1"
Symbol Legend
Description,Symbol
"not available for a specific reference period","..",
"less than the limit of detection","<LOD",
"value rounded to 0 (zero) where there is a meaningful distinction between true zero and the value that was rounded","0s",
"data quality: excellent","A",
"data quality: very good","B",
"data quality: good","C",
"data quality: acceptable","D",
"use with caution","E",
"too unreliable to be published","F",
"not applicable","...",
"preliminary","p",
"revised","r",
"suppressed to meet the confidentiality requirements of the Statistics Act","x",
```

**Response:**

```text
In 2021/2022, Laval region, Quebec reported significant health challenges: nearly 29% of adults were obese, 39% of youth were overweight or obese, 16.5% had arthritis, and 8.7% had diabetes. Each statistic includes confidence intervals reflecting measurement uncertainty, with youth obesity data flagged as needing cautious interpretation.
```

**C046 — Level (L0 / L1 / L2 / L3 / L4 / U):** L2

**C046 — Note:** Interval acknowledged only generically ("includes confidence intervals reflecting measurement uncertainty") with no bounds or width, so borderline L1; the "cautious interpretation" flag belongs to the reliability family, not this one.

---

## C047

- **Estimate:** the relative 95% confidence interval width above which an NCHS proportion with absolute width between 0.05 and 0.30 is suppressed — **130**
- **Qualifier family:** `reliability` · **published forms:** SUPPRESSION = suppressed
- **Mode:** direct · **Compression:** (n/a — direct mode)

**Prompt shown to the consumer:**

```text
Table. NCHS Data Presentation Standards for Proportions Statistic Standard Sample size Estimated proportions should be based on a minimum denominator sample size and effective denominator sample size (when applicable) of 30. Estimates with either a denominator sample size or an effective denominator sample size (when applicable) less than 30 should be suppressed. If the number of events is 0 (or its complement 1 ), then the denominator sample size should be used to obtain confidence intervals. If all other criteria are met for presentation, an estimate based on 0 events (or its complement 1 ) should be flagged for statistical review by the clearance official. The review could result in either the presentation or the suppression of the proportion. Confidence interval If the sample size criterion is met, calculate a 95% two-sided confidence interval using the Clopper-Pearson method, or the Korn-Graubard method for complex surveys, and obtain its width. Small absolute confidence interval width If the absolute confidence interval width is greater than 0.00 and less than or equal to 0.05, then the proportion can be presented if the number of events is greater than 0 and the degrees of freedom criterion (below) is met. If the number of events is 0 (or its complement 1 ) or the degrees of freedom criterion is not met, then the estimate should be flagged for statistical review by the clearance official. The review could result in either the presentation or the suppression of the proportion. Large absolute confidence interval width If the absolute confidence interval width is greater than or equal to 0.30, then the proportion should be suppressed. Relative confidence interval width If the absolute confidence interval width is between 0.05 and 0.30 and the relative confidence interval width is more than 130%, then the proportion should be suppressed. Relative confidence interval width If the absolute confidence interval width is between 0.05 and 0.30 and the relative confidence interval width is less than or equal to 130%, then the proportion can be presented if the degrees of freedom criterion below is met.

What is the publication status on the relative 95% confidence interval width above which an NCHS proportion with absolute width between 0.05 and 0.30 is suppressed?
```

**Response:**

```text
**Threshold: 130%; status above it: suppressed.**

Per the NCHS Data Presentation Standards for Proportions, when the absolute 95% CI width falls between 0.05 and 0.30:

- **Relative CI width > 130%** → the proportion is **suppressed** (no presentation, no review pathway).
- **Relative CI width ≤ 130%** → the proportion **may be presented**, but only if the degrees-of-freedom criterion is also met.

So 130% is the cutoff, and exceeding it is a hard suppression rule rather than a flag-for-clearance-review outcome — unlike the 0-events and small-width (≤0.05) cases, which route to the clearance official for statistical review.
```

**C047 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C047 — Note:** Response restates the 130% threshold and the suppressed status bound to it exactly; the "estimate" is a policy threshold rather than a survey statistic, so the suppression qualifier is a rule outcome, not a flag on a published number.

---

## C048

- **Estimate:** unemployment rate in Alberta, 2026-07 (seasonally adjusted) — **7.0**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = 2026-07 (as_of=2026-07)
- **Mode:** indirect · **Compression:** none

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary.

﻿"REF_DATE","GEO","DGUID","Labour force characteristics","Gender","Age group","Statistics","Data type","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2026-07","Alberta","2021A000248","Population","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064510","10.1.1.1.1.1","4150.2","","","","1"
"2026-07","Alberta","2021A000248","Labour force","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064511","10.2.1.1.1.1","2872.2","","","","1"
"2026-07","Alberta","2021A000248","Labour force","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888840","10.2.1.1.2.1","18.8","","","","1"
"2026-07","Alberta","2021A000248","Employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064512","10.3.1.1.1.1","2670.0","","","","1"
"2026-07","Alberta","2021A000248","Employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888894","10.3.1.1.2.1","19.8","","","","1"
"2026-07","Alberta","2021A000248","Full-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064513","10.4.1.1.1.1","2202.8","","","","1"
"2026-07","Alberta","2021A000248","Full-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888948","10.4.1.1.2.1","21.8","","","","1"
"2026-07","Alberta","2021A000248","Part-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064514","10.5.1.1.1.1","467.1","","","","1"
"2026-07","Alberta","2021A000248","Part-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888996","10.5.1.1.2.1","17.8","","","","1"
"2026-07","Alberta","2021A000248","Unemployment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064515","10.6.1.1.1.1","202.2","","","","1"
"2026-07","Alberta","2021A000248","Unemployment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889044","10.6.1.1.2.1","11.8","","","","1"
"2026-07","Alberta","2021A000248","Unemployment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064516","10.7.1.1.1.1","7.0","","","","1"
"2026-07","Alberta","2021A000248","Unemployment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889098","10.7.1.1.2.1","0.4","","","","1"
"2026-07","Alberta","2021A000248","Participation rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064517","10.8.1.1.1.1","69.2","","","","1"
"2026-07","Alberta","2021A000248","Participation rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889152","10.8.1.1.2.1","0.5","","","","1"
"2026-07","Alberta","2021A000248","Employment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064518","10.9.1.1.1.1","64.3","","","","1"
"2026-07","Alberta","2021A000248","Employment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889206","10.9.1.1.2.1","0.5","","","","1"
```

**Response:**

```text
## Alberta's job market, July 2026

*(Statistics Canada Labour Force Survey, seasonally adjusted. All figures come from a monthly sample survey, so each one carries a margin of error.)*

**The basics**

Alberta had about **4.15 million people aged 15 and over**. Of those:

- **2.87 million were in the labour force** — meaning they either had a job or were actively looking for one.
- **2.67 million were working**: 2.20 million full-time and 467,000 part-time.
- **202,000 were unemployed** — without work but looking for it.
- The remaining ~1.28 million were outside the labour force entirely: retirees, students, people caring for family, people not currently job-hunting.

**The three headline rates**

| Rate | Value | What it means |
|---|---|---|
| Unemployment rate | **7.0%** | Of everyone who wanted a job, 7 in 100 couldn't find one |
| Participation rate | **69.2%** | About 7 in 10 adults were working or job-hunting |
| Employment rate | **64.3%** | About 64 in 100 adults actually had a job |

**A note on precision.** These are survey estimates, not a headcount, and the file reports the uncertainty alongside each number. The unemployment rate's standard error is 0.4 points, so the true figure is roughly **7.0% ± 0.8** at conventional (95%) confidence — somewhere in the low-6s to high-7s. The employment figure of 2,670,000 carries a standard error of about 19,800, so it's good to within roughly ±40,000. Month-to-month wiggles smaller than that aren't real news.

"Seasonally adjusted" means the numbers have been smoothed to remove predictable annual patterns — summer student hiring, holiday retail, construction slowdowns in winter — so this month can be compared fairly against any other month.

**One caveat on scope:** this is the all-genders, all-ages-15-and-over total. The file doesn't break the numbers out by gender or age group, so it can't say whether, for example, youth unemployment differs from the 7.0% overall figure.
```

**C048 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C048 — Note:** none

---

## C049

- **Estimate:** overweight or obese youth (12 to 17, self-reported BMI) in Région de Lanaudière, Quebec, 2021/2022 (percent) — **26.5**
- **Qualifier family:** `interval` · **published forms:** CI (form=bounds, level=0.95, lower=15.8, lower_text=15.8, rows=['"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Low 95% confidence interval, percent","Percent","239","units","0","v115551973","36.1.1.8.5","15.8","E","","","1"', '"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","High 95% confidence interval, percent","Percent","239","units","0","v115551974","36.1.1.8.6","40.9","E","","","1"'], unit=percent, upper=40.9, upper_text=40.9)
- **Mode:** direct · **Compression:** (n/a — direct mode)

**Prompt shown to the consumer:**

```text
﻿"REF_DATE","GEO","DGUID","Age group","Sex","Indicators","Characteristics","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Percent","Percent","239","units","0","v115551964","36.1.1.7.4","33.7","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Low 95% confidence interval, percent","Percent","239","units","0","v115551965","36.1.1.7.5","30.1","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","High 95% confidence interval, percent","Percent","239","units","0","v115551966","36.1.1.7.6","37.5","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Percent","Percent","239","units","0","v115551972","36.1.1.8.4","26.5","E","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Low 95% confidence interval, percent","Percent","239","units","0","v115551973","36.1.1.8.5","15.8","E","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","High 95% confidence interval, percent","Percent","239","units","0","v115551974","36.1.1.8.6","40.9","E","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Percent","Percent","239","units","0","v115551980","36.1.1.9.4","19.3","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Low 95% confidence interval, percent","Percent","239","units","0","v115551981","36.1.1.9.5","16.8","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","High 95% confidence interval, percent","Percent","239","units","0","v115551982","36.1.1.9.6","22.1","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","Percent","Percent","239","units","0","v115551988","36.1.1.10.4","8.9","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","Low 95% confidence interval, percent","Percent","239","units","0","v115551989","36.1.1.10.5","7.2","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","High 95% confidence interval, percent","Percent","239","units","0","v115551990","36.1.1.10.6","11.0","","","","1"
Symbol Legend
Description,Symbol
"not available for a specific reference period","..",
"less than the limit of detection","<LOD",
"value rounded to 0 (zero) where there is a meaningful distinction between true zero and the value that was rounded","0s",
"data quality: excellent","A",
"data quality: very good","B",
"data quality: good","C",
"data quality: acceptable","D",
"use with caution","E",
"too unreliable to be published","F",
"not applicable","...",
"preliminary","p",
"revised","r",
"suppressed to meet the confidentiality requirements of the Statistics Act","x",

What is the confidence interval on overweight or obese youth (12 to 17, self-reported BMI) in Région de Lanaudière, Quebec, 2021/2022 (percent)?
```

**Response:**

```text
**15.8% – 40.9%** (95% CI), around an estimate of **26.5%**.

All three values carry the **`E` symbol — "use with caution"**, which the interval itself makes obvious: it spans ~25 percentage points, so the youth BMI estimate for Lanaudière is very imprecise (small 12–17 subsample).

Source rows: vectors `v115551972` (estimate), `v115551973` (low), `v115551974` (high).
```

**C049 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C049 — Note:** none

---

## C050

- **Estimate:** the number of Loudoun County, Virginia households with income of $25,000 to $34,999 in 2015 (Table DP03) — **3,537**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = from the 2015 ACS 1-year estimates (as_of=2015, period=1-year)
- **Mode:** indirect · **Compression:** none

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary.

Data.census.gov includes a collapsed income distribution within Demographic Profile DP03 that makes it possible to assess the difference in results from the approximation method illustrated above versus a direct estimation method that accounts for covariance between the component estimates of the subgroups. The relevant portion of this data.census.gov table, from the 2015 ACS 1-year estimates, is shown in Table 8.3 below. Table 8.3. Data From Demographic Profile DP03 for Loudoun County, Virginia: 2015 Household income category Subgroup # Estimate MOE SE CV $15,000 to $24,999 .... 1 3,497 ±1,037 630 18.0 $25,000 to $34,999 .... 2 3,537 ±973 591 16.7 $35,000 to $49,999 .... 3 7,270 ±1,554 945 13.0 Source: U.S. Census Bureau, data.census.gov, Table DP03: “Selected Economic Characteristics.” While the MOEs, SEs, and CVs for new Subgroup 1 and Subgroup 3 are almost identical to those derived from the approximation method, this is not the case for new Subgroup 2. The user-derived MOE is ±931 compared with the published MOE of ±973, and the derived CV is only 16.0 percent compared with a CV of 16.7 percent based on the published MOE for Subgroup 2.
```

**Response:**

```text
**General-audience restatement**

Census data on data.census.gov includes a table (Demographic Profile DP03) that already groups household incomes into broad categories. That gives us a useful test: we can compare the shortcut method for combining margins of error — the approximation shown earlier — against the Census Bureau's own published figures, which are calculated directly and account for the fact that errors in the individual income groups are related to one another (their covariance).

The comparison uses Loudoun County, Virginia, from the 2015 ACS 1-year estimates:

| Income category | Subgroup | Households | Margin of error | Standard error | Coefficient of variation |
|---|---|---|---|---|---|
| $15,000–$24,999 | 1 | 3,497 | ±1,037 | 630 | 18.0% |
| $25,000–$34,999 | 2 | 3,537 | ±973 | 591 | 16.7% |
| $35,000–$49,999 | 3 | 7,270 | ±1,554 | 945 | 13.0% |

*Source: U.S. Census Bureau, data.census.gov, Table DP03, "Selected Economic Characteristics."*

**What the comparison shows:** For Subgroups 1 and 3, the shortcut method produces margins of error, standard errors, and coefficients of variation that are essentially the same as the published values. Subgroup 2 is the exception. There, the shortcut gives a margin of error of ±931, while the published value is ±973 — the shortcut understates the uncertainty. The same gap appears in the coefficient of variation: 16.0 percent by the shortcut versus 16.7 percent using the published margin of error.

**The takeaway:** The approximation is usually close, but it can make an estimate look slightly more precise than it really is. When published figures are available, use them.
```

**C050 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C050 — Note:** none

---

## C051

- **Estimate:** the number of never-married females living in Fairfax County, Arlington County and Alexandria City combined (2015 ACS 1-year) — **203,119**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = 2015 ACS 1-year estimates (as_of=2015, period=1-year)
- **Mode:** direct · **Compression:** (n/a — direct mode)

**Prompt shown to the consumer:**

```text
The example below shows how to calculate the MOE and SE for the estimated number of never-married females living in the three Virginia counties/independent cities that border Washington, DC (Fairfax and Arlington counties, Alexandria City) from the 2015 ACS 1-year estimates. Table 8.1. Data for Example 1 From Three Virginia Counties/Independent Cities: 2015 Characteristic Estimate MOE Never-married females living in Fairfax County (Component 1) ................................. 135,173 ±3,860 Never-married females living in Arlington County (Component 2) ................................. 43,104 ±2,642 Never-married females living in Alexandria City (Component 3) .................................. 24,842 ±1,957 Source: U.S. Census Bureau, data.census.gov, Table B12001: “Sex by Marital Status for the Population 15 Years and Over.” 60 Understanding and Using American Community Survey Data 60 What All Data Users Need to Know U.S. Census Bureau The aggregate estimate is: Obtain MOEs of the component estimates: MOE (Fairfax) = ±3,860 MOE (Arlington) = ±2,642 MOE (Alexandria) = ±1,957 Using formula (1), calculate the MOE for the aggregate estimate: Thus, the derived estimate of the number of never-married females living in the three Virginia counties/independent cities that border Washington, DC, is 203,119, and the MOE for the estimate is ±5,070. The SE of this derived estimate can be calculated from the SEs of the component estimates as follows: 1. Calculate the SE of each component estimate from its MOE using: (2) SE (Fairfax) = 3,860 / 1.645 = 2,347 SE (Arlington) = 2,642 / 1.645 = 1,606 SE (Alexandria) = 1,957 / 1.645 = 1,190 2. Calculate the SE of the aggregate estimate: (3) With the three component estimates in this example, this becomes: To assess the reliability of this derived estimate, users may find it helpful to calculate the CV as follows: (4) Understanding and Using American Community Survey Data 61 What All Data Users Need to Know 61 U.S. Census Bureau This CV indicates that the sampling error of this estimate is very small relative to the estimate itself, so the number of never-married females residing in the Virginia tri-county area bordering Washington, DC, can be considered a very reliable estimate.

What is the reference period or as-of date on the number of never-married females living in Fairfax County, Arlington County and Alexandria City combined (2015 ACS 1-year)?
```

**Response:**

```text
**Reference period: calendar year 2015 — January 1 through December 31, 2015.**

The aggregate (203,119 never-married females, MOE ±5,070) inherits the reference period of its three components, all drawn from Table B12001 of the **2015 ACS 1-year estimates**.

Key points about what that means:

- **It is a period estimate, not a point-in-time count.** ACS 1-year estimates describe the average characteristics of the area over the full 12 months of data collection. There is no "as-of" date analogous to the decennial census's April 1 reference date.
- **Interview-date reference.** Marital status in B12001 is recorded as of the respondent's interview date, and interviews are spread across all 12 months of 2015. The published estimate is effectively an average over the year.
- **Inflation-adjusted dollar figures** (not relevant here, since this is a person count) would be in 2015 dollars — the same year.
- **Population universe:** population 15 years and over, per the B12001 table title.

So the correct citation of the derived figure is: *approximately 203,119 never-married females aged 15+ in Fairfax County, Arlington County, and Alexandria City, VA, averaged over calendar year 2015 (±5,070 at the 90% confidence level).*
```

**C051 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C051 — Note:** none

---

## C052

- **Estimate:** total turnover of water supply, sewerage, waste management and remediation activities in the UK in 2016, in £ millions — **34,677**
- **Qualifier family:** `interval` · **published forms:** SE = 222.7 (scale=1000000, unit=currency)
- **Mode:** direct · **Compression:** (n/a — direct mode)

**Prompt shown to the consumer:**

```text
Table 1: Total turnover estimates, standard error and relative standard error for education and water and waste management, UK, 2016 Total turnover in | Standard error in | Relative standard error (or coefficient of variation)2 ---|---|--£ millions1 | £ millions2 Industry 1: Education (private provision only) | 42,649 | 526.8 | 0.01 (or 1%) Industry 2: Water supply; sewerage, waste management and remediation activities | 34,677 | 222.7 | 0.01 (or 1%)

What is the standard error on total turnover of water supply, sewerage, waste management and remediation activities in the UK in 2016, in £ millions?
```

**Response:**

```text
£222.7 million.
```

**C052 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C052 — Note:** none

---

## C053

- **Estimate:** diabetes (12 and over) in Région de Lanaudière, Quebec, 2021/2022 (percent) — **8.9**
- **Qualifier family:** `interval` · **published forms:** CI (form=bounds, level=0.95, lower=7.2, lower_text=7.2, rows=['"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","Low 95% confidence interval, percent","Percent","239","units","0","v115551989","36.1.1.10.5","7.2","","","","1"', '"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","High 95% confidence interval, percent","Percent","239","units","0","v115551990","36.1.1.10.6","11.0","","","","1"'], unit=percent, upper=11.0, upper_text=11.0)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

﻿"REF_DATE","GEO","DGUID","Age group","Sex","Indicators","Characteristics","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Percent","Percent","239","units","0","v115551964","36.1.1.7.4","33.7","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Low 95% confidence interval, percent","Percent","239","units","0","v115551965","36.1.1.7.5","30.1","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","High 95% confidence interval, percent","Percent","239","units","0","v115551966","36.1.1.7.6","37.5","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Percent","Percent","239","units","0","v115551972","36.1.1.8.4","26.5","E","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Low 95% confidence interval, percent","Percent","239","units","0","v115551973","36.1.1.8.5","15.8","E","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","High 95% confidence interval, percent","Percent","239","units","0","v115551974","36.1.1.8.6","40.9","E","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Percent","Percent","239","units","0","v115551980","36.1.1.9.4","19.3","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Low 95% confidence interval, percent","Percent","239","units","0","v115551981","36.1.1.9.5","16.8","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","High 95% confidence interval, percent","Percent","239","units","0","v115551982","36.1.1.9.6","22.1","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","Percent","Percent","239","units","0","v115551988","36.1.1.10.4","8.9","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","Low 95% confidence interval, percent","Percent","239","units","0","v115551989","36.1.1.10.5","7.2","","","","1"
"2021/2022","Région de Lanaudière, Quebec","2015A00072414","Total, 12 years and over","Both sexes","Diabetes","High 95% confidence interval, percent","Percent","239","units","0","v115551990","36.1.1.10.6","11.0","","","","1"
Symbol Legend
Description,Symbol
"not available for a specific reference period","..",
"less than the limit of detection","<LOD",
"value rounded to 0 (zero) where there is a meaningful distinction between true zero and the value that was rounded","0s",
"data quality: excellent","A",
"data quality: very good","B",
"data quality: good","C",
"data quality: acceptable","D",
"use with caution","E",
"too unreliable to be published","F",
"not applicable","...",
"preliminary","p",
"revised","r",
"suppressed to meet the confidentiality requirements of the Statistics Act","x",
```

**Response:**

```text
During 2021–2022, the Région de Lanaudière in Quebec reported significant rates of chronic health conditions: approximately one-third of adults were obese (33.7%), one-fifth had arthritis (19.3%), and roughly one in eleven had diabetes (8.9%). Additionally, about one-quarter of youth aged 12–17 were overweight or obese (26.5%), though this youth estimate should be interpreted cautiously due to data quality limitations.
```

**C053 — Level (L0 / L1 / L2 / L3 / L4 / U):** L1

**C053 — Note:** The diabetes estimate is restated as 8.9% with no confidence interval, bounds, or verbal uncertainty band; the only caution language is bound to the youth BMI estimate.

---

## C054

- **Estimate:** the number of Loudoun County, Virginia households with income of $25,000 to $34,999 in 2015 (Table DP03) — **3,537**
- **Qualifier family:** `interval` · **published forms:** MOE = 973 (level=0.9, unit=count); SE = 591 (unit=count)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

Data.census.gov includes a collapsed income distribution within Demographic Profile DP03 that makes it possible to assess the difference in results from the approximation method illustrated above versus a direct estimation method that accounts for covariance between the component estimates of the subgroups. The relevant portion of this data.census.gov table, from the 2015 ACS 1-year estimates, is shown in Table 8.3 below. Table 8.3. Data From Demographic Profile DP03 for Loudoun County, Virginia: 2015 Household income category Subgroup # Estimate MOE SE CV $15,000 to $24,999 .... 1 3,497 ±1,037 630 18.0 $25,000 to $34,999 .... 2 3,537 ±973 591 16.7 $35,000 to $49,999 .... 3 7,270 ±1,554 945 13.0 Source: U.S. Census Bureau, data.census.gov, Table DP03: “Selected Economic Characteristics.” While the MOEs, SEs, and CVs for new Subgroup 1 and Subgroup 3 are almost identical to those derived from the approximation method, this is not the case for new Subgroup 2. The user-derived MOE is ±931 compared with the published MOE of ±973, and the derived CV is only 16.0 percent compared with a CV of 16.7 percent based on the published MOE for Subgroup 2.
```

**Response:**

```text
Census data for Loudoun County, Virginia shows the shortcut method for combining income groups slightly understates uncertainty, giving a margin of error of ±931 instead of ±973.
```

**C054 — Level (L0 / L1 / L2 / L3 / L4 / U):** L3

**C054 — Note:** Published MOE ±973 restated exactly but confidence level omitted; the 3,537 estimate and its subgroup are not named, so binding is only implicit via the ±931/±973 contrast.

---

## C055

- **Estimate:** labour force in Alberta, 2026-07 (seasonally adjusted) — **2872.2**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = 2026-07 (as_of=2026-07)
- **Mode:** direct · **Compression:** (n/a — direct mode)

**Prompt shown to the consumer:**

```text
﻿"REF_DATE","GEO","DGUID","Labour force characteristics","Gender","Age group","Statistics","Data type","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2026-07","Alberta","2021A000248","Population","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064510","10.1.1.1.1.1","4150.2","","","","1"
"2026-07","Alberta","2021A000248","Labour force","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064511","10.2.1.1.1.1","2872.2","","","","1"
"2026-07","Alberta","2021A000248","Labour force","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888840","10.2.1.1.2.1","18.8","","","","1"
"2026-07","Alberta","2021A000248","Employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064512","10.3.1.1.1.1","2670.0","","","","1"
"2026-07","Alberta","2021A000248","Employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888894","10.3.1.1.2.1","19.8","","","","1"
"2026-07","Alberta","2021A000248","Full-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064513","10.4.1.1.1.1","2202.8","","","","1"
"2026-07","Alberta","2021A000248","Full-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888948","10.4.1.1.2.1","21.8","","","","1"
"2026-07","Alberta","2021A000248","Part-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064514","10.5.1.1.1.1","467.1","","","","1"
"2026-07","Alberta","2021A000248","Part-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101888996","10.5.1.1.2.1","17.8","","","","1"
"2026-07","Alberta","2021A000248","Unemployment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064515","10.6.1.1.1.1","202.2","","","","1"
"2026-07","Alberta","2021A000248","Unemployment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889044","10.6.1.1.2.1","11.8","","","","1"
"2026-07","Alberta","2021A000248","Unemployment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064516","10.7.1.1.1.1","7.0","","","","1"
"2026-07","Alberta","2021A000248","Unemployment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889098","10.7.1.1.2.1","0.4","","","","1"
"2026-07","Alberta","2021A000248","Participation rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064517","10.8.1.1.1.1","69.2","","","","1"
"2026-07","Alberta","2021A000248","Participation rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889152","10.8.1.1.2.1","0.5","","","","1"
"2026-07","Alberta","2021A000248","Employment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064518","10.9.1.1.1.1","64.3","","","","1"
"2026-07","Alberta","2021A000248","Employment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889206","10.9.1.1.2.1","0.5","","","","1"

What is the reference period or as-of date on labour force in Alberta, 2026-07 (seasonally adjusted)?
```

**Response:**

```text
**Reference period: July 2026** (`REF_DATE` = `2026-07`).

Every row in the extract carries the same `REF_DATE`, so the whole table is a single-month snapshot — Alberta, seasonally adjusted, 15 years and over, both genders. There is no separate "as-of" or release-date column in the file; the only temporal field is the monthly reference period.

Two things worth noting for downstream use:

- **Monthly, not point-in-time.** These are Labour Force Survey estimates for the July 2026 reference month. Statistics Canada's LFS reference period is the week containing the 15th of the month, so the underlying collection window is mid-July 2026 — but the file itself only asserts month granularity.
- **`TERMINATED` and `STATUS` are blank** on all rows, meaning these are live, unflagged estimates, not revised-out or suppressed values.

Headline figures for that period: unemployment rate 7.0% (SE 0.4), participation rate 69.2% (SE 0.5), employment rate 64.3% (SE 0.5), employment 2,670.0 thousand (SE 19.8).
```

**C055 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C055 — Note:** none

---

## C056

- **Estimate:** the number of never-married females living in Arlington County (2015 ACS 1-year) — **43,104**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = 2015 ACS 1-year estimates (as_of=2015, period=1-year)
- **Mode:** direct · **Compression:** (n/a — direct mode)

**Prompt shown to the consumer:**

```text
The example below shows how to calculate the MOE and SE for the estimated number of never-married females living in the three Virginia counties/independent cities that border Washington, DC (Fairfax and Arlington counties, Alexandria City) from the 2015 ACS 1-year estimates. Table 8.1. Data for Example 1 From Three Virginia Counties/Independent Cities: 2015 Characteristic Estimate MOE Never-married females living in Fairfax County (Component 1) ................................. 135,173 ±3,860 Never-married females living in Arlington County (Component 2) ................................. 43,104 ±2,642 Never-married females living in Alexandria City (Component 3) .................................. 24,842 ±1,957 Source: U.S. Census Bureau, data.census.gov, Table B12001: “Sex by Marital Status for the Population 15 Years and Over.” 60 Understanding and Using American Community Survey Data 60 What All Data Users Need to Know U.S. Census Bureau The aggregate estimate is: Obtain MOEs of the component estimates: MOE (Fairfax) = ±3,860 MOE (Arlington) = ±2,642 MOE (Alexandria) = ±1,957 Using formula (1), calculate the MOE for the aggregate estimate: Thus, the derived estimate of the number of never-married females living in the three Virginia counties/independent cities that border Washington, DC, is 203,119, and the MOE for the estimate is ±5,070. The SE of this derived estimate can be calculated from the SEs of the component estimates as follows: 1. Calculate the SE of each component estimate from its MOE using: (2) SE (Fairfax) = 3,860 / 1.645 = 2,347 SE (Arlington) = 2,642 / 1.645 = 1,606 SE (Alexandria) = 1,957 / 1.645 = 1,190 2. Calculate the SE of the aggregate estimate: (3) With the three component estimates in this example, this becomes: To assess the reliability of this derived estimate, users may find it helpful to calculate the CV as follows: (4) Understanding and Using American Community Survey Data 61 What All Data Users Need to Know 61 U.S. Census Bureau This CV indicates that the sampling error of this estimate is very small relative to the estimate itself, so the number of never-married females residing in the Virginia tri-county area bordering Washington, DC, can be considered a very reliable estimate.

What is the reference period or as-of date on the number of never-married females living in Arlington County (2015 ACS 1-year)?
```

**Response:**

```text
**Reference period: calendar year 2015 (January 1 – December 31, 2015) — a 12-month period average, not a point-in-time as-of date.**

Specifics for the Arlington County figure (43,104 ±2,642, Table B12001):

- **1-year estimates** are built from all ACS interviews conducted over the 12 months of 2015. Every respondent reports marital status as of their own interview date, and those responses are spread across the year, so the published number represents the *average* characteristics of the population over the full year — there is no single day it describes.
- **Geography** is defined by the boundaries in effect on **January 1, 2015** (the vintage date for ACS geographic definitions), which is why "Arlington County" here is a county-level tabulation with its 2015 boundaries.
- **Not comparable to a decennial census count**, which is an as-of-April-1 point-in-time enumeration. This is the most common misreading of ACS figures.
- Contrast with 5-year estimates, where the same table for a small area would carry a 2011–2015 reference period.
- Dollar-denominated ACS variables get inflation-adjusted to the reference year; irrelevant for this table since it's a person count, but it's the same reference-period logic.

Release timing (published September 2016) is a *publication* date, not the reference period — worth keeping separate when citing.
```

**C056 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C056 — Note:** none

---

## C057

- **Estimate:** B19013_001E for "Bannock County, Idaho" — **64080**
- **Qualifier family:** `interval` · **published forms:** MOE = 2470 (field=B19013_001M, level=0.9, unit=currency)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

[["NAME","B19013_001E","B19013_001M","state","county"],
["Ada County, Idaho","88907","1710","16","001"],
["Adams County, Idaho","59286","4144","16","003"],
["Bannock County, Idaho","64080","2470","16","005"],
["Bear Lake County, Idaho","67304","6987","16","007"],
["Benewah County, Idaho","56553","3912","16","009"],
```

**Response:**

```text
This table shows median household income estimates for several Idaho counties, with Ada County being the highest at approximately $89,000 and others ranging from about $56,000 to $67,000. Each figure includes a margin of error from the U.S. Census Bureau, indicating the reliability range of the estimate.
```

**C057 — Level (L0 / L1 / L2 / L3 / L4 / U):** L2

**C057 — Note:** Existence-only mention ("each figure includes a margin of error") applied generically to all rows, no magnitude band or level; Bannock's estimate itself is only covered by the "$56,000 to $67,000" range.

---

## C058

- **Estimate:** the largest difference in the biggest demographic group’s share of total population between the published 2010 tabulations and the 2021-06-08 privacy-protected file, for block groups of 450 or more people — **5**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = Privacy-Protected Microdata File (2021-06-08) (as_of=2021-06-08)
- **Mode:** indirect · **Compression:** tight

**Prompt shown to the consumer:**

```text
Restate the following in one sentence of at most 30 words for a general audience.

In the first part of their analysis, the researchers sought to determine the minimum population size necessary for geographic areas to have reliable demographic characteristics for the purposes of redistricting. Examining census block groups as well as places and minor civil divisions (MCDs), they demonstrated that for any block group with a total population between 450 and 499 people or larger, and for MCDs and places between 200 and 249 or larger, the difference in the largest demographic group as a proportion of the total population between the published 2010 Census tabulations and the 2010 Demonstration PrivacyProtected Microdata File (2021-06-08) is less than or equal to 5 percentage points at least 95 percent of the time. No congressional or state legislative district fails this test; that is, for these districts, the 5-percentage-point criterion holds 100 percent of the time.
```

**Response:**

```text
Researchers found that demographic data needed for redistricting remains accurate when geographic areas have sufficient population, even with privacy protections applied.
```

**C058 — Level (L0 / L1 / L2 / L3 / L4 / U):** L1

**C058 — Note:** The vintage is entirely omitted; "with privacy protections applied" names neither the file nor the 2021-06-08 date, and the 5-point estimate itself is dropped too.

---

## C059

- **Estimate:** unemployment in British Columbia, 2025-12 (seasonally adjusted) — **199.6**
- **Qualifier family:** `interval` · **published forms:** SE = 9.6 (level=0.95, row="2025-12","British Columbia","2021A000259","Unemployment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889464","11.6.1.1.2.1","9.6","","","","1", scale=1000, unit=count, z=2.0)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

﻿"REF_DATE","GEO","DGUID","Labour force characteristics","Gender","Age group","Statistics","Data type","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2025-12","British Columbia","2021A000259","Population","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064699","11.1.1.1.1.1","4847.0","","","","1"
"2025-12","British Columbia","2021A000259","Labour force","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064700","11.2.1.1.1.1","3143.7","","","","1"
"2025-12","British Columbia","2021A000259","Labour force","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889260","11.2.1.1.2.1","17.3","","","","1"
"2025-12","British Columbia","2021A000259","Employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064701","11.3.1.1.1.1","2944.1","","","","1"
"2025-12","British Columbia","2021A000259","Employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889314","11.3.1.1.2.1","18.2","","","","1"
"2025-12","British Columbia","2021A000259","Full-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064702","11.4.1.1.1.1","2340.0","","","","1"
"2025-12","British Columbia","2021A000259","Full-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889368","11.4.1.1.2.1","20.1","","","","1"
"2025-12","British Columbia","2021A000259","Part-time employment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064703","11.5.1.1.1.1","604.2","","","","1"
"2025-12","British Columbia","2021A000259","Part-time employment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889416","11.5.1.1.2.1","15.9","","","","1"
"2025-12","British Columbia","2021A000259","Unemployment","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v2064704","11.6.1.1.1.1","199.6","","","","1"
"2025-12","British Columbia","2021A000259","Unemployment","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Persons in thousands","428","thousands","3","v101889464","11.6.1.1.2.1","9.6","","","","1"
"2025-12","British Columbia","2021A000259","Unemployment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064705","11.7.1.1.1.1","6.3","","","","1"
"2025-12","British Columbia","2021A000259","Unemployment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889518","11.7.1.1.2.1","0.3","","","","1"
"2025-12","British Columbia","2021A000259","Participation rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064706","11.8.1.1.1.1","64.9","","","","1"
"2025-12","British Columbia","2021A000259","Participation rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889572","11.8.1.1.2.1","0.4","","","","1"
"2025-12","British Columbia","2021A000259","Employment rate","Total - Gender","15 years and over","Estimate","Seasonally adjusted","Percent","239","units","0","v2064707","11.9.1.1.1.1","60.7","","","","1"
"2025-12","British Columbia","2021A000259","Employment rate","Total - Gender","15 years and over","Standard error of estimate","Seasonally adjusted","Percent","239","units","0","v101889626","11.9.1.1.2.1","0.4","","","","1"
```

**Response:**

```text
In December 2025, British Columbia's labour force comprised 3.1 million people, with 2.9 million employed (60.7% employment rate) and 199,600 unemployed (6.3% unemployment rate). The data shows seasonally adjusted estimates for the population aged 15 and over, with participation at 64.9% and standard errors provided for measurement precision.
```

**C059 — Level (L0 / L1 / L2 / L3 / L4 / U):** L1

**C059 — Note:** The response only says "standard errors provided for measurement precision" generically; no value, band, or binding to the unemployment estimate, so the interval qualifier is effectively omitted rather than verbally degraded.

---

## C060

- **Estimate:** overweight or obese youth (12 to 17, self-reported BMI) in Newfoundland and Labrador, 2022 (percent) — **37.5**
- **Qualifier family:** `reliability` · **published forms:** RELIABILITY_FLAG = E (legend=use with caution, polarity=unreliable, status_column=STATUS, symbol=E)
- **Mode:** indirect · **Compression:** short

**Prompt shown to the consumer:**

```text
Restate the following for a general-audience summary in no more than two sentences.

﻿"REF_DATE","GEO","DGUID","Age group","Sex","Indicators","Characteristics","UOM","UOM_ID","SCALAR_FACTOR","SCALAR_ID","VECTOR","COORDINATE","VALUE","STATUS","SYMBOL","TERMINATED","DECIMALS"
"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Percent","Percent","239","units","0","v110790864","2.1.1.7.4","41.9","","","","1"
"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","Low 95% confidence interval, percent","Percent","239","units","0","v110790865","2.1.1.7.5","38.9","","","","1"
"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Body mass index, adjusted self-reported, adult (18 years and over), obese","High 95% confidence interval, percent","Percent","239","units","0","v110790866","2.1.1.7.6","44.9","","","","1"
"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Percent","Percent","239","units","0","v110790871","2.1.1.8.4","37.5","E","","","1"
"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","Low 95% confidence interval, percent","Percent","239","units","0","v110790872","2.1.1.8.5","26.4","E","","","1"
"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Body mass index, self-reported, youth (12 to 17 years old), overweight or obese","High 95% confidence interval, percent","Percent","239","units","0","v110790873","2.1.1.8.6","50.1","E","","","1"
"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Percent","Percent","239","units","0","v110790878","2.1.1.9.4","27.3","","","","1"
"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","Low 95% confidence interval, percent","Percent","239","units","0","v110790879","2.1.1.9.5","25.3","","","","1"
"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Arthritis (15 years and over)","High 95% confidence interval, percent","Percent","239","units","0","v110790880","2.1.1.9.6","29.4","","","","1"
"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Diabetes","Percent","Percent","239","units","0","v110790885","2.1.1.10.4","12.4","","","","1"
"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Diabetes","Low 95% confidence interval, percent","Percent","239","units","0","v110790886","2.1.1.10.5","10.6","","","","1"
"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Diabetes","High 95% confidence interval, percent","Percent","239","units","0","v110790887","2.1.1.10.6","14.5","","","","1"
Symbol Legend
Description,Symbol
"not available for a specific reference period","..",
"less than the limit of detection","<LOD",
"value rounded to 0 (zero) where there is a meaningful distinction between true zero and the value that was rounded","0s",
"data quality: excellent","A",
"data quality: very good","B",
"data quality: good","C",
"data quality: acceptable","D",
"use with caution","E",
"too unreliable to be published","F",
"not applicable","...",
"preliminary","p",
"revised","r",
"suppressed to meet the confidentiality requirements of the Statistics Act","x",
```

**Response:**

```text
In 2022, about 42% of adults in Newfoundland and Labrador were classified as obese based on self-reported height and weight, and roughly 38% of youth aged 12 to 17 were overweight or obese (though that youth figure is uncertain and should be treated with caution). Chronic conditions were also common: about 27% of residents 15 and over reported arthritis, and roughly 12% reported diabetes.
```

**C060 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4

**C060 — Note:** none

---

