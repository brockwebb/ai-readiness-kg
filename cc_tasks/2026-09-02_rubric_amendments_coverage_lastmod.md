# CC Task: Rubric amendments from the D0-r2 probe task — catalog coverage clause and sitemap-without-lastmod clause

**Date:** 2026-09-02
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-02_rubric_amendments_coverage_lastmod_ADDENDUM*.md` files.**

## Context

`cc_tasks/2026-09-02_probe_depth_d0r2_RESULT.md` §5 registered two rubric decisions as open (items 1 and 3). They are decided here on the following grounding; the operator overrides by addendum if wrong.

**Decision 1 — catalog coverage.** A section of the enumerated sitemap universe with **zero** catalog references (`sections_with_zero_coverage` non-empty) scores `d1_catalog` **PARTIAL**, evidence: the section name and its denominator. This is categorical absence and needs no threshold. A *fractional* coverage threshold is **deferred** until the January pilot (3–5 products, `docs/crosswalk/deck_content_2026-09-01.md` slide 18) yields an observed distribution of `catalog_sitemap_coverage`; setting a fraction now would be a threshold chosen before data. The fraction is registered as an open rubric item with that trigger.

**Decision 2 — sitemap without `lastmod`.** Not scored stale and not scored PARTIAL. `lastmod` is optional in the sitemap protocol; penalizing a protocol-compliant sitemap would be scoring a hypothesis about machine behavior by vintage, which the orientation-first rule forbids. It is recorded as an observed fact (`sitemap_lastmod: null`, `determinable: false`) and the rubric states explicitly that freshness-metadata absence is a D4-class observation carried into the evidence record, unscored, pending observed-behavior evidence that crawlers treat lastmod-less sitemaps differently.

## Steps

1. Read `assessment/benchmark_rubric.md` and the D1 catalog and D1 sitemap entries. Restate their current text in the RESULT.
2. Amend D1 catalog with the zero-coverage clause (Decision 1) and register the fractional threshold as an open item in the rubric's own open-items section (create the section if none exists), with the pilot trigger.
3. Amend D1 sitemap with the no-lastmod clause (Decision 2).
4. Bump the rubric version marker per its own convention and record both amendments in its changelog with this task's filename. Versioned rules in code (`sitemap_stale` v1, `crawler_policy_mismatch` v1) are unchanged.
5. Implement Decision 1 in `assessment/harness/run.py` (or wherever `d1_catalog`'s score is assembled after `catalog_sitemap_coverage` is attached): zero-coverage section → PARTIAL, existing pass/fail on resolve+validate otherwise. Fixture: the census-shaped `data_json_census_shaped.json` case (one section with zero references) → PARTIAL; a clean case → unchanged. `cd assessment && python -m pytest tests/ -v` passes; report the count.
6. `seldon verify` clean.

## Constraints

Zero model calls. No other rubric text changes. Do not touch the burn, ledger, manifest, or event log.

## Completion

RESULT at `cc_tasks/2026-09-02_rubric_amendments_coverage_lastmod_RESULT.md`; `seldon cc complete`; commit and push.
