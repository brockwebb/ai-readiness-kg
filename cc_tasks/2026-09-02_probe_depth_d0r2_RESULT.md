# RESULT — Grow the harness probes toward the Machine Diagnostic: the four D0-r2 defects

**Task:** `cc_tasks/2026-09-02_probe_depth_d0r2.md` · **Executed:** 2026-09-02 · **Spend:** zero model
tokens. Code, fixtures, tests, README, this file.

**Addenda:** globbed `cc_tasks/2026-09-02_probe_depth_d0r2_ADDENDUM*.md` and
`assessment/cc_tasks/*_ADDENDUM*.md` at start: **none exist**. Read
`assessment/cc_tasks/2026-09-01_web_surface_enumeration_and_intermittency.md`, its `_TASK_LOG.md`,
and `assessment/cc_tasks/2026-09-02_followup_from_census_web_concept_inventory_d0r3.md` as
instructed. Source of the defects: `census-web-concept-inventory/cc_tasks/2026-09-01_d0_r2_task_log.md`
§"Four probe-design findings routed to the harness" (read-only; nothing in that repo was edited).

**Verification:** `cd assessment && python -m pytest tests/ -v` → **238 passed** (was 156; +82).
Root suite `python -m pytest tests/ -q` → **594 passed**, unchanged. No test touches the network:
no `HttpFetcher` is instantiated anywhere under `assessment/tests/`, every probe is scored from a
fixture through `FakeFetcher`, and no probe was run against live census.gov or any live host.

## 1. Premise check — the D0-r2 four vs the task's four

The D0-r2 log names `d2_no_barriers` (single fetch), `d1_robots`, `d1_sitemap`, `d1_catalog`. The
task file restates the first as the declared/enforced/observed triad. That is the right rewrite:
the June task (2026-09-01, TASK_LOG "Change 3") already made `d2_no_barriers` multi-attempt with a
refusal fraction, so the single-fetch defect was closed before this task began. Recorded here so the
count reconciles: **three of the D0-r2 four were open; the fourth had been replaced by the triad,
which builds on the June fix rather than repeating it.**

## 2. The four defects, restated, with what was already done and what was done here

### Defect 1 — `d1_robots` reads robots.txt only, never meta robots or `X-Robots-Tag`
*Restated:* the site-level probe scored census.gov PASS while 77 of 98 sampled QuickFacts pages
carried a `nofollow` meta robots directive that no probe read.
*Already done:* nothing.
*Done here:* new page-level probe `harness/probes/d1_robots_directives.py` (`d1_robots_directives`,
D1, web surface only). Per fetched page it records `robots_meta` (every `<meta name="robots">` plus
any bot-specific meta: names ending in `bot`, plus the configured list for tokens that do not, e.g.
`slurp`) and `x_robots_tag` (header, token-prefixed pieces kept per token, valued directives such as
`max-snippet:-1` not mistaken for tokens). A configured discovery-blocking directive (`noindex`,
`nofollow`, `none`) scores PARTIAL with the directive as evidence; clean PASS; unretrievable FAIL.
`d1_robots` (robots.txt eligibility) is unchanged. Applies to `SOURCE_SITEMAP` only: a catalog
distribution is not a page intended for discovery.

### Defect 2 — `d1_sitemap` reads the fixed path `/sitemap.xml` and has no non-stale condition
*Restated:* the probe scored census.gov PASS on a fixed-path document of 5,408 entries dated
2013–2015 while robots.txt declared a different index yielding 53,943 current URLs.
*Already done (June):* the **enumerator** follows the robots-declared sitemap and records drift
against `agencies.toml` (`resolve_sitemap_url`, `parse_robots_sitemaps`, case-insensitive); `lastmod`
is parsed per URL. The **probe** still read the fixed path and had no staleness rule.
*Done here:* `harness/probes/d1_sitemap.py` rewritten. `resolve()` follows robots.txt (reusing
`parse_robots_sitemaps`, so the enumerator and the probe cannot disagree about which document the
site declares) and falls back to the fixed path with `sitemap_source: fixed_path_fallback`. When the
declared sitemap is not the fixed path the runner fetches both; the fixed path is reported as
`sitemap_divergence` (entry count, newest lastmod, stale flag, `same_document`) and never scored.
Staleness: newest `lastmod` in the document read, older than `[probes.d1_sitemap] stale_after_days`
(config, default 365) → PARTIAL with that lastmod as evidence; observations `sitemap_lastmod`,
`sitemap_lastmod_count`, `sitemap_stale_warning` (rule `sitemap_stale` v1, threshold and evaluation
date recorded). `today` is injectable, so staleness is fixture-testable. A document with **no**
`lastmod` is recorded `sitemap_lastmod: null`, `determinable: false`, and not scored stale (§5).

### Defect 3 — `d1_catalog` scores presence and validity, not coverage
*Restated:* census.gov/data.json scored PASS with 1,798 distributions all on api.census.gov and zero
references to QuickFacts, 21.8% of the site's own sitemap universe.
*Already done (June):* the evidence-only `catalog_completeness` signal, which is a different
measure (pages *with Dataset markup* absent from the catalog) and was `null` on Census because no
sampled page carried markup.
*Done here:* `catalog_sitemap_coverage` in `harness/run.py`: of **every** URL the enumerated sitemap
declares (the full universe, not the probed sample; `WebSurfaceResult.universe_by_section` now holds
it in memory), the fraction the catalog references as a distribution `downloadURL`/`accessURL` or a
dataset `landingPage`. Numerator, denominator, per-section counts and `sections_with_zero_coverage`
are explicit; a zero denominator reads `null`, never `0.0`. Attached to the `d1_catalog` record's
`observations` and to `enumeration.web_surface.catalog_coverage`; the `d1_catalog` record is now
written after enumeration so the fact rides on it. **The score is unchanged** (§5, open item).

### Defect 4 — no declared / enforced / observed access triad (skeleton A11)
*Restated:* the harness could say a page was refused but not whether robots.txt had promised
access, so a policy/enforcement mismatch was invisible as such.
*Already done (June):* the multi-attempt machinery and refusal fraction in `d2_no_barriers`, which
the observed leg reuses without adding a request.
*Done here:* `harness/crawler_access.py` (pure). `declared`: robots.txt eligibility of the target
per token via stdlib `urllib.robotparser` (RFC 9309 semantics; prior art, not reinvented), for
`[probes.crawler_access] declared_user_agents` plus the harness's own identity, zero requests.
`observed_public`: per identity, the outcome of each attempt (served / refused / challenge /
unreachable; 401/403/429 from config; bot-management interstitial markers), collapsed to
`served|refused|challenge|unreachable|mixed` with per-attempt outcomes, statuses and refusal
fraction kept. `enforced`: documented hook — an optional per-agency
`enforced_observations_file` (`agencies.toml`, schema `enforced_observations/1`, path relative to
the config dir), loaded and validated fail-loud before any request, merged per URL and token; null
with a note otherwise. **No Cloudflare or other vendor reader.** `effective_crawler_access` is the
fact; `crawler_policy_mismatch_warning` is the versioned rule (`crawler_policy_mismatch` v1): fires
when a token is declared **allow** and observed **refused/challenge on any attempt**, listing
`declared_vs_observed_mismatch`; the reverse (disallowed but served) is recorded as
`declared_disallowed_but_served` without firing. Both attach to the `d2_no_barriers` record on both
surfaces. `observe_user_agents` (default **empty**) lists extra identities the harness will send
(`Fetcher.get(..., user_agent=)` added; each costs `attempts` requests per target); by default no
request goes out under any identity but the harness's, which keeps the June politeness stance (no
third-party crawler token) until an operator decides otherwise per run.

## 3. Discipline items

- **Fetch/evaluate separation.** Every new evaluator is pure and takes fixtures: `RobotsDirectivesProbe.evaluate/observe`, `SitemapProbe.resolve/evaluate` (with injectable `today` and an optional already-fetched fixed-path document), `catalog_sitemap_coverage`, and every function in `crawler_access.py`. The runner does all fetching.
- **Evidence emission.** `ProbeResult` gained `observations: dict` (serialized in `to_dict`, JSON round-trip tested), kept apart from `evidence` (raw artifact) and from warnings, per skeleton §6b.5. Field names used verbatim from the task's list: `robots_meta`, `x_robots_tag`, `sitemap_lastmod`, `sitemap_source`, `effective_crawler_access`, `crawler_policy_mismatch_warning`. Evidence files gained labelled sections for the fixed-path comparator, the coverage fact, the triad, and per-identity attempts. Probes may now return `(score, evidence, observations)`; `probes.base.unpack_verdict` accepts both shapes so untouched probes are untouched.
- **Config-not-constants.** New `harness.toml` sections `[probes.d1_sitemap]`, `[probes.d1_robots_directives]`, `[probes.crawler_access]`; `agencies.toml` documents `enforced_observations_file`. `HarnessConfig` loads and validates each (fail-loud, key named). `run_agency` now takes a required keyword `settings: ProbeSettings` built from config, so no probe is constructed on a value living in source; `SitemapProbe` and `RobotsDirectivesProbe` refuse to build without their config values. Existing pattern followed for the other run kwargs.
- **No self-attested input.** Every new observation is read from a fetched artifact, robots.txt, or the operator's edge file; the edge file is labelled `enforced` and never scored.
- **Zero-dependency invariant held:** `urllib.robotparser`, `html.parser`, `xml.etree`, `datetime`, `json`.

## 4. Fixtures (all under `assessment/tests/fixtures/`)

| fixture | reproduces |
|---|---|
| `robots_census_shaped.txt` | census.gov shape: `*` allows `/quickfacts/`, `usasearch` disallows it, uppercase `SITEMAP:` to a non-fixed path |
| `page_quickfacts_nofollow.html` | the D0-r2 case: `<meta name="robots" content="nofollow" />` plus a `googlebot` meta with valued directives |
| `page_clean_no_directives.html` | clean case for defect 1 |
| `sitemap_fixed_path_stale.xml` | the fixed-path case: lastmods 2013–2015 in three W3C forms, one entry without |
| `sitemap_index_current.xml` | clean case for defect 2: declared index, recent lastmod, one child without |
| `data_json_census_shaped.json` | defect 3: all distributions on an API host, one `landingPage` into the web surface |
| `enforced_observations_sample.json` | the enforced-layer hook's documented schema |

The QuickFacts-shaped triad case (statuses `403, 200, 403, 403, 403`) and the clean case are built
inline in `test_crawler_access.py` from `tests.helpers.fetched`. `FakeFetcher` gained a per-identity
response map (`responses[(url, user_agent)]`) and records the identity on each call, so a test can
assert that no third-party identity was sent.

## 5. Open items (registered, not decided here)

1. **Coverage scoring rule.** `catalog_sitemap_coverage` is an observed fact and does not move `d1_catalog`'s score. Whether a catalog that references 0% of a section, or below some fraction of the universe, should score PARTIAL is an operator decision (assessment protocol §3). Proposed rubric amendment to `benchmark_rubric.md` (not edited): D1 catalog gains a coverage clause once a threshold is chosen.
2. **Enforced-layer hook.** Schema `enforced_observations/1` is documented in `agencies.toml` and validated in code; producing the file from Cloudflare or any edge is an operator step. No vendor reader was built.
3. **Sitemap with no `lastmod`.** Recorded null and not scored stale. Whether absence of freshness metadata is itself a D1/D4 deficiency is a rubric decision. Proposed rubric amendment: state it either way.
4. **Sitemap index staleness reads the document fetched.** For a `sitemapindex`, the newest `<sitemap><lastmod>` decides; child `urlset` lastmods are not walked by the probe (the enumerator already fetches children; walking them twice would double the requests). An index that omits child lastmods therefore lands in item 3. A future pass could hand the enumerator's per-URL lastmods to the probe.
5. **Observed leg per named identity is opt-in.** `observe_user_agents` defaults to empty; the live question "does the edge treat GPTBot differently from the harness" is answerable by config, and running it is a politeness decision per run.
6. **Success contract.** Not written; this repo's CLAUDE.md does not require one and the task file's "required behavior" section served as the contract.

## 6. Files

**New:** `assessment/harness/crawler_access.py`, `assessment/harness/probes/d1_robots_directives.py`,
`assessment/tests/test_robots_directives.py` (17), `assessment/tests/test_sitemap_declared.py` (22),
`assessment/tests/test_catalog_coverage.py` (8), `assessment/tests/test_crawler_access.py` (24), the
seven fixtures in §4, this file.
**Modified:** `assessment/harness/probes/d1_sitemap.py` (rewrite), `d2_no_barriers.py`
(observations), `base.py` (`unpack_verdict`, contract note), `records.py` (`observations`),
`fetch.py` (`user_agent` override), `config.py` (new keys, `_string_list`, agency hook),
`enumerate_sitemap.py` (`universe_by_section`), `run.py` (`ProbeSettings`, `site_probes`,
`page_probes`, `catalog_reference_urls`, `catalog_sitemap_coverage`, site loop, `_probe_target`),
`config/harness.toml`, `config/agencies.toml`, `README.md`, `tests/helpers.py`,
`tests/test_config.py` (+11), `tests/test_runner.py`, `tests/test_site_probes.py`,
`tests/test_barrier_intermittency.py` (signature updates only).
**Untouched, by constraint:** the burn, ledger, manifest, event log, `benchmark_rubric.md` and the
other June documents, `docs/crosswalk/usafacts_operationalization_skeleton.md`,
`census-web-concept-inventory`.

Not committed by this session: the dispatching session commits these files together with its
sibling tasks.
