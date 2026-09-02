# RESULT: Rubric amendments from the D0-r2 probe task — catalog coverage clause and sitemap-without-lastmod clause

**Task:** `cc_tasks/2026-09-02_rubric_amendments_coverage_lastmod.md`
**Date:** 2026-09-02
**Addenda:** none (glob `2026-09-02_rubric_amendments_coverage_lastmod_ADDENDUM*.md` matched nothing).
**Model calls:** 0.

## 1. Premise check

- `cc_tasks/2026-09-02_probe_depth_d0r2_RESULT.md` §5 items 1 and 3 are as the task states: coverage rule open, no-`lastmod` open.
- **Discrepancy:** the task says "bump the rubric version marker per its own convention." `assessment/benchmark_rubric.md` had **no version marker and no changelog** (grep for `version|changelog` returned nothing; the file's only git history is the subtree import `4209e23`). The convention was created here: the pre-amendment text is declared **v1.0**, this task makes **v1.1**, and a `## Changelog` section was added. Reported, not silently reconciled.
- `benchmark_rubric.md` is not a Seldon-tracked artifact (zero mentions in `seldon_events.jsonl`), so no `seldon paper sync` step applied; `seldon verify` was run anyway (§6).

## 2. Rubric text before amendment (restated verbatim)

D1 table rows as they stood (v1.0):

```
| sitemap.xml | Present, parses, non-stale |
| Structured catalog | data.json (Project Open Data) / DCAT resolves & validates |
```

Open items section had no entry for either decision; the last two entries were the two unchecked Stage-3 items (probe implementation, target list).

## 3. Amendments applied (rubric v1.1)

**Decision 1 — D1 catalog, zero-coverage clause.** Appended to the Structured catalog row: a section of the enumerated sitemap universe with zero catalog references (`catalog_sitemap_coverage.sections_with_zero_coverage` non-empty) scores PARTIAL; evidence is the section name and its denominator; rule `catalog_zero_coverage` v1; categorical, no threshold. Fractional threshold deferred to Open items.

**Open item registered — fractional coverage threshold (DEFERRED).** Trigger: the January pilot (3–5 products, `docs/crosswalk/deck_content_2026-09-01.md` slide 18) yields an observed distribution of `catalog_sitemap_coverage`; the threshold is set from that distribution and recorded with its derivation. Until then the fraction is evidence only.

**Decision 2 — D1 sitemap, no-`lastmod` clause.** Appended to the sitemap.xml row: no `lastmod` on any entry is neither stale nor PARTIAL, because `lastmod` is optional in the sitemap protocol and penalizing a protocol-compliant sitemap would score a hypothesis about machine behavior by vintage (orientation-first rule). Recorded `sitemap_lastmod: null`, `determinable: false`; freshness-metadata absence is a D4-class observation carried into the evidence record, unscored, pending observed-behavior evidence that crawlers treat lastmod-less sitemaps differently.

**Version and changelog.** Header now carries `Rubric version: v1.1 (2026-09-02)` plus the convention statement; `## Changelog` added with the v1.1 entry naming this task file and a v1.0 baseline entry. Both decisions also appear as resolved `[x]` entries under Open items. `sitemap_stale` v1 and `crawler_policy_mismatch` v1 are unchanged.

No other rubric text was changed (diff is the header block, the two D1 rows, three Open-items lines, and the Changelog section).

## 4. Harness implementation (Decision 1), test-first

**Red first.** Tests were written before code; the suite failed at collection with `ImportError: cannot import name 'COVERAGE_RULE_ID' from 'harness.run'`, then (after a missing `Score` import in `run.py`) 17 failures, then green.

**Code (`assessment/harness/run.py`):**
- `COVERAGE_RULE_ID = "catalog_zero_coverage"`, `COVERAGE_RULE_VERSION = 1` — versioned like `sitemap_stale` so a re-score names the rule.
- `apply_catalog_coverage_rule(score, evidence, coverage) -> (score, evidence, warning)`: fires only when the coverage fact is `applicable` (catalog present, sitemap universe enumerated) and `sections_with_zero_coverage` is non-empty; lowers PASS → PARTIAL and appends `section <name>: 0 of <denominator> sitemap URLs referenced` to the evidence string. It never raises a score (a probe PARTIAL/FAIL is left alone) and is `determinable: false` with no universe. The warning record (`rule_id`, `rule_version`, `fired`, `determinable`, `sections_with_zero_coverage: [{section, sitemap_urls}]`) is always attached as `observations.catalog_coverage_warning`, whether or not it fired.
- The runner applies the rule where the held `d1_catalog` record is finalized after enumeration; the evidence file gains a `ZERO-COVERAGE RULE:` block.
- `catalog_sitemap_coverage`'s fact keys `evidence_only`/`scored` (both now false claims) replaced with `fraction_scored: False` and `zero_coverage_rule: "catalog_zero_coverage/1"`; its note and docstring updated. No config value was added: the rule is categorical, so there is nothing to tune.

**Tests (`assessment/tests/test_catalog_coverage.py`):**
- Census-shaped fixture (`data_json_census_shaped.json`, one section `PST045217` with 0/3 references) through the runner → **PARTIAL**, evidence names `PST045217` and `0 of 3`, warning `fired: true`.
- Clean case (same fixture plus a dataset whose `landingPage` is a QuickFacts URL, so every section is referenced) through the runner → **PASS unchanged**, warning `fired: false`.
- Pure-rule tests: demotion with section+denominator; not-fired on clean universe; not-determinable without a universe; never raises FAIL/PARTIAL; missing catalog does not fire.
- No-universe runner case additionally asserts PASS and `determinable: false`.

**Counts.** `cd assessment && python -m pytest tests/ -v`: **238 passed** before, **243 passed** after (5 new tests, 0 removed; one renamed: `test_the_probe_score_is_unchanged_by_coverage` → `test_the_probe_itself_still_scores_presence_and_validity_only`, same assertion).

## 5. Documentation kept in step

- `assessment/README.md` "Observed facts beside the score": the sitemap no-`lastmod` line and the catalog-coverage bullet now state the v1.1 rules instead of "open rubric item".
- `assessment/harness/probes/d1_sitemap.py` module docstring: the "registered as an open item, not decided here" sentence replaced with the v1.1 clause. No logic change in that probe.

## 6. Verification

- `seldon verify`: **All checks passed.**
- Burn state, ledger, manifest, event log: untouched.

## 7. Files

Modified: `assessment/benchmark_rubric.md`, `assessment/harness/run.py`, `assessment/tests/test_catalog_coverage.py`, `assessment/README.md`, `assessment/harness/probes/d1_sitemap.py`.
Created: this file.
