# CC Task: existence is read from known locations and discoverability becomes its own indicator; the three false passes the recollection exposed are fixed (part 1 of 2, no fetch)

**Date:** 2026-10-07
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from DN-013 §1 (R1) and `cc_tasks/2026-10-06_absence_verdicts_recollection_RESULT.md` §1, §2, §5 and its "Next" line. DN-013 named one file for R1. It is split in two because R1 needs new fetches against agency hosts and the operator reserves rescans to himself (the recollection's launch rule, DN-012 d6): this part writes the rules, the indicator, the seed table and one no-fetch re-judgement, and runs under the dispatcher; part 2, `2026-10-07_seed_known_locations_verify.md`, verifies the seeds by fetch and freezes the numbers, and is operator-launched.
**Implements:** DN-013-R1; the recollection RESULT's "Next" (A2 and D1 rule defects); its §5.5 (the A3 false pass).
**Framework layer served (DN-005 §5 rule 1):** §2.2, measurement; §2.1 for the new candidate indicator.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** 2026-10-06_absence_verdicts_recollection_v2, 2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict
**Spend:** est. 2.5M tokens (Opus). Rule work, fixtures, the seed table, one re-judgement, the views, the suite. No harness model call.
**Network:** none beyond git push. Nothing is fetched; every verdict here is judged from stored Observations.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Read first
DN-013 §1 in full; the recollection RESULT; `docs/research/2026-10-06_absence_rules_inventory.md`; `docs/design/scoring_model.md` lines 140 to 160 (candidate and frontier legs enter no level and no score); `docs/design_decisions.md` DD-054 (the candidate path) and the promotion rule near line 958.

## Decisions

1. **The three false passes, fixed as new rule versions.** Every predecessor stays in `REGISTRY`, unedited. Each fix lands with a fixture that reproduces the false pass from the stored body, and the fixture fails against the old version.
   - **A2** (`v2clauses.api_declarations`): a JSON body is an API description only when it carries the top-level `openapi` field (OpenAPI Specification 3.x, where it is REQUIRED) or `swagger` (Swagger/OpenAPI 2.0). A `dcat:Catalog` such as `https://api.census.gov/data` is an API's data catalog, not its description: A2 reads it as "API present, description not published at the base", which is a finding, not a pass. Fixture: the stored `api.census.gov/data` body.
   - **D1**: licence and terms tokens are matched on the page's visible text (scripts, styles and attributes removed), at word boundaries, case as the token's convention requires. Fixtures: census.gov's `CC0` inside a script hash; eia.gov's `MIT` inside "permit" and "Limit".
   - **A3**: the "unfiltered file" branch does not pass a response whose Content-Type is `text/html` or whose body sniffs as HTML. Fixture: `https://www.bea.gov/` as stored.

2. **Re-judge, no fetch.** `scan_2026-10-06_recollect` is re-judged under decision 1 as `scan_2026-10-06_recollect_rj1`, and `scan_2026-09-10_rj5` is re-judged for A3 only if A3 is taken from it in the composite. A new composite, `scan_2026-10-07_composite_c`, takes A2 and D1 from `_rj1` (the legs `_composite_b` withheld) and states that it does. Publish, project, regenerate the views as the recollection did, with every `--check` passing. Report the delta per leg.

3. **The existence/discoverability split, as rules (DN-013-R1).** Written and fixture-tested here; judged on live evidence in part 2.
   - **Existence legs** are A2 (an API exists), D1 (the API's terms exist, applicable when an API exists), F4 (a changelog exists), D4 (the body's products are listed in an inventory it publishes or that data.gov harvests) and D4's consumers B1, B4, D3, G4. Each reads only declared or seeded locations; the link probe, the guessed paths and the link cap feed none of them. Verdicts: `pass` when a verified location serves the object; `error` when a seeded location exists and could not be verified (refused, robots, 403, timeout), naming it; `fail` when every seed source in decision 4 was searched for that body and object and none records a location. That last clause makes `fail` a complete search over named sources, which satisfies DN-012 d1.
   - **The discoverability indicator** is new and enters as a **candidate** through the DD-054 path. `scripts/add_candidate_indicator.py` is written for A12 only; generalize it or write a sibling, and write through `framework_writeback.save` with a projection after. Its id is the next free one in the record's scheme; report it. Statement: *a machine client starting from the product page reaches the body's API, its terms, its changelog and its inventory without being told where they are.* Judged per object per surface: `pass` if the verified location's URL is among the product page's links (on-host or off-host, including links past the probe cap: an href on the page is reachable whether or not the harness probed it), or sits at a documented convention location: `/.well-known/api-catalog` or a `Link: rel="api-catalog"` header for an API (RFC 9727, June 2025), `/data.json` at the host root for an inventory (OMB M-13-13 and the Project Open Data metadata schema); `fail` if the page was read whole and neither holds; `error` if the page was not served or the convention location was not fetched. As a candidate it sits on the matrix and enters no level and no score (`scoring_model.md:146`). Promotion is the operator's (DD-054).
   - **The cap.** DN-013 closes the link-cap question: `link_probe.max_links_probed` stays a politeness bound on the discoverability probe and decides nothing about existence. A1 and A3 are not existence legs and are unchanged beyond decision 1.

4. **The seed table, written, not fetched.** `assessment/harness/scan/seeds/known_locations_2026-10-07.yaml`: for each of the 16 bodies in `declared_locations` and each object (API base, API terms, changelog, inventory, catalog.data.gov organization), every candidate location from these sources, each entry with `seeded_from` and `status: seeded_unverified`:
   - `model_knowledge:<model id>`: what this session knows (for example `api.bls.gov/publicAPI/v2`, `apps.bea.gov/api/data`, `api.eia.gov/v2`, `quickstats.nass.usda.gov/api`, the Socrata endpoints at `data.cdc.gov` and `data.bts.gov`, `api.ers.usda.gov`). Write what you know; mark confidence in a field; never drop a seed because it might be wrong, since part 2 verifies every one.
   - `repo:<path>:<line>`: every location this repository already cites (grep `docs/`, `corpus/evidence/frame/`, `docs/data/sources_per_check.json`, the recollection's `declared_locations` and its `not_declared` and `unreadable` page lists).
   - `catalog.data.gov` and `api.data.gov`: listed as sources to query in part 2, with the query each will run (the CKAN `package_search` action filtered by organization and resource format, and api.data.gov's agency listing). Not fetched here.
   Bodies the recollection marked `not_declared` or `unreadable` (BEA, BLS, BTS, DRSMSU, ERS, NAHMSAPHIS, NCES, NCHS, NCSES, ORES, SAMHSACBHS, SOI on at least one object) get particular care: the stranger rule is what left them blank. The table also lists, per seed, the host it lives on, so part 2's host list is generated from it.

5. **Declarations scheme 2.** `declarations.py` accepts `seeded_from`, `verified_at` and `status` (`verified`, `refused_robots`, `http_<code>`, `not_the_object`, `seeded_unverified`) beside the existing `read_from`, which stays on every recollection entry. A scheme-1 file still loads. No `targets.yaml` value changes in this part.

**Write set:** the new rule versions and their fixtures; `declarations.py`; the seed table; the candidate-indicator script and the framework record through `framework_writeback.save`; the re-judgement's state, log events and composite declaration; the regenerated views; tests; the RESULT. Byte-identical: `collectors/`, `manners.py`, `run.py`'s collection path, `scripts/score.py`, `targets.yaml`, every stored payload other than the new ones, every task file.

**Immutable once written.**

## Gate and report
`make gate-task` (rule modules changed), then the pre-push tier `CLAUDE.md` prescribes at launch (if `2026-10-07_parallel_hosts_and_fast_gate.md` has landed, its rule governs; quote the tier and both wall-clocks), `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability_RESULT.md`, under 60 lines: the three fixes with before and after verdict counts; the composite's id and what it takes from where; the candidate indicator's id and statement; seeds per body per object per source, and the bodies with no seed from any source; premises wrong; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** read → fixtures for the false passes → rule versions → re-judge → composite → publish and views → existence and discoverability rules with fixtures → candidate indicator → seed table → declarations scheme 2 → gate → RESULT → push.
