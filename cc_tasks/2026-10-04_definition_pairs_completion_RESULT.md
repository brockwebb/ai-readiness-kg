# RESULT: definition pairs completion: re-check, 21 more pairs, cross-document edges projected, citations retrieved

**Task:** `cc_tasks/2026-10-04_definition_pairs_completion.md` (no addenda). **Status:** complete, with **coverage 151 of 158**. The judge stopped cleanly at its declared 1,200,000 ceiling with 7 pairs unjudged (premise 1). Every gate below ran to its EXIT line before this file was written. Dispatched and headless; launch base `60f39205`; session `dbddc791`.

## 1. Controls re-run, then the pairs
`--recheck-controls` (new; `recheck_todo`, 2 tests) judged the 11 controls again under `definition_pairs_2026-10-04b`, with the same `criteria_version` `60256b3a937929b5`, before any pair was judged. Result: **positive 7/7 not `consistent`, PASS** (4 `not_comparable`, 3 `differs_no_conflict`, identical to the first run); **negative 4/4 `consistent`, PASS**. Cost: 404,546 tokens. Then 21 of the 28 pairs were judged before the spend guard refused the 22nd (`over_ceiling`, run exit 3, `logs/dpc_pairs_run.log`).

## 2. Counts over 158 (`docs/evidence/definition_pairs.md` Table 2)
| outcome | rows | scope | necessary_condition | object_of_readiness |
|---|---|---|---|---|
| conflict | 5 | 0 | 1 | 4 |
| differs_no_conflict | 86 | 33 | 42 | 11 |
| consistent | 0 | – | – | – |
| not_comparable | 60 | – | – | – |
| unjudged / unparsed | 7 / 0 | | | |

The 21 new rows hold **no new conflict**: 9 are `not_comparable` and 12 `differs_no_conflict`. `reason_check`: 147 `ok`, 4 `quote_not_in_spans` (the 3 already flagged, plus 1 new). The 0.60-confidence gloss row stays flagged. Nothing was adjudicated, and no Definition node changed.

## 3. Edges: 5 projected, gate green
`resolve_endpoint` now honours a qualified `from_key`/`to_key` only when its prefix is a manifested doc_id and its local part matches the asserted id. Otherwise it raises `EndpointRefused`; the edge is logged and counted, and no node is written. Unqualified ids are scoped as before. A qualified edge MATCHes both endpoints by label (never MERGE) and carries `grounding_span`, `grounding_span_to`, `kind`, `source` and `adjudicated`. The KG replay reads the tagged shard by name (`CROSS_DOCUMENT_EDGE_TAGS`) after the untagged log. No new phase was added, because `test_every_phase_boundary_is_logged` pins the phase list.
**Three controls** (`tests/test_build_projection.py`). Mutation check: breaking unqualified scoping fails control 1 only; scoping a manifested qualified key to the asserter fails control 2 only; accepting an unmanifested prefix fails control 3 only.
**Projection** (`logs/dpc_projection.log`, EXIT=0, about 40 min): `edges_cross_document: 5`, 0 refused, no new event written (the shard already held all 5; `--emit-edges` found 0 new). **Graph:** 12 `CONFLICTS_WITH` (7 + 5). Each of the 5 is `Definition`→`Definition` with `source: cross_document_pass`, its kind, both spans and `adjudicated: false`. All 10 phantom keys `<doc A>::<id B>` are absent. `get_overview().projection_gate`: **green**, 228 nodes, 0 mismatches.

## 4. The OECD edge (`batch-004:11185`, event `7ec72268f4f348dbad0cd298be0c94ac`)
**Cause: deliberate supersession, not the decision 2 defect; not fixed.** The edge asserts `introducing-the-oecd-ai-capability-indicators`: `d_superhuman_agi_deepmind` `conflicts_with` `d_agi`, span "In contrast, the OECD's AI Capability Indicators provide a framework to systematically compare AI developments with human performance across the range of human ability domains.", from extraction `source_sha256` `7e740330…`. `batch-005` event `d80671c0006b4ef8b66d92fe459a296b` (`extraction_superseded`, "Clearance 2: component-5.html markdown capture replaced by the full 56-page report PDF", authorised by the bulk_v1 closeout) supersedes that sha, and `read_overlays` drops it. The replacement extraction `798d84db…` asserts no `conflicts_with`.

## 5. Citations: 9 retrieved, 0 still recalled
All are in **`docs/evidence/method_sources.bib`** (premise 3), each with url, date and one sentence under 15 words: Podsakoff et al. 2016; MacKenzie et al. 2011; Walker & Avant 2011 (5th ed.); Euzenat & Shvaiko 2013 (2nd ed.); SemEval-2013 Task 9; DEFT 2019 and SemEval-2020 Task 6; Manheim & Garrabrant 2018; Campbell 1979.
**Retrieval corrected a recalled quote.** MacKenzie et al. say "the object to which the property applies", not "the entity to which…"; the README now quotes the paper. Two citations were read second-hand, and their bib notes say so: Walker & Avant (step 4 quoted from PMC10594418) and Campbell (the law's wording read on Wikipedia; RePEc has no abstract).
Labels replaced: `definition_pairs.md` (through the generator) and the Commerce note's lines 55–57. Manheim and Campbell are cited only in `docs/catalog/README.md`, which is protected and already said "read on the web".

## 6. Reader gate (fresh subagent, given only `definition_pairs.md`), verbatim
> Four of the five conflicts the model found are about what "AI readiness" applies to: the higher-education source calls it "the human capability to work effectively alongside intelligent systems," which the judge set against DataHub's "a data asset is prepared," the UK action plan's "whether institutions can reliably convert" data assets, and the UK/ODI line "a dataset may be considered AI-ready," while DataHub's data-asset reading was also judged to conflict with the UK institutional one. The fifth and only conflict over a required attribute pits the scientific-AI source, where readiness is "defined by sharded storage in binary formats," against the generative-AI open-data guidance, which requires data that is "not just machine-readable, but machine-understandable" and "enriched with contextual metadata" (confidence 0.60, against 0.86 to 0.92 for the other four). The remaining judged pairs never came back as fully consistent: 86 differ without conflicting (33 on scope, 42 on necessary conditions, 11 on what readiness applies to), and 60 are not comparable because they describe different things under different terms. Treat this as a screen, not a verdict: it covers 151 of 158 cross-document pairs among only 19 definitions from 11 documents, out of 2,064 definitions in 266 documents. Every row is one model's unchecked judgment with no second rater, the planted test pairs (7 known differences, 4 self-paraphrases) all came back as expected, and 4 rows quote wording that is not in the definitions they cite.

The reader added a sixth sentence picking "settle first": the 0.60 storage-format conflict, as the only one that decides what data-level checks must measure. **Change from the 130-pair reading:** same five conflicts and the same caveats, but "settle first" moved from the object-of-readiness question to the low-confidence necessary-condition conflict.

## 7. Gates (logs under `logs/`, not shipped)
- `make gate-fast`: **5 failed, 2899 passed, 3 skipped, 27 deselected, 12 xfailed**, 700.60 s, EXIT=2 (`logs/dpc2_gate_fast.log`).
- Full suite: **5 failed, 2926 passed, 3 skipped, 0 deselected, 12 xfailed**, 2370.88 s, EXIT=1 (`logs/dpc2_gate_full.log`).
- The 5 failures are the same tests as the views-task baseline (`logs/views_regenerate_gate_fast.log`): `test_brief_deck`, `test_brief_pack` ×2, `test_g4_resourcing_reissue`, `test_publication`. Each is a manifest-view guard on paths this task must leave byte-identical.
- `seldon verify`: all checks passed, EXIT=0 (`logs/dpc2_seldon_verify.log`).
- Protected paths (`logs/dpc2_protected.sh` → `logs/dpc2_protected.log`): PASS, EXIT=0. The check diffs against HEAD because two registration commits by another session landed meanwhile (`9475a700`, `8b2a31d4`, cc_tasks only). The FSS repo's one modified line is a `desktop` session's (`c8dc3312`, 19:28:12Z) `artifact_created`, not this session's.
- Definition and projection tests: 25 passed (`tests/test_definition_pairs.py`, `tests/test_build_projection.py`).

## 8. Premises wrong
1. **Ceiling arithmetic.** 28 × 36,795 ≈ 1.03M left out decision 1's own 11-control re-run (404,546 tokens), so 7 pairs could not fit under 1.2M. The ceiling held and was not raised. To close: `--run --run-id definition_pairs_2026-10-04c --ceiling-tokens 300000` (7 × ~37K plus headroom), with or without `--recheck-controls` (+~405K).
2. "Full suite (0 failed, since the views task precedes this one)." The views task STOPPED (`2803051b`), so its 5 guards are still red.
3. Write set:
   - `kg/build_projection.py` is `scripts/build_projection.py`, and `tests/test_build_projection.py` did not exist (created).
   - `scripts/run_definition_pairs.py` had to change: re-check flag, README citations, edge text. The units carry no run id, so a plain resume skips every control.
   - `docs/evidence/sources.bib` is pinned by `test_evidence_map` to exactly `claims.yaml`'s citations, so the entries went to the new `method_sources.bib`.
   - Projecting the edges moved Q3 of `docs/evidence/kg_questions.{yaml,md}` from `cannot_answer` to `answered` (5 cross-document edges touching Q1). It was regenerated by its own generator; Q1, Q2, Q4, Q5 and the epoch are unchanged.
4. The Commerce note never said "recalled": its label was "cited from the literature as known, not retrieved".

**Incident, recovered.** One `git stash`/`pop` ran while the judge was writing; it would have reverted `judgments.jsonl` and the ledger for under a second. Afterwards both were checked: 26 rows, each with its raw file; 28 reserves, 26 settles and 2 in flight; nothing lost.

**Tokens and models.** Judge `claude-opus-4-8`: 32 calls, **1,184,830 settled against 1,200,000**, 1 refusal, 0 failures (`state/spend_ledger.jsonl`, run `definition_pairs_2026-10-04b`). Session `claude-opus-5-5`, from its transcript at RESULT time: 98 turns; 196 input, 69,542 output, 249,274 cache-write and 17,911,178 cache-read tokens. Reader-gate subagent: 56,340.
