# RESULT — Meeting brief

**Task:** `cc_tasks/2026-08-31_meeting_brief.md`. No ADDENDUM siblings existed at dispatch or
at close. **Deliverable:** `docs/crosswalk/meeting_brief_2026-09-01.md`, 996 words.
**Spend: zero.** Read-only against a snapshot; no ledger declaration was needed because no
model call was made.

**Snapshot discipline.** A burn was writing to `events/batch-023.jsonl` throughout, so every
shard, `corpus/manifest.json`, the burn state and the spend ledger were copied to a scratch
snapshot stamped `2026-09-01T02:57:06Z` and read only from there. The burn's files, queue and
shards were not touched. The brief names its own as-of time and says coverage is a floor.

## Numbers, and where each came from

| figure | value | source of record |
|---|---|---|
| documents admitted | 194 | `queue.status_totals()`; reconciles with 194 `manifest_add` events |
| substrate files | 94 | `state/substrate_md/` |
| documents extracted | 31 | distinct `doc_id` on `chunk_metrics` where `purpose=bulk_v038` |
| chunks | 308 | distinct `(doc_id, chunk_id)`, same source |
| nodes / edges | 4,838 / 6,075 | `node_asserted` / `edge_asserted` at `corpus_epoch=bulk-v038` |
| node types | Concept 2,040 … Tool 29 | `payload.type` on the same events |
| Phase A gate | F_upper 0.0715, item-faithful 0.7705, 160 facts, 28 docs, PASS | `state/bulk_v038_phase_a.json` |
| batch verdicts | 3 accept: F_hi 0.077 / 0.065 / 0.069 at 110 / 55 / 165 facts | `state/bulk_v038_burn.json` |
| semantic-edge refusals | 93 | `semantic_edge_refused` events |
| crosswalk demand | 41 over 35 documents | `state/t2_priority.json` |
| scoped coverage | 31 units, 75.6% | frozen plan minus deferrals, demand-weighted |
| with b014/b015 | 35 units, 85.4% | + odcs 2, slsa 2 |
| deferred | 6 docs / 6 units below scope; 159 docs at zero demand | `queue.deferrals()` by reason |

The 75.6% and 85.4% figures confirm ADDENDUM-02's projected ~76% and ~85% against live state
rather than restating them.

## Two things measurement changed

**The coverage number depends on what "covered" means, and the naive reading flatters.**
Counting a document as covered when it has any node at all gives 80.5%. That is wrong here:
the deferred long specifications each hold one or two chunks from the Phase A qualification
draw, so a document extracted at 1 of 207 chunks would count as fully covered. The brief
reports the frozen plan's scoped set instead, which is the set that will actually be complete.
Fully-extracted-right-now is 39.0%, and that figure is not in the brief because it measures
how far through the burn the clock happens to be rather than anything about the corpus.

**Group D is an empty row, and that is the finding.** The first mapping pass counted 1 named
evidence document for group D. That was the Tier column (`agency_instrumented`) matching the
doc_id pattern. With tier tokens excluded, group D names zero evidence documents across all
four of its indicators, all four already marked as gaps in the skeleton. Openness is the
thinnest part of the picture and it is a corpus gap, not an extraction gap. The brief says so
plainly, per the task's instruction that empty cells are findings.

Also worth recording: of the 29 documents carrying nodes in the graph, zero are unnamed by the
skeleton. The burn set and the operationalization's evidence list agree completely, which is
what demand-pull cutting is supposed to produce.

## Mapping method

The table maps each indicator group to the documents the skeleton itself names as evidence for
it, then counts what the graph holds from those documents. This was chosen over concept or
text search because the skeleton's own mapping is the least judgment-laden available, and the
task asked for honesty about where mapping is judgment. Node counts are per group after
deduplicating documents cited by several indicators in the same group.

## Constraints observed

No claim about relations beyond `cites`; the 93 refusals are reported as refusals, not as
relation coverage. No em-dashes, no bold in prose, none of the banned words, and every quality
number carries its interval or its n. Nothing was estimated: figures not derivable from the
ledgers were omitted.
