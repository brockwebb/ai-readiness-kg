# CC Task — scan-frame-fss: the whole federal statistical system as the frame, by rule, with its sources on the log

**Date:** 2026-09-08
**Project:** ai-readiness-kg
**Authored by:** Desktop session after the operator's frame decision (2026-09-08) and the OODA on `2026-09-08_scan_harness_v4_RESULT.md`.
**Fulfils:** its own ResearchTask (registered by `seldon cc register`). Precedes cycle 3, which runs over this frame. Precedes `report-draft`.
**Spend:** zero model calls. **Network, bounded and named:** (a) one fetch of the ICSP membership page(s) on `statspolicy.gov` for the roster, retained as evidence; (b) for each agency, the fetches the surface-selection rule needs (home, product listing, developer/API landing: at most ~5 GETs per agency); (c) pre-flight per host: `robots.txt` plus one HEAD on the home. Identified UA, 1 req/s per host, robots obeyed, one worker. **No scan cycle in this task**; the rules do not run against real hosts.

**Frame decision (operator, 2026-09-08; recorded here, not re-decided):**
- **Tier A, the frame:** the 16 OMB-recognized statistical agencies and units under CIPSEA 2018: the 13 principal statistical agencies (BEA, BJS, BLS, BTS, Census, ERS, EIA, NASS, NCES, NCHS, NCSES, ORES/SSA, SOI/IRS) plus the three recognized units (Microeconomic Surveys Unit / Federal Reserve Board; CBHSQ / SAMHSA; NAHMS / APHIS). Every one, no sampling. Source: statspolicy.gov "About" (30 ICSP members; 24 designated Statistical Officials; 16 recognized agencies and units) and the ICSP charter. Fetch and cite; do not type the roster from this file.
- **Tier B:** the departments of the remaining designated Statistical Officials that have no recognized unit (DoD, DHS, State, and the rest as the charter lists them). Machine entry point and `robots.txt` only; reported separately; never in a Tier A denominator.
- **No external comparators.** NIST, GSA, data.gov, StatCan are not producers of official statistics in this frame; a comparator row that is not the same kind of thing is coherence by decoration. data.gov enters as a **collector** (is the product registered in the federal DCAT catalog), not as a row. StatCan leaves the frame; its two cycles stay on the log, immutable, and are excluded from every FSS denominator from here on (numerically nothing changes: it was `error` on every leg both cycles).
- **Unit of analysis:** the surface. Agencies group surfaces. No agency score, no ranking.
- **Tier 0 headline** (`params.tier0.legs`): A4 robots.txt served, A5 discovery (with `sitemap`, `llms.txt`, `well-known` reported as separate counts from the observation fields A5 already records), A10 deep link and bogus route, A11-declared machine layer, A12 declare-vs-enforce (candidate, reported beside not inside), G1-D error fields present. Everything else runs and is reported below the fold.

**Zero edits to:** any rule module, `params.yaml` beyond the additions §1 names, any existing targets DataFile (a new one is created), events, the G1 harness, `assessment/cq/*.yaml`, framework content, prior cc_tasks and RESULTs.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-08_scan_frame_fss_ADDENDUM*.md` before starting.**

---

## 0. Housekeeping first
Fix the pre-existing red test `tests/test_scan_run_2.py::test_the_uncited_set_only_shrinks_and_only_by_citation` (v4 RESULT §7.2): the pre-cycle tracked set comes from git at the cycle's recorded commit, or the invariant is restated over a set recoverable from disk; say which and why. The suite must be fully green before §1.

## 1. Roster as evidence
`scripts/build_roster.py` fetches the statspolicy.gov membership page(s), retains the bodies as evidence (content-addressed, cited), parses the 16 recognized agencies and units and the designated Statistical Officials' departments, and writes `state/fss_roster_2026-09.json` registered as DataFile `fss_roster_2026-09` with the source URLs, fetch time and body digests on its face. Tier A count must be 16 by parse, not by assertion; Tier B count is whatever the source says. Register `fss_agencies_tier_a` = 16 and `fss_departments_tier_b`. For each Tier A entry record: canonical host(s), parent department, principal-vs-unit, and the agency home URL as linked from the source page.

## 2. Surface selection by rule, pre-registered
Add `params.frame` before any agency page is fetched:
- `machine_entry_point`: the first link from the agency home whose anchor or path matches the declared token list (`api`, `developers`, `data-access`, `open-data`, `datasets`); if none, `robots.txt`-adjacent well-known probing yields none and the agency records `no_machine_entry_point` as an observation, not a gap in the roster.
- `flagship_products`: the first `N = 3` product links, in the agency's own order, from the agency's product/data listing page, identified by a declared token list; the listing page body is retained and its digest plus each product's position on it are recorded on the target entry. Same rule for the three units within their subsite.
- Tier B: home and `robots.txt` only.
The rule is a function with tests on stored listing bodies (Census, BLS, and one unit). Where the rule finds nothing, the entry says so; no hand-picked fallback. Produce `state/scan_targets_fss_2026-09.json`, admitted through the existing admission path with `purpose: scan_surface` (no conversion-gap tasks may be emitted; assert), registered as DataFile `scan_targets_fss_2026-09` with `derived_from: fss_roster_2026-09`. Carry forward the 26 already-admitted cycle-1 surfaces where the rule selects them again; record which cycle-1 surfaces the rule would not have selected (they stay admitted for history, out of the new target list).

## 3. Pre-flight over the full frame
`preflight.py` over every Tier A and Tier B host: `robots.txt` (status, bytes, whether the identified UA is permitted on `/`) and one HEAD on the home. Register per host `scan_preflight_<host>_reachable_2026-09` (1/0) and `_robots_status_2026-09`, plus `fss_hosts_refusing_identified_client_2026-09` and `fss_hosts_unreachable_2026-09` with the host list on the Result description. A refusal is a measurement, not a blocker; the task does not retry with any other identity.

## 4. Tool map, generated
`scripts/scan_tool_map.py` reads `params.yaml`, the collectors package and `rules.CURRENT` and emits `docs/design/scan_tool_map.md`: one row per collector (library used, request pattern, fields recorded, evidence retained) joined to the indicator(s) and rule(s) it serves. A second table lists indicators in `specified` state with a one-line verdict per indicator: `scan-observable` (name the collector that would serve it), `content-evaluation` (needs the second instrument), or `not web-observable`. Gaps a crawl-tool user would expect and that an open-source collector fills (sitemap crawl and URL inventory, schema.org `Dataset` extraction, OpenAPI detection, response headers, federal DCAT catalog presence via data.gov's catalog API) are named in a third table with the indicator each would serve. **Named, not built.** The document is regenerated by the script; hand edits are refused by a test that diffs regeneration against the checked-in file.

## 5. Two design decisions, appended (next free numbers; read the file)
- Frame: Tier A / Tier B as above, no external comparators, unit of analysis, StatCan exclusion, and the surface-selection rule as the sampling statement.
- Client identity: UA becomes `ai-readiness-kg-scanner/0.2 (+https://github.com/brockwebb/ai-readiness-kg)`, one identity, contact URL per RFC 9309 practice; refusals are findings. Cadence: monthly cycles from cycle 3, first Monday UTC, run by the existing launchd pattern **after** cycle 3 validates the full frame; no scheduler installed by this task.

## 6. Gate (the one gate of this task)
`tests/test_scan_frame.py`: roster Tier A parses to 16 from the retained body; every target entry carries its listing digest and position; zero conversion-gap tasks emitted by admission; pre-flight Results exist for every roster host; tool map regenerates byte-identically; full suite green; `git status --porcelain corpus/` shows only the roster and listing bodies this task cited. **Failure registers nothing further and reports.**

## 7. Report
RESULT `cc_tasks/2026-09-08_scan_frame_fss_RESULT.md`: gate first; the roster table with source; the target list with per-agency counts and the rule's misses; pre-flight matrix (reachable / robots / permitted) for all hosts; the `specified`-indicator verdict table from §4; every premise this task got wrong; what cycle 3 needs. `seldon verify`, `git diff` empty on protected paths. `seldon cc complete`; commit, push.

**SEQUENCING:** §0 → §1 → §2 → §3 → §4 → §5 → §6 (hard stop) → §7.
