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

### 3.2 A provenance defect caught mid-flight, and what it cost

Phase A's first chunk came back with `prompt_version: 0.3.5` on it. The prompt actually sent
was v0.3.8.

`build_prompt` reads the template from the **profile**; `prompt_version` reads it from
`model_stub._PROMPT_PATH`. Two reads of what is meant to be one fact. They diverged because
the production driver's document override made `members()` return early — and `members()` is
where `rbe.apply_profile` was called, which is also **the only thing that verifies the
template and chunker sha pins**. So the pass ran with the pin unenforced and would have
stamped a false prompt version on every node and edge it produced.

Severity: nothing downstream can detect this afterwards. The output is plausible, the
provenance simply lies, and `profile_for()` — which resolves "what was this extracted under" —
reads `prompt_version` as its disambiguator.

- The run was stopped at 1 chunk. That raw was **discarded**: ~39,190 settled tokens, already
  paid. Keeping a raw whose recorded provenance is false, in a system whose first invariant is
  provenance, is not a saving.
- `apply_arm` now applies the profile where every other arm-scoped global is bound, so the pin
  check and the prompt binding happen in exactly one place.
- `verify_prompt_binding()` refuses to dispatch unless the version being stamped comes from
  the template being sent, and every pass now prints its binding:
  `prompt prompt_template_v0_3_8.md v0.3.8`.

Two **test-isolation** defects surfaced while fixing it, both the same shape as the production
bug — state bound in one place, read in another:

- `_PROMPT_PATH` leaked across tests. The first fix, a snapshot-and-restore fixture, *did not
  work*: it unwound **before** `monkeypatch`'s own undo stack, and monkeypatch then put the
  polluted value back. The restore goes through monkeypatch now, registered first so it is
  undone last.
- The `cp` fixture did not restore the globals the production driver added.

### 3.3 Phase A extraction

| | |
|---|---|
| chunks dispatched | **30** |
| failures | **0** |
| nodes admitted | **351** |
| edges admitted | 452 |
| mention stubs | 137 |
| diverted relations | 81 |
| settled tokens | **1,492,023** against a 4,000,000 ceiling (37%) |
| measured cost | **49,734 settled tokens/chunk** |

Prompt binding printed at dispatch, as it now must be:
`prompt prompt_template_v0_3_8.md v0.3.8`.

**Yield bands — report only, no floor verdict** (ADDENDUM-06 §2; the 45.23 comparator does not
exist off the pilot documents and the 5.16 ground-truth floor is qualification evidence, not a
burn-time bar):

| stratum | chunks | mean nodes/chunk | sd | range |
|---|---:|---:|---:|---|
| academic | 8 | 10.75 | 6.96 | 0–18 |
| agency_framework | 7 | 13.86 | 14.68 | 0–36 |
| industry_practitioner | 7 | 11.86 | 9.39 | 0–24 |
| normative_standard | 8 | 10.63 | 6.72 | 0–19 |

Two findings in that table, both for Phase C's monitoring design rather than for a gate:

1. **Means are close; spreads are not.** `agency_framework`'s sd is 2.1× the next-widest, and
   its ±3 sd band spans −30 to +58 — a band so wide it can flag nothing. Its 0–36 range is
   two document classes wearing one label: dense framework tables and sparse front matter.
   Recorded as the heterogeneity finding ADDENDUM-06 §2 anticipated.
2. **Every stratum has a 0-chunk.** Bibliographies, headers and navigation blocks legitimately
   contain nothing extractable. A yield monitor that treats 0 as an anomaly will fire
   constantly on healthy output.

### 3.4 A scoping defect found by reading the numbers

The first scoped read of this run reported **4,890 Concepts and 1,388 semantic edges** from 30
chunks. Both are impossible; ingest had just said 351 and 452.

`shard_items()` and `chunk_yield()` read `eventlog.replay(tag=TAG)`. For an experiment arm that
isolates the shard, because `TAG` names one. For the production profile `TAG` is `None` **by
design** — that is precisely what makes its events reach the graph — and `replay(tag=None)`
reads *every untagged shard*, which is the entire v1 and kernel-v03 corpus. Now scoped by
`purpose`.

Worth stating plainly: the first thing I did with those numbers was check them against DD-024
and begin writing up a semantic-edge violation that had not happened. The real violation, §5,
was found only after the scoping was fixed — and it is a fifth the size the bad numbers
suggested.


### 3.5 Phase A gate — **PASS**

Pre-registered thresholds, unit and instrument stated per DD-028: **atomic facts of admitted
node items**, measured by the standing probe protocol (decompose 1.1.0, probe_judge 1.1.0, two
raters, Dawid–Skene, randomized order).

| | measured | threshold | |
|---|---:|---|---|
| **F_upper** (Wilson 95% upper) | **0.0715** | < 0.10 | **PASS** |
| **item-faithful** | **0.7705** (94/122) | ≥ 0.70 | **PASS** |
| facts judged, pooled | 160 (159 in the F denominator) | ≥ 35 (DD-026 minimum) | reachable |

**Pooled F = 0.0314 [0.0135, 0.0715].** Fact classes: 128 entailed, 16 span_truncated,
7 filled_attribute, 5 fabrication, 3 subject_dropped, 1 doc_level_attribute.

Per stratum — **reported, never gated**. 40 facts per stratum cannot power a stratum verdict,
and saying so is the requirement (ADDENDUM-06 §2):

| stratum | F | 95% CI | n |
|---|---:|---|---:|
| academic | 0.050 | [0.014, 0.165] | 40 |
| agency_framework | 0.000 | [0.000, 0.088] | 40 |
| industry_practitioner | 0.077 | [0.027, 0.203] | 39 |
| normative_standard | 0.000 | [0.000, 0.088] | 40 |

Every stratum's interval straddles the 0.10 line except the two at zero, which is exactly the
"cannot power a verdict" the addendum predicted. The pooled figure is the gate; these four are
inputs to Phase C's monitoring design and nothing else.

Rater agreement against the Dawid–Skene consensus: opus-4-8 **0.994**, sonnet-5 **0.906**. The
document-substring check reclassified **2 of 4** examined fabrications as `filled_attribute`
(value present in the document, outside the judged window) — the reclassification is in the
numbers above.

**What this PASS does and does not license.** It confirms the v0.3.8 contract off the pilot
documents: 28 documents, four document classes, none of which any arm had seen. It does not
speak to yield, which carries no verdict here by design, and it does not clear the burn — §5.

### 3.6 The gate reported FAIL on a passing run, for ninety seconds

The first verdict extraction read `pooled["F_upper"]` and `pooled["item_faithful"]`. Neither is
a key the aggregator writes (they are `pooled["F_hi"]` and `items["faithful_rate"]`). Both came
back `None`, the threshold comparisons were skipped, and the gate printed **FAIL** on the run
whose real numbers are in the table above.

This is DD-028's defect wearing a safe face — a gate whose instrument it cannot read — and the
failure direction is what makes it dangerous rather than merely wrong. `None` resolved to FAIL,
which *looks* conservative: it discards a passing run and sends the next task to repair
something that was never broken. `gate_inputs` now raises `GateUnreadable` naming the missing
keys, and there is a test that a missing field refuses rather than resolving to a verdict.

Found by reading the printed numbers against the protocol's own stdout, which had just said
`pooled F = 0.0314 [0.0135, 0.0715]` and `items faithful: 94/122 = 0.770` — both passing —
three lines above a FAIL.

### 3.7 One more epoch-resolution failure, at the last step

`probe_aggregate.doc_check_reclassify` resolves documents through `corpus_members()`, which is
epoch-scoped, and raised `KeyError: 'usafacts-ai-ready-data-guide'` — one of the five
crosswalk-lane documents belonging to no declared epoch (§0). It failed **after every label was
paid for**, and would have discarded the whole judged run.

Resolution now falls back to the manifest's `canonical_path`, and an unresolvable document
skips the reclassification check loudly (`doc_check: document_not_resolvable`) rather than
taking the run down with it.

---

## 4. Tests and mutation matrices

| | |
|---|---|
| suite at task start | 453 |
| suite at task end | **510** |
| mutations run | **43** |
| mutations killed | **42** |
| equivalent mutants | **1** (Q3, below) |

Four mutations exposed **defects, not missing tests**, and were fixed rather than tested around:

- **C6.** A malformed `bulk_batch_quarantined` event (no `batch_id`) put `None` in the
  exclusion set, and a bare membership test then excluded every event *predating* acceptance
  sampling — the entire v1 and kernel-v03 corpus. The absence of a `batch_id` is now tested
  where the exclusion happens, not only where the set is built.
- **C13/C15.** `batch_id` reached neither provenance nor `chunk_metrics` under mutation, and
  nothing failed. Without it `batch_items` finds nothing, every batch samples zero facts, the
  SPRT never decides, and the acceptance sampling runs while monitoring nothing. Provenance
  construction is now one function, so the field has one place to be lost.
- **G1.** An unreadable probe aggregate resolved to **FAIL** instead of refusing (§3.6).
- **Q3 — an equivalent mutant, the fourth of its kind here.** It survived because the logic
  it changed cannot change behaviour: `not n_want or n_have >= n_want` is identical to
  `n_have >= n_want`, since `n_have >= 0` always holds. Deleted, with the reasoning left in
  place and the mutation retargeted at the comparison that does run. Three earlier surviving
  mutations in this project (M65, M98, and `worklist`'s oversize skip) were the same finding.

**A defect in the event log itself, found and fixed:** two tests drove `phase_score` without
redirecting the event log and were appending synthetic `ground_truth_floor` events — for
documents `d#c1`/`d#c2`, which do not exist — into `events/batch-021_ground_truth.jsonl` on
every `pytest` run. An autouse conftest guard now refuses any test write to the real log; it
fired on exactly those two tests and nothing else in 453. **Three such events are already
committed and are left in place** — the no-delete invariant governs, and they sit on a tagged
shard `replay()` skips, so they reach no projection. Recorded here rather than repaired.

The guard's own test then leaked a `batch-999.jsonl` into the real log during the mutation
matrix, because a mutated guard lets the write through. It now cleans up unconditionally.

---

## 5. Phase C — NOT STARTED. A profile defect blocks it.

### 5.1 The defect

**The pinned production template emits semantic edges, which DD-024 closes.**

DD-024 (2026-08-27): *"**No bulk semantic-edge extraction under any profile.** Semantic edges
(`has_component`/`subtype_of`/`consumes`/`extends`/`implements` class) enter the graph only by
demand-pull adjudication."* This task's binding facts restate it: *"Semantic edges: none, ever,
under this task (DD-024)."*

`kg/extraction/prompt_template_v0_3_8.md` still carries the v0.3.4 section **"Semantic edges —
the span must state the relation"**, naming all five types, and `has_component` is in its edge
whitelist. The rule was inherited from v0.3.7 → v0.3.5 → v0.3.4 and nobody stripped it when
DD-024 closed the layer three days before the template was cut. All four chunked arms carry it.

Phase A emitted **5 `has_component` edges of 452**:

| document | chunk | span (truncated) |
|---|---|---|
| fcsm-20-04-a-framework-for-data-quality | c0015 | "…the objectivity domain comprise…" |
| fcsm-20-04-a-framework-for-data-quality | c0015 | "…documentation is primarily a contribut…" |
| schema-org-definedterm | c0001 | `\| [DefinedTermSet](https://schema.org/DefinedTermSet…` |
| sdmx-3-0-section-1-framework | c0008 | "The SDMX Information Model provides for a set of metadata…" |
| usafacts-ai-ready-data-guide | c0001 | "…we view an AI system comprised of an LLM and one or more…" |

The third is grounded on a **navigation table row** — which the template's *own* rule forbids
in the sentence right after the one that asks for these edges: *"a table row, or a navigation
grouping never grounds a semantic edge."* One instance in five is exactly the failure mode
DD-024 was decided on (live kernel-era edges 0.61 entailed, 23/35 non-entailed facts outright
fabrication).

Nothing suppresses them downstream. `build_projection` excludes semantic edges only when an
explicit `extraction_superseded` overlay names the `semantic_edges` stratum for that
extraction; there is no blanket rule. **These 5 would project.** At Phase A's rate, the full
1,121-chunk burn produces on the order of **190 forbidden edges** entering the graph.

### 5.2 The decision, and whose rule it is

The task's own **Out of scope**: *"template or profile edits (a profile defect mid-burn = STOP
+ report, new task)."* This is a profile defect, found before the burn rather than during it,
which makes the case for stopping stronger, not weaker. So:

- **Phase C is not started.** No batch dispatched, no batch ceiling declared, no burn events.
- **The template is not edited.** That is the new task's job, and editing a sha-pinned
  production template inside the run it governs would break the pin this task exists to hold.
- The 5 Phase A edges are **left on the log** and reported here. They are real extractions with
  real spans; correcting them is a decision for the task that fixes the template, and the
  no-delete invariant governs either way.

Phase A's gate is unaffected: its unit is atomic facts of admitted **node** items (DD-028), and
no semantic edge is a node item or enters the judged sample.

### 5.3 What Phase C would cost, measured rather than estimated

Recorded so the next task starts from numbers, not projections.

| | |
|---|---|
| burn set | 33 convertible documents, **1,121 chunks**, 13 batches |
| extraction, at Phase A's measured 49,734/chunk | **~55.8M tokens** |
| daily band (`controls.yaml`) | 55,000,000 |
| wall clock at 2 workers × ~5.5 min/chunk | **~51 hours** |
| SPRT sample budget | **463 facts per batch** (2 × ASN at the indifference rate) × 13 batches |

Two consequences worth stating before anyone schedules it:

1. **Phase C exceeds one day's cap on extraction alone** — 55.8M against a 55.0M band, before a single fact is judged. It is a multi-day
   scheduled burn with per-batch declarations, which is what DD-029's design already assumes —
   but it is not a single dispatch, and no single ceiling covers it.
2. **The monitoring is a first-order cost, not an overhead.** ~6,000 judged facts across 13
   batches, at two raters each. That is the price of discriminating a 5% fabrication rate from
   10% at α = β = 0.05, and the parameters were fixed in the task before Phase A ran precisely
   so this number could not be negotiated after seeing it. It stands.

---

## 6. Ledger

| run | call class | ceiling | settled |
|---|---|---:|---:|
| `bulk_v038_phase_a` | `extraction_chunk` | 4,000,000 | 1,492,023 |
| `bulk_v038_phase_a_judge` | `judge` | 4,000,000 (corrected) | 2,796,595 |
| Phase C batch runs | — | **none declared** | **0** |

**One ceiling correction, recorded with its authority.** The judge run was first declared at
2,000,000 — my own estimate, not a task-declared or pre-registered limit; the task declares
only the Phase A extraction ceiling in Phase 0.5. The guard refused dispatch at
1,952,265 + 60,950 vs 2,000,000 with rater 1 complete at 160/160 facts and rater 2 at 60/160.
**The refusal was correct and is the mechanism working**, not an incident. Re-declared at
4,000,000 with `supersede=True` and the authority named on the record: the control plane's
daily band of 55,000,000, with 51,016,360 headroom at the time. Under the cap, not over it —
and the corrected number is on the append-only ledger beside the original, not in place of it.

One paid-for artifact was **discarded** rather than used: the mislabeled Phase A raw (§3.2),
~39,190 settled tokens.

---

## 7. Deliverables

- [x] **Phase 0** — pin sha recorded (§1.2), cut 35/159 (§1.3), worklist 35 requests (§1.4),
      ledger declared (§1.5)
- [x] **Phase A** — pooled gate **PASS** (§3.5), per-stratum reported not gated, yield bands
      recorded (§3.3)
- [x] **Phase B** — SPRT constants and the 55-fact minimum derived (§2); the Phase C
      mutation matrix (C1–C17) ran and was clean **before any Phase C call**, per the
      task's own precondition
- [ ] **Phase C** — **NOT STARTED.** Blocked on the DD-024 profile defect (§5). No batch
      dispatched, no batch ceiling declared, no burn events, nothing to quarantine or
      reconcile.
- [x] **DD-028** — a gate's unit must be measurable by its validating instrument
- [x] **DD-029** — the acceptance-sampling burn design
- [x] tests green, suite count reported, commit, push
- [ ] `seldon cc complete` — see §8

Numbers taken as free at Phase 0: DD-027 was taken by the queue task, so this task took
**DD-028 and DD-029**, as its deliverable list instructed.

## 8. Status of this task

**Phases 0, A and B are complete. Phase C is stopped on a pre-existing profile defect that
this task is explicitly forbidden to fix.**

`seldon cc complete` is **not run**. The task's goal is a monitored burn; the burn did not
happen. Marking it complete would assert work that did not occur — the same reasoning that
kept the 2026-08-30 gate-check RESULT from claiming completion. What was built is durable and
committed: the production profile, the chunked burn driver, the acceptance-sampling machinery,
and a qualified extractor.

**The new task this hands off, in one line:** strip the semantic-edge section from the pinned
chunked template, re-pin the sha, and restart at Phase C — Phases 0/A/B do not need redoing,
and Phase A's 30 chunks are already in the graph.

Open, in the order they will bite:

1. **The DD-024 violation (§5).** Blocks Phase C. Affects all four chunked arm templates, not
   just the production one.
2. **2 unconvertible burn documents** (`odcs-open-data-contract-standard`,
   `slsa-specification-v1-0`). HTML with no markdown conversion; requested, recorded
   `bulk_doc_failed`/`unconvertible_source`, visible on the status surface. Conversion belongs
   to the T0/T1 substrate, not here.
3. **5 documents in no corpus epoch** (the `corpus/crosswalk/` lane). Worked around twice in
   this task — once in the driver, once in `probe_aggregate` after it had already cost a
   judged run. It will keep costing until an epoch is declared for that lane.
4. **`agency_framework`'s ±3 sd band is unusable** (−30 to +58). Phase C's monitoring should
   either split that stratum or use a distribution-free band. A finding for the burn's design,
   not a defect in this run.
5. **3 test-written events remain committed** in `events/batch-021_ground_truth.jsonl` (§4).
   Inert — tagged shard, `replay()` skips it — and left in place under the no-delete invariant.

## 9. Live state at close

```
python -m kg queue status
pinned profile: bulk_v038   included: 194   manifest_add events: 194   reconciles: YES
queued=34  extracted=1  skipped_oversize=3  deferred=156   total=194
```

`extracted=1` is `anthropic-crawler-support-article`, a single-chunk document that Phase A
genuinely completed — the completeness rule of §3.5's sibling fix working in both directions.

| | |
|---|---|
| suite | **510 passed** |
| mutations run / killed / equivalent | **43 / 42 / 1** |
| ledger, this task | 4,288,618 settled (1,492,023 extraction + 2,796,595 judge) |
| daily band | 55,000,000; committed today 4,827,970 |
| model spend on Phase C | **0** |

---

# ADDENDUM-01 execution — 2026-08-31

**Addenda re-globbed at start:** `cc_tasks/2026-08-30_bulk_extraction_v038_ADDENDUM-01.md`,
untracked on disk, committed first (`83fa66d`) so the record shows which instructions the run
was against.

**It rejects §8's handoff line, and its reasoning is the stronger one.** Phase A qualified
template sha `0c6fee1d…` *as sent*; an edited template is a different artifact, so burning it
on Phase A's qualification would be DD-028 one layer up — a qualification instrument that
measured something other than the thing burning. Re-qualifying a stripped template would have
cost ~4.3M tokens to remove an instruction whose *output* can be refused for free.

## 10. §1 — DD-024 enforced at graph entry, in two layers

The template is untouched and the pin holds.

**Layer 1, admission.** `semantic_edge_refused(edge_type)` refuses the five semantic types for
profiles carrying `profile_class: bulk`, and the refusal **emits an event**
(`semantic_edge_refused`, schema **0.3.8**) carrying doc, chunk, type, endpoints, span and the
rule. A rule that drops output silently is indistinguishable from an extractor that never
produced it, and that difference is the whole evidence base DD-024 rests on.

The key is the **profile class**, not the edge type: demand-pull adjudication produces exactly
these five types and is DD-024's own sanctioned path, so a global ban would close its remedy
along with the problem. `profile_class` lives in `run_profiles.yaml` — config, not code.

**Layer 2, projection.** `build_projection.is_projectable` excludes semantic edges from
bulk-class purposes independently, reading which profiles are bulk from the registry at call
time. §5.1 showed one missing rule let 190 edges through; that is the argument against relying
on one.

**§1.3 — the 5 existing Phase A edges.** `extraction_superseded` overlays naming the
`semantic_edges` stratum, on the 4 extractions that emitted them. Events stay on the log.
Verified by scoped read:

```
semantic edges on batch-023 (log):                     5
  dropped by the extraction_superseded overlay:        5
  dropped by the projection exclusion (independently): 5
SEMANTIC EDGES REACHING THE PROJECTION:                0
```

## 11. §2 — the crosswalk lane was never epoch-less

`crosswalk-2026-08-29` was declared by `cc_tasks/2026-08-29_crosswalk_operationalization.md`
and covers **all 5** documents. **No new epoch was declared** — the declaration existed and was
authoritative. What was wrong were the readers:

| | dixie ledger shape | event-shard shape |
|---|---|---|
| location | `corpus/evidence/decisions.jsonl` | `events/batch-017.jsonl` |
| nesting | under `payload` | top level |
| member key | `member_doc_ids` | `members` |

`kg.queue.corpus_epochs` now reads both sources and both shapes, and
`run_bulk_extraction.corpus_members` defers to it so the two cannot disagree about whether a
document is in an epoch. The epoch is also declared **twice** (8 members, then 2), so
declarations **union** rather than last-wins — last-wins would have reported 2 of its 10
documents.

The `canonical_path` fallback stays as defence, per §2, but resolution no longer needs it.

## 12. §3 — burn mechanics

**§3.1 chunk-level resume.** `resume_plan()` derives what is left from `chunk_coverage` — the
`chunk_metrics` events, i.e. the ledger — not from a file and not by counting raws on disk, so
a stray directory cannot fool it. Plan: **1,121 → 1,091 chunks over 32 documents**, 29 chunks
resumed rather than repeated. A document with zero remaining leaves the plan entirely instead
of riding along in a batch's document list and being reported as burned.

**§3.3 yield bands → observed envelope.** `agency_framework`'s ±3 sd band was −30 to +58: it
cannot flag anything, and a negative floor on a count is not a floor. All strata use the same
convention, labelled as decoration at n = 7–8. Flags are computed *after* the verdict; the test
asserts `sprt_decide` cannot even see a yield — its parameters are `(fabrications, facts, b)`.

**§3.4 zero-yield chunks are healthy.** Every Phase A stratum contained one. Zero is not
special-cased into an anomaly; it is compared to the envelope like any other value.

## 13. Two ledger defects caught in Phase C's first ninety seconds

**The batch ceiling was 70% too loose.** Batch 1 declared **6,695,537** = 1.3 × 84,433/chunk ×
61, against Phase A's measured 49,734. The running mean selected settles by a `bulk_v038`
run-id **prefix**, which admits `bulk_v038_phase_a_judge`; judge tokens inflated an extraction
ceiling. A ceiling that loose is a bound that would not catch a runaway, which is the only
thing a ceiling is for. The call class lives on the run's `declare` record, not on the settle,
so the mean now resolves run → class: **49,458/chunk, batch 1 ceiling 3,922,028**.

The test that was meant to cover this is the better finding. Its docstring named the right
principle — *"averaging them into an extraction ceiling would size the burn off the wrong call
class"* — and then chose `pilot_chunked_v035` as the contaminant, a run id that does **not**
start with `bulk_v038`. The prefix filter passed it while the real contaminant sailed through.
**A test can assert exactly the right thing and pick a fixture that cannot fail.** That is the
M85/M86 class arriving through the fixture rather than through the entry point — and the
running total of that class in this project is now eight.

**Burn runs were named for the wrong phase.** `bulk_v038_phase_a_bulk_v038_b001`. Now the batch
id, which is already unique and descriptive.

Cost of both: **zero settled tokens.** Batch 1 was stopped before any call settled, and
chunk-level resume returned its 61 chunks to the plan intact. Two reservations (40,000) remain
outstanding on the abandoned run — dead PID confirmed, but the orphan reaper requires age
> 600 s as well, so they clear on their own. The stale 6,695,537 declaration stays on the
append-only ledger beside the corrected one.
