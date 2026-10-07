# CC Task: verify every seeded location by one fetch, judge existence and discoverability on all 16 bodies, and freeze the composite the concise report will cite (part 2 of 2, operator-launched)

**Date:** 2026-10-07
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from DN-013 §1 (R1). Part 2 of `2026-10-07_seed_known_locations_and_split_discoverability.md`. It fetches from agency hosts, so it is the rescan the operator reserves to himself (DN-012 d6, as the recollection was): **launched by the operator, not the dispatcher.** It carries no Spend or Network header on purpose, so it is not a dispatcher candidate (DN-006 decision 3).
**Implements:** DN-013-R1.
**Framework layer served (DN-005 §5 rule 1):** §2.2, measurement.
**Fulfils:** its own ResearchTask. Launched by the operator.
**After:** 2026-10-07_seed_known_locations_and_split_discoverability
**Launch:** by the operator only, after part 1 is `completed` on the graph: `touch .seldon/DISPATCH_STOP`, wait until `seldon dispatch status` shows the lease free, paste the dispatch line, and let the session remove the STOP file at its close (it records both times). Estimated 2M tokens (Opus); no harness model call. Fetches under the manners layer only (identified UA, robots-first, the standing per-host rate), on exactly the hosts the seed table names plus `catalog.data.gov`, `api.data.gov` and the 16 roster hosts; the session prints that list before the first request and the RESULT quotes it; `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Complete the seeds from data.gov.** For each body, run the queries part 1's seed table names against `catalog.data.gov` (CKAN `package_search` by organization, resources with an API format, and the organization's harvest record if one is served) and `api.data.gov`'s agency listing. Every location found is added with `seeded_from: catalog.data.gov` or `api.data.gov` and the query that found it.

2. **Verify every seed by one GET.** Record `verified_at` and a status: `verified` only when the response is the object (an API base answers with a machine-readable body or a documented landing page; a terms page states terms; a changelog carries dated entries; an inventory parses as DCAT-US `data.json` or a CKAN listing); otherwise `refused_robots`, `http_<code>` or `not_the_object`. Write the results to `targets.yaml` `declared_locations` under scheme 2, keeping every `read_from` the recollection wrote. A seed that cannot be verified is never dropped; it stays with its status, and existence is `error` on it.

3. **Fetch the convention locations.** `/.well-known/api-catalog` (RFC 9727) and `/data.json` on each roster host and each verified API host, robots-first. These are discoverability's evidence; part 1's rule judges them.

4. **The cycle.** `scan_2026-10-07_seeded` over the existence legs (A2, D1, F4, D4, B1, B4, D3, G4, and A9 as frontier) and the new discoverability candidate, on the 16 bodies' 46 surfaces, judged under part 1's versions, to the log per DN-003. The product-page link observations are read from `scan_2026-10-06_recollect`, not re-fetched; say so on the cycle's manifest.

5. **Freeze.** Declare `scan_2026-10-07_composite_d`: existence and discoverability legs from this cycle, everything else from `_composite_c`. Publish, project, regenerate every view, and rebuild `docs/evidence/claims.yaml` with `scripts/build_evidence_map.py` so every claim cites `_composite_d`. Write `docs/evidence/FROZEN.md`: the composite id, the commit, the time, and one line, "the concise report cites this composite and no other". A later cycle does not move the report; a new report task would.

6. **Delta table.** For every body and object: the recollection's declaration status, the seed sources that named a location, the verified status, the existence verdict and the discoverability verdict. The headline count the report will need: bodies and objects where the thing exists and a machine cannot find it from the product page.

**Write set:** `targets.yaml` (`declared_locations` only), the seed table (statuses only), the fetch logs, the new cycle's state and log events, the composite declaration, the regenerated views, `docs/evidence/claims.yaml` and `FROZEN.md`, the RESULT. Byte-identical: every rule, collector, `manners.py`, `scripts/score.py`, every prior payload, every task file.

**Immutable once written.**

## Gate and report
`make gate-task`, then the pre-push tier `CLAUDE.md` prescribes at launch (quote it and the wall-clocks), `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-07_seed_known_locations_verify_RESULT.md`, under 60 lines: the host list as fetched; requests per host; seeds per source and per status; existence and discoverability counts per leg before (`_composite_c`) and after; the delta table's headline count; the frozen composite id and commit; premises wrong; STOP file times; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** host list → data.gov seeds → verify → convention fetches → cycle → judge → composite → publish, project, views → evidence map → FROZEN.md → delta → gate → RESULT → push → remove STOP.
