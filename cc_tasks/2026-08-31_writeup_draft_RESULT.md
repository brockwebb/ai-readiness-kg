# RESULT — Writeup draft v1

**Task:** `cc_tasks/2026-08-31_writeup_draft.md`. No ADDENDUM siblings existed at dispatch or
at close. **Deliverable:** `docs/research/writeup_draft_v1.md`, 4,143 words, within the
3,000–4,500 target. **Spend: zero.** Authoring only; no model call, no ledger declaration
needed. A burn was writing throughout, so burn state was read from a snapshot stamped
`2026-09-01T03:10:29Z` and no burn file or queue entry was touched.

`docs/research/writeup_foils.md` was read in full before anything else and its corrections
govern. The Karpathy characterization in the draft is the corrected one: lint is a real quality
mechanism that measures coherence rather than correspondence, with no denominator, rate, or
gate. The draft nowhere claims the pattern lacks a quality mechanism.

**Task closure:** this registered file is closed. `f1da94c6` is left open, per the task; it
closes when the operator accepts a final version, not when a draft exists.

## Sources of record for every number

| section | figures | source |
|---|---|---|
| §3 arms | A 0.0385/96, 60/60, 15.70 (0.347), recall 0.897; A2 0.0243/154, 72/73, 24.30 (0.537), 0.905; A3 0.0000 [0, 0.0464]/79, 46/46, 25.34 (0.5603), 0.888 | chunked pilot RESULT, §3 closure table |
| §3 floor | 45.23 = 16.95 nodes + 28.27 edges; 62.5% edges; node-basis 10.17; re-derived 5.16 = 0.60 × 8.60 | ground_truth_yield_floor RESULT |
| §3 ground truth | mean 8.60, median 1, range 0–28, sd 12.2, n = 5; 42 of 43 items in 2 chunks | same |
| §3 comparator | 0.93× ground truth on nodes; 0 nodes / 21 edges on a references chunk; 1,244 vs 382 edges over 44 chunks | same, §4.3 |
| §4 gate | F_upper 0.0715, item-faithful 0.7705 (94/122), 160 facts, 30 chunks, 28 docs, 4 strata, PASS | bulk_v038 RESULT §3.5; `state/bulk_v038_phase_a.json` |
| §4 SPRT | p0 0.05, p1 0.10, α = β = 0.05, ASN 158.6, budget 463, minimum 55 | bulk_v038 RESULT §2 |
| §4 batches | 3/110 (0.0273 [0.0093, 0.0771]); 0/55 (upper 0.0653); 5/165 (upper 0.0690) | `state/bulk_v038_burn.json` snapshot |
| §2, §4 corpus | 194 admitted, 94 substrate, 31 extracted, 308 chunks, 4,838 nodes, 6,075 edges, 93 refusals, 159 zero-demand deferrals | queue projection and event replay, snapshot |
| §5.7 ceiling | per-batch means 49k–54k; 10-observation window 21% low | bulk_v038 RESULT §19.3 |
| §7 agreement | rater agreement 0.909–1.000 | batch aggregates, bulk_v038 RESULT |

Numbers that move before burn close carry the `[as of 2026-09-01T03:10Z; final at burn close]`
marker: the three batch verdicts and the corpus totals in §2 and §4.

## One discrepancy, reported not reconciled

The task's thesis line says "eight instances of tests measuring artifacts instead of
generators". The live record is **nine**. The foils document, dated 2026-08-30, says sixth; the
ingestion task file, written later the same day, says the eighth had arrived and asked that a
ninth be avoided; the ninth was recorded today in `2026-08-31_ingestion_conversion_RESULT.md`
§8.2, where the admission gate's tests were found to drive the gate's own entry point while
nothing connected it to the admission path. The draft reports nine and states the discrepancy
in §5.5 rather than silently adopting either count.

The companion count in the thesis, four instances of derived identity moving under provenance,
is exact. The fourth was recorded today in the extent-remediation RESULT §3.2.

## Judgment calls in the draft, recorded

**Scope of §5.7.** The spend-guard crash and the ceiling estimator are today's findings and
postdate the foils document, so they are not in its exhibit list. They are included because
they are the same genus as the rest: a monitor whose own failure mode was untested. If the
operator wants the draft confined to the foils' exhibits, §5.7 is the section to cut.

**Nothing claimed about relations.** Per the constraint, the draft claims no semantic-edge
validation anywhere. The 93 refusals are reported as refusals. The limitation section states
plainly that 63 percent of the original target is unvalidated and that the system's response
was to close bulk relation extraction rather than validate it.

**Census framing kept to its weight.** The analogy carries the frame in §1 and sharpens once in
§5.1, where it becomes a margin of error computed on a different universe than the estimate.
It is not repeated elsewhere.

**Judges are models, and the draft says so.** The limitations section states that both judges
are from the extractor's family and that rater agreement measures consistency rather than
correctness, with a human-adjudicated subsample named as the obvious next instrument.

## Style compliance

Zero em-dashes, zero bold in prose, no one-sentence paragraphs, none of the banned words,
"confabulation" used in place of "hallucination" where the concept appears. Checked
mechanically rather than by eye.

## Not done

No figures or tables beyond the prose. No bibliography with full citations; prior art is named
in the closing section with what was taken and what was changed, and the final version will
need proper references. No abstract. These are v2 items and are not represented as complete.
