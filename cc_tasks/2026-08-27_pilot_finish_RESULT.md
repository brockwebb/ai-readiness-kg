# RESULT — `cc_tasks/2026-08-27_pilot_finish.md` (Seldon ea7dd3bd)

**Executed:** 2026-08-27, 21:25Z–22:00Z. **Outcome: both strata FAIL. No v0.3.6. Lanes 2 and
3 have no passing profile.** Thresholds were not moved at any step; §4 was skipped by §3b's
own pre-registered rule, not by judgment.

| step | state |
|---|---|
| §1 band raise 55M → 75M, committed | done (`63e52f0`) |
| §2 Instrument verdict on disk | done — **FAIL** |
| §3 §3b edge-suppression verdict on disk | done — **FAIL (0.607 < 0.85)** |
| §4 v0.3.6 + `pilot_v036_edges` | **not run** — §3b did not pass |
| §5 Lanes 2/3 not launched | honoured (and now moot: no stratum passed) |
| §6 band reverted to 55M, `seldon cc complete`, RESULT, push | done |

## §0 premises — verified against live state

| premise | verdict |
|---|---|
| `controls.yaml spend.daily_tokens = 55,000,000` | **true** |
| `over_daily` refusals at 18:53Z for `restoration_v2_resume` and `pilot_v035b_opus5` | **true** — 18:52:59.813Z (est. 62,535) and 18:53:08.991Z (est. 127,843) |
| Lane 4 is pid **70596**, in `daily_band_sleep` until 00:05Z | **false in the pid** — 70596 is gone. The status file's own detail says stage 2 was killed by the driver's subprocess timeout ("timed out after 3898 seconds") at 18:52:59Z. The process sleeping to `2026-08-28T00:05:00Z` is the **driver, pid 70576**, which will relaunch stage 2 on wake. Left untouched; confirmed alive at 21:56Z (05:56 elapsed). |
| Pilot process is pid **91558**, may be alive and sleeping — kill it | **false in the pid, true in substance** — the live pilot was chain `91292` → child `91293`, in `daily_band_sleep` to 00:05Z. Killed both at 21:26Z as instructed; the task relaunched the pilot explicitly. |
| `pilot_v035b_opus5` re-declared at 9M per ADDENDUM-05 §0 | **true** — declare at 18:29:28Z, `supersedes_prior_ceiling: 4,000,000` |
| Doc 5 status contested (handoff says pooled 24; verdict/status say 23 from 4 docs) | **resolved from the shard, as instructed: doc 5 IS extracted.** `events/batch-013_reextract_v035b.jsonl` holds 24 `node_asserted` + 21 `edge_asserted` across all five docs, `mitre-ai-maturity-model` contributing 1 Instrument and 18 semantic edges. The "23 from 4 docs" figures predate the doc-5 run. No re-extraction was needed and none was run. |
| §3a triage counts on disk (89 locatable, 52 `single_span`) | **true** |

## §1 — band raise, and one property of the guard

`daily_tokens: 55_000_000 → 75_000_000`, committed as specified (`63e52f0`); reverted to
`55_000_000` at close (§6). `python -m kg.spend status` confirmed both edits live.

**Property the operator asked about:** `kg/spend.py` reads `controls.yaml` inside every
`reserve()` (`_spend_config()`, documented "read at call time, never cached"). The raise
therefore reached *already-running* processes too, not only ones started after the edit —
which is why Lane 4's sleeping driver would have seen 75M had it woken before the revert. It
did not; it sleeps past the 00:00Z roll, so the raise was pilot-only in practice, as the task
predicted.

**Note on the revert:** committed today is 57.24M against a reverted 55M band, so any further
reserve today is refused `over_daily` until the 00:00Z roll. That is the intended scoping of
a task-local raise, and Lane 4 wakes after the roll.

## Ceiling arithmetic actually used

From the ledger's per-class running means at task start (`settled ÷ calls`): extraction
224,537/call, judge 58,756/call, cleanup 82,115/call.

- **§2 Instrument judge** — no new ceiling declared; ran inside `pilot_v035b_opus5` (9M,
  already declared by the operator per §0). Remaining work at start: 89 facts × 2 raters ÷ 10
  per batch = 18 calls, 4 already banked ⇒ ≈ 14 × 128K ≈ 1.8M against 4.4M remaining. Actual
  new spend on that run this task: 5,517,758 − 4,602,646 = **915,112**.
- **§3b** — ceiling **2,000,000** (declared by the phase, `judge` class). Estimate: 89
  candidates ÷ 10 × 2 raters = 18 calls × 58,756 ≈ 1.06M, plus decompose (edge candidates
  decompose deterministically, 0 model calls) ⇒ ≈ 1.1M, inside 2M. Actual **1,323,023** over
  18 calls (73,501/call).
- **§3d** — never declared; §3b failed.

## Per-run ledger at close (`python -m kg.spend status`)

| run | class | ceiling | settled | calls | mean | refusals |
|---|---|---|---|---|---|---|
| `pilot_instr_sem` | extraction | 3,000,000 | 1,050,000 | 4 | 262,500 | 0 |
| `pilot_v035` | extraction | 3,000,000 | 1,532,559 | 6 | 255,426 | 0 |
| `pilot_v035b_opus5` | extraction | 9,000,000 | 5,517,758 | 40 | 137,943 | 2 |
| `edge_suppression_judge` | judge | 2,000,000 | 1,323,023 | 18 | 73,501 | 0 |
| `restoration_v2_s1` | cleanup | 55,000,000 | 21,514,241 | 262 | 82,115 | 0 |
| `restoration_v2_s2` | judge | 55,000,000 | 7,458,511 | 124 | 60,149 | 0 |
| `restoration_v2_resume` | judge | 55,000,000 | 18,629,307 | 320 | 58,216 | 1 |
| `restv2test` | cleanup | 1,000,000 | 0 | 0 | — | 0 |

`committed_today` 57,238,004. This task's own spend: **2,238,135** (915,112 pilot + 1,323,023
edge judge).

## Per-doc extraction cost (the corpus-mean question)

This task ran **no extraction** — doc 5 was already on the shard. The numbers below are the
measured usage of the five v0.3.5b Opus-5 extractions, summed from the persisted raws in
`events/raw/reextract_v035b_pilot/` (4-key usage sum, the same quantity the ledger settles):

| doc | tokens | emission |
|---|---|---|
| `data-readiness-for-ai-a-360-degree-survey` | 1,330,683 | per_layer |
| `aidrin-hiniduma-2024` | 903,365 | per_layer |
| `from-accuracy-to-readiness-metrics-and-benchmarks-for-human` | 866,717 | per_layer |
| `fcsm-23-02-a-framework-for-data-quality-case-studies` | 426,215 | single_pass |
| `mitre-ai-maturity-model` | 398,880 | single_pass |
| **total / mean** | **3,925,860 / 785,172** | 3 of 5 needed the per-layer fallback |

**The ~977K/doc figure used to size Lane 2 in the task file, and the ~1,103,551 the verdict
script printed, are both too high.** The script divides the whole run (extraction + decompose
+ judge) by 5. Measured extraction alone is **785,172/doc**, and it splits cleanly: per-layer
fallback docs cost 866K–1,331K, single-pass docs 399K–426K. Lane 2 at 134 docs ≈ **105M**, not
130M+. The operator's open question about unit cost should use these numbers; the per-layer
fallback, not the whole-document call, is what doubles a doc.

## §2 — Instrument stratum: FAIL

`docs/research/2026-08-27_pilot_instrument_verdict.md` (script's verdict + a diagnosis section
added by this task, marked as such).

| | value | pre-registered | pass |
|---|---|---|---|
| F | 0.0769 | — | — |
| F_upper | 0.1578 | < 0.10 | **N** |
| item-faithful | 0.2917 (7/24) | ≥ 0.70 | **N** |

Pooled precondition met (24 Instruments ≥ 20, all five docs). 89 facts, 78 in the
F-denominator, Dawid–Skene (crowd-kit, n_iter=100); rater agreement with MAP 1.00 (opus-4-8)
and 0.966 (sonnet-5).

**What the failure is.** v0.3.5 fixed *admission* — 24 Instruments pooled where v0.3.4 failed
the precondition outright. What binds now is the `method` attribute: 27 of 34 non-entailed
facts are `span_truncated` and 26 of those are `method`. Item-faithfulness collapses because
one bad `method` fact condemns an item. Inside those 27, two distinguishable populations: 14
whose every content word *is* in the attribute's own span (the decomposer redistributed a
coordination — "profiling, cleansing, and monitoring" → one fact per conjunct — and both
raters called the redistributed form not span-entailed), and 13 where the model quoted a
fragment cut mid-noun-phrase. The first is a question about the pre-registered probe protocol;
the second is an extraction fix. Neither is a threshold adjustment, neither was made here.

**Consequence:** Instrument stratum stays closed. Lane 2 gets **no** `superseded_strata:
[instrument]` eligibility.

## §3 — semantic stratum: FAIL

`docs/research/2026-08-27_edge_suppression_judge_verdict.md`. Sample: all 89 locatable §3a
candidates (52 `single_span` + 37 `evidence_set`; cap 120 not binding, seed
`Random("edge_suppression")` recorded in `scripts/addendum05_pilot.py`), evidence sets
presented as grounding.

**Fact-level entailed 54/89 = 0.607**, against a pre-registered pass of ≥ 0.85 ⇒ the
diverted relations are mostly unfaithful, v0.3.5's rule is doing its job, **no v0.3.6**.

Three findings recorded in the verdict:

1. **ADDENDUM-06's premise does not survive measurement.** The 52 `single_span` candidates —
   the direct evidence for "the model over-diverted" — are 35/52 = 0.673 entailed.
   `evidence_set` candidates are 19/37 = 0.51.
2. **§3a's proxy is weak.** Endpoint surface forms + a predicate cue co-occurring in one
   sentence predicts faithfulness at 0.67; within ≤ 3 sentences, at 0.51. Co-occurrence is
   not assertion — the standard distant-supervision false positive, and the reason
   DocRED-style evidence sentences are hand-labelled. A future triage needs a relation-stating
   test.
3. **The unfaithfulness is in the graph, not only in the diverted set.** Live kernel-era
   semantic edges for these docs: 40/66 = 0.61 entailed. Diverted v0.3.5b candidates: 14/23 =
   0.61. Identical. Of 35 not-entailed, 23 are `fabrication`. This is a graph-quality finding
   about live `has_component`/`subtype_of` edges (`has_component` 0.62, `subtype_of` 0.44),
   out of scope for this task and flagged for whatever addresses the semantic layer next.

## §5 — Lane 2 / Lane 3 eligibility

**None.** Neither stratum passed, so there is no passing profile and no superseding scope:

| lane | eligibility |
|---|---|
| Lane 2 (`superseded_strata`) | not eligible — Instrument FAIL, semantic FAIL |
| Lane 3 (bulk under a passing profile) | not eligible — requires both strata |

Not launched (the task's §5 override was moot in the event). `reextract_v035` remains the
newest profile and it is not validated for bulk. The instrument-only Lane 2 scope
(`superseded_strata: ["instrument"]`) is **still unimplemented** in `scripts/overnight_burn.py`
— `lane2` supersedes both strata — and stays that way; nothing passed to justify building it.

## Discrepancies and defects found (reported, not reconciled)

1. **Lane 4 / pilot pids in §0** — see the premise table. Substance held, pids did not.
2. **`probe_decompose` resume was broken** (fixed, `156a91c`, mutation-proven). Its done-set
   held item_ids while the test read `it["item_id"] in done and it["event_id"] in done`; the
   second conjunct could never be true, so the post-refusal relaunch re-decomposed all 24
   Instrument items and appended a second copy of the fact set (177 lines for 89 facts,
   ≈ 315K spent before it was caught). Because `fact_id` hashes the sample's `event_id` and
   `addendum05_pilot` rebuilt the sample with fresh uuids, the 40 judge labels already paid
   for were orphaned as well. Three fixes: `(item_id, event_id)` pairs in the done-set;
   `write_sample` reuses an identical sample so fact_ids stay stable; `probe_aggregate` drops
   orphaned labels with a warning instead of `KeyError`. Facts file truncated back to the
   paid-for first pass. `tests/test_probe_resume.py` (3 tests) covers all three and the two
   bug-specific ones fail against the pre-fix code. Suite **198 passed**.
3. **Residue from that defect, disclosed in the Instrument verdict:** 5 opus-4-8 labels on the
   discarded intermediate fact set are on the shard and are dropped at aggregation; opus-4-8
   shows 93 labels over 89 facts (4 duplicates across the interruption). Agreement 1.00 — no
   effect on the MAP estimate.
4. **`--resume` for §3d would not have worked as written.** Session resume *is* implemented
   (`model_stub.invoke(resume_session_id=…)`), but the v035b pilot raws never persisted
   `session_id` — `events/raw/reextract_v035b_pilot/*.json` carries `doc_id`, `usage`,
   `cost_usd`, `emission_mode`, `raw_result` and nothing else. The edges-only resumed turn had
   no session to resume; §3d would have fallen back to full re-extraction (≈ 3.9M, inside the
   9M ceiling). Moot — §3b failed — but the harness gap is real and is recorded here.
5. **The verdict script's `cost/doc` is misleading** (whole run ÷ 5). Corrected in the verdict
   and above.

## Exit checklist

- [x] §2 verdict on disk; §3b verdict on disk; §4 correctly skipped
- [x] `daily_tokens` reverted to 55,000,000 and committed
- [x] `seldon cc complete cc_tasks/2026-08-27_pilot_finish.md` → state `completed`
- [x] Lane 4 untouched throughout (driver pid 70576 alive, sleeping to 00:05Z)
- [x] Shards, raws, verdicts, code, tests, RESULT committed and pushed
