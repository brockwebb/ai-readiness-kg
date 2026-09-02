# RESULT: Replace the deck's floor numbers with measured post-burn counts; correct the acceptance-sampling claim

**Task:** `cc_tasks/2026-09-02_deck_numbers_post_burn.md` (no addenda existed at execution time)
**Date:** 2026-09-02
**Model calls:** 0

## 1. Outcome

Slide 15 and the header block of `docs/crosswalk/deck_content_2026-09-01.md` (now content v4) and the
matching passages of `docs/crosswalk/meeting_brief_2026-09-01.md` carry measured post-burn values.
The false sentence "every batch passed acceptance sampling before entering" is replaced by the actual
tally with `sampling_inconclusive` explained in one clause. The deck was rebuilt to
`docs/crosswalk/framework_deck_2026-09-02.pptx` (18 slides; slide 15 text verified equal to the content
file's three bullets). The 09-01 pptx is untouched. `seldon verify` clean; root suite 594 passed.

One precondition the task did not anticipate: **the live Neo4j projection was stale.** Before this task
the graph held no `bulk-v038` nodes at all (`prov_corpus_epoch` values were `v1`, `kernel-v03`, and
null only), i.e. `build_projection.py` had not been replayed since the burn. The projection is a
disposable replay of the event log (CLAUDE.md invariant 1), so it was rebuilt here
(`/opt/anaconda3/bin/python3 scripts/build_projection.py`, exit 0, log in the session scratchpad) and
the graph counts below were read after the rebuild. Nothing in the event log, state files, ledger or
manifest was written.

## 2. Derivation table

| quantity | source | command / query | value |
|---|---|---|---|
| documents admitted | manifest projection | `python -m kg.manifest verify` → "clean: all local files present and unchanged"; `json.load('corpus/manifest.json')['counts_by_decision']` | included **194** (excluded 50, pending_refetch 39; 283 entries) |
| documents admitted (cross-check) | queue | `python -m kg queue status` totals line | total **194** |
| documents extracted under v038 | queue | `python -m kg queue status` | extracted **35**, skipped_oversize 3, deferred 156, queued 0, stale 0 |
| documents / chunks extracted (cross-check) | event log | distinct `doc_id` and `(doc_id, chunk_id)` on `chunk_metrics` events with `purpose=bulk_v038` in `events/batch-023.jsonl` | **35 docs, 1,198 chunks** |
| v038 nodes asserted (gross) | event log | `node_asserted` with `provenance.corpus_epoch=bulk-v038`, batch-023 | 12,856 (Concept 5,796; Claim 3,479; Definition 841; Measure 753; Practice 681; Standard 505; Instrument 289; Framework 235; Platform 164; Tool 113) |
| v038 edges asserted (gross) | event log | `edge_asserted`, same filter | 15,453 (`semantic_edge_refused` 226; 4 `extraction_superseded` overlays, stratum `semantic_edges` only) |
| v038 nodes in the live graph | Neo4j `seldon-ai-readiness-kg` | `MATCH (n) WHERE n.prov_corpus_epoch="bulk-v038" RETURN count(n)` | **10,305** (Concept 4,211; Claim 3,069; Definition 708; Measure 673; Practice 645; Standard 399; Instrument 215; Framework 170; Platform 120; Tool 95); distinct `doc_id` 35 |
| v038 edges in the live graph | Neo4j | `MATCH (a)-[r]->(b) WHERE a.prov_corpus_epoch="bulk-v038" OR b.prov_corpus_epoch="bulk-v038" RETURN count(r)` — edges carry no epoch property, so an edge is counted as v038 when it touches a v038 node | **11,914** |
| whole-graph nodes, KG labels only | Neo4j | label set = `kg/schema.yaml` `node_types` = Document, Definition, Concept, Construct, Instrument, Measure, Claim, Standard, Framework, Practice, Tool, Platform; `MATCH (n) WHERE any(l IN labels(n) WHERE l IN $ls) AND NOT n:Document RETURN count(n)` | **18,844** non-Document nodes (bulk-v038 10,305; v1 4,504; kernel-v03 3,755; null epoch 280) + 194 Document nodes |
| whole-graph edges, KG labels only | Neo4j | `MATCH (a)-[r]->(b) WHERE both endpoints carry a KG label RETURN count(r)` | **22,141** (projection fingerprint totals: nodes 21,874 incl. Seldon labels, edges 27,610) |
| pooled fabrication F, recomputed | `state/bulk_v038_burn.json` (read only) | sum `fabrications` / sum `facts` over `batches`; Wilson 95% with z=1.959964 | **37 / 1,480 = 0.0250, [0.0182, 0.0343]** |
| batch verdict tally | same file, `batches[*].outcome` | Counter | **accept 14, sampling_inconclusive 1 (b010), reject 0, quarantine 0** — 15 judged batches |
| b010 reason | same file, `batches[9].why` | verbatim | "33 admitted items < 55 facts needed for a decision; the plan cannot settle this batch" |
| SPRT parameters | same file | `sprt`, `min_facts_for_accept`, `sample_budget` | p0 0.05, p1 0.10, α=β=0.05; min 55; budget 463 |
| Group D evidence documents | `docs/crosswalk/usafacts_operationalization_skeleton.md` §5 | rows D1–D4, Evidence column | all four **gap**; **0** evidence documents — slide finding unchanged |
| crosswalk demand coverage | `state/t2_priority.json` × v038 `chunk_metrics` docs | sum `crosswalk_demand` over docs with demand; share whose doc is extracted | 43 of 43 units over 35 docs, 35/35 docs (see §3) |

Per-batch rows used for F (batch, facts, fabrications): b001 110/3, b002 110/3, b003 55/0, b004 55/0,
b005 220/11, b006 165/5, b007 55/0, b008 105/2, b009 110/1, b010 —, b011 110/3, b012 110/4, b013 55/0,
b014 110/2, b015 110/3.

## 3. Discrepancies (reported, not reconciled)

1. **§21.6 pooled F vs recomputation.** §21.6 states 37/1,474 = 0.0251 [0.0183, 0.0344] over
   "fourteen judged batches, 13 accept". The state file holds **15** batches with facts (b005 and b008
   are accepted tome batches with 220 and 105 facts, matching §21.5's own table), summing to 1,480 facts
   and 14 accepts. Same 37 fabrications; the difference is 6 facts and one batch in the count. Both are
   recorded here; the slide uses the recomputed 37/1,480 and the 15/14/1 tally because those are the
   measured values.
2. **Crosswalk demand units.** §21.6 and the brief say 41 of 41 units over 35 documents. The current
   `state/t2_priority.json` (regenerated 2026-09-02 02:30) sums to **43** units over the same 35
   documents (e.g. `odcs-open-data-contract-standard` now carries 3, the brief's ledger paragraph says
   2). Coverage is 100% either way; the unit total moved. Not edited anywhere (the brief's demand-ledger
   paragraph is outside this task's scope and is listed here as stale-but-untouched).
3. **Brief's demand-ledger paragraph** ("31 of those units, or 75.6 percent … 159 documents deferred")
   describes in-flight state; the queue now says 156 deferred / 3 skipped_oversize. Per the task's
   "nothing else in the brief changes", left as is and flagged.
4. **Node counts: event log vs graph.** 12,856 `node_asserted` events project to 10,305 live nodes
   because the projection MERGEs on `key` (same-key assertions within a document collapse) and applies
   the four `semantic_edges` supersessions. The brief's 09-01 figures (4,838 / 6,075) were gross event
   counts; the replacements are live-graph counts and say so.
5. **No other slide contradicted.** Slide 13 (G1), slide 16, slide 17 carry no corpus numbers; slide 18
   is a plan. Nothing else edited.

## 4. Files

- modified: `docs/crosswalk/deck_content_2026-09-01.md` (header v3→v4, `**Numbers:**` line, slide 15,
  closing note "none are floors")
- modified: `docs/crosswalk/meeting_brief_2026-09-01.md` (as-of paragraph; extraction/node paragraph;
  acceptance-sampling sentences in "The quality line")
- created: `docs/crosswalk/framework_deck_2026-09-02.pptx` (via
  `scripts/build_framework_deck.py --out docs/crosswalk/framework_deck_2026-09-02.pptx`; the script's
  existing `--out` flag was used, no code change)
- created: this RESULT
- rebuilt (not a file): Neo4j projection `seldon-ai-readiness-kg`, KG labels only

## 5. Verification

- `python -m pytest tests/ -q` → **594 passed** in 68.7 s (unchanged; no code touched by this task).
- `seldon verify` → all checks passed.
- Deck: 18 slides written, no splits; slide 15 bullets byte-equal to the content file after bold-marker
  stripping.
- Untouched, as constrained: `state/bulk_v038_burn.json`, `state/spend_ledger.jsonl`,
  `corpus/manifest.json`, `events/*`, `cc_tasks/2026-08-30_bulk_extraction_v038_RESULT.md`.
