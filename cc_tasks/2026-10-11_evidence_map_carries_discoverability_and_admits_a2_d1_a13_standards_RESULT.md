# RESULT: the evidence map carries the discoverability finding; Swagger 2.0, SPDX, two CC deeds and RFC 9727 admitted; A2 and D1 quotable

**Task:** `cc_tasks/2026-10-11_evidence_map_carries_discoverability_and_admits_a2_d1_a13_standards.md` (no addendum; globbed before starting). **Spend:** zero model calls; the session's own context is unmetered. **Network:** 16 requests, all through `scripts/fetch_allowlisted.py`, all to the four declared hosts, none refused. **Gate: green.** `make gate-task`: fast tier 3324 passed, 5 skipped, 41 xfailed, 30 deselected, 343.77 s; re-derivation 25 passed, 0 skipped, 0 xfailed, 25 deselected, 11.22 s; wall clock 357 s, `EXIT=0`. Deselected counts come from `--collect-only` (xdist prints none). The skips are the two live-model tests, `test_g1_preservation.py:337`, `test_scan_harness.py:290`, and `test_kg_questions.py:115`, which now skips because the corpus epoch moved (premise 6). The first gate run went red on 6 tests; §4 gives the causes. `seldon verify`: all checks passed, `EXIT=0`. `scripts/check_protected_a2_d1_a13_standards.sh` against `b9311e0f`: PASS. Projection round trip: 9 passed. `kg.manifest verify`: clean.

## 1. Admissions (decision 1). Epoch `standards-a2-d1-a13-2026-10-11`, `scripts/admit_a2_d1_a13_standards.py`
Each document took the same path. The capture was fetched robots-first and hash-checked against the fetch log, then rendered to markdown by `harvest_kernel.DomMarkdown`. It then got a `manifest_add` (`events/batch-001.jsonl:130–134`), dixie screening, and a sweep that returned `included` and `verified`. `included` went from 282 to 287. The table gives the capture sha256 / the admitted `.md` sha256.
| doc_id | url | captured_at (UTC) | sha256 | licence, as the document states it |
|---|---|---|---|---|
| `openapi-specification-v2-0` | spec.openapis.org/oas/v2.0.html | 2026-10-11T15:23:53 | `74960840…` / `c41436bb…` | Apache-2.0 (§2.1) |
| `spdx-license-list` (v3.29.0) | spdx.org/licenses/ | 15:23:55 | `38f2f860…` / `6b014ac8…` | "© 2018 SPDX Workgroup… All Rights Reserved"; the page states no open licence |
| `cc-by-4-0-deed` | creativecommons.org/licenses/by/4.0/ | 15:24:38 | `8dda1cce…` / `a1035c22…` | site content CC BY 4.0 |
| `cc0-1-0-deed` | creativecommons.org/publicdomain/zero/1.0/ | 15:24:40 | `abb4d48f…` / `42f7559c…` | site content CC BY 4.0 |
| `rfc-9727-api-catalog` | www.rfc-editor.org/rfc/rfc9727.txt | 15:23:56 | `e17c39c0…` / `1be014f2…` | IETF Trust Legal Provisions (BCP 78); code under Revised BSD |
**Not admitted:** OpenAPI 3.1. `openapi-specification-core` (OAS 3.2.0, kernel-v03) is already in the corpus, and `RULE-A2-v6` accepts any `3.x`, so per DN-001 d4 (corpus before web) it is bound and not re-fetched. Also not admitted: the CC legal-code index (`/licenses/list.en`). It was fetched, but it renders as a grid of "Deed Legal Code" links whose identifiers exist only in hrefs, so the two deeds for the rule's tokens `CC-BY` and `CC0` were admitted in its place. Same for the CC "About the licenses" page: fetched, not admitted, because it carries template residue.
**Departures from the Commerce path:** bytes came from a fetch (Commerce's came from a local copy); the files go to `corpus/kernel/`, not `bulk/`; HTML is rendered to markdown because the sweep fails HTML; `acquisition.licence` is recorded; and nothing is extracted.
**Binding (DN-001 d5):** I edited the skeleton evidence cells for A2 and D1, which removed both `**gap**` markers, and ran `framework_writeback_evidence.py`. A13, a candidate, was bound through `add_candidate_indicator.py --refresh --task`; refresh now adds missing evidence edges and never removes one. Both writes record 0 removals on their events, and the full projection shows `evidenced_by_missing_document: 0` (`logs/2026-10-11_standards_projection.log`).

## 2. Claims added (decisions 2–3), all through `build_evidence_map.py` (new Q7)
I registered 13 Results first with `scripts/register_seeded_delta_results.py`, using `seeded_delta.py` as the Script: the headline 15/11/29/54/88, plus exists and unreachable per object. `--check` reports no drift. The other claims that moved are CL-044 (282 → 287 admitted) and CL-054 (locators 10 → 12 of 50; `EVIDENCED_BY` 34/154 → 40/160; 16 → 14 indicators with no edge).
- **CL-118** "…`RULE-A13-v1`… finds 15 body and object pairs, in 11 bodies, where the object… exists and no product page of the body reaches it, of 29 pairs where it exists; counted per product page, 54 of the 88…"
- **CL-119–122**, one per object: API 5 exist / 3 unreachable (`BJS`, `NCES`, `NCHS`). Terms 3 / 2 (`BEA`, `CENSUS`). Changelog 5 / 1 (`CENSUS`). Inventory 16 / 9.
- **CL-123–138**, `A13` per body, for example "`EIA`… fail on 2 and error on 1 of the 3 product surfaces". These match part 2's per-body counts.
- **CL-139** "no host the harness fetched it on answered… `/.well-known/api-catalog` with an API catalog (`application/linkset+json`), and no product page sent a `Link` header with `rel="api-catalog"`…". The builder computes this over the A13 part's Observations and stops if any count is non-zero.
- **CL-140 / CL-141**: `A2` is pass 0 / fail 25 / error 21 and `D1` is pass 0 / fail 31 / error 15. Each cites its `scan_<leg>_*_2026-10-07_composite_d` Results (the tags) and the documents its indicator is evidenced by.

## 3. DN-001 floor over the claims file (`scripts/dn001_floor.py`; `state/dn001_floor_2026-10-11_{before,after}.json`)
Legs that some claim quotes and that reach an admitted source went from **20 of 24 to 22 of 24**. Before the change, `A2`, `B5`, `D1` and `D2` had none, across 13 claims. **After, only `B5` and `D2` remain**, across 8 claims (CL-036, 037, 039, 041, 052, 059, 060, 072). They are outside this task's scope and would need a follow-on task.

## 4. Premises wrong, and the first gate's six failures
1. "A2 reaches no admitted source": true of the edges, but an OpenAPI 3.x document was already admitted (§1).
2. The module text of `RULE-D1-v6` names neither SPDX nor CC. The params block it reads, `d1_licence`, does: `spdx.org/licenses/`, `creativecommons.org/`, `CC0`, `CC-BY`. I read the rule as module plus params. The other recognised prefixes and tokens it names (opensource.org, usa.gov, opendefinition.org, ODC-BY…) remain unadmitted.
3. A13 already reached 5 sources; RFC 9727 is now the sixth. Its record cell is written by `add_candidate_indicator.py`, not by the skeleton, whose candidate row I updated by hand to match.
4. The write set left out the framework record, the skeleton and the projection. Binding is impossible without them.
5. The views moved: brief pack, scan catalog, fig2, MCP doc, progress page and `docs/data/`. Each was regenerated by its own generator, and all 13 `--check` runs pass (`logs/2026-10-11_standards_views_check_2.log`). That accounts for 4 of the 6 failures.
6. `run_kg_questions.py --check` refuses with "EPOCH MOVED… a re-run is a new task", so it was not re-run, and its test skips.
7. `test_concise_report_shipped` read the live claims, but FROZEN.md says the report cites the claims at `cd0ccae6`. The guard now reads the claims at FROZEN's commit; `reports/` and FROZEN.md are byte-identical.
8. `test_framework_single_writer`'s pinned count of skeleton-unauthored `EVIDENCED_BY` edges went from 7 to 8, because of A13's new edge. I updated it with a dated comment.
9. Foreign file: `state/prior_art_queries.jsonl` was appended to this checkout by another session's `prior-art/1` tool. It is not committed.

## 5. Fetch log, whole (`logs/2026-10-11_standards_fetch.jsonl`, 16 lines, all `GET`, no `refused`/`error`)
spec.openapis.org: robots 200, `oas/v2.0.html` 200. spdx.org: robots 404, `licenses/` 200. rfc-editor.org: robots 200, `rfc9727.txt` 200. creativecommons.org: robots 200 ×4; `licenses/list.en` 200; `share-your-work/cclicenses/` 307 → `cc-licenses` 301 → `cc-licenses/` 200; `licenses/by/4.0/` 200; `publicdomain/zero/1.0/` 200.

## 6. Logs
`logs/2026-10-11_standards_gate_task_2.log` (gate), `…_gate_task.log` (the red first run), `…_post.log` (collect counts, round trip, `seldon verify`, `kg.manifest verify`), `…_standards_admit_{dryrun,live}.log`, `…_writeback_{a2_d1,a13}.log`, `…_register_seeded_delta.log`, `…_standards_projection.log`, `…_standards_views_check_2.log`, `…_standards_views_regen_2.log`.
