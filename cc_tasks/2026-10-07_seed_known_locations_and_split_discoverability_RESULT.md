# RESULT: three false passes fixed (generation 15), existence split from discoverability (generation 16, candidate A13), seed table written; `scan_2026-10-06_composite_c` is the cycle of record

**Task:** `cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md`. No addendum existed. Dispatched, headless, from `ce656639`. **Layer:** DN-005 §2.2 (measurement) and §2.1 (the candidate). **Network:** none beyond `git push`; nothing was fetched. **Spend:** no harness model call. This session ran on `claude-opus-5-5`; no tool here meters its own tokens, so none is quoted (the estimate was 2.5M).

**Gate: green, on `f9f3b449`.** `make gate-task` (rule modules changed): fast tier 3235 passed, 5 skipped, 41 xfailed, 30 deselected, 155.41 s; re-derivation 25 passed, 0 skipped, 0 xfailed, 25 deselected, 4.24 s; wall clock 160 s, `EXIT=0` (`logs/skl_gate_task_2.log`; deselected counts from `--collect-only`, `skl_gate_task_collect.log`, as xdist prints none). Skips: the standing three, `test_kg_questions.py:115` (the record moved under the stored answers) and two live-model skips. **`make guards`:** 73 passed, 0 skipped, 0 xfailed, 0 deselected, 75 s, `EXIT=0` (`skl_guards.log`, on `c583a9cd`). **`seldon verify`:** all checks passed, `EXIT=0` (`skl_seldon_verify_2.log`).
**Protected paths:** `scripts/check_protected_seed_known_locations.sh ce656639` gives PASS, `EXIT=0` (`skl_protected_2.log`). It holds byte-identical: `collectors/`, `manners.py`, `run.py`, `runner.py`, `score.py`, `targets.yaml`, every shipped `rule_*.py`, every prior payload, matrix and task file. Shards and the Seldon store only grow. `params.yaml` gained only the `existence` and `discoverability` blocks and moved only `link_probe.legs_served` (+A13).

## 1. The three fixes (generation 15), on the recollection's 46 surfaces, before → after (pass/fail/error)
Each fixture is the stored recollection group: the old rule still passes on it and the new one does not (`tests/test_gen15_false_passes.py`, 21 tests).
- **`RULE-A2-v5`: 4/3/39 → 0/7/39.** It passes only on a document carrying `openapi` (OAS 3.x) or `swagger` (2.0). Census's 4 move pass→fail: "the API is present ... does not parse as an API description".
- **`RULE-D1-v5`: 7/0/39 → 0/0/46.** Tokens are matched on visible text at word boundaries; an HTML `rel="license"` link also counts. Census ×4 and EIA ×3 move pass→error, because the collector keeps 20,000 characters of a terms page (census.gov's is 302,319 bytes) and a truncated read is a partial search.
- **`RULE-A3-v8`: 14/1/31 → 8/1/37.** An HTML page is not an "unfiltered file". BEA ×4 (`/research/special-sworn-researcher-program/papers`) and NCES ×2 move pass→error, under the link-cap remainder.
- **Re-judgement:** `scan_2026-10-06_recollect_rj1` (`scripts/rejudge_recollect_rj1.py`). Control gate PASS on 11 fixtures. It re-derives 552 of 552; the 414 Findings on unchanged legs are identical but for the identity fields. 552 supersession pairs, no self-loop (`skl_rj1.log`, `state/rejudgement_diff_2026-10-07.json`).

## 2. The composite
`scan_2026-10-06_composite_c` (`skl_composite_c.log`) takes all twelve recollected legs from `_recollect_rj1`, A2 and D1 included, withholding nothing. Every other leg comes from `scan_2026-09-10_rj5`. That gives 1009 Findings: 552 from rj1 and 457 from rj5. rj5 was not re-judged for A3, because A3 is taken from rj1.

Against `_composite_b`, the delta is A2 0/0/46 → 0/7/39 and A3 14/1/31 → 8/1/37; D1 stays 0/0/46 but is now the recollection's (`skl_delta.log`). On the product matrix A2 is 4 fail / 19 error, A3 6 / 17, and D1 is error on all 23.

Published and projected (13,748 Findings, 0 unresolved), and every view regenerated with every `--check` passing (`skl_views_5.log`). 66 of 66 tagged Results reproduce; Results were published at `73dc9498`, and composite B's 47 were moved to `stale` with `superseded_by`.

## 3. Existence and discoverability (decisions 3, 5)
- **Generation 16:** `RULE-A2-v6`, `D1-v6`, `F4-v5`, `D4-v5`, `B1-v4`, `B4-v3`, `D3-v3`, `G4-v3`. Each reads only recorded or seeded locations; guessed paths, the link probe and the cap feed none of them (`rules/_existence.py`).
  **Verdicts:** `pass` when a recorded location serves the object; `error` when a recorded location is unverified (naming it, its status and its source) or a seed source is unsearched; `fail` only when every recorded location was read AND every source in `params.existence.seed_sources` is in the body's `searched`.
  **Declarations scheme 2** (`declarations.py`) adds `seeded_from`, `status`, `verified_at` and `searched`. A scheme-1 file loads unchanged and its `declared` blocks are byte-identical.
- **Candidate `ind:A13`** (`RULE-A13-v1`, criterion A, construct "Discoverability from the product page", promotion the operator's, DD-054): *a machine client starting from the product page reaches the body's API, its terms, its changelog and its inventory without being told where they are.*
  Judged per object (`rule_a13.per_object`), combined fail > error > pass > not_applicable; convention locations RFC 9727 `/.well-known/api-catalog` or `Link: rel="api-catalog"`, and `/data.json` at the host root (M-13-13). Written through the generalised `scripts/add_candidate_indicator.py --code A13`, with one action (`act:a13-link-what-you-publish-from-the-product-page`), then projected.
- **Controls:** E5 fires on all 11 fixtures with no table row changed. The derivation, pre-registered in `params.yaml`, honours `CONSUMES_PAGE_ONLY`.
- **Smoke run on stored recollection evidence (not a Result):** A13 gives 33 fail, 13 error; every existence leg is 46 error, because scheme 1 records no search (`skl_smoke_gen16.log`).

## 4. Seed table (decision 4)
`assessment/harness/scan/seeds/known_locations_2026-10-07.yaml` (`scripts/build_seed_table.py`): 148 seeds on 45 hosts, all `seeded_unverified`. By source (a seed may carry several): repo 119, model knowledge 53, developer page 44. catalog.data.gov and api.data.gov are not fetched; each body carries the queries part 2 runs.

Per body, seeds for API base / terms / changelog / inventory / catalog org:

| | | | |
|---|---|---|---|
| BEA 6/2/3/2/1 | BJS 3/3/1/2/1 | BLS 4/1/3/2/1 | BTS 3/0/1/6/1 |
| CENSUS 4/4/2/2/1 | DRSMSU 4/0/2/1/1 | EIA 6/1/2/2/1 | ERS 4/1/2/2/1 |
| NAHMSAPHIS 1/0/1/2/1 | NASS 3/2/1/2/1 | NCES 4/0/2/2/1 | NCHS 4/1/1/4/1 |
| NCSES 3/0/2/2/1 | ORES 1/0/1/1/1 | SAMHSACBHS 2/0/2/3/1 | SOI 1/0/1/2/1 |

**No location seed from any source** (empty, or only a page the recollection searched): API base NAHMSAPHIS, ORES, SAMHSACBHS, SOI; terms BTS, DRSMSU, NAHMSAPHIS, NCES, NCSES, ORES, SAMHSACBHS, SOI; changelog BTS, DRSMSU, ERS, NAHMSAPHIS, NCHS, ORES, SAMHSACBHS; inventory none.

## 5. Premises wrong (the task's, then mine)
1. **Part 2 cannot collect A13 as written.** Part 1 holds `run.py` and `runner.py` byte-identical. A13 is in `CURRENT` through `link_probe.legs_served`, but `run.targets` gives candidate legs only to `well_known` rows, and nothing fetches `/.well-known/api-catalog`. Part 2's write set must admit `run.py`/`runner.py` for that (its byte-identical list names neither).
2. **D1's 20,000-character terms read** is a literal in `runner.py`, so census/EIA D1 stay `error` until collection reads visible text whole. A3's "body sniffs as HTML" cannot be implemented: link records are HEADs with no body, so the media type is all the evidence there is.
3. **Until part 2 runs, `CURRENT` (generation 16) is not the rule set that judged the cycle of record** (generation 15), by the task's own sequencing. Adopter frames cannot declare locations, so their existence legs are `error`; `adopt.py` needs that field.
4. **`ind:A2` has no admitted source** (an evidence gap), so the report states A2's new verdict in words, not tags. Three `_composite_c` A2 Results published at `73dc9498` are quoted only on the matrix. RFC 9727 is named, not admitted (no network).
5. **Writes outside the stated set, each needed:** `rederive.py` (a re-judged targeted cycle stays `scope: legs`); `composite.py` (a re-judged overlay's control gate); `fixture_expectations.py`; `rederive_tagged_results.py` and `mcp/airkg_tools.py` (a re-judged overlay's collection); `_scope.py` (reads scheme 2); `tag_prescriptions.py` and `catalog_inputs.yaml` (A13 rated 4 under rubric v1, by me); the skeleton's candidate row, the report sections, 12 gap maps re-rendered (they draw the record's candidates), and test pins.
6. **Mine:** the first matrix build died with my tool call (exit 143) and was rerun; the seed generator first emitted 14,431 Census URLs (now collapsed to API bases) and lost model seeds to `page_to_read` (fixed `f9f3b449`); my first A2 prose quoted tags that broke the sources floor.

**Logs:** `logs/skl_rj1.log`, `skl_publish_rj1.log`, `skl_composite_c.log`, `skl_matrices.log`, `skl_writebacks_2.log`, `skl_projection.log`, `skl_registrations_2.log`, `skl_views_5.log`, `skl_rederive_tagged_2.log`, `skl_rederive_tagged_final.log`, `skl_verify_states.log`, `skl_publish_states.log`, `skl_supersede.log`, `skl_rerender_gapmaps.log`, `skl_seed_table_2.log`, `skl_seed_stats_2.log`, `skl_smoke_gen16.log`, `skl_delta.log`, `skl_gate_task_2.log`, `skl_gate_task_collect.log`, `skl_guards.log`, `skl_seldon_verify_2.log`, `skl_protected_2.log`.
