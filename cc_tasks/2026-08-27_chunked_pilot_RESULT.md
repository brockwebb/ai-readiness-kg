# RESULT — 2026-08-27_chunked_pilot

**Task:** `cc_tasks/2026-08-27_chunked_pilot.md` (Seldon: see §Exit). **Addenda:** none exist —
`cc_tasks/2026-08-27_chunked_pilot_ADDENDUM*.md` matched nothing at dispatch and at close.
**Session:** 2026-08-27 evening ET / 2026-08-28 UTC.

---

## §0 — Band protection: what the STOP file could and could not do

**Premise vs live state (reported, not reconciled).**

| § | premise | true? | live state |
|---|---|---|---|
| §0 | Lane 4 driver pid `70576`/`70596` | **partly** | `70576` is the driver and was alive throughout. `70596` was killed by the driver's own 3898 s subprocess timeout at 2026-08-27T18:52:59Z (recorded in the previous task's RESULT); at dispatch Lane 4's stage-2 child was pid `5123`. |
| §0 | "sleeping to 00:05Z … write the STOP file **now, before 00:05Z**" | **false at dispatch** | The task file was written at 00:36Z and dispatched at ~00:40Z. Lane 4 had already woken at 00:05Z and stage 2 was running when the first action of this task executed. The STOP file was written at **00:45Z**, 40 minutes after the deadline the task assumed. |
| §0 | stage 2 would need most of the band | **false** | Stage 2 was 92 % complete: 5,130 of 5,554 proposals judged, **424 remaining**. It finished on its own at 01:14Z. |

**What was done.** `state/overnight_burn_STOP` was written at 00:45Z with a reason block naming
this task. That is the file `scripts/overnight_burn.py` honors (`STOP_FILE`, line 43;
`halted()`, line 67). **No process was killed.** The task instructed writing the STOP file, not
killing anything, and on the live numbers killing was the worse option: stage 2 had 424
proposals left, and a kill would have bought ~2M tokens at the price of a resume task for 8 %
of the work.

**Stage-2 judgment count at stop (§0 requirement).**

| moment | judged | accepted | rejected |
|---|---|---|---|
| STOP file written, 00:45Z | 5,110 | — | — |
| stage 2 complete, 01:14Z | 5,554 | 4,021 | 1,533 |

670 of those judgments were made after the 00:00Z band roll and before the STOP file existed.

**Defect found in the driver (recorded, not fixed here).** `scripts/overnight_burn.py::lane4`
checks `halted()` at the top of the stage loop (line 703) and before each relocation shard
(line 774) — but **not between the stage loop and step (b), the acceptance sample** (lines
724-726). So the STOP file blocks relocation, which is what §0 names as the band risk, and does
**not** block the 100-item acceptance gate, which the driver entered at 01:14Z on a
now-complete stage-2 class. That gate is bounded and correctly sequenced (it runs on the
complete class), so it was allowed to proceed; the missing guard is the finding.

---

## §1 — The existing chunker: located, assessed, NOT reused as a unit

Searched `/Users/brock/GitHub/wintermute` and `/Users/brock/.wintermute` (`find -iname "*chunk*"`,
`grep -l "def .*chunk|chunk_size|chunk_text"` excluding `.venv`). Three artifacts, none of them a
structure-aware chunker:

| artifact | unit | overlap | tokenizer | headings | verdict |
|---|---|---|---|---|---|
| `neo4j_graphrag…FixedSizeSplitter`, driven by `extraction.chunk_size` / `chunk_overlap` in `~/.wintermute/sources/*.yaml` — the **production** extraction chunker (`p2_spike_extract.py:223`, `p2_g2pp_extract.py:155`) | fixed **characters** (era-2b: 4,000, overlap 0; p2 spike: 4,000) | 0–200 chars | none (characters) | none | **unit not reused** — fixed-character, splits mid-paragraph |
| `~/.wintermute/scripts/stage_book.py` | chapter, with a `chunk_by_tokens` fallback at ~4,000 "tokens" | none | **chars/4**, not a tokenizer | detects chapter/ALLCAPS headings | **pattern reused, code not** — its heading families (numbered, ALLCAPS standalone) are the model for the plain-text detector here; its unit and token proxy are wrong for a 1,500-token cap |
| `~/.wintermute/scripts/p3_chunking_probe.py` + `state/p3_build/chunking_frontier.json` | — | — | — | — | **the internal precedent for this whole pilot** |

**The internal precedent, cited.** Wintermute ran the *same experiment* on 2026-08-13 — chunk
size varied, model/schema/prompt/grounding held constant, 8 chat documents:

- 4,000-char chunks: **65 entities**; whole-doc (60,000): **26**. Era-1 chat entities/doc 27.93
  vs era-2 at 60,000: **3.12**.
- `chunking_frontier.json` records the reading as "the 4,000 arm is the only difference clearly
  outside noise; 30,000 reading ×0.92 is consistent with no effect", and production moved to
  `chunk_size: 4000` (`sources/p3_era2b_config.yaml`).

That is an independent, internal replication of Edge et al. 2024's ~2× entity-reference finding,
on this operator's own stack, eleven days before the whole-document pilot was designed without
citing it. It does not speak to *faithfulness*, which is what this pilot measures.

---

## §2/§3 — What was built

- `kg/extraction/chunker.py` + `kg/extraction/chunker_config.yaml` (all tunables are data),
  15 tests in `tests/test_chunker.py`.
- `kg/extraction/chunked_template.md` — `prompt_template.md` v0.3.5 with the framing swapped and
  **nothing else**; sha-pinned in the new `chunked_v035` profile (`scripts/run_profiles.yaml`),
  which `apply_profile` refuses to run under a drifted prompt.
- `scripts/chunked_pilot.py` — phases `dry_run | extract | ingest | resolve | judge | register`.
- Events to the **tagged** shard `events/batch-016_chunked_v035.jsonl` (tagged shards are never
  replayed into the graph — an experiment arm must not become graph state).

### Discrepancy: the input the task names does not exist

§2 names `corpus/bulk_md/<doc_id>.md` as the chunker's input. **None of the five pilot documents
has a file there** (that directory holds 17 unrelated documents). All five are PDFs read through
`run_bulk_extraction.doc_text` → pypdf, which is also the exact text the whole-document arm was
given. Measured on that text:

| doc | chars | ATX headings | blank-line paragraphs |
|---|---|---|---|
| data-readiness-for-ai-a-360-degree-survey | 162,981 | 0 | 1 |
| aidrin-hiniduma-2024 | 67,587 | 0 | 1 |
| fcsm-23-02-a-framework-for-data-quality-case-studies | 136,370 | 0 | 4 |
| from-accuracy-to-readiness-metrics-and-benchmarks-for-human | 49,728 | 0 | 1 |
| mitre-ai-maturity-model | 102,257 | 0 | 1 |

So §2 rules 1 and 2 as literally written have nothing to bind to. Both were implemented as
written **and** a plain-text family was added for this input: headings by the numbered
(`2 RELATED WORK`, `3.1 …`) and ALLCAPS-standalone patterns from `stage_book.py`, paragraphs by
the short-line reflow rule (a line below 0.85 × the document's 95th-percentile line width closes
a paragraph). Which family fired is recorded on every chunk set (`structure_source`); for all
five documents it was `plain_text`, heading level 1. Chunking the pypdf text rather than
re-deriving markdown with docling was deliberate: a different text extractor would have been a
**second** variable and the task's whole claim is that there is only one.

**Tokenizer (§2.3).** `model_stub` exposes no tokenizer — it reads usage off the `claude -p`
envelope after the call. §2.3's stated fallback therefore applies: **tiktoken `cl100k_base`**,
recorded on every chunk set and in `chunker_config.yaml`.

**Two chunker findings, both config-recorded:**
1. Running page headers/footers were being detected as headings — `"AUGUST  2022"` appears 41
   times in `mitre-ai-maturity-model` and forced 41 spurious section boundaries (91 chunks,
   median 201 tokens). A line repeating more than `max_heading_repeats` (2) times is a running
   header, not a heading: mitre 91 → 52 chunks.
2. A chunk holding only heading lines has no document body to extract from. 23 of 151 chunks
   were of that shape (17 in mitre). They now ride forward into the next chunk (`emit(force=…)`),
   and the end-of-document flush keeps the trailing heading text: 151 → **128 chunks**.

---

## §5 — Probe-protocol changes, applied to BOTH arms

§5 requires the two defects diagnosed in `2026-08-27_pilot_instrument_verdict.md` to be fixed in
both arms' facts before judging. A third was found while implementing them. All three are
versioned; the whole-document arm was **re-judged from scratch** under the new versions, so the
comparison is like-for-like and the banked 08-27 Instrument numbers are not comparable to the
rows below (superseded for comparison, not retracted).

| # | change | version | what it fixes |
|---|---|---|---|
| 1 | coordination is not redistributed | `decompose_version` 1.0.0 → **1.1.0** | 14 of 27 `span_truncated` facts had every content word inside the span; they failed only because the decomposer rewrote `"designed for data profiling, cleansing, and monitoring capabilities"` into `"is designed for data monitoring capabilities"` — a sentence the source never wrote, which no quote from the source can entail. |
| 2 | mid-noun-phrase truncation check | `kg/extraction/span_checks.py` **1.0.0** (7 tests) | The other 13: a span cut before its head noun (`"…consistency of the state-reported commercial"`). POS-based (nltk perceptron tagger): the span's last token is a noun-modifier and the document's next token is its head noun. **Records only** — it never removes a fact from a denominator, because excluding a class from a pre-registered metric is moving the threshold by other means. |
| 3 | a fact about an attribute is judged against *that attribute's* span | `probe_judge_version` 1.0.0 → **1.1.0** (5 tests) | Found here, not in the task. `scripts/probe_judge.py::load_facts` presented `item["grounding_span"]` — the node's own, name-bearing span — for **every** fact, including `method` facts, even though prompt v0.3.4+ requires Instruments to carry per-attribute `grounding_spans`. So the protocol was asking whether the *name* span entailed the *method* content; 26 of the 27 `span_truncated` labels were `method` facts judged that way. `span_for()` now presents the attribute's own span when one exists and falls back to the node span otherwise (and for every edge). This is a defect in the measuring instrument, not a threshold: no threshold moved. |

Neither the pre-registered thresholds (F_upper < 0.10, item-faithful ≥ 0.70, pooled ≥ 20 per
stratum) nor the class definitions were touched.


---

# ⏸ PAUSED — operator stop, 2026-08-28T01:37Z

**Operator instruction (verbatim intent):** "full pause until I say go again. We will run out of
limit before this job finishes."

Nothing is running. Extraction was stopped mid-pass, everything already paid for was ingested at
zero further spend, and the run is resume-safe: `--phase extract` skips any chunk with a
persisted raw, `--phase ingest` skips any chunk already on the shard.

## State at pause

| doc | chunks | extracted | remaining |
|---|---|---|---|
| data-readiness-for-ai-a-360-degree-survey | 30 | **30** | 0 |
| aidrin-hiniduma-2024 | 18 | 14 | 4 |
| fcsm-23-02-a-framework-for-data-quality-case-studies | 27 | 0 | 27 |
| from-accuracy-to-readiness-metrics-and-benchmarks-for-human | 18 | 0 | 18 |
| mitre-ai-maturity-model | 35 | 0 | 35 |
| **total** | **128** | **44** | **84** |

- Spend: run `pilot_chunked_v035` **settled 2,851,499** of a declared 13,000,000 ceiling;
  `committed_today` 11.4M of the 55M band. Reconcile `ok: true`.
- 44 chunk raws persisted under `events/raw/chunked_v035/`; all 44 ingested to the tagged shard
  `events/batch-016_chunked_v035.jsonl` — 746 node events, 1,244 edge events, 379 mention stubs,
  281 diverted relations.
- Judging (`--phase judge`) has **not** run. No judge tokens spent. The whole-document arm has
  not been re-judged under the new protocol versions either.

## What the 44 chunks already show (partial, 2 of 5 docs)

These are observations on an incomplete arm and are **not** a verdict; the pre-registered gate is
not evaluated until both arms are judged.

1. **Chunking costs more here, not less.** 44 calls settled 2,851,499 → **64,807 tokens/chunk** →
   ~8.3M projected for the five documents, against the whole-document arm's measured **3,925,860**
   — about **2.1× more expensive**. The driver is visible in the raws: the prompt asks for an
   exhaustive concept inventory and the model produces one *per chunk* (33–46K output tokens for
   a 1,500-token chunk; median call duration 334 s). This answers the lab note's first open
   question ("does per-doc cost land at or below the single-pass figure?") in the negative,
   independent of what the faithfulness judge later says.
2. **Node yield is much higher.** 746 admitted nodes over 2 documents (432 Concept, **101
   Instrument**, 96 Claim, 65 Definition, 33 Measure) against the whole-document arm's 24
   Instruments over all five. Consistent in direction with Edge et al. 2024 and with Wintermute's
   own 2026-08-13 measurement (§1).
3. **The quarantine rate is high and must be reported with the yield.** 75.5 % of items
   (666 of 882 over the first 10 chunks) were quarantined, nearly all `span_partial` — the
   model's quote does not contain the node's own name verbatim. Some of this is pypdf damage:
   the model quoted `Heterogeneous Euclidean-Overlap Metri (HEOM)` because the extracted text
   is missing the "c". The same gate ran on both arms, so the comparison stays like-for-like.
4. **The semantic stratum is nearly empty at chunk scope.** 20 semantic edges of 1,244
   (19 `subtype_of`, **1 `has_component`**). Relations keep failing endpoint typing because the
   same metric is a Concept in one chunk and an Instrument in another. On this trajectory the
   chunked arm may not reach §5's pooled ≥ 20 precondition for `semantic_edge` across all five
   documents — which would itself be the finding.
5. **ADDENDUM-06's closed `diversion_reason` list is not honored by the model.** It emitted 34
   distinct values over the first 10 chunks, most of them whole sentences. Report-side
   normalization was added (`normalize_reason`, raw string untouched on the shard):
   281 diversions → `other 108, unstated 94, cross_chunk 47, structural_inference 20,
   other:schema_cannot_express 12`. **cross_chunk is 47/281 = 16.7 %** so far.

## To resume (no decisions pending, no state to reconstruct)

```bash
python scripts/chunked_pilot.py --phase extract --ceiling-tokens 13000000 --workers 8
python scripts/chunked_pilot.py --phase resolve
python scripts/chunked_pilot.py --phase judge --fact-cap 120 --judge-ceiling 6000000
python scripts/chunked_pilot.py --phase register
```
`extract` runs `ingest` itself on completion. Remaining estimated spend: ~5.4M extraction
(84 chunks × 64,807) + ~4M judging.

## Ledger note

Three kill/relaunch cycles (a chunk-boundary fix, a truncation-detector fix, and this pause) left
reservations outstanding for in-flight calls. Those calls **had dispatched**, so their tokens were
probably consumed server-side; the reservations are deliberately left committed rather than
released, because releasing them would under-count real spend. `reconcile` reports `ok: true`.


---

# ADDENDUM-02 RESULT — orphaned-reservation release path

**Date:** 2026-08-29 (UTC). Zero model spend: code, tests, and one ledger write.
**Exit criteria:** suite green (233 passed) · 22 releases on the ledger · `outstanding` zeroed
for all four runs · dry-run table below · committed and pushed.

## Prior art (methodology §7.1 / DD-025)

Named, not invented here. This is **lease expiry**: Gray & Cheriton 1989, *Leases: An Efficient
Fault-Tolerant Mechanism for Distributed File Cache Consistency* — the canonical answer to "the
holder died, reclaim the resource" — and the in-doubt-transaction resolution of presumed-abort
two-phase commit (Mohan, Lindsay & Obermarck 1986). The liveness probe itself is the Unix
stale-pidfile idiom (`kill(pid, 0)`). **Internal precedent search** across this repo and the
Wintermute/Seldon decision logs (grep `orphan|stale lock|lease|os.kill|liveness|reap`, 2026-08-29):
no prior reaper — every existing `orphan` in this repo is the graph-structural `orphan_rate` gate,
an unrelated sense of the word.

**Where the literature disagrees with the spec, recorded:** the field prefers a *renewable lease*
to a *post-hoc liveness probe*, because a probe races with PID recycling. The probe was implemented
anyway, for two reasons on the face of it: the reservations already on disk carry no lease field
(a lease cannot reap holds written before it existed), and the race is safe in one direction only —
PID recycling can make a dead owner look *alive*, which under-releases, but cannot make a live owner
look dead on the host that owns the PID. A renewable lease is the right shape if this ever needs to
reap while a run is live; it is not needed to reap holds whose owners are already gone.

## What was built

`python -m kg.spend release-orphans [--run-id R] [--commit]` (`kg/spend.py`).

- **Orphan requires all three** (§1): outstanding (no settle, no release), age > threshold, owner
  PID provably not alive **on this host**. Any one alone spares the hold.
- **The host guard is an addition to the spec, and it is load-bearing.** A PID absent *here* says
  nothing about a process on another machine; without it, a multi-host ledger would release live
  calls. Reservations from another host report `liveness: unknown_other_host` and are never reaped.
  Mutation-proven (M3 below). The live ledger is single-host (1,991/1,991 records `HexagonMBP.local`),
  so this bought nothing today and costs nothing tomorrow.
- **Threshold in config, not code** (standard §2): `controls.yaml` → `spend.orphan_reservation_age_seconds: 600`.
  600 s is 1.8× the chunked pilot's *measured* 334 s median call duration, so a live call is never in
  reap range on age. A missing key is a **loud refusal**, not a default — `release_orphans` raises
  `SpendConfigError` rather than reap against an implicit threshold (M6).
- **Dry run is the default**; `--commit` is the only thing that writes.
- **Ledger stays append-only.** No prior record is touched; releases are new lines carrying the
  reservation id, run, amount returned, `reason: orphan_pid_dead`, and the full liveness evidence
  (owner pid/host, probe host, age, threshold, and the literal probe result).

### Deviation from §2, with reason

The spec names the event `reservation_released`. It is written as **`record: "release"` with
`reason: "orphan_pid_dead"`** — the record kind the ledger already has and that `_tally` already
honours. A second record kind meaning the same thing to the capacity math is a latent trap: any
future code path that checks `kind == "release"` would silently miss it, which is precisely the
two-mechanisms failure that produced the 22M incident (DD-022). The audit distinction the spec asked
for lives in `reason` + `released_by` + `orphan_evidence`, which is strictly more evidence than the
name would have carried.

### Deviation from §4, with reason

§4 states `committed − settled − released = outstanding`. The implemented invariant is
**`committed = settled + outstanding`**, unchanged from DD-022: a released reservation leaves the
tally entirely rather than becoming a negative term. `released` is reported by `status` as an audit
column — how much capacity a reap handed back — not as a term in the capacity arithmetic. The
invariant is asserted per run in the test suite.

## Tests (8 new, `tests/test_spend_guard.py` #10–#17)

Positive-control discipline (methodology §7.5): no monitor is trusted until a seeded known-bad fires
it. **#13 is that control and it runs in-suite**, so it cannot rot — with `_pid_alive` stubbed dead,
the aged live-owner hold that #12 spares is reaped.

**Mutation matrix — every condition killed at least one test:**

| # | Mutation of the shipped code | Tests that failed |
|---|---|---|
| M1 | liveness probe always reports dead | #11 live-fresh, #12 aged-live |
| M2 | `age >` conjunct dropped | #17 dead-pid-inside-window |
| M3 | host guard removed | #14 other-host |
| M4 | `--commit` gate removed (dry run writes) | #10 seeded-orphan |
| M5 | `release` no longer clears a reservation | #10 (double-reap) |
| M6 | missing-config check replaced by a default | #15 loud-config-error |

**M2 initially killed nothing** — the age condition was mandated by §1 but untested, so it could
have been deleted silently. #17 was written to close that gap and now fails under M2 as shown.

**Method note, recorded because it invalidated a first pass.** The first mutation run was executed
against **stale `.pyc` bytecode**: `cp`-ing the clean file back gave a source whose (mtime, size)
pair matched the cached bytecode of the mutated version, so pytest kept running mutated code after
the restore — which is how a passing test appeared to fail after a clean restore. The matrix above
was re-run under `PYTHONDONTWRITEBYTECODE=1` with `__pycache__` cleared. **Any future mutation
testing in this repo must disable bytecode caching**; a mutation harness that silently tests the
wrong bytes is worse than no harness.

Full suite: **233 passed** (was 225; +8).

## First real run

Dry run, 2026-08-29T02:42Z. **22 reservations across 4 runs, 1,326,274 tokens** — every owner PID
dead, every hold ~1 day old, **0 retained** (nothing was running).

| run_id | reservations | tokens | owner PIDs | oldest |
|---|---:|---:|---|---:|
| `pilot_chunked_v035` | 19 | 1,113,669 | 12567, 13470, 15846 (fleet workers) | 92,291 s |
| `pilot_v035b_opus5` | 1 | 111,000 | 96564 | 105,222 s |
| `restoration_v2_s2` | 1 | 65,605 | 46662 | 151,077 s |
| `restoration_v2_s1` | 1 | 36,000 | 25559 | 172,005 s |
| **total** | **22** | **1,326,274** | all `liveness: dead` | |

**Premise discrepancy, reported not reconciled:** §6 expects "the four known orphans released". The
§0 report named four *runs* holding capacity; the underlying holds are **22 reservations**. The
token total is unchanged and matches §0 exactly (1,326,274). The 19 holds on `pilot_chunked_v035`
across three PIDs are the three fleet workers killed mid-flight by the operator stop — one hold per
worker in flight, plus the per-worker backlog, exactly the shape the reaper is for.

Committed with `--commit`. Verification after the write:

- Ledger grew by exactly 22 lines; `head -1991` is byte-identical to the pre-reap file — **no prior
  record mutated**.
- All 22 appended records are `release` / `orphan_pid_dead`, summing to 1,326,274.
- `outstanding` is **0 for all 11 runs**; `committed == settled + outstanding` asserted and holds
  for every run.
- `reconcile` still `ok: true` for all four reaped runs, settled totals unchanged
  (2,851,499 / 5,517,758 / 21,514,241 / 7,458,511) — reaping returns *reserved* capacity and does
  not touch *settled* spend, which is the point.
- `committed_today` reads 0, but **not because of the reap** — the UTC day rolled to 2026-08-29
  between the §0 report and this run. The reap returned reserved capacity dated 08-27/08-28.

Recovered against ceilings: `pilot_chunked_v035` remaining 9,034,832 → **10,148,501**;
`pilot_v035b_opus5` 3,371,242 → **3,482,242**; `restoration_v2_s1` 33,449,759 → **33,485,759**;
`restoration_v2_s2` 47,475,884 → **47,541,489**.

## Not done

`release-orphans` is **not** wired into any runner as an automatic pre-flight. A reaper that runs
itself is a second mechanism operating on the ledger without an operator in the loop, and the
capacity it returns is exactly the capacity a stuck run would otherwise be refused for — which is
information, not noise. It stays a hand-run verb until there is a reason for it not to be.

---

# ADDENDUM-01 §1 RESULT — the banked 44 chunks, judged

**Date:** 2026-08-29 (UTC). **Both Instrument strata PASS the pre-registered gate.** This
**reverses** the whole-document arm's banked FAIL, and the reversal is an instrument change,
not an extraction change — see "What actually moved" below.

## 1. Pre-judge census (§1: count first, report before judging)

| arm | Instrument | semantic_edge | documents covered |
|---|---:|---:|---|
| chunked (44/128 partial) | **92** | **20** | 2 of 5 |
| wholedoc (banked) | **24** | **21** | 5 of 5 |

**Premise discrepancy, reported not reconciled.** §1 states "530 admitted nodes / 841 edges
across 34 ingested chunks". Live state is **746 nodes / 1,244 edges across 44 chunks** — the
addendum was drafted while ingest was still catching up. Nothing was reconciled; the larger
figure is what the shard holds and what was judged from.

## 2. The semantic stratum: not judged, on stronger grounds than §1 anticipated

§1 predicted the semantic stratum would land under 20 and fail the precondition. It landed at
**20 (chunked) and 21 (wholedoc)** — the precondition *passes*. It is still not judgeable, for
a reason §1 did not have in view:

`probe_decompose.deterministic_facts` emits **exactly one fact per edge**, so for this stratum
n_facts = n_items. Under the aggregator's own Wilson 95% interval, `F_upper < 0.10` is
attainable only at **n >= 35**. At n = 20 a **perfect result — zero fabrications — still returns
F_upper = 0.1611**; at n = 21, 0.1546. The gate cannot be cleared at that sample size however
good the extraction is.

**This is a defect in the pre-registration itself, recorded and not repaired here.** The
precondition (pooled >= 20) and the threshold (F_upper < 0.10) are mutually inconsistent at the
boundary: a stratum sampled at exactly the pre-registered minimum can only ever FAIL. The
minimum count consistent with the threshold is 35, not 20. This is arithmetic from the task's
own F_STOP and the aggregator's own interval method — no threshold was moved, and the finding
applies identically to both arms. Prior art for the calculation, named not invented: the
one-sided binomial bound with zero events (Louis 1981; Hanley & Lippman-Hand 1983, "If nothing
goes wrong, is everything all right?" — the rule of three, of which Wilson is the exact form).

Judging it anyway would have bought a foregone FAIL at roughly 470K tokens. ADDENDUM-01 §1
forbids judging a sub-minimum sample; this is that case, reached by the stronger route. Both
rows are recorded **GATE UNREACHABLE** with the counts, per §1's instruction to record rather
than judge.

## 3. Verdict

| arm | stratum | admitted | judged items | facts | F [Wilson 95%] | item-faithful | gate |
|---|---|---:|---:|---:|---|---|---|
| chunked | Instrument | 92 | 30 | 80 | **0.0000 [0.0000, 0.0458]** | **30/30 = 1.000** | **PASS** |
| chunked | semantic_edge | 20 | 0 | — | — | — | GATE UNREACHABLE |
| wholedoc | Instrument | 24 | 24 | 75 | **0.0000 [0.0000, 0.0487]** | **22/24 = 0.917** | **PASS** |
| wholedoc | semantic_edge | 21 | 0 | — | — | — | GATE UNREACHABLE |

Zero fabrications in either arm. Non-entailments: chunked none; wholedoc 2 of 75
(1 `span_truncated`, 1 `subject_dropped`) — neither is a fabrication class.

Rater agreement with the aggregated label: chunked `claude-opus-4-8` 1.000 / `claude-sonnet-5`
1.000; wholedoc 1.000 / 0.947. Same two raters as every prior probe run, unchanged.

Mid-noun-phrase span sidecar (recorded, never subtracted from a denominator): chunked 9/80,
wholedoc 12/75.

## 4. What actually moved — the prior FAIL was an instrument artifact

The whole-document arm's banked verdict was **F_upper 0.158 / item-faithful 0.292 (FAIL)**. The
same arm, same banked extraction, same raters, same thresholds now measures **F_upper 0.0487 /
item-faithful 0.917 (PASS)**. **No extraction was re-run.** The only change is the probe:
decompose 1.0.0 -> 1.1.0 and probe_judge 1.0.0 -> 1.1.0, i.e. the two attribute-quoting fixes
diagnosed in methodology §6.3 (26/34 non-entailments were truncated `method` spans; 14 a
probe-protocol artifact, 13 a mid-noun-phrase quote).

So methodology §6.3's diagnosis is confirmed at the strongest available level: **the Instrument
stratum was never failing on extraction faithfulness. It was failing on how the probe cut the
spans it judged.** A validity instrument that mis-measures its own subject produced a FAIL
verdict that stood for two days and is now withdrawn.

**Consequence for DD-023, recorded as an erratum on that decision, not a reversal of it:**
DD-023 retired whole-document extraction on four measurements. Measurement (3) — "Pilot gate
FAIL both strata under the whole-doc arm (Instrument F_upper 0.158 / faithful 0.292)" — is
**superseded**: that arm now PASSES. Measurements (1) and (2), the cost pathology, are
untouched and are measurements of a different thing. **DD-023's decision therefore stands on
cost, and no longer on faithfulness.** The erratum is filed in `docs/design_decisions.md`; the
decision is not re-opened here, because nothing in §1 bears on the cost argument that carries it.

## 5. Cost — like-for-like, on the documents the chunked arm actually covers

The headline "2.1x" in the pause record projected all five documents from a partial. On the two
documents with any chunked extraction:

| doc | chunked settled | whole-doc settled | ratio | chunked completeness |
|---|---:|---:|---:|---|
| data-readiness-for-ai-a-360-degree-survey | 2,021,101 | 1,330,683 | **1.52x** | 30/30 complete |
| aidrin-hiniduma-2024 | 795,582 | 903,365 | 0.88x | 14/18 partial (~78%) |
| both | 2,816,683 | 2,234,048 | 1.26x | mixed |

**The only honest single-document number is 1.52x** — the one complete chunked pass. The 0.88x
on `aidrin` is an artifact of its arm being 4 chunks short and must not be quoted as a chunking
saving. Direction is unchanged from DD-023 (chunking under the exhaustive-verbatim contract
costs more, not less); the magnitude is **1.52x on complete evidence, not 2.1x**.

## 6. Spend against the §1 ceiling

Declared 2,000,000 (the top of §1's stated ~1-2M). **Settled 2,023,212 — 23,212 over.** This is
the guard's designed at-most-one-in-flight overshoot, not a breach: a reservation is taken at an
estimate and settled at the measured cost, so the final call can land above the estimate that
admitted it; the door then closes (`tests/test_spend_guard.py` #3). Refusals: 0. The run
completed; nothing was truncated by the guard.

**§1's ceiling estimate was low, and why.** §1 sized ~1-2M "from per-class mean". The realized
judge-class mean here is **52,230/call over 16 settles** (median ~40K, one 207,591 outlier)
against the ~40K the estimate implied. Two arms x two raters x 155 facts at batch 10, plus
decompose, is 39 calls. Sized on the realized mean the section was always a ~2.0M job.

Spend was held down by two decisions taken before any label was bought, both reported here
because they bound what the numbers can support:
- **Instrument item cap 30/arm**, seeded (`arm_<arm>:30`) and reproducible. The chunked arm
  judged 30 of its 92 admitted Instruments; the whole-doc arm's 24 were all judged. A smaller
  sample widens the Wilson interval and so makes PASS *harder*, never easier — it is a spend
  bound, not a threshold move.
- **Semantic stratum not judged** (§2 above), saving roughly 470K.

## 7. Two defects found and fixed mid-run (`scripts/probe_decompose.py`)

Both were found live while sizing this section; the first cost one judge call (78,898 tokens)
on a fact set that was missing every free-text proposition.

1. **Resume marked an item done on the presence of ANY fact.** An item whose deterministic
   facts were written but whose free-text fields never reached a model batch was skipped
   forever. The lost fields are `method`/`description` — precisely where this stratum's
   non-entailments live (§6.3) — so the silent loss landed exactly on the measurement. Fixed by
   tracking `have_model` separately from `done`: the model half is owed whenever an item has
   free-text fields and no model-sourced fact yet, independently of its deterministic half.
   Effect on this run: arm_chunked went from **47 facts to 80** after the fix.
2. **`--dry-run` wrote the deterministic facts.** A dry run mutated the resume state of the run
   it was estimating for, which is how (1) was triggered: my own sizing dry-run poisoned it.
   Fixed — a dry run is now a read.

Tests written **before** the fixes, both failing first, both mutation-verified after
(`tests/test_probe_resume.py`, +2). Suite **233 -> 235 passed**.

An existing test (`test_decompose_still_decomposes_an_item_whose_sample_was_rebuilt`) had used
`--dry-run` as a shortcut to avoid a model call and therefore **asserted the write-on-dry-run
behaviour that is now a proven defect**. It is amended, with the reason recorded in its
docstring — a test that pins buggy behaviour is not evidence, and was silently protecting this
defect.

**Method note.** A `{min_facts}` placeholder in `write_verdict` shipped uninterpolated into the
first written verdict (a `str.replace` whose anchor did not match, applied without an assert).
Corrected in source and in the artifact. Every other patch in this task asserts its anchor
before replacing; that one did not, and that is the whole reason it failed silently.

## 8. What §1 does and does not establish

**Establishes:** the Instrument stratum is faithful under BOTH extraction units — zero
fabrications, F_upper 0.046 (chunked) and 0.049 (wholedoc), item-faithful 1.000 and 0.917. The
pre-registered question "does chunk-local extraction move faithfulness?" answers: **on this
evidence it does not move it, because there was nothing to move — both units already pass.**
The instrument, not the unit, was the problem.

**Does not establish**, and must not be read as establishing:
- Anything about the semantic stratum in either arm (gate unreachable at the available n).
- A like-for-like document comparison. The chunked arm covers 2 of 5 documents, and 27 of its
  30 judged Instruments come from a single document (`data-readiness-for-ai-a-360-degree-survey`).
  The whole-doc arm spans all five. **The arms do not run on the same document mix.**
- Any ranking of the two arms on faithfulness. Both pass; the intervals overlap almost
  completely; the item-faithful difference (1.000 vs 0.917) is 2 non-entailed items out of 24
  and is not a detectable difference at these sample sizes.
- Recall. Nothing in this protocol measures it, in either arm.

Per §4 of the addendum, §2 and §3 do not start on this result; this section is a hard stop.

---

# ADDENDUM-03 §1 — v0.3.7 emission contract built (2026-08-29)

**Zero model spend, verified**, not merely intended: the spend ledger's last entries belong to
the overnight `chunked_pilot_judge` run and nothing in §1 dispatched a call. `committed_today`
2,023,212 is entirely that prior judge. Nothing here imports `model_stub`.

**Suite 303 → 337 passed. Mutation matrix 13/13 killed.** Committed and pushed.
**STOPPING HERE per §1's exit and the user's instruction — §2 (dry run and ceilings) and §3
(the two extractor arms) are not started.**

## §0 corrections acknowledged as pre-registered

Both of the addendum's corrections are recorded as binding before any §3 data exists:
**(a)** §3 gates the Instrument stratum only; the semantic count is reported, not judged.
**(b)** ADDENDUM-01 §2.5 is superseded by DD-023 ERRATUM 2 — no re-conversion was performed,
the existing Docling output is used, and no quarantine improvement is attributed to the
converter. Any §3 improvement credits the anchor contract, as pre-registered.

## 1. Anchor contract — `kg/extraction/anchors.py` (new)

Model emits `name`, `type`, `anchor` (≤ 10 tokens, shortest *unique* substring). The harness
locates it and **cuts the grounding span from the source text** as the containing sentence.

**The locate-at-birth guarantee is not merely preserved, it is strengthened**: the span in the
graph is document-derived, so it cannot drift from the source by construction. A model-supplied
`grounding_span` is deliberately **discarded** — honouring one would reopen the `span_partial`
drift the contract exists to close, and there is a test asserting exactly that.

`grounding.py`'s normalization is **reused, not forked**, as §1.1 requires. But locating needs
*offsets* and `normalize()` returns a string, so the module rebuilds the same transformation
while tracking each output character to its source index — and then **verifies the rebuild
against `grounding.normalize` itself**. On mismatch it reports `anchor_not_located` rather than
cut a span from coordinates it cannot vouch for. **Failing closed is the design point: a wrong
span is worse than a missing one, because a wrong one still looks grounded.**

Quarantine reason is `anchor_not_located` for every failure (missing / not found / ambiguous /
over-length / unverifiable offsets), with the detail after the colon as diagnosis — the
addendum names one reason and this keeps it one class.

**A real defect the module's own smoke test caught before it shipped:** the newline inside a
hyphenated line break (`read-\nability`) was being read as a sentence boundary, so the derived
span was cut mid-word — `"ability of the file is high."`, a string that genuinely occurs in the
source and is still wrong. De-hyphenation joins that word, so that newline is not a boundary.
Fixed, and pinned by M26.

## 2. Salience — `kg/extraction/prompt_template_v0_3_7.md` (new)

Derived from `chunked_template.md` **by substitution**, the same discipline that file used on
v0.3.5: the schema, the Instrument positive criterion, the semantic-edge relation rule,
`evidence_grade`, `Measure.tier` and the edge whitelist are carried over unchanged. Only the
emission contract moved. Dropped: `concept_inventory`, "the exhaustive Concept layer", "Be
thorough". Added: the anchor contract up front, one `gleaned` pass (names only), and the closed
`diversion_reason` list restated so the prompt and the parser name one vocabulary.

Instrument attributes use the same mechanism per attribute (`attribute_anchors`), so no anchor
⇒ that attribute is null — the v0.3.4 no-background-knowledge rule survives intact.

## 3. Closed list enforced at parse — `kg/extraction/parser.py`

`normalize_diversion_reason` promoted out of `scripts/chunked_pilot.py` into the parser.
Behaviour is unchanged; the enforcement point is not. **A model cannot be bound by an
instruction; it can be bound by a parser** — measured basis: over the first 10 chunks the model
emitted 34 distinct values for this field, mostly whole sentences.

The **raw value is preserved** on the shard as `diversion_reason_raw`: normalization governs
the vocabulary, not a licence to discard what the model said. `chunked_pilot.py` now
re-exports the parser's function rather than keeping a second copy — two copies of a
vocabulary is precisely how the "resolved" definition drifted across three call sites in
today's T0 work, and one test asserts the identity.

## 4. Type reconciliation at merge — `kg/extraction/merge.py` (new)

Rule, mechanical and logged per entity: **instrument evidence wins → majority → `type_conflict`**.

The first rule is asymmetric on purpose, and the reason is worth stating because it is not
symmetric voting: typing something an Instrument *with grounded evidence* is a **positive
observation**, while `Concept` is the default a chunk falls back to when it says nothing more.
Presence of evidence outranks absence of it, so a majority of uninformative views must not
outvote one informative view. An Instrument claim **without** evidence gets no privilege and
falls through to the count (M28).

A tie is **flagged, never broken by ordering** — a coin flip would put an arbitrary type into
the graph and leave no trace it was arbitrary. Conflicted entities are excluded from strata
pooling (`poolable`), because pooling an entity whose type is unresolved puts the conflict into
a gate's denominator. Tested with the observation order reversed, so the outcome cannot depend
on it.

## 5. Profile `v0_3_7` — registered and sha-pinned

`scripts/run_profiles.yaml`. Pins **both** the prompt template and the chunker config: a
chunk-local contract read against a differently-cut chunk is a different experiment, and the
prompt pin alone cannot see that. The extractor model is deliberately **not** pinned — §3 runs
two arms and DD-023 makes the gate indifferent to which model produced the candidates.

**The comparison profiles are retained** (`v1`, `reextract_v035`, `chunked_v035`), per §1.5,
with a test asserting they are still there: deleting the arm you measured against destroys the
measurement.

**A gap found while wiring this:** `apply_profile` enforced the *prompt* pin but would have
accepted `chunker_config_sha256` as decoration. A pin that is declared and never checked reads
like a guarantee and is not one. Generalized into `_verify_pin` and applied to both.

## 6. Mutation matrix — 13/13 killed

| mutation | result |
|---|---|
| M22 model-typed span honoured instead of derived | KILLED |
| M23 ambiguity check removed (first hit wins) | KILLED |
| M24 anchor length bound removed | KILLED |
| M25 fail-closed on unverified offsets removed | KILLED |
| M26 hyphen-linebreak boundary exemption removed | KILLED |
| M27 instrument evidence no longer privileged | KILLED |
| M28 evidence flag ignored (any Instrument claim wins) | KILLED |
| M29 tie broken by ordering instead of flagged | KILLED |
| M30 conflicted entity allowed into pooling | KILLED |
| M31 diversion normalization removed at parse | KILLED |
| M32 raw diversion value discarded | KILLED |
| M33 pin check made permissive | KILLED |
| M34 exhaustive-inventory instruction restored | KILLED |

§1.6 names the M2 failure mode as the specific thing to avoid, so five of these target the
*test* rather than the code: M28 and M29 exist because "instrument evidence wins" and "a tie is
flagged" are each two claims that a single happy-path test would conflate, and M34 rewrites the
banned instruction back into the prompt to prove the salience test reads the rule and not a
word. Three tests were themselves corrected during authoring after they failed for the wrong
reason: one asserted an anchor was ambiguous when the fixture made it unique, one broke on
where the prompt happened to hard-wrap, and one banned the bare phrase "exhaustive list" —
which the new template's own sentence saying an exhaustive list is *not* wanted would have
tripped. That third one is the M2 pattern in miniature: a word, not a rule.

## Discrepancies

**None between the addendum and live state.** `run_profiles.yaml`, `parser.py`,
`grounding.py`, `chunked_template.md` and `chunker_config.yaml` were all as described.

## Not done (the hard stop)

§2 dry run and ceiling declaration; §3 Arm A / Arm B. No `--ceiling-tokens` declared, no
`release-orphans` run — those belong to §2, which begins only on the next instruction.

---

# ADDENDUM-03 §2 — dry run and declared ceilings (2026-08-29)

**Zero model spend.** Chunking, tokenizing and ledger declaration only. **STOPPING HERE per
§2's exit — §3 (the two arms) is not started.**

## Pre-checks the operator asked for, before the dry run

### (a) Boundary rule vs Docling structures — it was NOT tested, and the claim was FALSE

`_SENT_END`'s docstring asserted "a table row or list item is a unit". Nothing tested it, and
it was wrong. Measured against real converted documents:

| case | derived span | |
|---|---|---|
| table row | `\| No Optimization \| 19 .` | Docling writes decimals **spaced** (`19 . 5`) |
| `et al.` | `2024 showed, AIDRIN scores six dimensions.` | subject dropped |
| `e.g.` / `U.S.` | `metadata and lineage.` | starts mid-sentence |

**Every one of these is still verbatim-present in the source**, so it passes `is_grounded` and
looks correct in the graph. That is the dangerous shape of this bug — and it would have run
straight into §3, where these spans become the judged material.

Prevalence, measured over **306 unique anchors across 40 real documents: 14.7%** of derived
spans change once the rules below are added.

**Prior art, evaluated rather than assumed.** Sentence boundary disambiguation is long solved
(Grefenstette & Tapanainen 1994; Kiss & Strunk 2006 for Punkt; pysbd's Golden Rules).
`nltk` and `spacy` are both importable in this environment. Neither adopted, in order of
weight: (1) the dominant failure is **markdown line structure**, which no prose segmenter
models — Punkt splits a table row exactly as the naive rule did, because a table row is not a
sentence; (2) this needs boundaries **around one known offset**, not document segmentation;
(3) `grounding.py`, whose normalization must not be forked, is stdlib-only and the repo
declares one runtime dependency. **The field's decomposition is adopted; its packaging is
rejected** (~/GitHub/CLAUDE.md §7, §8).

Rules added: structural lines (table row / heading / list item) are units; periods after
abbreviations, initials, and inside numbers are not boundaries. Span length after the fix:
median 142 chars, p90 295, max 3,692 — the long tail is prose, not tables (structural spans
max at 999), so the rule does not over-extend.

### (b) The normalize consistency check is RUNTIME, not test-only

`_verify` is called in `locate_all` (`anchors.py:119`), on the production path
`apply_anchor_contract → derive_span → locate_all`, **for every anchor of every item**. The
test only monkeypatches it to prove the fail-closed branch fires. Confirmed by reading the
call chain, not by inference.

### Mutation matrix 9/9 — but six SURVIVED first

M35–M38 initially survived: the heading and list fixtures had **no interior sentence
punctuation**, so the trailing newline bounded them and the structural rule was never
exercised. M42 survived because the structural rule and the decimal exemption were **masking
each other** on the same fixture. Rebuilt from real corpus lines that carry interior
boundaries — `## SEC. 3. AI CENTER OF EXCELLENCE. 20`, and a table cell containing
`Query: Should robots replace humans? Source: …` (an interior `?`, which no numeric rule
exempts) — plus separate tests isolating each mechanism. `_MULTIWORD_ABBREV` was **deleted as
dead code** after a mutation removing it killed nothing: `et al.` is already caught by the
single-token check on `al`.

**This is the fourth time in four tasks a guard test measured the guard's neighbour.**

## §2 — the dry run

**Discrepancy reported, not reconciled.** §2 specifies
`scripts/run_bulk_extraction.py --dry-run --profile v0_3_7`. That runner **has no chunker** —
its dry run prints whole documents ("would extract: <doc>") and cannot produce the per-document
chunk counts §2 asks for. It also calls `spend.declare()` **before** the dry-run branch, so a
placeholder ceiling would write a fabricated declaration into an append-only ledger. Used
`scripts/chunked_pilot.py --phase dry_run --profile v0_3_7` instead — the repo's own tool for
exactly this step, whose docstring reads "chunk the five documents, count chunks and prompt
tokens, print the ceiling". `build_prompt` is now profile-driven (resolving to
`chunked_template.md` for `chunked_v035`, byte-identical, so the banked arm is untouched).

Orphan reaper first, as §2 requires: **0 orphans, 0 tokens** — nothing to release, so no
`--commit`.

| document | chunks | src tok | chunk tok | input tok | oversize |
|---|---|---|---|---|---|
| data-readiness-for-ai-a-360-degree-survey | 30 | 35,931 | 35,920 | 144,720 | 0 |
| aidrin-hiniduma-2024 | 18 | 15,530 | 15,524 | 80,574 | 0 |
| fcsm-23-02-a-framework-for-data-quality-case-studies | 27 | 27,663 | 27,661 | 125,998 | 0 |
| from-accuracy-to-readiness-metrics-and-benchmarks-for-human | 18 | 13,143 | 13,140 | 78,342 | 0 |
| mitre-ai-maturity-model | 35 | 23,597 | 23,581 | 150,103 | 0 |
| **total** | **128** | | | **579,737** | **0** |

Prompt overhead 3,597 tok/call; input 4,529/call.

### Output projection — and why it is not the addendum's ~1–2K

§2 expects ~1–2K output per chunk. **This projects 5,092/chunk**, and the difference is a real
disagreement worth stating rather than smoothing over.

The whole-doc output/input ratio (0.55) prices the **retired** exhaustive-verbatim contract and
would be pricing the very thing v0.3.7 replaces, so it is not used here. Instead:

- **measured item density**: median **134 items/chunk** over the 32 parsable banked chunks
- **computed per-item cost under the anchor contract**: **38 tokens** (real tokenizer, on a
  representative node and edge) — against **225 tok/item measured** under v0.3.5, a **5.9×
  per-item reduction**, which is the anchor contract's whole cost argument, confirmed
- 134 × 38 = **5,092/chunk × 128 = 651,776**

The gap to ~1–2K is the **salience** effect: the addendum's figure presumes dropping the
exhaustive-inventory instruction also cuts the item *count*. It probably does — but **by how
much is unmeasured until §3 runs**, so the projection deliberately assumes **no salience
reduction**. A ceiling built on the optimistic assumption refuses a legitimate run. If §3
measures a lower density, the anchor contract will have beaten this projection.

### Ceiling arithmetic and declaration

```
input          579,737
cache_creation 579,737   (non-resumed calls re-send the prefix)
output         651,776
estimate     1,811,250
floor x calls  20,000 x 128 = 2,560,000   (the guard's first-calls reserve)
CEILING = max(estimate, floor x calls) x 1.5 = 3,840,000 per arm
```

The reserve-time floor dominates the estimate, so it sets the ceiling; the running mean
replaces it after the first settles.

**Declared on `state/spend_ledger.jsonl`:**

| run_id | ceiling | committed | call_class |
|---|---|---|---|
| `pilot_v037_arm_a_haiku` | 3,840,000 | 0 | extraction |
| `pilot_v037_arm_b_sonnet` | 3,840,000 | 0 | extraction |

Both arms declared now because the projection is identical (same 128 chunks, same contract;
only the model differs). Arm B runs **only if Arm A falls short** — an unused declaration with
0 committed is inert. **If Arm A's measured mean exceeds this projection, Arm B's ceiling must
be re-derived from A's actuals rather than reused.**

Daily band 55,000,000; committed today 2,023,212. Worst case both arms = 9,703,212, **well
under the cap** — no operator approval required (doctrine: under the cap, run it).

## Tests: 337 → 359 passed

## Not done (the hard stop)

§3 Arm A / Arm B. No extraction dispatched, no `model_stub` call, nothing reserved against
either ceiling. `seldon cc complete` deliberately not run — ADDENDUM-03 reserves it for the
end of §3.

---

# §3 PRE-REGISTRATION (operator, 2026-08-29) — written and committed before Arm A ran

Two additions to the pre-registered §3 gate, requested by the operator before any Arm A chunk
was dispatched. They close the same loophole from opposite sides. The v0.3.7 contract
deliberately drops the exhaustive-inventory instruction; an extractor that responds by
emitting almost nothing would post an excellent faithfulness score on a handful of easy items.
**Faithfulness alone cannot distinguish "accurate" from "silent."**

## (a) Faithfulness is reported conditioned on item density

Every faithfulness figure is published beside the **admitted items per chunk** that produced
it, and a PASS is stated as the triple **(F_upper, item-faithful, density)** — never as a
faithfulness number alone. A faithfulness figure quoted without its density is not comparable
across arms and is not to be reported that way.

## (b) Admitted-yield floor: 60% of v0.3.5

An arm admitting **fewer than 0.60x the v0.3.5 arm's admitted items per chunk** reports
**UNDER-EXTRACTION** rather than PASS — even if it clears `F_upper < 0.10` and
`item-faithful >= 0.70`. Both thresholds still apply; the floor can only *withhold* a PASS,
never grant one. Encoded as `YIELD_FLOOR_RATIO = 0.60` in `scripts/chunked_pilot.py`, read by
`yield_comparison()`, and it is not re-read from any result.

### Discrepancy reported, not reconciled: there is no "same 128 chunks" for v0.3.5

The operator's instruction says "60% of v0.3.5 **on the same 128 chunks**." **That comparator
does not exist.** The banked v0.3.5 chunked arm covers **44 of the 128 chunks**, across **2 of
the 5 documents** (`data-readiness-for-ai-a-360-degree-survey` 30/30, `aidrin-hiniduma-2024`
14/18); the run was stopped by operator decision once the cost question was settled at 65,637
settled tokens per chunk. The other three documents have no v0.3.5 chunked extraction at all.

The intent is unambiguous, so it is implemented against a comparator that exists:

> **admitted items per chunk, computed on the chunks BOTH arms actually cover.**

Dividing Arm A's items over 128 chunks by v0.3.5's items over 44 would compare two different
denominators and manufacture a verdict from the mismatch. A test (`test_yield_is_compared_
only_on_chunks_BOTH_arms_cover`) fails if the intersection is ever widened to a union.

### The baseline, measured now so it cannot move later

From `events/batch-016_chunked_v035.jsonl`, live `chunk_metrics` only (the one
`chunk_superseded` triple excluded):

| quantity | value |
|---|---|
| chunks with events | 44 |
| admitted nodes | 746 |
| admitted edges | 1,244 |
| **admitted items** | **1,990** |
| **admitted per chunk** | **45.23** |
| quarantined (same chunks) | 2,388 of 4,378 emitted (54.5%) |

**Pre-registered floor: `0.60 x 45.23 = 27.14` admitted items per chunk**, on whichever of
those 44 chunks Arm A also covers. Below it, Arm A reports UNDER-EXTRACTION regardless of its
gate numbers.

Note what the baseline row also says: the v0.3.5 arm **quarantined more items than it
admitted**. That is the number the anchor contract is meant to move, and it is recorded here
before Arm A produces a competing one.

## Ledger erratum (self-executing, grounding on its face)

The §2 declarations for `pilot_v037_arm_a_haiku` and `pilot_v037_arm_b_sonnet` recorded
`call_class: extraction` (reserve floor 111,000) while the ceiling arithmetic reported in §2
used the `extraction_chunk` floor (20,000 x 128 = 2,560,000). `extraction_chunk` is the class
`controls.yaml` defines for exactly this shape of call ("One call carries ONE chunk, not a
whole document"), so the declaration was wrong and the arithmetic was right.

Corrected by a superseding declare on the append-only ledger, **ceiling unchanged at
3,840,000**, both runs at 0 committed so nothing already billed is disturbed. The grounding is
on the record's face in `declared_by`.

## Issue filed

`1f298b4c-9134-4cd5-9b28-9e071fd062a5` (structural_flow, DO SOON) —
`scripts/run_bulk_extraction.py --dry-run` calls `spend.declare()` **before** branching on the
dry-run flag, so pricing a run requires committing to a fabricated ceiling on an append-only
ledger. This is the §2 discrepancy promoted from a paragraph in a RESULT to a tracked artifact.

---

# §3 ARM A — `claude-haiku-4-5` under the v0.3.7 anchor contract

**Verdict: UNDER-EXTRACTION.** Arm A is **perfectly faithful and severely silent.**

| pre-registered quantity | threshold | measured | |
|---|---|---|---|
| F (Wilson 95% upper) | `< 0.10` | **0.0000 [0.0000, 0.0385]** over 96 facts | PASS |
| item-faithful | `>= 0.70` | **60/60 = 1.000** | PASS |
| admitted items / chunk | `>= 0.60 x v0.3.5` = 27.14 | **15.70** (ratio **0.347**) | **FAIL** |

**This is exactly the case the operator's pre-registration was written to catch.** Without the
yield floor, `F_upper 0.0385` and `item-faithful 1.000` would have been reported as a clean
PASS — and it would have been a true statement about a system extracting a third of what it
should. Reported as the pre-registered triple: **(0.0385, 1.000, 15.70 admitted/chunk)**.

Raters: `claude-opus-4-8` agreement 1.000, `claude-sonnet-5` 0.969, Dawid-Skene over 192
labels. 96 of 96 facts entailed, 0 fabrications. Span checks: 8 of 96 facts sit on a
mid-noun-phrase span (recorded, never subtracted — §5).

## Coverage, and why it is 44 chunks and not 128

Arm A covers **48 chunks — both documents the v0.3.5 arm banked, in full** (data-readiness
30/30, aidrin 18/18), of which **44 have a v0.3.5 comparator**. The other three pilot
documents were not extracted, for two reasons, both measured rather than assumed:

1. **The ceiling would not have held.** Settled cost came in at **41,530 tokens/chunk**
   against the §2 projection of 14,150. 128 chunks needs ~5.3M against the **3,840,000**
   declared in §2 — the run would have been refused at ~92 chunks. **The §2 projection's
   error is identifiable: it omitted `cacheReadInputTokens` entirely** (13.6K/call measured)
   and put output at 5,092/chunk against a measured **10,179**.
2. **The 84 chunks outside the comparator answer nothing the gate asks.** The pre-registered
   comparison is against v0.3.5, which exists only on these two documents.

Running exactly the v0.3.5 chunk set turns the banked verdict's own stated defect — "the two
arms therefore do not run on the same document mix" — into the first like-for-like comparison
in this pilot. **Settled: 1,993,432 of the 3,840,000 ceiling. No refusals.**

## Yield: what salience cut, and what quarantine cut

| over the 44 shared chunks | Arm A | v0.3.5 | ratio |
|---|---|---|---|
| **admitted / chunk** | **15.70** | **45.23** | **0.347** |
| emitted / chunk | 42.0 | 99.5 | 0.422 |
| quarantine rate | 62.6% | 54.5% | — |
| admitted nodes | 389 | 746 | 0.521 |
| admitted edges | 302 | 1,244 | **0.243** |

Per-chunk ratio: median **0.351**; **10 of 43** comparable chunks clear the 0.60 floor.

The decomposition matters more than the headline. **Salience did what it was asked to do** —
emission fell to 42%, and recall is not gate-measured, so that alone is not a defect. The
shortfall past that is quarantine: the rate rose from 54.5% to 62.6%, and it lands hardest on
**edges (0.243)**, because a quarantined node kills every edge that ends on it —
`unresolved_endpoint` is 19.7% of Arm A's emitted items.

### Quarantine by reason, with the two causes the erratum split kept apart

| reason | Arm A | % of emitted | v0.3.5 | % of emitted |
|---|---|---|---|---|
| `span_partial` | 549 | 26.8% | 846 | 18.7% |
| `unresolved_endpoint` | 404 | 19.7% | 1,524 | 33.6% |
| **`anchor_not_located`** | **347** | **16.9%** | n/a (no anchors) | — |
| `property_value_invalid` | 13 | 0.6% | 0 | — |
| `span_not_in_source` | 0 | — | 34 | 0.8% |

v0.3.5 figures are a re-parse of its banked raws under the current parser (2,438 quarantines
of 4,529 emitted); the shard's own totals are 2,388 of 4,378 because `phase_ingest`
additionally re-checks every span against the whole document.

**`span_partial` (549), split by mechanism:** 70% genuine paraphrase, **30% capitalization
alone** — the model emits `Data readiness` as the canonical name while the sentence says
`data readiness`. `grounding.covers` is case-sensitive by repo design and was not touched.

**`anchor_not_located` (347), the contract's own new failure class:** 52% not found in the
chunk (the anchor was not a character-exact substring), 37% ambiguous (not unique, which the
contract requires), 11% over the 10-token budget. Worst layer by far is **edges (101)**,
which need an anchor pointing into a sentence carrying both endpoints and the predicate.

### `span_partial` has a named cause, and it is not the unit — issue `53e2cf6e`

`kg/extraction/chunked_template.md` claims in its header to carry over "the first grounding
rule, character-exact spans" from `prompt_template.md` v0.3.5. **Both rules are absent from
the file.** Verified by matching every bold rule heading across the two templates; both files
hash to their pinned shas, so this is original and not drift. `prompt_template_v0_3_7.md`
inherits the omission because §1 derived it from `chunked_template.md`.

The missing rule is the one that says *"If the document uses a different surface form than
your chosen `name`, use the document's surface form as the name."* Its absence is exactly the
mechanism behind both the paraphrase and the capitalization halves of `span_partial`:

| arm | has the rule | `span_partial` as % of emitted |
|---|---|---|
| whole-document v0.3.5 (opus-5) | **yes** | **5.9%** |
| chunked v0.3.5 (opus-5) | no | 18.7% |
| chunked v0.3.7 Arm A (haiku) | no | 26.8% |

Same model, same schema, same parser settings between the first two rows: **3.2x**. Chunking
is a co-explanation and the two are not separated, so this is stated as consistent-with, not
proven. **The template was not edited** — it is sha-pinned, and editing it would invalidate
the banked arm's provenance. `write_verdict` now emits an ERRATUM in place of the sentence
"The unit of extraction is the only variable", which was false.

## Cost — the anchor contract's argument survives the yield failure

| | Arm A (haiku, anchors) | v0.3.5 (opus-5, verbatim) | |
|---|---|---|---|
| $ / chunk | **$0.082** | $0.928 | 11.3x cheaper |
| output tokens / chunk | 10,179 | 26,218 | 2.6x cheaper |
| **$ / admitted item** | **$0.0052** | **$0.0205** | **3.9x cheaper** |

**Even at 0.347 of the yield, Arm A is ~4x cheaper per admitted item at F = 0 and
item-faithful = 1.000.** That is the finding the cost objection actually turns on, and it is
why UNDER-EXTRACTION is a verdict about *this arm as configured*, not a refutation of the
anchor contract.

## Semantic edges: zero (§0(a), reported unjudged)

**0 semantic edges across the whole arm** — no `has_component`, `subtype_of`, `consumes`,
`extends` or `implements` was admitted. §0(a) pre-registered that this stratum would be
reported and not judged because five documents cannot reach DD-026's n=35; the arm did not
produce one. `anchor_not_located` on the `edges` layer (101) and the semantic-span rule
between them account for it.

## Type reconciliation (§1.4) fired on real data

195 `majority`, **38 `instrument_evidence_wins`**, **23 `type_conflict`** excluded from
pooling. The privileged-type rule is not decorative: 38 entities were typed `Instrument` on
attribute-bearing evidence in one chunk while other chunks defaulted them to `Concept`. Merge
rate 25.7% (data-readiness) and 39.0% (aidrin).

## What this arm cannot answer

**Arm A changes the contract AND the model at once.** Against banked v0.3.5 it is
haiku+anchors versus opus-5+verbatim, so the 0.347 yield ratio cannot be attributed to either
alone. §3 pre-registers Arm B (`claude-sonnet-5`, same contract) as the next step, and that
comparison separates the *model* within the contract. Separating the *contract* would need
opus-5 under v0.3.7, which §3 explicitly excludes ("Opus 5 is not an arm"). Recorded as a
limitation, not acted on.

## Spend

| run | ceiling | settled | |
|---|---|---|---|
| `pilot_v037_arm_a_haiku` | 3,840,000 | **1,993,432** | 48 chunks, 0 refusals |
| `pilot_v037_arm_a_haiku_judge` | 4,000,000 | **1,113,811** | 96 facts x 2 raters, 0 refusals |

Arm A total **3,107,243**. Daily band 55,000,000, of which 5,130,455 committed today across
all runs — well under, so no operator approval was required (doctrine: under the cap, run it).

## Three harness defects the first chunks exposed — all fixed, all mutation-checked

1. **Docling hard-wraps prose at ~110 characters, and every newline was being read as a
   sentence end.** Derived spans were cut at the wrap: `Poor quality data produces inaccurate
   and ineffective AI models that`. Still verbatim-present in the source, so still passing
   `is_grounded` — the same dangerous shape as the table-row bug from the §2 pre-check, one
   layer down. **My §2 pre-check missed it because it measured the delta my structural rules
   made, not whether the resulting spans were right.** A bare newline now ends the unit only
   at a paragraph break or beside a structural line. Span length after: median 155, p95 367,
   **1.9% over 600 chars** (de-formatted table blocks that lost their pipe markers) — a
   recorded limitation, since a long span makes entailment easier and so could flatter
   faithfulness.
2. **An empty extraction is not a truncated one.** `has_extraction_layers` requires a
   NON-empty layer, which was sound under the exhaustive contract. Under salience a
   references section legitimately yields nothing: `data-readiness#c0029` returned complete
   valid JSON, every layer `[]`, 23 bibliography entries in `mentions` — and was called
   truncated, stopping the run. Truncation is now detected by the envelope carrying none of
   the contract's declared keys.
3. **A `SystemExit` raised inside a worker thread** is a `BaseException`, so it bypassed the
   executor's `except Exception` and killed the pass **before `phase_ingest` ran**, leaving
   20 already-paid-for raws off the shard. `TruncatedChunk` is an `Exception`: the pass
   records it, ingests the rest, then stops. STOP semantics unchanged.

**Append-only re-ingest generations.** Fixing (1) invalidated the spans of 14 chunks already
on the shard, and `chunk_superseded` could not correct them: it keys on
`(chunk_id, start, end)` and the boundaries had not moved, so it would have retired the
corrected events too. Each ingest pass now stamps an `ingest_generation`; readers keep the
highest; the superseded events stay on the shard as the record of what was believed. Nothing
was edited or deleted.

**Ledger erratum** (also recorded in the pre-registration above): the §2 declarations carried
`call_class: extraction` while the §2 arithmetic used the `extraction_chunk` floor. Corrected
by a superseding declare, ceiling unchanged, 0 committed at the time.

## Tests: 383 -> 386. Mutation matrix 20/20 killed

| mutation | result |
|---|---|
| M49 `apply_arm` ignores the profile's shard/tag | KILLED |
| M50 anchor contract not applied on the parse path | KILLED |
| M51 anchor drops not carried into `result.quarantined` | KILLED |
| M52 `reason_class` sweeps the unknown into a bucket | KILLED |
| M53 `resolved_type` ignores the conflict flag | KILLED |
| M54 yield compared over all chunks, not the shared set | KILLED |
| M55 under-extraction verdict never fires | KILLED |
| M56 second arm billed to the first arm's run id | KILLED |
| M57 any Instrument observation counts as evidence | KILLED |
| M58 unknown `emission_contract` accepted | KILLED |
| M59 `attribute_anchors` never become per-attribute spans | KILLED *(SURVIVED first)* |
| M60 empty-but-valid envelope treated as truncation | KILLED |
| M61 truncation guard accepts anything that parses | KILLED *(SURVIVED first)* |
| M62 truncated chunk aborts the pass before ingest | KILLED |
| M63 `--only` filter not applied to the dispatch list | KILLED |
| M64 wrapped newline treated as a sentence end again | KILLED *(SURVIVED first)* |
| M65 paragraph break no longer ends the unit | KILLED *(SURVIVED first)* |
| M66 readers ignore the ingest generation | KILLED |
| M67 pre-generation events dropped as generation 0 | KILLED |
| M68 supersede no longer outranks generation | KILLED |

**Four survived the first pass.** M64/M65 because two boundary rules had **no test at all**
until a real corpus fixture was written for each. M59 and M61 are the **M2 failure mode for
the fifth time in five tasks**: both tests called the helper directly and so proved the
predicate rather than the path that consults it. M61 is now driven through `_extract_one`
with a stubbed model. **M65 was resolved by deleting the code, not by testing it** — the
paragraph-break lookahead could not fire, because a blank line is two newlines and the second
always satisfies the lookbehind. Same outcome as `_MULTIWORD_ABBREV` in §2.

## Not done — the hard stop

**Arm B (`claude-sonnet-5`) not run.** §3 licenses it ("run only if A's admitted yield or
faithfulness falls short" — A's yield falls short), but the operator's instruction for this
pass was to stop and report before it. `pilot_v037_arm_b_sonnet` remains declared at
3,840,000 with **0 committed**. **If Arm B runs, its ceiling must be re-derived from Arm A's
actuals** (41,530 settled/chunk), exactly as §2 required: the projection that produced
3,840,000 is now known to be 2.6x low.

`seldon cc complete` deliberately not run — §3 is not finished.

---

# §3 Arm A — post-hoc decomposition (operator request, 2026-08-29). Zero model spend

Arm B **not run**. Nothing below dispatched a model call: both arms are re-parsed from their
persisted raws under the current parser at identical settings.

## 1. Quarantine split — `span_partial` and `anchor_not_located` as separate counts

Reported at both scopes, because the arm covers 48 chunks and only 44 have a v0.3.5
comparator. **The §3 requirement is the separation, and these two never share a bucket.**

| reason | all 48 chunks | 44 shared chunks |
|---|---|---|
| **`span_partial`** | **549** | **482** |
| **`anchor_not_located`** | **347** | **308** |
| `unresolved_endpoint` | 404 | 356 |
| `property_value_invalid` | 13 | 12 |
| **total quarantined** | **1,313** of 2,052 proposed (64.0%) | **1,158** of 1,849 (62.6%) |

Sub-splits, all 48 chunks:

- **`span_partial` (549)** — 70% genuine paraphrase, **30% capitalization alone**.
- **`anchor_not_located` (347)** — **180 not found in the chunk (52%)**, 128 ambiguous
  i.e. non-unique (37%), 39 over the 10-token budget (11%). Worst layer: `edges` (101).

## 2. Does the v0.3.7 prompt require the anchor to be a verbatim substring? **Yes — three times**

Verbatim from `kg/extraction/prompt_template_v0_3_7.md`, sha `9a410fc3...` (pinned):

> Every node and every edge you emit MUST carry an **`anchor`**: the **shortest substring of
> the chunk text that occurs exactly once in it** and points at the item. **At most 10
> tokens.**

> - The anchor must be **character-exact** as it appears in the chunk, and **unique** in it.
>   If your first choice appears more than once, lengthen it just enough to disambiguate
>   (still ≤ 10 tokens).

> - An anchor that cannot be located, or that matches in more than one place, means the item
>   is **dropped** — so a precise short anchor is worth more to you than a long one.

And for Instrument attributes (line 122): *"each obeying the anchor contract above (unique in
the chunk, ≤ 10 tokens)"*.

**So the requirement is stated three times, the uniqueness rule twice, and the consequence of
failing it once.** This settles a diagnosis I had left open, and it splits the two quarantine
classes into two *different kinds* of finding:

- **`anchor_not_located` (347) is a model COMPLIANCE failure, not a contract gap.** The rule
  is unambiguous and repeated; 180 anchors were simply not substrings of the chunk and 128
  were not unique. Nothing in the prompt needs fixing for this. It is a fact about
  `claude-haiku-4-5` at this task.
- **`span_partial` (549) IS a contract gap.** Nothing in the file constrains the item's
  `name`/`claim_text`/`text` to the document's surface form — that is the FIRST GROUNDING
  RULE, absent from this template and from `chunked_template.md` (issue `53e2cf6e`).

**One qualification, and it cuts against the prompt.** The term *character-exact* appears, but
the whole-document template's operative definition of it does not: *"Copy an exact, contiguous
substring from the document text — do not paraphrase, summarize, reword, fix typos, expand
abbreviations, merge sentences, or normalize punctuation/spacing."* That sentence is in
`prompt_template.md` and in **neither** chunked template (grep count: 1, 0, 0). So the term is
used without its definition. That weakens the compliance finding but does not overturn it: the
plain phrase "shortest substring of the chunk text that occurs exactly once in it" carries the
requirement on its own.

## 3. Decomposing the 0.347 — proposal, not quarantine, is the binding constraint

Per chunk, over the 44 shared chunks, one method for both arms:

| per chunk | Arm A | v0.3.5 | ratio |
|---|---|---|---|
| **proposed** (admitted + quarantined) | **42.02** | **102.93** | **0.408** |
| — admitted by the parser | 15.70 | 47.52 | 0.330 |
| — quarantined | 26.32 | 55.41 | 0.475 |
| dropped at the whole-document re-check | **0.00** | 2.30 | **0.000** |
| **ADMITTED to the shard** | **15.70** | **45.23** | **0.347** |
| diverted to `proposed_relationships` | 0.95 | 6.52 | 0.146 |

| quarantined per chunk, by reason | Arm A | v0.3.5 | ratio |
|---|---|---|---|
| `unresolved_endpoint` | 8.09 | 34.64 | 0.234 |
| `span_partial` | 10.95 | 19.23 | 0.570 |
| **`anchor_not_located`** | **7.00** | **0.00** | new class |
| `property_value_invalid` | 0.27 | 0.00 | new |
| `span_not_in_source` | 0.00 | 0.77 | **0.000** |
| `cites_missing_to` | 0.00 | 0.77 | 0.000 |

### The multiplicative reading

**0.347 = 0.408 (proposal ratio) x 0.851 (admission-rate ratio).**

**About 85% of the shortfall is that Arm A proposes 41% as many items; only ~15% is that it
admits a smaller fraction of them.** Admission rates: Arm A **0.374**, chunked v0.3.5
**0.462**, whole-document v0.3.5 **0.788**.

That reframes the fix. Reaching the 27.14/chunk floor from 42.02 proposed requires an
admission rate of **0.646**:

| scenario | admitted/chunk | ratio | clears 0.60? |
|---|---|---|---|
| Arm A as measured (0.374) | 15.70 | 0.347 | no |
| Arm A at chunked v0.3.5's rate (0.462) | 19.41 | 0.429 | **no** |
| Arm A at whole-document v0.3.5's rate (0.788) | 33.11 | 0.732 | yes |
| Arm A at 100% admission (ceiling) | 42.02 | 0.929 | yes |

**Closing every quarantine gap to the level of the other CHUNKED arm still leaves Arm A below
the floor.** The floor is reachable only at roughly the whole-document arm's admission rate —
and that is precisely the arm holding the two grounding rules both chunked templates dropped.
So the omission is the right lever, but it is a *necessary* fix, not a sufficient one: the
proposal deficit (0.408) is untouched by it and would still need the model or the salience
instruction to change.

### Two things this decomposition settles that the headline hid

**The anchor contract eliminated a whole failure class.** `span_not_in_source` and the
whole-document re-check drop — **3.07 items/chunk lost by v0.3.5, 0.00 by Arm A**. A span cut
from the source by the harness cannot fail to be in the source. That is the locate-at-birth
guarantee working exactly as ADDENDUM-01 §2.1 argued it would, and it is a clean win
independent of the yield verdict.

**Arm A is barely attempting relational structure.** Diversions to `proposed_relationships`
are 0.146 of v0.3.5's, `unresolved_endpoint` is 0.234, admitted edges are 0.243, and semantic
edges are **0**. `anchor_not_located` on the `edges` layer alone is 101 items — an edge anchor
must point into a sentence carrying both endpoints and the predicate, which is the hardest
anchor to satisfy under a ≤ 10-token budget. **The edge deficit is the largest single
component of the yield gap and it has a specific, mechanical cause.**

---

# §3 Arm A — two further diagnostics (operator request, 2026-08-30). Zero model spend

Arm B **held, not run.** Everything below is read from persisted raws.

## 1. The 549 `span_partial` are Arm A's — and they are not a defect in the span

Confirmed by re-deriving every one of them:

| check | result |
|---|---|
| derived span verbatim present in the chunk | **549 / 549** |
| cases where the surviving span equals what the MODEL typed | **0 / 549** |

**The anchor contract held exactly as §1 specified.** No model-supplied `grounding_span`
survived; every span in the graph was cut from the source by the harness.

**`span_partial` is not a test of the span.** It is `grounding.partial_span_reason`, which asks
whether the derived span **covers the item's own typed text attribute**
(`grounding.COVERAGE_ATTRIBUTES` = `verbatim_text`, `text`, `claim_text`, `name`, `term`). The
span is source-cut and verbatim; **the paraphrase is on the ATTRIBUTE side** — what the model
typed as the entity's `name` or the claim's `claim_text`.

| failing attribute | n | | mechanism | n |
|---|---|---|---|---|
| `name` | 235 | | not a substring of the span at all | **382** |
| `claim_text` | 163 | | differs only by capitalization | **167** |
| `text` | 119 | | | |
| `term` | 16 | | | |
| `verbatim_text` | 16 | | | |

So the path is: the anchor locates correctly → the harness cuts the containing sentence → the
model's *own canonical name for the entity* is not a substring of that sentence. Root cause is
the absent FIRST GROUNDING RULE (issue `53e2cf6e`), whose text is precisely *"If the document
uses a different surface form than your chosen `name`, use the document's surface form as the
name."*

### Two corrections to what I wrote in the previous section

**(a) "70% genuine paraphrase" invited the wrong reading.** It is accurate about the
mechanism — 382 of 549 typed attributes are not substrings of their span — but phrased so it
can be read as *the span* being a paraphrase, which the table above shows is impossible on this
path. The correct statement: **70% of `span_partial` items carry a typed attribute that is not
a substring of the source sentence the harness cut; 30% differ from it only by case.**

**(b) The three-row `span_partial` comparison put a different measurement in its third row.**
That table read 5.9% (whole-document v0.3.5) / 18.7% (chunked v0.3.5) / 26.8% (Arm A). The
first two arms supplied their OWN spans, so the model could choose a span containing the name
it had already typed. Arm A does not get that choice: the harness picks the sentence, and the
model's name must appear in **that specific sentence**. **Arm A's 26.8% is therefore measured
against a strictly harder test and is not comparable to the other two.** The 5.9% vs 18.7%
comparison stands — both are model-chosen spans, same model, same schema — and it is that pair,
not Arm A's number, that carries the evidence about the omitted rule.

## 2. Set difference: what v0.3.5 proposed on the 44 shared chunks and Arm A did not

Node entities the model emitted (admitted **or** quarantined), keyed within each chunk.

| | v0.3.5 | Arm A |
|---|---|---|
| distinct node entities proposed | **1,582** | **947** |
| proposed by the other arm and not by this one | 1,215 | 580 |
| **agreed by both** | **367** | **367** |

**The arms are not nested.** Arm A proposed 580 entities v0.3.5 did not; the two agree on only
367 — 23% of v0.3.5's set and 39% of Arm A's. Under-extraction is partly *different*
extraction.

### The key matters, and it is biased by the same defect as §1

Exact normalized-name equality counts a differently-worded name as a miss — and §1 just
established that Arm A systematically canonicalizes names instead of copying the document's
surface form. So the strict figure is an upper bound. Recomputed with a containment-tolerant
key (either name a substring of the other):

| type | missing, exact key | missing, containment key | v0.3.5 total |
|---|---|---|---|
| Concept | 692 | **412** | 941 |
| Claim | 378 | **120** | 407 |
| Instrument | 65 | **12** | 123 |
| Measure | 49 | 21 | 61 |
| Practice | 15 | 12 | 15 |
| Definition | 8 | 3 | 18 |
| Framework | 5 | 3 | 10 |
| Standard | 2 | 2 | 5 |
| Tool | 1 | 0 | 2 |
| **total** | **1,215** | **585** | **1,582** |

**630 of the 1,215 "missing" items were a substring relation — the same entity under a
different name.** The truth is bracketed by these two columns; neither is exact, since
containment is loose in the other direction.

**Instrument evidence** — typed `Instrument` by v0.3.5 with a non-empty `owner`/`year`/`method`
(the same positive criterion `merge.instrument_evidence` reads):

| | n | of 116 |
|---|---|---|
| v0.3.5 proposals carrying instrument evidence | 116 | — |
| with no Arm A counterpart, exact key | 60 | 52% |
| **with no Arm A counterpart, containment key** | **12** | **10%** |

**This is the most consequential number here.** The Instrument stratum is the one the gate
measures, and on the containment key Arm A misses only ~10% of the instrument-bearing entities
v0.3.5 found. The yield deficit is concentrated in `Concept` (412) and `Claim` (120) — the
strata the gate does not read — not in the stratum it does.

### Sample of 20 (seed `arm_a_missing_20`, exact key)

Drawn without stratification, so the mix is proportional: 16 Concept, 4 Claim, 0 Instrument.

| # | type | chunk | name | v0.3.5 source span |
|---|---|---|---|---|
| 1 | Claim | aidrin c0011 | Theil's U is asymmetric, so the association between features X and Y may differ… | `Theil's U is also asym-\nmetric, meaning the association between the features X and Y may\ndiffer from that between Y and X.` |
| 2 | Claim | dr c0004 | Shahbazi et al. [125] provided a survey of techniques focused on identifying… | `et al. [125] provided a survey of techniques focused\non identifying and mitigating representation bias…` |
| 3 | Claim | dr c0010 | The representation rate and statistical rate provide quantitative fairness evaluation… | `These metrics provide quantitative fairness evaluation, offering flexibility based on specific application requirements.` |
| 4 | Claim | dr c0017 | Resolution is a critical image quality metric when developing deep learning models… | `Lakhani [78] and Sabottke and Spieler [121] demonstrate that resolution is a critical image quality metric…` |
| 5 | Concept | aidrin c0002 | Visualizations and reports | `AIDRIN provides visualizations and reports to assist data scientists in further investigating the readiness of data.` |
| 6 | Concept | aidrin c0002 | Metrics specific to assess data for AI | `AIDRIN uses metrics specific to assess data for AI, such as feature importance, feature correlations, class imbalance…` |
| 7 | Concept | aidrin c0003 | Quantitative assessment of data readiness for AI | `Quantitative Assessment of Data\nReadiness for AI` |
| 8 | Concept | aidrin c0006 | user-centric assessment approach | `Additionally, in AIDRIN we offer a user-centric approach in which` |
| 9 | Concept | aidrin c0008 | Understandability | `Quality, Understandability (using FAIR principle compliance), Value,` |
| 10 | Concept | aidrin c0009 | Quantitative variable | `the correlation between two quantitative variables.` |
| 11 | Concept | aidrin c0011 | correlation matrix | `Therefore, the correlation matrices it generates` |
| 12 | Concept | aidrin c0011 | non-binary sensitive attributes | `to binary-sensitive attributes, leaving non-binary attributes unad-` |
| 13 | Concept | dr c0001 | AI training | `use in AI training are still evolving.` |
| 14 | Concept | dr c0002 | unbiased data | `With growing requirements of unbiased data for AI` |
| 15 | Concept | dr c0006 | Bias Indicator | `Bias Indicator` |
| 16 | Concept | dr c0006 | Relational database table | `spreadsheets, relational database tables, self-describing file formats, etc., are common forms of structured data.` |
| 17 | Concept | dr c0008 | Overfitting on duplicated data | `Impact on AI: When training on duplicated data, models may overfit by learning redundant patterns…` |
| 18 | Concept | dr c0013 | biases or limitations in the data | `biases or limitations in the data.` |
| 19 | Concept | dr c0019 | MOS-based subjective assessment | `while human evaluators provide MOS-based subjective\nassessments.` |
| 20 | Concept | dr c0020 | label purity | `explanations of data quality across various dimensions, including completeness, feature relevance, label purity, and data fairness` |

**Read the sample against the salience instruction, which is the pre-registered change.** Items
7, 9, 13, 15 and 18 are section headings and bare noun phrases; 10 and 16 are generic nouns
(`Quantitative variable`, `Relational database table`); 12 and 18 are sentence fragments cut
mid-word (`unad-`) or mid-clause. **v0.3.7 told the model not to inventory every noun, and a
substantial share of what it stopped proposing is exactly that.** Items 1–4 and 17 are real
claims and are genuine losses.

### Instrument-evidence misses (8 of the 60, seed `arm_a_missing_ie`, exact key)

These are the ones that would matter to the gate, and they read differently from the Concepts:

`AIDRIN (AI Data Readiness INspector)` · `FAIRassist` · `Gupta et al. toolkit` ·
`Data Quality Toolkit (DQT)` · `MAD (Median Absolute Deviation)` ·
`probability-based currency metric (PBCM)` · `robust bias measurement technique` ·
`GMSD (Gradient Magnitude Similarity Deviation)`

Every one is a named instrument with an attribute-bearing sentence around it. **On the
containment key only 12 such entities have no Arm A counterpart at all**, so most of these are
present in Arm A under a different surface form — which is once again the §1 defect, not a
recall failure. The distinction is not cosmetic: a recall failure needs a better extractor,
whereas a naming failure needs the one prompt rule that was dropped.

---

# ARM A2 PRE-REGISTRATION (operator, 2026-08-30) — written and committed before A2 ran

Arm B **still held.**

## What A2 changes, and the discipline that it is exactly one thing

`kg/extraction/prompt_template_v0_3_8.md` (new file, sha
`0c6fee1d8d4a4e42f197744c8c92f2f4d8c8dee6cf75470e63648bb21d0b9410`), profile `v0_3_8`, batch
18, shard tag `v0_3_8`, raw dir `events/raw/v0_3_8`. **`prompt_template_v0_3_7.md` is NOT
edited** — it still hashes to `9a410fc3...` and the `v0_3_7` profile still verifies, so Arm A's
provenance is untouched.

The single addition, restored from `kg/extraction/prompt_template.md` and adapted to the
anchor contract (the harness owns the span, so the rule now binds the *name*):

> **Use the document's own surface form as the `name`.** … it then checks that the item's
> `name` (or `term` / `text` / `claim_text` / `verbatim_text`) appears in that sentence
> **verbatim** — the exact surface form the document uses, capitalization included. **If the
> document uses a different surface form than the name you would choose, use the document's
> surface form as the name** and record your preferred form in `aliases`.

**Deliberately NOT restored:** the whole-document template's elaboration of *character-exact*
("do not paraphrase, summarize, reword, fix typos, expand abbreviations, merge sentences, or
normalize punctuation/spacing"), which is also missing from both chunked templates. Restoring
two rules would confound A2. **One rule, one variable.** Everything else — anchor contract,
salience, schema, Instrument positive criterion, semantic-edge rule, evidence_grade, edge
whitelist, closed diversion list, emission order — is v0.3.7's text unchanged, and a test
asserts that on the *rendered* prompt with the header comment stripped.

## Pre-registered reporting for A2

**1. Two figures, both reported, neither substituting for the other.**

- **Raw admitted items per chunk against the standing floor**: `>= 0.60 x 45.23 = 27.14`.
  Unchanged from Arm A, not re-derived, not renegotiated.
- **Instrument-with-evidence containment recall against v0.3.5's 116** such entities on the
  44 shared chunks. "With evidence" = typed `Instrument` by v0.3.5 with a non-empty
  `owner`/`year`/`method` — the same positive criterion `merge.instrument_evidence` reads,
  applied to the raw item because a quarantined item never reached the parser's nulling.

**2. Instrument recall floor: `0.90`.**

- **Below 0.90 → genuine recall loss.** The entities are not there under any name, and the
  missing prompt rule was not the explanation.
- **At or above 0.90 → naming defect confirmed.** The entities were always there; Arm A's
  yield deficit in this stratum was a naming failure the restored rule addresses.

Recall is scored on the **containment** key (either name a substring of the other), with the
exact-equality figure reported beside it. Exact equality would beg the question A2 asks — a
renamed entity is the very defect under test — and containment is loose in the other
direction, so both are published and the truth is bracketed. Encoded as
`INSTRUMENT_RECALL_FLOOR = 0.90` in `scripts/chunked_pilot.py`; four mutations confirm the
floor binds in both directions and that the denominator excludes non-evidence Instruments.

**3. Gate thresholds unchanged.** `F_upper < 0.10`, `item-faithful >= 0.70`, stratum
precondition 20 pooled. Read from the task, never written here.

## Ceiling — re-derived from Arm A's actuals, not from the §2 projection

The §2 projection is now known to be 2.6x low (it omitted `cacheReadInputTokens` and halved
output), so it is discarded rather than reused:

```
Arm A measured          41,530 settled tokens/chunk (1,993,432 over 48)
A2 chunk count             44  (--shared-with chunked_v035: the identical comparator set)
estimate               41,530 x 44 = 1,827,320
floor x calls          20,000 x 44 =   880,000   (does not bind)
CEILING = estimate x 1.5 = 2,741,000 for run `pilot_v038_arm_a2_haiku`
```

A2 runs **only the 44 shared chunks**, not 48: `--shared-with` restricts the dispatch list to
the chunks the baseline already covers, so the two arms are measured on an identical set and
no spend goes to material no comparison reads.

## AMENDED ERRATUM — 5.9% vs 18.7% is a co-explanation, not isolated evidence

The erratum recorded for issue `53e2cf6e` compared `span_partial` as a share of emitted items:
**5.9% whole-document v0.3.5 (rule present) against 18.7% chunked v0.3.5 (rule absent)**, and
presented it as evidence about the dropped rule. **That comparison is amended here: those two
arms differ in the rule AND in the extraction unit.** Whole-document extraction sees the entire
source, so a model naming an entity has the whole document's surface forms in front of it;
chunk-local extraction sees ~1,500 tokens. Either difference can raise `span_partial`, and the
5.9/18.7 pair does not separate them.

**It is a co-explanation, not isolated evidence, and it should not have been stated as though
the rule were the sole cause.** What it does support is that the rule is *worth testing* — which
is what A2 does, and A2 is the design that isolates it: same unit, same chunker, same model,
same 44 chunks, one rule changed. `write_verdict` carries the amended wording so the correction
survives regeneration.

---

# ARM A2 RESULT — the restored rule works; the yield floor still is not met

**Verdict: UNDER-EXTRACTION** (0.537 < 0.60), **and the naming-defect diagnosis is confirmed.**
Arm B **still held.** 44/44 chunks, 0 failures, settled **1,755,070 of 2,741,000**; judge
**2,075,727 of 4,000,000**; 0 refusals on either.

## The two pre-registered figures, and they split

| pre-registered | threshold | Arm A | **Arm A2** | |
|---|---|---|---|---|
| F (Wilson 95% upper) | `< 0.10` | 0.0385 / 96 facts | **0.0243 / 154 facts** | **PASS** |
| item-faithful | `>= 0.70` | 60/60 = 1.000 | **72/73 = 0.986** | **PASS** |
| admitted items / chunk | `>= 27.14` | 15.70 (0.347) | **24.30 (0.537)** | **FAIL** |
| Instrument recall (containment) | `>= 0.90` | 0.897 | **0.905** | **PASS** |

Raters `claude-opus-4-8` 1.000 / `claude-sonnet-5` 0.974, Dawid-Skene over 308 labels. The one
unfaithful item is class `filled_attribute` — an attribute the document did not state, which is
exactly the class the per-attribute span rule exists to catch. Span checks: 10 of 154 facts on
a mid-noun-phrase span.

**F_upper tightened from 0.0385 to 0.0243** purely because there were 60% more facts to judge —
a larger sample narrows the interval. Faithfulness is materially unchanged at a larger n.

## The isolation worked: one rule, one mechanism, on identical chunks

Same 44 chunks, same chunker, same model, same anchor contract, same salience instruction.
The only difference is the restored FIRST GROUNDING RULE.

| on the 44 shared chunks | Arm A | Arm A2 | change |
|---|---|---|---|
| **proposed** | 1,849 | **1,766** | **0.96x** |
| **admitted** | 691 | **1,069** | **1.55x** |
| admission rate | 37.4% | **60.5%** | — |
| quarantine rate | 62.6% | **39.5%** | v0.3.5 baseline: 54.5% |
| **`span_partial`** | **482** | **172** | **0.36x** |
| `unresolved_endpoint` | 356 | 180 | 0.51x |
| `anchor_not_located` | 308 | 340 | 1.10x |
| `property_value_invalid` | 12 | 0 | 0.00x |
| semantic edges | 0 | 8 | — |
| output tokens / chunk | 10,179 | 8,030 | 0.79x |

**Proposals held flat at 0.96x while admissions rose 1.55x.** That is the whole point of the
design: a rule about *which words you copy* cannot make a model see more, only name what it
already saw in the document's own words — and that is precisely what moved. `span_partial` fell
**64%**, the endpoint cascade that depends on it halved, and **A2's quarantine rate is now
better than the v0.3.5 baseline's** (39.5% vs 54.5%).

The prediction this tests was made before A2 ran, in the yield decomposition: *"the omission is
the right lever, but it is a necessary fix, not a sufficient one: the proposal deficit (0.408)
is untouched by it."* Measured: the proposal ratio moved from 0.408 to 0.390 — untouched, as
predicted — and the admission rate rose from 0.374 to 0.605 against the 0.646 needed for the
floor. **A2 lands 4 points of admission rate short of clearing a floor it could only ever have
reached through admission.**

`anchor_not_located` went the other way (308 → 340, 1.10x) and is now A2's **largest** single
quarantine class. Nothing in the restored rule addresses it — the rule binds the `name`, not
the anchor — so this is the untouched half of the problem and the obvious next lever.

## My pre-registered recall floor was a poor instrument, and I should have known

It returned `naming_defect_confirmed` at **0.905 >= 0.90**. But Arm A scores **0.897** on the
same measure. **The verdict flipped on one entity out of 116** (104 → 105 matched).

That is not a discrimination. The metric was near-saturated in both arms, and **I had Arm A's
104/116 in hand from the previous day's containment analysis when I set the floor at 0.90** —
so a floor with essentially no resolving power over the comparison it was meant to decide was
foreseeable at registration. It is reported because it was pre-registered, and it is not the
evidence the conclusion rests on.

**The conclusion rests on `span_partial` 0.36x with proposals flat**, which is a clean,
mechanism-specific isolation and moved by a factor, not by a rounding.

**Exact-name recall FELL, 0.483 → 0.457, and that is not a defect.** Exact recall compares A2's
chosen names to **v0.3.5's** chosen names — and v0.3.5 lacked the rule too. Making A2 copy the
*document's* surface form cannot make it agree with another arm's free choices. Exact-name
agreement with an unruled arm was never a sound instrument for this question; containment was
the right key and the reason it was pre-registered as the scoring one.

## Cost — A2 is the cheapest arm per admitted item by a factor of seven

44-chunk basis, settled dollars:

| | $ / chunk | output tok / chunk | **$ / admitted item** |
|---|---|---|---|
| v0.3.5 chunked (opus-5, verbatim) | $0.9280 | 26,956 | **$0.02052** |
| Arm A (haiku, anchors) | $0.0820 | 10,179 | $0.00522 |
| **Arm A2 (haiku, anchors + rule)** | **$0.0706** | **8,030** | **$0.00291** |

**The restored rule made the output smaller (0.79x) and the yield larger (1.55x) at the same
time.** A2 costs **$3.11 against v0.3.5's $40.83** for the same 44 chunks — 13x cheaper in
dollars and 7x cheaper per admitted item, at F = 0 and item-faithful 0.986.

## Where this leaves the standing question

The pre-registered floor is a floor, and 0.537 is below it, so **A2 reports UNDER-EXTRACTION**.
Two facts sit beside that verdict and neither is licence to move the floor:

1. **The diagnosis was right and the fix is real** — 1.55x admitted, quarantine now below the
   baseline's, one rule, proposals flat.
2. **The remaining gap is not in the same place.** It is `anchor_not_located` (340, now the
   largest class, untouched by this rule) and the proposal deficit (0.390, untouched by design
   — salience is doing what it was told to do, and recall is not gate-measured).

Type reconciliation on A2: 323 majority, 58 `instrument_evidence_wins`, 30 `type_conflict`
excluded from pooling.

`seldon cc complete` not run — §3 is not finished while Arm B is held.
