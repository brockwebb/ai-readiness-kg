# CC Task: Grow the harness probes toward the Machine Diagnostic — the four D0-r2 defects

**Date:** 2026-09-02
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-02_probe_depth_d0r2_ADDENDUM*.md` files. Also read `assessment/cc_tasks/*_ADDENDUM*.md` and `assessment/cc_tasks/2026-09-01_web_surface_enumeration_and_intermittency*.md` (the June task line, now in-repo), because two of the four defects may already be absorbed there.**

## Context

`assessment/harness/` is the public-tier reference implementation (DD-031, `docs/crosswalk/assessment_protocol.md` §9). census-web-concept-inventory's D0-r2 run against QuickFacts filed four probe-design defects. The SEO Machine Diagnostic constructs now stubbed as A10/A11 in the skeleton are the specification the probes grow toward. This task closes the four defects, verify-first.

Source of the defects: search `/Users/brock/GitHub/census-web-concept-inventory` for the D0-r2 report and its harness-findings section (read-only; do not edit that repo). Restate each defect in the RESULT in one sentence before fixing it.

## The four defects and the required behavior

1. **`d1_robots` reads only robots.txt; never reads meta robots or `X-Robots-Tag`.** Required: the probe records, per fetched page, the `<meta name="robots">` content and any bot-specific meta, and the `X-Robots-Tag` header; `noindex`/`nofollow` on a page intended for discovery is a `partial` with the directive as evidence. Robots.txt eligibility stays as-is.
2. **`d1_sitemap` reads the fixed path `/sitemap.xml` and has no non-stale condition.** Required: the probe follows the sitemap declared in robots.txt; if none is declared, fall back to the fixed path and record `sitemap_source: fixed_path_fallback`. Divergence between a robots-declared sitemap and the fixed-path one is reported as evidence. Staleness: a sitemap whose newest `lastmod` is older than a configured threshold (config value, not a constant; default 365 days) scores `partial`, with the newest lastmod as evidence. Verify first whether the June web-surface task already did part of this; do not redo what is done.
3. **`d1_catalog` scores presence and validity, not coverage.** Required: keep the existing pass/partial/fail on resolve+validate. Add a coverage observation: the fraction of sitemap-declared product URLs (from the web-surface enumeration) that appear as a distribution or landing page in the catalog. Coverage is reported as an observed fact with its numerator and denominator; it does not change the score in this task (the scoring rule for coverage is an operator decision, per assessment protocol §3, and is registered as an open item in the RESULT).
4. **No declared / enforced / observed access triad.** The harness is public-tier, so `enforced` (edge logs) is out of reach. Required: implement `declared` (existing robots eligibility per crawler UA) and `observed_public` (what the harness's own requests receive per UA: 200 / 403 / 429 / challenge page, using the multi-attempt intermittency machinery already present), and emit a `declared_vs_observed_mismatch` fact when robots.txt allows a UA that the observed requests refuse. Leave a documented hook for `enforced` (an optional edge-observation input file) but do not implement a Cloudflare reader.

## Discipline

- Fetch/evaluate separation: every new evaluator takes a fixture; every defect gets at least one fixture reproducing the QuickFacts-shaped case and one clean case.
- Evidence emission: new observations appear in the per-probe evidence record with field names drawn from the SEO Machine Diagnostic data dictionary where one exists (`robots_meta`, `x_robots_tag`, `sitemap_lastmod`, `sitemap_source`, `effective_crawler_access`, `crawler_policy_mismatch_warning`), so a future item-level crosswalk lines up.
- Thresholds are config values in the existing agency/probe config files, never constants.
- Config-not-constants and no-self-attested-input invariants are unchanged.
- `cd assessment && python -m pytest tests/ -v` must pass; report the count. Root suite unchanged.
- Do not run probes against live census.gov as part of tests; live runs are a separate operator decision.

## Constraints

Zero model calls. Do not touch the burn, ledger, manifest, or event log. Do not edit `benchmark_rubric.md` or the other June documents; if a rubric text change is implied, list it in the RESULT as a proposed rubric amendment.

## Completion

RESULT at `cc_tasks/2026-09-02_probe_depth_d0r2_RESULT.md` with the four defect restatements, what was already done vs. done here, fixture list, open items (coverage scoring rule; enforced-layer hook). `seldon cc complete`; commit and push.
