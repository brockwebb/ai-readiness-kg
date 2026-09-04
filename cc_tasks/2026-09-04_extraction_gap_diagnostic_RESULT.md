# RESULT: Diagnosis of the 72 unextracted Documents

**Task:** `cc_tasks/2026-09-04_extraction_gap_diagnostic.md` (no addenda: globbed `…_ADDENDUM*.md`, none exist). **Date:** 2026-09-04 UTC. **Spend: zero model calls** — diagnosis only; nothing was extracted, nothing was reserved on the spend ledger. **Task file committed before execution:** `3e257ff`.

**The answer: the gap is not a failure. It is 55 deliberate deferrals with a recorded reason and 17 documents nobody ever asked for.** Zero failed runs, zero missing sources, and — the result that matters most — **zero `run_ok_no_edges`**, so the extraction→projection path is exonerated. What the diagnosis does surface is a structural fact: **admission does not enqueue extraction**, so "never queued" is the pipeline's normal state after a document is admitted.

## 1. The classification

`scripts/extraction_gap_diagnostic.py` (Script `4387c2b4`) → `state/extraction_gap_2026-09-04.json` (DataFile `14bf4cdd`, snapshot) → **16 Results** named `kg_diag_gap_*`.

| class | count | root cause, with citation |
|---|---:|---|
| `excluded_by_design` | **55** | 53 carry an `extraction_deferred` event with reason **`no consumer`**, all written 2026-08-31T14:57–14:58 in one bulk decision. The rule is the demand-pull cut of **DD-024** ("bulk semantic-edge extraction is closed; semantic edges are demand-pull adjudications"), executed and recorded in `cc_tasks/2026-08-30_bulk_extraction_v038_RESULT.md` §0.3 as **EXTRACT 35 / DEFER 159**. 2 more are cut with reason: `ddi-codebook-specification` (`conversion_gap` — docling produced 2,152 chars from 7,139 visible at link density 0.371, under the converter's floor) and `itu-ai-ready-analysis-…` (`extent_unremediable` — "CUT WITH REASON, not remediated. The publication is served only through ITU's JavaScript e-publications reader; the page carries no PDF or download link"). |
| `never_queued` | **17** | Exactly the `g1eval-2026-09-02` epoch — the G1 prior-art sources. No `extraction_request` was ever emitted for any of them, and no `extraction_deferred` either: no decision exists on the record in either direction. |
| `queued_not_run` | **0** | — |
| `run_failed` | **0** | — |
| `run_ok_no_edges` | **0** | **The loader is exonerated.** All 139 documents with extraction history have edges, and no gap document has any extraction history. No Issue is owed on this ground and none was invented. |
| `source_missing` | **0** | All 72 sources are on disk: 46 pdf, 24 md, 2 html, 78,295,179 bytes total, median 547,324. |

**Per-document facts recorded** (in the JSON, all 72): source format, byte size, corpus epoch, admission timestamp, `content_hash` presence, queue state, path, and the reason string for its class. All 72 carry a `content_hash`. Epochs: `triage-2026-08-24` 33, `g1eval-2026-09-02` 17, `acquisition-round2-2026-08-30` 16, `crosswalk-2026-08-29` 5, `v1` 1.

**The one `v1` document is the ITU cut** (`itu-ai-ready-analysis-towards-a-standardized-readiness-frame`). Its history: `model_call` and `doc_state validated` on 2026-07-09, then `extraction_deferred` 2026-08-31, then `conversion_gap` and `extent_unremediable`. So the standing claim in `CLAUDE.md` — *"corpus epoch v1 frozen at 71 docs, 71/71 extracted"* — does not hold against the graph: one v1 member contributes no edges, because its source could never be converted. Reported, not edited.

## 2. Overlap with the CQ failures

Twelve CQs were examined — the 6 that were `no`/`partial` in the collapsed view and the 8 flagged `misleading_raw` (union of the two sets). Search terms were taken **from each CQ's own Cypher** (`CONTAINS '…'` literals) rather than chosen here, so the overlap is a count and not a judgment; the three structural CQs carry no literal terms and **no terms were invented for them**. Text came from the converted markdown substrate where it exists (25 of 72) and from the file itself otherwise (pypdf for the 46 PDFs): **72 of 72 documents yielded readable text.**

| CQ | collapsed | misleading | unextracted docs mentioning its terms | terms |
|---|---|---|---:|---|
| CQ-01 | partial | | **27** | confidence interval, margin of error, uncertain |
| CQ-02 | partial | | **23** | ai ready, ai-ready |
| CQ-05 | yes | yes | 21 | completeness |
| CQ-06 | yes | yes | 54 | documentation, metadata |
| CQ-13 | partial | yes | 27 | interoperab |
| CQ-21 | partial | yes | 8 | 9309, robots |
| CQ-22 | yes | yes | 15 | dcat, schema.org, sitemap |
| CQ-23 | yes | yes | 14 | mcp, model context protocol |
| CQ-24 | yes | yes | 5 | llms.txt |
| CQ-14, CQ-15, CQ-20 | partial/no/yes | | not term-testable | structural queries, no literals |

**All 9 term-testable CQs have at least one unextracted document mentioning their terms** (`kg_diag_gap_cqs_with_unextracted_evidence` = 9 of 9). The two CQs that failed hardest on substance are the two with the most unextracted evidence behind them: CQ-01 (uncertainty definitions — 27 documents) and CQ-02 (AI-ready data definitions — 23). **This is a count of what the coverage gap might have contributed. It is not a claim that extracting them would have changed any verdict** — the terms may appear in passing, and CQ-01's failure was that no document defines uncertainty *for a data product*, which more source text may or may not fix.

## 3. Estimate — computed, not executed

The §3 set is the classes extraction would close: `never_queued` (17) + `queued_not_run` (0) + transient `run_failed` (none exist).

| | value |
|---|---|
| documents | **17** |
| chunks under the pipeline's current chunking | **664** |
| tokens the DD-022 guard would reserve | **13,280,000** at the 20,000 `extraction_chunk` floor |
| standing daily band (`controls.yaml` `spend.daily_tokens`) | 55,000,000 |
| **inside the band?** | **YES** — 24% of one day's band |

Secondary figure, priced but explicitly **not** in the §3 set: reviving the 55 deferred documents would add 1,024 chunks / 20,480,000 tokens, for **33,760,000** in total — still inside the band. That is a decision to reverse DD-024's demand-pull cut, not a gap to fill, and this task does not make it.

The floor is the guard's *first-call* estimate and the runner switches to the run's measured mean once it has settles, so both figures are upper bounds. **Nothing was run and nothing was reserved.** No operator touchpoint is triggered: the estimate is inside the standing band.

## 4. Findings registered, no fix

**Issue `609cb10b` — admission does not enqueue extraction (the structural defect §4 asks about).** 233 documents carry a `manifest_add`; **68** have ever had an `extraction_request`; **165 admitted documents have never been requested**. Code location: `kg/manifest.py` emits `manifest_add` and nothing else — grepping it and `kg/eventlog.py` for `extraction_request` returns nothing. A request is emitted only by a later explicit action (`kg/queue_cli.py:174`, or `scripts/run_bulk_extraction.py:369` for the `--docs` override). The gate is deliberate and defensible — `kg/queue.py:132` enforces preconditions at emit, and DD-024 makes extraction demand-pull — but the consequence is that a document can be admitted, hashed, projected and cited while contributing nothing, **with no event recording that any decision was taken**. The 17 `never_queued` are exactly that; the 55 deferred are the contrasting case, where the decision is on the record and revivable.

**Issue `2e226acb` — 22 admitted documents have no `Document` node at all.** Found while classifying, outside the task's premise. They are three whole epochs: `g1sfc-2026-09-03` (17 product surfaces), `g1srp-2026-09-03` (4 producer rules), `g1dp-2026-09-02` (1 DAS handbook) — all admitted as **G1 EVAL fixtures** rather than KG source material, all postdating the last projection replay. So the corpus contributes nothing from **94 of its 233 documents**, not 72 of 211. Whether a fixture surface captured for an eval *should* become a Document node is a real question this task does not answer; the point is that the discrepancy should be visible rather than latent.

**No Issue was owed for a `run_ok_no_edges` loader defect** — the class is empty. **No Issue was owed for an undocumented exclusion rule** either: the `no consumer` deferral is documented as a standing decision in DD-024 and as an execution record in the v038 RESULT §0.3, and the reason vocabulary is documented by example in `kg/schema.yaml` (recorded in that RESULT: `extraction_deferred.reason` is free text). It is worth saying that this documentation lives in a task record and a schema example rather than in a rule doc of its own — a weaker form than a DD — but the §4 condition is "not written down anywhere", and it is written down.

## 5. Integration

| check | value |
|---|---|
| root `tests/` | **752 passed** (unchanged; this task added a script and no library code) |
| `assessment/` | **471 passed, 1 skipped** (unchanged) |
| `seldon verify` | **All checks passed** — after `seldon ontology sync` (the replica had fallen to epoch 4 against master epoch 6; synced 6 new, 103 updated, 0 deprecated) |
| artifacts | Script `4387c2b4`, DataFile `14bf4cdd`, 16 `kg_diag_gap_*` Results, Issues `609cb10b` and `2e226acb` |

## 6. Premises contradicted by live state

1. **"72 of 211" understates the gap.** 22 further admitted documents have no Document node, so 94 of 233 corpus documents contribute nothing (§4). The premise was right about what it measured; it measured nodes.
2. **`CLAUDE.md`'s "v1 frozen at 71 docs, 71/71 extracted" does not hold against the graph** — one v1 member (`itu-ai-ready-…`) contributes no edges, cut as `extent_unremediable` (§1). Reported, not edited: `CLAUDE.md` is outside this task.
3. **The queue's own `extracted` count is 35, not 139.** `kg.queue.project()` scores extraction against the **pinned profile** (`bulk_v038`), while the graph holds edges from earlier profiles. Both are correct under their own definition; a reader comparing them without knowing that would think 104 documents had lost their extractions.
4. **Two of my own script's first drafts were wrong and are recorded in it.** `canonical_paths()` swallowed an `ImportError` and returned `{}`, which made all 72 look like they had no source file on disk — the exact wrong answer to the question the script exists to ask; it now fails loud and uses the same `dixie_config(REPO / "dixie_evidence.yaml")` call the runner uses (`run_bulk_extraction.py:174`). And the cut-citation picked the *last* cut event, quoting a `conversion_gap` payload dict where an `extent_unremediable` carried the actual reason; it now prefers the decision event over the conversion note.
5. **`extraction_deferred` is revivable, so `excluded_by_design` is not permanent exclusion.** The v038 ADDENDUM-02 is explicit: "Revivable by any later `extraction_request`". The class fits — a documented rule excluded these documents from bulk scope — but the exclusion is a scope decision, not a judgment that the documents are unfit.
6. **The 17 `never_queued` are one whole epoch, not a scatter.** They are the `g1eval-2026-09-02` prior-art sources, admitted for citation in the G1 memo; the framework deck already says "17 of them G1-EVAL prior-art sources admitted 2026-09-02, **not yet extracted**". The gap was known and stated in prose; it had never been counted or classified.

## 7. Out of scope

Extraction itself — not run, and its cost is priced above for whoever decides. Entity resolution (`93a628e8`) — untouched, and this diagnosis is the precondition it was waiting on: **coverage is now explained, so a dedup pass would not be running over a corpus about to change underneath it.** No change to `CLAUDE.md`, to DD-024, or to the queue.
