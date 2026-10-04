# RESULT: cross-document conflict pass over the definitions of AI readiness (task 7ae11b56)

**Task:** `cc_tasks/2026-10-04_definition_conflict_pass.md` (no addenda exist). **Status:** complete, with **partial coverage: 130 of 158 pairs judged**. The run stopped cleanly at its declared 5,000,000-token ceiling (§7 premise 3). Every gate below ran to its EXIT line before this file was written. Launch base `503c115`; headless, dispatched. Layer: DN-005 §2.4 exposure. Shipped: `docs/evidence/definition_pairs.{csv,md}`, `scripts/run_definition_pairs.py`, `tests/test_definition_pairs.py` (15 tests), `events/batch-044_xdoc_conflict_held.jsonl`, `events/raw/definition_pairs/` (checkpoint `judgments.jsonl` plus 134 prompt/response files).

## 1. Controls first: criterion declared, then outcome
Declared in `CONTROL_CRITERION` and committed at `873cfa4` before any model call: **positive: no positive control comes back `consistent`; negative: every negative control comes back `consistent`.** The controls ran first as the pilot, and pairs ran only if both criteria passed.
- **Negative, 4/4 `consistent`: PASS.** Each pair was a definition against a script-made paraphrase of itself (serial comma ×2, American spelling, markdown emphasis). The judgments are usable.
- **Positive, 7/7 not `consistent`: PASS.** The 7 pairs are ones `48c74933` RESULT §4 characterised as differing. 4 came back `not_comparable`; 3 came back `differs_no_conflict` (scientific-AI × NOAA, UN × NOAA, UN × scientific-AI).

## 2. Set, pairs, counts
The set is Q1 as `run_kg_questions.py` wrote it (`--check`: no drift): **19 definitions from 11 documents**. That gives 171 unordered pairs; **13 same-document pairs skipped**, leaving **158 cross-document pairs**. Of those, **130 are judged, 28 unjudged** (ceiling) and 0 unparsed. Pairs ran in `pair_id` (hash) order, so the 28 were not chosen by their content.

| outcome | rows | scope | necessary_condition | object_of_readiness |
|---|---|---|---|---|
| conflict | 5 | 0 | 1 | 4 |
| differs_no_conflict | 74 | 29 | 36 | 9 |
| consistent | 0 | – | – | – |
| not_comparable | 51 | – | – | – |

`reason_check` (computed by script: are the reason's quotes verbatim in the spans?): 127 `ok`, 3 `quote_not_in_spans`. All 3 quote across markdown in a World Bank span; they are flagged, not fixed. The doc-pair matrix and the ranked list are in `definition_pairs.md`, and no interpretation is written there.

## 3. Edges: 5 written to an off-graph shard, 0 projected, 0 failed grounding
5 `conflict` rows. **All 5 passed the grounding gate on both spans** (`grounding.is_grounded` against the text from each document's `manifest_add` path). **All 5 are held, i.e. quarantined, and none is projected.** `build_projection.resolve_endpoint` scopes both endpoints of an `edge_asserted` to the document that asserts it. A cross-document edge on a graph shard would therefore MERGE a label-less phantom node `<doc A>::<id B>`. They were written through `kg.eventlog.append` (`edge_asserted`, `conflicts_with`, `source: cross_document_pass`, `kind`, both spans, `adjudicated: false`) to the tagged shard `batch-044_xdoc_conflict_held`. `replay()` never yields that shard. The CSV marks each row `quarantined: true` with that reason. `--emit-edges` is idempotent: a re-run wrote 0 new events.

Four of the conflicts are `object_of_readiness`: one unqualified term, "AI readiness", is attached to a human capability, a data asset or an institution. Three of the four involve the higher-education definition. The fifth (`d_airready_state` × Commerce `def_ai_ready_data`, confidence 0.60) depends on a gloss in the judge's reason, "(a machine-readable storage criterion)", whose words are not in the span. The mechanical reason check sees only quoted fragments, so it cannot catch this. Flagged for adjudication; not adjudicated here.

## 4. Prior art and method (README §Method)
**Repository precedent, read.** fss-policy-kg `docs/conflict_detection.md` §6–§8 and one verdict row from `kg/conflict_verdicts.jsonl`. This repository's 8 `conflicts_with` events. Adversarial-review rubric v1.3.0.

**Search.** Corpus MCP `search_text` and a full-text grep of `corpus/bulk_md` and `docs/` returned 0 method hits; Wintermute returned 0. **Adopted, recalled not retrieved** (§7 premise 1):
- Decomposition: concept clarification (Podsakoff, MacKenzie & Podsakoff 2016; MacKenzie et al. 2011; Walker & Avant).
- Outcomes: the correspondence relations of ontology matching (Euzenat & Shvaiko).
- Judge: the fss adjudicator's shape (one pair per call; ordered rubric; `criteria_version` `60256b3a937929b5`; every verdict persisted).

**Departures.** Single rater with no kappa; `adjudicator` is the full model id; the fss deontic vocabularies were replaced by this task's closed sets.

## 5. Reader gate (DN-009 d7): fresh subagent, given only `definition_pairs.md`
The first read found a gap: the file did not quote the wording of any conflict. A generated list of the 5 conflict rows was added, and the gate was re-run on the shipped file. The second read, verbatim:
> The judged pairs show 5 outright conflicts, and four of them are about what "AI readiness" is a property of: one paper calls it "the human capability to work effectively alongside intelligent systems," while other sources tie it to whether "a data asset is prepared," whether "institutions can reliably convert" data into systems, or whether "a dataset may be considered AI-ready." The fifth conflict, judged with less confidence (0.60 against 0.86 to 0.92 for the others), is about what data must have: one source defines readiness by "sharded storage in binary formats," and another says data must be "not just machine-readable, but machine-understandable" and "enriched with contextual metadata." Most pairs differ without conflicting: 74 do so on scope or required conditions (for example, the UN definition is the only one that names provenance and timeliness), 51 describe different things and cannot be compared, and no two definitions were judged equivalent. I would hold these findings loosely, because each one is a single model's unreviewed judgment, 28 of the 158 cross-document pairs were never judged, and 3 of the model's reasons quote text that does not appear in either definition. The disagreement I would settle first is whether AI readiness belongs to people, institutions or data, since it accounts for four of the five conflicts and one human-capability definition appears in three of them; the file says outright that it does not say what any conflict means for the framework, so it cannot tell me what settling it would change.

## 6. Gates (logs under `logs/`, not shipped)
- `make gate-fast`: **5 failed, 2852 passed, 3 skipped, 27 deselected, 12 xfailed**, 698.49 s, EXIT=2 (`logs/dcp_gate_fast.log`). Full suite: **5 failed, 2879 passed, 3 skipped, 0 deselected, 12 xfailed**, 2379.54 s, EXIT=1 (`logs/dcp_gate_full.log`). The 5 are the corpus-manifest view guards that the Commerce RESULT §6 reported red at its HEAD: `test_brief_deck`, `test_brief_pack` ×2, `test_g4_resourcing_reissue` (site `data/`) and `test_publication` (`corpus/manifest.json moved since the site was built`). Each failure names a manifest view this task may not touch. **Not fixed here**: `docs/brief/` and `docs/deck/` are byte-identical by this task's terms.
- `tests/test_definition_pairs.py`: 15 passed, 0 skipped, in both runs. One of them kills the run with SIGKILL mid-loop, resumes it, and asserts that no completed unit is called again and that the output equals an uninterrupted run's. `--check`: no drift, controls pass.
- `seldon verify`: all checks passed, EXIT=0 (`logs/dcp_seldon_verify.log`). Protected paths (`logs/dcp_protected.sh`): PASS, EXIT=0 (`logs/dcp_protected.log`): schema, brief, deck, framework and the FSS repo are unchanged. The one `seldon_events.jsonl` line that is not this task's is the standing dispatcher's `dispatch_refused` from 14:01Z; it is committed with this task's completion events.

## 7. Premises wrong
1. Decision 2 asks for a web search; `**Network:** none` forbids one, so no web search was run. The method citations are therefore recalled, not retrieved, and are labelled that way.
2. "Write `CONFLICTS_WITH` through the standing event-writing path": no standing path can place a cross-document edge (§3). Close: teach `resolve_endpoint` the fully qualified key carried on `from_key`/`to_key` when its prefix is a manifested doc_id, then replay the held shard. That needs no model call.
3. Spend: a declared 5M ceiling against a 6M estimate. One pair per call costs a measured **36,795 tokens on average over the 11-call pilot**. About 1K of that is the prompt; the rest is the `claude -p` system prompt (~24.6K cache read + 11.6K cache write). So 162 calls needed ~5.96M. Close: re-run `--run` with `--run-id` set to a new id and a ceiling of ≥1,100,000. The 28 pairs resume by skip under the same `criteria_version`.
4. "The 7 existing edges and the extraction run that wrote them": 8 `conflicts_with` events from four runs (`batch-002` fable pilot ×1, `batch-004` opus-4-8 ×3, `batch-023` opus-5 `bulk_v038` ×4); 7 are projected. The `batch-004:11185` OECD Definition edge is not in the projection, and why was not investigated.

**Model and tokens.** Pair judge `claude-opus-4-8` (`model_config.primary_judge_model_id`, the fss adjudicator's model): 134 calls, **4,975,390 tokens settled** against the 5,000,000 ceiling (`state/spend_ledger.jsonl`, run `definition_pairs_2026-10-04`; 1 refusal, 0 failures). Session `claude-opus-5-5`, measured from its transcript at RESULT time: 95 turns; 190 input, 97,490 output, 254,149 cache-write and 16,750,415 cache-read tokens. Reader-gate subagents: 53,401 and 54,491 tokens.
