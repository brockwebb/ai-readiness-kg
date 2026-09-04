# G1 calibration — rater/reviewer disagreements

**Written:** 2026-09-04T01:17:21.915914+00:00 · **Task:** `cc_tasks/2026-09-03_g1_calibration_rating_agreement.md` · **Zero model calls.**

**Rater:** `claude-fable-5-1`, independent (one record per call, hermetic cwd, no repo context, no scorer or reviewer information). **Reviewer:** the v2 LLM reviewer (Opus, CC). **Scorer:** `g1-score-v2`.

**Selection:** of the 60 rated sample records, the 9 below are those where the rater's level and the reviewer's implied level differ by 2 or more levels, or where either side gave U. The reviewer's verdict is mapped to a level as: `genuine` → the scorer's level; `parser_miss` → L3 (the lowest preserved level); `not_in_queue` → the scorer's level, with no reviewer judgment behind it (those rows are the rater against the scorer). `unparseable` is the scorer's own U and sorts below L0.

**Nothing in this file proposes a resolution.** It exists so the operator can look at the cases where the two instruments disagree, if he chooses to.

| sample | scorer | reviewer verdict | reviewer level | rater | gap |
|---|---|---|---|---|---:|
| C018 | L0 | genuine | L0 | L4 | 4 |
| C013 | L0 | genuine | L0 | L3 | 3 |
| C046 | unparseable | genuine | unparseable | L2 | U |
| C057 | unparseable | genuine | unparseable | L2 | U |
| C004 | unparseable | genuine | unparseable | L1 | U |
| C008 | L0 | genuine | L0 | L2 | 2 |
| C020 | unparseable | genuine | unparseable | L1 | U |
| C023 | L0 | genuine | L0 | L2 | 2 |
| C059 | unparseable | genuine | unparseable | L1 | U |

---

## C018

- **Record:** `g1h-lfs-ci-001` · family `interval` · mode indirect · compression short · split pooled_opus · `assessment/results/g1_v2_pooled_opus_reviewed.json` record 213
- **Evidence:** `assessment/evidence/g1/v2/dev/lfs-ci-example.indirect.indirect.short.g1-v2-2026-09-03.claude-opus-5.json`
- **Scorer level:** L0
- **Reviewer verdict:** genuine — genuine omission: only the 95 % interval is stated; the 68 % interval (35,000–85,000) is not (the scorer bound the 95 % one — class mislabel, loss unchanged)
- **Rater level:** L4 — Response restates the source's 95% CI (10,000–110,000, "19-in-20") exactly and bound to 60,000, but the record lists only the 68% form (35,000–85,000), so the match is to an unlisted published form, not a widening of the listed one.
- **Gap:** 4 levels

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

---

## C013

- **Record:** `g1v2h-acs-id-bannock` · family `interval` · mode indirect · compression none · split pooled_opus · `assessment/results/g1_v2_pooled_opus_reviewed.json` record 357
- **Evidence:** `assessment/evidence/g1/v2/holdout/acs-id-block1.indirect.indirect.g1-v2-2026-09-03.claude-opus-5.json`
- **Scorer level:** L0
- **Reviewer verdict:** genuine — genuine (D7): the value is restated at a coarser rounding than the source's (±$1,700 / ±$2,500 / ±$7,000 for 1,710 / 2,470 / 6,987); for Ada the scorer chose the '±2%' span over the table's ±$1,700 — both are L0
- **Rater level:** L3 — MOE restated as ±$2,500 (rounded from 2470) with 90% level and correct Bannock binding; rounding to hundreds is a legitimate transformation, not exact.
- **Gap:** 3 levels

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

---

## C046

- **Record:** `g1v2h-cchs113-laval-youth` · family `interval` · mode indirect · compression short · split control · `assessment/results/g1_v2_control_reviewed.json` record 41
- **Evidence:** `assessment/evidence/g1/v2/control/cchs113-qc-laval.indirect.indirect.short.g1-v2-2026-09-03.claude-haiku-4-5-20251001.json`
- **Scorer level:** unparseable
- **Reviewer verdict:** genuine — genuine omission: the qualifier is not stated in any form
- **Rater level:** L2 — Interval acknowledged only generically ("includes confidence intervals reflecting measurement uncertainty") with no bounds or width, so borderline L1; the "cautious interpretation" flag belongs to the reliability family, not this one.
- **Gap:** U given

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

---

## C057

- **Record:** `g1v2h-acs-id-bannock` · family `interval` · mode indirect · compression short · split control · `assessment/results/g1_v2_control_reviewed.json` record 10
- **Evidence:** `assessment/evidence/g1/v2/control/acs-id-block1.indirect.indirect.short.g1-v2-2026-09-03.claude-haiku-4-5-20251001.json`
- **Scorer level:** unparseable
- **Reviewer verdict:** genuine — genuine omission: no county's MOE value is stated
- **Rater level:** L2 — Existence-only mention ("each figure includes a margin of error") applied generically to all rows, no magnitude band or level; Bannock's estimate itself is only covered by the "$56,000 to $67,000" range.
- **Gap:** U given

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

---

## C004

- **Record:** `g1v2h-lfs-bc-employment` · family `interval` · mode indirect · compression short · split control · `assessment/results/g1_v2_control_reviewed.json` record 97
- **Evidence:** `assessment/evidence/g1/v2/control/lfs-2025-12-bc.indirect.indirect.short.g1-v2-2026-09-03.claude-haiku-4-5-20251001.json`
- **Scorer level:** unparseable
- **Reviewer verdict:** genuine — genuine omission: the qualifier is not stated in any form
- **Rater level:** L1 — The response only says "standard errors provided for measurement precision" generically, with no value, no verbal band, and no binding to the employment estimate, so the interval qualifier is effectively omitted for this row.
- **Gap:** U given

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

---

## C008

- **Record:** `g1h-das-dp-001` · family `vintage` · mode indirect · compression none · split control · `assessment/results/g1_v2_control_reviewed.json` record 52
- **Evidence:** `assessment/evidence/g1/v2/control/das-blockgroup-accuracy.indirect.indirect.g1-v2-2026-09-03.claude-haiku-4-5-20251001.json`
- **Scorer level:** L0
- **Reviewer verdict:** genuine — genuine: the 2021-06-08 file date is not stated (the scorer read the comparison year 2010 as the vintage — class mislabel, loss unchanged)
- **Rater level:** L2 — Response names "a privacy-protected version" of the 2010 data but drops the Demonstration file identity and its 2021-06-08 date; separately, the 450-person block-group threshold for this estimate is misbound to "200–250 people," which is outside the vintage family.
- **Gap:** 2 levels

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

---

## C020

- **Record:** `g1-das-dp-004` · family `dp` · mode indirect · compression tight · split pooled_opus · `assessment/results/g1_v2_pooled_opus_reviewed.json` record 125
- **Evidence:** `assessment/evidence/g1/v2/dev/das-plb-units.indirect.indirect.tight.g1-v2-2026-09-03.claude-opus-5.json`
- **Scorer level:** unparseable
- **Reviewer verdict:** genuine — genuine omission: the parameter is not stated in the compressed restatement
- **Rater level:** L1 — The response restates the epsilon estimate but neither rho (0.07) nor delta (10⁻¹⁰) appears in any form; the allocation clause loosely attributes the rho split to the epsilon budget but that is not a stated dp qualifier.
- **Gap:** U given

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

---

## C023

- **Record:** `g1-das-dp-001` · family `vintage` · mode indirect · compression tight · split pooled_opus · `assessment/results/g1_v2_pooled_opus_reviewed.json` record 119
- **Evidence:** `assessment/evidence/g1/v2/dev/das-county-accuracy.indirect.indirect.tight.g1-v2-2026-09-03.claude-opus-5.json`
- **Scorer level:** L0
- **Reviewer verdict:** genuine — genuine: the 2021-06-08 file date is not stated (the scorer read 2020 as the vintage — class mislabel, loss unchanged)
- **Rater level:** L2 — The as_of date 2021-06-08 is dropped; only the relative descriptor "newest" survives, which I treat as the verbal-band analogue for vintage, though the L2 definition is interval-shaped and fits vintage loosely.
- **Gap:** 2 levels

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

---

## C059

- **Record:** `g1v2h-lfs-bc-unemployment` · family `interval` · mode indirect · compression short · split control · `assessment/results/g1_v2_control_reviewed.json` record 99
- **Evidence:** `assessment/evidence/g1/v2/control/lfs-2025-12-bc.indirect.indirect.short.g1-v2-2026-09-03.claude-haiku-4-5-20251001.json`
- **Scorer level:** unparseable
- **Reviewer verdict:** genuine — genuine omission: the qualifier is not stated in any form
- **Rater level:** L1 — The response only says "standard errors provided for measurement precision" generically; no value, band, or binding to the unemployment estimate, so the interval qualifier is effectively omitted rather than verbally degraded.
- **Gap:** U given

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

---

