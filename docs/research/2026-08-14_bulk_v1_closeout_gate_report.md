# Bulk v1 closeout — gate report

**Date:** 2026-08-14
**Task:** `cc_tasks/2026-08-14_bulk_v1_closeout.md`
**Baseline for deltas:** `docs/research/bulk_v1_gate_report.md` as generated
2026-07-17T13:59:31Z (71 docs). **Thresholds frozen — zero retuning. Fails are findings.**

> Note on the baseline artifact: `run_baseline_gates.py` writes to a fixed path, so
> the 07-17 file was overwritten in place by this run. Its values are transcribed
> below before the overwrite, and the prior version remains in git history.

## Gate table

| check | 2026-07-17 | 2026-08-14 | threshold | verdict | Δ |
|---|---|---|---|---|---|
| min_verified_included | 71 | 71 | 71 | PASS | — |
| grounding_zero_ungrounded | 0 | **0** | 0 | **PASS** | — |
| quarantine_rate | 0.0342 | 0.0343 | 0.0152 | FAIL | +0.0001 |
| edge_endpoint_validation | 750 | 747 | 0 | FAIL | −3 |
| orphan_rate | 0.0969 | 0.098 | 0.0034 | FAIL | +0.0011 |
| projection_drift | 0 | 0 | 0 | PASS | — |
| empty_extraction_rate | 0.0141 | 0.0141 | 0.1196 | PASS | — |

The doctrine-absolute gate — `grounding_zero_ungrounded` — holds at **0**. It did
not hold on the first run of this closeout; see "The 96" below, which is the most
important thing in this report.

## edge_endpoint_validation: −3 net, but the components are large

A naive read of 750 → 747 says the id-mismatch fix did nothing. It did; the
movement is masked by the re-extraction landing in the same run.

| step | value | Δ |
|---|---|---|
| baseline, pre-closeout, pre-re-extract | 750 | — |
| + `edge_endpoint_alias` overlay, 8 aliases (item 3a) | 736 | **−14** |
| + `extraction_superseded` overlay (item 2) | 724 | −12 |
| + the NEW OECD extraction's own citations | 748 | +24 |
| + FCSM adjudication, 9th alias (operator rule) | **747** | **−1** |

The (a) fix removed exactly the refs it aliased — no more, no less. The +24 is
the full 56-page OECD report citing 24 more external works than the partial web
capture did: the (b) surface grew because a better source cites more. Both
remaining failures are the pre-registered heterogeneous-corpus findings, not
regressions.

## FCSM adjudication — branch fired: `bare_title -> fcsm-20-04`

The one endpoint the conservative rule could not resolve
(`doc-fcsm-framework-for-data-quality`, ambiguous between FCSM 20-04 and 23-02) was
resolved by operator rule on 2026-08-14: *resolve by grounding span; numeric/year
match wins; bare title maps to 20-04; else defer.*

Evidence — `edge_asserted acac0af1…`, batch-002, citing `fcsm-25-03`, location
"Challenge & Opportunity (p.3)":

> "The Federal Committee on Statistical Methodology (FCSM) developed the Framework
> for Data Quality to help analysts and the public assess fitness for use of data sets."

| branch | fired | why |
|---|---|---|
| numeric / year match | **no** | No numeric or year identifier for the *cited* work. The only numbers in the citing document are `25-03` (×2) and `2025`, which identify `fcsm-25-03` itself. |
| bare title → `fcsm-20-04` | **YES** | Bare title, no number, no year, no qualifier; the span states the framework's *purpose* ("assess fitness for use of data sets"), which is the framework document. Corroborating negative evidence: `case stud` occurs **nowhere** in the citing document, excluding `fcsm-23-02` on its own distinguishing feature. |
| defer | no | not reached |

The span was confirmed to ground against the current source (`is_grounded` = True)
before the adjudication was trusted — necessary because this edge lives in
batch-002, the pilot shard the grounding gate treats as legacy and does not
re-verify. Recorded as `edge_endpoint_alias aa435c02…` in batch-005 with the full
three-branch trace. Mutation-checked: removing this single alias moves the count
747 → 748, delta exactly 1.

Residual composition of the 747: **all** are `cites` edges whose targets are
unmanifested external works (item 3b). Zero are doc-id mismatches that the
conservative rule could resolve. The register is
`corpus/staging/refetch_candidates.jsonl` — **721 candidates, 747 refs**, sorted by
citation count, with citing-doc provenance and example grounding spans. **Nothing
was manifest-added from it.**

The register's ref count equals `edge_endpoint_validation` exactly (747 = 747) —
every remaining violation is accounted for as a refetch candidate, and no violation
is silently unclassified. That identity is the check that the (a)/(b) decomposition
is complete.

## The 96 — a gate catching the author of the fix

The first gate run of this closeout returned **`grounding_zero_ungrounded = 96`**,
and the task's instruction was to STOP rather than proceed. Doing so was correct,
and the cause was this closeout's own change:

`check_edges` was taught to honour the `extraction_superseded` overlay.
`check_grounding` was not. That check re-verifies every span against the
document's *current* canonical source — so the superseded OECD extraction's spans
were re-verified against the PDF that replaced them, and all 96 failures were that
one doc.

This was not a real grounding breach; no ungrounded item was ever admitted. But
the gate was right to fire: the event log genuinely contained assertions that do
not ground against the corpus as it now stands. A gate that only fired on
"real" breaches would have missed it.

**Fix:** the overlay was hoisted into a shared `live_events()` consumed by
grounding, edges, quarantine, and empty — patching one check and not its sibling
is the defect, so the shared helper is the remedy rather than a second patch.
`check_quarantine` had the same exposure by a different route: it sums
`build_metrics`, and a superseded doc now has two, so OECD was double-counted.
`build_metrics` carries no source sha, only an `extraction_event_id`, so that id
is mapped to a sha through the assertions it produced rather than resolved by
"keep the newest timestamp".

Quarantine rate moved 0.0342 → 0.0343 across the closeout — consistent with one
doc's metrics being replaced (99n/137e/7q → 83n/139e/7q), not double-counted. Had
the double-count survived, this number would have been visibly wrong in a
direction nothing else would have flagged.

## Verification

Both overlays were mutation-tested rather than read:

| overlay | neutered | with | delta | matches |
|---|---|---|---|---|
| `edge_endpoint_alias` (8 conservative) | 738 | 724 | 14 | the 14 aliased refs exactly |
| `edge_endpoint_alias` (9th, adjudicated) | 748 | 747 | 1 | the single FCSM ref |
| `extraction_superseded` | 736 | 724 | 12 | the superseded extraction's cites |

Projection end-state verified directly in Neo4j: **0** nodes carry the superseded
sha `7e740330…`, **83** carry the new `798d84db…`, the Document node's
`content_hash` reads the PDF, and there are **71** distinct Document nodes.

## Known cosmetic defect (not fixed — out of scope)

`build_projection.py` reports `documents: 72`. It increments per `manifest_add`
event and OECD now has two (the original and its supersession). The graph is
correct — 71 distinct Document nodes, verified by direct query. The counter is
wrong, not the projection. Left as a finding rather than fixed, since the task
scoped changes to the id-mismatch mechanism.
