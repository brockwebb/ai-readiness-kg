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

## 14. The SPRT was a fixed-n test wearing sequential constants

Found before batch 1 reached judging, by pricing the plan against what the code would actually
do.

`judge_batch` judged one fixed sample (`fact_cap × strata` = 160 facts) and applied the
boundary **once**. Two consequences:

1. **A `continue` at the fixed size was a dangling outcome** — not `accept`, not `reject`, not
   `sampling_inconclusive`, and `BurnState.should_stop` counts none of those. A persistently
   ambiguous burn would never have tripped the corpus stop rule, which is the single operator
   touchpoint in DD-029.
2. **Every batch would have paid the full budget.** 463 facts ≈ 8M tokens per batch, ≈ 105M
   across 13 — about twice the extraction cost — where a sequential test is expected to stop
   at Wald's ASN of **159**. That ASN was already computed and printed in DD-029; the
   implementation simply did not use it.

Now the boundary is evaluated after each increment of **55 facts** — the arithmetic minimum at
which `accept` is reachable at all (DD-026 applied to this plan) — and the batch stops at the
first crossing. `run_protocol` gained a `fact_limit` over a **stable seeded round-robin**, so
each increment is a superset of the last and `probe_judge` resumes rather than re-paying.

Stability is the whole contract, so it is its own tested function: an unstable order would
re-judge facts already paid for *and* apply the boundary to a sample that moved underneath it.
Round-robin across strata, so an early `accept` is a claim about the batch rather than about
whichever document class happened to sort first.

A `continue` that survives the loop — budget spent or sample exhausted — becomes
`sampling_inconclusive`, which is accept-with-flag for the batch **and** counts toward the
corpus stop rule.

Expected judging cost across the burn: **~105M → ~36M tokens.**

## 15. A batch declares its ceiling once

The burn crashed on restart:

```
SpendConfigError: run 'bulk_v038_b001' already declared with ceiling 3,922,028
  /extraction_chunk; refusing conflicting re-declare 4,686,194/extraction_chunk
```

The ledger was right to refuse, and the refusal exposed a design gap rather than a nuisance.
The running mean moves as the burn proceeds — 49,458/chunk before batch 1, **59,094** once
batch 1's own 19 settles entered the last-10 window. Recomputing on resume would ratchet a
batch's bound upward exactly when that batch is running hot, which is when a bound matters.

A per-batch ceiling bounds that batch's **total** spend, so it is declared once and a resume
runs under it. If the remaining work will not fit, the guard refuses and the burn stops
cleanly — the bound doing its job. `SpendLedger.declaration(run_id)` is a read-only accessor;
nothing here passes `supersede`, which the ledger reserves for operator-authorized corrections
and explicitly forbids code paths from using to get past a refusal.

**Two defects in my own tests, both the shape this project keeps producing.** The first
version drove the *ledger* rather than the resume decision, and the mutation that recomputes on
resume survived it — the decision is now its own function the test drives. And I asserted
`int(1.3 × mean × chunks)` where the code uses `ceil`: a bound rounded **down** is a bound the
work can exceed. The code was right; my arithmetic was not.

---

## 16. Batch 1 — TEVV record

**Verdict: ACCEPT.** `bulk_v038_b001` = `fcsm-23-02-a-framework-for-data-quality-case-studies`
+ `nist-ai-risk-management-framework-ai-rmf`, 62 chunks (61 dispatched, 1 banked from Phase A).

### 16.1 The sequential test, as it actually ran

| increment | fabrications | facts | accept line | reject line | decision |
|---|---:|---:|---:|---:|---|
| 1 | 2 | 55 | d ≤ 0.0 | d ≥ 7.9 | continue |
| 2 | **3** | **110** | **d ≤ 4.0** | d ≥ 11.9 | **accept** |

Stopped at **110 facts against a 463 budget** — the ASN saving landing on the first batch.
A fixed-n test at the same budget would have judged 353 more facts for a verdict it already had.

### 16.2 Faithfulness

| | measured | standing threshold |
|---|---:|---|
| pooled F | **0.0273** [0.0093, **0.0771**] | F_upper < 0.10 ✓ |
| item-faithful | **0.830** (78/94) | ≥ 0.70 ✓ |
| facts | 110 | ≥ 55 (plan minimum) ✓ |

Classes: 94 entailed, 6 filled_attribute, 6 span_truncated, **3 fabrication**, 1 subject_dropped.
Rater agreement against the Dawid–Skene consensus: opus-4-8 **0.991**, sonnet-5 **0.909**.
Document-substring check reclassified **2 of 2** examined fabrications as `filled_attribute`.

Batch 1 is *better* than Phase A on both measures (Phase A: F_upper 0.0715, item-faithful
0.770). One batch is not a trend, and the SPRT is deliberately indifferent to that comparison —
it tests this batch against p0/p1, not against Phase A.

### 16.3 Yield vs Phase A envelope — report only, gates nothing

| stratum | batch 1 mean | sd | range | n | Phase A mean | Phase A envelope | flag |
|---|---:|---:|---|---:|---:|---|---|
| agency_framework | **17.60** | 8.62 | 0–41 | 62 | 13.86 | 0–36 | **none** |

Both batch-1 documents are `agency_framework`, so this batch exercises one stratum only —
a consequence of batching in priority order, not of the design. Its mean runs 27% above Phase
A's and its max (41) exceeds Phase A's observed high (36) while the *mean* stays inside the
envelope, which is the quantity the convention compares. Recorded, not acted on.

### 16.4 DD-024 refusals — the guard is load-bearing

**30 semantic edges refused in 61 chunks** (27 `has_component`, 3 `subtype_of`; 15 from each
document).

| | rate | projected over the burn |
|---|---:|---:|
| Phase A (guard absent, edges admitted) | 0.167/chunk | ~190 |
| **Batch 1 (guard active)** | **0.492/chunk** | **~537** |

§5.3's projection of ~190 was **low by 2.8×**. Phase A's stratified 30-chunk draw understated
the rate because framework-heavy documents propose component relations constantly and few of
their chunks were sampled. ADDENDUM-01's choice to enforce at admission rather than
re-qualify a stripped template reads better with this number in hand: refusing at graph entry
costs nothing per edge, and 537 is well past the scale at which "clean it up later" stays
tractable.

### 16.5 Ledger

| run | settled | ceiling |
|---|---:|---:|
| `bulk_v038_b001` | 3,194,546 | 3,922,028 |
| `bulk_v038_b001_judge` | 2,221,824 | 3,000,000 |
| committed today | 10,603,321 | 55,000,000 band |

Extraction came in **19% under** its declared ceiling. Judging cost 2.22M for a verdict at 110
facts; a fixed-n 463-fact test would have been ~4× that.

**Measurement caveat, recorded.** The verdict was reached twice — once in the run that crashed
in the yield flags, once in the recovery. `probe_aggregate` aggregates over every labelled
fact in the run rather than only the increment's selection, so the recovery's *first* increment
already saw all 110 labels and accepted immediately. On a fresh batch the two are identical
(labels exist only for selected facts); on a re-judge the increment control is weaker than
designed. It cost nothing here — the same evidence, the same verdict — and is noted rather
than fixed, because the forward path never re-judges a settled batch.

## 17. Crosswalk-demand coverage by batch

Zero model spend; derived from `state/t2_priority.json` and the batch plan.

| batch | docs | chunks left/full | demand | cum demand | cum % | cum docs | doc % |
|---|---:|---:|---:|---:|---:|---:|---:|
| `b001` | 2 | 0/62 | 4 | 4 | 9.8% | 2 | 5.7% |
| `b002` | 2 | 45/47 | 4 | 8 | 19.5% | 4 | 11.4% |
| `b003` | 3 | 76/78 | 3 | 11 | 26.8% | 7 | 20.0% |
| `b004` | 4 | 50/53 | 4 | 15 | 36.6% | 11 | 31.4% |
| `b005` | 3 | 225/229 | 3 | 18 | 43.9% | 14 | 40.0% |
| `b006` | 1 | 46/47 | 1 | 19 | 46.3% | 15 | 42.9% |
| `b007` | 4 | 39/41 | 4 | 23 | 56.1% | 19 | 54.3% |
| `b008` | 2 | 223/225 | 2 | 25 | 61.0% | 21 | 60.0% |
| `b009` | 1 | 145/146 | 1 | 26 | 63.4% | 22 | 62.9% |
| `b010` | 1 | 64/65 | 1 | 27 | 65.9% | 23 | 65.7% |
| `b011` | 4 | 35/40 | 4 | 31 | 75.6% | 27 | 77.1% |
| `b012` | 5 | 59/64 | 5 | 36 | 87.8% | 32 | 91.4% |
| `b013` | 1 | 23/24 | 1 | 37 | 90.2% | 33 | 94.3% |

Extract set: **35 documents, total crosswalk_demand 41.** Two documents are unconvertible HTML
carrying 4 demand and are never batched, so the plan tops out at **90.2%**.

**The scope signal, for operator decision.** Coverage is close to linear in document count but
badly non-linear in *chunks*: `b005`, `b008` and `b009` are **593 of the 1,030 remaining
chunks — 58% of the work — for 6 of 37 demand (16%)**. Three long specifications
(nist-ai-rmf-playbook, nist-generative-ai-profile, fcsm-19-01) dominate the cost and carry one
demand unit each.

Stopping points, as measured:

| stop after | cum demand | cum chunks | share of remaining work |
|---|---:|---:|---:|
| b004 | 36.6% | 171 | 17% |
| b007 | 56.1% | 481 | 47% |
| b012 | 87.8% | 1,007 | 98% |
| b013 (all) | 90.2% | 1,030 | 100% |

**No gate changes are proposed and none are implied.** This is a scope question — how far down
a priority list to spend — which is operator input, not a threshold the machine may move.

---

# 18. ADDENDUM-02 — burn scope executed

Operator scope decision received 2026-08-31 as ADDENDUM-02: burn every planned batch except
`b005`, `b008`, `b009`; defer their documents with the new reason `below_burn_scope`.

## 18.1 The scope events

Six documents, in two events each. `queue.defer` refuses while a live request stands — by
design, so the worklist and the status surface cannot disagree about the same document — so
each deferral is preceded by the withdrawal that cancels its request. Twelve events on the
untagged queue shard (`events/batch-022.jsonl`):

| document | full chunks | crosswalk_demand | batch |
|---|---:|---:|---|
| cloudflare-ai-crawl-control-manage-crawlers | 7 | 1 | b005 |
| croissant-akhtar-2024-paper | 15 | 1 | b005 |
| fcsm-19-01-transparent-reporting-for-integrated-data-quality | 207 | 1 | b005 |
| mlcommons-croissant-spec | 17 | 1 | b008 |
| nist-ai-rmf-playbook | 208 | 1 | b008 |
| nist-generative-ai-profile-ai-600-1 | 146 | 1 | b009 |

**Reconciliation of the addendum's wording.** §2.2 says "three long specifications, 6 demand
total" while naming "the documents of b005, b008, b009" — six documents, not three. The
document set is what governs and the arithmetic confirms it: 593 deferred chunks leave
**437 to extract**, which is §2.1's own figure. The "three" names the tomes that drive the
cost (fcsm-19-01, nist-ai-rmf-playbook, nist-generative-ai-profile, 561 of the 593 chunks);
the other three ride along in their batches. No discrepancy, recorded for the reader.

**No schema append was owed.** §2.2 conditions one on the reason vocabulary being enumerated.
It is not — `extraction_deferred.reason` is free text in `kg/schema.yaml`, documented by
example ("no consumer"). `below_burn_scope` is admitted without a schema change and is
distinguishable in the status surface, which is what the addendum asks for.

**Phase A chunks stay in the graph.** Each deferred document has 1–2 chunks already extracted
under `bulk_v038` (7 in total) from the Phase A qualification draw. The deferral prices out
the *remaining* chunks; it does not retract work already done and already judged in the
Phase A gate. `kg queue status` shows them as `deferred` with `chunks_extracted` non-zero,
which is the honest reading: considered, partly measured, declined for the rest.

## 18.2 Batch identity, third arrival

The deferral would have renumbered the burn. `defer` requires the withdrawal, the withdrawal
removes the document from `queue.live_requests()`, and identity was cut over exactly that set
— so removing six documents would have closed the holes and slid `b006`→`b005`, `b010`→`b006`,
and so on. ADDENDUM-02 §2.1 names its batches by id, and provenance on 2,504 already-written
events names them too. This is the batch-identity defect a third time, arriving through a
legitimate scope change rather than through progress.

**Fix.** Identity is cut over the documents the ledger has *ever* requested
(`queue.requests_ever()`), unioned with the live set; dispatch is filtered by the deferrals.
A deferral moves a document out of dispatch without moving anyone's id. `requests_ever` is
bounded to actual `extraction_request` events so that a deferral of a never-requested document
cannot *insert* an id either — the mirror failure, which a "take every deferral" rule would
have introduced while fixing the first one.

The principle was already written into `resume_plan`'s docstring before this came up: *the
worklist governs what may RUN; it cannot govern what a batch IS*. A scope decision is a
dispatch fact, not an identity fact.

**Verification (ADDENDUM-02 §3.1).** Five new tests, three of which drive the real
`phase_burn` loop rather than its helpers — the M85/M86 class is at six recorded instances in
this project and a plan-level assertion cannot see what the loop does with the plan. Mutations
run and caught, 7/7:

| mutation | caught by |
|---|---|
| identity ignores deferrals (renumbering restored) | `deferring_documents_does_not_renumber_the_batches_after_them` |
| any deferral joins identity (insertion) | `a_deferral_of_a_never_requested_document_cannot_insert_itself` |
| deferred documents still sized for dispatch | plan + loop tests |
| `dispatch` list unfiltered | loop test |
| loop does not skip a deferred batch | loop test (ceiling declared for `b002`) |
| `requests_ever` degraded to `live_requests` | real-log queue test |
| extraction sent every document, deferred included | loop test (`cp.DOCS`) |

Suite: **557 passed**.

## 18.3 The plan after the cut

```
burn plan: 33 documents, 437 chunks to extract (91 already extracted), 13 batches
  bulk_v038_b001   2 docs     0/62   chunks  (62 already extracted)   -> accept, skipped
  bulk_v038_b002   2 docs    45/47   chunks
  bulk_v038_b003   3 docs    76/78   chunks
  bulk_v038_b004   4 docs    50/53   chunks
  bulk_v038_b005   3 docs   229 chunks  DEFERRED (below_burn_scope)
  bulk_v038_b006   1 docs    46/47   chunks
  bulk_v038_b007   4 docs    39/41   chunks
  bulk_v038_b008   2 docs   225 chunks  DEFERRED (below_burn_scope)
  bulk_v038_b009   1 docs   146 chunks  DEFERRED (below_burn_scope)
  bulk_v038_b010   1 docs    64/65   chunks
  bulk_v038_b011   4 docs    35/40   chunks
  bulk_v038_b012   5 docs    59/64   chunks
  bulk_v038_b013   1 docs    23/24   chunks
```

Ids unchanged from the pre-deferral plan; 437 chunks to extract, matching §2.1 exactly.
`kg queue status`: `queued` 26, `deferred` 162 (156 `no consumer` + 6 `below_burn_scope`),
`extracted` 3, `skipped_oversize` 3; 194 included, reconciling with 194 `manifest_add` events.

## 18.4 The judge ceiling, derived

`--judge-ceiling` defaults to 2,000,000, which batch 1 would have breached at 2,221,824. The
bound a sequential test needs is the cost of the budget it is *allowed* to spend, not the cost
of the sample it happened to need — a tighter bound would refuse a legitimate escalation, i.e.
stop the SPRT from doing its job. Batch 1 measured **10,099 tokens/label** over 220 labels; the
full 463-fact budget at two raters is 926 labels ≈ **9,351,859**; × 1.3, the same factor the
extraction formula uses, gives **12,157,417**. Declared at **12,200,000** per batch judge run.
Per-run ceilings do not consume the daily band; the band remains the control plane's gate and
is unchanged.

## 18.5 Burn ledger

Headroom at resume: **10,603,321 committed of 55,000,000** today. Remaining work is ~42–46M
against 44.4M headroom, so the guard is expected to refuse cleanly mid-plan and the burn
continues the next day — ADDENDUM-01 §3.2's multi-day schedule, not an incident.

# 19. Phase C batch ledger (ADDENDUM-02 §2.1 scope)

Appended as each batch settles. Verdicts are the sequential SPRT's, at p0=0.05 / p1=0.10 /
α=β=0.05; the accept line needs ≥ 55 facts and the budget is 463.

| batch | chunks | SPRT trace | verdict | pooled F [95% CI] | item-faithful | extraction settled / ceiling | judge settled |
|---|---:|---|---|---|---:|---|---:|
| `b001` | 61 | 2/55 continue → 3/110 accept | **accept** | 0.0273 [0.0093, 0.0771] | 0.830 (78/94) | 3,194,546 / 3,922,028 (81%) | 2,221,824 |
| `b002` | 45 | 2/55 continue → 3/110 accept | **accept** | 0.0275 [0.0094, 0.0778] | 0.805 (62/77) | 2,435,958 / 2,942,691 (83%) | 2,153,383 |
| `b003` | 76 | 0/55 accept | **accept** | 0.0000 [0.0000, 0.0653] | 0.800 (40/50) | 3,700,666 / 5,010,178 (74%) | 1,450,634 |

## 19.1 b002 — usafacts-ai-ready-data-guide, w3c-dcat-3

45 chunks; 858 nodes, 1,078 edges, 297 mentions, 159 diverted. 540 facts written (248
deterministic, 292 model-generated), 110 judged.

Trace identical to batch 1 — 2 fabrications at 55 facts (accept line d ≤ 0.0, so continue),
3 at 110 (accept line d ≤ 4.0). Rater agreement 1.000 / 0.936. Doc-check reclassified 2 of 5.
No yield flags; every stratum mean fell inside Phase A's observed envelope.

**Semantic-edge refusals: 18 in 45 chunks = 0.400/chunk**, against batch 1's 0.492 and Phase
A's 0.167. Two batches now put the bulk-profile refusal rate at roughly 2.4–3× the Phase A
estimate, which is enough to call §5.3's ~190-edge projection a stratified-sampling artifact
rather than noise: Phase A drew few chunks from framework-heavy documents, and those are the
documents that propose component relations constantly.

The judge ran to 18% of its derived 12,200,000 ceiling — the bound is loose because it bounds
the *budget* the SPRT may spend, not the sample it needs. Both batches stopped at 110 of 463.

## 19.2 b003 — data-readiness-360-survey, wilkinson-2016-FAIR, aggarwal-2024-GEO

76 chunks; 899 nodes, 1,255 edges, 331 mentions, 158 diverted. 545 facts written (241
deterministic, 304 model), 55 judged.

**The first single-increment accept.** Zero fabrications at 55 facts crosses the accept line
(d ≤ 0.0) outright, so the test stopped at the arithmetic minimum — 55 facts of a 463 budget,
and 1,450,634 judge tokens against the ~9.4M a fixed-n test of the full budget would cost.
Pooled F = 0.0000 [0.0000, 0.0653]; the interval's upper bound alone clears the 0.10 gate.
Rater agreement 1.000 / 0.964, doc-check reclassified 3 of 3, no yield flags.

**Refusals: 13 in 76 chunks = 0.171/chunk**, against b001's 0.492, b002's 0.400 and Phase A's
0.167. This is the stratum, not the burn: b003 is the academic stratum (a survey, the FAIR
principles paper, a GEO paper) while b001 and b002 were frameworks and standards (NIST AI RMF,
FCSM, DCAT). Academic prose does not propose component relations; specifications do it
constantly.

That refines §16's finding rather than overturning it. The claim "Phase A underestimated the
refusal rate" holds — Phase A's stratified draw undersampled framework-heavy documents — but
the corpus-wide projection is a **stratum-weighted mix**, not a flat multiple of any single
batch. The ~537-edge figure in §16 extrapolated b001's framework rate across everything and is
therefore an over-estimate; a weighted figure is deferred until enough batches have landed to
weight it, rather than re-extrapolated from three.

---

# 20. ADDENDUM-03 — close-out and full-burn reconciliation

Gate verified before any burn file was touched, as the addendum requires. No bulk process was
alive; the scoped set had verdicts on disk for every batch; the corpus stop rule had not fired
(`stopped: null`), so the addendum was live rather than void. Final state file written
`2026-09-01T12:56:34Z`.

## 20.1 Substrate wiring (item 1)

`run_bulk_extraction.doc_text` now consults `kg.ingest.gate.substrate_path(doc_id)` before the
suffix dispatch and strips the frontmatter block. The strip is the load-bearing half: chunk
boundaries and grounding anchors are offsets into the text the extractor was handed, so twelve
lines of YAML at the top would shift every offset in the document and silently invalidate
chunk-level resume against everything already ingested.

The addendum's "no behavior change for the 194-doc status quo" was measured, not assumed.
Across all 194 admitted documents: **92 with substrate read byte-identical text**, 100 have no
substrate and fall through unchanged (PDFs are delegated by design), and exactly **2 change** —
`w3c-prov-dm-data-model` and `w3c-prov-o-ontology`, the HTML sources the suffix dispatch used
to reject outright. Nothing already in the graph moved.

Thirteen call sites across three drivers pass `doc_id`. Eight are in `chunked_pilot`, which is
the extractor the burn actually runs; missing those would have left the substrate unread on the
only path that matters while the tests still passed. 4/4 mutations caught.

## 20.2 b014/b015 revival (item 2)

`extraction_request` emitted for both under the pinned profile at their original priorities,
executing ADDENDUM-02 §2.3 now that their `conversion_gap` is closed. Their frozen identifiers
survived the revival unchanged, which is the plan-as-logged-fact fix (§18.2, §3.2 of the extent
RESULT) doing exactly what it exists to do.

## 20.3 Batch ledger, b004 through b015

Continues the §19 table, which stopped at b003. Verdicts are the sequential SPRT's at
p0 = 0.05, p1 = 0.10, α = β = 0.05; accept needs ≥ 55 facts, budget 463.

| batch | SPRT trace | verdict | pooled F [95% CI] | item-faithful | extraction settled / ceiling | judge |
|---|---|---|---|---|---|---|
| `b004` | 0/55 accept | **accept** | 0.0000 [0.0000, 0.0653] | 0.800 (40/50) | 2,637,316 / 3,229,656 (82%) | 1,523,779 |
| `b006` | 2/55 continue → 5/110 continue → 5/165 accept | **accept** | 0.0303 [0.0130, 0.0690] | 0.754 (92/122) | 2,501,254 / 2,928,491 (85%) | 3,441,176 |
| `b007` | 0/55 accept | **accept** | 0.0000 [0.0000, 0.0653] | 0.829 (34/41) | 1,788,768 / 2,694,297 (66%) | 1,749,201 |
| `b010` | — | **sampling_inconclusive** | — | — | 2,353,484 / 4,262,234 (55%) | 0 |
| `b011` | 2/55 continue → 3/110 accept | **accept** | 0.0283 [0.0097, 0.0799] | 0.872 (75/86) | 1,701,338 / 1,813,675 (94%) | 2,259,811 |
| `b012` | 3/55 continue → 4/110 accept | **accept** | 0.0364 [0.0142, 0.0898] | 0.779 (67/86) | 2,912,677 / 3,146,616 (93%) | 2,288,961 |
| `b013` | 0/55 accept | **accept** | 0.0000 [0.0000, 0.0653] | 0.784 (40/51) | 1,300,836 / 1,450,469 (90%) | 1,560,872 |
| `b014` | 1/55 continue → 2/110 accept | **accept** | 0.0183 [0.0050, 0.0644] | 0.798 (75/94) | 1,930,404 / 3,001,034 (64%) | 2,312,435 |
| `b015` | 1/55 continue → 3/110 accept | **accept** | 0.0273 [0.0093, 0.0771] | 0.806 (75/93) | 1,687,191 / 1,981,463 (85%) | 2,432,897 |

Batches `b005`, `b008` and `b009` are absent because they are deferred `below_burn_scope`
(ADDENDUM-02 §2.2). They dispatched nothing, declared nothing and were never judged, which is
correct: an acceptance decision on a batch that never ran would be a lie in the ledger.

### b010, the one non-accept

`b010` (`openai-crawlers-bots`, 65 chunks) is `sampling_inconclusive`, and the distinction
matters diagnostically. The base task pre-registered that outcome for a batch that **runs its
whole 463-fact budget without crossing a boundary**, treated as accept-with-flag and counted
toward the stop rule. b010's cause is different: it produced **33 admitted items against the
55-fact minimum**, so the plan could never settle it at all. Same label, same treatment, same
contribution to the rolling window, but one means the quality is genuinely ambiguous and the
other means the batch was too small to test. Its judge spend is 0 because no judging run was
declared.

Its content stands, per the pre-registered accept-with-flag rule. This is recorded as a gap in
the pre-registration rather than resolved here: retuning a gate after seeing which batch it
caught is precisely the retuning the design forbids. A minimum-n precondition that a batch can
simply fail to reach is the same genus as DD-026, and belongs to a task with its own
measurement.

## 20.4 Full-burn reconciliation

**Acceptance.** 11 batches judged, 10 accept and 1 inconclusive, **0 rejects and 0
quarantines**. The corpus stop rule never approached firing. Pooled across every judged batch:
**23 fabrications in 1,039 facts = 0.0221, Wilson 95% [0.0148, 0.0330]**, against a
pre-registered gate of upper bound below 0.10. Item-faithfulness ran 0.754 to 0.872 against a
0.70 floor, and no batch trends worse than its predecessors.

**Coverage.** 29 of 35 demand-carrying documents fully extracted, **35 of 41 crosswalk demand
units = 85.4 percent**, which is exactly the ~85% ADDENDUM-03 anticipated. The residual 6 units
are the six documents deferred `below_burn_scope`, each holding one or two chunks from the
Phase A draw and otherwise untouched. Nothing is unstarted. `kg queue status`: extracted 29,
deferred 162, skipped_oversize 3, **queued 0**.

**Graph.** 35 documents, 605 chunks, 7,889 nodes, 9,582 edges under `corpus_epoch: bulk-v038`.
Nodes: Concept 3,292, Claim 2,339, Definition 648, Standard 416, Practice 394, Measure 257,
Instrument 193, Platform 155, Framework 136, Tool 59.

**Spend.** Extraction settled **28,144,438 of 36,382,832 declared (77%)**; judging
**23,394,973**; Phase A **4,288,618**; programme total **55,828,029**. Per-batch ceilings bound
without refusing after the LEDGER_WINDOW correction (§19.3), and judging ran at 13–19% of its
derived ceiling throughout because the sequential test kept stopping early. Worth stating
against §5's forecast: that section projected ~55.8M tokens for **extraction alone** at Phase
A's measured rate over the full 13-batch plan. Actual extraction was 28.1M, roughly half,
because ADDENDUM-02 cut three long specifications out of scope. The programme total landing at
55.8M is a coincidence of two different quantities and should not be read as the forecast
verifying.

**DD-024.** 147 semantic edges refused at admission across the burn: `has_component` 109,
`subtype_of` 32, `consumes` 4, `implements` 2, `extends` 0. Zero reached the projection. The
per-chunk refusal rate is stratum-driven, not burn-wide (§19.2): frameworks and standards run
0.40–0.49 per chunk, academic prose 0.17, so §16's ~537-edge corpus projection remains an
over-estimate built from a single framework-heavy batch.

## 20.5 A finding from b014, and a follow-up registered

b014 rejected 18 nodes and 21 edges as `node_not_in_document` / `edge_not_in_document`, a class
absent from every prior batch. Diagnosed rather than assumed: `chunker.Chunk.grounding_text()`
returns `overlap_text + "\n\n" + body`. Each part is a verbatim document substring but their
concatenation is not, so it reproduces the document only when the real split point was a blank
line. A model span straddling that junction is chunk-valid and document-invalid, and
`phase_ingest`'s document-level re-validation rejects it.

Measured on whether each chunk's `grounding_text()` is a document substring: **odcs 25 of 45
and slsa 17 of 32**, against **fcsm-20-04 2 of 47 and w3c-dcat-3 0 of 42**. Both outliers are
the documents assembled by `scripts/extent_remediation.py`, which joins sections with `---`, a
heading and a `Source:` line rather than a bare blank line. The guard is working as designed
and nothing ungrounded entered the graph; the cost is recall, about 5 percent of proposals on
that batch.

Not fixed here. Changing `grounding_text` changes chunk boundaries, which invalidates
chunk-level resume for every batch in the burn. Registered as ResearchTask `1bd304b1` with both
candidate fixes and a preference for repairing the chunker rather than the one producer.

## 20.6 Operator pause

A STOP file was written at operator request during b015 and remains in place. It had no batch
left to block, b015 being the last of 15, so the burn completed normally and exited. Resume by
removing `events/bulk_v038_STOP.json`; chunk-level resume repeats nothing.

**Suite at close: 593 passed.**

---

# Tome burn — b005, b008, b009 (operator scope reversal 2026-09-01)

Appended 2026-09-02 by the CC session that relaunched b009. Everything below is read from
the ledger, the shard, `state/bulk_v038_burn.json` and the driver logs, not relayed.

## 21.1 Scope reversal

ADDENDUM-02 §2.2 deferred six documents `below_burn_scope` on cost-per-demand (58% of
remaining work for 16% of remaining demand). On 2026-09-01 the operator reversed that for
the three tome batches; `extraction_request` events (priority 43–45, reason "operator scope
reversal 2026-09-01 … the cost premise changed") revived the documents under the pinned
`bulk_v038` profile. Batch ids are the ones frozen in `burn_plan_cut`, never renumbered. The
driver was the same `run_chunked_bulk.py --phase burn --workers 2 --judge-ceiling 12200000`
as the scoped burn; nothing in the contract, the SPRT constants, or the DD-024 layers changed.

## 21.2 Batch ledger

| batch | docs | chunks | SPRT trace | verdict | pooled F [95% CI] | item-faithful | extraction settled / ceiling | judge |
|---|---|---|---|---|---|---|---|---|
| `b005` | cloudflare-ai-crawl-control-manage-crawlers, croissant-akhtar-2024-paper, fcsm-19-01-transparent-reporting | 225 of 229 | 4/55 → 7/110 → 9/165 → 11/220 accept | **accept** | 0.0500 [0.0281, 0.0873] | 0.757 (109/144) | 9,911,812 / 14,386,411 (69%) | 3,870,131 |
| `b008` | nist-ai-rmf-playbook, mlcommons-croissant-spec | 223 of 225 | 1/55 → 2/105 accept | **accept** | 0.0190 [0.0052, 0.0668] | 0.812 (56/69) | 9,725,111 / 11,207,590 (87%) | 2,954,438 |
| `b009` | nist-generative-ai-profile-ai-600-1 | 145 of 146 | — | **in flight** (relaunched 2026-09-02 16:10 UTC) | — | — | ceiling 7,951,366 | — |

b005 is the burn's widest SPRT walk: four looks before accept, and its 55-fact F upper bound
(0.1726) sat above the 0.10 gate until the third look. It accepted on the sequential test's own
terms, at F = 0.050, the highest point estimate of any accepted batch. Item-faithfulness 0.757
is above the 0.70 floor but the second-lowest in the burn (b006's 0.754). Read it against
its composition: `fcsm-19-01` alone is 207 of the 229 chunks, so b005 is effectively one
long federal report, and §19.2's stratum finding (frameworks and standards run higher refusal
and lower faithfulness than academic prose) applies.

## 21.3 The b008/b009 stop — a CLI refusal, not an extraction failure

At 2026-09-02 03:01 UTC (23:01 ET on 09-01) every `claude -p` call began exiting 1 with an
empty stderr. The sequence on disk:

1. b008's last three judge batches (one Opus, two Sonnet) failed all three retries each. The
   SPRT had 105 facts labelled out of the 110 planned and accepted on those; the aggregate
   records `facts 105, labels 160`, which is why the second Opus rater shows n=105 and Sonnet
   n=55 in `state/bulk_v038_burn.json`.
2. b009 declared its ceiling, censused 146 chunks, dispatched, and lost its first five chunks
   the same way. The driver's systemic-failure rule fired: `FATAL: 5 consecutive chunk
   failures — systemic, pass stopped`. Zero extraction calls landed.
3. The stub's exit-nonzero path settles at the estimate (`settled_as_estimate: true`, no
   `model_call_event_id`) because a failed CLI may still have consumed tokens server-side.
   Seven b009 reservations were booked that way: 140,000 tokens of capacity charged against
   the batch for no output. That is the conservative rule working as written, and it is a
   measurable cost of the failure, recorded here so the b009 settled/ceiling ratio at close is
   not misread.

`_looks_rate_limited` did not match, so the reservations were settled rather than released
and the driver did not back off. Empty stderr on exit 1 is consistent with the Max
subscription's usage window closing; a Haiku liveness call succeeded at 16:08 UTC with no
change to the machine, and the relaunch's first chunks settled at measured usage
(~36–37k tokens each). No code changed between the failure and the relaunch. Whether the
stub should treat empty-stderr exit 1 as a release-and-back-off case rather than a
settle-and-fail case is a finding for the spend guard, not fixed here.

## 21.4 Relaunch

Chunk-level resume repeated nothing: the driver skipped b001–b008 as `already accept`, found
b009 with 145 of 146 chunks left, and resumed under the ceiling declared at 03:01 (a batch
declares its ceiling once, §15). Log: this session's scratchpad `burn9.log`. b008's artifacts
were committed first (`34b51cc`) so the relaunch's writes are separable in the history.

The first two chunks came back `[empty layers]` at 443 and 1,061 output tokens. Chunks 1–2 of
a NIST profile are front matter, so this is expected there; if it persists past the front
matter it is a yield collapse and the driver's yield flags are the instrument that says so.

## 21.5 Coverage after b005 and b008

`kg queue status`: extracted 34, stale 1 (b009's document, re-extraction owed), deferred 156
(all `no consumer`), skipped_oversize 3. Crosswalk demand: the six `below_burn_scope` units
of §20.4 are now down to one (b009's), so demand coverage stands at **40 of 41 units** pending
b009, against 35 of 41 at the scoped close.

Batch verdict and reconciliation for b009 to follow in this section when it is on disk.

## 21.6 b009 verdict and tome-burn reconciliation

The relaunch ran 2026-09-02 16:10–17:38 UTC. b009 dispatched 145 chunk calls with 0
failures; the two `[empty layers]` chunks were c0001–c0002 (front matter) and nothing after
them. Ingested: 1,178 nodes, 1,300 edges, 595 mentions, 314 diverted, 21 semantic edges
refused at admission (DD-024).

| batch | SPRT trace | verdict | pooled F [95% CI] | item-faithful | extraction settled / ceiling | judge |
|---|---|---|---|---|---|---|
| `b009` | 1/55 continue → 1/110 accept | **accept** | 0.0092 [0.0016, 0.0501] | 0.915 (86/94) | 6,122,134 / 7,951,366 (77%) | 2,308,725 |

b009 is the burn's cleanest batch on both instruments: lowest F point estimate and highest
item-faithfulness of any accepted batch. Its extraction settled figure includes the 140,000
tokens booked as estimates during the 09-01 CLI failure (§21.3); measured usage on the
relaunch was 5,982,134 over 145 chunks, 41,256 per chunk against the plan's 42,182.

After b009 the driver walked b010–b015 as "every chunk already extracted; judging without
dispatch", because `state/bulk_v038_burn.json` had been rewritten by the tome runs and no
longer carried their verdicts. The verdicts it reproduced are identical to §20.3 to the fact,
and the ledger shows **zero settles for any run other than `bulk_v038_b009` and
`bulk_v038_b009_judge` since the relaunch**: the judge replayed its persisted labels. The
state file now carries all fifteen outcomes. Cost of the re-walk: 0 tokens, ~1 minute.

**Tome batches pooled.** 14 fabrications in 435 facts = 0.0322, Wilson 95% [0.0193, 0.0533].
Extraction settled 25,759,057 of 33,545,367 declared (77%); judging 9,133,294. The tomes
ran at the same ceiling-utilisation as the scoped burn and their pooled F sits inside the
scoped burn's interval, so the ADDENDUM-02 deferral was a cost decision, not a quality one,
and the reversal changed nothing about the acceptance record.

**Full burn, fourteen judged batches.** 37 fabrications in 1,474 facts = **0.0251, Wilson 95%
[0.0183, 0.0344]**, against the pre-registered upper-bound gate of 0.10. 13 accept, 1
`sampling_inconclusive` (b010, unsatisfiable minimum-n, §20.3), 0 rejects, 0 quarantines.

**Coverage.** `kg queue status`: extracted 35, deferred 156 (all `no consumer`),
skipped_oversize 3, queued 0, stale 0. Crosswalk demand **41 of 41 units**. Nothing on the
v038 profile is left to burn; the 156 deferred documents carry no crosswalk demand and stay
demand-pull per the standing call.

**Spend, programme total.** Extraction 53,903,495; judging 32,528,267; Phase A 4,288,618;
**90,720,380 tokens**. Daily band today: 22,268,372 of 55,000,000 committed at close.

**Open from this section.** (1) The stub's handling of empty-stderr exit 1 (§21.3): settle-and-
fail cost 140k tokens and a driver stop where release-and-back-off would have cost a wait.
(2) The state-file rewrite that dropped b010–b015's verdicts was harmless here only because
judge labels persist; a driver that could not replay them would have re-spent ~9M on judging.
Both belong to a spend-guard task, not to this one.
