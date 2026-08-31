# RESULT — 2026-08-30_bulk_extraction_v038

**Run date:** 2026-08-31. **Supersedes** the 2026-08-30 gate-check RESULT of the same name,
which stopped at Phase 0 because `cc_tasks/2026-08-27_extraction_queue_RESULT.md` did not
exist. It exists (commit `e1d8c50`, DD-027). The gate is satisfied and this task ran.

**Addenda:** globbed `cc_tasks/2026-08-30_bulk_extraction_v038_ADDENDUM*.md` at start and at
each phase boundary — **none exist**. Nothing modifies the base file.

---

## 0. The premise defect, up front

The task specifies a corpus burn under profile `v0_3_8` and describes Phase C as "batches
dispatch per DD-019 (headless session per document)". **The infrastructure to run a chunked
burn did not exist**, and three of the task's phases are calls into it. Measured at start:

| what the task assumes | live state |
|---|---|
| a production runner for the v0.3.8 contract | `run_bulk_extraction.py` is **whole-document**; it has no chunker call, no anchor-contract parse, no chunk-level shard write |
| `v0_3_8` is a production profile | it is an **experiment arm**: `batch: 18`, `shard_tag: v0_3_8`. `eventlog.replay()` skips tagged shards *by design*, so a burn under it would cost full price and put nothing in the graph |
| the chunked path can address the corpus | `chunked_pilot.py` was hard-bound to `PILOT_DOCS`, 5 documents, at `chunk_sets()` and `phase_extract()` |
| ADDENDUM-06's three strata fit this corpus | the live `doc_type` vocabulary is {academic, industry, federal, standard, intergovernmental, practitioner, platform}. There are **no statutes**, and {industry, practitioner, platform} — 56 of 194 documents — falls outside all three of the addendum's classes |
| epoch-scoped document resolution reaches the burn set | **5 of the 31** burn documents (the `corpus/crosswalk/` lane) belong to no `corpus_epoch_declared` event at all |
| the T1 store can supply every burn document | **2 of 35** are `.html` with no markdown conversion; `doc_text` refuses them and ADDENDUM-06 §1 forbids re-converting inside this run |

Reported, not silently reconciled. What was built to clear them is in §1; what remains open is
in §7.

---

## 1. Phase 0 — preconditions

### 0.1 Queue reconciles

```
pinned profile: bulk_v038   included: 194   manifest_add events: 194   reconciles: YES
```

### 0.2 The pin — `bulk_v038`, not the arm

"Pin v0_3_8" binds the **extraction contract**, and every byte of it is carried over:

| | arm `v0_3_8` | production `bulk_v038` |
|---|---|---|
| `prompt_template` | `kg/extraction/prompt_template_v0_3_8.md` | identical |
| `template_sha256` | `0c6fee1d8d4a4e42f197744c8c92f2f4d8c8dee6cf75470e63648bb21d0b9410` | identical |
| `chunker_config` + sha | `8c5492b3a324…` | identical |
| `emission_contract` | `anchor` | identical |
| shard | `batch-018_v0_3_8` — **tagged** | `batch-023` — **untagged** |
| `corpus_epoch` | `chunked-2026-08-27` | `bulk-v038` |

Two reasons this is a new registration rather than a repurposed arm, both invariants:

1. A tagged shard is invisible to `replay()`. Burning the corpus under the arm profile would
   have run, settled real spend, and left the graph unchanged.
2. Repurposing the arm's shard in place would retroactively redefine what the pilot's banked
   batch-018 events mean; the pilot RESULT cites them as Arm A2.

`default:` moved from `v1` to `bulk_v038`, which is what `kg.queue.pinned_profile()` reads
(queue ADDENDUM-01 §4). Consequence, handled: the whole-document runner would otherwise
inherit a chunk-unit profile on any unflagged fire, so `apply_profile` now **refuses**
`emission_contract: anchor` unless the caller opts in with `chunk_unit_ok=True`. That failure
mode is silent — a chunk-local contract sent a whole document quarantines nearly everything
and reads as a yield collapse, not an error.

### 0.3 The extract/defer cut

`state/t2_priority.json`, label `final (T0 52/58 eligible; 136 out of scope)`,
`provisional: false`, 194 rows. Rule applied verbatim — extract iff `crosswalk_demand >= 1`
OR `t0_centrality > 0`:

| | n |
|---|---|
| **EXTRACT** | **35** (33 by demand only, 2 by both; 0 by centrality alone) |
| **DEFER** (`reason: no consumer`) | **159** |
| of the extract set: unconvertible source | 2 |

The 2026-08-30 preview computed the same 35/159 against the same file, so the cut is stable
across the queue build.

### 0.4 The worklist

35 `extraction_request` events, priority = `t2_priority` rank, `profile: bulk_v038`, and
**`superseding: true`** — 29 of the 35 were already extracted under v1 / kernel-v03 / the
triage epoch, i.e. under a different prompt *and* a different extraction unit. This was found
on the live surface: the first emission omitted the flag and the queue read **queued=6**
against 35 requests, because `stale` outranked a non-superseding request. Corrected forward
(the originals stay on the log; latest-wins is ordinary replay).

Two projection defects the live cut exposed, both fixed with tests:

- **`stale` outranked `deferred`.** 104 of the 159 deferred documents had prior extraction
  history and kept reading `stale` — a claim that re-extraction is *owed*, which the cut had
  just decided it is not. The cut looked four times smaller than it was. Deferral now outranks
  `stale` and never outranks `extracted`.
- **`not_requested` was doing two jobs.** "Nobody has looked" and "we looked and declined" are
  different facts. New event `extraction_deferred` (schema **0.3.6**) and state `deferred`,
  refused while a live request stands, revived by a later request, reason on the record.

Live surface after the cut:

```
queued=35  skipped_oversize=3  deferred=156   total=194
```

(159 deferred rows, 3 of which read `skipped_oversize` — that state outranks a deferral, and
should: an oversize skip is a hard fact about the document. 35 + 159 = 194.)

### 0.5 Ledger

`bulk_v038_phase_a`, ceiling **4,000,000**, `call_class: extraction_chunk`, declared at the
point of dispatch. Daily band headroom at declaration: 54,519,838 of 55,000,000 — Phase A is
7.3% of one day's cap, well inside the control plane's declared limit.

---

## 2. Phase B — the sequential plan, fixed before Phase A data

Parameters are the task's, unchanged: p0 = 0.05, p1 = 0.10, α = β = 0.05.

| constant | value |
|---|---|
| accept boundary | `d ≤ −3.9406 + 0.07236·n` |
| reject boundary | `d ≥ +3.9406 + 0.07236·n` |
| **minimum facts before ACCEPT is reachable** | **55** |
| expected sample number at p0 = 0.05 | 158.6 |
| expected sample number at the indifference rate (p = 0.07236) | **231.3** |
| expected sample number at p1 = 0.10 | 128.3 |
| batch sample budget | 2 × ASN; still `continue` at budget → accept-with-flag |
| corpus stop | 2 consecutive rejects, or 3 rejects/inconclusives in any rolling 5 |

Written to `state/bulk_v038_sprt.json`. The 55-fact minimum is DD-026 applied to this plan:
below it a *perfect* batch cannot cross the accept line, so a smaller sample buys a foregone
`continue`.

**Finding, reported not tuned away:** discriminating 5% from 10% at α = β = 0.05 is a small
effect size, and it costs ~159 judged facts per batch in expectation — more than five times
the entire Phase A confirmation set. That is the price of the discrimination the task
pre-registered. Widening p1 after seeing this number is exactly the retuning a pre-registered
gate exists to forbid, so it stands and the cost is recorded.

One arithmetic defect found and fixed in the derivation: Wald's ASN ratio is singular where
`E[log-LR] = 0`, which is *exactly* the boundary slope — the rate at which the plan is least
decisive. The first cut returned `0.0` there, which would have set the Phase C sample budget
to **zero facts at the worst possible rate**. The limit form is used instead, and a test
drives the peak.

---

## 3. Phase A — the confirmation set

### 3.1 Construction, and a departure from ADDENDUM-06 §1 with its reason

**Departure 1 — four strata, not three.** The addendum collapses `source_type` to
{statute/regulatory}, {agency/framework report}, {academic/preprint}. That vocabulary is
imported from a statute-heavy corpus; this corpus has no statutes, and {industry, practitioner,
platform} falls outside all three classes. Leaving them unstratified would give the largest
non-academic class in the corpus **no Phase C monitoring band** — the one thing ADDENDUM-06 §3
exists to prevent. Four strata, mapped so that *every* live `doc_type` lands in one (there is
a test that fails the moment a new type is admitted without a stratum). **Total n unchanged at
30; the pooled gate unchanged.** Per-stratum n falls from 10 to 7–8, which costs nothing: the
addendum already forbids gating per stratum, so these numbers were always report-only.

**Departure 2 — drawn from the burn set, not corpus-wide.** ADDENDUM-06 §1 says corpus-wide;
this task's own Phase 0.3 declares 159 documents "admitted, **not extracted**". A corpus-wide
draw would extract some of them. Two binding instructions collide, and the later, more
specific one wins. Consequence: the confirmation chunks are real burn output rather than spend
on documents the same task just declined.

**Held out as required:** all 5 documents any arm has touched. **Excluded:** the 2
unconvertible sources — ADDENDUM-06 §1 says the existing store, no re-conversion, and
converting them inside the run would break the pre-registration silently.

Seed `bulk_v038_confirmation:2026-08-31`, drawn by a script committed before dispatch
(`scripts/run_chunked_bulk.py --phase sample`), recorded at
`state/bulk_v038_confirmation.json`.

| stratum | docs | quota | drawn | distinct docs required |
|---|---:|---:|---:|---|
| academic | 7 | 8 | 8 | no (< 10 docs) |
| agency_framework | 7 | 7 | 7 | no |
| industry_practitioner | 6 | 7 | 7 | no |
| normative_standard | 9 | 8 | 8 | no |
| **total** | **29** | **30** | **30** | |

**28 distinct documents across 30 chunks** (max 2 from any one document). ADDENDUM-06 §0's
concern was the pilot's design effect — 44 chunks from 2 documents, effective n nearer the
document count than the chunk count. Effective n here is ~28 documents, not ~2.
