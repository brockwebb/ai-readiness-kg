# ERRATUM-01 to `docs/research/2026-09-02_g1_eval_prior_art.md`

**Issued:** 2026-09-03, task `cc_tasks/2026-09-03_g1_eval_v1_parser_fullgrid_errata.md` step 1. **Corrects:** memo §2.3 (StatCan row) and, by consequence, memo §4.5. The memo is not edited; this file is the correction of record and is registered as a Seldon DesignNote linked to the memo's DesignNote (`g1_eval_prior_art_memo`).

## What the memo says

§2.3, row *Statistics Canada 2019. Quality Guidelines, 6th ed. (12-539-X)*: "CV as the published accuracy measure; reliability bands; suppression rules" with the transfer line "Gives G1 a CV-class qualifier and a *suppression* class (an estimate the producer would not publish at all)". §5's web-search log row for the query "Statistics Canada Quality Guidelines communicating sampling variability coefficient of variation …" records "StatCan 12-539-X 6e (admitted); CV bands 16.6 % / 33.3 %". §4.5 then fixes as a design constraint: "StatCan CV bands and suppression. A restatement that keeps an estimate the producer would have suppressed is its own failure class (source: StatCan 6e)."

## What is wrong

The CV bands (acceptable ≤ 16.5 %, marginal 16.6–33.3 %, unacceptable > 33.3 %) and the suppression rule attached to them were read from a **web-search snippet** in that §5 row, not from the held text. The held copy of 12-539-X 6e (`corpus/g1eval/statcan-quality-guidelines-6th-edition.pdf`, 49 pages, pypdf 153,213 characters) names "coefficient of variation, margin of error or confidence interval" as accuracy measures and "suppress" only as a disclosure-control process step; it carries no band, no letter flag and no suppressed cell. A full-text scan of every admitted document with a local file (207 of 211 at the time) found the bands and the rule in **no** admitted document (v0 RESULT `cc_tasks/2026-09-02_g1_eval_probe_family_v0_RESULT.md` §9.2; F7 addendum §4).

The bands are real. They live in Statistics Canada's **product-level user guides** — e.g. *Guide to the Labour Force Survey* (71-543-G) §7, "Category 1 – If the CV is ≤ 16.5 % – no release restrictions … Category 2 – > 16.5 % and ≤ 33.3 % – release with caveats … Category 3 – > 33.3 % – not recommended for release" — and in the LFS methodology report (71-526-X, ch. 8), not in 12-539-X. Those guides are step 2's acquisition target of the task that issues this erratum.

## What this withdraws, and until when

1. The memo's §2.3 transfer line for 12-539-X 6e is reduced to: *process guidance naming CV, MOE and CI as the accuracy measures to publish; no bands, no suppression rule.* The row's "measures / defines" cell should read "quality-assurance process guidance", not "CV as the published accuracy measure; reliability bands; suppression rules".
2. Memo §4.5's clause "StatCan CV bands and suppression" is **unsupported by held text** and is withdrawn as a constraint until a product guide stating the bands is admitted. The design consequence already recorded in DD-033 stands: the G1 fixture SUPPRESSION class was empty and RELIABILITY_FLAG below floor in v0 because of this.
3. Nothing else in the memo changes. The F7 addendum's §4 already recorded the finding; this erratum makes the correction attributable to the memo row that carried the claim.

## Cause

A snippet-sourced fact was entered into a findings table whose every other row was written from a held document, with no marker distinguishing the two. The remedy applied going forward (this task's step 2 and DD-034): a claim about what a document *contains* is grounded in the held text or marked `snippet`, never mixed.
